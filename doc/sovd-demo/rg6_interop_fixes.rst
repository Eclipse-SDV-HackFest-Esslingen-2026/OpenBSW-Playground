RG-6 — Interoperability Fixes
=============================

Resolved integration issues between OpenBSW ECU and OpenSOVD CDA.

.. note:: **MECE overlap with RG-4**

   RG-6 captures *specific defect fixes* in DoIP interoperability.  RG-4
   captures the *nominal* DoIP protocol requirements.  The groups are
   intentionally separate: RG-4 requirements remain valid independently, while
   RG-6 requirements document regression-proofing of resolved bugs.

.. contents::
   :local:
   :depth: 1

.. req:: ECU handles tester-originated DiagnosticMessageAck payloads
   :id: REQ_RG6_001
   :status: done
   :tags: rg6, interop, doip
   :satisfies: SPEC_ARCH_INTEROP

   ECU handles tester-originated DiagnosticMessageAck payloads.
   Root cause: CDA sends 0x8002 back; ECU NACKed with 0x01 (unknown type).
   Solution: Overlay ``DoIpServerConnectionHandler.cpp`` lines 284-290 — added
   ``case DIAGNOSTIC_MESSAGE_POSITIVE_ACK / NEGATIVE_ACK`` to ``headerReceived()``
   switch; upstream file unchanged.

.. req:: CDA diagnostic ACK does not corrupt DoIP response stream
   :id: REQ_RG6_002
   :status: done
   :tags: rg6, interop, doip
   :satisfies: SPEC_ARCH_INTEROP

   CDA diagnostic ACK does not corrupt DoIP response stream.
   Root cause: Unconditional ACK in ``handle_response()`` confused parsing.
   Solution: Set ``send_diagnostic_message_ack = false`` in TOML.

.. req:: CDA send timeout accommodates lwIP userspace TCP timing
   :id: REQ_RG6_003
   :status: done
   :tags: rg6, interop, doip
   :satisfies: SPEC_ARCH_INTEROP

   CDA send timeout accommodates lwIP userspace TCP timing.
   Root cause: Default 1 s timeout too short for POSIX lwIP stack.
   Solution: Increased ``send_timeout_ms = 5000``.

.. req:: ECU does not stop when launched as background process
   :id: REQ_RG6_004
   :status: done
   :tags: rg6, interop, posix
   :satisfies: SPEC_ARCH_INTEROP

   ECU does not stop when launched as background process.
   Root cause: ``Uart::init()`` calls ``tcsetattr()`` → SIGTTOU stops process.
   Solution: Trap SIGTTOU, redirect stdin from ``/dev/null``.

.. req:: CDA uses standard DoIP matching ECU implementation
   :id: REQ_RG6_005
   :status: done
   :tags: rg6, interop, doip
   :satisfies: SPEC_ARCH_INTEROP

   CDA uses standard DoIP (not DOBT) matching ECU implementation.
   Root cause: DOBT uses different routing activation type.
   Solution: Set ``onboard_tester = false``.
