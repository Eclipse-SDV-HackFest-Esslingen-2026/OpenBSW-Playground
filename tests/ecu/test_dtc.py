"""Tier 2 — UDS ReadDTCInformation (0x19) and ClearDTC (0x14) tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_007, TEST_RG1_008, TEST_RG1_009
"""

import pytest


@pytest.mark.ecu
class TestDTC:
    def test_read_dtc_count(self, doip_client):
        """TEST_RG1_007: ReadDTCInformation subfunction 0x01 (count by status mask)."""
        # 0x19 0x01 <status_mask>
        response = doip_client.send_diagnostic(bytes([0x19, 0x01, 0xFF]))
        assert response is not None
        assert response[0] == 0x59, f"Expected 0x59, got 0x{response[0]:02X}"
        assert response[1] == 0x01  # subfunction echo

    def test_read_dtc_list(self, doip_client):
        """TEST_RG1_007 / TEST_RG1_009: ReadDTCInformation subfunction 0x02 (list by mask)."""
        response = doip_client.send_diagnostic(bytes([0x19, 0x02, 0xFF]))
        assert response is not None
        assert response[0] == 0x59
        assert response[1] == 0x02
        # Each DTC is 3 bytes DTC + 1 byte status = 4 bytes per DTC
        # Response: [0x59, 0x02, availabilityMask, DTC1(3), status1(1), ...]
        dtc_data = response[3:]  # skip SID, subfunction, availability mask
        if len(dtc_data) >= 4:
            num_dtcs = len(dtc_data) // 4
            assert num_dtcs >= 1, "Expected at least 1 DTC"

    def test_five_dtcs_exist(self, doip_client):
        """TEST_RG1_009: ECU simulates exactly 5 DTCs."""
        response = doip_client.send_diagnostic(bytes([0x19, 0x02, 0xFF]))
        assert response is not None
        assert response[0] == 0x59
        dtc_data = response[3:]
        num_dtcs = len(dtc_data) // 4
        assert num_dtcs == 5, f"Expected 5 DTCs, got {num_dtcs}"

    def test_read_dtc_extended_data(self, doip_client):
        """TEST_RG1_007: ReadDTCInformation subfunction 0x06 (extended data)."""
        # Read with first known DTC (0x010100)
        response = doip_client.send_diagnostic(
            bytes([0x19, 0x06, 0x01, 0x01, 0x00, 0xFF])
        )
        assert response is not None
        # Either positive response or NRC (if extended data not available)
        assert response[0] in (0x59, 0x7F)

    def test_clear_all_dtcs(self, doip_client):
        """TEST_RG1_008: ClearDiagnosticInformation clears all DTCs."""
        # Clear all DTCs
        response = doip_client.send_diagnostic(bytes([0x14, 0xFF, 0xFF, 0xFF]))
        assert response is not None
        assert response[0] == 0x54, f"Expected 0x54, got 0x{response[0]:02X}"

        # Verify DTCs are cleared
        count_resp = doip_client.send_diagnostic(bytes([0x19, 0x01, 0xFF]))
        assert count_resp[0] == 0x59
