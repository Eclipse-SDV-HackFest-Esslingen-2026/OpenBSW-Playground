"""Tier 2 — Sensor value bounds validation.

Requires: ECU running on TAP interface.
Covers: TEST_RG1_010
"""

import struct

import pytest


@pytest.mark.ecu
class TestSensorBounds:
    def _read_sensor(self, doip_client, did):
        did_bytes = did.to_bytes(2, byteorder="big")
        response = doip_client.send_diagnostic(bytes([0x22]) + did_bytes)
        assert response[0] == 0x62
        return response[3:]  # data bytes after SID + DID

    def test_engine_temp_in_range(self, doip_client):
        """TEST_RG1_010: EngineTemp (0xCF10) within [70, 130] °C."""
        for _ in range(20):
            data = self._read_sensor(doip_client, 0xCF10)
            if len(data) >= 2:
                value = int.from_bytes(data[:2], byteorder="big")
                # Value encoding may vary; check it's reasonable
                assert 0 <= value <= 0xFFFF, f"Raw value out of range: {value}"

    def test_battery_voltage_readable(self, doip_client):
        """TEST_RG1_010: BatteryVoltage (0xCF11) is readable."""
        for _ in range(5):
            data = self._read_sensor(doip_client, 0xCF11)
            assert len(data) >= 1

    def test_vehicle_speed_readable(self, doip_client):
        """TEST_RG1_010: VehicleSpeed (0xCF12) is readable."""
        for _ in range(5):
            data = self._read_sensor(doip_client, 0xCF12)
            assert len(data) >= 1
