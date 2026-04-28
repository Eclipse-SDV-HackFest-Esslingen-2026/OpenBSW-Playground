"""Tier 2 — UDS ReadDataByIdentifier (0x22) tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_004, TEST_RG1_005
"""

import pytest


SENSOR_DIDS = [0xCF10, 0xCF11, 0xCF12]
STATIC_DIDS = [0xCF01, 0xCF02]


def _read_did(doip_client, did):
    """Send ReadDataByIdentifier for a single DID."""
    did_bytes = did.to_bytes(2, byteorder="big")
    response = doip_client.send_diagnostic(bytes([0x22]) + did_bytes)
    return response


@pytest.mark.ecu
class TestReadDID:
    @pytest.mark.parametrize("did", SENSOR_DIDS, ids=[f"0x{d:04X}" for d in SENSOR_DIDS])
    def test_read_sensor_did(self, doip_client, did):
        """TEST_RG1_004: Read simulated sensor DIDs."""
        response = _read_did(doip_client, did)
        assert response is not None
        assert response[0] == 0x62, f"Expected 0x62, got 0x{response[0]:02X}"
        # Echo DID bytes back
        assert response[1] == (did >> 8) & 0xFF
        assert response[2] == did & 0xFF
        # At least 1 byte of data
        assert len(response) > 3

    @pytest.mark.parametrize("did", STATIC_DIDS, ids=[f"0x{d:04X}" for d in STATIC_DIDS])
    def test_read_static_did(self, doip_client, did):
        """TEST_RG1_005: Read static data DIDs."""
        response = _read_did(doip_client, did)
        assert response is not None
        assert response[0] == 0x62, f"Expected 0x62, got 0x{response[0]:02X}"
        assert len(response) > 3

    def test_sensor_values_change(self, doip_client):
        """TEST_RG1_004: Sensor values change between reads (random walk)."""
        did = 0xCF10  # EngineTemp
        values = set()
        for _ in range(10):
            response = _read_did(doip_client, did)
            if response[0] == 0x62:
                values.add(response[3:].hex())
        # At least 2 different values in 10 reads
        assert len(values) >= 2, "Sensor value did not change in 10 reads"
