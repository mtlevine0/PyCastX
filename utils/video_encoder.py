#!/usr/bin/env python3
"""
Video encoder that wraps FFmpeg and sends H.264 stream over TCP
Separates encoding from network transfer for better reliability
"""

import subprocess
import socket
import sys
import logging

logging.basicConfig(level=logging.INFO, format='[Encoder] %(message)s')

class VideoEncoder:
    def __init__(self, width=384, height=192, fps=12, bitrate='1M',
                 server_ip='192.168.68.57', server_port=12001):
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.server_ip = server_ip
        self.server_port = server_port
        self.ffmpeg_process = None
        self.socket = None

    def start(self):
        """Start FFmpeg encoder subprocess"""
        logging.info(f"Starting encoder: {self.width}x{self.height} @ {self.fps}fps, {self.bitrate}")

        # Start FFmpeg encoder that outputs H.264 to stdout
        cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{self.width}x{self.height}',
            '-framerate', str(self.fps),
            '-i', '-',  # Read from stdin
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-pix_fmt', 'yuv420p',
            '-g', str(self.fps),  # Keyframe every second
            '-b:v', self.bitrate,
            '-maxrate', self.bitrate,
            '-bufsize', '512k',
            '-x264-params', 'bframes=0:scenecut=0',
            '-f', 'h264',
            '-',  # Output to stdout
            '-loglevel', 'error'
        ]

        self.ffmpeg_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr.buffer
        )

        # Connect to server
        logging.info(f"Connecting to {self.server_ip}:{self.server_port}...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip, self.server_port))
        logging.info("Connected!")

    def write_frame(self, frame_data: bytes):
        """Write raw RGB frame to encoder"""
        if self.ffmpeg_process and self.ffmpeg_process.stdin:
            try:
                self.ffmpeg_process.stdin.write(frame_data)
                self.ffmpeg_process.stdin.flush()
            except BrokenPipeError:
                logging.error("FFmpeg pipe broken!")
                return False
        return True

    def send_encoded_data(self):
        """Read encoded data from FFmpeg and send over socket"""
        if not self.ffmpeg_process or not self.socket:
            return

        # Read available encoded data from FFmpeg stdout
        # Non-blocking read with select would be better but keeping it simple
        try:
            # Read in chunks
            chunk = self.ffmpeg_process.stdout.read(4096)
            if chunk:
                self.socket.sendall(chunk)
                return len(chunk)
        except Exception as e:
            logging.error(f"Error sending data: {e}")
            return 0
        return 0

    def stop(self):
        """Stop encoder gracefully"""
        logging.info("Stopping encoder...")
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait(timeout=5)
        if self.socket:
            self.socket.close()
        logging.info("Encoder stopped")


if __name__ == "__main__":
    # Test mode: read frames from stdin, encode, and stream
    import time

    encoder = VideoEncoder()
    encoder.start()

    frame_size = 384 * 192 * 3
    frame_count = 0

    try:
        while True:
            # Read one frame from stdin
            frame_data = sys.stdin.buffer.read(frame_size)
            if len(frame_data) != frame_size:
                break

            # Write to encoder
            if not encoder.write_frame(frame_data):
                break

            # Send any available encoded data
            sent = encoder.send_encoded_data()

            frame_count += 1
            if frame_count % 10 == 0:
                logging.info(f"Frames: {frame_count}, Sent: {sent} bytes")

    except KeyboardInterrupt:
        logging.info("Interrupted")
    finally:
        encoder.stop()
        logging.info(f"Total frames: {frame_count}")
