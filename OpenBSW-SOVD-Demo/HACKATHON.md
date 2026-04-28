# Hackathon Guide: DoIP Diagnostics with OpenBSW & SOVD

## Quick Start (5 minutes)

```bash
# 1. Build the OpenBSW ECU
cd ../openbsw && cmake --preset posix-freertos && cmake --build build/posix-freertos

# 2. Set up networking & start everything
cd .. && ./demo.sh

# 3. Open the SOVD API in your browser
# → http://localhost:8080/docs  (Swagger UI)
```

Or use the fully automated demo script:
```bash
./demo.sh            # start everything
./demo.sh --live     # start everything + tmux split (status + logs)
./demo.sh --stop     # tear down
```

### Live Monitoring

Use `--live` for a split-screen tmux view — status dashboard on top, live
ECU + CDA logs scrolling on the bottom:

```bash
./demo.sh --live          # opens tmux session "sovd-demo"
# Ctrl-B d  → detach      # keeps demo running in background
# tmux attach -t sovd-demo # re-attach later
```

Requires tmux: `sudo apt-get install -y tmux`

---

## Architecture Overview

```
┌─────────────────────────────────┐
│     Browser / curl / Postman    │  ← You interact here
│         (SOVD Client)          │
└──────────────┬──────────────────┘
               │ HTTP/REST
               ▼
┌─────────────────────────────────┐
│   SOVD Classic Diagnostic       │
│   Adapter (CDA)                │  sovd-cda/main.py
│   FastAPI on :8080             │  Port 8080
│                                │
│  /sovd/v1/components/…/faults  │──→ UDS 0x19 ReadDTCInformation
│  /sovd/v1/components/…/data/*  │──→ UDS 0x22 ReadDataByIdentifier
│  DELETE …/faults               │──→ UDS 0x14 ClearDiagnosticInfo
└──────────────┬──────────────────┘
               │ DoIP (TCP :13400)
               │ ISO 13400-2
               ▼
┌─────────────────────────────────┐
│      OpenBSW Reference App      │
│   (POSIX + FreeRTOS simulator)  │
│                                │
│   DoIP Server ─→ UDS Router    │
│                  ├─ 0x10 DiagSessionControl
│                  ├─ 0x14 ClearDiagnosticInfo  ← NEW
│                  ├─ 0x19 ReadDTCInformation   ← NEW
│                  ├─ 0x22 ReadDataByIdentifier
│                  ├─ 0x2E WriteDataByIdentifier
│                  ├─ 0x28 CommunicationControl
│                  ├─ 0x31 RoutineControl
│                  ├─ 0x3E TesterPresent
│                  └─ 0x85 ControlDTCSetting
│                                │
│   DTC Simulator (5 demo DTCs)  │
│   Simulated Sensors (3 DIDs)   │
│                                │
│   TAP ethernet: 192.168.0.201  │
│   DoIP port:    13400          │
│   Logical addr: 0x002A         │
└─────────────────────────────────┘
```

---

## What is UDS?

**Unified Diagnostic Services (ISO 14229)** is the standard protocol for automotive ECU diagnostics. Every modern car uses UDS for:

- **Reading trouble codes** (DTCs) – "What's wrong with the car?"
- **Reading live data** (DIDs) – "What's the engine temperature?"
- **Clearing faults** – "Reset the check-engine light"
- **Flashing firmware** – "Update the ECU software"
- **Security access** – "Authenticate before writing"

### Key UDS Services

| Service ID | Name | What it does |
|:---:|---|---|
| 0x10 | DiagnosticSessionControl | Switch between default/extended/programming sessions |
| 0x14 | ClearDiagnosticInformation | Clear stored DTCs |
| 0x19 | ReadDTCInformation | Read DTCs and their status |
| 0x22 | ReadDataByIdentifier | Read a data value by 2-byte DID |
| 0x2E | WriteDataByIdentifier | Write a data value |
| 0x27 | SecurityAccess | Challenge-response authentication |
| 0x31 | RoutineControl | Start/stop/get results of routines |
| 0x3E | TesterPresent | Keep-alive heartbeat |

### UDS Message Format

```
Request:  [ServiceID] [SubFunction/DID] [Data...]
Response: [ServiceID+0x40] [Echo] [ResponseData...]
Error:    [0x7F] [ServiceID] [NRC]

Example – Read DTC by status mask:
  TX: 19 02 FF        (ReadDTCInfo, reportByStatusMask, mask=all)
  RX: 59 02 FF        (positive response header)
      01 01 00 09     (DTC 0x010100, status=0x09: testFailed+confirmed)
      01 02 00 08     (DTC 0x010200, status=0x08: confirmed only)
```

---

## What is DoIP?

**Diagnostic communication over Internet Protocol (ISO 13400)** carries UDS messages over TCP/IP instead of CAN. This enables:

- Remote diagnostics over Ethernet
- Higher bandwidth (vs CAN's 1 Mbps)
- Standard networking tools (Wireshark, curl)

### DoIP Message Flow

```
1. TCP connect to ECU:13400
2. Vehicle identification (optional)
3. Routing activation:  Client tells ECU its logical address
4. Diagnostic messages: UDS requests/responses wrapped in DoIP headers
5. TCP close
```

In this demo, the CDA uses the `doipclient` Python library to handle all DoIP protocol details.

---

## What is SOVD?

**Service-Oriented Vehicle Diagnostics (ISO 17978)** is the next-generation diagnostic standard. Instead of binary UDS protocols, SOVD uses **REST/HTTP APIs**:

```
Traditional:  Tester → binary UDS → DoIP/CAN → ECU
SOVD:         Client → REST/HTTP  → SOVD Server → (optional) UDS → ECU
```

The **Classic Diagnostic Adapter (CDA)** bridges legacy UDS ECUs into the SOVD world:
- Translates REST calls → UDS requests
- Returns JSON responses instead of binary
- Provides a self-documenting API (Swagger UI)

---

## Demo DTCs (Diagnostic Trouble Codes)

The DTC simulator creates 5 demo faults that change dynamically:

| DTC Number | Name | Description | Trigger |
|:---:|:---:|---|---|
| 0x010100 | P0100 | Engine Coolant Over-Temperature | Simulated temp > 120°C |
| 0x010200 | P0200 | Battery Voltage Low | Simulated voltage < 11.0V |
| 0x010300 | P0300 | Communication Fault | Random toggle (demo) |
| 0x010400 | P0400 | Sensor Malfunction | Random toggle (demo) |
| 0x010500 | C0500 | Brake System Fault | Random toggle (demo) |

### DTC Status Byte (ISO 14229 Annex D)

Each DTC has an 8-bit status byte:

| Bit | Name | Meaning |
|:---:|---|---|
| 0 | testFailed | Currently failing |
| 1 | testFailedThisOperationCycle | Failed at least once this cycle |
| 2 | pendingDTC | Suspected but not confirmed |
| 3 | confirmedDTC | Confirmed fault |
| 4 | testNotCompletedSinceLastClear | Not re-tested since clear |
| 5 | testFailedSinceLastClear | Failed at least once since clear |
| 6 | testNotCompletedThisOperationCycle | Not tested this cycle |
| 7 | warningIndicatorRequested | Dashboard warning active |

---

## Demo DIDs (Data Identifiers)

| DID | Name | Description | Range |
|:---:|---|---|---|
| 0xCF01 | StaticData | Fixed data from memory | — |
| 0xCF02 | ADC_Value | Potentiometer ADC reading | 0–4095 |
| 0xCF03 | WritableData | Read/write test DID | — |
| 0xCF10 | EngineTemp | Simulated coolant temperature | 60–140 °C |
| 0xCF11 | BatteryVoltage | Simulated battery (÷100 for V) | 9.00–15.00 V |
| 0xCF12 | VehicleSpeed | Simulated vehicle speed | 0–220 km/h |

The simulated DIDs (0xCF10–0xCF12) change dynamically using a random-walk algorithm. Engine temperature and battery voltage are linked to DTC triggers.

---

## SOVD API Reference

Base URL: `http://localhost:8080`

### List Components
```bash
curl http://localhost:8080/sovd/v1/components
```

### Get Component Info
```bash
curl http://localhost:8080/sovd/v1/components/openbsw-ecu
```

### Read All Faults
```bash
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/faults
# With status filter (e.g., only confirmed DTCs, mask=0x08):
curl "http://localhost:8080/sovd/v1/components/openbsw-ecu/faults?status_mask=8"
```

### Read Single Fault (with extended data)
```bash
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/faults/0x010100
```

### Clear All Faults
```bash
curl -X DELETE http://localhost:8080/sovd/v1/components/openbsw-ecu/faults
```

### List Available DIDs
```bash
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/data
```

### Read a DID Value
```bash
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/data/CF10   # Engine Temp
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/data/CF11   # Battery Voltage
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/data/CF12   # Vehicle Speed
```

### Interactive API Explorer
Open **http://localhost:8080/docs** in your browser for the Swagger UI.

---

## Using the UdsTool Directly (low-level)

You can also talk directly to the ECU using the existing UdsTool:

```bash
cd ../openbsw/tools/UdsTool
pip install -r requirements.txt

# Read DTC by status mask
python udsTool.py raw --eth --host 192.168.0.201 --ecu 002A --source 0EF1 \
  --data "19 02 FF"

# Clear all DTCs
python udsTool.py raw --eth --host 192.168.0.201 --ecu 002A --source 0EF1 \
  --data "14 FF FF FF"

# Read engine temperature DID
python udsTool.py read --eth --host 192.168.0.201 --ecu 002A --source 0EF1 \
  --did CF10
```

---

## Hackathon Challenges

### Challenge 1: Add a New DID (Beginner, ~30 min)

**Goal**: Add a new simulated sensor (e.g., fuel level, RPM, tire pressure).

1. Open `../openbsw/executables/referenceApp/application/include/uds/DtcSimulator.h`
2. Add a new DID constant (e.g., `static constexpr uint16_t DID_FUEL_LEVEL = 0xCF13;`)
3. Add a new `ReadIdentifierSimulated` member variable
4. In `DtcSimulator.cpp`:
   - Initialize it in the constructor with min/max/seed values
   - Call `.step()` in the `step()` method
5. In `UdsSystem.cpp`: register it in `addDiagJobs()` / `removeDiagJobs()`
6. Update `sovd-cda/catalog.json` with the new DID description
7. Rebuild and test!

### Challenge 2: Add a New DTC (Beginner, ~30 min)

**Goal**: Create a new fault condition linked to a sensor.

1. Add a DTC constant in `DtcSimulator.h`
2. Add it to `_dtcStore` in `init()`
3. Add trigger logic in `step()` (e.g., fuel < 5% → fault)
4. Update `sovd-cda/catalog.json`
5. Test via SOVD API

### Challenge 3: Build a Dashboard (Intermediate, ~1-2 hrs)

**Goal**: Create a web dashboard that polls SOVD and displays live data.

- Use any web framework (React, Vue, plain HTML+JS)
- Poll `GET /sovd/v1/components/openbsw-ecu/faults` every 2 seconds
- Poll `GET /sovd/v1/components/openbsw-ecu/data/CF10` etc. for live gauges
- Show DTC status changes in real-time
- Color-code faults by severity

### Challenge 4: Implement WriteDataByIdentifier via SOVD (Intermediate, ~1 hr)

**Goal**: Add a `PUT /sovd/v1/components/{id}/data/{did}` endpoint to the CDA.

1. Add a new FastAPI route in `sovd-cda/main.py`
2. Accept JSON body with the value to write
3. Send UDS 0x2E with DID and data
4. Test with DID 0xCF03 (the writable one)

### Challenge 5: Add RoutineControl via SOVD (Advanced, ~2 hrs)

**Goal**: Expose UDS RoutineControl (0x31) as a SOVD endpoint.

1. Add `POST /sovd/v1/components/{id}/routines/{routineId}` to the CDA
2. Map routine IDs to UDS 0x31 requests
3. Support start (0x01), stop (0x02), and requestResults (0x03) subfunctions

### Challenge 6: S32K344 Hardware Port (Advanced, ~2-4 hrs)

**Goal**: Run the same diagnostics on real hardware.

1. Flash the OpenBSW S32K344 build to the Mini-EVB board
2. Connect via Ethernet (real EMAC, no TAP needed)
3. Update `catalog.json` with the S32K344 IP (192.168.0.200)
4. Point the CDA at the real ECU
5. Compare real ADC readings (DID 0xCF02) with simulated values

---

## Code Map

| Path | What |
|---|---|
| `../openbsw/libs/bsw/uds/` | UDS protocol library |
| `../openbsw/libs/bsw/doip/` | DoIP server/client library |
| `../openbsw/libs/bsw/uds/include/uds/dtc/` | **DTC store** (new) |
| `../openbsw/libs/bsw/uds/include/uds/services/readdtcinformation/` | **0x19 service** (new) |
| `../openbsw/libs/bsw/uds/include/uds/services/cleardiagnosticinformation/` | **0x14 service** (new) |
| `../openbsw/executables/referenceApp/application/` | Reference app (where you add features) |
| `../openbsw/executables/referenceApp/application/include/uds/DtcSimulator.h` | **DTC simulator** (new) |
| `../openbsw/executables/referenceApp/application/include/uds/ReadIdentifierSimulated.h` | **Simulated DID** (new) |
| `../openbsw/executables/referenceApp/application/src/systems/UdsSystem.cpp` | UDS system integration |
| `sovd-cda/main.py` | **SOVD CDA** (REST→DoIP bridge) |
| `sovd-cda/catalog.json` | Diagnostic catalog (DTC/DID descriptions) |
| `demo.sh` | One-click demo launcher |
| `../openbsw/doc/dev/learning/uds/` | UDS tutorial documentation |
| `../openbsw/tools/UdsTool/` | CLI diagnostic tool (Python) |

---

## Key Documents

- **UDS Learning Guide**: `../openbsw/doc/dev/learning/uds/index.rst`
- **Ethernet Learning Guide**: `../openbsw/doc/dev/learning/ethernet/`
- **Lifecycle & Systems**: `../openbsw/doc/dev/learning/lifecycle/`
- **CAN Learning Guide**: `../openbsw/doc/dev/learning/can/`
- **ISO 14229** (UDS): Defines all diagnostic services
- **ISO 13400** (DoIP): Defines diagnostic transport over IP
- **ISO 17978** (SOVD): Defines service-oriented diagnostic APIs
- **OpenSoVD project**: https://github.com/eclipse-opensovd/opensovd

---

## Glossary

| Term | Definition |
|---|---|
| **UDS** | Unified Diagnostic Services – ISO 14229 |
| **DoIP** | Diagnostics over Internet Protocol – ISO 13400 |
| **SOVD** | Service-Oriented Vehicle Diagnostics – ISO 17978 |
| **DTC** | Diagnostic Trouble Code – a fault identifier |
| **DID** | Data Identifier – a 2-byte ID for a data value |
| **NRC** | Negative Response Code – error code in UDS |
| **CDA** | Classic Diagnostic Adapter – bridge from SOVD to legacy UDS |
| **ECU** | Electronic Control Unit – the embedded target |
| **ODX** | Open Diagnostic data eXchange – XML diagnostic descriptions |
| **TAP** | Virtual network device (TUN/TAP) for POSIX simulation |
| **FreeRTOS** | Real-time OS (simulated on POSIX in this demo) |
