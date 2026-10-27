"""Sprint 02 Security RETEST (VULN-011 JWT-14 + lock path, VULN-013 THR-1 local only). Dev server, fresh SQLite, no Docker.
Usage: python retest_sprint02.py <backend_dir> <python_executable>"""
import base64, hashlib, hmac, http.cookiejar, json, os, re, statistics, subprocess, sys, tempfile, threading, time
import urllib.error, urllib.parse, urllib.request

BACKEND, PY = sys.argv[1], sys.argv[2]
PORT = 8777
BASE = f"http://127.0.0.1:{PORT}"
KEY = "pentest-throwaway-key-pentest-throwaway-key"
PW = "Zx9!kLm#Qw27pR"
DB = os.path.join(tempfile.mkdtemp(), "pt.sqlite3")
ENV = {**os.environ, "DATABASE_URL": f"sqlite:///{DB}", "DEBUG": "False", "ALLOWED_HOSTS": "127.0.0.1,localhost",
       "SECRET_KEY": KEY, "DJANGO_SETTINGS_MODULE": "config.settings.development", "DEMO_PASSWORD": PW,
       "CORS_ALLOWED_ORIGINS": "http://localhost:5173"}
RELAXED = {"RATELIMIT_AUTH": "100000/minute", "RATELIMIT_SENSITIVE": "100000/minute", "RATELIMIT_USER": "100000/minute",
           "RATELIMIT_ANON": "100000/minute"}


def out(kind, cid, msg):
    print(f"{kind:8} {cid:10} {msg}", flush=True)


def call(path, method="POST", body=None, headers=None, raw=None, ctype="application/json", timeout=120):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": ctype, **(headers or {})}
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt, st, hd = r.read().decode("utf-8", "replace"), r.status, r.headers
    except urllib.error.HTTPError as e:
        txt, st, hd = e.read().decode("utf-8", "replace"), e.code, e.headers
    dt = time.perf_counter() - t
    try:
        j = json.loads(txt)
    except ValueError:
        j = None
    return st, j, hd, txt, dt


def manage(*a):
    return subprocess.run([PY, "manage.py", *a], cwd=BACKEND, env=ENV, capture_output=True, text=True, timeout=180)


def shell(code):
    r = manage("shell", "-c", code)
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]


def start(extra):
    p = subprocess.Popen([PY, "manage.py", "runserver", str(PORT), "--noreload"], cwd=BACKEND,
                         env={**ENV, **extra}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/api/v1/nope/", timeout=1)
        except urllib.error.HTTPError:
            break
        except Exception:
            time.sleep(0.5)
    return p


def stop(p):
    p.terminate()
    try:
        p.wait(10)
    except Exception:
        p.kill()


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64(s):
    return json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))


def forge(payload, key=KEY, alg="HS256"):
    si = b64(json.dumps({"typ": "JWT", "alg": alg}).encode()) + "." + b64(json.dumps(payload).encode())
    if alg == "none":
        return si + "."
    dig = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}[alg]
    return si + "." + b64(hmac.new(key.encode(), si.encode(), dig).digest())


def login(ident, pw=PW, headers=None):
    return call("/api/v1/auth/token/", body={"username_or_phone": ident, "password": pw}, headers=headers)


def reg(kind, headers=None, **kw):
    body = {"full_name": "Pen Tester", "phone": "01155550000", "password": PW}
    body.update(kw)
    return call(f"/api/v1/auth/register/{kind}/", body=body, headers=headers)


def me(tok, headers=None):
    return call("/api/v1/auth/me/", "GET", headers={"Authorization": f"Bearer {tok}", **(headers or {})})


def refresh(tok):
    return call("/api/v1/auth/token/refresh/", body={"refresh": tok})


def uid(username):
    return int(shell(f"from apps.users.models import User; print(User.all_objects.get(username='{username}').pk)"))


def upd(username, **fields):
    shell(f"from django.utils import timezone; from apps.users.models import User; User.all_objects.filter(username='{username}').update(**{fields!r}); print(1)")

import sqlite3
manage("migrate", "--noinput")
manage("seed_demo", "--force")
p = start(RELAXED)
try:
    for n in (10, 30):
        for rnd in range(3):
            tk = login("demo_client")[1]["data"]["refresh"]
            res, bodies = [], []
            def go():
                r = refresh(tk); res.append(r[0]); bodies.append(r)
            ts = [threading.Thread(target=go) for _ in range(n)]
            [t.start() for t in ts]; [t.join() for t in ts]
            ok = res.count(200) <= 1 and 500 not in res and set(res) <= {200, 401}
            out("OK" if ok else "FINDING", "JWT-14", f"{n} parallel redemptions, round {rnd+1}: 200x{res.count(200)} 401x{res.count(401)} other={sorted(set(res)-{200,401})}")
            win = [b for b in bodies if b[0] == 200]
            out("OK" if (len(win) == 1) else "INFO", "JWT-14s", f"strict exactly-one-200 observed on SQLite this round: {len(win)}")
            out("OK" if refresh(tk)[0] == 401 else "FINDING", "JWT-14b", "old token refused after the race")
            if win:
                d = win[0][1]["data"]
                out("OK" if me(d["access"])[0] == 200 else "FINDING", "JWT-14c", "winner's access token works")
                s2 = refresh(d["refresh"])
                out("OK" if s2[0] == 200 else "FINDING", "JWT-14d", f"winner's refresh rotates again -> {s2[0]}")
                out("OK" if refresh(d["refresh"])[0] == 401 else "FINDING", "JWT-14e", "winner's rotated-away refresh refused")
    # sequential reuse / logout
    d = login("demo_client")[1]["data"]
    r1 = refresh(d["refresh"]); again = refresh(d["refresh"])[0]
    out("OK" if (r1[0], again) == (200, 401) else "FINDING", "ROT-1", f"rotate {r1[0]}, reuse {again}")
    lo = call("/api/v1/auth/logout/", body={"refresh": r1[1]["data"]["refresh"]})[0]
    out("OK" if refresh(r1[1]["data"]["refresh"])[0] == 401 else "FINDING", "ROT-2", f"logout {lo}, refresh after logout 401")
    out("OK" if call("/api/v1/auth/logout/", body={"refresh": d["refresh"]})[0] in (200, 204) else "FINDING", "ROT-3", "logout of an already rotated-away token is idempotent")
    st, j, _, txt, _ = refresh(d["refresh"])
    out("INFO", "ROT-4", f"error envelope on reuse: {txt[:160]}")
    # lock-error path: hold an exclusive write lock on the SQLite file while refreshing
    tk = login("demo_client")[1]["data"]["refresh"]
    con = sqlite3.connect(DB, timeout=1, isolation_level=None)
    con.execute("BEGIN EXCLUSIVE")
    st, j, _, txt, dt = refresh(tk)
    out("OK" if st in (401, 503) else "FINDING", "LOCK-1", f"refresh while DB write-locked -> {st} in {dt:.1f}s (never 500); body {txt[:120]}")
    con.execute("ROLLBACK"); con.close()
    s = refresh(tk)
    out("OK" if s[0] == 200 else "FINDING", "LOCK-2", f"same token after the lock is released -> {s[0]} (rolled back, token not burned)")
    out("OK" if refresh(tk)[0] == 401 else "FINDING", "LOCK-3", "and then it is single-use again")
finally:
    stop(p)

for np_ in ("0", "1"):
    p = start({"NUM_PROXIES": np_})
    try:
        codes = [login("demo_client", "wrong-" + str(i), headers={"X-Forwarded-For": f"10.9.{i}.{i + 1}"})[0] for i in range(25)]
        out("OK" if (codes.count(429) >= 14) == (np_ == "0") else "FINDING", f"THR-1/np{np_}", f"25 logins rotating a forged X-Forwarded-For (direct to app, LOCAL ONLY): {codes.count(401)}x401 {codes.count(429)}x429 (expected: np0 limited, np1 bypassed = why the port must not be exposed)")
    finally:
        stop(p)
print("DONE")
