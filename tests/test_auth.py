import sys, os, logging
from fastapi.testclient import TestClient
from app.main import app

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    force=True,  # pytest'in kendi log ayarlarını ez
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- TEST CLIENT ---
client = TestClient(app)

def test_register_and_login():
    client.post("/api/user/register", json={
        "username": "mike",
        "email": "mike@example.com",
        "password": "pw"
    })
    r = client.post("/api/user/login", json={
        "email": "mike@example.com",
        "password": "pw"
    })

    data = r.json()

    logger.info("🔹 Status Code: %s", r.status_code)
    logger.info("🔹 Full Response: %s", data)
    logger.info("🔹 Access Token: %s", data.get("access_token"))

    assert r.status_code == 200
    assert "access_token" in data
