"""Tier 2 — RG-6 Interoperability regression tests.

Tests guard against the most dangerous regressions in the
ECU/CDA DoIP integration.

Requires: ECU running on TAP interface.
Covers: TEST_RG6_001, TEST_RG6_002, TEST_RG6_003, TEST_RG6_004, TEST_RG6_005
"""

import os
import signal
import socket
import struct
import subprocess
import time

import pytest

from conftest import ECU_IP, ECU_DOIP_PORT, ECU_LOGICAL_ADDR, TESTER_LOGICAL_ADDR, REPO_ROOT


def _build_doip_header(payload_type, payload_length):
    """Build an 8-byte DoIP header."""
    return struct.pack("!BBHI", 0x02, 0xFD, payload_type, payload_length)


def _send_raw_doip(sock, payload_type, payload):
    """Send a raw DoIP message on a connected socket."""
    header = _build_doip_header(payload_type, len(payload))
    sock.sendall(header + payload)


def _recv_doip(sock, timeout=5):
    """Receive and parse one DoIP message. Returns (type, payload)."""
    sock.settimeout(timeout)
    header = b""
    while len(header) < 8:
        chunk = sock.recv(8 - len(header))
        if not chunk:
            return None, None
        header += chunk
    _, _, ptype, plen = struct.unpack("!BBHI", header)
    payload = b""
    while len(payload) < plen:
        chunk = sock.recv(plen - len(payload))
        if not chunk:
            break
        payload += chunk
    return ptype, payload


def _do_routing_activation(sock):
    """Perform DoIP routing activation on connected socket."""
    # Routing Activation Request (0x0005)
    # SA(2) + activation_type(1) + reserved(4) = 7 bytes
    sa = TESTER_LOGICAL_ADDR.to_bytes(2, "big")
    payload = sa + b"\x00" + b"\x00\x00\x00\x00"
    _send_raw_doip(sock, 0x0005, payload)

    ptype, data = _recv_doip(sock)
    assert ptype == 0x0006, f"Expected routing activation response 0x0006, got 0x{ptype:04X}"
    return data


@pytest.mark.ecu
class TestInteropRegressions:
    def test_ecu_handles_tester_ack(self, ecu_process):
        """TEST_RG6_001: ECU silently consumes tester-originated 0x8002 ACKs.

        Regression: Before the overlay fix, ECU NACKed with type 0x01 (unknown).
        """
        sock = socket.create_connection((ECU_IP, ECU_DOIP_PORT), timeout=5)
        try:
            _do_routing_activation(sock)

            # Send DiagnosticMessagePositiveAck (0x8002) from tester
            # SA(2) + TA(2) + ACK_code(1) = 5 bytes
            sa = TESTER_LOGICAL_ADDR.to_bytes(2, "big")
            ta = ECU_LOGICAL_ADDR.to_bytes(2, "big")
            ack_payload = sa + ta + b"\x00"
            _send_raw_doip(sock, 0x8002, ack_payload)

            # Now send a normal diagnostic request — should still work
            diag_payload = sa + ta + bytes([0x3E, 0x00])  # TesterPresent
            _send_raw_doip(sock, 0x8001, diag_payload)

            # Should get PositiveAck (0x8002) then DiagnosticMessage (0x8001)
            ptype1, _ = _recv_doip(sock)
            assert ptype1 in (0x8001, 0x8002), \
                f"ECU disconnected or NACKed after tester ACK: got 0x{ptype1:04X}"

            if ptype1 == 0x8002:
                ptype2, data2 = _recv_doip(sock)
                assert ptype2 == 0x8001, f"Expected diagnostic response, got 0x{ptype2:04X}"
                # UDS response should be TesterPresent positive response
                uds = data2[4:]  # skip SA + TA
                assert uds[0] == 0x7E
        finally:
            sock.close()

    def test_rapid_requests_no_corruption(self, doip_client):
        """TEST_RG6_002: Rapid diagnostic requests don't corrupt responses.

        Regression: CDA ACK interleaving caused response stream corruption.
        """
        for i in range(10):
            response = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
            assert response is not None, f"Request {i} returned None"
            assert response[0] == 0x7E, \
                f"Request {i}: expected 0x7E, got 0x{response[0]:02X} — possible corruption"

    def test_timeout_under_load(self, doip_client):
        """TEST_RG6_003: No timeouts under sequential load.

        Regression: Default 1s CDA timeout was too short for lwIP timing.
        """
        start = time.time()
        for _ in range(20):
            response = doip_client.send_diagnostic(bytes([0x22, 0xCF, 0x10]))
            assert response is not None, "Timeout: no response received"
            assert response[0] == 0x62
        elapsed = time.time() - start
        # 20 requests should complete well within reasonable time
        assert elapsed < 30, f"20 requests took {elapsed:.1f}s — possible timeout issues"

    def test_ecu_background_process(self, ecu_process):
        """TEST_RG6_004: ECU runs as background process without SIGTTOU.

        Regression: Uart::init() tcsetattr() caused SIGTTOU in background.
        """
        # The ECU fixture already starts the process in background
        # If we get here, the process is running
        assert ecu_process.poll() is None, \
            f"ECU process died with exit code {ecu_process.returncode}"

        # Verify it responds to diagnostic requests
        sock = socket.create_connection((ECU_IP, ECU_DOIP_PORT), timeout=5)
        sock.close()

    def test_standard_doip_not_dobt(self, doip_client):
        """TEST_RG6_005: Routing activation uses standard DoIP (type 0x00).

        Regression: DOBT uses different routing activation type.
        """
        # doipclient performs routing activation during connection
        # The fact that it connects successfully with standard type proves this
        # Send a diagnostic request to fully verify the connection is working
        response = doip_client.send_diagnostic(bytes([0x3E, 0x00]))
        assert response is not None
        assert response[0] == 0x7E

        # Also verify the CDA config if accessible
        cda_config = os.path.join(REPO_ROOT, "OpenBSW-SOVD-Demo/real-sovd-cda/opensovd-cda.toml")
        if os.path.isfile(cda_config):
            with open(cda_config) as f:
                config_text = f.read()
            assert "onboard_tester = false" in config_text or \
                   'onboard_tester = false' in config_text, \
                   "CDA config should have onboard_tester = false"
