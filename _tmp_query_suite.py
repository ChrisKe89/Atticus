from fastapi.testclient import TestClient

from api.main import app

qs = [
    "What is the print resolution?",
    "What is the maximum bypass tray size?",
    "What is the toner yield for black toner?",
    "Which interfaces are standard?",
]
with TestClient(app) as c:
    for q in qs:
        r = c.post("/ask", json={"question": q})
        j = r.json()
        print(q, "->", j["confidence"], "ESC", j["should_escalate"])
        print(j["answer"][:140])
        print("first cite", j["citations"][0]["source_path"] if j["citations"] else None)
        print("-" * 60)
