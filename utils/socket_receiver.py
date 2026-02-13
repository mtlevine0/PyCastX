#!/usr/bin/env python3
"""
Simple socket receiver - receives H.264 over TCP, writes to stdout
More reliable than FFmpeg's built-in TCP streaming
"""

import sys
import socket
import time

if len(sys.argv) != 2:
    print("Usage: socket_receiver.py <port>")
    sys.exit(1)

port = int(sys.argv[1])

print(f"[Receiver] Listening on port {port}...", file=sys.stderr)

# Create server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', port))
server.listen(1)

print(f"[Receiver] Waiting for connection...", file=sys.stderr)

# Accept connection
conn, addr = server.accept()
conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm

print(f"[Receiver] Connected from {addr[0]}:{addr[1]}", file=sys.stderr)

bytes_received = 0
start_time = time.time()
last_report = start_time

try:
    while True:
        # Receive from socket
        chunk = conn.recv(8192)
        if not chunk:
            break

        # Write to stdout (to FFmpeg decoder)
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        bytes_received += len(chunk)

        # Report every 2 seconds
        now = time.time()
        if now - last_report >= 2.0:
            elapsed = now - start_time
            mbps = (bytes_received * 8 / elapsed) / 1_000_000
            kbps = (bytes_received * 8 / elapsed) / 1_000
            print(f"[Receiver] {bytes_received:,} bytes received | {mbps:.2f} Mbps ({kbps:.0f} Kbps) | {elapsed:.1f}s", file=sys.stderr)
            last_report = now

except BrokenPipeError:
    print("[Receiver] Output pipe closed", file=sys.stderr)
except KeyboardInterrupt:
    print("[Receiver] Interrupted", file=sys.stderr)
finally:
    elapsed = time.time() - start_time
    if elapsed > 0:
        mbps = (bytes_received * 8 / elapsed) / 1_000_000
        print(f"[Receiver] Complete: {bytes_received:,} bytes in {elapsed:.1f}s ({mbps:.2f} Mbps)", file=sys.stderr)
    conn.close()
    server.close()
