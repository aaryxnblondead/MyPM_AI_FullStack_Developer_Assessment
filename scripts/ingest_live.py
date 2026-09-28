"""Live ingest check with a small synthetic resume. Needs GEMINI_API_KEY."""
import json
import sys
import urllib.request

BASE = "http://localhost:8000"

RESUME = """Riya Shah
B2B SaaS Customer Success, five years.
Managed 25 client accounts. Used HubSpot.
Improved customer retention by 12 percent."""

JD = """Enterprise Customer Success Manager.
Needs five years of experience, Salesforce, enterprise renewals,
and experience supporting US customers."""


def post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())


def main() -> None:
    try:
        payload = {
            "candidate_name": "Riya Shah",
            "target_role": "Customer Success Manager",
            "resume_text": RESUME,
            "company_name": "Acme",
            "job_title": "Enterprise CSM",
            "job_description": JD,
        }
        out = post("/api/candidates/ingest", payload)
    except Exception as e:
        print(f"FAIL: ingest call failed. Is the backend running with GEMINI_API_KEY set? {e}")
        sys.exit(1)
    print(f"candidate_id={out['candidate_id']}")
    print(f"job_description_id={out['job_description_id']}")
    print(f"chunk_count={out['chunk_count']}")
    print(f"requirements={len(out['requirements'])}")
    print("ingest ok")


if __name__ == "__main__":
    main()
