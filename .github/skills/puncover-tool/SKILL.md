---
name: puncover-tool
description: "Puncover tool skill for OpenBSW binary analysis. Use when: analyzing code size, stack usage, static memory, ELF binary analysis, puncover, puncover_tool, generate_html, HTML report, RAM usage, FLASH usage, binary size report, call-stack analysis, disassembly, Poetry, generate_html.py, run.py, referenceApp ELF, S32K148 binary analysis, memory footprint, symbol size."
argument-hint: "cd tools/puncover_tool && python run.py  OR  poetry run puncover_tool"
---

# Puncover Tool Skill

**puncover_tool** wraps the [Puncover](https://github.com/HBehrens/puncover) library to analyze compiled C/C++ ELF binaries and produce interactive HTML reports covering:

- Code size per symbol / file / folder
- Static RAM usage
- Stack depth requirements
- Disassembly with linked symbols
- Call-graph analysis

Tool source: `openbsw/tools/puncover_tool/`

---

## When to Use

Load this skill whenever:
- Inspecting binary/memory footprint of **any C/C++ ARM embedded build** (including OpenBSW referenceApp)
- Investigating code size regressions
- Understanding stack depth or RAM allocation per module
- Running `puncover_tool`, `generate_html.py`, or `run.py`
- Setting up or troubleshooting the Poetry environment for this tool
- Adapting the tool for a non-referenceApp project

---

## Architecture

```
tools/puncover_tool/
├── run.py                          ← Bootstrap: runs poetry install + poetry add puncover + tool
├── pyproject.toml                  ← Poetry project; entry point: puncover_tool → generate_html:main
├── src/puncover_tool/
│   ├── __init__.py
│   └── generate_html.py            ← Core: builds ElfBuilder → HTMLRenderer → Jinja2 HTML output
├── templates/                      ← Jinja2 HTML templates (overview, symbol, file, folder, rack…)
├── output/                         ← Generated HTML report written here (created on first run)
└── doc/index.rst                   ← Sphinx documentation
```

**Dependency chain:**
```
run.py / poetry run puncover_tool
    → generate_html.py
        → puncover.ElfBuilder      (parses ELF: symbols, sizes, call graph)
        → puncover.collector       (aggregates data)
        → LocalHTMLRenderer        (Jinja2 → output/*.html)
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | `>=3.10` | Required by `pyproject.toml` |
| Poetry | any recent | `pip install poetry` |
| ARM GCC toolchain | — | Must be on `PATH` (`arm-none-eabi-gcc`, `arm-none-eabi-nm`, `arm-none-eabi-objdump`) |
| Built ELF | — | See **Input ELF** section below |

---

## Installation

```bash
# Install Poetry if not already available
pip install poetry
```

No further manual setup — `run.py` handles `poetry install` and `poetry add puncover` automatically.

---

## Input ELF

### OpenBSW referenceApp (default)

The tool's `generate_html.py` has three paths **hardcoded** inside the `generate_html_output()` function that target the OpenBSW referenceApp build:

```python
# src/puncover_tool/generate_html.py — generate_html_output()
src_root  = os.path.abspath("../source")                    # relative to tools/puncover_tool/
build_dir = os.path.abspath("../../build/s32k148-freertos-gcc")  # relative to tools/puncover_tool/
elf_file  = os.path.join(build_dir,
    "executables/referenceApp/application/RelWithDebInfo/app.referenceApp.elf")
```

Build the referenceApp first (from repo root):
```bash
cmake --preset s32k148-freertos-gcc
cmake --build --preset s32k148-freertos-gcc-RelWithDebInfo
```

> **`RelWithDebInfo` is required** — it retains `-g` debug symbols that Puncover needs for symbol/call-graph resolution. `Release` builds will produce empty or incomplete reports.

### ARM Toolchain Path

`get_arm_tools_prefix_path()` looks for the ARM toolchain at a **hardcoded path**:
```python
/opt/arm-gnu-toolchain/bin/arm-none-eabi-objdump
```
If the toolchain is not at that path, `main()` exits with code 1. See **Adapting for Your Project** below to change this.

---

## Adapting for Your Project

To use the tool with a **different ELF** (non-referenceApp), edit `src/puncover_tool/generate_html.py` directly:

```python
def generate_html_output(gcc_tools_base):
    # ← Change these three lines for your project:
    src_root  = os.path.abspath("/path/to/your/source/root") + os.sep
    build_dir = os.path.abspath("/path/to/your/build/dir")   + os.sep
    elf_file  = os.path.join(build_dir, "your_app.elf")
```

And if the ARM toolchain is not at `/opt/arm-gnu-toolchain/`, update `get_arm_tools_prefix_path()`:

```python
def get_arm_tools_prefix_path():
    obj_dump = shutil.which("/your/toolchain/path/arm-none-eabi-objdump")
    ...
```

Or set the toolchain on your `PATH` and call `shutil.which("arm-none-eabi-objdump")` without an absolute path.

---

## Running the Tool

### Option 1 — `run.py` (recommended, handles all setup)

```bash
cd tools/puncover_tool
python run.py
```

This script:
1. Runs `poetry install` (installs declared dependencies)
2. Runs `poetry add puncover` (adds puncover to the environment)
3. Executes `poetry run puncover_tool` (runs `generate_html:main`)

### Option 2 — Direct Poetry invocation (dependencies already installed)

```bash
cd tools/puncover_tool
poetry run puncover_tool
```

### Output

```
tools/puncover_tool/output/index.html
```

Open in any browser:
```bash
xdg-open tools/puncover_tool/output/index.html   # Linux
open tools/puncover_tool/output/index.html        # macOS
```

---

## HTML Report Structure

The generated report contains the following pages (navigable from `index.html`):

| Page | Template | Content |
|------|----------|---------|
| Overview | `overview.html.jinja` | Top-level summary: total size, RAM, stack |
| All Symbols | `all_symbols.html.jinja` | Sortable flat list of every symbol with sizes |
| File | `file.html.jinja` | Per-source-file breakdown |
| Folder | `folder.html.jinja` | Per-directory rollup |
| Symbol | `symbol.html.jinja` | Individual symbol detail: disassembly, callers, callees |
| Rack | `rack.html.jinja` | Visual stack allocation diagram |

---

## Key Implementation Details

### `generate_html.py` — `LocalHTMLRenderer`

Extends `puncover.renderers.HTMLRenderer` to:
- Use local `./templates/` directory (Jinja2 `FileSystemLoader`) instead of puncover's bundled templates
- Add cross-linked assembly output: symbol names in disassembly become HTML hyperlinks
- Inject `now` (current datetime) into all template contexts
- Sanitise file paths: removes `<` / `>` characters before writing output files
- Build `symbols_by_address` lookup dict for fast address → symbol resolution

### ELF Builder

```python
from puncover.builders import ElfBuilder
from puncover.gcc_tools import GCCTools
```

`ElfBuilder` drives `arm-none-eabi-nm`, `arm-none-eabi-objdump`, and `arm-none-eabi-size` to extract symbol metadata and disassembly from the ELF binary.

---

## Common Pitfalls & Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `poetry: command not found` | Poetry not installed | `pip install poetry` |
| `FileNotFoundError` / ELF not found | ELF not built, or wrong path in `generate_html.py` | For referenceApp: build with `cmake --build --preset s32k148-freertos-gcc-RelWithDebInfo`. For other projects: update the paths in `generate_html_output()` |
| Script exits with code 1 silently | `get_arm_tools_prefix_path()` returned `None` | ARM toolchain not found at `/opt/arm-gnu-toolchain/bin/`; update the path in `generate_html.py` or install toolchain there |
| No symbol sizes / blank overview | ELF built without debug info | Use `RelWithDebInfo` build type, not `Release` |
| `arm-none-eabi-nm: command not found` | ARM toolchain not on PATH | Add ARM GCC `bin/` to `PATH` |
| `output/` directory missing | First run | Created automatically by `generate_html.py` |
| Template rendering error | Jinja2 template issue | Check `tools/puncover_tool/templates/` — templates must be present |
| Poetry env conflict | Stale venv | `cd tools/puncover_tool && poetry env remove python && python run.py` |

---

## Quick Reference

```bash
# One-time: install Poetry
pip install poetry

# --- OpenBSW referenceApp ---
# Build the ELF first (from repo root) — RelWithDebInfo required for debug symbols
cmake --preset s32k148-freertos-gcc
cmake --build --preset s32k148-freertos-gcc-RelWithDebInfo

# --- Other projects ---
# Edit src/puncover_tool/generate_html.py: update src_root, build_dir, elf_file
# Edit get_arm_tools_prefix_path() if toolchain is not at /opt/arm-gnu-toolchain/

# Run analysis (works for any project after paths are set)
cd tools/puncover_tool
python run.py

# View report
xdg-open output/index.html
```
