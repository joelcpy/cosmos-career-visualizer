import json
from unittest.mock import patch
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


# ── /api/generate ──────────────────────────────────────────────────────────────

def test_generate_missing_image(client):
    res = client.post("/api/generate", json={"occupation": "chef"})
    assert res.status_code == 400
    assert "No image provided" in res.get_json()["error"]


def test_generate_blocked_career(client):
    with patch("server.generate_image", side_effect=ValueError("blocked")):
        res = client.post("/api/generate", json={
            "image_base64": "abc123",
            "occupation": "bad career"
        })
    assert res.status_code == 400
    assert res.get_json()["error"] == "blocked"


def test_generate_success(client):
    with patch("server.generate_image", return_value=("https://example.com/img.jpg", "Chef")):
        res = client.post("/api/generate", json={
            "image_base64": "abc123",
            "occupation": "chef"
        })
    assert res.status_code == 200
    assert res.get_json()["image_url"] == "https://example.com/img.jpg"
    assert res.get_json()["occupation"] == "Chef"


def test_generate_fal_error(client):
    with patch("server.generate_image", side_effect=Exception("fal.ai timeout")):
        res = client.post("/api/generate", json={
            "image_base64": "abc123",
            "occupation": "chef"
        })
    assert res.status_code == 500


# ── /api/auth ──────────────────────────────────────────────────────────────────

def test_auth_correct_password(client):
    with patch.dict(os.environ, {"SITE_PASSWORD": "secret"}):
        res = client.post("/api/auth", json={"password": "secret"})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_auth_wrong_password(client):
    with patch.dict(os.environ, {"SITE_PASSWORD": "secret"}):
        res = client.post("/api/auth", json={"password": "wrong"})
    assert res.status_code == 401
    assert res.get_json()["ok"] is False
