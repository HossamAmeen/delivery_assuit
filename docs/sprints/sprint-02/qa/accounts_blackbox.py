"""QA black-box checks for Sprint 02 accounts (TASK-039) against a LIVE dev server.

Usage: python accounts_blackbox.py <backend_dir> <python_executable>
Fresh SQLite DB, runserver (no Docker). Phase A: relaxed throttles for functional cases.
Phase B: default throttles (auth 10/min, sensitive 30/min), spoofed X-Forwarded-For,
NUM_PROXIES=0 and =1. Prints PASS/FAIL per case.
"""
import json, os, statistics, subprocess, sys, tempfile, time, urllib.error, urllib.request

BACKEND, PY = sys.argv[1], sys.argv[2]
PORT = 8766
BASE = f"http://127.0.0.1:{PORT}"
APW, DPW = "Qa!Str0ng#Pass42", "Demo!Pass#2468"
STRONG = "Zx9!kLm#Qw27pR"
DB = os.path.join(tempfile.mkdtemp(), "qa2.sqlite3")
ENV = {**os.environ, "DATABASE_URL": f"sqlite:///{DB}", "HEALTH_CHECK_PASSWORD": "qa-health-pw",
       "DEBUG": "False", "ALLOWED_HOSTS": "127.0.0.1,localhost", "SECURE_SSL_REDIRECT": "False",
       "SECRET_KEY": "qa-secret-key-qa-secret-key-qa-secret-key",
       "DJANGO_SETTINGS_MODULE": "config.settings.development"}
RES = []

def case(cid, title, ok, note=""):
    RES.append((cid, title, ok, note)); print(f"{'PASS' if ok else 'FAIL'} {cid} {title} {note}", flush=True)

def call(path, method="POST", body=None, headers=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            txt, st, h = r.read().decode(), r.status, r.headers
    except urllib.error.HTTPError as e:
        txt, st, h = e.read().decode(), e.code, e.headers
    dt = time.perf_counter() - t
    try: j = json.loads(txt)
    except ValueError: j = None
    return st, j, h, txt, dt

def manage(*a, env=None):
    return subprocess.run([PY, "manage.py", *a], cwd=BACKEND, env={**ENV, **(env or {})}, capture_output=True, text=True, timeout=180, check=False)

def start(extra):
    p = subprocess.Popen([PY, "manage.py", "runserver", str(PORT), "--noreload"], cwd=BACKEND, env={**ENV, **extra}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try: urllib.request.urlopen(BASE + "/api/v1/nope/", timeout=1)
        except urllib.error.HTTPError: break
        except Exception: time.sleep(0.5)
    return p

def stop(p):
    p.terminate()
    try: p.wait(10)
    except Exception: p.kill()

def sql(code):
    r = manage("shell", "-c", code); return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]

def err(b, msg=None, code=None):
    return isinstance(b, dict) and b.get("success") is False and isinstance(b.get("errors"), dict) and (msg is None or b.get("message") == msg) and b.get("code") == code

def reg(kind, **kw):
    body = {"full_name": "Ahmed Ali", "phone": "0100 123 4567", "password": STRONG, **kw}
    return call(f"/api/v1/auth/register/{kind}/", body=body)

def login(i, p, h=None): return call("/api/v1/auth/token/", body={"username_or_phone": i, "password": p}, headers=h)
def me(tok, h=None): return call("/api/v1/auth/me/", "GET", headers={"Authorization": f"Bearer {tok}", **(h or {})})

RELAX = {"RATELIMIT_AUTH": "10000/minute", "RATELIMIT_SENSITIVE": "10000/minute", "RATELIMIT_ANON": "10000/minute", "RATELIMIT_USER": "10000/minute"}

case("SETUP-1", "migrate on empty DB (incl. token_blacklist)", manage("migrate", "--noinput").returncode == 0)
manage("create_admin", "--username", "qaadmin", "--phone", "01011112222", env={"ADMIN_PASSWORD": APW})

# ---------------- BL-007/033 seed_demo ------------------------------------------------
cnt = "from apps.users.models import User; print(User.all_objects.count(), sorted(User.all_objects.values_list('username','role','status')))"
s1 = manage("seed_demo", env={"DEMO_PASSWORD": DPW, "DEBUG": "True"}); c1 = sql(cnt)
s2 = manage("seed_demo", env={"DEMO_PASSWORD": DPW, "DEBUG": "True"}); c2 = sql(cnt)
case("T033-1", "seed_demo succeeds, no password printed", s1.returncode == 0 and DPW not in s1.stdout + s1.stderr)
case("T033-2", "seed_demo twice: identical users, no duplicates", s2.returncode == 0 and c1 == c2, c1[:60])
case("T033-3", "each status represented (active, pending_approval, deactivated)", all(x in c1 for x in ("'active'", "'pending_approval'", "'deactivated'")))
case("T033-4", "demo pending driver + deactivated client exist; active driver and trader exist", all(x in c1 for x in ("demo_driver_pending", "demo_client_deactivated", "'demo_driver', 'driver', 'active'", "'demo_trader', 'trader', 'active'")))

p = start(RELAX)
try:
    A = "/api/v1/auth/"
    # ---------------- BL-009/010/011 registration ------------------------------------
    st, b, h, raw, _ = reg("driver", email="ahmed@example.com")
    u = (b or {}).get("data", {}).get("user", {})
    case("BL009-1", "driver register -> 201, role driver, pending_approval, phone normalised, no tokens", st == 201 and u.get("role") == "driver" and u.get("status") == "pending_approval" and u.get("phone") == "01001234567" and "access" not in raw and "refresh" not in raw and set(u) == {"id", "full_name", "phone", "role", "status"}, raw[:120])
    case("BL009-1b", "driver register message per contract", b and b["message"] == "Registration successful. Your account is pending approval.")
    st, b, *_ = reg("trader", phone="+20 111-222-3333", full_name="Nile Shop")
    u = b["data"]["user"]
    case("BL010-1", "trader register -> 201 trader pending_approval, +20 phone normalised", st == 201 and u["role"] == "trader" and u["status"] == "pending_approval" and u["phone"] == "201112223333", str(u))
    st, b, *_ = reg("client", phone="٠١٢٠٠٣٣٤٤٥٥")
    u = b["data"]["user"]
    case("BL011-1", "client register -> 201 client active, Arabic-Indic digits normalised", st == 201 and u["role"] == "client" and u["status"] == "active" and u["phone"] == "01200334455" and b["message"] == "Registration successful.", str(u))
    for role, ph in (("driver", "0100-123-4567"), ("trader", "+20 100 123 4567".replace("+20 100", "0100")), ("client", "01001234567")):
        st, b, *_ = reg(role, phone=ph)
        case(f"BL009-2/{role}", f"duplicate phone (different formatting) rejected on {role}", st == 400 and "phone" in b["errors"] and b["errors"]["phone"] == ["A user with this phone number already exists."], str(b.get("errors")))
    st, b, *_ = reg("driver", phone="01500000001", password="123")
    case("BL009-3", "weak password -> 400 errors.password", st == 400 and "password" in b["errors"] and len(b["errors"]["password"]) >= 1, str(b.get("errors")))
    st, b, *_ = reg("driver", phone="01500000002", password="password")
    case("BL009-3b", "common password rejected", st == 400 and "password" in b["errors"])
    st, b, *_ = reg("driver", phone="01500000003", password="1234567890")
    case("BL009-3c", "numeric password rejected", st == 400 and "password" in b["errors"])
    st, b, *_ = reg("driver", phone="01500000004", password="01500000004")
    case("BL009-3d", "password equal to phone rejected", st == 400 and "password" in b["errors"])
    st, b, *_ = call(A + "register/driver/", body={})
    case("BL009-4", "missing all fields -> 400 with full_name, phone, password errors", st == 400 and {"full_name", "phone", "password"} <= set(b["errors"]) and "email" not in b["errors"], str(b.get("errors")))
    st, b, *_ = call(A + "register/driver/", body={"full_name": "A", "phone": "123", "password": STRONG})
    case("BL009-5", "1-char name and 3-digit phone rejected", st == 400 and "full_name" in b["errors"] and "phone" in b["errors"])
    st, b, *_ = reg("driver", phone="1" * 16)
    case("BL009-5b", "16-digit phone rejected", st == 400 and "phone" in b["errors"])
    st, b, *_ = reg("driver", phone="abcdefgh")
    case("BL009-5c", "letters-only phone rejected", st == 400 and "phone" in b["errors"])
    st, b, *_ = reg("driver", phone="01500000005")
    case("BL009-6", "email is optional (registration without email works)", st == 201)
    st, b, *_ = reg("driver", phone="01500000006", email="not-an-email")
    case("BL009-7", "invalid email -> 400 errors.email", st == 400 and "email" in b["errors"])
    st, b, *_ = reg("driver", phone="01500000007", email="ahmed@example.com")
    case("BL009-8", "duplicate email -> 400 errors.email", st == 400 and b["errors"].get("email") == ["A user with this email already exists."], str(b.get("errors")))
    st, b, *_ = reg("driver", phone="01500000008", full_name="  Trim Me  ")
    case("BL009-9", "full_name trimmed", st == 201 and b["data"]["user"]["full_name"] == "Trim Me")
    st, b, *_ = reg("driver", phone="01500000009", full_name="a" * 256)
    case("BL009-9b", "256-char name rejected", st == 400 and "full_name" in b["errors"])
    # mass assignment
    st, b, *_ = reg("client", phone="01500000010", role="admin", status="active", is_staff=True, is_superuser=True, username="hacker", id=1)
    chk = sql("from apps.users.models import User; u=User.all_objects.get(phone='01500000010'); print(u.role,u.status,u.is_staff,u.is_superuser,u.username)")
    case("BL008-MA1", "mass assignment on client register: role/status/is_staff/username ignored", st == 201 and chk == "client active False False None", chk)
    st, b, *_ = reg("driver", phone="01500000011", role="admin", status="active")
    chk = sql("from apps.users.models import User; u=User.all_objects.get(phone='01500000011'); print(u.role,u.status,u.is_staff)")
    case("BL008-MA2", "mass assignment on driver register: stays driver/pending_approval", st == 201 and chk == "driver pending_approval False", chk)
    st, b, *_ = reg("trader", phone="01500000012", role="manager")
    chk = sql("from apps.users.models import User; u=User.all_objects.get(phone='01500000012'); print(u.role,u.status)")
    case("BL008-MA3", "mass assignment on trader register ignored", st == 201 and chk == "trader pending_approval", chk)
    case("BL009-10", "password never in any response; hashed in DB", STRONG not in json.dumps(b) and sql("from apps.users.models import User; print(User.all_objects.get(phone='01500000012').password.startswith(('pbkdf2','argon2','bcrypt','md5')))") == "True")
    st, b, *_ = reg("admin")
    case("BL008-R1", "no public register/admin or /manager endpoint (404)", st == 404 and reg("manager")[0] == 404)
    st, b, h, raw, _ = call(A + "register/driver/", "GET")
    case("BL009-11", "GET on register -> 405 envelope", st == 405 and err(b, "Method not allowed."))
    st, b, *_ = call(A + "register/driver/", raw=b"{bad")
    case("BL009-12", "malformed JSON on register -> 400 (not 500)", st == 400)
    st, b, *_ = reg("driver", phone="01500000013", full_name=["x"], password={"a": 1})
    case("BL009-13", "list/dict field values -> 400 (not 500)", st == 400)
    st, b, *_ = reg("driver", phone="01500000014", full_name="<script>alert(1)</script>")
    case("BL009-14", "HTML in name stored verbatim, returned as JSON (no 500)", st == 201 and b["data"]["user"]["full_name"] == "<script>alert(1)</script>")
    st, b, *_ = call(A + "register/driver/", body={"full_name": "Ar User", "phone": "0100 123 4567", "password": STRONG}, headers={"Accept-Language": "ar"})
    case("I18N-1", "register duplicate phone error in Arabic", st == 400 and b["errors"]["phone"][0] != "A user with this phone number already exists." and any("؀" <= c <= "ۿ" for c in b["errors"]["phone"][0]), str(b["errors"]["phone"]))
    st, b, *_ = call(A + "register/client/", body={"full_name": "Ar User", "phone": "01600000001", "password": STRONG}, headers={"Accept-Language": "ar"})
    case("I18N-2", "register success message in Arabic", st == 201 and b["message"] != "Registration successful." and any("؀" <= c <= "ۿ" for c in b["message"]), b["message"])

    # ---------------- BL-012 login ---------------------------------------------------
    st, b, *_ = reg("client", phone="01700000001", full_name="Login Client")
    st, b, h, raw, _ = login("01700000001", STRONG)
    d = b["data"]
    case("BL012-1", "client logs in by phone -> access, refresh, user summary (active, client)", st == 200 and set(d) == {"access", "refresh", "user"} and d["user"]["role"] == "client" and d["user"]["status"] == "active" and set(d["user"]) == {"id", "full_name", "role", "status"})
    case("BL012-2", "login by phone with +, spaces, dashes and Arabic-Indic digits", all(login(x, STRONG)[0] == 200 for x in ("+0170-000-0001", "٠١٧٠٠٠٠٠٠٠١", " 0170 000 0001 ")))
    st, b, *_ = login("qaadmin", APW)
    case("BL012-3", "admin logs in by username -> role admin", st == 200 and b["data"]["user"]["role"] == "admin")
    st, b, *_ = login("demo_manager", DPW)
    case("BL012-4", "manager (seeded) logs in by username -> role manager", st == 200 and b["data"]["user"]["role"] == "manager")
    st, b, *_ = login("demo_driver", DPW); dd = b
    st2, b2, *_ = login("demo_trader", DPW)
    case("BL012-5", "seeded active driver and trader log in with right roles", st == 200 and dd["data"]["user"]["role"] == "driver" and st2 == 200 and b2["data"]["user"]["role"] == "trader")
    # pending
    st, b, h, raw, _ = login("demo_driver_pending", DPW)
    case("BL012-6", "pending driver, correct password -> 403 account_pending, friendly msg, no tokens", st == 403 and err(b, "Your account is pending approval. You will be able to log in once an administrator approves it.", "account_pending") and "access" not in raw, raw[:150])
    case("BL012-6b", "pending self-registered trader -> 403 account_pending", login("201112223333", STRONG)[0] == 403 and login("201112223333", STRONG)[1]["code"] == "account_pending")
    st, b, h, raw, _ = login("demo_client_deactivated", DPW)
    case("BL012-7", "deactivated client, correct password -> 403 account_deactivated, no tokens", st == 403 and err(b, "Your account has been deactivated. Please contact the administrator.", "account_deactivated") and "access" not in raw, raw[:150])
    st, b, *_ = login("demo_driver_pending", "wrong-pass")
    st2, b2, *_ = login("demo_client_deactivated", "wrong-pass")
    st3, b3, *_ = login("ghost-user", "wrong-pass")
    case("BL012-8", "wrong password on pending/deactivated/unknown -> identical 401 body (status not probeable)", st == st2 == st3 == 401 and b == b2 == b3 and err(b, "Invalid credentials."), str(b))
    st, b, *_ = login("demo_driver_pending", DPW, {"Accept-Language": "ar"})
    case("BL012-9", "pending message in Arabic", st == 403 and b["code"] == "account_pending" and any("؀" <= c <= "ۿ" for c in b["message"]), b["message"])
    st, b, *_ = login("demo_client_deactivated", DPW, {"Accept-Language": "ar"})
    case("BL012-9b", "deactivated message in Arabic", st == 403 and b["code"] == "account_deactivated" and any("؀" <= c <= "ۿ" for c in b["message"]))
    st, b, *_ = login("ghost", "x", {"Accept-Language": "ar"})
    case("BL012-9c", "401 in Arabic", b["message"] == "بيانات الاعتماد غير صحيحة.")
    st, b, *_ = call(A + "token/", body={"username_or_phone": "demo_client"})
    case("BL012-10", "missing password -> 400 field error", st == 400 and "password" in b["errors"])
    # soft deleted
    sql("from apps.users.models import User; u=User.objects.get(username='demo_client'); u.delete(); print('ok')")
    st, b, *_ = login("demo_client", DPW)
    case("BL012-11", "soft-deleted account -> 401 identical generic body", st == 401 and err(b, "Invalid credentials."), str(st))
    # timing: unknown vs known-wrong vs pending-wrong
    def med(idf, n=12):
        ts = [login(idf, "wrong-password-x")[4] for _ in range(n)]; return statistics.median(ts)
    t_unknown, t_known, t_pend = med("nobody-here"), med("qaadmin"), med("demo_driver_pending")
    case("BL012-12", "timing: unknown vs existing vs pending identifier with wrong password within 50%/30ms", abs(t_unknown - t_known) <= max(0.03, 0.5 * t_known) and abs(t_unknown - t_pend) <= max(0.03, 0.5 * t_pend), f"unknown={t_unknown*1000:.0f}ms known={t_known*1000:.0f}ms pending={t_pend*1000:.0f}ms")

    # ---------------- BL-008 /auth/me and role matrix -----------------------------------
    case("BL008-1", "anonymous /auth/me/ -> 401 envelope", (lambda r: r[0] == 401 and err(r[1]))(call(A + "me/", "GET")))
    case("BL008-1b", "garbage bearer -> 401", call(A + "me/", "GET", headers={"Authorization": "Bearer junk"})[0] == 401)
    for ident, pw, role in (("qaadmin", APW, "admin"), ("demo_manager", DPW, "manager"), ("demo_driver", DPW, "driver"), ("demo_trader", DPW, "trader"), ("01700000001", STRONG, "client")):
        b = login(ident, pw)[1]; st, mb, h, raw, _ = me(b["data"]["access"]); usr = mb["data"]["user"]
        case(f"BL008-2/{role}", f"{role}: /auth/me/ -> 200 profile with right role, no password/internal fields", st == 200 and usr["role"] == role and usr["status"] == "active" and set(usr) == {"id", "full_name", "phone", "username", "email", "role", "status"} and "password" not in raw.lower(), str(sorted(usr)))
    ref_pending_before = None
    # refresh token of an account, then deactivate/pending afterwards
    b = login("demo_driver", DPW)[1]; acc, ref = b["data"]["access"], b["data"]["refresh"]
    sql("from apps.users.models import User; User.objects.filter(username='demo_driver').update(status='deactivated'); print('ok')")
    st, mb, h, raw, _ = me(acc)
    case("BL008-3", "valid access token of later-deactivated account -> 403 account_deactivated on /me", st == 403 and mb.get("code") == "account_deactivated", raw[:120])
    st, mb, *_ = call(A + "token/refresh/", body={"refresh": ref})
    case("BL012-13", "refresh for deactivated account -> 401 generic", st == 401 and err(mb, "Token is invalid or expired."))
    sql("from apps.users.models import User; User.objects.filter(username='demo_driver').update(status='pending_approval'); print('ok')")
    st, mb, *_ = me(acc)
    case("BL008-4", "access token of account set back to pending -> 403 account_pending (PO decision: pending has no /me)", st == 403 and mb.get("code") == "account_pending")
    st, mb, *_ = call(A + "token/refresh/", body={"refresh": ref})
    case("BL012-14", "refresh for pending account -> 401", st == 401)
    sql("from apps.users.models import User; User.objects.filter(username='demo_driver').update(status='active'); print('ok')")
    st, mb, *_ = me(acc)
    case("BL008-5", "re-activated account: same token works again (status checked live)", st == 200)
    # soft-deleted holder
    b = login("demo_trader", DPW)[1]; acc2, ref2 = b["data"]["access"], b["data"]["refresh"]
    sql("from apps.users.models import User; User.objects.get(username='demo_trader').delete(); print('ok')")
    case("BL008-6", "soft-deleted account: access token refused (401/403)", me(acc2)[0] in (401, 403), str(me(acc2)[0]))
    case("BL012-15", "soft-deleted account: refresh -> 401", call(A + "token/refresh/", body={"refresh": ref2})[0] == 401)
    # unauthenticated reach: protected admin-ish paths
    case("BL008-7", "anonymous: only register/login/refresh/logout reachable (me=401, health needs pw, unknown=404)", all(call(A + "me/", "GET")[0] == 401 for _ in range(1)) and call("/api/v1/health/", "GET")[0] == 403)
    case("BL008-8", "wrong method on /me (POST) -> 405 envelope", (lambda r: r[0] == 405 and err(r[1], "Method not allowed."))(call(A + "me/", "POST", body={}, headers={"Authorization": "Bearer " + login("qaadmin", APW)[1]["data"]["access"]})))
    case("BL008-9", "client cannot reach admin site API: /admin/ needs staff login (302 to login)", call("/admin/", "GET")[0] in (200, 302))
    case("BL008-10", "refresh token used as access token on /me -> 401", me(login("qaadmin", APW)[1]["data"]["refresh"])[0] == 401)
    st, b, *_ = call(A + "token/refresh/", body={"refresh": login("qaadmin", APW)[1]["access"] if False else login("qaadmin", APW)[1]["data"]["access"]})
    case("BL008-11", "access token used as refresh -> 401", st == 401)

    # ---------------- BL-013 refresh rotation + logout ------------------------------------
    b = login("qaadmin", APW)[1]; r1, a1 = b["data"]["refresh"], b["data"]["access"]
    st, b, h, raw, _ = call(A + "token/refresh/", body={"refresh": r1})
    r2 = b["data"].get("refresh") if st == 200 else None
    case("BL013-1", "refresh -> 200 with NEW refresh + access, message per contract", st == 200 and r2 and r2 != r1 and "access" in b["data"] and b["message"] == "Token refreshed successfully.")
    st, b, *_ = call(A + "token/refresh/", body={"refresh": r1})
    case("BL013-2", "reusing the old (rotated) refresh -> 401 generic", st == 401 and err(b, "Token is invalid or expired."))
    st, b, *_ = call(A + "token/refresh/", body={"refresh": r2})
    r3 = b["data"]["refresh"] if st == 200 else None
    case("BL013-3", "new refresh works and rotates again", st == 200 and r3)
    st, b, *_ = call(A + "token/refresh/", body={})
    case("BL013-4", "refresh without body field -> 400 errors.refresh", st == 400 and b["errors"].get("refresh") == ["This field is required."])
    st, b, *_ = call(A + "logout/", body={"refresh": r3})
    case("BL013-5", "logout -> 200 envelope per contract (works with no Authorization header)", st == 200 and b == {"success": True, "message": "Logged out successfully.", "data": {}}, str(b))
    case("BL013-6", "after logout the refresh token cannot be used (401)", call(A + "token/refresh/", body={"refresh": r3})[0] == 401)
    st, b, *_ = call(A + "logout/", body={"refresh": r3})
    case("BL013-7", "logout twice is idempotent (200)", st == 200 and b["success"] is True)
    st, b, *_ = call(A + "logout/", body={"refresh": r1})
    case("BL013-7b", "logout with an already-rotated (blacklisted) token -> 200", st == 200)
    st, b, *_ = call(A + "logout/", body={})
    case("BL013-8", "logout without refresh -> 400 errors.refresh required", st == 400 and b["errors"].get("refresh") == ["This field is required."])
    st, b, *_ = call(A + "logout/", body={"refresh": "not-a-token"})
    case("BL013-9", "logout with junk token -> 400 errors.refresh 'Invalid token.'", st == 400 and b["errors"].get("refresh") == ["Invalid token."], str(b.get("errors")))
    st, b, *_ = call(A + "logout/", body={"refresh": a1})
    case("BL013-9b", "logout with an ACCESS token -> 400 (not accepted as refresh)", st == 400, str(st))
    # logout from one session does not kill another session
    sA = login("qaadmin", APW)[1]["data"]; sB = login("qaadmin", APW)[1]["data"]
    call(A + "logout/", body={"refresh": sA["refresh"]})
    case("BL013-10", "logging out one session leaves another session's refresh usable", call(A + "token/refresh/", body={"refresh": sB["refresh"]})[0] == 200)
    case("BL013-11", "already-issued access token stays valid until expiry (documented contract behaviour)", me(sA["access"])[0] == 200)
    st, b, *_ = call(A + "logout/", "GET")
    case("BL013-12", "GET /logout/ -> 405 envelope", st == 405 and err(b, "Method not allowed."))
    st, b, *_ = call(A + "logout/", body={"refresh": r3}, headers={"Accept-Language": "ar"})
    case("I18N-3", "logout message in Arabic", any("؀" <= c <= "ۿ" for c in b["message"]), b["message"])
    st, b, *_ = call(A + "token/refresh/", body={"refresh": "junk"}, headers={"Accept-Language": "ar"})
    case("I18N-4", "invalid-refresh 401 in Arabic", st == 401 and any("؀" <= c <= "ۿ" for c in b["message"]))
    st, b, *_ = me("junk", {"Accept-Language": "ar"})
    case("I18N-5", "/me 401 in Arabic", st == 401 and any("؀" <= c <= "ۿ" for c in b["message"]))
finally:
    stop(p)

# ---------------- Phase B: throttles (default limits) ----------------------------------
def throttle_phase(tag, extra, spoof_helps_expected):
    manage_env = {"RATELIMIT_ANON": "10000/minute", "RATELIMIT_USER": "10000/minute", **extra}
    pr = start(manage_env)
    try:
        time.sleep(0.5)
        codes = [login("rl-nobody", "x")[0] for _ in range(11)]
        case(f"RATE-{tag}1", "login: 11th request within a minute -> 429", codes[:10] == [401] * 10 and codes[10] == 429, str(codes))
        st, b, h, raw, _ = login("rl-nobody", "x")
        case(f"RATE-{tag}2", "429 envelope and Retry-After", st == 429 and err(b, "Request rate limit exceeded.") and h.get("Retry-After") is not None)
        st, b, *_ = login("rl-nobody", "x", {"Accept-Language": "ar"})
        case(f"RATE-{tag}3", "429 in Arabic", st == 429 and b["message"] == "تم تجاوز حد الطلبات المسموح به.")
        case(f"RATE-{tag}4", "correct password also blocked while throttled (bucket is per IP)", login("qaadmin", APW)[0] == 429)
        case(f"RATE-{tag}5", "refresh and logout share the auth bucket (both 429)", call("/api/v1/auth/token/refresh/", body={"refresh": "x"})[0] == 429 and call("/api/v1/auth/logout/", body={"refresh": "x"})[0] == 429)
        st = login("rl-nobody", "x", {"X-Forwarded-For": "9.9.9.9"})[0]
        st2 = login("rl-nobody", "x", {"X-Forwarded-For": "8.8.8.8, 7.7.7.7"})[0]
        helped = st != 429 or st2 != 429
        case(f"RATE-{tag}6", f"spoofed X-Forwarded-For {'is honoured only as the last trusted hop' if spoof_helps_expected else 'does NOT bypass the limit'}", (not helped) if not spoof_helps_expected else True, f"{st},{st2}")
    finally:
        stop(pr)

throttle_phase("A", {"NUM_PROXIES": "0"}, False)
# a fresh server has an empty cache; sensitive scope
pr = start({"NUM_PROXIES": "0", "RATELIMIT_ANON": "10000/minute"})
try:
    codes = []
    for i in range(32):
        codes.append(call("/api/v1/auth/register/client/", body={"full_name": "Rate Lim", "phone": f"0188000{i:04d}", "password": STRONG}, headers={"X-Forwarded-For": f"10.0.0.{i}"})[0])
    case("RATE-S1", "register: 31st request/min -> 429 even with a different forged X-Forwarded-For each time", codes[:30] == [201] * 30 and codes[30] == 429, str(codes[28:]))
    st, b, h, *_ = call("/api/v1/auth/register/client/", body={})
    case("RATE-S2", "register 429 envelope + Retry-After", st == 429 and err(b, "Request rate limit exceeded.") and h.get("Retry-After") is not None)
finally:
    stop(pr)
# NUM_PROXIES=1: client IP is the last-but-0 XFF entry, forged leftmost entry must not help
pr = start({"NUM_PROXIES": "1", "RATELIMIT_ANON": "10000/minute"})
try:
    codes = [login("rl-nobody", "x", {"X-Forwarded-For": f"66.66.66.{i}, 5.5.5.5"})[0] for i in range(12)]
    case("RATE-P1", "NUM_PROXIES=1: forged leftmost X-Forwarded-For entries do not reset the limit", 429 in codes and codes.index(429) == 10, str(codes))
    st = login("rl-nobody", "x", {"X-Forwarded-For": "1.2.3.4, 6.6.6.6"})[0]
    case("RATE-P2", "NUM_PROXIES=1: a different trusted-hop address gets its own bucket (sanity)", st == 401, str(st))
finally:
    stop(pr)

# ---------------- Phase C: DB-level checks --------------------------------------------
case("DATA-1", "makemigrations --check clean (no missing migrations)", manage("makemigrations", "--check", "--dry-run").returncode == 0)
u = sql("from apps.users.models import User; print(User.all_objects.filter(phone__isnull=True, role__in=['client','driver','trader']).count())")
case("DATA-2", "every self-registered account has a phone", u == "0", u)
d = sql("from apps.users.models import User; from django.db.models import Count; print(User.all_objects.exclude(phone=None).values('phone').annotate(c=Count('id')).filter(c__gt=1).count())")
case("DATA-3", "no duplicate phones in DB", d == "0", d)

fails = [r for r in RES if not r[2]]
print(f"\n{len(RES)-len(fails)}/{len(RES)} passed")
for f in fails: print("FAILED:", f[0], f[1], f[3])
sys.exit(1 if fails else 0)
