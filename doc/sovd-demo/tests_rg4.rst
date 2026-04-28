RG-4 Tests — DoIP Communication
================================

Test cases for the DoIP transport layer.

.. contents::
   :local:
   :depth: 1

.. test:: DoIP routing activation succeeds
   :id: TEST_RG4_001
   :status: done
   :tags: rg4, doip
   :tests: REQ_RG4_001

   Send DoIP Routing Activation Request (type 0x00) from tester 0x0EE0.
   Verify Routing Activation Response with status 0x10 (success) and
   ECU logical address 0x002A.

.. test:: DoIP diagnostic messages flow bidirectionally
   :id: TEST_RG4_002
   :status: done
   :tags: rg4, doip
   :tests: REQ_RG4_002

   Send DiagnosticMessage (0x8001) from CDA to ECU with UDS payload.
   Verify ECU responds with DiagnosticMessage (0x8001) containing UDS response.
   Verify source/target address fields are correct in both directions.

.. test:: ECU sends DiagnosticMessagePositiveAck
   :id: TEST_RG4_003
   :status: done
   :tags: rg4, doip
   :tests: REQ_RG4_003

   Send diagnostic request to ECU. Capture raw TCP stream. Verify ECU sends
   0x8002 (PositiveAck) before the 0x8001 diagnostic response.

.. test:: ECU silently consumes tester-originated ACKs
   :id: TEST_RG4_004
   :status: done
   :tags: rg4, doip, interop
   :tests: REQ_RG4_004; REQ_RG6_001

   Send DiagnosticMessagePositiveAck (0x8002) and NegativeAck (0x8003) from
   tester to ECU. Verify ECU does not NACK or disconnect. Verify subsequent
   diagnostic requests still succeed.

.. test:: DoIP uses standard protocol (not DOBT)
   :id: TEST_RG4_005
   :status: done
   :tags: rg4, doip
   :tests: REQ_RG4_005

   Verify routing activation type is 0x00 (standard). Verify CDA config has
   ``onboard_tester = false``. Verify no DOBT-specific headers in traffic.

.. test:: TAP networking provides L2 connectivity
   :id: TEST_RG4_006
   :status: done
   :tags: rg4, doip, networking
   :tests: REQ_RG4_006

   Verify ``tap0`` interface exists in 192.168.0.0/24 subnet. Send ICMP ping
   from host to ECU (192.168.0.201). Verify bidirectional Ethernet frames on
   the TAP interface.
