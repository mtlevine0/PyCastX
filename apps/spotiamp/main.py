#!/usr/bin/env python

import sys
from pathlib import Path

# Add project root to Python path so we can import from utils/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pygame
from components import base
from components.text import Marquee
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

    # Volume change tracking state
    previous_volume = None  # Track previous volume to detect changes
    volume_display_frames_remaining = 0  # Countdown timer (60 frames = 1 second)
    original_marquee = None  # Store original marquee object to preserve scroll position

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

                # Reset volume display state on track change
                volume_display_frames_remaining = 0
                original_marquee = None
                previous_volume = None  # Reset to allow volume changes on new track

            # Use progress_ms directly from provider (DBUS/MPRIS handles playback state)
            display_time_ms = updated_track.progress_ms
            display_time = milliseconds_to_mmss(display_time_ms)

            # Calculate progress percentage
            if updated_track.duration_ms > 0:
                progress_percent = (display_time_ms / updated_track.duration_ms) * 100.0
                progress_percent = min(progress_percent, 100.0)  # Cap at 100%
            else:
                progress_percent = 0.0

            # Get current volume
            volume_info = volume_provider.get_volume()
            current_volume_percent = None
            if volume_info:
                current_volume_percent = volume_info.volume_percent
                volume = volume_info.volume * 100  # For slider (0-100 float)

                # Detect volume change
                if previous_volume is not None and previous_volume != current_volume_percent:
                    # Volume changed - start displaying volume
                    volume_display_frames_remaining = 60  # 1 second at 60 FPS

                    # Store original text surface and position to restore later
                    if original_marquee is None:
                        original_marquee = {
                            'text_surface': test.marquee.text_surface,
                            'text_rect': test.marquee.text_rect,
                            'marquee_position': test.marquee.marquee_position,
                            'tiles': test.marquee.tiles
                        }

                    # Replace text surface with volume display (centered, no scrolling)
                    volume_text = f"VOLUME: {current_volume_percent}%"
                    volume_text_surface = test.text.draw(volume_text, test.base_surface)

                    # Clear the marquee surface with black before replacing text
                    test.marquee.marquee_surface.fill((0, 0, 0))

                    test.marquee.text_surface = volume_text_surface
                    test.marquee.text_rect = volume_text_surface.get_rect()
                    test.marquee.marquee_position = 0  # Reset position
                    test.marquee.tiles = 1  # Don't repeat

                    # Manually draw the volume text once (since we'll freeze the marquee)
                    test.marquee.marquee_surface.blit(volume_text_surface, (0, 0))

                previous_volume = current_volume_percent

            # Handle volume display countdown
            if volume_display_frames_remaining > 0:
                volume_display_frames_remaining -= 1

                # Keep marquee frozen (prevent scrolling) by resetting frame counter
                # Marquee only scrolls when frame > 15, so keeping it at 0 prevents movement
                test.marquee.frame = 0

                # Time expired - restore original marquee with preserved scroll position
                if volume_display_frames_remaining == 0 and original_marquee is not None:
                    test.marquee.text_surface = original_marquee['text_surface']
                    test.marquee.text_rect = original_marquee['text_rect']
                    test.marquee.marquee_position = original_marquee['marquee_position']
                    test.marquee.tiles = original_marquee['tiles']
                    original_marquee = None

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
