#!/bin/bash
# Socket-based streaming: Python handles network, FFmpeg handles codec
# More reliable than FFmpeg's built-in TCP streaming

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../../config/streaming.json"

# Load configuration from JSON
if [ -f "$CONFIG_FILE" ]; then
    SERVER_IP=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['network']['server_ip'])")
    SERVER_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['network']['server_port'])")
    WIDTH=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['video']['width'])")
    HEIGHT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['video']['height'])")
    FPS=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['video']['fps'])")
    BITRATE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['encoding']['bitrate'])")
    GOP_SIZE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['encoding']['gop_size'])")
    PRESET=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['encoding']['preset'])")
    LOW_LATENCY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['encoding'].get('low_latency', False))")
else
    echo "ERROR: Config file not found at $CONFIG_FILE"
    exit 1
fi

echo "Starting socket-based streaming client..."
echo "  Server: $SERVER_IP:$SERVER_PORT"
echo "  Video: ${WIDTH}x${HEIGHT} @ ${FPS} FPS"
echo "  Encoding: ${BITRATE}, GOP=${GOP_SIZE}, preset=${PRESET}"
echo "  Low latency: ${LOW_LATENCY}"
echo "  Using Python socket for network transfer"
echo ""

source "$SCRIPT_DIR/.venv/bin/activate"

# Build FFmpeg command with low latency options if enabled
FFMPEG_OPTS=""
if [ "$LOW_LATENCY" = "True" ]; then
    # Low latency: minimal buffering, frame dropping allowed
    FFMPEG_OPTS="-fflags nobuffer -flags low_delay -max_delay 0"
    BUFSIZE="100k"
else
    # Normal: standard buffering
    BUFSIZE="1M"
fi

# Python app → FFmpeg encode → Python socket sender
python -u "$SCRIPT_DIR/main.py" | \
ffmpeg \
    -f rawvideo \
    -pix_fmt rgb24 \
    -s ${WIDTH}x${HEIGHT} \
    -framerate ${FPS} \
    $FFMPEG_OPTS \
    -i - \
    -c:v libx264 \
    -preset ${PRESET} \
    -tune zerolatency \
    -pix_fmt yuv420p \
    -g ${GOP_SIZE} \
    -b:v ${BITRATE} \
    -bufsize ${BUFSIZE} \
    -x264-params "bframes=0:scenecut=0:ref=1" \
    -f h264 \
    - \
    -loglevel error 2>&1 | \
python3 -u "$SCRIPT_DIR/../../utils/socket_sender.py" $SERVER_IP $SERVER_PORT
