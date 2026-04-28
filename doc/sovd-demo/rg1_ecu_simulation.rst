RG-1 — ECU Simulation
=====================

ECU-side requirements for the POSIX-FreeRTOS OpenBSW reference application.

.. contents::
   :local:
   :depth: 1

.. req:: ECU builds as POSIX-FreeRTOS overlay without patching upstream
   :id: REQ_RG1_001
   :status: done
   :tags: rg1, ecu-simulation
   :satisfies: SPEC_ARCH_ECU

   ECU builds as a POSIX-FreeRTOS overlay without patching upstream OpenBSW.
   CMake overlay adds ``app.sovdDemo.elf`` alongside ``app.referenceApp.elf``.
   DoIP interop fix also lives in the overlay (see RG-6.1).

.. req:: ECU exposes a DoIP server on TCP/UDP port 13400
   :id: REQ_RG1_002
   :status: done
   :tags: rg1, ecu-simulation, doip
   :satisfies: SPEC_ARCH_ECU

   ECU exposes a DoIP server (ISO 13400) on TCP/UDP port 13400.
   Logical address ``0x002A``, gateway address ``0x002A``.

.. req:: ECU supports UDS DiagnosticSessionControl (0x10)
   :id: REQ_RG1_003
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS DiagnosticSessionControl (0x10).
   Default (0x01) and Extended (0x03) sessions.

.. req:: ECU supports UDS ReadDataByIdentifier (0x22) for simulated sensors
   :id: REQ_RG1_004
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS ReadDataByIdentifier (0x22) for simulated sensors.
   DIDs 0xCF10, 0xCF11, 0xCF12 with random-walk values.

.. req:: ECU supports UDS ReadDataByIdentifier (0x22) for static data
   :id: REQ_RG1_005
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS ReadDataByIdentifier (0x22) for static data.
   DIDs 0xCF01 (static), 0xCF02 (ADC).

.. req:: ECU supports UDS WriteDataByIdentifier (0x2E)
   :id: REQ_RG1_006
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS WriteDataByIdentifier (0x2E).
   DID 0xCF03, requires extended session.

.. req:: ECU supports UDS ReadDTCInformation (0x19)
   :id: REQ_RG1_007
   :status: done
   :tags: rg1, ecu-simulation, uds, dtc
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS ReadDTCInformation (0x19) subfunctions 0x01, 0x02, 0x06.
   Count-by-mask, list-by-mask, extended-data-by-DTC.

.. req:: ECU supports UDS ClearDiagnosticInformation (0x14)
   :id: REQ_RG1_008
   :status: done
   :tags: rg1, ecu-simulation, uds, dtc
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS ClearDiagnosticInformation (0x14).
   Clears all (0xFFFFFF) or individual DTCs.

.. req:: ECU simulates 5 realistic DTCs with ISO 14229 Annex D status bytes
   :id: REQ_RG1_009
   :status: done
   :tags: rg1, ecu-simulation, dtc
   :satisfies: SPEC_ARCH_ECU

   ECU simulates 5 realistic DTCs with ISO 14229 Annex D status bytes.
   Engine overtemp, battery low, comm fault, sensor malfunction, brake fault.

.. req:: ECU simulates 3 live sensor values with bounded random walk
   :id: REQ_RG1_010
   :status: done
   :tags: rg1, ecu-simulation, sensors
   :satisfies: SPEC_ARCH_ECU

   ECU simulates 3 live sensor values with bounded random walk.
   EngineTemp (70–130 °C), BatteryVoltage (10.0–15.0 V), VehicleSpeed (0–220 km/h).

.. req:: ECU supports UDS TesterPresent (0x3E)
   :id: REQ_RG1_011
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS TesterPresent (0x3E). Keep-alive for sessions.

.. req:: ECU supports UDS RoutineControl (0x31)
   :id: REQ_RG1_012
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS RoutineControl (0x31) start/stop/results.
   Inherited from upstream referenceApp.

.. req:: ECU supports UDS CommunicationControl (0x28)
   :id: REQ_RG1_013
   :status: done
   :tags: rg1, ecu-simulation, uds
   :satisfies: SPEC_ARCH_ECU

   ECU supports UDS CommunicationControl (0x28).
   Inherited from upstream referenceApp.

.. req:: ECU runs on Linux TAP interface for network I/O
   :id: REQ_RG1_014
   :status: done
   :tags: rg1, ecu-simulation, networking
   :satisfies: SPEC_ARCH_ECU

   ECU runs on Linux TAP interface for network I/O.
   tap0 with IP 192.168.0.201/24.
