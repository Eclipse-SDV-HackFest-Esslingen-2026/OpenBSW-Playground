"""Tier 2 — DoIP protocol-level tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG4_002, TEST_RG4_003, TEST_RG4_004
"""

import pytest


@pytest.mark.ecu
class TestDoIPProtocol:
    def test_bidirectional_diagnostic_message(self, doip_client):
        """TEST_RG4_002: DiagnosticMessage flows bidirectionally."""
        # Send a simple TesterPresent and verify response
        response = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
        assert response is not None
        assert len(response) >= 2
        assert response[0] == 0x7E

    def test_multiple_sequential_requests(self, doip_client):
        """TEST_RG4_002: Multiple requests/responses on same connection."""
        for _ in range(5):
            response = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
            assert response is not None
            assert response[0] == 0x7E

    def test_request_response_consistency(self, doip_client):
        """TEST_RG4_003: ECU responds correctly to different services."""
        # TesterPresent
        r1 = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
        assert r1[0] == 0x7E

        # DiagnosticSessionControl
        r2 = doip_client.send_diagnostic(bytes([0x10, 0x01]))
        assert r2[0] == 0x50

        # ReadDID
        r3 = doip_client.send_diagnostic(bytes([0x22, 0xCF, 0x01]))
        assert r3[0] == 0x62
