# SOVD Demo — Requirements Summary

A MECE (Mutually Exclusive, Collectively Exhaustive) checklist of all
requirements the demo fulfils, grouped by domain.

---

## RG-1 — ECU Simulation

ECU-side requirements for the POSIX-FreeRTOS OpenBSW reference application.

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-1.1 | ECU builds as a POSIX-FreeRTOS overlay without patching upstream OpenBSW | Done | CMake overlay adds `app.sovdDemo.elf` alongside `app.referenceApp.elf`. DoIP interop fix also lives in the overlay (see RG-6.1). |
| RG-1.2 | ECU exposes a DoIP server (ISO 13400) on TCP/UDP port 13400 | Done | Logical address `0x002A`, gateway address `0x002A` |
| RG-1.3 | ECU supports UDS DiagnosticSessionControl (0x10) | Done | Default (0x01) and Extended (0x03) sessions |
| RG-1.4 | ECU supports UDS ReadDataByIdentifier (0x22) for simulated sensors | Done | DIDs 0xCF10, 0xCF11, 0xCF12 with random-walk values |
| RG-1.5 | ECU supports UDS ReadDataByIdentifier (0x22) for static data | Done | DIDs 0xCF01 (static), 0xCF02 (ADC) |
| RG-1.6 | ECU supports UDS WriteDataByIdentifier (0x2E) | Done | DID 0xCF03, requires extended session |
| RG-1.7 | ECU supports UDS ReadDTCInformation (0x19) subfunctions 0x01, 0x02, 0x06 | Done | Count-by-mask, list-by-mask, extended-data-by-DTC |
| RG-1.8 | ECU supports UDS ClearDiagnosticInformation (0x14) | Done | Clears all (0xFFFFFF) or individual DTCs |
| RG-1.9 | ECU simulates 5 realistic DTCs with ISO 14229 Annex D status bytes | Done | Engine overtemp, battery low, comm fault, sensor malfunction, brake fault |
| RG-1.10 | ECU simulates 3 live sensor values with bounded random walk | Done | EngineTemp (70–130 °C), BatteryVoltage (10.0–15.0 V), VehicleSpeed (0–220 km/h) |
| RG-1.11 | ECU supports UDS TesterPresent (0x3E) | Done | Keep-alive for sessions |
| RG-1.12 | ECU supports UDS RoutineControl (0x31) start/stop/results | Done | Inherited from upstream referenceApp |
| RG-1.13 | ECU supports UDS CommunicationControl (0x28) | Done | Inherited from upstream referenceApp |
| RG-1.14 | ECU runs on Linux TAP interface for network I/O | Done | tap0 with IP 192.168.0.201/24 |

---

## RG-2 — SOVD REST API (Real CDA)

Requirements for the Eclipse OpenSOVD Classic Diagnostic Adapter integration.

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-2.1 | CDA translates SOVD REST calls to UDS/DoIP diagnostic commands | Done | Rust / axum server on port 8080 |
| RG-2.2 | CDA discovers ECU via DoIP Vehicle Identification Request (VIR) | Done | UDP broadcast, gateway found at 192.168.0.201 |
| RG-2.3 | CDA activates DoIP routing to ECU logical address | Done | Tester 0x0EE0 → ECU 0x002A |
| RG-2.4 | CDA exposes component listing at `/vehicle/v15/components` | Done | Returns `openbsw` component |
| RG-2.5 | CDA exposes data identifier listing at `.../data` | Done | 7 DIDs listed (names from MDD) |
| RG-2.6 | CDA reads individual DIDs at `.../data/{name}` | Done | EngineTemp, BatteryVoltage, VehicleSpeed, StaticData, ADC_Value verified |
| RG-2.7 | CDA reads fault memory at `.../faults` | Done | 5 DTCs returned with full status mask |
| RG-2.8 | CDA provides health endpoint | Done | `GET /health` → `{"status":"Up"}` |
| RG-2.9 | CDA requires JWT Bearer token for diagnostic endpoints | Done | `POST /vehicle/v15/authorize` with any credentials |
| RG-2.10 | CDA loads ECU diagnostic description from MDD (FlatBuffers) file | Done | `OpenBSW.mdd` pre-generated from `openbsw_ecu.json` |
| RG-2.11 | CDA falls back to base variant when variant detection fails | Done | `fallback_to_base_variant = true` in config |

---

## RG-3 — SOVD REST API (Python Stub CDA)

Requirements for the Python/FastAPI stub CDA (alternative to real CDA).

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-3.1 | Stub CDA provides SOVD v1 API at `/sovd/v1/` | Done | FastAPI with Swagger UI at `/docs` |
| RG-3.2 | Stub CDA translates REST to DoIP/UDS for ECU communication | Done | Direct socket implementation |
| RG-3.3 | Stub CDA exposes Grafana-compatible JSON endpoints | Done | `/api/sensors/*`, `/api/faults/*` |
| RG-3.4 | Stub CDA provides component, fault, and data APIs | Done | Read, clear faults; read DIDs |

---

## RG-4 — DoIP Communication

Requirements for the DoIP (ISO 13400) transport layer between ECU and CDA.

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-4.1 | DoIP routing activation succeeds between CDA (tester) and ECU | Done | Tester 0x0EE0, activation type 0x00 |
| RG-4.2 | DoIP diagnostic messages (0x8001) flow bidirectionally | Done | Request from CDA, response from ECU |
| RG-4.3 | ECU sends DiagnosticMessagePositiveAck (0x8002) for valid requests | Done | Sent before UDS response |
| RG-4.4 | ECU silently consumes tester-originated 0x8002/0x8003 ACKs | Done | Overlay `DoIpServerConnectionHandler.cpp` lines 284-290 — see [RG-6.1] |
| RG-4.5 | DoIP communication uses standard protocol (not DOBT) | Done | `onboard_tester = false` |
| RG-4.6 | TAP-based networking provides L2 connectivity on POSIX | Done | lwIP userspace TCP/IP stack over tap0 |

---

## RG-5 — Build & Deployment

Requirements for building, packaging, and running the demo.

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-5.1 | `demo.sh` provides one-command bring-up with `--real-cda` flag | Done | Sets up TAP, builds ECU, starts CDA Docker container |
| RG-5.2 | Multi-stage Docker build for CDA minimises image size | Done | cargo-chef + sccache for layer caching |
| RG-5.3 | Docker Compose orchestrates ECU + CDA + Grafana with profiles | Done | `--profile stub-cda` or `--profile real-cda` |
| RG-5.4 | ECU build is reproducible from CMake preset | Done | `cmake --preset posix-freertos-sovd` |
| RG-5.5 | Demo runs in GitHub Codespaces with port forwarding | Done | `demo.sh --codespaces` mode |
| RG-5.6 | Demo runs locally on Ubuntu with sudo for TAP setup | Done | `demo.sh --local` or `demo.sh --real-cda` |
| RG-5.7 | `demo.sh --stop` tears down all processes cleanly | Done | Kills ECU, CDA container, TAP interface |
| RG-5.8 | Live tmux status dashboard shows connection health | Done | `demo.sh --live` with auto-refresh |
| RG-5.9 | Pre-built CDA binary checked into repo via Git LFS | Done | `real-sovd-cda/bin/opensovd-cda` (~26 MB, x86-64), Dockerfile supports `USE_PREBUILT=1` |
| RG-5.10 | `demo.sh` auto-detects stub vs real CDA mode | Done | Checks for `real-sovd-cda` Docker container or stub PID file |

---

## RG-6 — Interoperability Fixes

Resolved integration issues between OpenBSW ECU and OpenSOVD CDA.

| ID | Requirement | Status | Root Cause | Solution |
|:---|:---|:---:|:---|:---|
| RG-6.1 | ECU handles tester-originated DiagnosticMessageAck payloads | Done | CDA sends 0x8002 back; ECU NACKed with 0x01 (unknown type) | Overlay: `openbsw-overlay/libs/doip/src/doip/server/DoIpServerConnectionHandler.cpp` lines 284-290 — added `case DIAGNOSTIC_MESSAGE_POSITIVE_ACK / NEGATIVE_ACK` to `headerReceived()` switch; upstream file unchanged |
| RG-6.2 | CDA diagnostic ACK does not corrupt DoIP response stream | Done | Unconditional ACK in `handle_response()` confused parsing | Set `send_diagnostic_message_ack = false` in TOML |
| RG-6.3 | CDA send timeout accommodates lwIP userspace TCP timing | Done | Default 1 s timeout too short for POSIX lwIP stack | Increased `send_timeout_ms = 5000` |
| RG-6.4 | ECU does not stop when launched as background process | Done | `Uart::init()` calls `tcsetattr()` → SIGTTOU stops process | Trap SIGTTOU, redirect stdin from `/dev/null` |
| RG-6.5 | CDA uses standard DoIP (not DOBT) matching ECU implementation | Done | DOBT uses different routing activation type | Set `onboard_tester = false` |

---

## RG-7 — Diagnostic Data Model (MDD / ODX)

Requirements for the ECU diagnostic description used by the CDA.

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-7.1 | MDD describes 7 DIDs with correct SID + DID hex values | Partial | 6 of 7 match ECU; `Identification` uses 0xF100 (ECU has no such DID) |
| RG-7.2 | MDD describes 5 DTCs with DTC numbers matching ECU simulation | Done | 0x010100–0x010500 |
| RG-7.3 | MDD describes DoIP communication parameters | Done | Gateway 0x002A, tester 0x0EE0, functional 0xFFFF |
| RG-7.4 | MDD supports both DoIP and DoIP-DOBT protocol entries | Done | Dual `com_param_refs` in JSON |
| RG-7.5 | MDD is regenerable from `openbsw_ecu.json` via `generate_mdd.py` | Done | FlatBuffers + Protobuf toolchain |

---

## RG-8 — Observability & Dashboard

Requirements for monitoring, visualization, and operational visibility.

| ID | Requirement | Status | Notes |
|:---|:---|:---:|:---|
| RG-8.1 | Grafana dashboard displays live sensor data (real CDA) | Done | Gauges for temp, voltage, speed via `/vehicle/v15/...` with JWT auth |
| RG-8.2 | Grafana dashboard displays active faults (real CDA) | Done | Table with DTC code, name, status mask |
| RG-8.3 | Status dashboard shows ECU / CDA / DoIP / Grafana health | Done | ASCII art, colour-coded in `demo.sh --status`, auto-detects CDA mode |
| RG-8.4 | Log file captures ECU + CDA output for debugging | Done | `/tmp/openbsw-demo.log` |
| RG-8.5 | Separate Grafana dashboard for stub CDA | Done | `openbsw-stub.json` with `/api/sensors/...` endpoints, no auth |

---

## Summary

| Group | Total | Done | Partial | Open |
|:---|:---:|:---:|:---:|:---:|
| RG-1 ECU Simulation | 14 | 14 | 0 | 0 |
| RG-2 Real CDA | 11 | 11 | 0 | 0 |
| RG-3 Stub CDA | 4 | 4 | 0 | 0 |
| RG-4 DoIP Communication | 6 | 6 | 0 | 0 |
| RG-5 Build & Deployment | 10 | 10 | 0 | 0 |
| RG-6 Interop Fixes | 5 | 5 | 0 | 0 |
| RG-7 Data Model (MDD) | 5 | 4 | 1 | 0 |
| RG-8 Observability | 5 | 5 | 0 | 0 |
| **Total** | **60** | **59** | **1** | **0** |
