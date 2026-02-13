#!/bin/bash
# Wrapper script to run spotiamp with H.264 codec compression
# Pipes pygame output to FFmpeg encoder which sends H.264 stream over UDP

# Configuration
SERVER_IP="192.168.68.57"
SERVER_PORT="12001"
WIDTH="384"
HEIGHT="192"
FPS="10"  # Match actual output (was 12, but app only does ~10.5)
BITRATE="1M"
GOP_SIZE="10"  # I-frame every second (match FPS)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg not found. Please install ffmpeg."
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "ERROR: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "Starting Spotiamp with H.264 codec streaming..."
echo "  Server: $SERVER_IP:$SERVER_PORT"
echo "  Resolution: ${WIDTH}x${HEIGHT}"
echo "  FPS: $FPS"
echo "  Bitrate: $BITRATE"
echo ""
echo "Note: Python stderr output will appear below (if any)"
echo "      FFmpeg is receiving binary frame data via pipe"
echo ""

# Activate virtual environment and run main.py piped to FFmpeg encoder
source "$SCRIPT_DIR/.venv/bin/activate"

# Use python -u for unbuffered output (critical for streaming!)
# Python's stdout → FFmpeg stdin (binary frame data)
# Python's stderr → terminal (log messages, won't corrupt stream)
# FFmpeg's stderr → terminal (encoding stats)
python -u "$SCRIPT_DIR/main.py" | ffmpeg \
    -f rawvideo \
    -pix_fmt rgb24 \
    -s ${WIDTH}x${HEIGHT} \
    -framerate ${FPS} \
    -use_wallclock_as_timestamps 1 \
    -i - \
    -c:v libx264 \
    -preset ultrafast \
    -tune zerolatency \
    -pix_fmt yuv420p \
    -g ${GOP_SIZE} \
    -r ${FPS} \
    -b:v ${BITRATE} \
    -maxrate ${BITRATE} \
    -bufsize 512K \
    -x264-params "bframes=0:scenecut=0" \
    -f h264 \
    -flush_packets 1 \
    tcp://${SERVER_IP}:${SERVER_PORT} \
    -loglevel error
