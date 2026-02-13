#!/bin/bash
# Unified streaming script - automatically uses codec or raw mode based on config

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../../config/streaming.json"

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Read mode from config
MODE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['mode'])")

echo "==================================="
echo "  PyCastX Streaming Client"
echo "==================================="
echo ""

case "$MODE" in
    "codec")
        echo "Mode: CODEC (H.264 compressed)"
        echo "Running: run-socket-client.sh"
        echo ""
        exec "$SCRIPT_DIR/run-socket-client.sh"
        ;;
    "raw")
        echo "Mode: RAW (uncompressed UDP)"
        echo "Running: main.py with UDP client"
        echo ""

        # Load config
        SERVER_IP=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['network']['server_ip'])")

        # Activate venv and run with UDP client
        source "$SCRIPT_DIR/.venv/bin/activate"
        python -u "$SCRIPT_DIR/main.py" | python "$SCRIPT_DIR/../../utils/client.py" $SERVER_IP
        ;;
    *)
        echo "ERROR: Invalid mode '$MODE' in config"
        echo "Valid modes: 'codec', 'raw'"
        exit 1
        ;;
esac
