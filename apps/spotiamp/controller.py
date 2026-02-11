#!/usr/bin/env python

from typing import Optional
from components.base import Base
from providers import MediaProvider, TrackInfo
from providers.volume_providers import VolumeProvider
from providers.visualizer_providers import VisualizerProvider

def milliseconds_to_mmss(ms: int) -> str:
    """Convert milliseconds to MM:SS format"""
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    if minutes > 99:
        return "99:99"
    return f"{minutes:02}:{seconds:02}"

class SpotiampController:
    """
    Controller for spotiamp application.
    Orchestrates updates between data providers and UI view.
    """

    def __init__(self, display_width, display_height,
                 media_provider: MediaProvider,
                 volume_provider: VolumeProvider,
                 visualizer_provider: VisualizerProvider):
        self.display_width = display_width
        self.display_height = display_height
        self.media_provider = media_provider
        self.volume_provider = volume_provider
        self.visualizer_provider = visualizer_provider

        # State
        self.current_track: Optional[TrackInfo] = None
        self.view: Optional[Base] = None

        # Volume display state
        self.previous_volume: Optional[int] = None
        self.volume_display_frames_remaining = 0

    def initialize_view(self, initial_track: TrackInfo):
        """Create initial view with track information"""
        self.current_track = initial_track
        title = self._format_track_title(initial_track)
        self.view = Base(self.display_width, self.display_height, title)

    def update(self):
        """
        Main update method called every frame.
        Orchestrates all provider updates and view rendering.
        """
        # 1. Get updated track info
        updated_track = self.media_provider.get_current_track()
        if updated_track is None:
            updated_track = self.current_track  # Keep current if provider returns None

        # 2. Handle track changes
        if self._detect_track_change(updated_track):
            self._handle_track_change(updated_track)

        # 3. Handle volume changes
        volume_info = self.volume_provider.get_volume()
        volume = 0.0
        if volume_info:
            volume = volume_info.volume * 100
            self._handle_volume_change(volume_info.volume_percent)

        # 4. Get spectrum data
        spectrum_data = self.visualizer_provider.get_spectrum()

        # 5. Calculate display values
        display_time = milliseconds_to_mmss(updated_track.progress_ms)
        progress_percent = self._calculate_progress_percent(updated_track)

        # 6. Update view
        self.view.move(
            progress_percent,
            display_time,
            volume,
            updated_track.playback_status,
            spectrum_data
        )

    def _detect_track_change(self, updated_track: TrackInfo) -> bool:
        """Check if track has changed"""
        return (self.current_track is None or
                self.current_track.track_name != updated_track.track_name)

    def _handle_track_change(self, new_track: TrackInfo):
        """Handle track change - recreate view and reset state"""
        self.current_track = new_track
        title = self._format_track_title(new_track)
        self.view = Base(self.display_width, self.display_height, title)

        # Reset volume display state
        self.volume_display_frames_remaining = 0
        self.previous_volume = None

    def _handle_volume_change(self, current_volume_percent: int):
        """Detect volume changes and manage display countdown"""
        # Detect change
        if (self.previous_volume is not None and
            self.previous_volume != current_volume_percent):
            # Volume changed - show display
            self.view.show_volume_display(current_volume_percent)
            self.volume_display_frames_remaining = 60  # 1 second at 60 FPS

        self.previous_volume = current_volume_percent

        # Handle countdown
        if self.volume_display_frames_remaining > 0:
            self.volume_display_frames_remaining -= 1
            if self.volume_display_frames_remaining == 0:
                self.view.hide_volume_display()

    def _calculate_progress_percent(self, track: TrackInfo) -> float:
        """Calculate playback progress percentage"""
        if track.duration_ms > 0:
            progress = (track.progress_ms / track.duration_ms) * 100.0
            return min(progress, 100.0)
        return 0.0

    def _format_track_title(self, track: TrackInfo) -> str:
        """Format track title for marquee display"""
        duration_str = milliseconds_to_mmss(track.duration_ms)
        return f"{track.artist_name} - {track.track_name} ({duration_str}) *** "

    def draw(self, surface):
        """Draw view to surface"""
        self.view.draw(surface)
