import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import json
from progressbar import Percentage, Bar
import progressbar

# Set up authentication
secrets = json.load(open("./secrets.json", 'r'))
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=secrets["client_id"],
    client_secret=secrets["client_secret"],
    redirect_uri=secrets["redirect_uri"],
    scope=secrets["scope"]
))

def get_currently_playing():
    current_track = sp.current_user_playing_track()
    if current_track and current_track["is_playing"]:
        track = current_track["item"]["name"]
        artist = ", ".join(artist["name"] for artist in current_track["item"]["artists"])
        progress_percent = float(current_track["progress_ms"]) / float(current_track["item"]["duration_ms"]) * 100
    return {"progress_percent": progress_percent, "track": track, "artist": artist, "duration_ms": int(current_track["item"]["duration_ms"]), "progress_ms": int(current_track["progress_ms"]) }

if __name__ == "__main__":
    now = get_currently_playing()
    widgets = ['Now Playing: ' + now['artist'] + ' - ' + now['track'], Percentage(), ' ', Bar()]
    bar = progressbar.ProgressBar(initial_value=int(now['progress_percent']), maxval=100, widgets=widgets).start()

    while True:
        updated_track = get_currently_playing()
        with open('/tmp/now-playing.json', 'w') as file:
            file.write(json.dumps(updated_track))
        if now['track'] != updated_track['track']:
            now = updated_track
            widgets = ['Now Playing: ' + now['artist'] + ' - ' + now['track'], Percentage(), ' ', Bar()]
            bar = progressbar.ProgressBar(initial_value=int(now['progress_percent']), maxval=100, widgets=widgets).start()
    
        progress_precent = updated_track['progress_percent']
        bar.update(progress_precent)
        time.sleep(5)
