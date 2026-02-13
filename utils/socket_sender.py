#!/usr/bin/env python3
"""
Simple socket sender - reads H.264 from stdin, sends over TCP
More reliable than FFmpeg's built-in TCP streaming
"""

import sys
import socket
import time

if len(sys.argv) != 3:
    print("Usage: socket_sender.py <host> <port>")
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])

print(f"[Sender] Connecting to {host}:{port}...", file=sys.stderr)

# Connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
sock.connect((host, port))

print(f"[Sender] Connected! Streaming...", file=sys.stderr)

bytes_sent = 0
start_time = time.time()
last_report = start_time

try:
    while True:
        # Read from stdin (encoded H.264 data from FFmpeg)
        chunk = sys.stdin.buffer.read(4096)
        if not chunk:
            break

        # Send over socket
        sock.sendall(chunk)
        bytes_sent += len(chunk)

        # Report every 2 seconds
        now = time.time()
        if now - last_report >= 2.0:
            elapsed = now - start_time
            mbps = (bytes_sent * 8 / elapsed) / 1_000_000
            kbps = (bytes_sent * 8 / elapsed) / 1_000
            recent_bytes = bytes_sent
            print(f"[Sender] {bytes_sent:,} bytes sent | {mbps:.2f} Mbps ({kbps:.0f} Kbps) | {elapsed:.1f}s", file=sys.stderr)
            last_report = now

except BrokenPipeError:
    print("[Sender] Connection closed by server", file=sys.stderr)
except KeyboardInterrupt:
    print("[Sender] Interrupted", file=sys.stderr)
finally:
    elapsed = time.time() - start_time
    if elapsed > 0:
        mbps = (bytes_sent * 8 / elapsed) / 1_000_000
        print(f"[Sender] Complete: {bytes_sent:,} bytes in {elapsed:.1f}s ({mbps:.2f} Mbps)", file=sys.stderr)
    sock.close()
