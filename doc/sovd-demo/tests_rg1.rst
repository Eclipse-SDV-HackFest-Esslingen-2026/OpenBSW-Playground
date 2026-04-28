RG-1 Tests — ECU Simulation
============================

Test cases for ECU simulation requirements.

.. contents::
   :local:
   :depth: 1

Build & Overlay Tests
---------------------

.. test:: Verify ECU overlay builds without patching upstream
   :id: TEST_RG1_001
   :status: done
   :tags: rg1, build, ecu
   :tests: REQ_RG1_001

   Run ``cmake --preset posix-freertos-sovd && cmake --build build/posix-freertos-sovd``.
   Verify ``app.sovdDemo.elf`` is produced alongside ``app.referenceApp.elf`` and that
   no upstream OpenBSW source files are modified.

   Verified by CI: ``.github/workflows/build.yml`` (build job).

   Executable: ``tests/ecu/test_rg1_supplementary.py::TestBuildVerification::test_cmake_preset_builds``

.. test:: Verify ECU DoIP server listens on port 13400
   :id: TEST_RG1_002
   :status: done
   :tags: rg1, doip, ecu
   :tests: REQ_RG1_002

   Start ECU process, verify TCP and UDP listeners on port 13400 using
   ``netstat`` or ``ss``. Confirm DoIP Vehicle Identification Response
   contains logical address ``0x002A``.

UDS Service Tests
-----------------

.. test:: DiagnosticSessionControl (0x10) default and extended sessions
   :id: TEST_RG1_003
   :status: done
   :tags: rg1, uds, ecu
   :tests: REQ_RG1_003

   Send UDS 0x10 0x01 (default session) and verify positive response 0x50 0x01.
   Send UDS 0x10 0x03 (extended session) and verify positive response 0x50 0x03.
   Reference: ``openbsw/test/pyTest/uds/test_DiagSession.py``.

.. test:: ReadDataByIdentifier (0x22) for simulated sensor DIDs
   :id: TEST_RG1_004
   :status: done
   :tags: rg1, uds, sensors, ecu
   :tests: REQ_RG1_004

   Read DIDs 0xCF10, 0xCF11, 0xCF12 via UDS 0x22. Verify positive response
   0x62 with valid data bytes. Confirm values change between consecutive reads
   (random walk). Reference: ``openbsw/test/pyTest/uds/test_RDBI.py``.

.. test:: ReadDataByIdentifier (0x22) for static data DIDs
   :id: TEST_RG1_005
   :status: done
   :tags: rg1, uds, ecu
   :tests: REQ_RG1_005

   Read DIDs 0xCF01 and 0xCF02 via UDS 0x22. Verify positive response with
   expected static values.

.. test:: WriteDataByIdentifier (0x2E) requires extended session
   :id: TEST_RG1_006
   :status: done
   :tags: rg1, uds, ecu
   :tests: REQ_RG1_006

   Attempt UDS 0x2E to DID 0xCF03 in default session; verify NRC
   (conditions not correct). Switch to extended session (0x10 0x03), retry
   write; verify positive response 0x6E.
   Reference: ``openbsw/test/pyTest/uds/test_WDBI.py``.

.. test:: ReadDTCInformation (0x19) subfunctions 0x01, 0x02, 0x06
   :id: TEST_RG1_007
   :status: done
   :tags: rg1, uds, dtc, ecu
   :tests: REQ_RG1_007

   Send UDS 0x19 0x01 (count-by-mask), verify DTC count > 0. Send 0x19 0x02
   (list-by-mask), verify DTC list contains known DTCs. Send 0x19 0x06
   (extended-data-by-DTC), verify extended data record returned.

.. test:: ClearDiagnosticInformation (0x14) clears DTCs
   :id: TEST_RG1_008
   :status: done
   :tags: rg1, uds, dtc, ecu
   :tests: REQ_RG1_008

   Read DTC count, clear all DTCs via UDS 0x14 0xFF 0xFF 0xFF, verify positive
   response 0x54. Re-read DTC count and verify it is zero or reduced.

.. test:: ECU simulates 5 DTCs with ISO 14229 Annex D status bytes
   :id: TEST_RG1_009
   :status: done
   :tags: rg1, dtc, ecu
   :tests: REQ_RG1_009

   Read DTC list via 0x19 0x02. Verify exactly 5 DTCs: engine overtemp
   (0x010100), battery low (0x010200), comm fault (0x010300), sensor
   malfunction (0x010400), brake fault (0x010500). Verify status byte bits
   conform to ISO 14229 Annex D.

.. test:: ECU sensor values stay within bounded ranges
   :id: TEST_RG1_010
   :status: done
   :tags: rg1, sensors, ecu
   :tests: REQ_RG1_010

   Read EngineTemp, BatteryVoltage, VehicleSpeed 100 times. Verify
   EngineTemp ∈ [70, 130] °C, BatteryVoltage ∈ [10.0, 15.0] V,
   VehicleSpeed ∈ [0, 220] km/h.

.. test:: TesterPresent (0x3E) keeps session alive
   :id: TEST_RG1_011
   :status: done
   :tags: rg1, uds, ecu
   :tests: REQ_RG1_011

   Enter extended session (0x10 0x03). Send TesterPresent (0x3E 0x00)
   periodically. Verify session does not time out back to default.
   Reference: ``openbsw/test/pyTest/uds/test_TesterPresent.py``.

.. test:: RoutineControl (0x31) start/stop/results
   :id: TEST_RG1_012
   :status: done
   :tags: rg1, uds, ecu
   :tests: REQ_RG1_012

   Send RoutineControl start (0x31 0x01); ECU rejects with NRC since service
   is not implemented. Verify negative response.

   Executable: ``tests/ecu/test_rg1_supplementary.py::TestUnsupportedServices::test_routine_control_rejected``

.. test:: CommunicationControl (0x28) enable/disable
   :id: TEST_RG1_013
   :status: done
   :tags: rg1, uds, ecu
   :tests: REQ_RG1_013

   Send CommunicationControl (0x28); ECU rejects with NRC since service
   is not implemented. Verify negative response.

   Executable: ``tests/ecu/test_rg1_supplementary.py::TestUnsupportedServices::test_communication_control_rejected``

.. test:: ECU runs on TAP interface with correct IP
   :id: TEST_RG1_014
   :status: done
   :tags: rg1, networking, ecu
   :tests: REQ_RG1_014

   After ECU startup, verify ``tap0`` interface exists with IP
   192.168.0.201/24. Ping 192.168.0.201 from host and verify connectivity.
