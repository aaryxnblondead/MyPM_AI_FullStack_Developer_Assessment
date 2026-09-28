"""Live full pipeline check. Needs backend running with GEMINI_API_KEY funded."""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"


def call(method: str, path: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"body": e.read().decode()[:500]}


def main() -> None:
    status, out = call("POST", "/api/evaluations", {
        "candidate_name": "Riya Shah",
        "target_role": "Customer Success Manager",
        "resume_text": "Riya Shah has five years of B2B SaaS customer success experience. She has managed 25 client accounts, used HubSpot and improved customer retention by 12 percent.",
        "company_name": "Acme",
        "job_title": "Enterprise CSM",
        "job_description": "Enterprise Customer Success Manager. Needs five years of experience, Salesforce, enterprise renewals, and experience supporting US customers.",
    })
    print(f"POST /api/evaluations -> {status}")
    if status != 200:
        print(out)
        print("FAIL: live eval needs funded GEMINI_API_KEY and running backend.")
        sys.exit(1)
    print(f"fit={out.get('fit_category')} score={out.get('fit_score')}")
    for r in out.get("per_requirement", []):
        print(r["requirement_id"], r["verdict"], len(r.get("evidence", [])))
    print("live eval ok")


if __name__ == "__main__":
    main()
