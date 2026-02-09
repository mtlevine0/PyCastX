#!/usr/bin/env python

import json
import os
from typing import Optional
from . import MediaProvider, TrackInfo


class JSONFileMediaProvider(MediaProvider):
    """Media provider using JSON file (legacy/fallback)"""

    def __init__(self, file_path: str = "/tmp/now-playing.json"):
        self.file_path = file_path

    def is_available(self) -> bool:
        """Check if JSON file exists"""
        return os.path.exists(self.file_path)

    def get_current_track(self) -> Optional[TrackInfo]:
        """Read track info from JSON file"""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)

            return TrackInfo(
                track_name=data['track'],
                artist_name=data['artist'],
                duration_ms=data['duration_ms'],
                progress_ms=data['progress_ms'],
                playback_status="Playing"
            )
        except (FileNotFoundError, KeyError, json.JSONDecodeError, IOError):
            return None
