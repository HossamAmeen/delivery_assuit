import json,urllib.request,urllib.error
B="http://127.0.0.1:8795"
def call(path,method="POST",body=None,raw=None,ct="application/json",h=None):
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    hd={**({"Content-Type":ct} if ct else {}),**(h or {})}
    r=urllib.request.Request(B+path,data=data,method=method,headers=hd)
    try: x=urllib.request.urlopen(r,timeout=10); st,b=x.status,x.read().decode()
    except urllib.error.HTTPError as e: st,b=e.code,e.read().decode()
    try: j=json.loads(b)
    except Exception: j=None
    return st,j,b
L="/api/v1/auth/token/"; P="Edge!Str0ng#Pass1"
def lg(u,p=P,**k): return call(L,body={"username_or_phone":u,"password":p},**k)
cases=[]
def chk(name,ok,note=""): cases.append(ok); print("PASS" if ok else "FAIL",name,note)
st,j,_=lg("edgeadmin"); chk("login ok",st==200)
refresh=j["data"]["refresh"]
chk("unicode username",lg("Ünï_user")[0]==200)
chk("username is case-sensitive (EDGEADMIN rejected)",lg("EDGEADMIN")[0]==401)
chk("whitespace around identifier trimmed",lg("  edgeadmin  ")[0]==200)
chk("phone login",lg("01099998888")[0]==200)
chk("phone with spaces rejected cleanly (401, not 500)",lg("0109 9998888")[0]==401)
chk("soft-deleted user cannot log in",lg("deleted")[0]==401)
chk("password with trailing space is a different password",lg("edgeadmin",P+" ")[0]==401)
chk("empty strings -> 400",lg("","")[0]==400)
chk("null values -> 400",call(L,body={"username_or_phone":None,"password":None})[0]==400)
chk("numbers instead of strings handled (no 500)",call(L,body={"username_or_phone":123,"password":456})[0] in (400,401))
chk("list/dict values handled (no 500)",call(L,body={"username_or_phone":["a"],"password":{"x":1}})[0]==400)
st,j,b=call(L,raw=b"{not json",); chk("malformed JSON -> 400 envelope",st==400 and j and j["success"] is False,b[:80])
chk("empty body -> 400",call(L,raw=b"")[0]==400)
st,j,_=call(L,raw=b"a=1&b=2",ct="application/x-www-form-urlencoded"); chk("form-encoded body handled (no 500)",st in (400,401,415),str(st))
st,j,_=call(L,raw=b"{}",ct="text/plain"); chk("wrong content type -> 415 envelope",st==415 and j and j["success"] is False,str(st))
st,j,_=call(L,raw=json.dumps({"username_or_phone":"x","password":"y"*1000000}).encode()); chk("1 MB password handled (no 500/timeouts)",st in (400,401,413),str(st))
chk("GET on token endpoint -> 405 envelope",call(L,method="GET")[0]==405)
chk("PUT/DELETE -> 405",call(L,method="PUT",body={})[0]==405 and call(L,method="DELETE")[0]==405)
chk("OPTIONS works (CORS preflight)",call(L,method="OPTIONS",h={"Origin":"http://localhost:5173","Access-Control-Request-Method":"POST"})[0]==200)
chk("refresh with access token rejected",call("/api/v1/auth/token/refresh/",body={"refresh":lg("edgeadmin")[1]["data"]["access"]})[0]==401)
chk("refresh valid",call("/api/v1/auth/token/refresh/",body={"refresh":refresh})[0]==200)
chk("refresh empty -> 400",call("/api/v1/auth/token/refresh/",body={"refresh":""})[0]==400)
# a deleted user's refresh token
d=lg("edgeadmin")  # sanity
chk("trailing slash missing redirects or 404 cleanly",call("/api/v1/auth/token",body={})[0] in (301,308,404,400,405),"")
chk("health: query param password with special chars handled",call("/api/v1/health/?password=%00%27",method="GET")[0]==403)
chk("health: very long token header handled",call("/api/v1/health/",method="GET",h={"X-Health-Check-Token":"a"*8000})[0] in (403,400,431))
chk("health: unicode token handled (no 500)",call("/api/v1/health/",method="GET",h={"X-Health-Check-Token":"é".encode("latin-1").decode("latin-1")})[0]==403)
chk("HEAD on health",call("/api/v1/health/",method="HEAD",h={"X-Health-Check-Token":"edge-health"})[0] in (200,405))
chk("unknown language header values safe",call("/api/v1/health/",method="GET",h={"X-Health-Check-Token":"edge-health","Accept-Language":"zz-ZZ;q=abc,,;;"})[0]==200)
st,j,_=call("/api/v1/health/",method="GET",h={"X-Health-Check-Token":"edge-health","Accept-Language":"ar-EG;q=0.9,en;q=0.8"}); chk("quality-valued language",j["message"]=="الخدمة تعمل بشكل سليم.")
chk("404 on deep unknown path under /api/ is envelope",call("/api/v9/x/y/z",method="GET")[1] and call("/api/v9/x/y/z",method="GET")[1]["success"] is False)
print(f"{sum(cases)}/{len(cases)} passed")
