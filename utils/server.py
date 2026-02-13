#!/usr/bin/env python

import asyncio
import sys
import argparse
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import struct

width = 384
height = 192
max_message_length = 1024
bytes_per_frame = width * height * 3

def init_led():
    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols=64
    options.chain_length = 6
    options.parallel = 3
    options.gpio_slowdown = 4
    options.brightness = 75
    options.pixel_mapper_config= "Rotate:0"
    options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'
    matrix = RGBMatrix(options = options)
    return matrix

class EchoServerProtocol:
    frame = bytearray()
    received_packets = {}

    def connection_made(self, transport):
        print('Connection')
        self.matrix = init_led()
        self.transport = transport

    def datagram_received(self, data, addr):
        packet = data

        # Extract sequence number and data from the packet
        sequence_number = struct.unpack('!I', packet[:4])[0]
        packet_data = packet[4:]

        # Store the packet in the dictionary using the sequence number
        self.received_packets[sequence_number] = packet_data

        # Check if all packets have been received
        if len(self.received_packets) == sequence_number + 1:
            received_data = b''.join(self.received_packets[i] for i in range(len(self.received_packets)))
            self.paint(received_data)

    def paint(self, image):
        pil_image = Image.frombytes("RGB", (width, height), image)
        self.matrix.SetImage(pil_image)

def init_socket():
    loop = asyncio.get_event_loop()
    print("Starting UDP server")

    # One protocol instance will be created to serve all client requests
    listen = loop.create_datagram_endpoint(
        EchoServerProtocol, local_addr=('192.168.68.57', 12000))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    loop.close()

def run_stdin_mode():
    """Read raw RGB frames from stdin and display on matrix (codec mode)"""
    print("Starting stdin mode (codec)")
    print(f"  Reading raw RGB frames from stdin")
    print(f"  Frame size: {width}x{height} ({bytes_per_frame} bytes)")
    print("")

    # Initialize LED matrix
    matrix = init_led()

    # Configure stdin to binary mode
    stdin_binary = sys.stdin.buffer

    frame_count = 0
    bytes_read_total = 0
    try:
        while True:
            # Read one complete frame from stdin
            frame_data = stdin_binary.read(bytes_per_frame)
            bytes_received = len(frame_data)
            bytes_read_total += bytes_received

            # Debug: Show what we're receiving
            if frame_count < 5 or bytes_received != bytes_per_frame:
                print(f"[Frame {frame_count}] Received {bytes_received} bytes (total: {bytes_read_total})")

            # Check if we got a complete frame
            if bytes_received != bytes_per_frame:
                if bytes_received == 0:
                    print("\nEnd of stream (stdin closed)")
                else:
                    print(f"\nIncomplete frame: got {bytes_received} bytes, expected {bytes_per_frame}")
                break

            # Convert to PIL image and display
            pil_image = Image.frombytes("RGB", (width, height), frame_data)
            matrix.SetImage(pil_image)

            frame_count += 1
            if frame_count % 10 == 0:
                print(f"Frames displayed: {frame_count}", end='\r')

    except KeyboardInterrupt:
        print(f"\nStopped. Total frames: {frame_count}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LED Matrix Server')
    parser.add_argument('--mode', choices=['udp', 'stdin'], default='udp',
                        help='Server mode: udp (raw packets) or stdin (codec stream)')
    args = parser.parse_args()

    if args.mode == 'stdin':
        run_stdin_mode()
    else:
        init_socket()