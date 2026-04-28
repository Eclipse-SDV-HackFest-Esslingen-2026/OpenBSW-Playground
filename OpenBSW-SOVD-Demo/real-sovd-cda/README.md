# Real SOVD CDA Integration

This directory integrates the **Eclipse OpenSOVD Classic Diagnostic Adapter** (CDA) as
an optional drop-in replacement for the Python stub CDA in the SOVD demo.

> **Documentation**: See [`../doc/demo-architecture.md`](../doc/demo-architecture.md) for
> full architecture, DoIP flow diagrams (good-case and error patterns), and design
> rationale. See [`../doc/requirements-summary.md`](../doc/requirements-summary.md) for
> a MECE checklist of all demo requirements.

## Architecture

```
┌──────────────────┐      DoIP :13400      ┌──────────────────┐
│   OpenBSW ECU    │◄═══════════════════►│   OpenSOVD CDA   │
│  192.168.0.201   │                       │  192.168.0.10    │
│  UDS addr 0x002A │                       │  Rust / axum     │
└──────────────────┘                       └────────┬─────────┘
                                                    │ SOVD REST :8080
                                                    │ /vehicle/v15/...
                                                    ▼
                                           ┌──────────────────┐
                                           │     Grafana      │
                                           │  192.168.0.100   │
                                           └──────────────────┘
```

## Key Design Choices

### 1. DoIP Protocol Interop — Diagnostic ACK Handling

The CDA (per ISO 13400) sends `DiagnosticMessagePositiveAck` (payload type
`0x8002`) back to the ECU after receiving each diagnostic response. OpenBSW's
DoIP server did not handle this payload type, returning Generic NACK `0x01`
(unknown payload type), which corrupted the CDA's response stream.

**Solution**: Two-sided fix:
- **ECU side**: Patched `DoIpServerConnectionHandler::headerReceived()` to
  silently consume `0x8002` / `0x8003` payloads instead of NACKing.
- **CDA side**: Set `send_diagnostic_message_ack = false` in the TOML config
  to suppress the ACK on one code path. Set `send_timeout_ms = 5000` to
  accommodate the userspace lwIP TCP stack timing.

### 2. Standard DoIP (not DOBT)

Set `onboard_tester = false` to use standard DoIP protocol (`ISO 13400-2`)
instead of DoIP DOBT (Diagnostic On Board Tester). The ECU's DoIP stack
implements standard DoIP; DOBT uses a different routing activation type.

### 3. Variant Detection Fallback

The MDD defines an empty `variant_pattern`, causing CDA variant detection to
fail with `NotFound(None)`. The config sets `fallback_to_base_variant = true`
so the CDA uses the base diagnostic layer directly.

### 4. Bearer Token Authentication

The CDA requires JWT authentication even with the `auth` compile-time feature
disabled. Clients must first `POST /vehicle/v15/authorize` with any
`client_id` / `client_secret` to obtain a Bearer token for subsequent requests.

### 5. ECU Background Process (SIGTTOU)

The POSIX FreeRTOS ECU calls `tcsetattr()` during `Uart::init()`, which sends
`SIGTTOU` to background processes. The `demo.sh` script traps `SIGTTOU` and
redirects stdin from `/dev/null` to prevent the process from being stopped.

## Quick Start

```bash
# From the OpenBSW-SOVD-Demo directory:
./demo.sh --real-cda
```

This will:
1. Build the OpenBSW ECU application
2. Build the real CDA Docker image (first build takes several minutes for Rust compilation)
3. Start the ECU, CDA, and Grafana
4. Run smoke tests

## Components

### `classic-diagnostic-adapter/` (git submodule)
The [Eclipse OpenSOVD Classic Diagnostic Adapter](https://github.com/eclipse-opensovd/classic-diagnostic-adapter) -
a Rust-based SOVD server that translates REST API calls to UDS/DoIP diagnostic commands.

### `odx-converter/` (git submodule)
The [Eclipse OpenSOVD ODX Converter](https://github.com/eclipse-opensovd/odx-converter) -
converts PDX (ODX archive) files to MDD format for the CDA.

### `odx-gen/`
Scripts to generate the OpenBSW ECU diagnostic description:

- **`generate_openbsw.py`** - Generates an ODX/PDX file using `odxtools`
- **`generate_mdd.py`** - Generates an MDD file directly using FlatBuffers + Protobuf
- **`openbsw_ecu.json`** - FlatBuffers JSON describing OpenBSW ECU diagnostics
  (5 DTCs, 6 DIDs, session control, reset, DTC read/clear)
- **`OpenBSW.mdd`** - Pre-generated MDD file for the CDA
- **`OpenBSW.pdx`** - Pre-generated PDX file

### `opensovd-cda.toml`
CDA configuration for the OpenBSW ECU (server port 8080, DoIP settings).

### `entrypoint.sh`
Docker entrypoint that auto-detects the tester IP and starts the CDA.

### `Dockerfile`
Multi-stage Rust build for the CDA, based on the upstream Dockerfile pattern.

## API Differences

| Feature | Python Stub | Real CDA |
|---|---|---|
| Base URL | `/sovd/v1/` | `/vehicle/v15/` |
| Components | `/sovd/v1/components` | `/vehicle/v15/components` |
| Faults | `/sovd/v1/components/{id}/faults` | `/vehicle/v15/components/{id}/faults` |
| Data | `/sovd/v1/components/{id}/data/{did}` | `/vehicle/v15/components/{id}/data/{name}` |
| Health | `/health` | `/health` |
| Auth | None required | `POST /vehicle/v15/authorize` → Bearer token |
| ECU Discovery | Static config | DoIP VIR broadcast |
| Grafana API | `/api/sensors/*`, `/api/faults/*` | Not available |

## Re-generating the MDD File

If you modify the ECU's diagnostic description (DTCs, DIDs, etc.):

```bash
cd odx-gen

# Option A: Generate MDD directly (recommended, no external deps beyond flatc + protoc)
pip install protobuf flatbuffers
# Edit openbsw_ecu.json with your changes
python generate_mdd.py

# Option B: Generate via PDX (requires odx-converter with ODX XSD schema)
pip install odxtools==11.0.0
python generate_openbsw.py
java -jar <odx-converter>/converter-all.jar OpenBSW.pdx
```

## Verified Working Endpoints

| Endpoint | Status | Notes |
|---|---|---|
| `GET /health` | Working | Returns `{"status":"Up"}` with doip, main, database |
| `POST /vehicle/v15/authorize` | Working | Any credentials; returns JWT Bearer token |
| `GET /vehicle/v15/components` | Working | Lists `openbsw` ECU |
| `GET /vehicle/v15/components/openbsw/data` | Working | Lists 7 data identifiers |
| `GET /vehicle/v15/components/openbsw/data/EngineTemp` | Working | Live value (random walk 70–130) |
| `GET /vehicle/v15/components/openbsw/data/BatteryVoltage` | Working | Live value (÷10 → volts) |
| `GET /vehicle/v15/components/openbsw/data/VehicleSpeed` | Working | Live value (0–220 km/h) |
| `GET /vehicle/v15/components/openbsw/data/StaticData` | Working | Static byte array from DID 0xCF01 |
| `GET /vehicle/v15/components/openbsw/data/ADC_Value` | Working | ADC potentiometer value |
| `GET /vehicle/v15/components/openbsw/data/Identification` | NRC 0x31 | DID 0xF100 not registered on ECU |
| `GET /vehicle/v15/components/openbsw/data/WritableData` | NRC | Requires extended diagnostic session |
| `GET /vehicle/v15/components/openbsw/faults` | Working | 5 DTCs with full ISO 14229 status bytes |

## Docker Compose Profiles

The `docker-compose.yaml` uses profiles for mutual exclusion:

```bash
# Default: Python stub CDA
docker compose up --build

# Real CDA: Eclipse OpenSOVD
docker compose --profile real-cda up --build
```
