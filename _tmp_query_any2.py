from fastapi.testclient import TestClient

from api.main import app

payload = {"question": "What is the maximum AMPV for the C4570?"}
with TestClient(app) as c:
    r = c.post("/ask", json=payload)
    print("STATUS", r.status_code)
    j = r.json()
    print("CONF", j["confidence"], "ESC", j["should_escalate"])
    print("ANSWER\n", j["answer"][:300])
    print("FIRST CITATION", j["citations"][0] if j["citations"] else None)
