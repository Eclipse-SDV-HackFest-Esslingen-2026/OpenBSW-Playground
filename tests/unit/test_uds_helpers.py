"""Tier 1 — UDS helper / protocol unit tests (no ECU needed)."""

import pytest


@pytest.mark.unit
class TestUdsHelpers:
    def test_positive_response_sid(self):
        """UDS positive response SID = request SID + 0x40."""
        request_sids = {
            0x10: 0x50,  # DiagnosticSessionControl
            0x22: 0x62,  # ReadDataByIdentifier
            0x2E: 0x6E,  # WriteDataByIdentifier
            0x19: 0x59,  # ReadDTCInformation
            0x14: 0x54,  # ClearDiagnosticInformation
            0x3E: 0x7E,  # TesterPresent
            0x31: 0x71,  # RoutineControl
            0x28: 0x68,  # CommunicationControl
        }
        for req_sid, expected_resp in request_sids.items():
            assert req_sid + 0x40 == expected_resp, f"SID 0x{req_sid:02X}"

    def test_nrc_byte_positions(self):
        """Negative response is [0x7F, SID, NRC]."""
        neg_response = bytes([0x7F, 0x22, 0x31])
        assert neg_response[0] == 0x7F
        assert neg_response[1] == 0x22  # original SID
        assert neg_response[2] == 0x31  # NRC: requestOutOfRange

    def test_dtc_status_byte_bits(self):
        """ISO 14229 Annex D status byte bit definitions."""
        # Bit 0: testFailed
        # Bit 1: testFailedThisOperationCycle
        # Bit 2: pendingDTC
        # Bit 3: confirmedDTC
        # Bit 4: testNotCompletedSinceLastClear
        # Bit 5: testFailedSinceLastClear
        # Bit 6: testNotCompletedThisOperationCycle
        # Bit 7: warningIndicatorRequested
        status = 0x2F  # testFailed + testFailedThisOC + pendingDTC + confirmedDTC + testFailedSinceLastClear
        assert status & 0x01  # testFailed
        assert status & 0x02  # testFailedThisOperationCycle
        assert status & 0x04  # pendingDTC
        assert status & 0x08  # confirmedDTC
        assert status & 0x20  # testFailedSinceLastClear

    def test_did_encoding(self):
        """DID is 2 bytes big-endian in UDS request."""
        did = 0xCF10
        encoded = did.to_bytes(2, byteorder="big")
        assert encoded == b"\xCF\x10"
        assert int.from_bytes(encoded, byteorder="big") == did

    def test_doip_header_format(self):
        """DoIP header: version(1) + inv_version(1) + type(2) + length(4) = 8 bytes."""
        # DiagnosticMessage type = 0x8001
        import struct

        version = 0x02
        inv_version = 0xFD
        payload_type = 0x8001
        payload_length = 7  # SA(2) + TA(2) + UDS(3)

        header = struct.pack("!BBHI", version, inv_version, payload_type, payload_length)
        assert len(header) == 8
        assert header[0] == 0x02
        assert header[1] == 0xFD
