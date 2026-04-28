RG-6 Tests — Interoperability Fixes
====================================

Regression tests for resolved integration issues.

.. contents::
   :local:
   :depth: 1

.. test:: ECU handles tester-originated DiagnosticMessageAck
   :id: TEST_RG6_001
   :status: done
   :tags: rg6, interop, doip
   :tests: REQ_RG6_001

   Send DiagnosticMessagePositiveAck (0x8002) from tester to ECU. Verify ECU
   does not respond with NACK (0x01 unknown type). Verify subsequent diagnostic
   requests succeed. Regression test for overlay fix in
   ``DoIpServerConnectionHandler.cpp`` lines 284-290.

   Executable: ``tests/ecu/test_interop_regression.py::TestInteropRegressions::test_ecu_handles_tester_ack``

.. test:: CDA ACK suppression prevents response corruption
   :id: TEST_RG6_002
   :status: done
   :tags: rg6, interop, doip
   :tests: REQ_RG6_002

   Verify CDA config has ``send_diagnostic_message_ack = false``. Send
   multiple rapid diagnostic requests. Verify all responses are correctly
   parsed without corruption from interleaved ACK messages.

   Executable: ``tests/ecu/test_interop_regression.py::TestInteropRegressions::test_rapid_requests_no_corruption``

.. test:: CDA send timeout handles lwIP timing
   :id: TEST_RG6_003
   :status: done
   :tags: rg6, interop, doip
   :tests: REQ_RG6_003

   Verify CDA config has ``send_timeout_ms = 5000``. Under high load, send
   diagnostic requests and verify no timeout errors occur that would have
   occurred with the default 1000 ms timeout.

   Executable: ``tests/ecu/test_interop_regression.py::TestInteropRegressions::test_timeout_under_load``

.. test:: ECU runs as background process without SIGTTOU
   :id: TEST_RG6_004
   :status: done
   :tags: rg6, interop, posix
   :tests: REQ_RG6_004

   Launch ECU as background process (``&``). Verify process does not receive
   SIGTTOU and does not stop. Verify ECU continues to respond to diagnostic
   requests.

   Executable: ``tests/ecu/test_interop_regression.py::TestInteropRegressions::test_ecu_background_process``

.. test:: CDA uses standard DoIP (not DOBT)
   :id: TEST_RG6_005
   :status: done
   :tags: rg6, interop, doip
   :tests: REQ_RG6_005

   Verify CDA config has ``onboard_tester = false``. Verify routing activation
   uses type 0x00 (standard), not DOBT-specific type.

   Executable: ``tests/ecu/test_interop_regression.py::TestInteropRegressions::test_standard_doip_not_dobt``
