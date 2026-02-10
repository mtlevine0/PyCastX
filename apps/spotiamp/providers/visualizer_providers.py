#!/usr/bin/env python

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import logging
import threading


@dataclass
class SpectrumData:
    """Standardized audio spectrum information structure"""
    bands: List[float]  # Magnitude for each frequency band (0.0 to 1.0)
    num_bands: int

    @property
    def normalized_bands(self) -> List[float]:
        """Get bands normalized to 0-1 range"""
        if not self.bands or max(self.bands) == 0:
            return [0.0] * self.num_bands
        max_val = max(self.bands)
        return [b / max_val for b in self.bands]


class VisualizerProvider(ABC):
    """Abstract base class for audio visualizer providers"""

    @abstractmethod
    def get_spectrum(self) -> Optional[SpectrumData]:
        """
        Get current audio spectrum data.
        Returns None if spectrum data is unavailable.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available on the current system"""
        pass

    @abstractmethod
    def start(self):
        """Start audio capture and analysis"""
        pass

    @abstractmethod
    def stop(self):
        """Stop audio capture and cleanup resources"""
        pass


class SoundDeviceVisualizerProvider(VisualizerProvider):
    """Visualizer provider using sounddevice for audio capture and FFT analysis"""

    def __init__(self, num_bands=10, samplerate=44100, blocksize=2048, noise_threshold=0.001, device_name=None):
        """
        Initialize the visualizer provider.

        Args:
            num_bands: Number of frequency bands (like Winamp's equalizer bars)
            samplerate: Audio sample rate in Hz
            blocksize: Number of samples per FFT block
            noise_threshold: Minimum RMS amplitude to consider as signal (0.0 to 1.0)
            device_name: Specific device name to use (e.g., "pulse" or PulseAudio source name)
                        If None, will auto-detect monitor device
        """
        self.num_bands = num_bands
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.noise_threshold = noise_threshold
        self.device_name = device_name
        self._stream = None
        self._latest_spectrum = SpectrumData(bands=[0.0] * num_bands, num_bands=num_bands)
        self._lock = threading.Lock()
        self._started = False

    def is_available(self) -> bool:
        """Check if sounddevice and required libraries are available"""
        try:
            import sounddevice as sd
            import numpy as np
            from scipy.fft import rfft

            # Try to query devices
            devices = sd.query_devices()
            return True
        except (ImportError, Exception) as e:
            logging.error(f"SoundDevice visualizer not available: {e}")
            return False

    def _audio_callback(self, indata, frames, time, status):
        """Callback function for sounddevice audio stream"""
        if status:
            logging.warning(f"Audio callback status: {status}")

        try:
            import numpy as np
            from scipy.fft import rfft

            # Use first channel only
            audio_data = indata[:, 0]

            # Calculate RMS to detect if there's actual audio signal
            rms = np.sqrt(np.mean(audio_data ** 2))

            # If signal is below noise threshold, return zeros
            if rms < self.noise_threshold:
                with self._lock:
                    self._latest_spectrum = SpectrumData(
                        bands=[0.0] * self.num_bands,
                        num_bands=self.num_bands
                    )
                return

            # Apply Hanning window to reduce spectral leakage
            window = np.hanning(len(audio_data))
            windowed_data = audio_data * window

            # Perform FFT
            fft_result = rfft(windowed_data)
            magnitudes = np.abs(fft_result)

            # Convert to frequency bands
            bands = self._calculate_bands(magnitudes)

            # Store latest spectrum data (thread-safe)
            with self._lock:
                self._latest_spectrum = SpectrumData(
                    bands=bands,
                    num_bands=self.num_bands
                )

        except Exception as e:
            logging.error(f"Error in audio callback: {e}")

    def _calculate_bands(self, magnitudes):
        """
        Convert FFT magnitudes to frequency bands.
        Uses logarithmic spacing to match human hearing (like Winamp).

        Args:
            magnitudes: FFT magnitude array

        Returns:
            List of band magnitudes
        """
        import numpy as np

        # Logarithmic frequency bands (20Hz to 20kHz)
        # This matches how humans perceive sound (more detail in bass)
        freq_bands = np.logspace(np.log10(20), np.log10(20000), self.num_bands + 1)
        band_magnitudes = []

        for i in range(self.num_bands):
            start_freq = freq_bands[i]
            end_freq = freq_bands[i + 1]

            # Convert frequencies to FFT bin indices
            start_idx = int(start_freq * self.blocksize / self.samplerate)
            end_idx = int(end_freq * self.blocksize / self.samplerate)

            # Ensure valid indices
            start_idx = max(0, start_idx)
            end_idx = min(len(magnitudes), end_idx)

            if start_idx < end_idx:
                # Average magnitude in this frequency range
                band_mag = float(np.mean(magnitudes[start_idx:end_idx]))
            elif start_idx == end_idx and start_idx < len(magnitudes):
                # Narrow frequency range rounds to single bin - use that bin's magnitude
                band_mag = float(magnitudes[start_idx])
            else:
                band_mag = 0.0

            band_magnitudes.append(band_mag)

        return band_magnitudes

    def start(self):
        """Start audio capture and FFT analysis"""
        if self._started:
            logging.warning("Visualizer already started")
            return

        try:
            import sounddevice as sd

            monitor_device = None

            # If device name is explicitly specified, use it
            if self.device_name is not None:
                logging.info(f"Using specified device: {self.device_name}")
                monitor_device = self.device_name
            else:
                # Auto-detect monitor device
                devices = sd.query_devices()

                logging.info("Searching for audio monitor device...")

                # Strategy 1: Look for "monitor" or "loopback" in the name
                for i, dev in enumerate(devices):
                    if dev['max_input_channels'] == 0:
                        continue

                    name_lower = dev['name'].lower()
                    logging.debug(f"Device {i}: {dev['name']} (input channels: {dev['max_input_channels']})")

                    if 'monitor' in name_lower or 'loopback' in name_lower:
                        monitor_device = i
                        logging.info(f"Found monitor device: {dev['name']} (device {i})")
                        break

                # Strategy 2: If on Linux, try "pulse" which uses PulseAudio's default monitor
                if monitor_device is None:
                    try:
                        # Try using "pulse" device which may automatically route to monitor
                        import platform
                        if platform.system() == 'Linux':
                            logging.info("Trying 'pulse' device (PulseAudio default)...")
                            monitor_device = "pulse"
                    except:
                        pass

                if monitor_device is None:
                    logging.warning("=" * 70)
                    logging.warning("WARNING: No monitor/loopback device found!")
                    logging.warning("=" * 70)
                    logging.warning("Monitor devices capture your system's audio OUTPUT.")
                    logging.warning("Without one, the visualizer cannot capture playing audio.")
                    logging.warning("")
                    logging.warning("To find your monitor device:")
                    logging.warning("  1. Run: bash find_monitor_source.sh")
                    logging.warning("  2. Or run: pactl list sources short | grep monitor")
                    logging.warning("")
                    logging.warning("Then specify the device manually:")
                    logging.warning("  visualizer = get_visualizer_provider(device_name='DEVICE_NAME')")
                    logging.warning("=" * 70)

            # Create and start input stream
            self._stream = sd.InputStream(
                device=monitor_device,
                channels=2,
                callback=self._audio_callback,
                blocksize=self.blocksize,
                samplerate=self.samplerate
            )
            self._stream.start()
            self._started = True

            device_str = str(monitor_device) if monitor_device is not None else "default"
            logging.info(f"Audio visualizer started (device={device_str}, bands={self.num_bands}, rate={self.samplerate}Hz, threshold={self.noise_threshold})")

        except Exception as e:
            logging.error(f"Failed to start audio visualizer: {e}")
            import traceback
            logging.error(traceback.format_exc())
            self._started = False

    def stop(self):
        """Stop audio capture and cleanup"""
        if not self._started:
            return

        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            self._started = False
            logging.info("Audio visualizer stopped")
        except Exception as e:
            logging.error(f"Error stopping audio visualizer: {e}")

    def get_spectrum(self) -> Optional[SpectrumData]:
        """Get latest spectrum data (thread-safe)"""
        if not self._started:
            return None

        with self._lock:
            return self._latest_spectrum


class DummyVisualizerProvider(VisualizerProvider):
    """Dummy visualizer provider that returns zeros (fallback)"""

    def __init__(self, num_bands=10):
        self.num_bands = num_bands

    def is_available(self) -> bool:
        """Always available as fallback"""
        return True

    def get_spectrum(self) -> Optional[SpectrumData]:
        """Return zero spectrum"""
        return SpectrumData(
            bands=[0.0] * self.num_bands,
            num_bands=self.num_bands
        )

    def start(self):
        """No-op for dummy provider"""
        logging.warning("Using dummy visualizer provider (no audio analysis)")

    def stop(self):
        """No-op for dummy provider"""
        pass


def get_visualizer_provider(num_bands=10, noise_threshold=0.001, device_name=None) -> VisualizerProvider:
    """
    Factory function to get the best available visualizer provider.
    Tries providers in order of preference:
    1. SoundDevice with FFT (Linux/Windows/Mac with audio input)
    2. Dummy provider (fallback - returns zeros)

    Args:
        num_bands: Number of frequency bands for spectrum analysis
        noise_threshold: Minimum RMS amplitude to consider as signal (0.0 to 1.0)
                        Higher values = less sensitive, filters out more background noise
                        Default 0.001 works for most systems, try 0.01 or 0.1 if needed
        device_name: Specific audio device to use (e.g., "pulse" or PulseAudio source name)
                    If None, will auto-detect monitor device
                    Find your monitor device with: pactl list sources short | grep monitor

    Returns:
        VisualizerProvider instance
    """
    # Try SoundDevice provider first
    try:
        sounddevice_provider = SoundDeviceVisualizerProvider(
            num_bands=num_bands,
            noise_threshold=noise_threshold,
            device_name=device_name
        )
        if sounddevice_provider.is_available():
            logging.info("Using SoundDevice visualizer provider")
            return sounddevice_provider
    except Exception as e:
        logging.error(f"SoundDevice provider initialization failed: {e}")

    # Fallback to dummy provider
    logging.warning("Using dummy visualizer provider (no audio analysis)")
    return DummyVisualizerProvider(num_bands=num_bands)
