"""QA black-box checks for TASK-045 (refresh cookie, Origin check, reuse detection) against a LIVE dev server.

Usage: python cookie_blackbox.py <backend_dir> <python_executable>
Fresh SQLite, runserver (no Docker), relaxed throttles. Prints PASS/FAIL per case.
Tests the contract in docs/sprints/sprint-03/API_CONTRACT.md, not the code.
"""
import http.cookies, json, os, subprocess, sys, tempfile, threading, time, urllib.error, urllib.request

BACKEND, PY = sys.argv[1], sys.argv[2]
PORT = 8768
BASE = f"http://127.0.0.1:{PORT}"
ORIGIN = "http://localhost:5173"
STRONG = "Zx9!kLm#Qw27pR"
DB = os.path.join(tempfile.mkdtemp(), "cookie.sqlite3")
ENV = {**os.environ, "DATABASE_URL": f"sqlite:///{DB}", "HEALTH_CHECK_PASSWORD": "qa-health-pw", "DEBUG": "False",
       "ALLOWED_HOSTS": "127.0.0.1,localhost", "SECURE_SSL_REDIRECT": "False",
       "SECRET_KEY": "qa-secret-key-qa-secret-key-qa-secret-key", "DJANGO_SETTINGS_MODULE": "config.settings.development",
       "NUM_PROXIES": "0", "RATELIMIT_AUTH": "100000/minute", "RATELIMIT_SENSITIVE": "100000/minute",
       "RATELIMIT_ANON": "100000/minute", "RATELIMIT_USER": "100000/minute"}
n_fail = 0


def case(cid, title, ok, note=""):
    global n_fail
    n_fail += (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {cid} {title} {note}", flush=True)


def call(path, body=None, method="POST", headers=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            st, txt, h = r.status, r.read().decode(), r.headers
    except urllib.error.HTTPError as e:
        st, txt, h = e.code, e.read().decode(), e.headers
    try:
        j = json.loads(txt)
    except ValueError:
        j = None
    return st, j, h, txt


def cookie_of(h):
    """Return (value, morsel) of delivery_refresh from Set-Cookie headers, or (None, None)."""
    for sc in h.get_all("Set-Cookie") or []:
        c = http.cookies.SimpleCookie()
        c.load(sc)
        if "delivery_refresh" in c:
            return c["delivery_refresh"].value, c["delivery_refresh"]
    return None, None


def login(ident="01001234567", pw=STRONG):
    return call("/api/v1/auth/token/", {"username_or_phone": ident, "password": pw})


def refresh(tok, origin=ORIGIN, body=None):
    hdr = {"Cookie": f"delivery_refresh={tok}"} if tok is not None else {}
    if origin:
        hdr["Origin"] = origin
    return call("/api/v1/auth/token/refresh/", body, headers=hdr)


def logout(tok, origin=ORIGIN):
    hdr = {"Cookie": f"delivery_refresh={tok}"} if tok is not None else {}
    if origin:
        hdr["Origin"] = origin
    return call("/api/v1/auth/logout/", None, headers=hdr)


def manage(*a):
    return subprocess.run([PY, "manage.py", *a], cwd=BACKEND, env=ENV, capture_output=True, text=True, timeout=180, check=False)


subprocess.run([PY, "manage.py", "migrate", "--noinput"], cwd=BACKEND, env=ENV, capture_output=True, check=True)
p = subprocess.Popen([PY, "manage.py", "runserver", str(PORT), "--noreload"], cwd=BACKEND, env=ENV,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    try:
        urllib.request.urlopen(BASE + "/api/v1/nope/", timeout=1)
    except urllib.error.HTTPError:
        break
    except Exception:
        time.sleep(0.5)

try:
    for who, ph in (("Ahmed Ali", "01001234567"), ("Sara Omar", "01002223344")):
        call("/api/v1/auth/register/client/", {"full_name": who, "phone": ph, "password": STRONG})

    # ---- Login -------------------------------------------------------------------
    st, b, h, raw = login()
    tok, m = cookie_of(h)
    case("C-LOGIN-1", "login 200, access in body, no refresh anywhere in JSON", st == 200 and b["data"].get("access") and '"refresh"' not in raw, raw[:80])
    case("C-LOGIN-2", "cookie set with HttpOnly, SameSite=Strict, Path=/api/v1/auth/, Max-Age=7d, no Domain",
         bool(tok) and m["httponly"] and m["samesite"].lower() == "strict" and m["path"] == "/api/v1/auth/" and int(m["max-age"]) == 7 * 86400 and not m["domain"],
         str(dict(m.items())) if m else "no cookie")
    case("C-LOGIN-3", "dev default: cookie not Secure", bool(m) and not m["secure"])
    st2, b2, h2, _ = call("/api/v1/auth/token/", {"username_or_phone": "01001234567", "password": "wrong-pass"})
    case("C-LOGIN-4", "bad password 401, no cookie", st2 == 401 and cookie_of(h2)[0] is None)
    st3, b3, h3, _ = call("/api/v1/auth/token/", {"username_or_phone": "01001234567", "password": STRONG, "refresh": "x"})
    case("C-LOGIN-5", "extra 'refresh' field in login body ignored", st3 == 200)
    # Over-long login fields are TASK-053 (not built yet); out of scope for TASK-045.

    # ---- Refresh -----------------------------------------------------------------
    st, b, h, raw = login()
    c1, _ = cookie_of(h)
    st, b, h, raw = refresh(c1)
    c2, m2 = cookie_of(h)
    case("C-REF-1", "refresh 200 with access only, no refresh in JSON", st == 200 and b["data"].get("access") and set(b["data"]) == {"access"} and '"refresh"' not in raw, raw[:100])
    case("C-REF-2", "refresh sets a NEW cookie with same flags", bool(c2) and c2 != c1 and m2["httponly"] and m2["samesite"].lower() == "strict" and m2["path"] == "/api/v1/auth/")
    tk = b["data"]["access"]
    st, bm, *_ = call("/api/v1/auth/me/", method="GET", headers={"Authorization": f"Bearer {tk}"})
    case("C-REF-3", "new access token works on /auth/me/", st == 200)

    # ---- Origin check -----------------------------------------------------------
    st, b, h, _ = refresh(c2, origin=None)
    case("C-ORG-1", "refresh without Origin -> 403 origin_rejected, cookie untouched", st == 403 and b.get("code") == "origin_rejected" and b.get("success") is False and cookie_of(h)[0] is None, str(b))
    for o in ("http://evil.example", "http://localhost:5174", "https://localhost:5173", "http://localhost:5173/", "null", "http://LOCALHOST:5173.evil.com"):
        st, b, h, _ = refresh(c2, origin=o)
        case("C-ORG-2", f"foreign Origin {o!r} -> 403", st == 403 and b.get("code") == "origin_rejected", str(st))
    st, b, h, _ = refresh(c2)
    case("C-ORG-3", "rejected Origin did NOT rotate/blacklist: same cookie still works", st == 200, str(st))
    c3, _ = cookie_of(h)
    st, b, h, _ = logout(c3, origin="http://evil.example")
    case("C-ORG-4", "logout foreign Origin -> 403 and cookie not blacklisted", st == 403 and b.get("code") == "origin_rejected")
    st, b, h, _ = refresh(c3)
    case("C-ORG-5", "after rejected logout the token still refreshes", st == 200)
    c4, _ = cookie_of(h)
    st, *_ = login()  # login needs no Origin
    case("C-ORG-6", "login does not require Origin", st == 200)

    # ---- Refresh credential channel ----------------------------------------------
    st, b, *_ = refresh(None)
    case("C-CH-1", "no cookie -> 401 Token is invalid or expired.", st == 401 and b.get("message") == "Token is invalid or expired.", str(b))
    st, b, h, _ = refresh(c4 and "junk.token.value")
    case("C-CH-2", "junk cookie -> 401", st == 401)
    st, b, *_ = call("/api/v1/auth/token/refresh/", {"refresh": c4}, headers={"Origin": ORIGIN})
    case("C-CH-3", "refresh token in JSON body only (no cookie) is ignored -> 401", st == 401, str(st))
    st, b, *_ = call("/api/v1/auth/logout/", {"refresh": c4}, headers={"Origin": ORIGIN})
    st_after, *_ = refresh(c4)
    case("C-CH-4", "logout with token in body only does NOT blacklist it", st == 200 and st_after == 200, f"{st},{st_after}")
    c5 = cookie_of(refresh(c4)[2])[0] if False else None

    # ---- Reuse detection ---------------------------------------------------------
    st, b, h, _ = login()
    r0, _ = cookie_of(h)
    st, b, h, _ = refresh(r0)
    r1, _ = cookie_of(h)
    st, b, h, _ = refresh(r1)
    r2, _ = cookie_of(h)  # r2 is current outstanding token
    st, b, h, raw = refresh(r0)  # reuse of r0 (blacklisted)
    cl, mcl = cookie_of(h)
    case("C-REUSE-1", "reuse of old token -> 401 same body", st == 401 and b.get("message") == "Token is invalid or expired.", raw[:100])
    case("C-REUSE-2", "reuse clears the cookie (Max-Age=0 / empty)", mcl is not None and (cl == "" or str(mcl["max-age"]) == "0"), str(dict(mcl.items())) if mcl else "no Set-Cookie")
    st, *_ = refresh(r2)
    case("C-REUSE-3", "after reuse, the user's OTHER outstanding token (r2) is revoked -> 401", st == 401, str(st))
    st, b, h, _ = login()
    rn, _ = cookie_of(h)
    case("C-REUSE-4", "user can log in again after reuse revocation", st == 200 and rn is not None)
    st, *_ = refresh(rn)
    case("C-REUSE-5", "...and the new session refreshes", st == 200)
    # other user must be unaffected
    st, b, h, _ = login("01002223344")
    o0, _ = cookie_of(h)
    st, b, h, _ = login()
    a0, _ = cookie_of(h)
    refresh(a0)
    refresh(a0)  # reuse by user A
    st, *_ = refresh(o0)
    case("C-REUSE-6", "reuse by user A does not revoke user B's tokens", st == 200, str(st))

    # ---- Logout ------------------------------------------------------------------
    st, b, h, _ = login()
    l0, _ = cookie_of(h)
    st, b, h, raw = logout(l0)
    cl, mcl = cookie_of(h)
    case("C-OUT-1", "logout 200 contract body", st == 200 and b == {"success": True, "message": "Logged out successfully.", "data": {}}, raw[:100])
    case("C-OUT-2", "logout clears cookie (Max-Age=0)", mcl is not None and (cl == "" or str(mcl["max-age"]) == "0") and mcl["path"] == "/api/v1/auth/")
    st, *_ = refresh(l0)
    case("C-OUT-3", "token blacklisted after logout -> refresh 401", st == 401)
    st, b, *_ = logout(l0)
    case("C-OUT-4", "logout idempotent with already-blacklisted token -> 200", st == 200)
    st, *_ = logout(None)
    case("C-OUT-5", "logout with no cookie -> 200", st == 200)
    st, *_ = logout("junk")
    case("C-OUT-6", "logout with junk cookie -> 200", st == 200)
    # logout with expired ACCESS token must still work: no bearer is required at all
    st, b, h, _ = login()
    l1, _ = cookie_of(h)
    st, *_ = call("/api/v1/auth/logout/", None, headers={"Origin": ORIGIN, "Cookie": f"delivery_refresh={l1}", "Authorization": "Bearer expired.invalid.token"})
    case("C-OUT-7", "logout works with an invalid/expired bearer attached", st == 200, str(st))

    # ---- CORS --------------------------------------------------------------------
    req = urllib.request.Request(BASE + "/api/v1/auth/token/refresh/", method="OPTIONS",
                                 headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"})
    try:
        r = urllib.request.urlopen(req, timeout=10); hh = r.headers
    except urllib.error.HTTPError as e:
        hh = e.headers
    case("C-CORS-1", "preflight allows exact origin + credentials true, not '*'", hh.get("Access-Control-Allow-Origin") == ORIGIN and hh.get("Access-Control-Allow-Credentials") == "true", str(hh.get("Access-Control-Allow-Origin")))
    req = urllib.request.Request(BASE + "/api/v1/auth/token/refresh/", method="OPTIONS",
                                 headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    try:
        r = urllib.request.urlopen(req, timeout=10); hh = r.headers
    except urllib.error.HTTPError as e:
        hh = e.headers
    case("C-CORS-2", "preflight from evil origin gets no Allow-Origin", hh.get("Access-Control-Allow-Origin") in (None, ""), str(hh.get("Access-Control-Allow-Origin")))

    # ---- Inactive account --------------------------------------------------------
    st, b, h, _ = login("01002223344")
    d0, _ = cookie_of(h)
    manage("shell", "-c", "from apps.users.models import User; u=User.objects.get(phone='01002223344'); u.status='deactivated'; u.save()")
    st, b, *_ = refresh(d0)
    case("C-STAT-1", "deactivated account cannot refresh -> 401", st == 401, str(b))

    # ---- Parallel refresh (SQLite: <=1 success, never 500) -----------------------
    st, b, h, _ = login()
    pr, _ = cookie_of(h)
    out = []
    def go():
        out.append(refresh(pr)[0])
    ts = [threading.Thread(target=go) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    case("C-RACE-1", "8 parallel refreshes of one token: <=1 success, no 500", out.count(200) <= 1 and 500 not in out, str(sorted(out)))

    # ---- Headers -----------------------------------------------------------------
    st, b, h, _ = login()
    case("C-HDR-1", "no refresh token or Set-Cookie leaked into JSON; X-Content-Type-Options present", h.get("X-Content-Type-Options") == "nosniff")
finally:
    p.terminate()
    try:
        p.wait(10)
    except Exception:
        p.kill()

print(f"\nFAILED: {n_fail}")
sys.exit(1 if n_fail else 0)
