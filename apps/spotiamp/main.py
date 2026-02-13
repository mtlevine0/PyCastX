#!/usr/bin/env python

import os
import sys
import json
from pathlib import Path

# Suppress pygame welcome message (corrupts binary stdout stream!)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Add project root to Python path so we can import from utils/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pygame
import time
import logging

from controller import SpotiampController
from providers import get_media_provider
from providers.volume_providers import get_volume_provider
from providers.visualizer_providers import get_visualizer_provider
from utils.client import UDPFrameClient

# Configure logging to stderr (default) to keep stdout clean for binary frame data
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    stream=sys.stderr  # Explicitly use stderr
)

# Load streaming configuration
config_path = project_root / 'config' / 'streaming.json'
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
    display_width = config['video']['width']
    display_height = config['video']['height']
    frame_skip = config['application']['frame_skip']
    logging.info(f"Loaded config: {display_width}x{display_height} @ {60/frame_skip:.1f} FPS (skip={frame_skip})")
else:
    # Defaults if no config
    display_width = 384
    display_height = 192
    frame_skip = 4  # 15 FPS
    logging.warning(f"Config not found, using defaults")

if __name__ == "__main__":
    # Initialize providers
    media_provider = get_media_provider()
    volume_provider = get_volume_provider()
    visualizer_provider = get_visualizer_provider(num_bands=19)
    visualizer_provider.start()

    # Wait for initial track
    initial_track = media_provider.get_current_track()
    if initial_track is None:
        logging.error("Waiting for media to start playing...")
        while initial_track is None:
            time.sleep(1)
            initial_track = media_provider.get_current_track()

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((display_width, display_height))
    clock = pygame.time.Clock()
    pygame.font.init()

    # Verify frame size for codec streaming
    expected_frame_size = display_width * display_height * 3  # RGB = 3 bytes per pixel
    logging.info(f"Display: {display_width}x{display_height}, expected frame size: {expected_frame_size} bytes")

    # Initialize controller
    controller = SpotiampController(
        display_width, display_height,
        media_provider, volume_provider, visualizer_provider
    )
    controller.initialize_view(initial_track)

    # Pre-warm: Run for a few seconds without streaming to stabilize FPS
    logging.info("Pre-warming app (2 seconds)...")
    warm_start = time.time()
    while time.time() - warm_start < 2.0:
        controller.update()
        controller.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    logging.info("Pre-warm complete, starting stream output...")

    # Main game loop
    running = True
    counter = 0
    frames_sent = 0
    fps_start_time = time.time()
    last_fps_report = fps_start_time

    with UDPFrameClient() as client:
        try:
            while running:
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                # Update controller (orchestrates everything)
                controller.update()

                # Draw to screen
                controller.draw(screen)
                pygame.display.flip()

                # Send frame to LED matrix (every Nth frame, configurable)
                if counter % frame_skip == 0:
                    pil_string_image = pygame.image.tostring(screen, "RGB", False)
                    # client.send_frame(pil_string_image)
                    try:
                        sys.stdout.buffer.write(pil_string_image)
                        sys.stdout.buffer.flush()  # Critical: ensure frame is sent immediately
                        frames_sent += 1

                        # Report FPS every 2 seconds
                        now = time.time()
                        if now - last_fps_report >= 2.0:
                            elapsed = now - fps_start_time
                            current_fps = frames_sent / elapsed
                            logging.info(f"Streaming: {frames_sent} frames sent, {current_fps:.2f} FPS")
                            last_fps_report = now
                    except BrokenPipeError:
                        # FFmpeg/pipe closed, exit gracefully
                        logging.info("Output pipe closed, exiting")
                        running = False

                clock.tick(60)
                counter += 1
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl+C
            logging.info("Interrupted, shutting down...")
        finally:
            # Cleanup
            visualizer_provider.stop()
