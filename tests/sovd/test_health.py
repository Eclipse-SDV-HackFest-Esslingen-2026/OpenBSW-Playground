"""Tier 3 — Stub CDA health endpoint tests.

Requires: ECU + Stub CDA running.
Covers: TEST_RG3_001
"""

import pytest
import requests

from conftest import CDA_HOST, CDA_PORT

BASE_URL = f"http://{CDA_HOST}:{CDA_PORT}"


@pytest.mark.sovd
class TestHealth:
    def test_health_endpoint(self, cda_process):
        """TEST_RG3_001: CDA health endpoint returns healthy status."""
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200

    def test_swagger_docs(self, cda_process):
        """TEST_RG3_001: Swagger UI is accessible at /docs."""
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert r.status_code == 200
        assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
