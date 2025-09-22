from fastapi.testclient import TestClient
from api.main import app

with TestClient(app) as c:
    r = c.get("/ui")
    print("UI:", r.status_code, len(r.text))
