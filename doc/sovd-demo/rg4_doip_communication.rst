RG-4 — DoIP Communication
=========================

Requirements for the DoIP (ISO 13400) transport layer between ECU and CDA.

.. note:: **MECE overlap with RG-6**

   RG-4 covers *nominal* DoIP protocol behaviour (routing activation, diagnostic
   message exchange, vehicle identification).  RG-6 covers *defects and fixes*
   discovered during integration (ACK handling, timeout tuning, DOBT vs standard
   DoIP).  Some requirements touch the same protocol areas but from different
   angles: RG-4 = "it shall work", RG-6 = "this specific bug was fixed".

.. contents::
   :local:
   :depth: 1

.. req:: DoIP routing activation succeeds between CDA and ECU
   :id: REQ_RG4_001
   :status: done
   :tags: rg4, doip
   :satisfies: SPEC_ARCH_DOIP

   DoIP routing activation succeeds between CDA (tester) and ECU.
   Tester 0x0EE0, activation type 0x00.

.. req:: DoIP diagnostic messages flow bidirectionally
   :id: REQ_RG4_002
   :status: done
   :tags: rg4, doip
   :satisfies: SPEC_ARCH_DOIP

   DoIP diagnostic messages (0x8001) flow bidirectionally.
   Request from CDA, response from ECU.

.. req:: ECU sends DiagnosticMessagePositiveAck for valid requests
   :id: REQ_RG4_003
   :status: done
   :tags: rg4, doip
   :satisfies: SPEC_ARCH_DOIP

   ECU sends DiagnosticMessagePositiveAck (0x8002) for valid requests.
   Sent before UDS response.

.. req:: ECU silently consumes tester-originated ACK payloads
   :id: REQ_RG4_004
   :status: done
   :tags: rg4, doip, interop
   :satisfies: SPEC_ARCH_DOIP; SPEC_ARCH_INTEROP

   ECU silently consumes tester-originated 0x8002/0x8003 ACKs.
   Overlay ``DoIpServerConnectionHandler.cpp`` lines 284-290 — see REQ_RG6_001.

.. req:: DoIP communication uses standard protocol (not DOBT)
   :id: REQ_RG4_005
   :status: done
   :tags: rg4, doip
   :satisfies: SPEC_ARCH_DOIP

   DoIP communication uses standard protocol (not DOBT).
   ``onboard_tester = false``.

.. req:: TAP-based networking provides L2 connectivity on POSIX
   :id: REQ_RG4_006
   :status: done
   :tags: rg4, doip, networking
   :satisfies: SPEC_ARCH_DOIP; SPEC_ARCH_ECU

   TAP-based networking provides L2 connectivity on POSIX.
   lwIP userspace TCP/IP stack over tap0.
