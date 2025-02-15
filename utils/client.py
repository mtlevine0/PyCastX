#!/usr/bin/env python

import struct
import socket
import datetime as dt
import sys

max_message_length = 1024
width = 384
height = 192

def init_network():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(5.0)
    addr = ("192.168.68.85", 12000)
    return (client_socket, addr)

def send_frame(client_socket, addr, frame):
    packets = [frame[i:i + max_message_length] for i in range(0, len(frame), max_message_length)]
    for i, packet in enumerate(packets):
        # Add sequence number to the packet
        packet_with_sequence = struct.pack('!I', i) + packet
        client_socket.sendto(packet_with_sequence, addr)

def read_exact_bytes(stream, size):
    buffer = b''
    while len(buffer) < size:
        chunk = stream.read(size - len(buffer))
        if not chunk:
            return None  # Return None if no more data is available
        buffer += chunk
    return buffer

if __name__ == "__main__":
    client_socket, addr = init_network()
    start_time = dt.datetime.today().timestamp()
    i = 0
    frame_size_bytes = width * height * 3 # Calculate the size of a single frame in bytes
    while True:
        frame_data = read_exact_bytes(sys.stdin.buffer.raw, frame_size_bytes)
        if frame_data is None:
            break  # Break the loop if no more data is available
        img_data = struct.unpack(f'{width * height * 3}B', frame_data)
        print(len(frame_data))
        send_frame(client_socket, addr, frame_data)
