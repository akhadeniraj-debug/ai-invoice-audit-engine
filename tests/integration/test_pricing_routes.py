"""Integration tests for protected pricing and quotation estimation routes."""

import pytest
from fastapi.testclient import TestClient

from app.database.connection import init_db
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def api_key(client: TestClient) -> str:
    """Creates a standard API key with 100 RPM for testing protected routes."""
    res = client.post(
        "/api/v1/auth/keys",
        json={"client_name": "Test Signage Contractor", "rate_limit_rpm": 100},
    )
    assert res.status_code == 201
    return res.json()["raw_key"]


class TestProtectedPricingRoutes:
    """Verifies authentication, deterministic pricing calculation, and response headers."""

    def test_calculate_pricing_sqft_acp_facade(self, client: TestClient, api_key: str):
        """POST /api/v1/pricing/calculate for sqft panels with 18% GST."""
        payload = {
            "unit_type": "sqft",
            "product_name": "Exterior ACP Facade Cladding",
            "material_name": "4mm Heavy-Duty PVDF ACP",
            "material_multiplier": 1.35,
            "lighting_surcharge": 0.0,
            "width_ft": 10.0,
            "width_in": 6.0,  # 10.5 ft
            "height_ft": 4.0,
            "height_in": 0.0,  # 4.0 ft => 42.0 sqft
            "base_sqft_rate": 420.0,
            "installation_rate": 85.0,
            "gst_percent": 18.0,
        }

        response = client.post(
            "/api/v1/pricing/calculate",
            headers={"X-API-Key": api_key},
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()

        # 10.5 × 4.0 = 42.0 sq.ft
        # base_cost = 42.0 * 420 * 1.35 = 23814.0
        # installation_cost = 42.0 * 85 = 3570.0
        # subtotal = 23814 + 3570 = 27384
        # gst = 27384 * 0.18 = 4929.12 -> 4929
        # grand_total = 27384 + 4929 = 32313
        assert data["unit_type"] == "sqft"
        assert data["total_units"] == 42.0
        assert data["subtotal"] == 27384.0
        assert data["gst_amount"] == 4929.0
        assert data["grand_total"] == 32313.0
        assert data["currency"] == "INR"
        assert data["client_name"] == "Test Signage Contractor"

        # Rate limit headers check
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "100"

    def test_calculate_pricing_3d_letters(self, client: TestClient, api_key: str):
        """POST /api/v1/pricing/calculate for 3D channel letters (running inch basis)."""
        payload = {
            "unit_type": "letter",
            "product_name": "Front-Lit 3D Acrylic Letters",
            "material_name": "3mm Virgin Cast Face",
            "material_multiplier": 1.0,
            "lighting_surcharge": 160.0,
            "letter_height_in": 12.0,
            "letter_count": 7,  # "SAI ARTS"
            "base_letter_rate": 95.0,
            "installation_rate": 85.0,
            "gst_percent": 18.0,
        }

        response = client.post(
            "/api/v1/pricing/calculate",
            headers={"X-API-Key": api_key},
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()

        # Running inches: 7 * 12 = 84"
        # base_cost: 84 * 95 * 1.0 = 7980
        # lighting_cost: 7 * 160 = 1120
        # installation_cost: 7 * 85 * 1.5 = 892.5
        # subtotal: 7980 + 1120 + 892.5 = 9992.5 -> 9993
        # gst: 9993 * 0.18 = 1798.74 -> 1799
        # grand_total: 9993 + 1799 = 11792
        assert data["unit_type"] == "letter"
        assert data["total_units"] == 84.0
        assert data["base_cost"] == 7980.0
        assert data["lighting_cost"] == 1120.0
        assert data["subtotal"] == 9993.0
        assert data["gst_amount"] == 1799.0
        assert data["grand_total"] == 11792.0

    def test_generate_quote_estimate_formal(self, client: TestClient, api_key: str):
        """POST /api/v1/quotes/estimate returns formal company quote with serial reference."""
        payload = {
            "unit_type": "sqft",
            "product_name": "Industrial Safety Radium Board",
            "width_ft": 4.0,
            "height_ft": 2.0,
            "material_multiplier": 1.0,
        }

        response = client.post(
            "/api/v1/quotes/estimate",
            headers={"X-API-Key": api_key},
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()

        assert "estimate_reference" in data
        assert data["estimate_reference"].startswith("EST-2026-")
        assert data["enterprise"] == "Sai Arts Industrial Manufacturing"
        assert "warranty" in data
        assert "calculation" in data
        assert data["calculation"]["grand_total"] > 0
