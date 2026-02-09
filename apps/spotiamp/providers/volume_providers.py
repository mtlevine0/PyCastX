#!/usr/bin/env python

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging
import subprocess


@dataclass
class VolumeInfo:
    """Standardized volume information structure"""
    volume: float  # 0.0 to 1.0 (0% to 100%)
    is_muted: bool

    @property
    def volume_percent(self) -> int:
        """Get volume as integer percentage 0-100"""
        return int(self.volume * 100)


class VolumeProvider(ABC):
    """Abstract base class for volume providers"""

    @abstractmethod
    def get_volume(self) -> Optional[VolumeInfo]:
        """
        Get current system volume information.
        Returns None if volume data is unavailable.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the current system"""
        pass


class PulseAudioVolumeProvider(VolumeProvider):
    """Volume provider using PulseAudio via pulsectl library"""

    def __init__(self):
        self._pulse = None

    def is_available(self) -> bool:
        """Check if PulseAudio and pulsectl are available"""
        try:
            import pulsectl
            # Test connection
            with pulsectl.Pulse('volume-check') as pulse:
                pulse.server_info()
            return True
        except (ImportError, Exception):
            return False

    def get_volume(self) -> Optional[VolumeInfo]:
        """Get volume from PulseAudio default sink"""
        try:
            import pulsectl

            with pulsectl.Pulse('volume-getter') as pulse:
                # Get default sink (master output)
                server_info = pulse.server_info()
                sink = pulse.get_sink_by_name(server_info.default_sink_name)

                # Volume is per-channel, calculate average
                if sink.volume.values:
                    avg_volume = sum(sink.volume.values) / len(sink.volume.values)
                else:
                    avg_volume = 0.0

                return VolumeInfo(
                    volume=avg_volume,
                    is_muted=bool(sink.mute)
                )

        except (ImportError, Exception) as e:
            return None


class SubprocessVolumeProvider(VolumeProvider):
    """Volume provider using pactl subprocess (fallback)"""

    def is_available(self) -> bool:
        """Check if pactl command is available"""
        try:
            result = subprocess.run(
                ['pactl', '--version'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_volume(self) -> Optional[VolumeInfo]:
        """Get volume using pactl command"""
        try:
            # Get volume
            result = subprocess.run(
                ['pactl', 'get-sink-volume', '@DEFAULT_SINK@'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return None

            # Parse output like: "Volume: front-left: 65536 / 100% / 0.00 dB"
            volume = None
            for part in result.stdout.split():
                if '%' in part:
                    volume = float(part.rstrip('%')) / 100.0
                    break

            if volume is None:
                return None

            # Get mute status
            mute_result = subprocess.run(
                ['pactl', 'get-sink-mute', '@DEFAULT_SINK@'],
                capture_output=True,
                text=True,
                timeout=2
            )

            is_muted = 'yes' in mute_result.stdout.lower() if mute_result.returncode == 0 else False

            return VolumeInfo(
                volume=volume,
                is_muted=is_muted
            )

        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            return None


def get_volume_provider() -> VolumeProvider:
    """
    Factory function to get the best available volume provider.
    Tries providers in order of preference:
    1. PulseAudio via pulsectl (Linux with PulseAudio)
    2. Subprocess pactl (fallback)
    """
    # Try PulseAudio via pulsectl first
    try:
        pulse_provider = PulseAudioVolumeProvider()
        if pulse_provider.is_available():
            logging.info("Using PulseAudio volume provider")
            return pulse_provider
    except Exception as e:
        logging.error(f"PulseAudio provider not available: {e}")

    # Fallback to subprocess pactl
    subprocess_provider = SubprocessVolumeProvider()
    if subprocess_provider.is_available():
        logging.info("Using subprocess (pactl) volume provider (fallback)")
        return subprocess_provider

    # Return subprocess provider anyway (will return None from get_volume)
    logging.warning("Warning: No volume provider available, using subprocess with no pactl")
    return subprocess_provider
