RG-2 Tests — SOVD REST API (Real CDA)
======================================

Test cases for the Eclipse OpenSOVD Classic Diagnostic Adapter.

.. contents::
   :local:
   :depth: 1

.. test:: CDA translates SOVD REST to UDS/DoIP
   :id: TEST_RG2_001
   :status: manual
   :tags: rg2, cda, sovd
   :tests: REQ_RG2_001

   Send ``GET /vehicle/v15/components/openbsw/data/EngineTemp`` with JWT token.
   Verify JSON response contains sensor value. Confirm CDA issued UDS 0x22 0xCF10
   over DoIP (visible in ECU logs).

.. test:: CDA discovers ECU via DoIP VIR
   :id: TEST_RG2_002
   :status: manual
   :tags: rg2, cda, doip
   :tests: REQ_RG2_002

   Start CDA with ECU running. Check CDA logs for successful Vehicle
   Identification Response from 192.168.0.201 with logical address 0x002A.

.. test:: CDA activates DoIP routing to ECU
   :id: TEST_RG2_003
   :status: manual
   :tags: rg2, cda, doip
   :tests: REQ_RG2_003

   Verify CDA logs show routing activation success: tester 0x0EE0 → ECU 0x002A.
   Verify subsequent diagnostic messages are acknowledged.

.. test:: CDA component listing endpoint
   :id: TEST_RG2_004
   :status: manual
   :tags: rg2, cda, sovd
   :tests: REQ_RG2_004

   ``GET /vehicle/v15/components`` with JWT token. Verify response contains
   ``openbsw`` component. Reference: ``demo.sh check_cda()``.

.. test:: CDA data identifier listing
   :id: TEST_RG2_005
   :status: manual
   :tags: rg2, cda, sovd
   :tests: REQ_RG2_005

   ``GET /vehicle/v15/components/openbsw/data`` with JWT token. Verify 7 DIDs
   are listed with names from MDD.

.. test:: CDA reads individual DIDs
   :id: TEST_RG2_006
   :status: manual
   :tags: rg2, cda, sovd
   :tests: REQ_RG2_006

   Read each DID individually: EngineTemp, BatteryVoltage, VehicleSpeed,
   StaticData, ADC_Value. Verify each returns valid JSON with data values.

.. test:: CDA reads fault memory
   :id: TEST_RG2_007
   :status: manual
   :tags: rg2, cda, sovd, dtc
   :tests: REQ_RG2_007

   ``GET /vehicle/v15/components/openbsw/faults`` with JWT token. Verify
   5 DTCs returned with DTC code, name, and status mask fields.
   Reference: ``demo.sh get_dtc_count()``.

.. test:: CDA health endpoint
   :id: TEST_RG2_008
   :status: manual
   :tags: rg2, cda, health
   :tests: REQ_RG2_008

   ``GET /health`` without authentication. Verify response ``{"status":"Up"}``.
   Reference: ``demo.sh check_cda()``.

.. test:: CDA JWT authentication required
   :id: TEST_RG2_009
   :status: manual
   :tags: rg2, cda, security
   :tests: REQ_RG2_009

   Call diagnostic endpoints without Authorization header; verify 401/403.
   ``POST /vehicle/v15/authorize`` with credentials; verify JWT token returned.
   Retry with ``Authorization: Bearer <token>``; verify 200.

.. test:: CDA loads MDD file correctly
   :id: TEST_RG2_010
   :status: manual
   :tags: rg2, cda, mdd
   :tests: REQ_RG2_010

   Verify CDA starts without MDD-related errors in logs. Verify DID names in
   ``/data`` listing match MDD definitions from ``OpenBSW.mdd``.

.. test:: CDA falls back to base variant
   :id: TEST_RG2_011
   :status: manual
   :tags: rg2, cda
   :tests: REQ_RG2_011

   Verify config has ``fallback_to_base_variant = true``. Start CDA with ECU
   that does not support variant detection. Verify CDA connects and serves
   data successfully using base variant.
