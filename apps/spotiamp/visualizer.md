# Winamp VISCOLOR.txt Documentation

## Overview

`VISCOLOR.txt` is a configuration file used in Winamp Classic skins to define the colors for the built-in visualization panel (spectrum analyzer and oscilloscope). Unlike the bitmap-based skinning system used for buttons and controls, the visualization is rendered programmatically using the colors defined in this file.

## File Format

The file contains **24 lines**, where each line specifies an RGB color value followed by an optional comment.

### Line Format
```
R,G,B, // optional comment
```

Where:
- **R** = Red value (0-255)
- **G** = Green value (0-255)
- **B** = Blue value (0-255)
- Comments after `//` are optional but recommended for clarity

### Example VISCOLOR.txt
```
223,223,223, // color 0 = light gray (background)
234,234,234, // color 1 = lighter gray for dots
210,210,210, // color 2 = top of spectrum analyzer
205,205,205, // color 3
200,200,200, // color 4
195,195,195, // color 5
190,190,190, // color 6
185,185,185, // color 7
180,180,180, // color 8
175,175,175, // color 9
170,170,170, // color 10
165,165,165, // color 11
160,160,160, // color 12
155,155,155, // color 13
150,150,150, // color 14
145,145,145, // color 15
140,140,140, // color 16
135,135,135, // color 17 = bottom of spectrum analyzer
210,210,210, // color 18 = oscilloscope wave 1 (trough)
174,174,174, // color 19 = oscilloscope wave 2 (slightly dimmer)
138,138,138, // color 20 = oscilloscope wave 3
102,102,102, // color 21 = oscilloscope wave 4
66,66,66,    // color 22 = oscilloscope wave 5 (crest)
200,200,200, // color 23 = analyzer peak dots
```

## Line-by-Line Breakdown

### Background & Base Colors (Rows 0-1)

| Row | Purpose | Description |
|-----|---------|-------------|
| 0 | Background color | The background color of the entire visualization area. Visible when no audio is playing or between bars in spectrum analyzer mode. |
| 1 | Dot color | Color of decorative dots that appear in the visualization area (aesthetic element). |

### Spectrum Analyzer Colors (Rows 2-17)

The spectrum analyzer uses **16 color levels** (rows 2-17) to create a gradient effect showing frequency intensity.

| Row | Purpose | Description |
|-----|---------|-------------|
| 2 | Peak/Top color | The highest part of the frequency bar - appears at maximum intensity |
| 3-16 | Gradient levels | Intermediate colors creating smooth gradation from peak to base |
| 17 | Base/Bottom color | The lowest visible part of the frequency bar |

**How it works:**
- When audio plays, the spectrum analyzer displays vertical bars for different frequency bands
- Row 2 colors the very top of tall bars (highest intensity)
- Row 17 colors the bottom portion of bars (lowest visible intensity)
- Rows 3-16 fill in between, creating a smooth color gradient
- By varying these colors, you can create effects like:
  - Fire effect: red at top (row 2) → yellow → orange → dark red at bottom (row 17)
  - Ice effect: bright cyan at top → darker blue at bottom
  - Monochrome: same color at different brightness levels

### Oscilloscope Colors (Rows 18-22)

The oscilloscope displays the audio waveform using **5 color levels** (rows 18-22).

| Row | Purpose | Description |
|-----|---------|-------------|
| 18 | Trough color | Color at the lowest points (troughs) of the waveform |
| 19 | Intermediate level 1 | |
| 20 | Intermediate level 2 | Middle of the waveform |
| 21 | Intermediate level 3 | |
| 22 | Crest color | Color at the highest points (crests) of the waveform |

**How it works:**
- The oscilloscope shows the raw audio waveform as it oscillates
- Row 18 colors the bottom of the wave
- Row 22 colors the top of the wave
- Rows 19-21 create smooth transitions between extremes

### Peak Marker (Row 23)

| Row | Purpose | Description |
|-----|---------|-------------|
| 23 | Peak dots | Color used to mark the last peak value in spectrum analyzer mode. These are small markers that remain at the highest point each frequency band has recently reached, slowly falling down as the audio intensity decreases. |

## Visualization Modes

Winamp's built-in visualization can display in two modes:

1. **Spectrum Analyzer** - Uses rows 0, 1, 2-17, and 23
2. **Oscilloscope** - Uses rows 0, 1, and 18-22

Users switch between these modes via Winamp's interface (right-click on visualization area).

## Important Notes

### Color Theory
- RGB values range from 0 (no intensity) to 255 (full intensity)
- Black = 0,0,0
- White = 255,255,255
- For gradients, increment or decrement values smoothly between rows

### Common Patterns

**Fire Effect:**
```
255,0,0,     // row 2 - bright red peak
255,64,0,    // row 3 - red-orange
255,128,0,   // row 4 - orange
255,192,0,   // row 5 - yellow-orange
...
128,0,0,     // row 17 - dark red base
```

**Ice Effect:**
```
0,255,255,   // row 2 - bright cyan peak
0,224,255,   // row 3
0,192,255,   // row 4
...
0,64,128,    // row 17 - dark blue base
```

**Monochrome Gradient:**
```
255,255,255, // row 2 - white peak
240,240,240, // row 3
225,225,225, // row 4
...
64,64,64,    // row 17 - dark gray base
```

### Rendering Behavior

- The visualization area is defined by the `main.bmp` skin file
- When no audio is playing, only row 0 (background color) is visible
- The visualization area is typically 76 pixels wide × 16 pixels tall in the classic Winamp interface
- Colors are applied in real-time as audio plays
- The engine performs interpolation between the defined color rows for smooth gradients

### Transparency

The background color (row 0) is always rendered as a solid color. Unlike other Winamp skin elements, the visualization area cannot be made transparent, though the surrounding main window can be using `region.txt`.

### Missing File Behavior

If `VISCOLOR.txt` is not present in a skin, Winamp uses hardcoded default values:
- Background: Black (0,0,0)
- This is redrawn only at track changes
- Between redraws, the underlying `main.bmp` may be visible if the window is refreshed

## Development Tools

Several tools exist to help create `VISCOLOR.txt` files:

- **Vis Toolkit** - Visual color picker for generating VISCOLOR.txt
- **Viscolor Utility** by Eugene Loginov - Simple utility for creating the file
- **Sublime Text Winamp Skin Developer Package** - Includes scaffolding snippets for VISCOLOR.txt

## Technical Details

### File Location
Place `VISCOLOR.txt` in the root of your skin directory:
```
MySkin.wsz (or extracted MySkin/ folder)
├── main.bmp
├── cbuttons.bmp
├── VISCOLOR.TXT
├── pledit.txt
└── ... other skin files
```

### Case Sensitivity
Filename is typically uppercase `VISCOLOR.TXT` but Winamp may accept lowercase on case-insensitive filesystems.

### Reloading
After editing `VISCOLOR.txt`, press **F5** in Winamp to reload the skin and see changes immediately.

## References

- Winamp skin format: Classic skins (.wsz files are renamed .zip archives)
- Related files: `pledit.txt` (playlist colors), `region.txt` (transparency masks)
- The spectrum analyzer typically displays 15-20 frequency bands
- Peak dots (row 23) have a fall-off rate that can be affected by Winamp settings but not by VISCOLOR.txt

## Example Use Cases

### Creating a "Classic Winamp Green" Look
```
0,0,0,       // black background
0,255,0,     // green dots
0,255,0,     // bright green peak
0,240,0,     // 
0,225,0,     // gradient
...
0,64,0,      // dark green base
```

### Creating LED-Style Segments
Use distinct colors without smooth gradients:
```
0,0,0,       // black background  
255,255,255, // white dots
255,0,0,     // red peak
255,0,0,     // red
255,0,0,     // red
255,128,0,   // orange
255,128,0,   // orange
255,255,0,   // yellow
...
```

This gives a segmented "LED bar graph" appearance rather than smooth gradients.

---

**Version History:**
- Winamp 2.x - Original implementation
- Remains unchanged through Winamp 5.x series
- Webamp (browser implementation) also supports VISCOLOR.txt parsing
