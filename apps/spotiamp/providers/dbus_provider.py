#!/usr/bin/env python

import dbus
from dbus.exceptions import DBusException
from typing import Optional
from . import MediaProvider, TrackInfo
import logging

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

    def _find_playing_player(self, prefer_current: bool = True) -> Optional[str]:
        """
        Find an actively playing MPRIS player.

        Args:
            prefer_current: If True and current player is playing, return it immediately

        Returns:
            Player bus name or None if no players found
        """
        try:
            players = [
                name for name in self._bus.list_names()
                if name.startswith("org.mpris.MediaPlayer2.")
            ]

            if not players:
                return None

            # Quick check: if we have a cached player and prefer_current, check if it's still valid
            if prefer_current and self._player_name and self._player_name in players:
                try:
                    obj = self._bus.get_object(self._player_name, "/org/mpris/MediaPlayer2")
                    props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
                    status = props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
                    if str(status) == "Playing":
                        return self._player_name
                except (DBusException, Exception):
                    # Current player is broken, continue search
                    pass

            # Search for any playing player
            for player in players:
                try:
                    obj = self._bus.get_object(player, "/org/mpris/MediaPlayer2")
                    props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
                    status = props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
                    if str(status) == "Playing":
                        return player
                except (DBusException, Exception):
                    # This player is broken, try next
                    continue

            # No playing players found, return first available
            return players[0]

        except (DBusException, Exception):
            return None

    def _should_switch_player(self, current_status: str) -> bool:
        """
        Determine if we should search for a different player.

        Args:
            current_status: PlaybackStatus of current player

        Returns:
            True if we should search for a different playing player
        """
        return current_status in ("Paused", "Stopped")

    def get_current_track(self) -> Optional[TrackInfo]:
        """Get track info from DBUS/MPRIS"""
        try:
            # Initialize bus connection if needed
            if self._bus is None:
                self._bus = dbus.SessionBus()

            # Find active MPRIS player (cache player name)
            if self._player_name is None:
                self._player_name = self._find_playing_player(prefer_current=False)
                if not self._player_name:
                    return None

            # Get media player object and properties
            obj = self._bus.get_object(self._player_name, "/org/mpris/MediaPlayer2")
            props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")

            metadata = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            status = props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
            position = props.Get("org.mpris.MediaPlayer2.Player", "Position")

            # Opportunistic switching: if current player not playing, look for playing player
            status_str = str(status)
            if self._should_switch_player(status_str):
                better_player = self._find_playing_player(prefer_current=False)
                if better_player and better_player != self._player_name:
                    # Switch to the playing player
                    logging.info(f"Switching from {self._player_name} ({status_str}) to {better_player}")
                    self._player_name = better_player

                    # Re-fetch data from new player
                    obj = self._bus.get_object(self._player_name, "/org/mpris/MediaPlayer2")
                    props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
                    metadata = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
                    status = props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
                    position = props.Get("org.mpris.MediaPlayer2.Player", "Position")
                    status_str = str(status)

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
                playback_status=status_str
            )

        except (DBusException, KeyError, ValueError) as e:
            # Reset cached connection on error
            self._bus = None
            self._player_name = None
            logging.error(e)
            return None
