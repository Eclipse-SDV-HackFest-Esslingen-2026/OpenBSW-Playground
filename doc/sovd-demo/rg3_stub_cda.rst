RG-3 — SOVD REST API (Python Stub CDA)
=======================================

Requirements for the Python/FastAPI stub CDA (alternative to real CDA).

.. contents::
   :local:
   :depth: 1

.. req:: Stub CDA provides SOVD v1 API at /sovd/v1/
   :id: REQ_RG3_001
   :status: done
   :tags: rg3, stub-cda, sovd
   :satisfies: SPEC_ARCH_STUB_CDA

   Stub CDA provides SOVD v1 API at ``/sovd/v1/``.
   FastAPI with Swagger UI at ``/docs``.

.. req:: Stub CDA translates REST to DoIP/UDS for ECU communication
   :id: REQ_RG3_002
   :status: done
   :tags: rg3, stub-cda, doip
   :satisfies: SPEC_ARCH_STUB_CDA

   Stub CDA translates REST to DoIP/UDS for ECU communication.
   Direct socket implementation.

.. req:: Stub CDA exposes Grafana-compatible JSON endpoints
   :id: REQ_RG3_003
   :status: done
   :tags: rg3, stub-cda, grafana
   :satisfies: SPEC_ARCH_STUB_CDA

   Stub CDA exposes Grafana-compatible JSON endpoints.
   ``/api/sensors/*``, ``/api/faults/*``.

.. req:: Stub CDA provides component, fault, and data APIs
   :id: REQ_RG3_004
   :status: done
   :tags: rg3, stub-cda, sovd
   :satisfies: SPEC_ARCH_STUB_CDA

   Stub CDA provides component, fault, and data APIs.
   Read, clear faults; read DIDs.
