# SOVD Demo — Architecture & Design

This document describes the architecture of the OpenBSW + SOVD demo, the key
design choices made during integration, and the DoIP communication flow
including error patterns encountered and their solutions.

> **Requirements traceability**: Each section references the corresponding
> requirement group from [`requirements-summary.md`](requirements-summary.md).

---

## 1. System Architecture

*Covers: [RG-1], [RG-2], [RG-4], [RG-5]*

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                         Host / Dev-Container                       │
 │                                                                    │
 │  ┌───────────────────────┐         ┌───────────────────────┐       │
 │  │   OpenBSW ECU (C++)   │  DoIP   │  OpenSOVD CDA (Rust)  │       │
 │  │                       │ :13400  │                       │       │
 │  │  app.sovdDemo.elf     │◄═══════►│  opensovd-cda         │       │
 │  │                       │  TCP    │                       │       │
 │  │  POSIX-FreeRTOS       │  over   │  axum HTTP server     │       │
 │  │  lwIP TCP/IP stack    │  tap0   │  DoIP client          │       │
 │  │                       │         │                       │       │
 │  │  Logical addr: 0x002A │         │  Tester addr: 0x0EE0  │       │
 │  │  IP: 192.168.0.201    │         │  IP: 192.168.0.10     │       │
 │  └───────────┬───────────┘         └───────────┬───────────┘       │
 │              │                                 │                   │
 │              │  tap0 (L2 TAP interface)        │ :8080 REST        │
 │              │  192.168.0.0/24 subnet          │                   │
 │              │                                 │                   │
 │  ┌───────────┴─────────────────────────────────┴───────────┐       │
 │  │                    doip-net bridge                      │       │
 │  │              (or host networking for local mode)        │       │
 │  └─────────────────────────┬───────────────────────────────┘       │
 │                            │                                       │
 │                ┌───────────┴───────────┐                           │
 │                │       Grafana         │                           │
 │                │   192.168.0.100       │                           │
 │                │   :3000               │                           │
 │                │   Infinity datasource │                           │
 │                └───────────────────────┘                           │
 │                                                                    │
 └────────────────────────────────────────────────────────────────────┘

  External access:
    SOVD API   → http://localhost:8080/vehicle/v15/...
    Grafana    → http://localhost:3000
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

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                        SOVD Client                              │
  │              (curl / Grafana / Browser)                         │
  └───────────────────────┬─────────────────────────────────────────┘
                          │  HTTP / JSON
  ┌───────────────────────┴─────────────────────────────────────────┐
  │                    SOVD REST Layer                              │
  │              /vehicle/v15/components/...                        │
  │              JWT Bearer authentication                          │
  │              axum router (cda-sovd)                              │
  ├─────────────────────────────────────────────────────────────────┤
  │                    UDS Application Layer                        │
  │              Service dispatch (cda-comm-uds)                    │
  │              MDD-driven request encoding                        │
  │              Variant detection / fallback                       │
  ├─────────────────────────────────────────────────────────────────┤
  │                    DoIP Transport Layer                         │
  │              ISO 13400-2 framing (cda-comm-doip)                │
  │              Routing activation, alive check                    │
  │              DiagnosticMessage (0x8001) exchange                │
  ├─────────────────────────────────────────────────────────────────┤
  │                    TCP/IP (Kernel / lwIP)                       │
  │              CDA: kernel TCP socket                             │
  │              ECU: lwIP userspace TCP/IP over TAP                │
  ├─────────────────────────────────────────────────────────────────┤
  │                    L2 Ethernet (tap0)                           │
  │              Linux TAP interface, 192.168.0.0/24                │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 3. CMake Overlay Strategy (Zero-Patch)

*Covers: [RG-1.1], [RG-5.4]*

The demo builds on top of upstream OpenBSW without modifying its source tree:

```
  OpenBSW-SOVD-Demo/
  │
  ├── CMakeLists.txt              ─┐
  │   add_subdirectory(openbsw)    │  Adds all upstream library targets
  │   add_library(uds_dtc_overlay) │  Overlay: ReadDTCInformation, ClearDTC
  │   add_executable(app.sovdDemo) │  Demo binary with DTC + sensor simulation
  │                                │
  │   target_include_directories(  │  Overlay includes listed FIRST
  │     openbsw-overlay/app/include│  → UdsSystem.h shadows upstream
  │     openbsw/.../include        │
  │   )                           ─┘
  │
  ├── openbsw-overlay/
  │   ├── app/
  │   │   ├── include/systems/UdsSystem.h      ← Replaces upstream header
  │   │   ├── include/uds/DtcSimulator.h
  │   │   ├── include/uds/ReadIdentifierSimulated.h
  │   │   └── src/...                          ← Corresponding implementations
  │   ├── libs/uds/
  │   │   ├── include/uds/dtc/                 ← DTC model classes
  │   │   └── src/services/                    ← UDS 0x19, 0x14 implementations
  │   └── libs/doip/
  │       └── src/doip/server/
  │           └── DoIpServerConnectionHandler.cpp  ← DoIP interop fix (lines 284-290)
  │
  └── openbsw/                                 ← Upstream (unmodified)
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

```
  Client                     CDA (Rust)               ECU (OpenBSW)
    │                          │                          │
    │  POST /authorize         │                          │
    │  {"client_id":"test"...} │                          │
    │─────────────────────────>│                          │
    │  {"access_token":"JWT"}  │                          │
    │<─────────────────────────│                          │
    │                          │                          │
    │  GET .../data/EngineTemp │                          │
    │  Authorization: Bearer.. │                          │
    │─────────────────────────>│                          │
    │                          │                          │
    │                          │  DoIP: DiagnosticMessage (0x8001)
    │                          │  [0x0EE0 → 0x002A]       │
    │                          │  UDS: 0x22 0xCF 0x10     │
    │                          │─────────────────────────>│
    │                          │                          │
    │                          │  DoIP: DiagPositiveAck (0x8002)
    │                          │  [0x002A → 0x0EE0]       │
    │                          │<─────────────────────────│
    │                          │                          │
    │                          │  DoIP: DiagnosticMessage (0x8001)
    │                          │  [0x002A → 0x0EE0]       │
    │                          │  UDS: 0x62 0xCF 0x10 <val>
    │                          │<─────────────────────────│
    │                          │                          │
    │                          │  (ACK suppressed by config)
    │                          │                          │
    │  {"id":"enginetemp",     │                          │
    │   "data":{"EngineTemp":  │                          │
    │   121}}                  │                          │
    │<─────────────────────────│                          │
    │                          │                          │
```

**Key points**:
- ECU sends `DiagnosticMessagePositiveAck` (0x8002) to confirm receipt
- ECU sends UDS positive response `0x62` (SID + 0x40) with the DID data
- CDA's outbound ACK to the ECU is suppressed (`send_diagnostic_message_ack = false`)

### 4.2 Good Case — Fault Memory Read

```
  Client                     CDA (Rust)               ECU (OpenBSW)
    │                          │                          │
    │  GET .../faults          │                          │
    │  Authorization: Bearer.. │                          │
    │─────────────────────────>│                          │
    │                          │                          │
    │                          │  DiagMsg: UDS 0x19 0x02 0xFF
    │                          │  (ReadDTCInfo, reportByStatusMask)
    │                          │─────────────────────────>│
    │                          │                          │
    │                          │  DiagPosAck (0x8002)      │
    │                          │<─────────────────────────│
    │                          │                          │
    │                          │  DiagMsg: UDS 0x59 0x02 ...
    │                          │  (5 DTCs × 4 bytes each) │
    │                          │<─────────────────────────│
    │                          │                          │
    │  {"items":[              │                          │
    │    {"code":"010100",     │                          │
    │     "fault_name":"Engine │                          │
    │      Coolant...",        │                          │
    │     "status":{...}},     │                          │
    │    ... 4 more DTCs       │                          │
    │  ]}                      │                          │
    │<─────────────────────────│                          │
    │                          │                          │
```

### 4.3 Good Case — DoIP Connection Establishment

```
  CDA (Tester)                               ECU (DoIP Server)
    │                                            │
    │  UDP: Vehicle Identification Request (VIR)  │
    │  Broadcast to 255.255.255.255:13400         │
    │───────────────────────────────────────────>│
    │                                            │
    │  UDP: Vehicle Announcement Message (VAM)    │
    │  LogicalAddr=0x002A, VIN, EID, GID          │
    │<───────────────────────────────────────────│
    │                                            │
    │  TCP: Connect to 192.168.0.201:13400        │
    │───────────────────────────────────────────>│
    │                                            │
    │  DoIP: Routing Activation Request (0x0005)  │
    │  SourceAddr=0x0EE0, ActivationType=0x00     │
    │───────────────────────────────────────────>│
    │                                            │
    │  DoIP: Routing Activation Response (0x0006) │
    │  TesterAddr=0x0EE0, Status=0x10 (success)   │
    │<───────────────────────────────────────────│
    │                                            │
    │  ══════ Connection ACTIVE ══════            │
    │  Ready for DiagnosticMessage exchange        │
    │                                            │
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

```
  CDA (Tester)                               ECU (DoIP Server)
    │                                            │
    │  DiagMsg 0x8001: UDS 0x22 0xCF 0x01         │
    │───────────────────────────────────────────>│
    │                                            │  UDS processes request
    │  DiagPosAck 0x8002 [ECU → CDA]              │  ECU ACKs receipt
    │<───────────────────────────────────────────│
    │                                            │
    │  DiagMsg 0x8001: UDS 0x62 0xCF 0x01 <data>  │  ECU sends response
    │<───────────────────────────────────────────│
    │                                            │
    │  DiagPosAck 0x8002 [CDA → ECU]              │  CDA ACKs response
    │───────────────────────────────────────────>│
    │                                            │
    │                        ┌───────────────────┤
    │                        │ headerReceived()  │
    │                        │ payloadType=0x8002│
    │                        │ → NOT in switch   │
    │                        │ → headerDefault() │
    │                        │ → no handler      │
    │                        │ → NACK 0x01!      │
    │                        └───────────────────┤
    │                                            │
    │  Generic NACK 0x0000: code=0x01             │  ECU rejects ACK
    │<───────────────────────────────────────────│
    │                                            │
    │  !! CDA confused: unexpected NACK !!        │
    │  !! Next request will timeout !!            │
    │                                            │
```

**Solution (two-sided)**:

```
  ┌─────────────────────────────────────────────────────────┐
  │  ECU FIX: DoIpServerConnectionHandler.cpp (OVERLAY)     │
  │                                                         │
  │  File: openbsw-overlay/libs/doip/src/doip/server/       │
  │        DoIpServerConnectionHandler.cpp  (lines 284-290)  │
  │  Upstream file: UNMODIFIED                               │
  │                                                         │
  │  Added to headerReceived() switch:                      │
  │                                                         │
  │    case DIAGNOSTIC_MESSAGE_POSITIVE_ACK:  // 0x8002     │
  │    case DIAGNOSTIC_MESSAGE_NEGATIVE_ACK:  // 0x8003     │
  │      // Silently consume tester ACKs                    │
  │      _connection.endReceiveMessage(...);                 │
  │      return HandledByThisHandler{};                      │
  │                                                         │
  ├─────────────────────────────────────────────────────────┤
  │  CDA FIX: opensovd-cda.toml                            │
  │                                                         │
  │    [doip]                                               │
  │    send_diagnostic_message_ack = false                   │
  │    send_timeout_ms = 5000                                │
  │                                                         │
  │  Note: The CDA has TWO code paths that send ACKs:       │
  │    1. DoIPConnection::read()  → gated by config ✓       │
  │    2. handle_response()       → unconditional (bug)      │
  │  The ECU-side fix handles the unconditional path.        │
  └─────────────────────────────────────────────────────────┘
```

### 5.2 ERR-2: ECU Process Stopped (SIGTTOU) (RESOLVED)

**Root cause**: The POSIX FreeRTOS ECU application calls `tcsetattr()` in
`Uart::init()` to disable canonical mode and echo on stdout. When the process
runs in the background (`&`), the kernel delivers `SIGTTOU` (signal 22), whose
default action is to stop the process.

**Impact**: ECU stuck at "Initialize level 1" with process state `Tl`
(stopped + multi-threaded). No FreeRTOS tasks run. No DoIP server.

*Requirement: [RG-6.4]*

```
  Shell                              ECU Process
    │                                    │
    │  ./app.sovdDemo.elf &              │
    │───────────────────────────────────>│
    │                                    │
    │                                    │  main() → app_main() → staticInit()
    │                                    │  Uart::init()
    │                                    │  tcsetattr(stdout, TCSANOW, ...)
    │                                    │
    │                          ┌─────────┤
    │                          │ Kernel: │
    │                          │ Process │
    │                          │ is in   │
    │                          │ bg and  │
    │                          │ modifies│
    │                          │ terminal│
    │                          │ → send  │
    │                          │ SIGTTOU │
    │                          └─────────┤
    │                                    │
    │                                    │  SIGTTOU not caught
    │                                    │  → Process STOPPED (state: T)
    │                                    │  All pthreads frozen
    │                                    │  SIGALRM (FreeRTOS tick) cannot fire
    │                                    │
    │  ps shows: Tl (stopped)            │
    │                                    │
```

**Solution**:

```
  ┌─────────────────────────────────────────────────────────┐
  │  demo.sh FIX:                                           │
  │                                                         │
  │  (trap '' SIGTTOU;                                      │
  │   ./app.sovdDemo.elf < /dev/null >> log 2>&1 &          │
  │   echo $! > pidfile)                                    │
  │                                                         │
  │  • trap '' SIGTTOU  → ignore the signal                 │
  │  • < /dev/null      → no stdin (prevents SIGTTIN)       │
  │  • subshell (...)   → signal trap doesn't leak          │
  └─────────────────────────────────────────────────────────┘
```

### 5.3 ERR-3: UDS Request Out of Range (DID Mismatch) (KNOWN)

**Root cause**: The MDD file maps `Identification_Read` to DID `0xF100`, but
the ECU only registers DIDs `0xCF01`–`0xCF12`. The ECU returns UDS NRC `0x31`
(requestOutOfRange).

**Impact**: Reading the `Identification` data item fails. All other 6 DIDs
work correctly.

*Requirement: [RG-7.1]*

```
  CDA                                     ECU
    │                                        │
    │  DiagMsg: 0x22 0xF1 0x00               │  ReadDataByIdentifier
    │  (Identification, DID=0xF100)           │  for DID 0xF100
    │───────────────────────────────────────>│
    │                                        │
    │                              ┌─────────┤
    │                              │ Lookup:  │
    │                              │ 0xF100   │
    │                              │ not in   │
    │                              │ diag job │
    │                              │ table    │
    │                              └─────────┤
    │                                        │
    │  DiagMsg: 0x7F 0x22 0x31               │  Negative Response
    │  (NRC = requestOutOfRange)             │  Service 0x22 rejected
    │<───────────────────────────────────────│
    │                                        │

  Fix: Update openbsw_ecu.json to use DID 0xCF01 for Identification,
       or add DID 0xF100 to the ECU's diag job table.
```

### 5.4 ERR-4: Variant Detection Failure (MITIGATED)

**Root cause**: The MDD file defines an empty `variant_pattern: []`. The CDA's
variant detection sends a specific DID read to determine which diagnostic
variant to use. With no pattern, it cannot detect any variant.

**Impact**: CDA logs `Variant detection error: Failed to detect variant:
NotFound(None)`. Falls back to the base variant, which works for this single-ECU
demo but may miss variant-specific services in a multi-variant setup.

*Requirement: [RG-2.11]*

```
  CDA                                     ECU
    │                                        │
    │  (Startup: detect variant)              │
    │  variant_pattern is []                  │
    │  → No DID to read for detection         │
    │  → Result: NotFound(None)               │
    │                                        │
    │  fallback_to_base_variant = true        │
    │  → Use base "OpenBSW" diag layer        │
    │  → All services available ✓             │
    │                                        │
```

### 5.5 ERR-5: AliveCheck NACK (30-second interval) (COSMETIC)

**Root cause**: The CDA sends DoIP `AliveCheckRequest` (payload type `0x0007`)
every 30 seconds to verify the gateway is live. The ECU's DoIP server handles
`AliveCheckResponse` (0x0008) from testers but does not handle unsolicited
`AliveCheckRequest` from a tester — it falls to `headerReceivedDefault()` and
NACKs.

**Impact**: Cosmetic — logged as a warning but does not break communication.
The CDA reconnects if it doesn't receive a response.

```
  CDA                                     ECU
    │                                        │
    │  (Every 30 seconds)                     │
    │  DoIP: AliveCheckRequest (0x0007)       │
    │───────────────────────────────────────>│
    │                                        │
    │                              ┌─────────┤
    │                              │ 0x0007   │
    │                              │ not in   │
    │                              │ switch   │
    │                              │ (only    │
    │                              │ 0x0008   │
    │                              │ handled) │
    │                              └─────────┤
    │                                        │
    │  Generic NACK 0x0000: code=0x01         │
    │<───────────────────────────────────────│
    │                                        │
    │  CDA: "Received Generic NACK" (warn)    │
    │  → Connection stays alive               │
    │  → UDS traffic unaffected               │
    │                                        │
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

```
  Grafana container (bridge)              Host (CDA on :8080)
    │                                        │
    │  Infinity plugin queries:              │
    │  GET http://localhost:8080/...          │
    │─────────┐                              │
    │         │  localhost = 127.0.0.1        │
    │         │  inside container             │
    │         │  → port 8080 not listening    │
    │         │  → connection refused         │
    │<────────┘                              │
    │                                        │
    │  Panel result: "No data"               │
    │                                        │
```

**Solution**: Changed all panel URLs in `grafana/dashboards/openbsw.json`
from `http://localhost:8080` to `http://host.docker.internal:8080` and added
the new host to the datasource's `allowedHosts` in
`grafana/provisioning/datasources/sovd.yaml`. The `--add-host=host.docker.internal:host-gateway`
flag in the `docker run` command (already present in `demo.sh`) ensures this
hostname resolves to the host's gateway IP.

```
  ┌─────────────────────────────────────────────────────────┐
  │  FIX 1: grafana/dashboards/openbsw.json                │
  │                                                         │
  │  All panel target URLs changed:                         │
  │    http://localhost:8080/vehicle/v15/...                 │
  │    → http://host.docker.internal:8080/vehicle/v15/...   │
  │                                                         │
  ├─────────────────────────────────────────────────────────┤
  │  FIX 2: grafana/provisioning/datasources/sovd.yaml      │
  │                                                         │
  │    allowedHosts:                                        │
  │      - "http://localhost:8080"                          │
  │      - "http://host.docker.internal:8080"   ← added    │
  │                                                         │
  ├─────────────────────────────────────────────────────────┤
  │  ALREADY IN PLACE: demo.sh docker run flag              │
  │                                                         │
  │    --add-host=host.docker.internal:host-gateway         │
  └─────────────────────────────────────────────────────────┘
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

```
  Host OS (Ubuntu / Dev-Container)
    │
    ├── tap0 interface (192.168.0.10/24)
    ├── ECU process (native binary)
    ├── CDA Docker container (--network host)
    └── Grafana Docker container
```

### 8.2 Docker Compose (`docker compose --profile real-cda up`)

```
  Docker
    │
    ├── openbsw-ecu container
    │     tap0 (192.168.0.201)
    │     doip-net bridge
    │
    ├── real-sovd-cda container
    │     192.168.0.10 on doip-net
    │     Port 8080 mapped to host
    │
    └── grafana container
          192.168.0.100 on doip-net
          Port 3000 mapped to host
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

```
  USE_PREBUILT=1 (default when bin/ exists)     USE_PREBUILT=0 (from source)
  ┌────────────────────────────────┐            ┌────────────────────────────────┐
  │  debian:trixie-slim            │            │  rust:1.88 + cargo-chef        │
  │  COPY bin/opensovd-cda /app/   │            │  cargo build --release         │
  │  + runtime deps (libssl, etc.) │            │  → /tmp/opensovd-cda           │
  │  ≈ 5 seconds                   │            │  ≈ 10–15 minutes (cold)        │
  └────────────────────────────────┘            └────────────────────────────────┘
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
