#!/usr/bin/env python

import asyncio
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import struct

width = 384
height = 192
max_message_length = 1024

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
        EchoServerProtocol, local_addr=('192.168.68.85', 12000))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    loop.close()

if __name__ == "__main__":
    init_socket()