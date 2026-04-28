---
name: safety-crc
description: "Safety CRC skill for OpenBSW ELF CRC validation and injection. Use when: CRC check, crcCheck.py, CRC32, ELF CRC, flash CRC, safety check, __checksum_result, inject CRC, ELF to HEX, objcopy, pyelftools, FLASH_START, ROM_CRC_END, CRC_IVT, CRC_APP, S32K148 CRC, firmware integrity, safety validation, post-build CRC, IVT CRC, application CRC, VMA CRC."
argument-hint: "cd tools/safety && python crcCheck.py"
---

# Safety CRC Skill

`crcCheck.py` is a post-build safety tool that computes a **CRC32 checksum** over defined flash regions of a compiled S32K148 ELF binary and **injects the result** back into the ELF at the `__checksum_result` symbol address. This checksum is verified at runtime by the firmware's safety monitor.

Tool source: `openbsw/tools/safety/`

---

## When to Use

Load this skill whenever:
- Running or understanding the post-build CRC injection step
- Debugging CRC mismatches at runtime on S32K148
- Working with `crcCheck.py`, `pyelftools`, or ELF symbol extraction
- Configuring flash region boundaries for CRC computation
- Understanding `FLASH_START`, `__CRC_IVT_END`, `__CRC_APP_START`, and related linker symbols

---

## Architecture

```
tools/safety/
├── crcCheck.py       ← Main script: ELF→HEX, parse regions, CRC32, inject into ELF
└── requirements.txt  ← pyelftools==0.32 (Python >=3.10)
```

**Pipeline:**

```
app.referenceApp.elf
    ↓ objcopy -O ihex
output.hex  (Intel HEX format)
    ↓ parse_hex_file() × 3 regions
raw byte arrays
    ↓ convert_to_little_endian()
little-endian bytes
    ↓ calculate_crc()            (CRC32, seed 0xFFFFFFFF)
crc_value (4 bytes)
    ↓ inject_crc()               (write into ELF at __checksum_result)
app.referenceApp.elf  (patched in-place)
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | `>=3.10` | Required by `requirements.txt` |
| `pyelftools` | `0.32` | ELF parsing library |
| `objcopy` | any | Must be on PATH; for S32K148 use `arm-none-eabi-objcopy` |

```bash
pip install -r tools/safety/requirements.txt
```

---

## ELF Input Path

The script looks for the ELF using a **glob pattern** relative to the `tools/safety/` working directory.

### OpenBSW referenceApp (default)

```python
elf_pattern = "../../cmake-build-s32k148*/application/app.referenceApp.elf"
```

This resolves (from repo root) to:
```
cmake-build-s32k148*/application/app.referenceApp.elf
```

### ELF Selection Priority (when multiple matches)

1. `cmake-build-s32k148/` (no `-gcc` or `-clang` suffix)
2. Any path containing `gcc`
3. Any path containing `clang`
4. First match in glob result

A warning is printed when multiple ELF files are found.

### Adapting for Your Project

The glob pattern and symbol names are the two things to change. Edit the `__main__` block of `crcCheck.py`:

```python
if __name__ == "__main__":
    # ← Update this glob to point to your ELF
    elf_pattern = "../../<your-build-dir>/your_app.elf"
    hex_file_path = "output.hex"

    # ← Update this to your CRC result symbol name
    symbol_name = "__checksum_result"

    elf_file_path = select_elf_file(elf_pattern)
    ...
    # ← Replace these with your linker script's equivalent symbols
    flash_start          = extract_symbol_address(elf_file, "FLASH_START")
    ivt_end              = extract_symbol_address(elf_file, "__CRC_IVT_END")
    application_start    = extract_symbol_address(elf_file, "__CRC_APP_START")
    rom_crc_end          = extract_symbol_address(elf_file, "__ROM_CRC_END")
    data_rom_start       = extract_symbol_address(elf_file, "__DATA_ROM_START")
    used_flash_end       = extract_symbol_address(elf_file, "__USED_FLASH_END")
```

Your linker script needs to export equivalent symbols defining the flash regions to protect and the CRC result storage address.

---

## Running the Tool

```bash
# From the tools/safety/ directory
cd tools/safety
python crcCheck.py
```

The script modifies the ELF file **in-place**. Run it after every build before flashing.

---

## Flash Regions Covered

The CRC is computed over **three concatenated regions**, extracted from the ELF's linker symbols:

| Region | Start Symbol | End Symbol | Description |
|--------|-------------|------------|-------------|
| IVT | `FLASH_START` | `__CRC_IVT_END` | Interrupt Vector Table |
| Application | `__CRC_APP_START` | `__ROM_CRC_END` | Main application code |
| VMA ROM | `__DATA_ROM_START` | `__USED_FLASH_END` | Initialised data in flash (ROM copy) |

These regions are parsed from the Intel HEX file, concatenated in order, then converted to little-endian 32-bit words before the CRC is computed.

---

## CRC Algorithm

| Parameter | Value |
|---|---|
| Algorithm | CRC-32 (`binascii.crc32`) |
| Seed | `0xFFFFFFFF` |
| Endianness | Input data converted to **little-endian** (4-byte word swap) before hashing |
| Result width | 32-bit unsigned |
| Injection target | `__checksum_result` symbol in ELF, written as 4-byte little-endian |

```python
# Exact implementation
crc = binascii.crc32(bytearray(data_little_endian)) & 0xFFFFFFFF
```

---

## Key Functions Reference

| Function | Signature | Description |
|----------|-----------|-------------|
| `select_elf_file` | `(pattern) → str` | Glob-select ELF with priority (cmake-build > gcc > clang) |
| `convert_elf_to_hex` | `(elf_path, hex_path)` | Calls `objcopy -O ihex` |
| `parse_hex_file` | `(hex_path, start_addr, end_addr) → list[int]` | Extracts bytes from Intel HEX within address range; handles type-02 and type-04 address extension records |
| `convert_to_little_endian` | `(data) → list[int]` | Reverses each 4-byte word in the byte array |
| `calculate_crc` | `(data) → int` | CRC32 with seed `0xFFFFFFFF` via `binascii.crc32` |
| `extract_symbol_address` | `(elf_file, symbol_name) → int` | Reads `st_value` from ELF symbol table via `pyelftools` |
| `inject_crc` | `(file_path, symbol_name, crc_value)` | Seeks to symbol's file offset in ELF and writes 4-byte little-endian CRC |

---

## Linker Symbols Required in ELF

The following symbols are read from the ELF symbol table. The names below are those used by the **OpenBSW referenceApp linker script** — your project must export equivalent symbols (names can differ; update `crcCheck.py` accordingly):

| Symbol (referenceApp) | Purpose |
|--------|------|
| `FLASH_START` | Base address of flash (IVT region start) |
| `__CRC_IVT_END` | End of IVT CRC region |
| `__CRC_APP_START` | Start of application CRC region |
| `__ROM_CRC_END` | End of application CRC region |
| `__DATA_ROM_START` | ROM copy of initialised data (VMA region start) |
| `__USED_FLASH_END` | End of used flash / VMA region end |
| `__checksum_result` | Location where computed CRC is written |

If any symbol is missing, the tool raises: `Exception: Symbol '<name>' not found in ELF file`

> For non-referenceApp projects: the CRC regions and the injection target symbol must be defined in your linker script. The minimum requirement is one contiguous region start/end pair and one 4-byte-aligned result storage symbol.

---

## Intel HEX Record Handling

`parse_hex_file()` correctly handles:

| Record Type | Hex Code | Action |
|-------------|----------|--------|
| Data | `00` | Extracts bytes within `[start_address, end_address)` |
| Extended Segment Address | `02` | Sets `address_offset = segment × 16` |
| Extended Linear Address | `04` | Sets `address_offset = upper_16_bits << 16` |
| Other | any | Silently skipped |

---

## Common Pitfalls & Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `No ELF files found matching pattern` | ELF not built or wrong working directory | Run from `tools/safety/`; build S32K148 target first |
| `Symbol 'FLASH_START' not found in ELF file` | Linker script missing symbol export | Verify linker script exports all required symbols |
| `Symbol table not found in ELF file` | ELF stripped of symbols | Use debug or release build with symbol table retained (not `--strip-all`) |
| `objcopy: command not found` | ARM toolchain not on PATH | Add `arm-gnu-toolchain.../bin/` to PATH |
| CRC mismatch at runtime | Tool not run after last build | Always run `crcCheck.py` as a post-build step after recompiling |
| `Warning: Multiple ELF files found` | Multiple cmake-build-s32k148 directories exist | Clean stale build dirs; the tool will pick the preferred one automatically |
| Wrong CRC injected | Byte order confusion | Input must be little-endian words; `convert_to_little_endian()` handles this — do not pre-convert |

---

## Integration as Post-Build Step

To automate CRC injection after every build, add to your CMake `add_custom_command`:

```cmake
# Replace <your_target> with your actual CMake target name
add_custom_command(
    TARGET <your_target> POST_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tools/safety/crcCheck.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/tools/safety
    COMMENT "Injecting CRC32 into ELF"
)
```

For the OpenBSW referenceApp the target is `app.referenceApp`.

---

## Quick Reference

```bash
# Install dependencies
pip install -r tools/safety/requirements.txt

# --- OpenBSW referenceApp ---
cmake --preset s32k148-gcc
cmake --build --preset s32k148-gcc

# --- Other projects ---
# Edit crcCheck.py __main__ block:
#   elf_pattern  ← glob to your ELF file
#   symbol_name  ← your CRC result symbol
#   extract_symbol_address calls ← your linker script symbols

# Run CRC injection (from tools/safety/)
cd tools/safety
python crcCheck.py

# Verify the CRC symbol was patched (use arm-none-eabi-nm or nm for your target)
arm-none-eabi-nm ../../cmake-build-s32k148*/application/app.referenceApp.elf | grep __checksum_result
```
