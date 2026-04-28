#!/bin/bash
# Generate the OpenBSW ECU PDX file using Docker.
# Usage: ./generate_pdx.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build the generator image
docker build -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR" -t openbsw-odx-gen

# Run the generator, mounting the odx-gen dir and the CDA's ODX modules
docker run --rm \
    -v "$SCRIPT_DIR:/data" \
    -v "$SCRIPT_DIR/../classic-diagnostic-adapter/testcontainer/odx:/cda-odx:ro" \
    -u "$(id -u):$(id -g)" \
    -t openbsw-odx-gen

echo ""
echo "PDX file generated: $SCRIPT_DIR/OpenBSW.pdx"
echo ""
echo "To convert to MDD (requires odx-converter with ODX XSD schema):"
echo "  java -jar <path-to>/converter-all.jar $SCRIPT_DIR/OpenBSW.pdx"
