#!/usr/bin/env python

import dbus
from dbus.exceptions import DBusException
from typing import Optional
from . import MediaProvider, TrackInfo


class DBusMediaProvider(MediaProvider):
    """Media provider using DBUS/MPRIS interface"""

    def __init__(self):
        self._bus = None
        self._player_name = None

    def is_available(self) -> bool:
        """Check if DBUS and MPRIS players are available"""
        try:
            bus = dbus.SessionBus()
            players = [
                name for name in bus.list_names()
                if name.startswith("org.mpris.MediaPlayer2.")
            ]
            return len(players) > 0
        except (DBusException, Exception):
            return False

    def get_current_track(self) -> Optional[TrackInfo]:
        """Get track info from DBUS/MPRIS"""
        try:
            # Initialize bus connection if needed
            if self._bus is None:
                self._bus = dbus.SessionBus()

            # Find active MPRIS player (cache player name)
            if self._player_name is None:
                players = [
                    name for name in self._bus.list_names()
                    if name.startswith("org.mpris.MediaPlayer2.")
                ]
                if not players:
                    return None
                self._player_name = players[0]

            # Get media player object and properties
            obj = self._bus.get_object(self._player_name, "/org/mpris/MediaPlayer2")
            props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")

            metadata = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            status = props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
            position = props.Get("org.mpris.MediaPlayer2.Player", "Position")

            # Extract and convert data
            track_name = str(metadata.get("xesam:title", "Unknown"))
            artist_name = ", ".join(str(a) for a in metadata.get("xesam:artist", []))
            duration_us = int(metadata.get("mpris:length", 0))

            # Convert microseconds to milliseconds
            duration_ms = duration_us // 1000
            progress_ms = int(position) // 1000

            return TrackInfo(
                track_name=track_name,
                artist_name=artist_name,
                duration_ms=duration_ms,
                progress_ms=progress_ms,
                playback_status=str(status)
            )

        except (DBusException, KeyError, ValueError) as e:
            # Reset cached connection on error
            self._bus = None
            self._player_name = None
            return None
