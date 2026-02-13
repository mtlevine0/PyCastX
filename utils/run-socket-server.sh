#!/bin/bash
# Socket-based streaming: Python handles network, FFmpeg handles codec
# More reliable than FFmpeg's built-in TCP streaming

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/streaming.json"

# Load configuration from JSON
if [ -f "$CONFIG_FILE" ]; then
    LISTEN_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['network']['server_port'])")
    FPS=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['video']['fps'])")
    LOW_LATENCY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['encoding'].get('low_latency', False))")
else
    echo "ERROR: Config file not found at $CONFIG_FILE"
    exit 1
fi

echo "Starting socket-based streaming server..."
echo "  Listening on port: $LISTEN_PORT"
echo "  Expected FPS: $FPS"
echo "  Low latency: $LOW_LATENCY"
echo "  Using Python socket for network receive"
echo ""

# Detect hardware decoder
DECODER="h264"
if ffmpeg -decoders 2>/dev/null | grep -q "h264_mmal"; then
    DECODER="h264_mmal"
    echo "  Using hardware decoder: h264_mmal (Raspberry Pi)"
elif ffmpeg -decoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
    DECODER="h264_v4l2m2m"
    echo "  Using hardware decoder: h264_v4l2m2m"
else
    echo "  Using software decoder: h264 (CPU-based)"
fi
echo ""

# Python socket receiver → FFmpeg decode → Python display
# Note: Don't specify codec for decoding - FFmpeg auto-decodes the input
# -c:v is for encoding, not decoding!

# Build FFmpeg command with low latency options if enabled
FFMPEG_DECODE_OPTS=""
if [ "$LOW_LATENCY" = "True" ]; then
    # Low latency: minimal buffering, sync options for real-time
    # Note: -framedrop not available in FFmpeg 4.3, using sync instead
    FFMPEG_DECODE_OPTS="-fflags nobuffer -flags low_delay -avioflags direct"
fi

python3 -u "$SCRIPT_DIR/socket_receiver.py" $LISTEN_PORT | \
stdbuf -o0 ffmpeg \
    -f h264 \
    -framerate ${FPS} \
    $FFMPEG_DECODE_OPTS \
    -i - \
    -f rawvideo \
    -pix_fmt rgb24 \
    - \
    -loglevel info -stats | \
python3 -u "$SCRIPT_DIR/server.py" --mode stdin
