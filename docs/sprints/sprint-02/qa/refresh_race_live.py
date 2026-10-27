"""QA live cases for TASK-041 (atomic refresh rotation, VULN-011) against a LIVE dev server.

Usage: python refresh_race_live.py <backend_dir> <python_executable>
Fresh SQLite, runserver (threaded, no Docker), relaxed throttles.
NOTE: strict "exactly one 200" is PostgreSQL-only and is NOT asserted here (SQLite: <=1 200, never 500).
"""
import json, os, subprocess, sys, tempfile, threading, time, urllib.error, urllib.request

BACKEND, PY = sys.argv[1], sys.argv[2]
PORT = 8767
BASE = f"http://127.0.0.1:{PORT}"
PW = "Demo!Pass#2468"
DB = os.path.join(tempfile.mkdtemp(), "race.sqlite3")
ENV = {**os.environ, "DATABASE_URL": f"sqlite:///{DB}", "HEALTH_CHECK_PASSWORD": "qa-health-pw", "DEBUG": "False",
       "ALLOWED_HOSTS": "127.0.0.1,localhost", "SECURE_SSL_REDIRECT": "False",
       "SECRET_KEY": "qa-secret-key-qa-secret-key-qa-secret-key", "DJANGO_SETTINGS_MODULE": "config.settings.development",
       "NUM_PROXIES": "0", "RATELIMIT_AUTH": "100000/minute", "RATELIMIT_SENSITIVE": "100000/minute",
       "RATELIMIT_ANON": "100000/minute", "RATELIMIT_USER": "100000/minute", "DEMO_PASSWORD": PW}
n_fail = 0
def case(cid, title, ok, note=""):
    global n_fail; n_fail += (not ok); print(f"{'PASS' if ok else 'FAIL'} {cid} {title} {note}", flush=True)
def call(path, body=None, method="POST", headers=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: st, txt = r.status, r.read().decode()
    except urllib.error.HTTPError as e: st, txt = e.code, e.read().decode()
    try: j = json.loads(txt)
    except ValueError: j = None
    return st, j
def manage(*a): return subprocess.run([PY, "manage.py", *a], cwd=BACKEND, env={**ENV, "DEBUG": "True"}, capture_output=True, text=True, timeout=180)
def login(): return call("/api/v1/auth/token/", {"username_or_phone": "demo_driver", "password": PW})
def refresh(t): return call("/api/v1/auth/token/refresh/", {"refresh": t})
def me(a): return call("/api/v1/auth/me/", method="GET", headers={"Authorization": f"Bearer {a}"})
def tokens():
    st, j = login(); d = j.get("data", j)
    return d["access"], d["refresh"]
def race(tok, n):
    out = [None] * n; bar = threading.Barrier(n)
    def w(i):
        bar.wait(); out[i] = refresh(tok)
    ts = [threading.Thread(target=w, args=(i,)) for i in range(n)]
    [t.start() for t in ts]; [t.join() for t in ts]
    return out
def new_pair(j):
    d = (j or {}).get("data", j) or {}
    return d.get("access"), d.get("refresh")

assert manage("migrate", "--noinput").returncode == 0
assert manage("seed_demo").returncode == 0
p = subprocess.Popen([PY, "manage.py", "runserver", str(PORT), "--noreload"], cwd=BACKEND, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try: urllib.request.urlopen(BASE + "/api/v1/nope/", timeout=1)
        except urllib.error.HTTPError: break
        except Exception: time.sleep(0.5)
    # Sequential regressions
    a, r = tokens()
    st, j = refresh(r); a2, r2 = new_pair(j)
    case("ROT-1", "normal rotation: 200 with new access + refresh, both differ", st == 200 and a2 and r2 and r2 != r)
    case("ROT-2", "new access token works on /auth/me/", me(a2)[0] == 200)
    case("ROT-3", "sequential reuse of old refresh -> 401 generic envelope", (lambda x: x[0] == 401 and x[1].get("success") is False)(refresh(r)))
    st3, j3 = refresh(r2); a3, r3 = new_pair(j3)
    case("ROT-4", "chain: rotated token rotates again (200)", st3 == 200 and r3)
    case("ROT-5", "reuse of r2 afterwards -> 401", refresh(r2)[0] == 401)
    # Logout regressions
    a, r = tokens()
    case("LOG-1", "logout 200/204", call("/api/v1/auth/logout/", {"refresh": r}, headers={"Authorization": f"Bearer {a}"})[0] in (200, 204))
    case("LOG-2", "refresh after logout -> 401", refresh(r)[0] == 401)
    case("LOG-3", "logout twice idempotent", call("/api/v1/auth/logout/", {"refresh": r}, headers={"Authorization": f"Bearer {a}"})[0] in (200, 204))
    a, r = tokens(); st, j = refresh(r); _, rn = new_pair(j)
    case("LOG-4", "logout with the old (rotated) token is idempotent success", call("/api/v1/auth/logout/", {"refresh": r}, headers={"Authorization": f"Bearer {a}"})[0] in (200, 204))
    case("LOG-5", "logout kills the new token; refresh with it -> 401", (call("/api/v1/auth/logout/", {"refresh": rn})[0] in (200, 204)) and refresh(rn)[0] == 401)
    case("ERR-1", "garbage refresh -> 401", refresh("not-a-token")[0] == 401)
    # Parallel races
    summary = []
    for rnd in range(1, 6):
        for n in (10, 20):
            a, r = tokens(); res = race(r, n)
            codes = sorted(x[0] for x in res); wins = [x for x in res if x[0] == 200]
            summary.append((rnd, n, codes.count(200), codes.count(401), codes.count(500)))
            case(f"RACE-{rnd}.{n}a", f"{n} parallel refreshes: no 500 and no other non-200/401 codes", set(codes) <= {200, 401}, str(dict((c, codes.count(c)) for c in set(codes))))
            case(f"RACE-{rnd}.{n}b", f"{n} parallel refreshes: at most one 200", len(wins) <= 1, f"200s={len(wins)}")
            case(f"RACE-{rnd}.{n}c", "old token refused after the race (401)", refresh(r)[0] == 401)
            for st, j in res:
                if st == 401: assert j and j.get("success") is False
            if wins:
                wa, wr = new_pair(wins[0][1])
                case(f"RACE-{rnd}.{n}d", "winner's new access works", me(wa)[0] == 200)
                s2, j2 = refresh(wr)
                case(f"RACE-{rnd}.{n}e", "winner's new refresh rotates (200)", s2 == 200)
            else:
                # no winner is tolerated on SQLite; token must then still be... (it was refused above, so note it)
                print(f"NOTE RACE-{rnd}.{n}: zero winners (SQLite tolerated); old token check above shows state", flush=True)
    print("SUMMARY (round, n, #200, #401, #500):", summary)
    print("NOT RUN: strict exactly-one-200 assertion (PostgreSQL only).")
finally:
    p.terminate()
    try: p.wait(10)
    except Exception: p.kill()
print(f"FAILS={n_fail}")
