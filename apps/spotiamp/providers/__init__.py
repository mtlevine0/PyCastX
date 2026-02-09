#!/usr/bin/env python

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging

@dataclass
class TrackInfo:
    """Standardized track information structure"""
    track_name: str
    artist_name: str
    duration_ms: int
    progress_ms: int
    playback_status: str  # "Playing", "Paused", "Stopped"

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.duration_ms <= 0:
            return 0.0
        return (self.progress_ms / self.duration_ms) * 100.0


class MediaProvider(ABC):
    """Abstract base class for media providers"""

    @abstractmethod
    def get_current_track(self) -> Optional[TrackInfo]:
        """
        Get currently playing track information.
        Returns None if no track is playing or data unavailable.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the current system"""
        pass


def get_media_provider() -> MediaProvider:
    """
    Factory function to get the best available media provider.
    Tries providers in order of preference:
    1. DBus (Linux with MPRIS)
    2. JSON file (fallback)
    """
    from .json_provider import JSONFileMediaProvider

    # Try DBUS first (may fail if dbus-python not installed)
    try:
        from .dbus_provider import DBusMediaProvider
        dbus_provider = DBusMediaProvider()
        if dbus_provider.is_available():
            logging.error("Using DBUS media provider")
            return dbus_provider
    except (ImportError, Exception) as e:
        logging.error(f"DBUS provider not available: {e}")

    # Fallback to JSON file
    json_provider = JSONFileMediaProvider()
    if json_provider.is_available():
        logging.error("Using JSON file media provider (fallback)")
        return json_provider

    # Return JSON provider anyway (will return None from get_current_track)
    logging.error("Warning: No media provider available, using JSON with no file")
    return json_provider
