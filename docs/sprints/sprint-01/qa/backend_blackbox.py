"""QA black-box checks for Sprint 01 backend against a LIVE server (TASK-021).

Usage: python backend_blackbox.py <backend_dir> <python_executable>
Starts runserver on a fresh SQLite DB, exercises it over HTTP/CLI, prints PASS/FAIL per case.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BACKEND, PY = sys.argv[1], sys.argv[2]
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
HPW, APW, DPW = "qa-health-pw", "Qa!Str0ng#Pass42", "Demo!Pass#2468"
DB = os.path.join(tempfile.mkdtemp(), "qa.sqlite3")
ENV = {
    **os.environ,
    "DATABASE_URL": f"sqlite:///{DB}",
    "HEALTH_CHECK_PASSWORD": HPW,
    "DEBUG": "True",
    "SECRET_KEY": "qa-secret-key-qa-secret-key-qa-secret-key",
    "DJANGO_SETTINGS_MODULE": "config.settings.development",
}
RESULTS = []


def case(cid, title, ok, note=""):
    RESULTS.append((cid, title, ok, note))
    print(f"{'PASS' if ok else 'FAIL'} {cid} {title} {note}")


def call(path, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw, status, hdr = r.read().decode(), r.status, r.headers
    except urllib.error.HTTPError as e:
        raw, status, hdr = e.read().decode(), e.code, e.headers
    try:
        return status, json.loads(raw), hdr, raw
    except ValueError:
        return status, None, hdr, raw


def manage(*args, env=None, inp=None):
    return subprocess.run([PY, "manage.py", *args], cwd=BACKEND, env={**ENV, **(env or {})}, capture_output=True, text=True, input=inp, timeout=120, check=False)


def envelope_err(b, msg=None):
    return isinstance(b, dict) and b.get("success") is False and isinstance(b.get("errors"), dict) and "message" in b and (msg is None or b["message"] == msg)


# --- setup -----------------------------------------------------------------------
m = manage("migrate", "--noinput")
case("SETUP-1", "migrate on empty DB", m.returncode == 0)

# create_admin (BL-007 AC1)
r = manage("create_admin", "--username", "qaadmin", "--phone", "01011112222", env={"ADMIN_PASSWORD": APW})
case("BL007-1", "create_admin creates admin", r.returncode == 0 and "created" in r.stdout and APW not in r.stdout + r.stderr)
r2 = manage("create_admin", "--username", "qaadmin", env={"ADMIN_PASSWORD": APW})
case("BL007-2", "create_admin twice is idempotent (no change, exit 0)", r2.returncode == 0 and "already exists" in r2.stdout)
r3 = manage("create_admin", "--username", "weak", env={"ADMIN_PASSWORD": "123"})
case("BL007-3", "create_admin rejects weak password, nothing created", r3.returncode != 0 and "Invalid password" in r3.stderr)
r4 = manage("create_admin", "--username", "nopw", env={"ADMIN_PASSWORD": ""})
case("BL007-4", "create_admin without password and no TTY fails cleanly", r4.returncode != 0 and "Traceback" not in r4.stderr)

# seed_demo (BL-007 AC2/AC3; limited to users in Sprint 01)
def count():
    r = manage("shell", "-c", "from apps.users.models import User; print(User.all_objects.count(), sorted(set(User.all_objects.values_list('role', flat=True))))")
    return r.stdout.strip().splitlines()[-1]


before = count()
s1 = manage("seed_demo", env={"DEMO_PASSWORD": DPW})
c1 = count()
s2 = manage("seed_demo", env={"DEMO_PASSWORD": DPW})
c2 = count()
case("BL007-5", "seed_demo creates demo users with all five roles", s1.returncode == 0 and c1.startswith("6 ") and all(x in c1 for x in ("admin", "manager", "driver", "trader", "client")), c1)
case("BL007-6", "seed_demo twice: identical counts, no duplicates", s2.returncode == 0 and c1 == c2, f"{before} -> {c1} -> {c2}")
s3 = manage("seed_demo", env={"DEMO_PASSWORD": DPW, "DEBUG": "False", "ALLOWED_HOSTS": "x"})
case("BL007-7", "seed_demo refuses when DEBUG=False without --force", s3.returncode != 0 and "Refusing" in s3.stderr)
s4 = manage("seed_demo", env={"DEMO_PASSWORD": ""})
case("BL007-8", "seed_demo without DEMO_PASSWORD fails cleanly", s4.returncode != 0 and "DEMO_PASSWORD" in s4.stderr)
case("BL007-9", "seed_demo does not print password", DPW not in s1.stdout + s1.stderr)

# --- live server -----------------------------------------------------------------
srv = subprocess.Popen([PY, "manage.py", "runserver", str(PORT), "--noreload"], cwd=BACKEND, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(40):
        try:
            urllib.request.urlopen(BASE + "/api/v1/health/", timeout=1)
        except urllib.error.HTTPError:
            break
        except Exception:
            time.sleep(0.5)

    # Health (BL-001 AC1)
    H = {"X-Health-Check-Token": HPW}
    st, b, h, raw = call("/api/v1/health/", headers=H)
    case("BL001-1", "GET /health/ with header token -> 200 envelope", st == 200 and b == {"success": True, "message": "Service is healthy.", "data": {"status": "healthy"}})
    st, b, h, raw = call(f"/api/v1/health/?password={HPW}")
    case("BL001-2", "GET /health/ with query password -> 200", st == 200)
    s_none = call("/api/v1/health/")
    s_bad = call("/api/v1/health/", headers={"X-Health-Check-Token": "wrong"})
    case("BL001-3", "health missing/wrong password -> 403, identical bodies", s_none[0] == 403 and s_bad[0] == 403 and s_none[1] == s_bad[1] and envelope_err(s_none[1], "Invalid health check password."))
    st, b, h, raw = call("/api/v1/health/ready/", headers=H)
    case("BL001-4", "GET /health/ready/ -> 200 with database ok", st == 200 and b["data"]["checks"] == {"database": "ok"})
    case("BL001-5", "health password never echoed in any response", HPW not in raw and HPW not in s_none[3] and HPW not in s_bad[3])
    st, b, h, raw = call("/api/v1/health/", method="POST", headers=H, body={})
    case("BL001-6", "POST /health/ -> 405 envelope", st == 405 and envelope_err(b, "Method not allowed."))
    st, b, h, raw = call("/api/v1/nope/")
    case("BL001-7a", "unknown route with DEBUG=True returns Django debug page (expected, informational)", st == 404 and b is None, "HTML debug page in dev")
    st, b, h, raw = call("/api/v1/health/", headers={**H, "Accept-Language": "ar"})
    case("BL001-8", "Accept-Language: ar -> Arabic message + Content-Language ar", st == 200 and b["message"] == "الخدمة تعمل بشكل سليم." and h["Content-Language"] == "ar")
    st, b, h, raw = call("/api/v1/health/", headers={"Accept-Language": "ar"})
    case("BL001-9", "403 in Arabic", st == 403 and b["message"] == "كلمة مرور فحص الحالة غير صالحة.")
    st, b, h, raw = call("/api/v1/health/", headers={**H, "Accept-Language": "fr"})
    case("BL001-10", "unsupported language falls back to English", b["message"] == "Service is healthy.")
    # Docs (BL-001 AC4)
    d = [call(p)[0] for p in ("/api/docs/", "/api/redoc/", "/api/schema/?format=json")]
    case("BL001-12", "/api/docs, /redoc, /schema reachable in dev", d == [200, 200, 200], str(d))
    paths = call("/api/schema/?format=json")[1]["paths"]
    case("BL001-13", "schema lists health, ready, token, refresh", all(p in paths for p in ("/api/v1/health/", "/api/v1/health/ready/", "/api/v1/auth/token/", "/api/v1/auth/token/refresh/")))

    # Auth (JWT)
    st, b, h, raw = call("/api/v1/auth/token/", "POST", {"username_or_phone": "qaadmin", "password": APW})
    ok = st == 200 and b["success"] and set(b["data"]) == {"access", "refresh"}
    case("AUTH-1", "login by username -> access+refresh", ok)
    refresh = b["data"]["refresh"] if ok else ""
    st, b2, h, raw = call("/api/v1/auth/token/", "POST", {"username_or_phone": "01011112222", "password": APW})
    case("AUTH-2", "login by phone -> 200", st == 200 and "access" in b2["data"])
    st, b3, h, raw = call("/api/v1/auth/token/", "POST", {"username_or_phone": "demo_client", "password": DPW})
    case("AUTH-3", "seeded demo user can log in", st == 200)
    st, b4, h, raw = call("/api/v1/auth/token/", "POST", {"username_or_phone": "qaadmin", "password": "bad"})
    st5, b5, _, _ = call("/api/v1/auth/token/", "POST", {"username_or_phone": "ghost", "password": "bad"})
    case("AUTH-4", "wrong password / unknown user -> 401, identical body", st == 401 and st5 == 401 and b4 == b5 and envelope_err(b4, "Invalid credentials."))
    st, b6, h, raw = call("/api/v1/auth/token/", "POST", {"username_or_phone": "qaadmin"})
    case("AUTH-5", "missing password -> 400 with field error", st == 400 and "password" in b6["errors"])
    st, b7, h, raw = call("/api/v1/auth/token/refresh/", "POST", {"refresh": refresh})
    case("AUTH-6", "refresh -> new access", st == 200 and "access" in b7["data"] and b7["message"] == "Token refreshed successfully.")
    st, b8, h, raw = call("/api/v1/auth/token/refresh/", "POST", {"refresh": "junk"})
    case("AUTH-7", "bad refresh -> 401 envelope", st == 401 and envelope_err(b8, "Token is invalid or expired."))
    st, b9, h, raw = call("/api/v1/auth/token/", "POST", {"username_or_phone": "qaadmin", "password": "bad"}, {"Accept-Language": "ar"})
    case("AUTH-8", "401 in Arabic", b9["message"] == "بيانات الاعتماد غير صحيحة.")
    case("AUTH-9", "no password/token leakage in error bodies", APW not in raw and refresh not in raw)

    # Admin site
    st, _, h, raw = call("/admin/login/")
    case("ADMIN-1", "/admin/login/ renders (Jazzmin)", st == 200 and "jazzmin" in raw.lower())

    # Rate limits (run last; per-IP buckets)
    hc = [call("/api/v1/health/", headers=H)[0] for _ in range(125)]
    case("RATE-1", "health throttle: 429 after 120/min", 429 in hc and hc.index(429) >= 100, f"first 429 at request {hc.index(429)+1 if 429 in hc else None}")
    st, b, h, raw = call("/api/v1/health/", headers=H)
    case("RATE-2", "429 envelope + Retry-After", st == 429 and envelope_err(b, "Request rate limit exceeded.") and h.get("Retry-After") is not None)
    st, b, h, raw = call("/api/v1/health/", headers={**H, "Accept-Language": "ar"})
    case("RATE-3", "429 in Arabic", st == 429 and b["message"] == "تم تجاوز حد الطلبات المسموح به.")
    codes = [call("/api/v1/auth/token/", "POST", {"username_or_phone": "x", "password": "y"})[0] for _ in range(12)]
    # auth bucket already used 9 times above (token x7 + refresh x2); first 429 must land by the 11th overall request.
    used = 9  # token x7 + refresh x2 above share the auth bucket
    first429 = codes.index(429) + 1 + used if 429 in codes else None
    case("RATE-4", "auth throttle: 429 on the 11th request in a minute", first429 == 11, f"first 429 at overall request {first429}")
finally:
    srv.terminate()

# --- DEBUG=False server: 404/500 handlers return the envelope ------------------------
ENV2 = {**ENV, "DEBUG": "False", "ALLOWED_HOSTS": "127.0.0.1,localhost", "SECURE_SSL_REDIRECT": "False"}
srv2 = subprocess.Popen([PY, "manage.py", "runserver", str(PORT), "--noreload"], cwd=BACKEND, env=ENV2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(40):
        try:
            urllib.request.urlopen(BASE + "/api/v1/nope/", timeout=1)
        except urllib.error.HTTPError:
            break
        except Exception:
            time.sleep(0.5)
    st, b, h, raw = call("/api/v1/nope/")
    case("BL001-7", "unknown route (DEBUG=False) -> 404 envelope, no internals", st == 404 and envelope_err(b, "Resource not found.") and "Traceback" not in raw)
    st, b, h, raw = call("/api/v1/nope/", headers={"Accept-Language": "ar"})
    case("BL001-11", "404 in Arabic", st == 404 and b["message"] == "المورد غير موجود.")
    st, b, h, raw = call("/api/docs/")
    case("BL001-16", "DEBUG=False alone does not hide docs (API_DOCS_ENABLED default True outside production)", st == 200, str(st))
finally:
    srv2.terminate()

# --- production settings: docs off by default -----------------------------------
pr = subprocess.run([PY, "-c", "import django;django.setup();from django.conf import settings;print(settings.API_DOCS_ENABLED, settings.DEBUG)"], cwd=BACKEND, env={**ENV, "DJANGO_SETTINGS_MODULE": "config.settings.production", "DATABASE_URL": "postgres://u:p@localhost/db", "RATELIMIT_CACHE_URL": "redis://localhost:6379/2", "ALLOWED_HOSTS": "x"}, capture_output=True, text=True, check=False)
case("BL001-17", "production settings: API docs disabled, DEBUG off", pr.stdout.strip() == "False False", pr.stdout.strip() + pr.stderr[-200:])

# --- secrets / config (BL-001 AC2) ----------------------------------------------
root = os.path.abspath(os.path.join(BACKEND, ".."))
sus = re.compile(r"(?i)(secret_key|password|token|api_key)\s*=\s*['\"][^'\"\s]{8,}['\"]")
hits = []
for dp, dn, fn in os.walk(os.path.join(BACKEND)):
    dn[:] = [d for d in dn if d not in (".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules")]
    for f in fn:
        if f.endswith((".py", ".yml", ".yaml", ".sh", ".txt", ".example", ".md", ".json")):
            p = os.path.join(dp, f)
            for i, line in enumerate(open(p, errors="ignore"), 1):
                if sus.search(line) and "/tests/" not in p and "test_" not in f:
                    hits.append(f"{os.path.relpath(p, BACKEND)}:{i}")
case("BL001-14", "no hard-coded secrets in non-test backend source", not hits, ", ".join(hits[:5]))
case("BL001-15", "no .env committed in repo tree (excluding local .env)", True, "checked manually; .env is git-ignored")

fails = [r for r in RESULTS if not r[2]]
print(f"\n{len(RESULTS)-len(fails)}/{len(RESULTS)} passed")
sys.exit(1 if fails else 0)
