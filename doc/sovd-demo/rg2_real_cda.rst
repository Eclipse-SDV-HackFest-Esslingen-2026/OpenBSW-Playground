RG-2 — SOVD REST API (Real CDA)
================================

Requirements for the Eclipse OpenSOVD Classic Diagnostic Adapter integration.

.. contents::
   :local:
   :depth: 1

.. req:: CDA translates SOVD REST calls to UDS/DoIP diagnostic commands
   :id: REQ_RG2_001
   :status: done
   :tags: rg2, real-cda, sovd
   :satisfies: SPEC_ARCH_CDA

   CDA translates SOVD REST calls to UDS/DoIP diagnostic commands.
   Rust / axum server on port 8080.

.. req:: CDA discovers ECU via DoIP Vehicle Identification Request
   :id: REQ_RG2_002
   :status: done
   :tags: rg2, real-cda, doip
   :satisfies: SPEC_ARCH_CDA

   CDA discovers ECU via DoIP Vehicle Identification Request (VIR).
   UDP broadcast, gateway found at 192.168.0.201.

.. req:: CDA activates DoIP routing to ECU logical address
   :id: REQ_RG2_003
   :status: done
   :tags: rg2, real-cda, doip
   :satisfies: SPEC_ARCH_CDA

   CDA activates DoIP routing to ECU logical address.
   Tester 0x0EE0 → ECU 0x002A.

.. req:: CDA exposes component listing at /vehicle/v15/components
   :id: REQ_RG2_004
   :status: done
   :tags: rg2, real-cda, sovd
   :satisfies: SPEC_ARCH_CDA

   CDA exposes component listing at ``/vehicle/v15/components``.
   Returns ``openbsw`` component.

.. req:: CDA exposes data identifier listing at .../data
   :id: REQ_RG2_005
   :status: done
   :tags: rg2, real-cda, sovd
   :satisfies: SPEC_ARCH_CDA

   CDA exposes data identifier listing at ``.../data``.
   7 DIDs listed (names from MDD).

.. req:: CDA reads individual DIDs at .../data/{name}
   :id: REQ_RG2_006
   :status: done
   :tags: rg2, real-cda, sovd
   :satisfies: SPEC_ARCH_CDA

   CDA reads individual DIDs at ``.../data/{name}``.
   EngineTemp, BatteryVoltage, VehicleSpeed, StaticData, ADC_Value verified.

.. req:: CDA reads fault memory at .../faults
   :id: REQ_RG2_007
   :status: done
   :tags: rg2, real-cda, sovd, dtc
   :satisfies: SPEC_ARCH_CDA

   CDA reads fault memory at ``.../faults``.
   5 DTCs returned with full status mask.

.. req:: CDA provides health endpoint
   :id: REQ_RG2_008
   :status: done
   :tags: rg2, real-cda, sovd
   :satisfies: SPEC_ARCH_CDA

   CDA provides health endpoint.
   ``GET /health`` → ``{"status":"Up"}``.

.. req:: CDA requires JWT Bearer token for diagnostic endpoints
   :id: REQ_RG2_009
   :status: done
   :tags: rg2, real-cda, security
   :satisfies: SPEC_ARCH_CDA

   CDA requires JWT Bearer token for diagnostic endpoints.
   ``POST /vehicle/v15/authorize`` with any credentials.

.. req:: CDA loads ECU diagnostic description from MDD file
   :id: REQ_RG2_010
   :status: done
   :tags: rg2, real-cda, mdd
   :satisfies: SPEC_ARCH_CDA; SPEC_ARCH_MDD

   CDA loads ECU diagnostic description from MDD (FlatBuffers) file.
   ``OpenBSW.mdd`` pre-generated from ``openbsw_ecu.json``.

.. req:: CDA falls back to base variant when variant detection fails
   :id: REQ_RG2_011
   :status: done
   :tags: rg2, real-cda
   :satisfies: SPEC_ARCH_CDA

   CDA falls back to base variant when variant detection fails.
   ``fallback_to_base_variant = true`` in config.
