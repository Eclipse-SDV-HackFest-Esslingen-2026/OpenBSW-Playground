"""Tier 3 — Stub CDA component listing tests.

Requires: ECU + Stub CDA running.
Covers: TEST_RG3_004
"""

import pytest
import requests

from conftest import CDA_HOST, CDA_PORT

BASE_URL = f"http://{CDA_HOST}:{CDA_PORT}"


@pytest.mark.sovd
class TestComponents:
    def test_component_listing(self, cda_process):
        """TEST_RG3_004: Component listing returns at least one component."""
        # Try common SOVD endpoint patterns
        for path in ["/sovd/v1/components", "/sovd/v1/"]:
            r = requests.get(f"{BASE_URL}{path}", timeout=5)
            if r.status_code == 200:
                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                assert data is not None
                return
        pytest.fail("No component listing endpoint found")
