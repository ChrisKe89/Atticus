from fastapi.testclient import TestClient

from api.main import app

with TestClient(app) as c:
    res = c.post("/ask", json={"question": "What is the print resolution?"})
    print(res.status_code)
    j = res.json()
    print("confidence", j.get("confidence"))
    print("answer:\n", j.get("answer"))
