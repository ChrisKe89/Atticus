from fastapi.testclient import TestClient

from api.main import app

with TestClient(app) as c:
    p = {
        "question": "What is the maximum AMPV for the C4570?",
        "filters": {"path_prefix": "content/model/AC7070", "source_type": "xlsx"},
    }
    r = c.post("/ask", json=p)
    print("STATUS", r.status_code)
    j = r.json()
    print("CONF", j["confidence"], "ESC", j["should_escalate"])
    print("ANSWER\n", j["answer"][:400])
    print("CITATIONS", len(j["citations"]))
    for ci in j["citations"][:3]:
        print(ci)
