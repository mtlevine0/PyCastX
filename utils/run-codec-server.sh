#!/bin/bash
# Wrapper script to run LED server with H.264 codec decompression
# Receives H.264 stream via UDP, decodes with FFmpeg, pipes to server.py

# Configuration
LISTEN_PORT="12001"
WIDTH="384"
HEIGHT="192"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg not found. Please install ffmpeg."
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    exit 1
fi

echo "Starting LED server with H.264 codec streaming..."
echo "  Listening on: 192.168.68.57:$LISTEN_PORT"
echo "  Resolution: ${WIDTH}x${HEIGHT}"
echo ""

# Detect hardware decoder availability
# Temporarily force software decoder for testing
DECODER="h264"
echo "  Using software decoder: h264 (testing - may be CPU intensive)"
# DECODER="h264"
# if ffmpeg -decoders 2>/dev/null | grep -q "h264_mmal"; then
#     DECODER="h264_mmal"
#     echo "  Using hardware decoder: h264_mmal (Raspberry Pi)"
# elif ffmpeg -decoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
#     DECODER="h264_v4l2m2m"
#     echo "  Using hardware decoder: h264_v4l2m2m"
# else
#     echo "  Using software decoder: h264 (CPU-based)"
#     echo "  WARNING: Software decoding may be slow!"
# fi
echo ""
echo "Waiting for H.264 stream... (may take a few seconds to sync)"
echo ""

# Run FFmpeg decoder piped to server.py in stdin mode
# Using raw H.264 stream (no container) for minimal latency
# Expecting ~10 FPS (actual app output rate, not 12)
stdbuf -o0 ffmpeg \
    -listen 1 \
    -f h264 \
    -framerate 10 \
    -fflags nobuffer \
    -flags low_delay \
    -i tcp://192.168.68.57:${LISTEN_PORT} \
    -c:v ${DECODER} \
    -f rawvideo \
    -pix_fmt rgb24 \
    -vsync passthrough \
    - \
    -loglevel warning | python -u "$SCRIPT_DIR/server.py" --mode stdin
