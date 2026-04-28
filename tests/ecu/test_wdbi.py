"""Tier 2 — UDS WriteDataByIdentifier (0x2E) tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_006
"""

import pytest


@pytest.mark.ecu
class TestWriteDID:
    def test_wdbi_requires_extended_session(self, doip_client):
        """TEST_RG1_006: WDBI to DID 0xCF03 fails in default session."""
        # Ensure default session
        doip_client.send_diagnostic(bytes([0x10, 0x01]))

        # Attempt write in default session
        response = doip_client.send_diagnostic(bytes([0x2E, 0xCF, 0x03, 0x42]))
        assert response is not None
        # Expect negative response (conditions not correct or similar NRC)
        assert response[0] == 0x7F, "Write should fail in default session"

    def test_wdbi_succeeds_in_extended_session(self, doip_client):
        """TEST_RG1_006: WDBI to DID 0xCF03 succeeds in extended session."""
        # Switch to extended session
        sess_resp = doip_client.send_diagnostic(bytes([0x10, 0x03]))
        assert sess_resp[0] == 0x50

        # Write data
        response = doip_client.send_diagnostic(bytes([0x2E, 0xCF, 0x03, 0x42]))
        assert response is not None
        assert response[0] == 0x6E, f"Expected 0x6E, got 0x{response[0]:02X}"
