# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyCastX is a modular Python stack for rendering dynamic content on LED video walls. The architecture separates content generation (apps) from display infrastructure (utils), using a UDP-based video streaming protocol to send frames from apps to the physical LED matrix.

## Architecture

### Core Components

**utils/** - Display infrastructure shared across all apps:
- `server.py`: UDP server running on the Raspberry Pi with the LED matrix. Receives raw RGB video frames over UDP, reassembles packets using sequence numbers, and renders to the LED matrix using the `rgbmatrix` library.
- `client.py`: UDP client that reads raw RGB video frames from stdin and transmits them over UDP to the server. Splits frames into 1024-byte packets with sequence numbers.

**apps/** - Independent applications that generate video content:
- `spotiamp/`: Winamp-style Spotify visualization using pygame to render the UI
- `scoreboard/`: Placeholder for future sports score display

### Video Pipeline

The system uses a pipe-based architecture:
1. Apps render frames using pygame/PIL to a 384x192 resolution
2. Raw RGB frame data is written to stdout as bytes
3. `client.py` reads from stdin and transmits over UDP
4. `server.py` receives UDP packets and displays on LED matrix

Example: `python main.py | python ../../utils/client.py`

### Spotiamp Architecture

The Spotify visualization app has two independent processes:
- `utils/now-playing.py`: Polls Spotify API every 5 seconds, writes track metadata to `/tmp/now-playing.json`
- `main.py`: Reads metadata from `/tmp/now-playing.json`, renders Winamp-style UI using pygame components

Components system (`components/`):
- `base.py`: Main Winamp UI container with nested sprite classes for each UI element (title bar, buttons, posbar, volume, etc.)
- `text.py`: Text rendering with Marquee scrolling support
- `time.py`: Time display component

Skins system (`skins/base/`): Contains bitmap assets extracted from Winamp skins (BMP format)

## Development Commands

### Setting Up an App

Each app has its own virtual environment:

```bash
cd apps/spotiamp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running Spotiamp

1. Set up Spotify API credentials in `apps/spotiamp/utils/secrets.json` (use `secrets-template.json` as reference)

2. Start the now-playing poller:
```bash
cd apps/spotiamp
source .venv/bin/activate
python utils/now-playing.py
```

3. In a separate terminal, run the visualization:
```bash
cd apps/spotiamp
source .venv/bin/activate
python main.py  # For local preview
# OR
python main.py | python ../../utils/client.py  # To send to LED matrix
```

### Running the LED Server

On the Raspberry Pi with the LED matrix:
```bash
cd utils
python server.py
```

## Network Configuration

The UDP socket is hardcoded in both `client.py` and `server.py`:
- IP: `192.168.68.57` (Raspberry Pi)
- Port: `12000`

Display resolution: 384x192 pixels (6 chained 64x64 LED panels)

## Key Technical Details

- Frame format: Raw RGB bytes, no compression
- UDP packet size: 1024 bytes + 4-byte sequence number header
- Frame rate: 60 FPS (main.py) but only every 5th frame is transmitted to reduce bandwidth
- Spotify polling interval: 5 seconds
- LED matrix configuration: 64x64 panels, chain length 6, parallel 3

## Dependencies

- `pygame`: UI rendering for apps
- `spotipy`: Spotify API client
- `rgbmatrix`: LED matrix driver (server only, requires rpi-rgb-led-matrix library)
- `Pillow`: Image processing
- `redis`: Used for caching/state (in requirements but not actively used in current code)

## Important Notes

- The `now-playing.json` file in `apps/spotiamp/` is a local copy; the app actually reads from `/tmp/now-playing.json`
- Spotify authentication uses OAuth flow with `SpotifyOAuth` - first run will open browser for auth
- The server uses `rgbmatrix` which requires specific hardware (only works on Raspberry Pi with LED matrix HAT)
- Git status shows modified `utils/client.py` and `utils/server.py` - these are the core infrastructure files
