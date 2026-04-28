# SOVD Demo for OpenBSW

A self-contained SOVD (Service-Oriented Vehicle Diagnostics) demo that augments
[Eclipse OpenBSW](https://github.com/eclipse-openbsw/openbsw) with DTC
simulation, sensor data, and a full REST diagnostic adapter — **without modifying
the upstream OpenBSW source**.

## Architecture

```
┌─────────────────────────────┐
│  Browser / curl / Grafana   │  ← You interact here
│       (SOVD Client)        │
└────────────┬────────────────┘
             │ HTTP :8080 (SOVD REST API)
┌────────────▼────────────────┐
│  SOVD CDA (Rust / Python)   │  real-sovd-cda/ or sovd-cda/
│  Translates SOVD → DoIP/UDS │
└────────────┬────────────────┘
             │ DoIP :13400 (ISO 13400)
┌────────────▼────────────────┐
│    OpenBSW ECU (C++)        │  openbsw/ + overlay
│  POSIX-FreeRTOS + Demo DTCs │
│  app.sovdDemo.elf           │
└─────────────────────────────┘
```

Two CDA options are supported:
- **Real CDA** (`real-sovd-cda/`): Eclipse OpenSOVD Classic Diagnostic Adapter
  (Rust/axum), driven by an MDD diagnostic description file.
- **Stub CDA** (`sovd-cda/`): Python/FastAPI stub with hardcoded DIDs.

## Quick Start (Local)

```bash
# From the OpenBSW-SOVD-Demo/ directory:
./demo.sh               # builds, starts ECU + CDA, runs smoke test
./demo.sh --live         # same + opens tmux split: status top, logs bottom
./demo.sh --stop        # tear down

# Swagger UI:  http://localhost:8080/docs
# Grafana:     http://localhost:3000  (start via docker compose)
```

### Live Monitoring (tmux split-screen)

After the demo is running, use `--live` for a combined view:

```bash
./demo.sh --live
```

This opens a **tmux** session with two panes:

```
┌──────────────────────────────────────────────────────┐
│  Status dashboard (auto-refreshes every 3 s)         │
│  Shows ECU / CDA / Grafana health + connection lines │
│  URLs, quick commands                                │
├──────────────────────────────────────────────────────┤
│  Live log output (ECU + CDA combined)                │
│  Scrolls continuously, tail -f style                 │
└──────────────────────────────────────────────────────┘
```

- **Detach** without stopping: `Ctrl-B` then `d`
- **Re-attach**: `tmux attach -t sovd-demo`
- **Exit**: `Ctrl-C` in the status pane, or `./demo.sh --stop`

> **Prerequisite**: `sudo apt-get install -y tmux` (already in the dev-container).

## Quick Start (Docker Compose)

```bash
cd OpenBSW-SOVD-Demo
docker compose up --build

# Three services start:
#   openbsw-ecu  → DoIP server at 192.168.0.201:13400
#   sovd-cda     → REST API at http://localhost:8080
#   grafana      → Dashboard at http://localhost:3000

# Try:
curl http://localhost:8080/sovd/v1/components
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/faults
curl http://localhost:8080/sovd/v1/components/openbsw-ecu/data/CF10
```

## Build Only (No Docker)

```bash
cd OpenBSW-SOVD-Demo
cmake --preset posix-freertos-sovd
cmake --build build/posix-freertos-sovd
# Binary: build/posix-freertos-sovd/Release/app.sovdDemo.elf
```

### Pre-built CDA Binary

A pre-built `opensovd-cda` binary (x86-64 Linux) is checked into
`real-sovd-cda/bin/` via **Git LFS** (~26 MB, unstripped for debug).
`demo.sh` auto-detects it and uses `--build-arg USE_PREBUILT=1` to skip the
Rust build entirely — Docker image creation takes seconds instead of minutes.

To force a build from source instead:

```bash
docker build -f real-sovd-cda/Dockerfile \
  --build-context cda-src=real-sovd-cda/classic-diagnostic-adapter \
  -t opensovd-cda .
```

## Folder Structure

```
OpenBSW-SOVD-Demo/
├── CMakeLists.txt           # CMake overlay: wraps openbsw, adds app.sovdDemo
├── CMakePresets.json        # Build preset (posix-freertos-sovd)
├── demo.sh                  # One-click bring-up script
├── docker-compose.yaml      # Docker orchestration (ECU + CDA + Grafana)
├── HACKATHON.md             # Hackathon guide
├── README.md                # This file
├── prepare-gh-codespaces.md # Codespace setup instructions
│
├── real-sovd-cda/           # Eclipse OpenSOVD CDA (Rust) — real diagnostic adapter
│   ├── bin/opensovd-cda     # Pre-built binary (Git LFS, x86-64 Linux)
│   ├── opensovd-cda.toml    # CDA runtime configuration
│   ├── Dockerfile           # Multi-stage Docker build (supports USE_PREBUILT=1)
│   ├── classic-diagnostic-adapter/  # CDA Rust source (submodule)
│   ├── odx-converter/       # ODX-to-MDD converter (submodule)
│   └── odx-gen/             # MDD generation from ECU JSON description
│
├── sovd-cda/                # SOVD Stub CDA (Python/FastAPI) — simpler alternative
│   ├── main.py              # REST API → DoIP/UDS bridge
│   ├── catalog.json         # ECU component catalog (DTCs, DIDs)
│   ├── Dockerfile
│   └── requirements.txt
│
├── doc/                     # Documentation
│   ├── demo-architecture.md # Architecture diagrams & flow charts
│   └── requirements-summary.md  # MECE requirements checklist (57 items)
│
├── grafana/                 # Grafana dashboards + provisioning
│   ├── dashboards/openbsw.json
│   └── provisioning/
│
└── openbsw-overlay/         # C++ sources that augment OpenBSW (zero-patch)
    ├── libs/doip/           # DoIP interop fix (replaces upstream source at build time)
    │   └── src/doip/server/
    │       └── DoIpServerConnectionHandler.cpp  ← lines 284-290: ACK handling
    ├── libs/uds/            # Generic UDS additions (upstream candidates)
    │   ├── include/uds/dtc/               # DTC class + store
    │   └── include/uds/services/          # ReadDTCInformation, ClearDTC
    └── app/                 # Demo-specific simulation code
        ├── include/systems/UdsSystem.h    # Demo UdsSystem (replaces upstream)
        ├── include/uds/                   # DtcSimulator, ReadIdentifierSimulated
        └── src/                           # Corresponding implementations
```

## How It Works

The CMake overlay (`CMakeLists.txt`) adds the upstream `openbsw/` as a
subdirectory to obtain all library targets, then defines a **separate**
executable `app.sovdDemo.elf` that:

- Compiles its own `UdsSystem.cpp` (with DTC + sensor simulation wiring)
- Includes the demo-specific `DtcSimulator` and `ReadIdentifierSimulated`
- Links a small `uds_dtc_overlay` library with `ReadDTCInformation` (0x19)
  and `ClearDiagnosticInformation` (0x14) services
- Replaces the upstream `DoIpServerConnectionHandler.cpp` in the `doip` library
  target with an overlay copy that handles `DiagnosticMessagePositiveAck` (0x8002)
  and `DiagnosticMessageNegativeAck` (0x8003) payload types — the upstream source
  file remains **completely unmodified** (see `openbsw-overlay/libs/doip/`, lines 284-290)
- Links against all the same OpenBSW libraries as `app.referenceApp`

The overlay include path is listed **before** the upstream include path, so
the demo `UdsSystem.h` takes precedence without patching the original.

## Demo Features

- **5 simulated DTCs** (engine overtemp, low battery, comm fault, sensor
  malfunction, brake system) with realistic status bit toggling
- **3 simulated sensors** (engine temp, battery voltage, vehicle speed) with
  pseudo-random walk within physical bounds
- **UDS services**: 0x19 ReadDTCInformation (subfunctions 0x01, 0x02, 0x06),
  0x14 ClearDiagnosticInformation, 0x22 ReadDataByIdentifier
- **SOVD REST API** with Swagger UI at `/docs`
- **Grafana dashboard** with 5 panels (3 sensor gauges, DTC status table, API health)

> **Grafana networking note**: Grafana runs in a Docker container on bridge
> networking. Dashboard panel URLs use `http://host.docker.internal:8080`
> (not `localhost`) so the Infinity datasource can reach the CDA on the host.
> The `--add-host=host.docker.internal:host-gateway` flag in `demo.sh` maps
> this hostname to the host's IP.
