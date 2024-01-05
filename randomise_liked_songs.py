import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

# Refer to .env file for these
SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')
SPOTIPY_USERNAME = os.environ.get('SPOTIPY_USERNAME')
SPOTIPY_RANDOM_PLAYLIST_ID = os.environ.get('SPOTIPY_RANDOM_PLAYLIST_ID')

# Other constants
SPOTIPY_SCOPE = 'user-library-read playlist-modify-public playlist-modify-private user-library-modify'
CHUNK_SIZE = 100


print('Starting program')

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SPOTIPY_SCOPE,
    )
)

# Get the current list of liked songs
print('Collecting the list of your liked tracks...', end='')
tracks_liked = []
results = sp.current_user_saved_tracks()
tracks_liked.extend(results['items'])
print(' done')


while results['next']:
    results = sp.next(results)
    tracks_liked.extend(results['items'])
    print('.', end='')
print(' done')

tracks_liked_ids = [track['track']['id'] for track in tracks_liked]

# Shuffle the list
random.shuffle(tracks_liked_ids)

# Get the current list of tracks in the playlist, these are going to be removed.
tracks_playlist = []
results = sp.playlist_tracks(SPOTIPY_RANDOM_PLAYLIST_ID)
tracks_playlist.extend(results['items'])

while results['next']:
    results = sp.next(results)
    tracks_playlist.extend(results['items'])

tracks_playlist_ids = [track['track']['id'] for track in tracks_playlist]

# Remove all the tracks from the target playlist in batches
print('Clearing the target playlist...', end='')
for i in range(0, len(tracks_playlist_ids), CHUNK_SIZE):
    chunk_track_ids = tracks_playlist_ids[i : i + CHUNK_SIZE]
    sp.playlist_remove_all_occurrences_of_items(
        SPOTIPY_RANDOM_PLAYLIST_ID, chunk_track_ids
    )
    print('.', end='')
print(' done')

# Add the randomized tracks to the playlist in batches
print('Adding your liked songs randomly to the playlist...', end='')
for i in range(0, len(tracks_liked_ids), CHUNK_SIZE):
    chunk_track_ids = tracks_liked_ids[i : i + CHUNK_SIZE]
    sp.playlist_add_items(SPOTIPY_RANDOM_PLAYLIST_ID, chunk_track_ids)
    print('.', end='')
print(' done')


print('Program complete.')
