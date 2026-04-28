#!/usr/bin/env python3
"""
Generate an MDD file for the OpenBSW ECU.

This script:
1. Compiles openbsw_ecu.json → FlatBuffers binary using flatc
2. Wraps the binary in a protobuf MDDFile container
3. Writes the result with the MDD magic bytes header

Prerequisites:
  pip install protobuf flatbuffers
  apt install flatbuffers-compiler protobuf-compiler
  # Or download flatc v25+ from https://github.com/google/flatbuffers/releases

Usage:
  python generate_mdd.py
  # Produces: OpenBSW.mdd
"""

import os
import struct
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CDA_DIR = os.path.join(SCRIPT_DIR, "..", "classic-diagnostic-adapter")
FBS_SCHEMA = os.path.join(
    CDA_DIR, "cda-database", "src", "flatbuf", "diagnostic_description.fbs"
)
JSON_FILE = os.path.join(SCRIPT_DIR, "openbsw_ecu.json")
PROTO_DIR = os.path.join(SCRIPT_DIR, "generated")
BIN_FILE = os.path.join(SCRIPT_DIR, "openbsw_ecu.bin")
OUTPUT_MDD = os.path.join(SCRIPT_DIR, "OpenBSW.mdd")

# MDD magic bytes: "MDD version 0" padded to 20 bytes with spaces + null terminator
MDD_MAGIC = b"MDD version 0      \x00"
assert len(MDD_MAGIC) == 20

ECU_NAME = "OpenBSW"


def step_compile_flatbuffers():
    """Compile openbsw_ecu.json → openbsw_ecu.bin using flatc."""
    print("Step 1: Compiling FlatBuffers JSON → binary...")
    cmd = ["flatc", "--binary", FBS_SCHEMA, JSON_FILE]
    result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: flatc failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(BIN_FILE):
        print("Error: openbsw_ecu.bin not generated", file=sys.stderr)
        sys.exit(1)
    size = os.path.getsize(BIN_FILE)
    print(f"  Generated: openbsw_ecu.bin ({size} bytes)")


def step_compile_protobuf():
    """Compile file_format.proto → Python if not already done."""
    pb2_file = os.path.join(PROTO_DIR, "file_format_pb2.py")
    if os.path.exists(pb2_file):
        return

    print("Step 1b: Compiling protobuf schema → Python...")
    os.makedirs(PROTO_DIR, exist_ok=True)
    proto_file = os.path.join(CDA_DIR, "cda-database", "proto", "file_format.proto")
    cmd = [
        "protoc",
        f"--proto_path={os.path.dirname(proto_file)}",
        f"--python_out={PROTO_DIR}",
        proto_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: protoc failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"  Generated: {pb2_file}")


def step_create_mdd():
    """Wrap the FlatBuffers binary in a protobuf MDDFile and write MDD."""
    print("Step 2: Creating MDD file...")

    # Add generated dir to path for the protobuf module
    sys.path.insert(0, PROTO_DIR)
    import file_format_pb2

    # Read the FlatBuffers binary
    with open(BIN_FILE, "rb") as f:
        flatbuf_data = f.read()

    # Create the protobuf MDDFile
    mdd = file_format_pb2.MDDFile()
    mdd.version = "1"
    mdd.ecu_name = ECU_NAME

    # Add a DIAGNOSTIC_DESCRIPTION chunk containing the FlatBuffers payload
    chunk = mdd.chunks.add()
    chunk.type = file_format_pb2.Chunk.DIAGNOSTIC_DESCRIPTION
    chunk.name = f"{ECU_NAME}.fbs"
    chunk.data = flatbuf_data

    # Serialize the protobuf
    proto_data = mdd.SerializeToString()

    # Write MDD file: magic + protobuf
    with open(OUTPUT_MDD, "wb") as f:
        f.write(MDD_MAGIC)
        f.write(proto_data)

    total_size = len(MDD_MAGIC) + len(proto_data)
    print(f"  Generated: {OUTPUT_MDD} ({total_size} bytes)")
    print(f"  FlatBuffers payload: {len(flatbuf_data)} bytes")
    print(f"  Protobuf wrapper: {len(proto_data)} bytes")


def main():
    print(f"Generating MDD file for {ECU_NAME}...", flush=True)
    print(flush=True)

    step_compile_protobuf()
    step_compile_flatbuffers()
    step_create_mdd()

    print(flush=True)
    print(f"Done! MDD file: {OUTPUT_MDD}", flush=True)
    print(f"Copy this file to the CDA's database directory.", flush=True)


if __name__ == "__main__":
    main()
