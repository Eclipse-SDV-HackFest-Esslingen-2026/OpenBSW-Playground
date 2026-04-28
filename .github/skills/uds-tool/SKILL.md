---
name: uds-tool
description: "UDS Tool skill for OpenBSW UdsTool CLI. Use when: sending UDS diagnostic requests, reading DIDs, writing DIDs, security access, session control, routine control, ECU reset, request download, transfer data, raw UDS payloads, CAN diagnostics, DoIP diagnostics, ISO 14229, ISO 13400, automotive ECU diagnostics, udstool command, canConfig, python-can, udsoncan. Covers installation, connection setup (CAN/DoIP), all service workflows, example commands, troubleshooting."
argument-hint: "udstool read|write|session|security|routine|raw --can|--eth [connection options] [service options]"
---

# UDS Tool Skill

The **UdsTool** is a Python CLI for communicating with automotive ECUs using **Unified Diagnostic Services (UDS / ISO 14229-1)**. It supports two transport layers — **CAN (ISO-TP / ISO 15765-2)** and **Ethernet (DoIP / ISO 13400)** — and is built on top of the `udsoncan` and `python-can` libraries using the `click` CLI framework.

Tool source: `openbsw/tools/UdsTool/`

---

## When to Use

Load this skill whenever:
- Working with `udstool` CLI commands
- Diagnosing, reading, or writing ECU data via UDS
- Setting up CAN (socketcan, pcan) or DoIP (Ethernet) connections to an ECU
- Implementing or debugging UDS service sequences (session, security access, download, etc.)
- Configuring ISO-TP parameters (`canConfig.json`)
- Running diagnostics against **any UDS-capable ECU** (including the OpenBSW referenceApp) on POSIX or S32K1xx targets
- Asking `gh copilot suggest` for UDS-related commands

---

## Architecture

```
udsTool.py          ← Click CLI entry point; console_scripts: udstool → udsTool:start
  app/
    connection.py   ← createCanConnection() / createEthConnection()
    services.py     ← Per-service request builders (udsoncan library)
    helper.py       ← Binary utils, CRC32, seed/key XOR, response printer
    rawCommand.py   ← Service enum dispatcher for raw hex payloads
    canConfig.json  ← ISO-TP default parameters for CAN transport
```

**Dependency chain:**
```
Click (CLI) → connection.py → udsoncan.Client
                                  ↕
                  CAN: python-can Bus + can-isotp CanStack (ISO 15765-2)
                  ETH: doipclient DoIPClient (ISO 13400 v2/v3)
```

---

## Installation

```bash
cd openbsw/tools/UdsTool

# Standard
pip install .

# Editable (keep source changes live)
pip install --editable .
```

**Python requirement:** `>=3.7`

**Key dependencies** (`requirements.txt`):
| Package | Version | Purpose |
|---------|---------|---------|
| `udsoncan` | 1.23.1 | UDS protocol (ISO 14229-1) |
| `python-can` | 4.4.2 | CAN bus abstraction |
| `can-isotp` | 2.0.6 | ISO-TP segmentation (ISO 15765-2) |
| `doipclient` | 1.1.1 | DoIP transport (ISO 13400) |
| `click` | 8.0.3 | CLI framework |

After installation the `udstool` command is available system-wide.

---

## Connection Setup

All commands accept the same connection flags. Choose **either** `--can` or `--eth`.

### CAN Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--can` | flag | — | Activates CAN transport |
| `--canif` | string | `socketcan` | python-can interface: `socketcan` (Linux), `pcan` (PCAN adapter) |
| `--channel` | string | — | CAN channel: `vcan0` (POSIX virtual), `pcan` (S32K148) |
| `--txid` | hex string | — | Transmit CAN ID (ECU logical address) |
| `--rxid` | hex string | — | Receive CAN ID (client logical address) |
| `--config` | path | — | Path to ISO-TP `canConfig.json` |

**OpenBSW referenceApp defaults (CAN):**
- ECU address (txid): `0x2A`
- Client address (rxid): `0xEF0`
- Channel POSIX: `vcan0`
- Channel S32K148: `pcan`

### DoIP (Ethernet) Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--eth` | flag | — | Activates DoIP transport |
| `--host` | IP string | — | ECU IP address |
| `--ecu` | hex string | — | ECU logical address |
| `--source` | hex string | — | Client (tester) logical address |
| `--doip` | int | `2` | DoIP protocol version: `2` (ISO 13400-2:2012) or `3` (ISO 13400-3:2019) |

**OpenBSW referenceApp defaults (DoIP):**
- Host POSIX: `192.168.0.201`
- Host S32K1xx: `192.168.0.200`
- ECU logical address: `0x2A`
- Client logical address: `0xEF1`

---

## canConfig.json Reference

Located at `openbsw/tools/UdsTool/app/canConfig.json`. Pass with `--config <path>`.

```json
{
    "stmin": 32,
    "wftmax": 0,
    "tx_padding": 0,
    "rx_flowcontrol_timeout": 1000,
    "rx_consecutive_frame_timeout": 1000,
    "override_receiver_stmin": 0
}
```

| Field | Unit | Description |
|-------|------|-------------|
| `stmin` | ms | Minimum separation time between consecutive CAN frames sent by this node |
| `wftmax` | count | Maximum number of Wait Flow Control frames to accept (0 = no limit) |
| `tx_padding` | 0/1 | Pad outgoing CAN frames to 8 bytes (0 = off) |
| `rx_flowcontrol_timeout` | ms | Timeout waiting for Flow Control frame from peer |
| `rx_consecutive_frame_timeout` | ms | Timeout waiting for next Consecutive Frame |
| `override_receiver_stmin` | ms | Force a specific stmin regardless of what the receiver reports (0 = off) |

---

## Commands Reference

### `read` — Read Data By Identifier (SID 0x22)

```
udstool read [CONNECTION FLAGS] --did <hex_did>
```

| Flag | Type | Description |
|------|------|-------------|
| `--did` | hex string | Data Identifier to read (e.g. `cf01`) |

**Response SID:** `0x62`

---

### `write` — Write Data By Identifier (SID 0x2E)

```
udstool write [CONNECTION FLAGS] --did <hex_did> --data <value>
```

| Flag | Type | Description |
|------|------|-------------|
| `--did` | hex string | Data Identifier to write |
| `--data` | string | ASCII data value to write |

**Response SID:** `0x6E`

---

### `session` — Diagnostic Session Control (SID 0x10)

```
udstool session [CONNECTION FLAGS] --id <hex_session_id>
```

| Flag | Type | Description |
|------|------|-------------|
| `--id` | hex string | Session identifier |

**Session IDs:**
| Value | Session Type |
|-------|-------------|
| `01` | Default Session |
| `02` | Programming Session |
| `03` | Extended Diagnostic Session |

**Response SID:** `0x50`

---

### `security` — Security Access (SID 0x27)

```
udstool security [CONNECTION FLAGS] --level <int> --path <keyfile>
```

| Flag | Type | Description |
|------|------|-------------|
| `--level` | int | Security access level to unlock |
| `--path` | path | Path to shared key binary file (16 bytes) |

**Two-step flow (handled automatically):**
1. Send `RequestSeed` (sub-function = `level`) → receive 16-byte seed
2. Compute key = XOR of seed with shared key file (first 16 bytes)
3. Send `SendKey` (sub-function = `level + 1`) with computed key

**Response SID:** `0x67`

---

### `routine` — Routine Control (SID 0x31)

```
udstool routine [CONNECTION FLAGS] --type <int> --id <hex_id>
```

| Flag | Type | Description |
|------|------|-------------|
| `--type` | int | Sub-function / routine type |
| `--id` | hex string | Routine identifier |

Raises `RoutineFailedException` if `response.get_payload()[4] != 0`.

**Response SID:** `0x71`

---

### `raw` — Raw UDS Payload Dispatcher

```
udstool raw [CONNECTION FLAGS] --data <hex_payload> [--path <binary_file>]
```

| Flag | Type | Description |
|------|------|-------------|
| `--data` | hex string | Full UDS payload (SID + data), e.g. `22cf01` |
| `--path` | path | Optional: binary file path (for Transfer Data 0x36) |

**Dispatcher routing** (keyed on first byte pair of `--data`):

| Prefix | Service | Payload Layout |
|--------|---------|----------------|
| `22` | Read DID (0x22) | `22` + DID (4 hex chars) |
| `2e` | Write DID (0x2E) | `2e` + DID (4) + data |
| `10` | Session Control (0x10) | `10` + session ID (2) |
| `11` | ECU Reset (0x11) | `11` + reset type (int as string) |
| `27` | Security Access (0x27) | `27` + level |
| `31` | Routine Control (0x31) | `31` + type (2) + ID (4) [+ optional data] |
| `34` | Request Download (0x34) | `34` + method (2) + memSizeLen (1) + addrLen (1) + address + memSize |
| `36` | Transfer Data (0x36) | `36` + counter (2) + hex data [or use `--path` for binary file] |
| `37` | Transfer Exit (0x37) | `37` |

---

## Service Workflows

### Firmware Download Sequence

The full OTA/flash workflow using raw commands.

> Replace `<ECU_IP>` with your ECU's actual IP address.

```bash
# 1. Switch to programming session
udstool raw --eth --host <ECU_IP> --ecu 002a --source ef1 --data 1002

# 2. Security access — unlock level 1 (requires shared key file)
udstool security --eth --host <ECU_IP> --ecu 002a --source ef1 --level 1 --path ./shared_key.bin

# 3. Request download (example: address=0x08000000, size=0x20000, 32-bit lengths)
#    Payload: 34 + method(00) + memSizeLen(4) + addrLen(4) + address + size
udstool raw --eth --host <ECU_IP> --ecu 002a --source ef1 \
    --data 340044000000000000200000

# 4. Transfer data from binary file (counter starts at 1)
udstool raw --eth --host <ECU_IP> --ecu 002a --source ef1 \
    --data 3601 --path ./firmware.bin

# 5. Transfer exit
udstool raw --eth --host <ECU_IP> --ecu 002a --source ef1 --data 37

# 6. Return to default session
udstool raw --eth --host <ECU_IP> --ecu 002a --source ef1 --data 1001
```

### Security Access Key Calculation

```python
# helper.calculateKey() — exact algorithm:
def calculateKey(seed, path):
    sharedKey = open(path, "rb").read()   # first 16 bytes used
    return bytes([seed[i] ^ sharedKey[i] for i in range(16)])
```

The seed is extracted from the `RequestSeed` response by skipping the first 2 bytes:
```python
seed = response.get_payload()[2:]   # [SID(0x67), sub-fn, seed bytes...]
```

### Transfer Data Chunking

Large binaries are split into `0xFF0` (4080) byte bundles automatically:
```python
def divideBinaryIntoBundles(binary_data, bundle_size=0xFF0):
    return [binary_data[i:i+bundle_size] for i in range(0, len(binary_data), bundle_size)]
```
The counter wraps modulo 256 across bundles.

---

## Example Commands

### CAN — POSIX (vcan0)

```bash
# Read DID 0xCF01
udstool read --can --channel vcan0 --txid 2A --rxid F0 \
    --did cf01 --config tools/UdsTool/app/canConfig.json

# Write DID 0xCF03 with value "999"
udstool write --can --channel vcan0 --txid 2A --rxid F0 \
    --did cf03 --data 999 --config tools/UdsTool/app/canConfig.json

# Switch to default session (0x01)
udstool session --can --channel vcan0 --txid 2A --rxid F0 \
    --id 01 --config tools/UdsTool/app/canConfig.json

# Security access level 1
udstool security --can --channel vcan0 --txid 2A --rxid F0 \
    --level 1 --path ./shared_key.bin \
    --config tools/UdsTool/app/canConfig.json

# Routine control: type 1, routine ID 0xFF00
udstool routine --can --channel vcan0 --txid 2A --rxid F0 \
    --type 1 --id ff00 --config tools/UdsTool/app/canConfig.json

# ECU reset (hard reset = type 1)
udstool raw --can --channel vcan0 --txid 2A --rxid F0 \
    --data 1101 --config tools/UdsTool/app/canConfig.json

# Raw: read DID 0xCF01
udstool raw --can --channel vcan0 --txid 2A --rxid F0 \
    --data 22cf01 --config tools/UdsTool/app/canConfig.json
```

### CAN — S32K148 (pcan interface)

```bash
udstool read --can --canif pcan --channel pcan --txid 2A --rxid F0 \
    --did cf01 --config tools/UdsTool/app/canConfig.json
```

### DoIP — Ethernet

> Replace `<ECU_IP>` with your ECU's actual IP address.
> OpenBSW referenceApp defaults: POSIX → `192.168.0.201`, S32K1xx → `192.168.0.200`.

```bash
# Read DID 0xCF01
udstool read --eth --host <ECU_IP> --ecu 002a --source ef1 --did cf01

# Write DID 0xCF03 with value "999"
udstool write --eth --host <ECU_IP> --ecu 002a --source ef1 \
    --did cf03 --data 999

# Switch to extended session (0x03)
udstool session --eth --host <ECU_IP> --ecu 002a --source ef1 --id 03

# Security access level 1
udstool security --eth --host <ECU_IP> --ecu 002a --source ef1 \
    --level 1 --path ./shared_key.bin

# Routine control: type 1, routine ID 0xFF00
udstool routine --eth --host <ECU_IP> --ecu 002a --source ef1 \
    --type 1 --id ff00

# ECU reset
udstool raw --eth --host <ECU_IP> --ecu 002a --source ef1 --data 1101

# DoIP version 3 (ISO 13400-3:2019)
udstool read --eth --host <ECU_IP> --ecu 002a --source ef1 \
    --did cf01 --doip 3
```

---

## Helper Utilities Reference

| Function | Signature | Description |
|----------|-----------|-------------|
| `handleResponse` | `(response) → response` | Prints hex payload + response object; returns response |
| `extractSeed` | `(response) → bytes` | Returns `response.get_payload()[2:]` (skips SID + sub-fn) |
| `calculateKey` | `(seed: bytes, path: str) → bytes` | XOR of seed[0:16] with sharedKey[0:16] |
| `getSharedKey` | `(path: str) → bytes` | Reads binary key file |
| `divideBinaryIntoBundles` | `(data, bundle_size=0xFF0) → list[bytes]` | Splits binary into 4080-byte chunks |
| `calculateCrc32` | `(path: str) → int` | CRC32 of file (zlib, streaming 4096-byte chunks) |
| `getSize` | `(path: str) → int` | File size in bytes via `os.path.getsize` |
| `getDate` | `() → str` | Current date as `YYMMDD` string |

---

## Common Pitfalls & Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Error during UDS operation` on CAN | Missing or wrong `--config` path | Point to a valid `canConfig.json`; copy from `tools/UdsTool/app/canConfig.json` |
| `Can't connect to CAN bus` | `vcan0` not set up | `sudo modprobe vcan && sudo ip link add dev vcan0 type vcan && sudo ip link set vcan0 up` |
| Security access fails | Wrong key file or mismatched level | Ensure `--path` points to a 16-byte binary key matching the ECU; `--level` must be odd (request seed uses even sub-fn internally) |
| `Service not supported by tool` | Unknown SID prefix in `--data` | Raw dispatcher only handles: `10 11 22 27 2e 31 34 36 37` |
| DoIP connection refused | Wrong host, ECU not in DoIP mode | Verify `--host` reachability (`ping`), switch to programming session first if required |
| Transfer Data counter mismatch | Counter not matching ECU expectation | Counter auto-wraps mod 256; ensure `requestDownload` was acknowledged before starting |
| `RoutineFailedException` | `response.get_payload()[4] != 0` | Check routine ID, type, and whether correct session/security level is active |
| `txid`/`rxid` hex parsing fails | Leading `0x` prefix passed | Pass raw hex without prefix: `--txid 2A` not `--txid 0x2A` |
| DoIP version mismatch | ECU uses ISO 13400-3 but default v2 used | Add `--doip 3` |

---

## Quick Reference Card

> The values below (`vcan0`, `txid 2A`, `rxid F0`) are the **OpenBSW referenceApp defaults**.
> Replace them with your ECU's actual CAN channel, transmit ID, and receive ID.

```
# Setup virtual CAN (POSIX one-time setup)
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set vcan0 up

# Install UdsTool
cd openbsw/tools/UdsTool && pip install .

# Monitor CAN traffic (separate terminal)
candump vcan0

# Read → Write → Session → Security → Raw
udstool read     --can --channel <CHANNEL> --txid <TXID> --rxid <RXID> --did <DID>            --config app/canConfig.json
udstool write    --can --channel <CHANNEL> --txid <TXID> --rxid <RXID> --did <DID> --data <V> --config app/canConfig.json
udstool session  --can --channel <CHANNEL> --txid <TXID> --rxid <RXID> --id <01|02|03>        --config app/canConfig.json
udstool security --can --channel <CHANNEL> --txid <TXID> --rxid <RXID> --level <N> --path <K> --config app/canConfig.json
udstool routine  --can --channel <CHANNEL> --txid <TXID> --rxid <RXID> --type <T> --id <ID>   --config app/canConfig.json
udstool raw      --can --channel <CHANNEL> --txid <TXID> --rxid <RXID> --data <HEX>           --config app/canConfig.json

# OpenBSW referenceApp values: --channel vcan0 --txid 2A --rxid F0
```
