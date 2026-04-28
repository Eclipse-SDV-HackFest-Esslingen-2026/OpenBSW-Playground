"""
SOVD Classic Diagnostic Adapter (CDA) for OpenBSW

A minimal implementation of the SOVD (Service-Oriented Vehicle Diagnostics)
REST API that translates SOVD HTTP requests into UDS-over-DoIP messages
targeting an OpenBSW ECU.

Architecture:
  SOVD Client (browser/curl) --HTTP/REST--> This CDA --DoIP/UDS--> OpenBSW ECU

Implements a subset of ISO 17978 (SOVD) endpoints:
  GET  /sovd/v1/components                           - list ECUs
  GET  /sovd/v1/components/{id}                      - ECU info
  GET  /sovd/v1/components/{id}/faults                - read DTCs (UDS 0x19)
  GET  /sovd/v1/components/{id}/faults/{dtcId}        - read single DTC detail
  DELETE /sovd/v1/components/{id}/faults               - clear DTCs (UDS 0x14)
  GET  /sovd/v1/components/{id}/data/{did}            - read DID  (UDS 0x22)
  GET  /sovd/v1/components/{id}/data                  - list available DIDs
"""

import json
import struct
import time
import asyncio
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from doipclient import DoIPClient

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sovd-cda")

# ---------------------------------------------------------------------------
# Load diagnostic catalog
# ---------------------------------------------------------------------------
CATALOG_PATH = Path(__file__).parent / "catalog.json"
with open(CATALOG_PATH) as f:
    CATALOG = json.load(f)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SOVD Classic Diagnostic Adapter",
    description="Translates SOVD REST calls to UDS-over-DoIP for OpenBSW",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models (SOVD-like response schemas)
# ---------------------------------------------------------------------------

class ComponentInfo(BaseModel):
    id: str
    name: str
    description: str

class FaultEntry(BaseModel):
    id: str
    dtc_number: str
    name: str
    description: str
    severity: str
    system: str
    status_byte: int
    status: dict

class FaultDetail(FaultEntry):
    occurrence_counter: Optional[int] = None

class DataValue(BaseModel):
    did: str
    name: str
    description: str
    raw_hex: str
    value: Optional[float] = None
    unit: Optional[str] = None

# ---------------------------------------------------------------------------
# UDS status byte interpretation (ISO 14229 Annex D)
# ---------------------------------------------------------------------------
STATUS_BITS = {
    "testFailed":                 0x01,
    "testFailedThisOperationCycle": 0x02,
    "pendingDTC":                 0x04,
    "confirmedDTC":               0x08,
    "testNotCompletedSinceLastClear": 0x10,
    "testFailedSinceLastClear":   0x20,
    "testNotCompletedThisOperationCycle": 0x40,
    "warningIndicatorRequested":  0x80,
}

def decode_status_byte(sb: int) -> dict:
    return {name: bool(sb & mask) for name, mask in STATUS_BITS.items()}

# ---------------------------------------------------------------------------
# DoIP/UDS transport helper
# ---------------------------------------------------------------------------

def _get_component_config(component_id: str) -> dict:
    comp = CATALOG["components"].get(component_id)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")
    return comp

@contextmanager
def _doip_connection(comp: dict):
    """Create a short-lived DoIP connection to the ECU."""
    doip_cfg = comp["doip"]
    client = None
    try:
        client = DoIPClient(
            ecu_ip_address=doip_cfg["host"],
            ecu_logical_address=int(doip_cfg["ecu_logical_address"], 16),
            protocol_version=doip_cfg["protocol_version"],
            client_logical_address=int(doip_cfg["client_logical_address"], 16),
        )
        yield client
    except Exception as e:
        logger.error("DoIP connection failed: %s", e)
        raise HTTPException(status_code=502, detail=f"ECU communication error: {e}")
    finally:
        if client:
            try:
                client.close()
            except Exception:
                pass

def _send_uds(client: DoIPClient, request: bytes) -> bytes:
    """Send a UDS request via DoIP and return the response payload."""
    logger.info("UDS TX: %s", request.hex())
    client.send_diagnostic(request)
    resp = client.receive_diagnostic()
    if resp is None:
        raise HTTPException(status_code=504, detail="No response from ECU")
    logger.info("UDS RX: %s", resp.hex())
    # Check for negative response (0x7F)
    if len(resp) >= 3 and resp[0] == 0x7F:
        nrc = resp[2]
        nrc_names = {
            0x10: "generalReject",
            0x11: "serviceNotSupported",
            0x12: "subFunctionNotSupported",
            0x13: "incorrectMessageLengthOrInvalidFormat",
            0x14: "responseTooLong",
            0x22: "conditionsNotCorrect",
            0x31: "requestOutOfRange",
        }
        raise HTTPException(
            status_code=422,
            detail=f"UDS negative response: NRC 0x{nrc:02X} ({nrc_names.get(nrc, 'unknown')})"
        )
    return resp

# ---------------------------------------------------------------------------
# SOVD Endpoints
# ---------------------------------------------------------------------------

@app.get("/sovd/v1/components", tags=["Components"])
def list_components():
    """List all available ECU components."""
    items = []
    for cid, comp in CATALOG["components"].items():
        items.append(ComponentInfo(
            id=cid,
            name=comp["name"],
            description=comp["description"],
        ))
    return {"items": items}

@app.get("/sovd/v1/components/{component_id}", tags=["Components"])
def get_component(component_id: str):
    """Get detailed information about a component."""
    comp = _get_component_config(component_id)
    return {
        "id": component_id,
        "name": comp["name"],
        "description": comp["description"],
        "connection": {
            "protocol": "DoIP",
            "host": comp["doip"]["host"],
            "port": comp["doip"].get("port", 13400),
            "ecu_address": comp["doip"]["ecu_logical_address"],
        },
        "capabilities": {
            "faults": True,
            "data": True,
            "fault_count": len(comp.get("dtcs", {})),
            "data_count": len(comp.get("dids", {})),
        }
    }

@app.get("/sovd/v1/components/{component_id}/faults", tags=["Faults"])
def read_faults(component_id: str, status_mask: int = Query(0xFF, description="DTC status mask filter")):
    """
    Read all DTCs from the ECU.

    Sends UDS ReadDTCInformation (0x19) subfunction 0x02 (reportDTCByStatusMask).
    """
    comp = _get_component_config(component_id)
    dtc_catalog = comp.get("dtcs", {})

    with _doip_connection(comp) as doip:
        # UDS: 0x19 0x02 <statusMask>
        resp = _send_uds(doip, bytes([0x19, 0x02, status_mask & 0xFF]))

    # Response: 0x59 0x02 <availMask> [DTC_hi DTC_mid DTC_lo status]*
    if len(resp) < 3 or resp[0] != 0x59:
        raise HTTPException(status_code=502, detail="Unexpected response format")

    avail_mask = resp[2]
    dtc_data = resp[3:]
    faults = []

    for i in range(0, len(dtc_data) - 3, 4):
        dtc_hi = dtc_data[i]
        dtc_mid = dtc_data[i + 1]
        dtc_lo = dtc_data[i + 2]
        status_byte = dtc_data[i + 3]
        dtc_num = (dtc_hi << 16) | (dtc_mid << 8) | dtc_lo
        dtc_hex = f"0x{dtc_num:06X}"

        cat = dtc_catalog.get(dtc_hex, {})
        faults.append(FaultEntry(
            id=dtc_hex,
            dtc_number=dtc_hex,
            name=cat.get("name", f"DTC_{dtc_hex}"),
            description=cat.get("description", "Unknown DTC"),
            severity=cat.get("severity", "unknown"),
            system=cat.get("system", "unknown"),
            status_byte=status_byte,
            status=decode_status_byte(status_byte),
        ))

    return {
        "availability_mask": f"0x{avail_mask:02X}",
        "count": len(faults),
        "items": faults,
    }

@app.get("/sovd/v1/components/{component_id}/faults/{dtc_id}", tags=["Faults"])
def read_fault_detail(component_id: str, dtc_id: str):
    """
    Read details for a specific DTC, including extended data.

    Sends UDS ReadDTCInformation (0x19) subfunction 0x06
    (reportDTCExtDataRecordByDTCNumber).
    """
    comp = _get_component_config(component_id)
    dtc_catalog = comp.get("dtcs", {})

    # Parse dtc_id as hex number
    try:
        dtc_num = int(dtc_id, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid DTC ID: {dtc_id}")

    dtc_hi = (dtc_num >> 16) & 0xFF
    dtc_mid = (dtc_num >> 8) & 0xFF
    dtc_lo = dtc_num & 0xFF

    with _doip_connection(comp) as doip:
        # UDS: 0x19 0x06 <DTC_hi> <DTC_mid> <DTC_lo> <recordNum=0xFF>
        resp = _send_uds(doip, bytes([0x19, 0x06, dtc_hi, dtc_mid, dtc_lo, 0xFF]))

    # Response: 0x59 0x06 <DTC_hi> <DTC_mid> <DTC_lo> <status> [extData...]
    if len(resp) < 7 or resp[0] != 0x59:
        raise HTTPException(status_code=502, detail="Unexpected response format")

    status_byte = resp[5]
    occurrence_counter = resp[6] if len(resp) > 6 else None

    dtc_hex = f"0x{dtc_num:06X}"
    cat = dtc_catalog.get(dtc_hex, {})

    return FaultDetail(
        id=dtc_hex,
        dtc_number=dtc_hex,
        name=cat.get("name", f"DTC_{dtc_hex}"),
        description=cat.get("description", "Unknown DTC"),
        severity=cat.get("severity", "unknown"),
        system=cat.get("system", "unknown"),
        status_byte=status_byte,
        status=decode_status_byte(status_byte),
        occurrence_counter=occurrence_counter,
    )

@app.delete("/sovd/v1/components/{component_id}/faults", tags=["Faults"])
def clear_faults(component_id: str, group: str = Query("0xFFFFFF", description="DTC group (default: all)")):
    """
    Clear DTCs from the ECU.

    Sends UDS ClearDiagnosticInformation (0x14).
    """
    comp = _get_component_config(component_id)

    try:
        group_num = int(group, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid group: {group}")

    g_hi = (group_num >> 16) & 0xFF
    g_mid = (group_num >> 8) & 0xFF
    g_lo = group_num & 0xFF

    with _doip_connection(comp) as doip:
        resp = _send_uds(doip, bytes([0x14, g_hi, g_mid, g_lo]))

    # Positive response: 0x54
    if resp[0] != 0x54:
        raise HTTPException(status_code=502, detail="Unexpected response to ClearDTC")

    return {"status": "ok", "message": "DTCs cleared successfully", "group": group}

@app.get("/sovd/v1/components/{component_id}/data", tags=["Data"])
def list_data(component_id: str):
    """List all available data identifiers (DIDs) for a component."""
    comp = _get_component_config(component_id)
    dids = comp.get("dids", {})
    items = []
    for did_hex, info in dids.items():
        items.append({
            "did": did_hex,
            "name": info["name"],
            "description": info["description"],
            "access": info.get("access", "read"),
            "unit": info.get("unit"),
        })
    return {"count": len(items), "items": items}

@app.get("/sovd/v1/components/{component_id}/data/{did}", tags=["Data"])
def read_data(component_id: str, did: str):
    """
    Read a Data Identifier (DID) value from the ECU.

    Sends UDS ReadDataByIdentifier (0x22).
    """
    comp = _get_component_config(component_id)
    did_catalog = comp.get("dids", {})

    # Parse DID as hex
    try:
        did_num = int(did, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid DID: {did}")

    did_hi = (did_num >> 8) & 0xFF
    did_lo = did_num & 0xFF

    with _doip_connection(comp) as doip:
        # UDS: 0x22 <DID_hi> <DID_lo>
        resp = _send_uds(doip, bytes([0x22, did_hi, did_lo]))

    # Response: 0x62 <DID_hi> <DID_lo> <data...>
    if len(resp) < 3 or resp[0] != 0x62:
        raise HTTPException(status_code=502, detail="Unexpected response format")

    data_bytes = resp[3:]
    raw_hex = data_bytes.hex()

    did_hex = f"0x{did_num:04X}"
    cat = did_catalog.get(did_hex, {})
    fmt = cat.get("format", "raw")

    # Try to interpret the value based on catalog format
    value = None
    if fmt == "int32" and len(data_bytes) >= 4:
        value = float(struct.unpack(">i", data_bytes[:4])[0])
    elif fmt == "uint16" and len(data_bytes) >= 2:
        value = float(struct.unpack(">H", data_bytes[:2])[0])
    elif fmt == "int16" and len(data_bytes) >= 2:
        value = float(struct.unpack(">h", data_bytes[:2])[0])

    return DataValue(
        did=did_hex,
        name=cat.get("name", f"DID_{did_hex}"),
        description=cat.get("description", "Unknown DID"),
        raw_hex=raw_hex,
        value=value,
        unit=cat.get("unit"),
    )

# ---------------------------------------------------------------------------
# Health / info endpoints
# ---------------------------------------------------------------------------

@app.get("/sovd/v1/info", tags=["Info"])
def info():
    """SOVD server information."""
    return {
        "name": "OpenBSW SOVD Classic Diagnostic Adapter",
        "version": "0.1.0",
        "sovd_version": "1.0.0-draft",
        "description": "Hackathon demo: translates SOVD REST to UDS/DoIP",
    }

@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# History store – ring buffer of recent readings for Grafana time-series
# ---------------------------------------------------------------------------
MAX_HISTORY = 300  # ~5 minutes at 1 sample/sec

# sensor_history[did_hex] = deque([(epoch_ms, value), ...])
sensor_history: dict[str, deque] = {}
# fault_history = deque([(epoch_ms, {dtc_hex: status_byte}), ...])
fault_history: deque = deque(maxlen=MAX_HISTORY)

POLL_DIDS = ["CF10", "CF11", "CF12"]  # engine temp, battery, speed
POLL_COMPONENT = "openbsw-ecu"

def _poll_ecu_once():
    """Poll all sensors and faults from the ECU once."""
    comp = CATALOG["components"].get(POLL_COMPONENT)
    if not comp:
        return
    doip_cfg = comp["doip"]
    did_catalog = comp.get("dids", {})
    dtc_catalog = comp.get("dtcs", {})
    ts = int(time.time() * 1000)

    try:
        client = DoIPClient(
            ecu_ip_address=doip_cfg["host"],
            ecu_logical_address=int(doip_cfg["ecu_logical_address"], 16),
            protocol_version=doip_cfg["protocol_version"],
            client_logical_address=int(doip_cfg["client_logical_address"], 16),
        )

        # Poll each DID
        for did_str in POLL_DIDS:
            try:
                did_num = int(did_str, 16)
                did_hi = (did_num >> 8) & 0xFF
                did_lo = did_num & 0xFF
                client.send_diagnostic(bytes([0x22, did_hi, did_lo]))
                resp = client.receive_diagnostic()
                if resp and len(resp) >= 7 and resp[0] == 0x62:
                    data_bytes = resp[3:]
                    did_hex = f"0x{did_str.upper()}"
                    cat = did_catalog.get(did_hex, {})
                    fmt = cat.get("format", "raw")
                    value = None
                    if fmt == "int32" and len(data_bytes) >= 4:
                        value = float(struct.unpack(">i", data_bytes[:4])[0])
                    elif fmt == "uint16" and len(data_bytes) >= 2:
                        value = float(struct.unpack(">H", data_bytes[:2])[0])
                    if value is not None:
                        if did_hex not in sensor_history:
                            sensor_history[did_hex] = deque(maxlen=MAX_HISTORY)
                        sensor_history[did_hex].append((ts, value))
            except Exception as e:
                logger.debug("Poll DID %s failed: %s", did_str, e)

        # Poll faults
        try:
            client.send_diagnostic(bytes([0x19, 0x02, 0xFF]))
            resp = client.receive_diagnostic()
            if resp and len(resp) >= 3 and resp[0] == 0x59:
                dtc_data = resp[3:]
                fault_snap = {}
                for i in range(0, len(dtc_data) - 3, 4):
                    dtc_num = (dtc_data[i] << 16) | (dtc_data[i+1] << 8) | dtc_data[i+2]
                    status_byte = dtc_data[i+3]
                    fault_snap[f"0x{dtc_num:06X}"] = status_byte
                fault_history.append((ts, fault_snap))
        except Exception as e:
            logger.debug("Poll faults failed: %s", e)

        client.close()
    except Exception as e:
        logger.warning("ECU poll failed: %s", e)

async def _background_poller():
    """Background task polling the ECU every second."""
    await asyncio.sleep(2)  # let the ECU start up
    while True:
        try:
            await asyncio.get_event_loop().run_in_executor(None, _poll_ecu_once)
        except Exception as e:
            logger.warning("Poller error: %s", e)
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(_background_poller())
    logger.info("Background ECU poller started")

# ---------------------------------------------------------------------------
# Grafana-friendly endpoints
# ---------------------------------------------------------------------------

@app.get("/api/sensors/current", tags=["Grafana"])
def sensors_current():
    """Return latest value for each polled sensor (for Stat/Gauge panels)."""
    comp = CATALOG["components"].get(POLL_COMPONENT, {})
    did_catalog = comp.get("dids", {})
    result = []
    for did_hex, hist in sensor_history.items():
        if hist:
            ts, val = hist[-1]
            cat = did_catalog.get(did_hex, {})
            result.append({
                "did": did_hex,
                "name": cat.get("name", did_hex),
                "value": val,
                "unit": cat.get("unit", ""),
                "timestamp": ts,
            })
    return result

@app.get("/api/sensors/history", tags=["Grafana"])
def sensors_history_endpoint(did: str = Query(..., description="DID hex, e.g. 0xCF10")):
    """Return time-series history for a sensor (for Graph panels)."""
    did_upper = did.upper()
    if not did_upper.startswith("0X"):
        did_upper = "0x" + did_upper
    hist = sensor_history.get(did_upper, deque())
    return [{"time": ts, "value": val} for ts, val in hist]

@app.get("/api/faults/current", tags=["Grafana"])
def faults_current():
    """Return latest DTC snapshot (for Table panels)."""
    comp = CATALOG["components"].get(POLL_COMPONENT, {})
    dtc_catalog = comp.get("dtcs", {})
    if not fault_history:
        return []
    ts, snap = fault_history[-1]
    result = []
    for dtc_hex, status_byte in snap.items():
        cat = dtc_catalog.get(dtc_hex, {})
        result.append({
            "dtc": dtc_hex,
            "name": cat.get("name", dtc_hex),
            "description": cat.get("description", ""),
            "severity": cat.get("severity", "unknown"),
            "system": cat.get("system", "unknown"),
            "status_byte": status_byte,
            "testFailed": bool(status_byte & 0x01),
            "confirmedDTC": bool(status_byte & 0x08),
            "timestamp": ts,
        })
    return result

@app.get("/api/faults/history", tags=["Grafana"])
def faults_history_endpoint():
    """Return fault count over time (for Graph panels)."""
    result = []
    for ts, snap in fault_history:
        active = sum(1 for s in snap.values() if s & 0x01)
        confirmed = sum(1 for s in snap.values() if s & 0x08)
        result.append({
            "time": ts,
            "active_faults": active,
            "confirmed_faults": confirmed,
            "total_faults": len(snap),
        })
    return result

@app.get("/api/faults/active_count", tags=["Grafana"])
def faults_active_count():
    """Return current number of active faults (testFailed bit set)."""
    if not fault_history:
        return [{"active_faults": 0}]
    _, snap = fault_history[-1]
    active = sum(1 for s in snap.values() if s & 0x01)
    return [{"active_faults": active}]

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
