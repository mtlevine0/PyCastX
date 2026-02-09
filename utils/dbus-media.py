#!/usr/bin/env python3

import dbus

def main():
    bus = dbus.SessionBus()

    # Find the first active MPRIS player
    players = [
        name for name in bus.list_names()
        if name.startswith("org.mpris.MediaPlayer2.")
    ]

    if not players:
        print("No media players found")
        return

    player_name = players[0]
    obj = bus.get_object(player_name, "/org/mpris/MediaPlayer2")

    props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")

    metadata = props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    status = props.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")
    position = props.Get("org.mpris.MediaPlayer2.Player", "Position")

    title = metadata.get("xesam:title", "Unknown")
    artist = ", ".join(metadata.get("xesam:artist", []))
    duration = metadata.get("mpris:length", 0)  # microseconds

    # Convert to seconds
    pos_sec = position / 1_000_000
    dur_sec = duration / 1_000_000 if duration else 0

    if dur_sec > 0:
        progress = f"{int(pos_sec)}/{int(dur_sec)}s"
    else:
        progress = f"{int(pos_sec)}s"

    print(f"Title   : {title}")
    print(f"Artist  : {artist}")
    print(f"Status  : {status}")
    print(f"Progress: {progress}")

if __name__ == "__main__":
    main()
