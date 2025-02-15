#!/usr/bin/env python

import pygame
from components import base
import time
import json
import sys

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
    now_playing = json.load(open('/tmp/now-playing.json', 'r'))
    pygame.init()
    screen = pygame.display.set_mode((display_width, display_height))
    clock = pygame.time.Clock()
    pygame.font.init()
    title = now_playing['artist'] + ' - ' + now_playing['track'] + ' (' + milliseconds_to_mmss(now_playing['duration_ms']) + ') *** '
    test = base.Base(display_width, display_height, title)
    running = True
    position = 0
    start_time = time.time()
    counter = 0
    while running:
        # Handle events, required in order to display the PyGame window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if position < 100:
            position += 0.005
        else:
            position = 0

        try:
            updated_track = json.load(open('/tmp/now-playing.json', 'r'))
        except:
            pass
        
        if now_playing['track'] != updated_track['track']:
            start_time = time.time()
            now_playing = updated_track
            title = now_playing['artist'] + ' - ' + now_playing['track'] + ' (' + milliseconds_to_mmss(now_playing['duration_ms']) + ') *** '
            test = base.Base(display_width, display_height, title)

        display_time = milliseconds_to_mmss(int(time.time() - start_time) * 1000 + now_playing['progress_ms'])
        test.move(updated_track['progress_percent'], display_time)
        test.draw(screen)

        pygame.display.flip()

        if counter % 5 == 0:
            pil_string_image = pygame.image.tostring(screen, "RGB", False)
            sys.stdout.buffer.write(pil_string_image)

        clock.tick(60)
        counter += 1
