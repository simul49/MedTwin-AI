#!/usr/bin/env python3
"""End-to-end API smoke test.

Usage:  ./.venv/bin/python tests/api_smoke.py [BASE_URL]
Default BASE_URL: http://127.0.0.1:8001/api/v1
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001/api/v1"
PASSWORD = "MedTwin@2026"

failures = 0


class Session:
    def __init__(self):
        self.cookies = {}
        self.csrf = ""

    def _merge(self, headers):
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if self.csrf:
            headers["X-CSRFToken"] = self.csrf

    def _store(self, resp):
        headers = getattr(resp, "headers", None)
        if headers is None:
            return
        for header in headers.get_all("Set-Cookie") or []:
            first = header.split(";", 1)[0]
            if "=" not in first:
                continue
            k, v = first.split("=", 1)
            if k.lower() in ("path", "domain", "expires", "max-age", "samesite", "secure", "httponly"):
                continue
            self.cookies[k] = v

    def request(self, method, path, body=None, expect=None, label=None):
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        self._merge(headers)
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self._store(resp)
                code, raw = resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            self._store(exc)
            code, raw = exc.code, exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw[:120]
        if expect is not None and code != expect:
            global failures
            failures += 1
            print(f"  !! {label or path}: expected {expect}, got {code}: {str(payload)[:90]}")
        return code, payload

    def get(self, path, expect=200, label=None):
        return self.request("GET", path, expect=expect, label=label)

    def post(self, path, body, expect=200, label=None):
        return self.request("POST", path, body=body, expect=expect, label=label)


def section(title):
    print(f"\n== {title} ==")


def refresh_csrf(s):
    _, d = s.get("/auth/csrf/")
    s.csrf = d["csrfToken"] if isinstance(d, dict) and "csrfToken" in d else s.cookies.get("csrftoken", "")


def login(s, email):
    refresh_csrf(s)
    _, d = s.post("/auth/login/", {"email": email, "password": PASSWORD},
                  expect=200, label=f"login {email}")
    name = d.get("name", "?") if isinstance(d, dict) else "?"
    role = d.get("role", "?") if isinstance(d, dict) else "?"
    print(f"  login {email:24} {name} ({role})")
    refresh_csrf(s)


def show(path, d):
    n = len(d["results"]) if isinstance(d, dict) and "results" in d else "?"
    print(f"  {path:32} 200  results={n}")


def main():
    # ---------------- health ----------------
    section("HEALTH")
    s = Session()
    code, d = s.get("/health/", label="health")
    print(f"  health {code}  database={d.get('database')}  provider={d['aiProvider']['name']}")

    # ---------------- patient ----------------
    section("PATIENT")
    p = Session()
    login(p, "patient@medtwin.dev")
    _, d = p.get("/patient/digital-twin/")
    print(f"  twin {d['counts']}")
    for path in ["/patient/records/", "/patient/timeline/", "/patient/documents/",
                 "/patient/observations/", "/patient/medications/", "/patient/allergies/",
                 "/consent/grants/", "/doctors/", "/appointments/", "/notifications/",
                 "/conversations/", "/recommendations/", "/ai/history/"]:
        code, d = p.get(path, expect=200, label=path)
        show(path, d)

    for label, msg, check in [
        ("explain term", "What does my HbA1c result mean?", {"EXPLAIN_TERM", "LAB_RESULT"}),
        ("emergency", "I have crushing chest pain and shortness of breath", {"ESCALATION"}),
        ("out of scope", "Change my metformin dose to double", None),
    ]:
        _, d = p.post("/ai/chat/", {"message": msg}, label=f"chat {label}")
        print(f"  chat {label:14} intent={d['intent']} risk={d['riskCategory']} "
              f"trust={d['safety']['score']} sources={len(d.get('sources', []))}")
        if check and d["intent"] not in check:
            global failures
            failures += 1
            print(f"    !! expected intent in {check}")
        if label == "emergency":
            print(f"    answer: {d['answer'][:110]}")

    # ---------------- doctor ----------------
    section("DOCTOR")
    dr = Session()
    login(dr, "doctor@medtwin.dev")
    _, d = dr.get("/doctor/authorized-patients/")
    results = d["results"]
    print(f"  authorised patients: {len(results)}")
    first = results[0]
    pid = first["patient"]["id"] if "patient" in first else first["id"]
    _, d = dr.get(f"/doctor/patients/{pid}/summary/")
    print(f"  summary {pid[:8]}  patient={d['patient']['name']}  "
          f"records={len(d['records'])} obs={len(d['observations'])}")
    _, d = dr.get(f"/doctor/patients/{pid}/documents/")
    show(f"doctor documents {pid[:8]}", d)
    _, d = dr.get(f"/doctor/patients/{pid}/timeline/")
    show(f"doctor timeline {pid[:8]}", d)
    _, d = dr.post("/safety/evaluate/",
                   {"answer": "Take twice your usual metformin dose tonight. This will definitely fix it."})
    print(f"  safety evaluate   score={d['score']} labels={d['labels']}")

    # ---------------- admin ----------------
    section("ADMIN")
    ad = Session()
    login(ad, "admin@medtwin.dev")
    _, d = ad.get("/admin/users/")
    show("/admin/users/", d)
    _, d = ad.get("/admin/audit-logs/")
    show("/admin/audit-logs/", d)
    _, d = ad.get("/admin/consent-grants/")
    show("/admin/consent-grants/", d)
    _, d = ad.get("/admin/knowledge-sources/")
    show("/admin/knowledge-sources/", d)
    _, d = ad.get("/admin/feature-flags/")
    show("/admin/feature-flags/", d)
    _, d = ad.get("/admin/system/health/")
    print(f"  system health     db={d['database']} users={d['counts']['users']} "
          f"chunks={d['counts']['knowledgeChunks']} models={d['models']}")

    # ---------------- authorisation / IDOR ----------------
    section("AUTHORISATION")
    code, _ = Session().get("/patient/digital-twin/", expect=403, label="anon twin")
    print(f"  anonymous twin -> {code} (expect 401/403)")
    code, _ = dr.get("/admin/users/", expect=403, label="doctor hits admin")
    print(f"  doctor hits /admin/users -> {code} (expect 403)")
    code, _ = p.get("/admin/users/", expect=403, label="patient hits admin")
    print(f"  patient hits /admin/users -> {code} (expect 403)")
    code, _ = dr.get("/doctor/patients/00000000-0000-0000-0000-000000000000/summary/",
                     expect=404, label="ungranted patient")
    print(f"  ungranted patient ID -> {code} (expect 404)")

    print(f"\n{'PASS' if failures == 0 else f'FAIL ({failures})'} — core flows verified")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
