#!/usr/bin/env python

import pygame
from components import base
import time
import sys
from providers import get_media_provider, TrackInfo
import logging

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
    # Initialize media provider
    provider = get_media_provider()

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
    start_time = time.time()
    counter = 0

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
            start_time = time.time()
            current_track = updated_track
            title = current_track.artist_name + ' - ' + current_track.track_name + ' (' + milliseconds_to_mmss(current_track.duration_ms) + ') *** '
            test = base.Base(display_width, display_height, title)

        # Calculate display time and position
        elapsed_ms = int((time.time() - start_time) * 1000)
        display_time_ms = elapsed_ms + current_track.progress_ms
        display_time = milliseconds_to_mmss(display_time_ms)

        # Calculate progress percentage
        if current_track.duration_ms > 0:
            progress_percent = (display_time_ms / current_track.duration_ms) * 100.0
            progress_percent = min(progress_percent, 100.0)  # Cap at 100%
        else:
            progress_percent = 0.0

        # Update and draw UI
        test.move(progress_percent, display_time)
        test.draw(screen)

        pygame.display.flip()

        # Output frame to stdout for piping to client (every 5th frame)
        if counter % 5 == 0:
            pil_string_image = pygame.image.tostring(screen, "RGB", False)
            sys.stdout.buffer.write(pil_string_image)

        clock.tick(60)
        counter += 1
