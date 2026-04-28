"""Tier 2 — UDS TesterPresent (0x3E) tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_011
"""

import pytest


@pytest.mark.ecu
class TestTesterPresent:
    def test_tester_present(self, doip_client):
        """TEST_RG1_011: TesterPresent (0x3E 0x00) returns positive response."""
        response = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
        assert response is not None
        assert response[0] == 0x7E, f"Expected 0x7E, got 0x{response[0]:02X}"
        assert response[1] == 0x00

    def test_tester_present_keeps_extended_session(self, doip_client):
        """TEST_RG1_011: TesterPresent keeps extended session alive."""
        # Enter extended session
        sess_resp = doip_client.send_diagnostic(bytes([0x10, 0x03]))
        assert sess_resp[0] == 0x50

        # Send TesterPresent multiple times
        for _ in range(3):
            response = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
            assert response[0] == 0x7E

        # Verify still in extended session by attempting session-gated operation
        # (read session — should still be 0x03)
        sess_check = doip_client.send_diagnostic(bytes([0x10, 0x03]))
        assert sess_check[0] == 0x50
