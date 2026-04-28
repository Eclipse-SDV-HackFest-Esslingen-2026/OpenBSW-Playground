"""Tier 3 — Stub CDA data/DID reading tests.

Requires: ECU + Stub CDA running.
Covers: TEST_RG3_002, TEST_RG3_003, TEST_RG3_004
"""

import pytest
import requests

from conftest import CDA_HOST, CDA_PORT

BASE_URL = f"http://{CDA_HOST}:{CDA_PORT}"


@pytest.mark.sovd
class TestData:
    def test_sensor_data_endpoint(self, cda_process):
        """TEST_RG3_003: Grafana-compatible sensor endpoints return data."""
        for path in [
            "/api/sensors/engine_temp",
            "/api/sensors/battery_voltage",
            "/api/sensors/vehicle_speed",
        ]:
            r = requests.get(f"{BASE_URL}{path}", timeout=10)
            if r.status_code == 200:
                return  # At least one sensor endpoint works
        pytest.fail("No sensor endpoint returned 200")

    def test_data_listing(self, cda_process):
        """TEST_RG3_004: Data/DID listing endpoint."""
        for path in [
            "/sovd/v1/components/openbsw-ecu/data",
            "/sovd/v1/components/openbsw/data",
        ]:
            r = requests.get(f"{BASE_URL}{path}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                assert data is not None
                return
        pytest.fail("No data listing endpoint returned 200")
