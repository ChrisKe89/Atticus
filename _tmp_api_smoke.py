from fastapi.testclient import TestClient

from api.main import app

with TestClient(app) as c:
    r = c.get("/health")
    print("HEALTH:", r.status_code, r.json())
