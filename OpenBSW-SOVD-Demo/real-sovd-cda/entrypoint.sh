#!/bin/sh -e
# Entrypoint for the OpenBSW SOVD CDA container.
# Auto-detects the container's IP for DoIP tester address unless
# DOIP_TESTER_IP env var is already set.

if [ -z "$DOIP_TESTER_IP" ]; then
    DOIP_TESTER_IP=$(ip -4 a show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
fi

echo "OpenBSW SOVD CDA starting..."
echo "  DoIP Tester IP: $DOIP_TESTER_IP"
echo "  Database path:  /app/odx"
echo "  Config file:    ${CDA_CONFIG_FILE:-/app/opensovd-cda.toml}"
echo "  Arguments:      $@"

ls /app/odx/*.mdd 2>/dev/null && echo "  MDD files found" || echo "  WARNING: No MDD files in /app/odx/"

exec /app/opensovd-cda --tester-address "$DOIP_TESTER_IP" -d /app/odx "$@"
