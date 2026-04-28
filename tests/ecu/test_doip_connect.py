"""Tier 2 — DoIP connectivity and routing activation tests.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_002, TEST_RG4_001, TEST_RG4_006, TEST_RG1_014
"""

import socket

import pytest

from conftest import ECU_IP, ECU_DOIP_PORT


@pytest.mark.ecu
class TestDoIPConnect:
    def test_ecu_doip_port_listening(self, ecu_process):
        """TEST_RG1_002: ECU DoIP server listens on TCP port 13400."""
        with socket.create_connection((ECU_IP, ECU_DOIP_PORT), timeout=5):
            pass  # connection succeeded

    def test_tap_interface_reachable(self, ecu_process):
        """TEST_RG1_014 / TEST_RG4_006: ECU IP reachable on TAP interface."""
        with socket.create_connection((ECU_IP, ECU_DOIP_PORT), timeout=5) as s:
            peer = s.getpeername()
            assert peer[0] == ECU_IP
            assert peer[1] == ECU_DOIP_PORT

    def test_doip_routing_activation(self, doip_client):
        """TEST_RG4_001: DoIP routing activation succeeds."""
        # doipclient performs routing activation during __init__
        # If we get here, routing activation succeeded
        assert doip_client is not None
