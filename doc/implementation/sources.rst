Source Implementations
======================

Implementation elements linking architecture specifications to source code.

.. contents::
   :local:
   :depth: 1

ECU Simulation
--------------

.. impl:: ECU overlay application
   :id: IMPL_ECU_APP
   :status: done
   :tags: ecu, overlay
   :implements: SPEC_ARCH_ECU

   POSIX-FreeRTOS ECU overlay application.
   Source: ``OpenBSW-SOVD-Demo/openbsw-overlay/app/``

   - ``include/systems/UdsSystem.h`` — shadows upstream header
   - ``include/uds/DtcSimulator.h`` — DTC simulation logic
   - ``include/uds/ReadIdentifierSimulated.h`` — simulated sensor DIDs
   - ``src/`` — corresponding implementations

.. impl:: ECU DTC and UDS services overlay
   :id: IMPL_ECU_UDS
   :status: done
   :tags: ecu, uds, dtc
   :implements: SPEC_ARCH_ECU

   UDS service implementations for DTC handling (0x19, 0x14).
   Source: ``OpenBSW-SOVD-Demo/openbsw-overlay/libs/uds/``

   - ``include/uds/dtc/`` — DTC model classes
   - ``src/services/`` — ReadDTCInformation, ClearDiagnosticInformation

.. impl:: ECU CMake overlay build
   :id: IMPL_ECU_BUILD
   :status: done
   :tags: ecu, cmake
   :implements: SPEC_ARCH_ECU; SPEC_ARCH_BUILD

   Zero-patch CMake overlay that builds on top of upstream OpenBSW.
   Source: ``OpenBSW-SOVD-Demo/CMakeLists.txt``

   Uses ``add_subdirectory(openbsw)`` and overlay include precedence.

Real CDA
--------

.. impl:: OpenSOVD Classic Diagnostic Adapter
   :id: IMPL_CDA
   :status: done
   :tags: cda, rust
   :implements: SPEC_ARCH_CDA

   Rust/axum CDA binary and configuration.
   Source: ``OpenBSW-SOVD-Demo/real-sovd-cda/``

   - ``opensovd-cda.toml`` — TOML configuration
   - ``bin/opensovd-cda`` — pre-built x86-64 binary (Git LFS)
   - ``Dockerfile`` — multi-stage build with cargo-chef

Stub CDA
--------

.. impl:: Python stub CDA
   :id: IMPL_STUB_CDA
   :status: done
   :tags: cda, python, fastapi
   :implements: SPEC_ARCH_STUB_CDA

   FastAPI-based stub CDA with SOVD v1 API and Grafana-compatible endpoints.
   Source: ``OpenBSW-SOVD-Demo/sovd-cda/``

   - ``main.py`` — FastAPI application
   - ``catalog.json`` — DID/DTC catalog
   - ``requirements.txt`` — Python dependencies

DoIP Interop Fix
-----------------

.. impl:: DoIP server connection handler overlay
   :id: IMPL_DOIP_FIX
   :status: done
   :tags: doip, interop
   :implements: SPEC_ARCH_DOIP; SPEC_ARCH_INTEROP

   DoIP interoperability fix overlay — adds ACK handling to ECU.
   Source: ``OpenBSW-SOVD-Demo/openbsw-overlay/libs/doip/src/doip/server/DoIpServerConnectionHandler.cpp``

   Lines 284-290: added ``case DIAGNOSTIC_MESSAGE_POSITIVE_ACK / NEGATIVE_ACK``
   to ``headerReceived()`` switch. Upstream file remains unmodified.

Build & Deployment
------------------

.. impl:: Demo launch script
   :id: IMPL_DEMO_SCRIPT
   :status: done
   :tags: build, deployment
   :implements: SPEC_ARCH_BUILD

   One-command demo bring-up with mode detection.
   Source: ``OpenBSW-SOVD-Demo/demo.sh``

   Handles TAP setup, ECU launch, CDA start, Grafana orchestration,
   and status monitoring.

.. impl:: Docker Compose orchestration
   :id: IMPL_DOCKER
   :status: done
   :tags: build, docker
   :implements: SPEC_ARCH_BUILD

   Docker Compose configuration with stub-cda and real-cda profiles.
   Source: ``OpenBSW-SOVD-Demo/docker-compose.yaml``

Diagnostic Data Model
---------------------

.. impl:: MDD data model and generator
   :id: IMPL_MDD
   :status: done
   :tags: mdd, odx
   :implements: SPEC_ARCH_MDD

   ECU diagnostic description files.
   Source: ``OpenBSW-SOVD-Demo/real-sovd-cda/odx-gen/``

   - ``openbsw_ecu.json`` — source JSON describing DIDs, DTCs, DoIP params
   - ``generate_mdd.py`` — FlatBuffers + Protobuf MDD generator
   - ``OpenBSW.mdd`` — generated binary MDD file

Observability
-------------

.. impl:: Grafana dashboards
   :id: IMPL_GRAFANA
   :status: done
   :tags: grafana, observability
   :implements: SPEC_ARCH_GRAFANA

   Grafana dashboard definitions and datasource provisioning.
   Source: ``OpenBSW-SOVD-Demo/grafana/``

   - ``dashboards/openbsw.json`` — real CDA dashboard (UID: openbsw-sovd-demo)
   - ``dashboards/openbsw-stub.json`` — stub CDA dashboard (UID: openbsw-stub-cda)
   - ``provisioning/datasources/sovd.yaml`` — Infinity datasource config
