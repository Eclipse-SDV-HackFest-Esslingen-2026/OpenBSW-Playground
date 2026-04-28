RG-3 Tests — SOVD REST API (Stub CDA)
======================================

Test cases for the Python/FastAPI stub CDA.

.. contents::
   :local:
   :depth: 1

.. test:: Stub CDA provides SOVD v1 API
   :id: TEST_RG3_001
   :status: done
   :tags: rg3, stub-cda, sovd
   :tests: REQ_RG3_001

   Start stub CDA. Verify ``GET /sovd/v1/`` returns valid response.
   Verify Swagger UI is accessible at ``/docs``.

.. test:: Stub CDA translates REST to DoIP/UDS
   :id: TEST_RG3_002
   :status: done
   :tags: rg3, stub-cda, doip
   :tests: REQ_RG3_002

   Request sensor data via stub CDA REST API. Verify data is retrieved from
   running ECU over DoIP/UDS. Compare response values with direct UDS read.

.. test:: Stub CDA Grafana-compatible JSON endpoints
   :id: TEST_RG3_003
   :status: done
   :tags: rg3, stub-cda, grafana
   :tests: REQ_RG3_003

   ``GET /api/sensors/engine_temp``, ``GET /api/faults/list``. Verify JSON
   responses are in Grafana Infinity datasource format.

.. test:: Stub CDA component, fault, and data APIs
   :id: TEST_RG3_004
   :status: done
   :tags: rg3, stub-cda, sovd
   :tests: REQ_RG3_004

   Test component listing, fault reading, fault clearing, and DID reading
   through the stub CDA API endpoints.
