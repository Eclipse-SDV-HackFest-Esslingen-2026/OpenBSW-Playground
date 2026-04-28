# ECU Fault Memory in Embedded Flash

A classic automotive ECU has only a small amount of on-chip memory but must
remember **diagnostic data across power cycles**: identification data exposed
via **DIDs** (`0x22 / 0x2E`) and the **fault memory** queried via DTC services
(`0x19`, `0x14`). This is implemented on top of the microcontroller’s
**embedded non-volatile Flash** using a small NVM / EEPROM-emulation layer.


- DID = a named variable in the ECU you can read/write.
- DTC = a logged event that says something went wrong.



# ECU Fault Memory in Embedded Flash

A classic automotive ECU has only a small amount of on-chip memory but must
remember **diagnostic data across power cycles**: identification data exposed
via **DIDs** (`0x22 / 0x2E`) and the **fault memory** queried via DTC services
(`0x19`, `0x14`). This is implemented on top of the microcontroller’s
**embedded non-volatile Flash** using a small NVM / EEPROM-emulation layer.

## Memory map of a typical ECU

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'16px','fontFamily':'Arial','lineColor':'#FFFFFF','textColor':'#FFFFFF','arrowheadColor':'#FFFFFF'}}}%%
flowchart TB
    subgraph MCU["Microcontroller (e.g. S32K148)"]
        direction TB

        subgraph PFlash["Program Flash (code + const)"]
            direction LR
            BL["Bootloader"]:::pflash
            APP["Application<br/>(BSW + ASW)"]:::pflash
            CAL["Calibration / const DIDs<br/>(VIN, HW/SW version, part no.)"]:::pflash
        end

        subgraph DFlash["Data Flash / EEPROM area"]
            direction LR
            NVMA["NVM Block A<br/>(active)"]:::dflash
            NVMB["NVM Block B<br/>(shadow)"]:::dflash
            FMGR["NVM / Fee manager<br/>wear-levelling • CRC • A/B swap"]:::dflash
        end

        subgraph RAM["SRAM (volatile)"]
            direction LR
            MIRROR["RAM mirror<br/>of NVM blocks"]:::ram
            EVMEM["Event memory<br/>active DTCs • snapshots • counters"]:::ram
        end
    end

    APP <-->|"read / write"| MIRROR
    MIRROR <-->|"on change / shutdown"| FMGR
    FMGR <--> NVMA
    FMGR <--> NVMB
    APP -. "read-only" .- CAL
    EVMEM <--> MIRROR

    classDef pflash fill:#1565C0,stroke:#0D47A1,stroke-width:2px,color:#FFFFFF
    classDef dflash fill:#6A1B9A,stroke:#4A148C,stroke-width:2px,color:#FFFFFF
    classDef ram    fill:#2E7D32,stroke:#1B5E20,stroke-width:2px,color:#FFFFFF

    style MCU    fill:#FAFAFA,stroke:#212121,stroke-width:2px,color:#212121
    style PFlash fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    style DFlash fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C
    style RAM    fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
```

**Key idea:** the application never writes to Flash directly. It works on a
**RAM mirror**; an NVM manager periodically (or on shutdown / on event)
serializes the dirty blocks into Data Flash, protected by a **CRC** and an
**A/B (ping-pong)** scheme so a power loss during the write cannot corrupt the
last good copy.

## What lives in fault memory

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'16px','fontFamily':'Arial','lineColor':'#FFFFFF','textColor':'#FFFFFF','arrowheadColor':'#FFFFFF'}}}%%
flowchart LR
    subgraph FaultMem["Fault Memory (per DTC entry)"]
        direction TB
        DTC["DTC ID<br/>(3 bytes, ISO 15031-6 / 14229-1)"]:::dtc
        STAT["Status byte (8 bits)<br/>testFailed • confirmedDTC<br/>pendingDTC • warningIndicator"]:::dtc
        AGE["Aging / occurrence counter"]:::dtc
        SNAP["Snapshot / FreezeFrame<br/>DIDs captured at fault time"]:::dtc
        EXT["Extended data records<br/>fault counters, env. data"]:::dtc
    end

    subgraph DIDs["DID Storage"]
        direction TB
        STATIC["Static DIDs<br/>VIN, part no., SW version<br/>→ Program Flash"]:::did
        DYN["Writable DIDs<br/>VIN write, config, coding<br/>→ Data Flash via NVM"]:::did
        LIVE["Live DIDs<br/>sensor values, status<br/>→ computed from RAM"]:::did
    end

    UDS19["UDS 0x19<br/>ReadDTCInformation"]:::uds --> FaultMem
    UDS14["UDS 0x14<br/>ClearDiagnosticInformation"]:::uds --> FaultMem
    UDS22["UDS 0x22<br/>ReadDataByIdentifier"]:::uds --> DIDs
    UDS2E["UDS 0x2E<br/>WriteDataByIdentifier"]:::uds --> DYN

    classDef dtc fill:#EF6C00,stroke:#BF360C,stroke-width:2px,color:#FFFFFF
    classDef did fill:#1565C0,stroke:#0D47A1,stroke-width:2px,color:#FFFFFF
    classDef uds fill:#37474F,stroke:#212121,stroke-width:2px,color:#FFFFFF

    style FaultMem fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#BF360C
    style DIDs     fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
```

## Lifecycle of a DTC: detection → storage → readout → clear

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'16px','fontFamily':'Arial','actorBkg':'#1565C0','actorTextColor':'#FFFFFF','actorLineColor':'#FFFFFF','actorBorder':'#FFFFFF','signalColor':'#FFFFFF','signalTextColor':'#FFFFFF','messageTextColor':'#FFFFFF','loopTextColor':'#FFFFFF','noteBkgColor':'#FFF59D','noteTextColor':'#212121','noteBorderColor':'#FFFFFF','sequenceNumberColor':'#212121','labelBoxBkgColor':'#1565C0','labelTextColor':'#FFFFFF'}}}%%
sequenceDiagram
    autonumber
    participant MON as Monitor / Diagnostic Function
    participant DEM as Event Manager (DEM)
    participant NVM as NVM Manager
    participant DF as Data Flash
    participant T as Tester (UDS)

    MON->>DEM: Report event "failed" (Event ID)
    DEM->>DEM: Debounce → set DTC status<br/>(testFailed, pending → confirmed)
    DEM->>DEM: Capture FreezeFrame (snapshot DIDs)<br/>increment counters
    DEM->>NVM: Mark fault-memory block dirty (RAM mirror)

    Note over NVM,DF: Deferred write (shutdown / threshold / periodic)
    NVM->>DF: Write block to inactive bank + CRC
    DF-->>NVM: Program OK
    NVM->>DF: Mark new bank "active", erase old bank later

    T->>DEM: 0x19 02  reportDTCByStatusMask
    DEM-->>T: 0x59 02  list of DTC + status bytes

    T->>DEM: 0x19 04  reportDTCSnapshotRecordByDTCNumber
    DEM-->>T: 0x59 04  freeze-frame DIDs

    T->>DEM: 0x14 FF FF FF  ClearDiagnosticInformation
    DEM->>DEM: Reset status / counters / snapshots in RAM
    DEM->>NVM: Mark block dirty
    NVM->>DF: Persist cleared block (A/B swap)
    DEM-->>T: 0x54
```

## Why this layered design

* **Endurance** — embedded Flash supports only ~10⁴–10⁵ erase cycles per
  sector. A RAM mirror + deferred write + wear-levelling keeps the cell count
  low.
* **Power-fail safety** — A/B (ping-pong) sectors with CRC ensure the previous
  valid copy survives if power is lost mid-write.
* **Determinism** — the application reads/writes RAM at runtime; Flash access
  (slow, blocking) happens only in the NVM manager.
* **Standard separation** — UDS services (`0x19`, `0x14`, `0x22`, `0x2E`) only
  see logical IDs; the physical layout in Flash is hidden behind the NVM/DEM
  layer (in AUTOSAR: NvM + Fee + Fls under Dem).



# UDS — Unified Diagnostic Services (ISO 14229)

UDS is a **request/response** protocol used by a diagnostic **Tester (Client)**
to talk to one or more **ECUs (Servers)** in a vehicle. Every request is a
single byte **Service Identifier (SID)**; the positive response is `SID + 0x40`,
a negative response is the fixed byte `0x7F` followed by the original SID and a
**Negative Response Code (NRC)**.

## Request / Response model

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'18px','fontFamily':'Arial','lineColor':'#FFFFFF','textColor':'#FFFFFF','arrowheadColor':'#FFFFFF'}}}%%
flowchart LR
    Tester([Tester / Client]):::client
    ECU([ECU / Server]):::server

    Tester -- "Request<br/>SID + sub-function + data" --> ECU
    ECU -- "Positive<br/>SID+0x40 + data" --> Tester
    ECU -- "Negative<br/>0x7F + SID + NRC" --> Tester

    classDef client fill:#1565C0,stroke:#0D47A1,stroke-width:3px,color:#FFFFFF
    classDef server fill:#EF6C00,stroke:#BF360C,stroke-width:3px,color:#FFFFFF
```

## Core service groups

Services are grouped by purpose. Each box shows the SID and the service name.

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'18px','fontFamily':'Arial','lineColor':'#FFFFFF','textColor':'#FFFFFF','arrowheadColor':'#FFFFFF'}}}%%
flowchart TB
    subgraph SESSION["Session &amp; Control"]
        direction LR
        S10["<b>0x10</b><br/>DiagnosticSessionControl"]:::session
        S11["<b>0x11</b><br/>ECUReset"]:::session
        S3E["<b>0x3E</b><br/>TesterPresent"]:::session
        S28["<b>0x28</b><br/>CommunicationControl"]:::session
    end

    subgraph SECURITY["Security"]
        direction LR
        S27["<b>0x27</b><br/>SecurityAccess"]:::security
        S29["<b>0x29</b><br/>Authentication"]:::security
    end

    subgraph DATA["Data Transmission (DIDs)"]
        direction LR
        S22["<b>0x22</b><br/>ReadDataByIdentifier"]:::data
        S2E["<b>0x2E</b><br/>WriteDataByIdentifier"]:::data
        S23["<b>0x23</b><br/>ReadMemoryByAddress"]:::data
        S3D["<b>0x3D</b><br/>WriteMemoryByAddress"]:::data
    end

    subgraph FAULT["Fault Memory (DTCs)"]
        direction LR
        S19["<b>0x19</b><br/>ReadDTCInformation"]:::fault
        S14["<b>0x14</b><br/>ClearDiagnosticInformation"]:::fault
    end

    subgraph ROUTINE["Routine &amp; Upload / Download"]
        direction LR
        S31["<b>0x31</b><br/>RoutineControl"]:::routine
        S34["<b>0x34</b><br/>RequestDownload"]:::routine
        S36["<b>0x36</b><br/>TransferData"]:::routine
        S37["<b>0x37</b><br/>RequestTransferExit"]:::routine
    end

    classDef session  fill:#1565C0,stroke:#0D47A1,stroke-width:2px,color:#FFFFFF
    classDef security fill:#C62828,stroke:#8E0000,stroke-width:2px,color:#FFFFFF
    classDef data     fill:#2E7D32,stroke:#1B5E20,stroke-width:2px,color:#FFFFFF
    classDef fault    fill:#EF6C00,stroke:#BF360C,stroke-width:2px,color:#FFFFFF
    classDef routine  fill:#6A1B9A,stroke:#4A148C,stroke-width:2px,color:#FFFFFF

    style SESSION  fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    style SECURITY fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#8E0000
    style DATA     fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    style FAULT    fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#BF360C
    style ROUTINE  fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C
```

## Typical session lifecycle

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'17px','fontFamily':'Arial','actorBkg':'#1565C0','actorTextColor':'#FFFFFF','actorLineColor':'#FFFFFF','actorBorder':'#FFFFFF','signalColor':'#FFFFFF','signalTextColor':'#FFFFFF','messageTextColor':'#FFFFFF','loopTextColor':'#FFFFFF','noteBkgColor':'#FFF59D','noteTextColor':'#212121','noteBorderColor':'#FFFFFF','sequenceNumberColor':'#212121','labelBoxBkgColor':'#1565C0','labelTextColor':'#FFFFFF'}}}%%
sequenceDiagram
    autonumber
    participant T as Tester
    participant E as ECU

    T->>E: 0x10 03  (switch to Extended Diagnostic Session)
    E-->>T: 0x50 03  (positive response, timing params)

    loop keep session alive
        T->>E: 0x3E 00  TesterPresent
        E-->>T: 0x7E 00
    end

    T->>E: 0x27 01  SecurityAccess — requestSeed
    E-->>T: 0x67 01 <seed>
    T->>E: 0x27 02 <key>  sendKey
    E-->>T: 0x67 02       (unlocked)

    T->>E: 0x22 F1 90    ReadDataByIdentifier (VIN)
    E-->>T: 0x62 F1 90 <VIN bytes>

    T->>E: 0x31 01 FF 00 RoutineControl — start
    E-->>T: 0x71 01 FF 00 <result>

    T->>E: 0x11 01  ECUReset (hardReset)
    E-->>T: 0x51 01
```

## Negative Response Codes (most common)

| NRC  | Name                                     |
|------|------------------------------------------|
| 0x10 | generalReject                            |
| 0x11 | serviceNotSupported                      |
| 0x12 | subFunctionNotSupported                  |
| 0x13 | incorrectMessageLengthOrInvalidFormat    |
| 0x22 | conditionsNotCorrect                     |
| 0x31 | requestOutOfRange                        |
| 0x33 | securityAccessDenied                     |
| 0x35 | invalidKey                               |
| 0x78 | requestCorrectlyReceived-ResponsePending |




# DoIP — Diagnostics over IP (ISO 13400)

DoIP is the **transport layer** that carries UDS messages over standard IP
networks (typically automotive Ethernet). It replaces ISO-TP / CAN for high-
bandwidth use cases such as ECU flashing, vehicle-wide diagnostics through a
central gateway, and remote / off-board diagnostics.

## Core concepts

* **Vehicle discovery** over UDP broadcast / multicast (port **13400**)
  – the tester learns which DoIP entities exist and their **Logical Address**.
* **Diagnostic communication** over a TCP connection (port **13400**)
  carrying length-prefixed DoIP messages with a UDS payload.
* **Routing Activation** authorizes the TCP socket and binds the tester’s
  **Source Address** to the connection before any UDS traffic flows.
* **Logical Addresses** identify the *Tester* (e.g. `0x0E00`) and the
  *target ECU / Gateway* (e.g. `0x1234`) — independent of IP addressing.
* A **DoIP Gateway** can route UDS messages from Ethernet onto an internal
  CAN bus to reach legacy ECUs (mixed topologies).

## Protocol stack

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'17px','fontFamily':'Arial','lineColor':'#FFFFFF','textColor':'#FFFFFF','arrowheadColor':'#FFFFFF'}}}%%
flowchart TB
    UDS["UDS application<br/>(ISO 14229-1)"]:::app
    DOIP["DoIP (ISO 13400-2)<br/>header • payload type • logical addresses"]:::doip
    L4["TCP : 13400 (diagnostic messages)<br/>UDP : 13400 (vehicle discovery)"]:::transport
    L3["IPv4 / IPv6"]:::net
    L2["Ethernet MAC"]:::link
    L1["100/1000BASE-T1"]:::phy

    UDS --> DOIP --> L4 --> L3 --> L2 --> L1

    classDef app       fill:#1565C0,stroke:#0D47A1,stroke-width:2px,color:#FFFFFF
    classDef doip      fill:#6A1B9A,stroke:#4A148C,stroke-width:2px,color:#FFFFFF
    classDef transport fill:#2E7D32,stroke:#1B5E20,stroke-width:2px,color:#FFFFFF
    classDef net       fill:#00838F,stroke:#005662,stroke-width:2px,color:#FFFFFF
    classDef link      fill:#EF6C00,stroke:#BF360C,stroke-width:2px,color:#FFFFFF
    classDef phy       fill:#37474F,stroke:#212121,stroke-width:2px,color:#FFFFFF
```

## End-to-end message flow

```mermaid
%%{init: {'theme':'base','themeVariables':{'fontSize':'16px','fontFamily':'Arial','actorBkg':'#1565C0','actorTextColor':'#FFFFFF','actorLineColor':'#FFFFFF','actorBorder':'#FFFFFF','signalColor':'#FFFFFF','signalTextColor':'#FFFFFF','messageTextColor':'#FFFFFF','loopTextColor':'#FFFFFF','noteBkgColor':'#FFF59D','noteTextColor':'#212121','noteBorderColor':'#FFFFFF','sequenceNumberColor':'#212121','labelBoxBkgColor':'#1565C0','labelTextColor':'#FFFFFF'}}}%%
sequenceDiagram
    autonumber
    participant T as Tester (Client)
    participant G as DoIP Gateway / ECU

    Note over T,G: 1) Discovery (UDP 13400, broadcast / multicast)
    T->>G: Vehicle Identification Request (0x0001)
    G-->>T: Vehicle Announcement / Identification Response (0x0004)<br/>VIN, Logical Address, EID, GID

    Note over T,G: 2) TCP connection (port 13400)
    T->>G: TCP SYN / SYN-ACK / ACK

    Note over T,G: 3) Routing Activation (mandatory before UDS)
    T->>G: Routing Activation Request (0x0005)<br/>SourceAddr=0x0E00, ActivationType=0x00
    G-->>T: Routing Activation Response (0x0006)<br/>Code=0x10 (success)

    Note over T,G: 4) Diagnostic message exchange
    T->>G: Diagnostic Message (0x8001)<br/>Src=0x0E00 Tgt=0x1234  UDS=22 F1 90
    G-->>T: Diagnostic Message ACK (0x8002)
    G-->>T: Diagnostic Message (0x8001)<br/>Src=0x1234 Tgt=0x0E00  UDS=62 F1 90 <VIN>

    Note over T,G: 5) Keep-alive / teardown
    loop while session needed
        T->>G: UDS 0x3E 00 TesterPresent (in DoIP message)
        G-->>T: UDS 0x7E 00
    end
    T->>G: TCP FIN
```

This is exactly the pattern visible in a Wireshark capture of a DoIP session:
*Vehicle announcement (UDP) → TCP handshake → Routing activation request /
response → Diagnostic message + ACK → reply → FIN*.



## Common DoIP payload types

| Type   | Direction      | Meaning                                |
|--------|----------------|----------------------------------------|
| 0x0000 | T ↔ G          | Generic DoIP header negative ACK       |
| 0x0001 | T → G (UDP)    | Vehicle Identification Request         |
| 0x0004 | G → T (UDP)    | Vehicle Announcement / Ident. Response |
| 0x0005 | T → G (TCP)    | Routing Activation Request             |
| 0x0006 | G → T (TCP)    | Routing Activation Response            |
| 0x0007 | T → G          | Alive Check Request                    |
| 0x0008 | G → T          | Alive Check Response                   |
| 0x8001 | T ↔ G          | Diagnostic Message (carries UDS)       |
| 0x8002 | G → T          | Diagnostic Message Positive ACK        |
| 0x8003 | G → T          | Diagnostic Message Negative ACK        |

## Why DoIP?

* **Bandwidth** — flashing a modern ECU over CAN is too slow; Ethernet/DoIP
  reaches hundreds of Mbit/s.
* **Topology** — a single Ethernet link to a central gateway can reach every
  ECU in the vehicle, including legacy CAN nodes via routing.
* **Off-board access** — works natively over standard IP networks, enabling
  remote, plant, and service-bay diagnostics without proprietary hardware.
* **Reuses UDS** — application-level diagnostic logic (DIDs, routines, DTCs,
  flashing) is unchanged; only the transport differs.



