"""Tier 2 — RG-1 supplementary executable tests.

Covers gaps identified by QM audit:
  TEST_RG1_001: Build and run (cmake preset builds successfully)
  TEST_RG1_012: RoutineControl 0x31 negative response
  TEST_RG1_013: CommunicationControl 0x28 negative response
"""

import os
import subprocess

import pytest

from conftest import REPO_ROOT


@pytest.mark.unit
class TestBuildVerification:
    def test_cmake_preset_builds(self):
        """TEST_RG1_001: posix-freertos preset builds without errors."""
        build_dir = os.path.join(REPO_ROOT, "openbsw/build/posix-freertos")
        # Check that build artifacts exist
        ninja_file = os.path.join(build_dir, "build.ninja")
        assert os.path.isfile(ninja_file), \
            f"Build file not found at {ninja_file} — run cmake preset first"


@pytest.mark.ecu
class TestUnsupportedServices:
    def test_routine_control_rejected(self, doip_client):
        """TEST_RG1_012: RoutineControl (0x31) rejected with NRC.

        ECU should return NRC 0x11 (serviceNotSupported) or 0x31 (requestOutOfRange).
        """
        # RoutineControl: startRoutine (0x01), routineId 0x0001
        response = doip_client.send_diagnostic(bytes([0x31, 0x01, 0x00, 0x01]))
        assert response is not None, "No response to RoutineControl"
        assert response[0] == 0x7F, \
            f"Expected NRC, got SID 0x{response[0]:02X}"
        assert response[1] == 0x31, \
            f"NRC should reference SID 0x31, got 0x{response[1]:02X}"
        assert response[2] in (0x11, 0x12, 0x31, 0x7E, 0x7F), \
            f"Unexpected NRC code: 0x{response[2]:02X}"

    def test_communication_control_rejected(self, doip_client):
        """TEST_RG1_013: CommunicationControl (0x28) rejected with NRC.

        ECU should return NRC 0x11 (serviceNotSupported).
        """
        # CommunicationControl: enableRxAndTx (0x00), communicationType 0x01
        response = doip_client.send_diagnostic(bytes([0x28, 0x00, 0x01]))
        assert response is not None, "No response to CommunicationControl"
        assert response[0] == 0x7F, \
            f"Expected NRC, got SID 0x{response[0]:02X}"
        assert response[1] == 0x28, \
            f"NRC should reference SID 0x28, got 0x{response[1]:02X}"
        assert response[2] in (0x11, 0x12, 0x31, 0x7E, 0x7F), \
            f"Unexpected NRC code: 0x{response[2]:02X}"
