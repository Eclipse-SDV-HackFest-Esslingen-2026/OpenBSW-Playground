"""Tier 3 — Stub CDA fault reading tests.

Requires: ECU + Stub CDA running.
Covers: TEST_RG3_002, TEST_RG3_004
"""

import pytest
import requests

from conftest import CDA_HOST, CDA_PORT

BASE_URL = f"http://{CDA_HOST}:{CDA_PORT}"


@pytest.mark.sovd
class TestFaults:
    def test_read_faults(self, cda_process):
        """TEST_RG3_002 / TEST_RG3_004: Read faults via SOVD API."""
        # Try common endpoint patterns
        for path in [
            "/sovd/v1/components/openbsw-ecu/faults",
            "/sovd/v1/components/openbsw/faults",
            "/api/faults/list",
        ]:
            r = requests.get(f"{BASE_URL}{path}", timeout=10)
            if r.status_code == 200:
                return  # Success
        pytest.fail("No fault listing endpoint returned 200")

    def test_read_faults_returns_json(self, cda_process):
        """TEST_RG3_004: Fault endpoint returns valid JSON."""
        for path in [
            "/sovd/v1/components/openbsw-ecu/faults",
            "/sovd/v1/components/openbsw/faults",
            "/api/faults/list",
        ]:
            r = requests.get(f"{BASE_URL}{path}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                assert data is not None
                return
        pytest.fail("No fault endpoint returned valid JSON")
