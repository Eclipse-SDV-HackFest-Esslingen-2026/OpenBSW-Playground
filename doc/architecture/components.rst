Architecture Components
=======================

.. contents::
   :local:
   :depth: 1

ECU Simulation
--------------

.. spec:: OpenBSW ECU
   :id: SPEC_ARCH_ECU
   :status: done
   :tags: ecu, posix-freertos, lwip, uds, doip

   POSIX-FreeRTOS based ECU simulation using the OpenBSW reference application.
   Provides UDS diagnostic services (0x10, 0x22, 0x2E, 0x19, 0x14, 0x31, 0x28,
   0x3E) over a DoIP server on TCP/UDP port 13400. Runs on a Linux TAP interface
   with the lwIP userspace TCP/IP stack. Logical address 0x002A, IP 192.168.0.201.

SOVD Classic Diagnostic Adapter
--------------------------------

.. spec:: OpenSOVD CDA (Rust)
   :id: SPEC_ARCH_CDA
   :status: done
   :tags: cda, rust, axum, sovd, doip

   Eclipse OpenSOVD Classic Diagnostic Adapter. Rust/axum HTTP server on port 8080
   that translates SOVD REST API calls to UDS/DoIP diagnostic commands. Discovers
   ECU via DoIP Vehicle Identification Request, activates routing, and exposes
   component, data, and fault endpoints. Requires JWT Bearer token authentication.
   Loads ECU diagnostic description from MDD (FlatBuffers) file.

Python Stub CDA
----------------

.. spec:: Python Stub CDA
   :id: SPEC_ARCH_STUB_CDA
   :status: done
   :tags: cda, python, fastapi, stub

   FastAPI-based stub CDA providing SOVD v1 API at ``/sovd/v1/``. Translates REST
   to DoIP/UDS via direct socket implementation. Exposes Grafana-compatible JSON
   endpoints for sensor data and faults.

DoIP Transport
--------------

.. spec:: DoIP Transport Layer
   :id: SPEC_ARCH_DOIP
   :status: done
   :tags: doip, iso13400, transport

   ISO 13400-2 DoIP transport layer between ECU and CDA. Handles routing
   activation (tester 0x0EE0, activation type 0x00), DiagnosticMessage (0x8001)
   exchange, and positive/negative ACK handling. Uses standard DoIP protocol
   (not DOBT). TAP-based networking provides L2 connectivity on POSIX via the
   lwIP userspace TCP/IP stack.

Build & Deployment
------------------

.. spec:: Build and Deployment System
   :id: SPEC_ARCH_BUILD
   :status: done
   :tags: build, docker, cmake, demo

   Build and deployment infrastructure including ``demo.sh`` for one-command
   bring-up, multi-stage Docker builds, Docker Compose orchestration with profiles,
   CMake overlay strategy (zero-patch on upstream OpenBSW), GitHub Codespaces
   support, and local Ubuntu mode.

Interoperability Fixes
----------------------

.. spec:: Interoperability Fixes
   :id: SPEC_ARCH_INTEROP
   :status: done
   :tags: interop, doip, fixes

   Resolved integration issues between OpenBSW ECU and OpenSOVD CDA. Includes
   DoIP ACK handling overlay, CDA diagnostic ACK suppression, send timeout
   adjustment for lwIP timing, SIGTTOU handling for background process launch,
   and standard DoIP (non-DOBT) configuration.

Diagnostic Data Model
---------------------

.. spec:: Diagnostic Data Model (MDD/ODX)
   :id: SPEC_ARCH_MDD
   :status: done
   :tags: mdd, odx, flatbuffers, diagnostic

   ECU diagnostic description using MDD (Machine-readable Diagnostic Description)
   in FlatBuffers format. Describes 7 DIDs with SID + DID hex values, 5 DTCs with
   DTC numbers, DoIP communication parameters, and supports both DoIP and DoIP-DOBT
   protocol entries. Regenerable from ``openbsw_ecu.json`` via ``generate_mdd.py``.

Observability & Dashboard
--------------------------

.. spec:: Observability and Dashboard
   :id: SPEC_ARCH_GRAFANA
   :status: done
   :tags: grafana, observability, dashboard

   Monitoring and visualization infrastructure. Grafana dashboards for live sensor
   data and active faults (real CDA mode), separate dashboard for stub CDA,
   ASCII status dashboard in ``demo.sh --status``, and log file capture at
   ``/tmp/openbsw-demo.log``.
