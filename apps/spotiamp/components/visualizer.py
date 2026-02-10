import pygame

class Visualizer(pygame.sprite.Sprite):
    """
    Winamp-style spectrum analyzer visualization component.
    Displays vertical frequency bars with gradient colors from VISCOLOR.TXT
    """

    def __init__(self, skin, width=76, height=16, num_bands=16, position=(24, 43)):
        """
        Initialize the spectrum analyzer visualizer.

        Args:
            skin: Skin directory name
            width: Width of visualizer area in pixels (default 76 for Winamp)
            height: Height of visualizer area in pixels (default 16 for Winamp)
            num_bands: Number of frequency bands to display (default 16)
            position: (x, y) position in the UI where visualizer is drawn
        """
        super().__init__()
        self.width = width
        self.height = height
        self.num_bands = num_bands
        self.position = position

        # Create surface with per-pixel alpha for proper transparency
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Load background for this area from MAIN.BMP to clear between frames
        try:
            main_image = pygame.image.load(f"skins/{skin}/MAIN_no_logo.png")
            self.background = main_image.subsurface(pygame.Rect(position[0], position[1], width, height)).copy()
        except Exception as e:
            print(f"Warning: Could not load visualizer background: {e}")
            # Fallback to black background
            self.background = pygame.Surface((width, height))
            self.background.fill((0, 0, 0))

        # Load colors from VISCOLOR.TXT
        self.colors = self._load_viscolor(skin)

        # Extract color ranges from VISCOLOR.TXT
        self.spectrum_colors = self.colors[2:18]  # Rows 2-17 (16 colors for gradient)
        self.peak_color = self.colors[23]

        # Current spectrum levels (0.0 to 1.0) for each band
        self.levels = [0.0] * num_bands

        # Peak markers for each band (y position in pixels, from top)
        self.peaks = [float(height)] * num_bands
        self.peak_fall_rate = 0.3  # pixels per frame

        # Smoothing parameters for natural decay
        self.decay_rate = 0.03   # How fast bars fall (lower = slower decay)
        self.rise_rate = 0.8     # How fast bars rise (higher = more responsive)

        # Calculate band width and spacing
        total_spacing = num_bands - 1  # 1 pixel between each bar
        available_width = width - total_spacing
        self.band_width = max(1, available_width // num_bands)
        self.band_spacing = 1

    def _load_viscolor(self, skin):
        """Load and parse VISCOLOR.TXT file"""
        colors = []
        try:
            with open(f"skins/{skin}/VISCOLOR.TXT", 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse "R,G,B, // comment" format
                    color_part = line.split('//')[0].strip()
                    if color_part:
                        rgb_values = [int(x.strip()) for x in color_part.rstrip(',').split(',') if x.strip()]
                        if len(rgb_values) >= 3:
                            colors.append(tuple(rgb_values[:3]))
        except Exception as e:
            print(f"Error loading VISCOLOR.TXT: {e}")
            # Fallback to default grayscale colors
            colors = [(i * 10, i * 10, i * 10) for i in range(24)]

        # Ensure we have exactly 24 colors
        while len(colors) < 24:
            colors.append((0, 0, 0))

        return colors[:24]

    def move(self, spectrum_data):
        """
        Update visualization with new spectrum data.

        Args:
            spectrum_data: SpectrumData object with bands (list of floats 0.0-1.0)
                          or None if no data available
        """
        if spectrum_data is None:
            # No data - decay current levels toward zero
            self.levels = [max(0.0, level - self.decay_rate) for level in self.levels]
        else:
            # Get normalized bands from spectrum data
            if hasattr(spectrum_data, 'normalized_bands'):
                bands = spectrum_data.normalized_bands
            else:
                bands = spectrum_data.bands if hasattr(spectrum_data, 'bands') else []

            # Match number of bands (interpolate if needed)
            if len(bands) != self.num_bands:
                target_bands = self._interpolate_bands(bands, self.num_bands)
            else:
                target_bands = list(bands)

            # Apply smoothing - don't jump directly to new values
            # This creates natural decay even when audio stops abruptly
            for i in range(self.num_bands):
                target = target_bands[i]
                current = self.levels[i]

                if target > current:
                    # Rising - respond quickly to new audio
                    self.levels[i] = min(target, current + self.rise_rate)
                else:
                    # Falling - decay gradually for natural look
                    self.levels[i] = max(target, current - self.decay_rate)

        # Update peak markers
        for i, level in enumerate(self.levels):
            # Calculate current bar height in pixels
            bar_height_pixels = level * self.height
            bar_top_y = self.height - bar_height_pixels  # y position from top

            # Update peak if current level exceeds it (lower y = higher bar)
            if bar_top_y < self.peaks[i]:
                self.peaks[i] = bar_top_y
            else:
                # Let peak fall slowly
                self.peaks[i] = min(self.peaks[i] + self.peak_fall_rate, self.height)

    def _interpolate_bands(self, bands, target_count):
        """Interpolate band data to match target number of bands"""
        if not bands or len(bands) == 0:
            return [0.0] * target_count

        if len(bands) == target_count:
            return list(bands)

        result = []
        for i in range(target_count):
            # Map target index to source index with linear interpolation
            if target_count == 1:
                src_idx = 0
            else:
                src_idx = i * (len(bands) - 1) / (target_count - 1)

            src_idx_low = int(src_idx)
            src_idx_high = min(src_idx_low + 1, len(bands) - 1)

            # Linear interpolation
            frac = src_idx - src_idx_low
            value = bands[src_idx_low] * (1 - frac) + bands[src_idx_high] * frac
            result.append(max(0.0, min(1.0, value)))  # Clamp to [0, 1]

        return result

    def draw(self, surface):
        """
        Render the spectrum analyzer to the given surface.

        Args:
            surface: pygame.Surface to draw on
        """
        # First, clear the visualizer area on the base surface with the background
        surface.blit(self.background, self.position)

        # Clear our drawing surface with fully transparent background
        self.surface.fill((0, 0, 0, 0))

        # Draw each frequency band as a vertical bar
        for i in range(self.num_bands):
            # Calculate bar position
            x = i * (self.band_width + self.band_spacing)

            # Ensure we don't exceed surface width
            if x + self.band_width > self.width:
                break

            # Calculate bar height based on level (0.0 to 1.0)
            level = self.levels[i]
            bar_height_pixels = int(level * self.height)

            if bar_height_pixels > 0:
                # Draw bar from bottom up with gradient colors
                # Winamp style: top of bar (peak) uses row 2, bottom uses row 17
                for pixel_y in range(bar_height_pixels):
                    # Calculate how far from bottom we are (0 = bottom, bar_height = top)
                    progress_from_bottom = pixel_y / bar_height_pixels

                    # Map to color index (0 = row 17/bottom, 15 = row 2/top)
                    # Reverse the index so top is brightest
                    color_idx = int(progress_from_bottom * (len(self.spectrum_colors) - 1))
                    color_idx = len(self.spectrum_colors) - 1 - color_idx  # Reverse
                    color_idx = max(0, min(color_idx, len(self.spectrum_colors) - 1))

                    color = self.spectrum_colors[color_idx]

                    # Calculate y position (draw from bottom up)
                    y_pos = self.height - pixel_y - 1

                    # Draw horizontal line for this pixel row
                    pygame.draw.rect(self.surface, color,
                                   (x, y_pos, self.band_width, 1))

            # Draw peak dot if it's visible
            peak_y = int(self.peaks[i])
            if 0 <= peak_y < self.height and bar_height_pixels > 0:
                pygame.draw.rect(self.surface, self.peak_color,
                               (x, peak_y, self.band_width, 1))

        # Blit the spectrum bars to target surface at the visualizer position
        surface.blit(self.surface, self.position)
