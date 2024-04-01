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


class SpotifyRandomiser:

    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIPY_CLIENT_ID,
                client_secret=SPOTIPY_CLIENT_SECRET,
                redirect_uri=SPOTIPY_REDIRECT_URI,
                scope=SPOTIPY_SCOPE,
            )
        )

    def get_liked_tracks(self):
        # Get the current list of liked tracks
        print('Collecting the list of your liked tracks...', end='')
        tracks_liked = []
        results = self.sp.current_user_saved_tracks()
        tracks_liked.extend(results['items'])

        while results['next']:
            results = self.sp.next(results)
            tracks_liked.extend(results['items'])
            print('.', end='')
        print(' done')

        tracks_liked_ids = [track['track']['id'] for track in tracks_liked]
        return tracks_liked_ids

    def get_playlist_tracks(self, playlist_id):
        # Get the current list of tracks in the playlist, these are going to be removed.
        tracks_playlist = []
        results = self.sp.playlist_tracks(playlist_id)
        tracks_playlist.extend(results['items'])

        while results['next']:
            results = self.sp.next(results)
            tracks_playlist.extend(results['items'])

        tracks_playlist_ids = [track['track']['id'] for track in tracks_playlist]
        return tracks_playlist_ids
        
    def get_playlist_name(self, playlist_id):
        results = self.sp.playlist(playlist_id, fields='name')
        return results['name']

    def remove_tracks_from_playlist(self, playlist_id, tracks):
        # Remove all the tracks from the target playlist in batches
        print('Clearing the target playlist...', end='')
        for i in range(0, len(tracks), CHUNK_SIZE):
            chunk_track_ids = tracks[i : i + CHUNK_SIZE]
            self.sp.playlist_remove_all_occurrences_of_items(
                playlist_id, chunk_track_ids
            )
            print('.', end='')
        print(' done')


    def add_tracks_to_playlist(self, playlist_id, tracks):
        # Add the randomized tracks to the playlist in batches
        print('Adding your liked tracks randomly to the playlist...', end='')
        for i in range(0, len(tracks), CHUNK_SIZE):
            chunk_track_ids = tracks[i : i + CHUNK_SIZE]
            self.sp.playlist_add_items(playlist_id, chunk_track_ids)
            print('.', end='')
        print(' done')


    def randomise(self, source, target, exclude=None, max_tracks=None):
        print('Starting program')

        if source == 'liked':
            source_tracks = self.get_liked_tracks()
        else:
            source_tracks = self.get_playlist_tracks(playlist_id=source)
        random.shuffle(source_tracks)

        if exclude:
            if type(exclude) is str:
                exclude = [exclude]
        if exclude:
            for exclusion_playlist_id in exclude:
                removal_tracks = self.get_playlist_tracks(exclusion_playlist_id)
                source_tracks = [track for track in source_tracks if track not in removal_tracks]
        current_tracks = self.get_playlist_tracks(playlist_id=target)
        current_tracks_len = len(current_tracks)
        target_name = self.get_playlist_name(target)

        if current_tracks_len > 0:
            user_input = input(f'Target playlist, {target_name}, contains {current_tracks_len} tracks. Type "X" to confirm overwrite:\n')
            if user_input.upper() != 'X':
                raise ValueError('Target is not empty')
            else:
                self.remove_tracks_from_playlist(playlist_id=target, tracks=current_tracks)

        if max_tracks:
            source_tracks = source_tracks[:max_tracks]
        self.add_tracks_to_playlist(playlist_id=target, tracks=source_tracks)
        print('Program complete.')



def make_nadia_another_playlist():
    """Takes tracks from the staging playlist and puts a selection
    into a target playlist, excluding previous inclusions"""
    SPOTIPY_NADIA_STAGING = os.environ.get('SPOTIPY_NADIA_STAGING')
    SPOTIPY_NADIA_1 = os.environ.get('SPOTIPY_NADIA_1')
    SPOTIPY_NADIA_2 = os.environ.get('SPOTIPY_NADIA_2')

    source = SPOTIPY_NADIA_STAGING_PLAYLIST_ID
    target = SPOTIPY_NADIA_2
    exclude = [SPOTIPY_NADIA_1]
    max_tracks = 20
    sp_rand = SpotifyRandomiser()
    sp_rand.randomise(
        source=source,
        target=target,
        exclude=exclude,
        max_tracks=max_tracks
        )


def randomize_liked_tracks():
    """Takes liked songs and puts them into a target playlist"""
    source = 'liked'
    target = SPOTIPY_RANDOM_PLAYLIST_ID
    exclude = None
    max_tracks = None
    sp_rand = SpotifyRandomiser()
    sp_rand.randomise(source='liked', target=SPOTIPY_RANDOM_PLAYLIST_ID, exclude=exclude, max_tracks=max_tracks)


if __name__ == '__main__':
    randomize_liked_tracks()
    #make_nadia_another_playlist()
