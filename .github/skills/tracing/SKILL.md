---
name: tracing
description: "Tracing skill for OpenBSW runtime trace analysis. Use when: trace_convert, bt_plugin_openbsw, Babeltrace2, BTF, trace file, thread switching, ISR tracing, RTOS tracing, OpenBSW trace, binary trace format, trace_convert.py, bt2 plugin, babeltrace plugin, CTF trace, timeline, thread_switched_in, thread_switched_out, isr_enter, isr_exit, real-time trace, event trace, CPU trace, cycle counter trace."
argument-hint: "python trace_convert.py <trace_file>  OR  babeltrace2 --plugin-path=tools/tracing --component=source.openbsw.OpenBSWSource --params='inputs=[\"<trace_file>\"]'"
---

# Tracing Skill

The tracing toolset converts and visualises **binary runtime traces** produced by firmware using the OpenBSW trace format — captured event logs recording thread switches and ISR activity with cycle-accurate timestamps.

> The trace format and plugin are tied to the **OpenBSW tracing infrastructure** (the same binary frame layout must be produced by the firmware). Any firmware implementing this format is supported.

Two components work together:

| File | Role |
|------|------|
| `trace_convert.py` | Standalone binary trace parser; readable directly or importable as a library |
| `bt_plugin_openbsw.py` | Babeltrace2 source plugin; feeds parsed events into the `bt2` pipeline for CTF/timeline output |

Tool source: `openbsw/tools/tracing/`

---

## When to Use

Load this skill whenever:
- Working with binary trace files in the **OpenBSW trace format** (any firmware using this format, not exclusively the referenceApp)
- Running `trace_convert.py` to inspect thread/ISR events
- Integrating with Babeltrace2 (`bt2`) for trace visualization
- Debugging RTOS thread scheduling or ISR timing
- Understanding the trace binary format or event encoding

---

## Architecture

```
tools/tracing/
├── trace_convert.py        ← Standalone parser: TraceParser + Event dataclass
└── bt_plugin_openbsw.py    ← Babeltrace2 source plugin: OpenBSWSource + OpenBSWSourceIter
```

**Data flow:**

```
ECU trace binary file
    → TraceParser.read()           (trace_convert.py)
        → list[Event]              (timestamp_ns, id, arg)
            → OpenBSWSourceIter    (bt_plugin_openbsw.py)
                → bt2 event messages
                    → babeltrace2 pipeline (CTF sink, pretty-print, etc.)
```

---

## Binary Trace Format

### File Header (4 bytes, little-endian)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | `cyclesPerSec` | CPU clock frequency in Hz (used to convert cycles → nanoseconds) |

### Event Frame (4 bytes each, little-endian, repeated)

Each 32-bit frame is decoded as:

```
Bit 31..24: ctrl byte
    bit 7:    ext        (extension flag, reserved)
    bits 6-4: id         (event type, 0–4)
    bits 3-0: rel_cycles_high  (upper 4 bits of relative cycle delta)
Bit 23..16: arg          (event argument / thread or ISR ID, 0–255)
Bit 15..0:  rel_cycles_low    (lower 16 bits of relative cycle delta)
```

**Relative cycle delta** = `(rel_cycles_high << 16) | rel_cycles_low`

Timestamps are accumulated from relative cycle deltas and converted to nanoseconds:
```
timestamp_ns = accumulated_cycles * (1_000_000_000 / cyclesPerSec)
```

### Event Types

| ID | Name | `arg` Meaning |
|----|------|---------------|
| `0` | `thread_switched_out` | Thread ID |
| `1` | `thread_switched_in` | Thread ID |
| `2` | `isr_enter` | ISR ID |
| `3` | `isr_exit` | ISR ID |
| `4` | `user` | User-defined payload |

---

## `trace_convert.py` — Standalone Parser

### `Event` Dataclass

```python
@dataclass
class Event:
    timestamp: int   # nanoseconds (absolute)
    id: int          # 0–4 (event type)
    arg: int         # 0–255 (thread/ISR ID or user arg)
```

Constraints (validated in `__post_init__`): `id` in `0–7`, `arg` in `0–255`.

### `TraceParser`

```python
parser = TraceParser("path/to/trace.bin")
events = parser.read()   # returns list[Event]
```

### Standalone CLI

```bash
python tools/tracing/trace_convert.py <trace_file>
```

Prints each event in human-readable form:
```
[00:00:00.000001234] thread_switched_out (id=1, arg=2)   (+0.000001234)
[00:00:00.000002500] thread_switched_in  (id=1, arg=3)   (+0.000001266)
...
```

---

## `bt_plugin_openbsw.py` — Babeltrace2 Plugin

### Prerequisites

```bash
pip install babeltrace2   # Python bt2 bindings
# OR install via system package manager:
sudo apt install python3-bt2
```

### Plugin Registration

The file registers itself as a Babeltrace2 plugin named `openbsw`:
```python
bt2.register_plugin(__name__, "openbsw")
```

Component class: `OpenBSWSource` (source component with one output port `"out"`)

### Event Classes Created

| Event class ID | Name | Payload field |
|---|---|---|
| 0 | `thread_switched_out` | `id: uint` |
| 1 | `thread_switched_in` | `id: uint` |
| 2 | `isr_enter` | `id: uint` |
| 3 | `isr_exit` | `id: uint` |
| 4 | `user` | `id: uint` |

### Running with Babeltrace2

```bash
# Pretty-print all events
babeltrace2 \
  --plugin-path=tools/tracing \
  --component=source.openbsw.OpenBSWSource \
  --params='inputs=["path/to/trace.bin"]' \
  --component=sink.text.pretty

# Convert to CTF (Common Trace Format) for use with TraceCompass / lttng-analyses
babeltrace2 \
  --plugin-path=tools/tracing \
  --component=source.openbsw.OpenBSWSource \
  --params='inputs=["path/to/trace.bin"]' \
  --component=sink.ctf.fs \
  --params='path="output_ctf/"'
```

### Parameter Requirements

| Parameter | Type | Required | Description |
|---|---|---|---|
| `inputs` | list of strings | Yes | Must be a list with exactly **one** trace file path |

Passing zero or more than one element raises `ValueError`. Passing a non-string element raises `TypeError`.

---

## Common Pitfalls & Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ImportError: No module named 'bt2'` | Babeltrace2 Python bindings not installed | `sudo apt install python3-bt2` or `pip install babeltrace2` |
| `Error: unexpected end of file while reading first cyclesPerSec bytes` | Trace file is empty or truncated | Verify the trace file was fully captured from the ECU |
| All timestamps are `0` | `cyclesPerSec` read as 0 | ECU firmware did not write the header correctly; check trace capture |
| `OpenBSWSource: missing 'inputs' parameter` | `--params` not provided to babeltrace2 | Add `--params='inputs=["<file>"]'` to the command |
| Events show `id=unknown` | Event ID outside 0–4 range | Trace may be from a newer firmware with additional event types |
| `ValueError: id must be in range 0–7` | Corrupt frame in trace file | Trace file may be corrupted; verify binary capture integrity |

---

## Quick Reference

```bash
# Standalone: parse and pretty-print a trace file
python tools/tracing/trace_convert.py path/to/trace.bin

# Babeltrace2: pretty-print via plugin
babeltrace2 \
  --plugin-path=tools/tracing \
  --component=source.openbsw.OpenBSWSource \
  --params='inputs=["path/to/trace.bin"]' \
  --component=sink.text.pretty

# Babeltrace2: convert to CTF for TraceCompass
babeltrace2 \
  --plugin-path=tools/tracing \
  --component=source.openbsw.OpenBSWSource \
  --params='inputs=["path/to/trace.bin"]' \
  --component=sink.ctf.fs \
  --params='path="output_ctf/"'
```
