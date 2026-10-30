"""Unit tests for API key generation, cryptographic storage, verification, and revocation."""

import hashlib
import pytest
from fastapi.testclient import TestClient

from app.database.connection import init_db
from app.database.models import ApiKeyRecord
from app.main import app
from app.services.security import generate_raw_api_key, get_key_prefix, hash_api_key


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure clean schema for each test."""
    init_db()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


class TestApiKeyGenerationAndHashing:
    """Tests key formatting, cryptographic hashing, and prefix extraction."""

    def test_raw_key_format(self):
        """Raw key must start with 'sai_live_' followed by 32 url-safe random bytes (43 chars)."""
        key = generate_raw_api_key()
        assert key.startswith("sai_live_")
        # 'sai_live_' is 9 chars; token_urlsafe(32) produces 43 chars -> total 52 chars
        token_part = key[len("sai_live_"):]
        assert len(token_part) >= 42
        assert len(key) >= 50

    def test_sha256_hash_deterministic(self):
        """SHA-256 hash must be a deterministic 64-character lowercase hex string."""
        raw_key = "sai_live_test_key_sample_1234567890abcdef"
        hash_1 = hash_api_key(raw_key)
        hash_2 = hash_api_key(raw_key)

        assert hash_1 == hash_2
        assert len(hash_1) == 64
        expected = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        assert hash_1 == expected

    def test_key_prefix_length(self):
        """Key prefix must capture exactly the first 12 characters."""
        raw_key = "sai_live_ABC123456789xyz"
        prefix = get_key_prefix(raw_key)
        assert prefix == "sai_live_ABC"
        assert len(prefix) == 12


class TestApiKeyAdminEndpoints:
    """Tests admin API key issuance, listing, and revocation endpoints."""

    def test_issue_api_key_success(self, client: TestClient):
        """POST /api/v1/auth/keys should issue a key, save its hash, and return raw key once."""
        response = client.post(
            "/api/v1/auth/keys",
            json={"client_name": "Acme Architectural", "rate_limit_rpm": 120},
        )
        assert response.status_code == 201
        data = response.json()

        assert "raw_key" in data
        assert data["raw_key"].startswith("sai_live_")
        assert data["client_name"] == "Acme Architectural"
        assert data["rate_limit_rpm"] == 120
        assert data["is_active"] is True
        assert data["key_prefix"] == data["raw_key"][:12]

    def test_list_api_keys_never_exposes_raw_key(self, client: TestClient):
        """GET /api/v1/auth/keys should list keys without exposing raw keys or hashes."""
        client.post("/api/v1/auth/keys", json={"client_name": "Client Alpha", "rate_limit_rpm": 60})
        client.post("/api/v1/auth/keys", json={"client_name": "Client Beta", "rate_limit_rpm": 30})

        response = client.get("/api/v1/auth/keys")
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 2

        for item in items:
            assert "key_prefix" in item
            assert "client_name" in item
            assert "raw_key" not in item
            assert "hashed_key" not in item

    def test_revoke_api_key(self, client: TestClient):
        """PATCH /api/v1/auth/keys/{id}/revoke should deactivate the key."""
        create_res = client.post(
            "/api/v1/auth/keys",
            json={"client_name": "Temporary Client", "rate_limit_rpm": 45},
        )
        key_id = create_res.json()["id"]

        revoke_res = client.patch(f"/api/v1/auth/keys/{key_id}/revoke")
        assert revoke_res.status_code == 200
        assert revoke_res.json()["is_active"] is False


class TestApiKeyVerification:
    """Tests verification of X-API-Key header against database records."""

    def test_missing_api_key_header_returns_401(self, client: TestClient):
        """Calling protected endpoint without X-API-Key header must return HTTP 401."""
        response = client.post(
            "/api/v1/pricing/calculate",
            json={
                "unit_type": "sqft",
                "width_ft": 10,
                "height_ft": 4,
            },
        )
        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]

    def test_invalid_api_key_returns_401(self, client: TestClient):
        """Calling protected endpoint with bogus key must return HTTP 401."""
        response = client.post(
            "/api/v1/pricing/calculate",
            headers={"X-API-Key": "sai_live_invalid_and_unknown_key_string"},
            json={
                "unit_type": "sqft",
                "width_ft": 10,
                "height_ft": 4,
            },
        )
        assert response.status_code == 401
        assert "Invalid or unknown API key" in response.json()["detail"]

    def test_revoked_api_key_returns_403(self, client: TestClient):
        """Calling protected endpoint with a revoked key must return HTTP 403."""
        # 1. Issue key
        issue_res = client.post(
            "/api/v1/auth/keys",
            json={"client_name": "Revocable Client", "rate_limit_rpm": 60},
        )
        raw_key = issue_res.json()["raw_key"]
        key_id = issue_res.json()["id"]

        # 2. Revoke key
        client.patch(f"/api/v1/auth/keys/{key_id}/revoke")

        # 3. Attempt protected access
        response = client.post(
            "/api/v1/pricing/calculate",
            headers={"X-API-Key": raw_key},
            json={
                "unit_type": "sqft",
                "width_ft": 5,
                "height_ft": 3,
            },
        )
        assert response.status_code == 403
        assert "inactive or has been revoked" in response.json()["detail"]

    def test_valid_api_key_succeeds_and_updates_last_used(self, client: TestClient):
        """Valid key should authenticate successfully and record last_used_at timestamp."""
        issue_res = client.post(
            "/api/v1/auth/keys",
            json={"client_name": "Active Partner", "rate_limit_rpm": 60},
        )
        raw_key = issue_res.json()["raw_key"]
        key_id = issue_res.json()["id"]

        # Access protected endpoint
        response = client.post(
            "/api/v1/pricing/calculate",
            headers={"X-API-Key": raw_key},
            json={
                "unit_type": "sqft",
                "width_ft": 10,
                "height_ft": 4,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["client_name"] == "Active Partner"

        # Check that last_used_at is now populated in key listing
        keys_res = client.get("/api/v1/auth/keys")
        key_info = next(k for k in keys_res.json() if k["id"] == key_id)
        assert key_info["last_used_at"] is not None
