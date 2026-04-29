# SOVD Demo — Architecture & Design

This document describes the architecture of the OpenBSW + SOVD demo, the key
design choices made during integration, and the DoIP communication flow
including error patterns encountered and their solutions.

> **Requirements traceability**: Each section references the corresponding
> requirement group from [`requirements-summary.md`](requirements-summary.md).

---

## 1. System Architecture

*Covers: [RG-1], [RG-2], [RG-4], [RG-5]*

```mermaid
flowchart TB
  subgraph host[Host / Dev-Container]
        ecu["OpenBSW ECU (C++)<br/>app.sovdDemo.elf<br/>POSIX-FreeRTOS<br/>lwIP TCP/IP stack<br/>Logical addr: 0x002A<br/>IP: 192.168.0.201"]
        cda["OpenSOVD CDA (Rust)<br/>opensovd-cda<br/>axum HTTP server<br/>DoIP client<br/>Tester addr: 0x0EE0<br/>IP: 192.168.0.10"]
        bridge["doip-net bridge<br/>(or host networking for local mode)"]
        grafana["Grafana<br/>192.168.0.100<br/>:3000<br/>Infinity datasource"]
  end

  ecu <-->|DoIP TCP :13400 over tap0| cda
  ecu -->|tap0 (L2 TAP interface)<br/>192.168.0.0/24 subnet| bridge
  cda --> bridge
  bridge --> grafana

    sovd["External access<br/>SOVD API: http://localhost:8080/vehicle/v15/..."] -->|REST :8080| cda
    ui["External access<br/>Grafana: http://localhost:3000"] --> grafana
```

### Component Summary

| Component | Technology | Role |
|:---|:---|:---|
| **OpenBSW ECU** | C++, POSIX-FreeRTOS, lwIP | Simulates ECU with UDS diagnostic services over DoIP |
| **OpenSOVD CDA** | Rust, axum, tokio | Translates SOVD REST API to UDS/DoIP diagnostic commands |
| **Grafana** | Docker, Infinity datasource | Visualises live sensor data and faults |
| **tap0** | Linux TAP interface | Provides L2 Ethernet connectivity for the ECU's lwIP stack |
| **MDD file** | FlatBuffers binary | ECU diagnostic description consumed by the CDA |

---

## 2. Software Stack Layers

*Covers: [RG-1], [RG-2], [RG-4]*

```mermaid
flowchart TB
    client["SOVD Client<br/>(curl / Grafana / Browser)"] -->|HTTP / JSON| rest
    rest["SOVD REST Layer<br/>/vehicle/v15/components/...<br/>JWT Bearer authentication<br/>axum router (cda-sovd)"] --> uds
    uds["UDS Application Layer<br/>Service dispatch (cda-comm-uds)<br/>MDD-driven request encoding<br/>Variant detection / fallback"] --> doip
    doip["DoIP Transport Layer<br/>ISO 13400-2 framing (cda-comm-doip)<br/>Routing activation, alive check<br/>DiagnosticMessage (0x8001) exchange"] --> tcp
    tcp["TCP/IP (Kernel / lwIP)<br/>CDA: kernel TCP socket<br/>ECU: lwIP userspace TCP/IP over TAP"] --> l2
    l2["L2 Ethernet (tap0)<br/>Linux TAP interface<br/>192.168.0.0/24"]
```

---

## 3. CMake Overlay Strategy (Zero-Patch)

*Covers: [RG-1.1], [RG-5.4]*

The demo builds on top of upstream OpenBSW without modifying its source tree:

```mermaid
flowchart TD
    root["OpenBSW-SOVD-Demo"]
    cmake["CMakeLists.txt<br/>add_subdirectory(openbsw)<br/>add_library(uds_dtc_overlay)<br/>add_executable(app.sovdDemo)"]
    include_order["target_include_directories<br/>openbsw-overlay/app/include first<br/>UdsSystem.h shadows upstream"]
    overlay["openbsw-overlay"]
    overlay_app["app/include and src<br/>systems/UdsSystem.h replaces upstream header<br/>DtcSimulator.h<br/>ReadIdentifierSimulated.h<br/>corresponding implementations"]
    overlay_uds["libs/uds<br/>include/uds/dtc<br/>src/services<br/>UDS 0x19 and 0x14 implementations"]
    overlay_doip["libs/doip/src/doip/server<br/>DoIpServerConnectionHandler.cpp<br/>DoIP interop fix at lines 284-290"]
    upstream["openbsw<br/>Upstream (unmodified)"]

    root --> cmake
    root --> overlay
    root --> upstream
    cmake -->|Adds all upstream library targets| upstream
    cmake --> include_order
    overlay --> overlay_app
    overlay --> overlay_uds
    overlay --> overlay_doip
    overlay_doip -->|Injected in place of upstream source| upstream
```

**Key insights**:

1. The overlay include path takes precedence over the upstream include path.
   The demo's `UdsSystem.h` shadows the upstream version.
2. For the DoIP fix, the upstream `DoIpServerConnectionHandler.cpp` is excluded
   from the `doip` library target via `SOURCES` property manipulation, and the
   overlay copy (with the interop fix) is injected in its place. The upstream
   file remains **completely unmodified**.

All other upstream sources are compiled as-is.

---

## 4. DoIP Communication Flows

*Covers: [RG-4], [RG-6]*

### 4.1 Good Case — Successful DID Read

This is the working end-to-end flow for reading a sensor value
(e.g. `GET /vehicle/v15/components/openbsw/data/EngineTemp`):

```mermaid
sequenceDiagram
    participant Client
    participant CDA as CDA (Rust)
    participant ECU as ECU (OpenBSW)

    Client->>CDA: POST /authorize\n{"client_id":"test"...}
    CDA-->>Client: {"access_token":"JWT"}
    Client->>CDA: GET .../data/EngineTemp\nAuthorization: Bearer..
    CDA->>ECU: DoIP DiagnosticMessage (0x8001)\n[0x0EE0 -> 0x002A]\nUDS 0x22 0xCF 0x10
    ECU-->>CDA: DoIP DiagPositiveAck (0x8002)\n[0x002A -> 0x0EE0]
    ECU-->>CDA: DoIP DiagnosticMessage (0x8001)\n[0x002A -> 0x0EE0]\nUDS 0x62 0xCF 0x10 <val>
    Note over CDA: ACK suppressed by config
    CDA-->>Client: {"id":"enginetemp","data":{"EngineTemp":121}}
```

**Key points**:
- ECU sends `DiagnosticMessagePositiveAck` (0x8002) to confirm receipt
- ECU sends UDS positive response `0x62` (SID + 0x40) with the DID data
- CDA's outbound ACK to the ECU is suppressed (`send_diagnostic_message_ack = false`)

### 4.2 Good Case — Fault Memory Read

```mermaid
sequenceDiagram
    participant Client
    participant CDA as CDA (Rust)
    participant ECU as ECU (OpenBSW)

    Client->>CDA: GET .../faults\nAuthorization: Bearer..
    CDA->>ECU: DiagMsg: UDS 0x19 0x02 0xFF\n(ReadDTCInfo, reportByStatusMask)
    ECU-->>CDA: DiagPosAck (0x8002)
    ECU-->>CDA: DiagMsg: UDS 0x59 0x02 ...\n(5 DTCs x 4 bytes each)
    CDA-->>Client: {"items":[{"code":"010100","fault_name":"Engine Coolant...","status":{...}}, ... 4 more DTCs]}
```

### 4.3 Good Case — DoIP Connection Establishment

```mermaid
sequenceDiagram
    participant CDA as CDA (Tester)
    participant ECU as ECU (DoIP Server)

    CDA->>ECU: UDP Vehicle Identification Request (VIR)\nBroadcast to 255.255.255.255:13400
    ECU-->>CDA: UDP Vehicle Announcement Message (VAM)\nLogicalAddr=0x002A, VIN, EID, GID
    CDA->>ECU: TCP connect to 192.168.0.201:13400
    CDA->>ECU: DoIP Routing Activation Request (0x0005)\nSourceAddr=0x0EE0, ActivationType=0x00
    ECU-->>CDA: DoIP Routing Activation Response (0x0006)\nTesterAddr=0x0EE0, Status=0x10 (success)
    Note over CDA,ECU: Connection ACTIVE\nReady for DiagnosticMessage exchange
```

---

## 5. Error Patterns & Solutions

*Covers: [RG-6]*

### 5.1 ERR-1: DoIP Generic NACK on DiagnosticMessageAck (RESOLVED)

**Root cause**: After receiving a UDS response from the ECU, the CDA sends a
`DiagnosticMessagePositiveAck` (payload type `0x8002`) back on the TCP stream.
The ECU's `DoIpServerConnectionHandler::headerReceivedDefault()` did not
recognise this payload type and responded with Generic NACK code `0x01`
(unknown payload type).

**Impact**: The NACK corrupted the CDA's response stream. Subsequent UDS
requests would either timeout or receive garbled data.

*Requirement: [RG-6.1], [RG-6.2]*

```mermaid
sequenceDiagram
    participant CDA as CDA (Tester)
    participant ECU as ECU (DoIP Server)

    CDA->>ECU: DiagMsg 0x8001: UDS 0x22 0xCF 0x01
    Note right of ECU: UDS processes request\nECU ACKs receipt
    ECU-->>CDA: DiagPosAck 0x8002 [ECU -> CDA]
    Note right of ECU: ECU sends response
    ECU-->>CDA: DiagMsg 0x8001: UDS 0x62 0xCF 0x01 <data>
    CDA->>ECU: DiagPosAck 0x8002 [CDA -> ECU]
    Note right of ECU: headerReceived()\npayloadType=0x8002\nnot in switch\nheaderDefault()\nno handler\nNACK 0x01
    ECU-->>CDA: Generic NACK 0x0000: code=0x01
    Note over CDA: Unexpected NACK\nNext request will timeout
```

**Solution (two-sided)**:

```mermaid
flowchart TD
    root["ERR-1 solution"]
    ecu_fix["ECU FIX<br/>DoIpServerConnectionHandler.cpp (OVERLAY)<br/>openbsw-overlay/libs/doip/src/doip/server/DoIpServerConnectionHandler.cpp<br/>lines 284-290<br/>Upstream file unchanged"]
    ecu_impl["Added to headerReceived() switch<br/>case DIAGNOSTIC_MESSAGE_POSITIVE_ACK (0x8002)<br/>case DIAGNOSTIC_MESSAGE_NEGATIVE_ACK (0x8003)<br/>Silently consume tester ACKs<br/>_connection.endReceiveMessage(...)<br/>return HandledByThisHandler{}"]
    cda_fix["CDA FIX<br/>opensovd-cda.toml<br/>[doip]<br/>send_diagnostic_message_ack = false<br/>send_timeout_ms = 5000"]
    cda_note["CDA has two ACK paths<br/>1. DoIPConnection::read() gated by config<br/>2. handle_response() unconditional bug<br/>ECU-side fix handles the unconditional path"]

    root --> ecu_fix --> ecu_impl
    root --> cda_fix --> cda_note
```

### 5.2 ERR-2: ECU Process Stopped (SIGTTOU) (RESOLVED)

**Root cause**: The POSIX FreeRTOS ECU application calls `tcsetattr()` in
`Uart::init()` to disable canonical mode and echo on stdout. When the process
runs in the background (`&`), the kernel delivers `SIGTTOU` (signal 22), whose
default action is to stop the process.

**Impact**: ECU stuck at "Initialize level 1" with process state `Tl`
(stopped + multi-threaded). No FreeRTOS tasks run. No DoIP server.

*Requirement: [RG-6.4]*

```mermaid
sequenceDiagram
    participant Shell
    participant ECU as ECU Process
    participant Kernel

    Shell->>ECU: ./app.sovdDemo.elf &
    Note right of ECU: main() -> app_main() -> staticInit()\nUart::init()
    ECU->>Kernel: tcsetattr(stdout, TCSANOW, ...)
    Note over Kernel: Process is in background and modifies terminal\nKernel sends SIGTTOU
    Kernel-->>ECU: SIGTTOU
    Note right of ECU: SIGTTOU not caught\nProcess STOPPED (state: T)\nAll pthreads frozen\nSIGALRM cannot fire
    Note over Shell: ps shows Tl (stopped)
```

**Solution**:

```mermaid
flowchart TD
    fix["demo.sh FIX"]
    cmd["trap '' SIGTTOU;<br/>./app.sovdDemo.elf < /dev/null >> log 2>&1 &<br/>echo $! > pidfile"]
    sig["trap '' SIGTTOU<br/>ignore the signal"]
    stdin["< /dev/null<br/>no stdin, prevents SIGTTIN"]
    subshell["subshell group<br/>signal trap does not leak"]

    fix --> cmd
    cmd --> sig
    cmd --> stdin
    cmd --> subshell
```

### 5.3 ERR-3: UDS Request Out of Range (DID Mismatch) (KNOWN)

**Root cause**: The MDD file maps `Identification_Read` to DID `0xF100`, but
the ECU only registers DIDs `0xCF01`–`0xCF12`. The ECU returns UDS NRC `0x31`
(requestOutOfRange).

**Impact**: Reading the `Identification` data item fails. All other 6 DIDs
work correctly.

*Requirement: [RG-7.1]*

```mermaid
sequenceDiagram
    participant CDA
    participant ECU

    CDA->>ECU: DiagMsg: 0x22 0xF1 0x00\nIdentification, DID=0xF100
    Note right of ECU: ReadDataByIdentifier for DID 0xF100\nLookup 0xF100 not in diag job table
    ECU-->>CDA: DiagMsg: 0x7F 0x22 0x31\nNRC = requestOutOfRange
    Note over CDA,ECU: Fix: update openbsw_ecu.json to use DID 0xCF01 for Identification, or add DID 0xF100 to the ECU diag job table.
```

### 5.4 ERR-4: Variant Detection Failure (MITIGATED)

**Root cause**: The MDD file defines an empty `variant_pattern: []`. The CDA's
variant detection sends a specific DID read to determine which diagnostic
variant to use. With no pattern, it cannot detect any variant.

**Impact**: CDA logs `Variant detection error: Failed to detect variant:
NotFound(None)`. Falls back to the base variant, which works for this single-ECU
demo but may miss variant-specific services in a multi-variant setup.

*Requirement: [RG-2.11]*

```mermaid
sequenceDiagram
    participant CDA
    participant ECU

    Note over CDA: Startup detect variant\nvariant_pattern is []\nNo DID to read for detection\nResult: NotFound(None)
    Note over CDA: fallback_to_base_variant = true\nUse base OpenBSW diag layer
    Note over CDA,ECU: All services available
```

### 5.5 ERR-5: AliveCheck NACK (30-second interval) (COSMETIC)

**Root cause**: The CDA sends DoIP `AliveCheckRequest` (payload type `0x0007`)
every 30 seconds to verify the gateway is live. The ECU's DoIP server handles
`AliveCheckResponse` (0x0008) from testers but does not handle unsolicited
`AliveCheckRequest` from a tester — it falls to `headerReceivedDefault()` and
NACKs.

**Impact**: Cosmetic — logged as a warning but does not break communication.
The CDA reconnects if it doesn't receive a response.

```mermaid
sequenceDiagram
    participant CDA
    participant ECU

    CDA->>ECU: Every 30 seconds\nDoIP AliveCheckRequest (0x0007)
    Note right of ECU: 0x0007 not in switch\nonly 0x0008 handled
    ECU-->>CDA: Generic NACK 0x0000: code=0x01
    Note over CDA: Received Generic NACK warning\nConnection stays alive\nUDS traffic unaffected
```

### 5.6 ERR-6: Grafana "No Data" — Bridge Network Cannot Reach localhost (RESOLVED)

**Root cause**: In `demo.sh --real-cda` mode, Grafana runs as a Docker
container on the default **bridge** network (with `-p 3000:3000`), while the
CDA runs on **host** networking. The Infinity datasource panel URLs were
configured as `http://localhost:8080`, which inside the bridge-networked
Grafana container resolves to the container itself — not the host where the
CDA listens.

**Impact**: All Grafana dashboard panels showed "No data". The CDA was healthy
and responding to `curl` from the host, but unreachable from Grafana's
perspective.

```mermaid
sequenceDiagram
    participant Grafana as Grafana container (bridge)
    participant Host as Host (CDA on :8080)

    Grafana->>Grafana: Infinity plugin queries\nGET http://localhost:8080/...
    Note right of Grafana: localhost = 127.0.0.1 inside container\nport 8080 not listening\nconnection refused
    Note over Grafana,Host: CDA remains healthy on the host but is unreachable via localhost from the bridge container
    Note over Grafana: Panel result: No data
```

**Solution**: Changed all panel URLs in `grafana/dashboards/openbsw.json`
from `http://localhost:8080` to `http://host.docker.internal:8080` and added
the new host to the datasource's `allowedHosts` in
`grafana/provisioning/datasources/sovd.yaml`. The `--add-host=host.docker.internal:host-gateway`
flag in the `docker run` command (already present in `demo.sh`) ensures this
hostname resolves to the host's gateway IP.

```mermaid
flowchart TD
    root_fix["ERR-6 solution"]
    dash["FIX 1<br/>grafana/dashboards/openbsw.json<br/>All panel URLs changed from<br/>http://localhost:8080/vehicle/v15/...<br/>to http://host.docker.internal:8080/vehicle/v15/..."]
    datasource["FIX 2<br/>grafana/provisioning/datasources/sovd.yaml<br/>allowedHosts includes<br/>http://localhost:8080<br/>http://host.docker.internal:8080"]
    hostflag["Already in place<br/>demo.sh docker run flag<br/>--add-host=host.docker.internal:host-gateway"]

    root_fix --> dash
    root_fix --> datasource
    root_fix --> hostflag
```

---

## 6. Configuration Reference

*Covers: [RG-2], [RG-6]*

### 6.1 CDA Configuration (`opensovd-cda.toml`)

```toml
# Standard DoIP protocol (not DOBT)                     → [RG-6.5]
onboard_tester = false
flash_files_path = "/app/flash"

[server]
address = "0.0.0.0"
port = 8080                                              # → [RG-2.1]

[database]
path = "/app/odx"                                        # → [RG-2.10]
exit_no_database_loaded = true
fallback_to_base_variant = true                          # → [RG-2.11]

[doip]
tester_address = "192.168.0.10"
tester_subnet = "255.255.0.0"
gateway_port = 13400                                     # → [RG-4.1]
send_diagnostic_message_ack = false                      # → [RG-6.2]
send_timeout_ms = 5000                                   # → [RG-6.3]
```

### 6.2 ECU DoIP Overlay Fix

File: `openbsw-overlay/libs/doip/src/doip/server/DoIpServerConnectionHandler.cpp`
(replaces `openbsw/libs/bsw/doip/src/doip/server/DoIpServerConnectionHandler.cpp`
at build time — upstream file is **not modified**)

Lines 284-290 — added to `headerReceived()` switch, before `default:`:         → [RG-6.1]

```cpp
case DoIpConstants::PayloadTypes::DIAGNOSTIC_MESSAGE_POSITIVE_ACK:   // line 284
case DoIpConstants::PayloadTypes::DIAGNOSTIC_MESSAGE_NEGATIVE_ACK:   // line 285
{                                                                    // line 286
    // Silently consume diagnostic ACKs sent by the tester           // line 287
    _connection.endReceiveMessage(                                   // line 288
        IDoIpConnection::PayloadDiscardedCallbackType());
    return HeaderReceivedContinuation{                               // line 289
        IDoIpConnectionHandler::HandledByThisHandler{}};
}                                                                    // line 290
```

CMake mechanism (in `CMakeLists.txt`):

```cmake
# Remove upstream source from the doip target, inject overlay copy
get_target_property(_doip_srcs doip SOURCES)
list(FILTER _doip_srcs EXCLUDE REGEX "DoIpServerConnectionHandler\\.cpp$")
...
target_sources(doip PRIVATE ${_doip_srcs} <overlay path>)
```

### 6.3 ECU Launch Command

```bash
# → [RG-6.4]
(trap '' SIGTTOU;
 ./build/posix-freertos-sovd/Release/app.sovdDemo.elf \
   < /dev/null >> /tmp/openbsw-demo.log 2>&1 &
 echo $! > /tmp/openbsw-demo.pid)
```

---

## 7. Data Model

*Covers: [RG-7]*

### 7.1 UDS Service Map

| SID | Service | Source | DID/DTC Hex |
|:---:|:---|:---|:---|
| 0x10 | DiagnosticSessionControl | upstream | — |
| 0x14 | ClearDiagnosticInformation | overlay | 0xFFFFFF (all) |
| 0x19 | ReadDTCInformation | overlay | subfns 0x01, 0x02, 0x06 |
| 0x22 | ReadDataByIdentifier | upstream + overlay | 0xCF01–0xCF12 |
| 0x28 | CommunicationControl | upstream | — |
| 0x2E | WriteDataByIdentifier | upstream | 0xCF03 |
| 0x31 | RoutineControl | upstream | subfns 0x01, 0x02, 0x03 |
| 0x3E | TesterPresent | upstream | — |

### 7.2 DID Map (MDD → ECU)

| MDD Name | MDD DID | ECU DID | Match | SOVD Endpoint |
|:---|:---:|:---:|:---:|:---|
| StaticData | 0xCF01 | 0xCF01 | ✓ | `.../data/StaticData` |
| ADC_Value | 0xCF02 | 0xCF02 | ✓ | `.../data/ADC_Value` |
| WritableData | 0xCF03 | 0xCF03 | ✓ | `.../data/WritableData` |
| EngineTemp | 0xCF10 | 0xCF10 | ✓ | `.../data/EngineTemp` |
| BatteryVoltage | 0xCF11 | 0xCF11 | ✓ | `.../data/BatteryVoltage` |
| VehicleSpeed | 0xCF12 | 0xCF12 | ✓ | `.../data/VehicleSpeed` |
| Identification | 0xF100 | — | ✗ | `.../data/Identification` (NRC 0x31) |

### 7.3 DTC Map

| DTC Number | MDD Name | ECU Constant | Simulated Status |
|:---:|:---|:---|:---|
| 0x010100 | Engine Overtemp | `DTC_ENGINE_OVERTEMP` | Random toggle |
| 0x010200 | Battery Low | `DTC_BATTERY_VOLTAGE_LOW` | Random toggle |
| 0x010300 | Comm Fault | `DTC_COMMUNICATION_FAULT` | Random toggle |
| 0x010400 | Sensor Malfunction | `DTC_SENSOR_MALFUNCTION` | Random toggle |
| 0x010500 | Brake Fault | `DTC_BRAKE_SYSTEM_FAULT` | Random toggle |

---

## 8. Deployment Modes

*Covers: [RG-5]*

### 8.1 Local (`demo.sh --real-cda`)

```mermaid
flowchart TB
  subgraph host_os[Host OS (Ubuntu / Dev-Container)]
        tap["tap0 interface<br/>192.168.0.10/24"]
        ecu_proc["ECU process<br/>native binary"]
        cda_host["CDA Docker container<br/>--network host"]
        grafana_local["Grafana Docker container"]
  end
```

### 8.2 Docker Compose (`docker compose --profile real-cda up`)

```mermaid
flowchart TB
    subgraph docker[Docker]
        ecu_container["openbsw-ecu container<br/>tap0: 192.168.0.201<br/>doip-net bridge"]
        cda_container["real-sovd-cda container<br/>192.168.0.10 on doip-net<br/>Port 8080 mapped to host"]
        grafana_container["grafana container<br/>192.168.0.100 on doip-net<br/>Port 3000 mapped to host"]
    end

    ecu_container <-->|DoIP over doip-net| cda_container
    cda_container -->|REST data source| grafana_container
```

### 8.3 GitHub Codespaces

Same as local mode with port forwarding via `*.app.github.dev` URLs.
Ports 8080 and 3000 must be set to "Public" in the Ports tab.

---

## 9. Pre-built CDA Binary

*Covers: [RG-5.9]*

A pre-built `opensovd-cda` binary (x86-64 Linux, unstripped, ~26 MB) is
checked into `real-sovd-cda/bin/` via **Git LFS**. The Dockerfile supports
a `USE_PREBUILT` build arg:

```mermaid
flowchart LR
    prebuilt["USE_PREBUILT=1<br/>default when bin/ exists"] --> prebuilt_image["debian:trixie-slim<br/>COPY bin/opensovd-cda to /app/<br/>runtime deps such as libssl<br/>about 5 seconds"]
    source["USE_PREBUILT=0<br/>from source"] --> source_image["rust:1.88 + cargo-chef<br/>cargo build --release<br/>output /tmp/opensovd-cda<br/>about 10-15 minutes cold"]
```

`demo.sh` auto-detects the pre-built binary and uses the fast path.

---

## 10. Dual Grafana Dashboards

*Covers: [RG-8.1], [RG-8.5]*

Two provisioned dashboards are available, one per CDA mode:

| Dashboard | File | UID | Endpoints | Auth |
|:---|:---|:---|:---|:---|
| **OpenBSW Vehicle Diagnostics** | `openbsw.json` | `openbsw-sovd-demo` | `/vehicle/v15/...` | JWT Bearer |
| **OpenBSW Vehicle Diagnostics (Stub CDA)** | `openbsw-stub.json` | `openbsw-stub-cda` | `/api/sensors/...` | None |

Both are provisioned from `grafana/dashboards/` and appear in the Grafana
dashboard list. Select the one matching the running CDA mode.
