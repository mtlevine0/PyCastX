# Streaming Configuration Guide

Edit `streaming.json` to configure video streaming settings.

## Quick Start

### Enable/Disable Compression

Edit `streaming.json`:
```json
{
  "mode": "codec"   // or "raw"
}
```

- **`codec`** - H.264 compression (~1-4 Mbps, configurable quality)
- **`raw`** - Uncompressed UDP (~20 Mbps, maximum quality)

Then use the unified scripts:
```bash
# Client
./run-streaming.sh

# Server (Pi)
sudo bash ./run-streaming-server.sh
```

The scripts automatically use the correct mode from config!

### Increase Frame Rate

Edit `streaming.json`:
```json
{
  "video": {
    "fps": 20
  },
  "application": {
    "frame_skip": 3
  },
  "encoding": {
    "gop_size": 20
  }
}
```

**Frame rate calculation:**
- App runs at 60 FPS internally
- `frame_skip = 3` → send every 3rd frame = **20 FPS**
- `frame_skip = 4` → send every 4th frame = **15 FPS** (default)
- `frame_skip = 5` → send every 5th frame = **12 FPS**
- `frame_skip = 6` → send every 6th frame = **10 FPS**

**GOP size** should match FPS for 1-second keyframe intervals.

---

### Mode Comparison

| Feature | Codec Mode | Raw Mode |
|---------|-----------|----------|
| **Bandwidth** | ~1-4 Mbps | ~20 Mbps |
| **Quality** | Very good | Perfect |
| **Latency** | ~150-200ms | ~50-100ms |
| **CPU (Client)** | Medium (encoding) | Low |
| **CPU (Server)** | Low-Medium (decoding) | Low |
| **Network** | WiFi OK | Ethernet recommended |
| **Frame rate** | Up to 60 FPS | Up to 60 FPS |

**Use codec mode when:**
- On WiFi or limited bandwidth
- Want configurable quality/bandwidth
- CPU not a concern

**Use raw mode when:**
- On fast Ethernet
- Want absolute minimum latency
- Want perfect quality
- Have 20+ Mbps available

---

## Configuration Options

### Video Settings
```json
"video": {
  "width": 384,        // Display width in pixels
  "height": 192,       // Display height in pixels
  "fps": 15           // Target frame rate
}
```

### Encoding Settings
```json
"encoding": {
  "bitrate": "1M",     // 1M = 1 Mbps, 2M = 2 Mbps, etc.
  "gop_size": 15,      // Keyframe interval (frames)
  "preset": "ultrafast" // ultrafast, superfast, veryfast, faster, fast
}
```

**Bitrate recommendations:**
- `500K` - Very low quality, minimum bandwidth
- `1M` - Good quality for LED matrix (default)
- `2M` - Higher quality, more bandwidth
- `3M` - Best quality, most bandwidth

**Preset options** (speed vs quality):
- `ultrafast` - Fastest encoding, lowest quality (default)
- `superfast` - Very fast encoding
- `veryfast` - Fast encoding, better quality
- `faster` - Balanced
- `fast` - Slower encoding, good quality

**GOP size** (Group of Pictures):
- Should match FPS for 1-second keyframe intervals
- Lower = more keyframes = better error recovery, more bandwidth
- Higher = fewer keyframes = less bandwidth, slower sync

### Network Settings
```json
"network": {
  "server_ip": "192.168.68.57",  // Raspberry Pi IP address
  "server_port": 12001            // TCP port
}
```

### Application Settings
```json
"application": {
  "frame_skip": 4  // Send every Nth frame (60 FPS ÷ N)
}
```

---

## Common Configurations

### Maximum Smoothness (20 FPS)
```json
{
  "video": { "fps": 20 },
  "application": { "frame_skip": 3 },
  "encoding": { "bitrate": "2M", "gop_size": 20 }
}
```
- Smoothest animation
- Higher bandwidth (~2 Mbps)
- More CPU usage

### Balanced (15 FPS) - DEFAULT
```json
{
  "video": { "fps": 15 },
  "application": { "frame_skip": 4 },
  "encoding": { "bitrate": "1M", "gop_size": 15 }
}
```
- Good balance of smoothness and efficiency
- Moderate bandwidth (~1 Mbps)
- Current default

### Power Saving (10 FPS)
```json
{
  "video": { "fps": 10 },
  "application": { "frame_skip": 6 },
  "encoding": { "bitrate": "750K", "gop_size": 10 }
}
```
- Lower frame rate
- Minimum bandwidth (~750 Kbps)
- Less CPU usage on Pi

### Maximum Quality (15 FPS, high bitrate)
```json
{
  "video": { "fps": 15 },
  "application": { "frame_skip": 4 },
  "encoding": {
    "bitrate": "3M",
    "gop_size": 15,
    "preset": "veryfast"
  }
}
```
- Best visual quality
- Higher bandwidth (~3 Mbps)
- Slower encoding

---

## Testing Your Configuration

After editing `streaming.json`:

1. **Restart both scripts** (configuration is loaded at startup)

2. **Check client output:**
   ```
   Loaded config: 384x192 @ 20.0 FPS (skip=3)
   [INFO] Streaming: 20 frames sent, 19.85 FPS
   ```

3. **Check server output:**
   ```
   Expected FPS: 20
   frame= 120 fps=19.8
   ```

4. **Monitor bandwidth:**
   - Should match configured bitrate
   - Client: `[Sender] X bytes sent | 2.05 Mbps`
   - Server: `[Receiver] X bytes received | 2.05 Mbps`

---

## Troubleshooting

### Frame rate too low
- **Cause**: CPU can't keep up with encoding
- **Solution**: Lower FPS, use faster preset, or reduce bitrate

### Stuttering playback
- **Cause**: Network issues or inconsistent frame rate
- **Solution**: Check network quality, try lower FPS

### High latency
- **Cause**: Large buffers or slow encoding
- **Solution**: Use `ultrafast` preset, lower bitrate

### Video quality poor
- **Cause**: Bitrate too low
- **Solution**: Increase bitrate (e.g., 1M → 2M)

### High CPU usage on Pi
- **Cause**: Decoding too demanding
- **Solution**: Lower FPS or resolution

---

## Advanced: Resolution Changes

To change display resolution:

1. **Edit config:**
   ```json
   "video": {
     "width": 768,
     "height": 384,
     "fps": 15
   }
   ```

2. **Update LED matrix configuration** in `utils/server.py`

3. **Adjust pygame window** in app's main.py (done automatically from config)

---

## Notes

- Changes take effect on next restart (not live)
- Frame skip must be calculated for 60 FPS base rate
- GOP size should generally match FPS
- Higher FPS = more bandwidth and CPU usage
- Hardware decoder on Pi supports up to ~30 FPS at this resolution
