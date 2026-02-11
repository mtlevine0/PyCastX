#!/usr/bin/env python

import sys
from pathlib import Path

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

display_width = 384
display_height = 192

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

    # Initialize controller
    controller = SpotiampController(
        display_width, display_height,
        media_provider, volume_provider, visualizer_provider
    )
    controller.initialize_view(initial_track)

    # Main game loop
    running = True
    counter = 0

    with UDPFrameClient() as client:
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

            # Send frame to LED matrix (every 2nd frame)
            if counter % 2 == 0:
                pil_string_image = pygame.image.tostring(screen, "RGB", False)
                client.send_frame(pil_string_image)

            clock.tick(60)
            counter += 1

    # Cleanup
    visualizer_provider.stop()
