RG-8 — Observability & Dashboard
=================================

Requirements for monitoring, visualization, and operational visibility.

.. contents::
   :local:
   :depth: 1

.. req:: Grafana dashboard displays live sensor data (real CDA)
   :id: REQ_RG8_001
   :status: done
   :tags: rg8, observability, grafana
   :satisfies: SPEC_ARCH_GRAFANA

   Grafana dashboard displays live sensor data (real CDA).
   Gauges for temp, voltage, speed via ``/vehicle/v15/...`` with JWT auth.

.. req:: Grafana dashboard displays active faults (real CDA)
   :id: REQ_RG8_002
   :status: done
   :tags: rg8, observability, grafana
   :satisfies: SPEC_ARCH_GRAFANA

   Grafana dashboard displays active faults (real CDA).
   Table with DTC code, name, status mask.

.. req:: Status dashboard shows ECU / CDA / DoIP / Grafana health
   :id: REQ_RG8_003
   :status: done
   :tags: rg8, observability, status
   :satisfies: SPEC_ARCH_GRAFANA

   Status dashboard shows ECU / CDA / DoIP / Grafana health.
   ASCII art, colour-coded in ``demo.sh --status``, auto-detects CDA mode.

.. req:: Log file captures ECU + CDA output for debugging
   :id: REQ_RG8_004
   :status: done
   :tags: rg8, observability, logging
   :satisfies: SPEC_ARCH_GRAFANA

   Log file captures ECU + CDA output for debugging.
   ``/tmp/openbsw-demo.log``.

.. req:: Separate Grafana dashboard for stub CDA
   :id: REQ_RG8_005
   :status: done
   :tags: rg8, observability, grafana
   :satisfies: SPEC_ARCH_GRAFANA

   Separate Grafana dashboard for stub CDA.
   ``openbsw-stub.json`` with ``/api/sensors/...`` endpoints, no auth.
