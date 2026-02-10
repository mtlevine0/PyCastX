#!/usr/bin/env python

import sys
from pathlib import Path

# Add project root to Python path so we can import from utils/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pygame
from components import base
import time
from providers import get_media_provider, TrackInfo
from providers.volume_providers import get_volume_provider
from providers.visualizer_providers import get_visualizer_provider
import logging

from utils.client import UDPFrameClient

display_width = 384 * 1
display_height = 192 * 1

def milliseconds_to_mmss(ms: int) -> str:
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    # Cap at 99:99
    if minutes > 99:
        return "99:99"
    return f"{minutes:02}:{seconds:02}"

if __name__ == "__main__":
    # Initialize providers
    provider = get_media_provider()
    volume_provider = get_volume_provider()
    visualizer_provider = get_visualizer_provider(num_bands=19)

    # Start visualizer (audio capture)
    visualizer_provider.start()

    # Initial track load with error handling
    current_track = provider.get_current_track()
    if current_track is None:
        logging.error("Error: No media playing. Waiting for media...")
        while current_track is None:
            time.sleep(1)
            current_track = provider.get_current_track()

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((display_width, display_height))
    clock = pygame.time.Clock()
    pygame.font.init()

    # Set up initial UI
    title = current_track.artist_name + ' - ' + current_track.track_name + ' (' + milliseconds_to_mmss(current_track.duration_ms) + ') *** '
    test = base.Base(display_width, display_height, title)

    running = True
    counter = 0

    with UDPFrameClient() as client:

        while running:
            # Handle events, required in order to display the PyGame window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Poll for updated track information
            updated_track = provider.get_current_track()

            # Handle None case gracefully - keep displaying current track
            if updated_track is None:
                updated_track = current_track

            # Detect track changes
            if current_track.track_name != updated_track.track_name:
                current_track = updated_track
                title = current_track.artist_name + ' - ' + current_track.track_name + ' (' + milliseconds_to_mmss(current_track.duration_ms) + ') *** '
                test = base.Base(display_width, display_height, title)

            # Use progress_ms directly from provider (DBUS/MPRIS handles playback state)
            display_time_ms = updated_track.progress_ms
            display_time = milliseconds_to_mmss(display_time_ms)

            # Calculate progress percentage
            if updated_track.duration_ms > 0:
                progress_percent = (display_time_ms / updated_track.duration_ms) * 100.0
                progress_percent = min(progress_percent, 100.0)  # Cap at 100%
            else:
                progress_percent = 0.0

            volume_info = volume_provider.get_volume()
            if volume_info:
                volume = volume_info.volume * 100

            # Get audio spectrum data
            spectrum_data = visualizer_provider.get_spectrum()

            # Update and draw UI
            test.move(progress_percent, display_time, volume, updated_track.playback_status, spectrum_data)
            test.draw(screen)

            pygame.display.flip()

            # Output frame to stdout for piping to client (every 5th frame)
            if counter % 2 == 0:
                pil_string_image = pygame.image.tostring(screen, "RGB", False)
                # sys.stdout.buffer.write(pil_string_image)
                client.send_frame(pil_string_image)

            clock.tick(60)
            counter += 1

        # Cleanup
        visualizer_provider.stop()
