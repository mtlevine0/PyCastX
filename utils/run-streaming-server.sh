#!/bin/bash
# Unified streaming server - automatically uses codec or raw mode based on config

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/streaming.json"

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Read mode from config
MODE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['mode'])")

echo "==================================="
echo "  PyCastX Streaming Server"
echo "==================================="
echo ""

case "$MODE" in
    "codec")
        echo "Mode: CODEC (H.264 compressed)"
        echo "Running: run-socket-server.sh"
        echo ""
        exec "$SCRIPT_DIR/run-socket-server.sh"
        ;;
    "raw")
        echo "Mode: RAW (uncompressed UDP)"
        echo "Running: server.py with UDP"
        echo ""
        exec python3 "$SCRIPT_DIR/server.py"
        ;;
    *)
        echo "ERROR: Invalid mode '$MODE' in config"
        echo "Valid modes: 'codec', 'raw'"
        exit 1
        ;;
esac
