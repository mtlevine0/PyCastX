#!/usr/bin/env python

import struct
import socket
import datetime as dt
import sys


class UDPFrameClient:
    """UDP client for sending video frames to an LED matrix server.

    Handles packetization and transmission of raw RGB frame data over UDP.
    """

    def __init__(self, host="192.168.68.57", port=12000, max_message_length=1024, timeout=5.0):
        """Initialize the UDP frame client.

        Args:
            host: IP address of the server (Raspberry Pi)
            port: UDP port number
            max_message_length: Maximum size of each UDP packet payload (bytes)
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.max_message_length = max_message_length
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(timeout)
        self.addr = (host, port)

    def send_frame(self, frame):
        """Send a video frame to the server.

        Splits the frame into packets with sequence numbers and transmits via UDP.

        Args:
            frame: Raw RGB frame data as bytes
        """
        packets = [frame[i:i + self.max_message_length] for i in range(0, len(frame), self.max_message_length)]
        for i, packet in enumerate(packets):
            # Add sequence number to the packet
            packet_with_sequence = struct.pack('!I', i) + packet
            self.client_socket.sendto(packet_with_sequence, self.addr)

    def close(self):
        """Close the UDP socket."""
        self.client_socket.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close socket."""
        self.close()

def read_exact_bytes(stream, size):
    buffer = b''
    while len(buffer) < size:
        chunk = stream.read(size - len(buffer))
        if not chunk:
            return None  # Return None if no more data is available
        buffer += chunk
    return buffer

if __name__ == "__main__":
    # Default frame dimensions for standalone mode
    width = 384
    height = 192
    frame_size_bytes = width * height * 3  # Calculate the size of a single frame in bytes

    with UDPFrameClient() as client:
        start_time = dt.datetime.today().timestamp()
        i = 0
        while True:
            frame_data = read_exact_bytes(sys.stdin.buffer.raw, frame_size_bytes)
            if frame_data is None:
                break  # Break the loop if no more data is available
            client.send_frame(frame_data)
