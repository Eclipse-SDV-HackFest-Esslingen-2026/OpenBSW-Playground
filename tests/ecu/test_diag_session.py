"""Tier 2 — UDS DiagnosticSessionControl (0x10) tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_003
"""

import pytest


@pytest.mark.ecu
class TestDiagSession:
    def test_default_session(self, doip_client):
        """TEST_RG1_003: Switch to default session (0x01)."""
        response = doip_client.send_diagnostic(bytes([0x10, 0x01]))
        assert response is not None
        assert response[0] == 0x50, f"Expected positive response 0x50, got 0x{response[0]:02X}"
        assert response[1] == 0x01

    def test_extended_session(self, doip_client):
        """TEST_RG1_003: Switch to extended session (0x03)."""
        response = doip_client.send_diagnostic(bytes([0x10, 0x03]))
        assert response is not None
        assert response[0] == 0x50, f"Expected positive response 0x50, got 0x{response[0]:02X}"
        assert response[1] == 0x03

    def test_invalid_session_nrc(self, doip_client):
        """Invalid session sub-function should return NRC."""
        response = doip_client.send_diagnostic(bytes([0x10, 0xFF]))
        assert response is not None
        # Expect negative response
        assert response[0] == 0x7F
        assert response[1] == 0x10  # SID
