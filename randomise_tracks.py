import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
import json
from pathlib import Path

from spotify_database import SpotifyDatabaseWrapper

load_dotenv()

# Refer to .env file for these
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')
SPOTIFY_USERNAME = os.environ.get('SPOTIFY_USERNAME')

SPOTIFY_RANDOM_PLAYLIST_ID = os.environ.get('SPOTIFY_RANDOM_PLAYLIST_ID')
SPOTIFY_DB_PLAYLIST_ID     = os.environ.get('SPOTIFY_INFINITE_STEW_PLAYLIST_ID')
SPOTIFY_DB_N_TRACKS              = os.environ.get('SPOTIFY_DB_N_TRACKS')
SPOTIFY_DB_RETAIN_TRACKS         = os.environ.get('SPOTIFY_DB_RETAIN_TRACKS')
SPOTIFY_LEFTOVER_STEW_PLAYLIST_ID = os.environ.get('SPOTIFY_LEFTOVER_INFINITE_STEW_PLAYLIST_ID')

# Other constants
SPOTIFY_SCOPE = 'user-library-read playlist-modify-public playlist-modify-private user-library-modify'
CHUNK_SIZE = 100

# Class to randomise spotify playlists and do other things also
class SpotifyManager:
    """Randomise spotify playlists"""
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SPOTIFY_SCOPE,
            )
        )
        self.output_directory = Path('output_files')

    def get_liked_tracks(self):
        # Get the current list of liked tracks
        print('Collecting the list of your liked tracks...', end='')
        liked_tracks = []
        results = self.sp.current_user_saved_tracks()
        liked_tracks.extend(results['items'])

        while results['next']:
            results = self.sp.next(results)
            liked_tracks.extend(results['items'])
            print('.', end='')
        print(' done')

        return liked_tracks

    def delete_liked_dupe_tracks(self, track_ids):

        user_input = input(f'You are about to delete {len(track_ids)} from your liked tracks. Are you sure?:\n')
        if user_input.upper() != 'X':
            raise ValueError('Aborted')
        else:
            self.sp.current_user_saved_tracks_delete(tracks=track_ids)

    def get_playlist_tracks(self, playlist_id):
        # Get the current list of tracks in the playlist, these are going to be removed.
        playlist_tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        playlist_tracks.extend(results['items'])

        while results['next']:
            results = self.sp.next(results)
            playlist_tracks.extend(results['items'])

        return playlist_tracks

    def get_track_id(self, track):
        return track['track']['id']

    def get_track_ids(self, tracks):
        return [self.get_track_id(track) for track in tracks]
        
    def get_track_metadata(self, track):
        uri = track['track']['uri']
        metadata = {
            'uri' : track['track']['uri'],
            'artists' : ', '.join([artist['name'] for artist in track['track']['artists']]),
            'name' : track['track']['name'],
            'album' : track['track']['album']['name'],
            'release_date' : track['track']['album']['release_date'],
            'popularity' : track['track']['popularity'],
            'duration_ms' : track['track']['duration_ms'],
            'type' : track['track']['type'],
            'explicit' : track['track']['explicit'],
            'url' : track['track']['external_urls']['spotify'],
            'hyperlink' : f'=HYPERLINK("{uri}", "Link")'
        }
        return metadata

    def get_tracks_metadata(self, tracks):
        return [self.get_track_metadata(track) for track in tracks]

    def get_tracks_metadata_df(self, tracks):
        df = pd.DataFrame.from_records(self.get_tracks_metadata(tracks))
        return df

    def get_tracks_metadata_duplicates_df(self, tracks):
        df = self.get_tracks_metadata_df(tracks)
        return df[df.duplicated(subset=['artists', 'name'], keep=False)]


    def get_playlist_name(self, playlist_id):
        results = self.sp.playlist(playlist_id, fields='name')
        return results['name']


    def remove_track_ids_from_playlist(self, playlist_id, track_ids):
        # Remove all the tracks from the target playlist in batches
        print('Removing old tracks from the playlist...', end='')
        for i in range(0, len(track_ids), CHUNK_SIZE):
            chunk_track_ids = track_ids[i : i + CHUNK_SIZE]
            self.sp.playlist_remove_all_occurrences_of_items(
                playlist_id, chunk_track_ids
            )
            print('.', end='')
        print(' done')


    def add_track_ids_to_playlist(self, playlist_id, track_ids):
        # Add the randomized tracks to the playlist in batches
        print('Adding tracks randomly to the playlist...', end='')
        for i in range(0, len(track_ids), CHUNK_SIZE):
            track_ids_chunk = track_ids[i : i + CHUNK_SIZE]
            self.sp.playlist_add_items(playlist_id, track_ids_chunk)
            print('.', end='')
        print(' done')


    def randomise(self, source, target, exclude_playlist_ids=None, include_track_ids=None, max_tracks=None, require_confirmation=True):
        print('Starting program')

        include_track_ids = include_track_ids or []

        if source == 'liked':
            source_tracks = self.get_liked_tracks()
        else:
            source_tracks = self.get_playlist_tracks(playlist_id=source)
        
        source_track_ids = self.get_track_ids(source_tracks)

        random.shuffle(source_track_ids)

        if exclude_playlist_ids:
            if type(exclude_playlist_ids) is str:
                exclude_playlist_ids = [exclude_playlist_ids]

            for exclude_playlist_id in exclude_playlist_ids:
                excluded_tracks = self.get_playlist_tracks(exclude_playlist_id)
                excluded_track_ids = self.get_track_ids(excluded_tracks)
                source_track_ids = [track_id for track_id in source_track_ids if track_id not in excluded_track_ids]

        current_tracks = self.get_playlist_tracks(playlist_id=target)
        current_track_ids = self.get_track_ids(current_tracks)
        current_track_ids_len = len(current_track_ids)

        target_name = self.get_playlist_name(target)

        if current_track_ids_len > 0:
            if require_confirmation:
                user_input = input(f'Target playlist, {target_name}, contains {current_track_ids_len} tracks. Type "X" to confirm overwrite:\n')
                if user_input.upper() != 'X':
                    raise ValueError('Target is not empty')
            self.remove_track_ids_from_playlist(playlist_id=target, track_ids=current_track_ids)

        source_track_ids = include_track_ids + [track_id for track_id in source_track_ids if track_id not in include_track_ids]

        print(f'Number of source tracks after exclusions: {len(source_track_ids)}')
        if max_tracks:
            source_track_ids = source_track_ids[:max_tracks]
        self.add_track_ids_to_playlist(playlist_id=target, track_ids=source_track_ids)
        print('Program complete.')


    def randomise_liked_tracks(self, require_confirmation=True):
        """Takes liked songs and puts them into a target playlist"""
        source = 'liked'
        target = SPOTIFY_RANDOM_PLAYLIST_ID
        exclude_playlist_ids = None
        include_track_ids = None
        max_tracks = None

        self.randomise(
            source=source,
            target=target,
            exclude_playlist_ids=exclude_playlist_ids,
            include_track_ids=include_track_ids,
            max_tracks=max_tracks,
            require_confirmation=require_confirmation
            )
  

    def get_playlist_intersection(self, left_playlists, right_playlists):

        with open('playlists.json', 'r') as f:
            playlists = json.load(f)

        left_tracks = []
        right_tracks = []

        for playlist in left_playlists:
            tracks = self.get_playlist_tracks(playlist)
            left_tracks.extend(tracks)

        for playlist in right_playlists:
            tracks = self.get_playlist_tracks(playlist)
            track_ids = self.get_track_ids(tracks)
            right_tracks.extend(tracks)

        df_left = self.get_tracks_metadata_df(left_tracks)
        df_right =self.get_tracks_metadata_df(right_tracks)

        df_merge = df_left.merge(df_right, on='uri', how='outer', indicator=True)

        return df_merge


    def make_someone_another_playlist(self):
        """Takes tracks from the staging playlist and puts a selection
        into a new playlist, excluding previous inclusions"""

        with open('make_someone_another_playlist.json', 'r') as f:
            playlists = json.load(f)

        source = list(playlists['source_playlists'].keys())[0]
        target = list(playlists['target_playlist'].keys())[0]
        exclude_playlist_ids = list(playlists['previous_playlists'].keys())
        include_track_ids = list(playlists['include_track_ids'].keys())

        received_playlists = list(playlists['received_playlists'].keys())

        max_tracks = 20

        self.randomise(
            source=source,
            target=target,
            exclude_playlist_ids=exclude_playlist_ids,
            include_track_ids=include_track_ids,
            max_tracks=max_tracks,
            )

        all_output_playlists = exclude_playlist_ids + [target]
        all_track_metadata = []

        for playlist in all_output_playlists:
            playlist_name = self.get_playlist_name(playlist)
            tracks = self.get_playlist_tracks(playlist)
            df = self.get_tracks_metadata_df(tracks)
            df['playlist'] = playlist
            df['playlist_name'] = playlist_name
            all_track_metadata.append(df)

        df_output_tracks = pd.concat(all_track_metadata)

        df_source_tracks = self.get_tracks_metadata_df(self.get_playlist_tracks(source))
        df_output_tracks = df_output_tracks.merge(df_source_tracks, on='uri', how='outer', suffixes=('', '_source'), indicator=True)

        output_file = self.output_directory / 'their_playlist_summary.xlsx'
        df_output_tracks.to_excel(output_file, index=False)
        os.startfile(output_file)


    @staticmethod
    def _compute_weights(df):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        def row_weight(row):
            if pd.isnull(row['last_added_at']) or row['times_added'] == 0:
                return 1.0
            try:
                last = pd.to_datetime(row['last_added_at'], utc=True)
                days_since = (now - last).days
            except Exception:
                return 1.0
            penalty = row['times_added'] / (1 + days_since / 30)
            return 1.0 / (1 + penalty)

        return df.apply(row_weight, axis=1)

    def cook_perpetual_stew(self, n=None, playlist_id=None):
        if playlist_id is None:
            playlist_id = SPOTIFY_DB_PLAYLIST_ID
        if not playlist_id:
            raise ValueError("Set SPOTIFY_INFINITE_STEW_PLAYLIST_ID in .env")

        if n is None:
            n = int(SPOTIFY_DB_N_TRACKS) if SPOTIFY_DB_N_TRACKS else int(input("How many tracks to add from the database? "))

        db = SpotifyDatabaseWrapper()
        df = db.get_tracks_for_weighted_selection()

        if len(df) == 0:
            print("No eligible tracks found in database.")
            return

        current_tracks = self.get_playlist_tracks(playlist_id)
        current_ids = self.get_track_ids(current_tracks)
        retain_n = int(SPOTIFY_DB_RETAIN_TRACKS) if SPOTIFY_DB_RETAIN_TRACKS else 1
        kept_ids = []
        if current_ids:
            kept_ids = random.sample(current_ids, min(retain_n, len(current_ids)))
            print(f"Keeping {len(kept_ids)} existing track(s), removing {len(current_ids) - len(kept_ids)} others.")

        if current_ids:
            self.remove_track_ids_from_playlist(playlist_id, current_ids)

        kept_uris = {f"spotify:track:{tid}" for tid in kept_ids}
        if kept_uris:
            df = df[~df['uri'].isin(kept_uris)]

        n = min(n, len(df))
        weights = self._compute_weights(df)
        selected_df = df.sample(n=n, weights=weights / weights.sum(), replace=False)
        selected_uris = selected_df['uri'].tolist()
        selected_ids = [uri.split(':')[-1] for uri in selected_uris]

        all_ids = kept_ids + selected_ids
        random.shuffle(all_ids)
        self.add_track_ids_to_playlist(playlist_id, all_ids)
        db.update_selected_tracks(selected_uris)
        kept_uris = [f"spotify:track:{tid}" for tid in kept_ids]
        db.save_stew_history(kept_uris + selected_uris)
        print("cook_perpetual_stew complete.")

    def copy_stew_to_leftovers(self, days=7):
        playlist_id = SPOTIFY_LEFTOVER_STEW_PLAYLIST_ID
        if not playlist_id:
            raise ValueError("Set SPOTIFY_LEFTOVER_INFINITE_STEW_PLAYLIST_ID in .env")

        db = SpotifyDatabaseWrapper()
        df = db.get_recent_stew_tracks(days=days)

        if df.empty:
            print(f"No stew tracks found in the last {days} days.")
            return

        track_ids = [uri.split(':')[-1] for uri in df['uri']]
        print(f"Found {len(track_ids)} track(s) from the last {days} days.")

        current_tracks = self.get_playlist_tracks(playlist_id)
        current_ids = self.get_track_ids(current_tracks)
        if current_ids:
            self.remove_track_ids_from_playlist(playlist_id, current_ids)

        self.add_track_ids_to_playlist(playlist_id, track_ids)
        print("copy_stew_to_leftovers complete.")

    def main(self):

        message = """
        Spotify Manager.

            - Type 'L' to randomise [L]iked songs, saving to the target playlist.
            - Type 'R' to get random [R]ecommendations.
            - Type 'S' to make [S]omeone another playlist, drawing tracks from their staging area.
            - Type 'D' to populate the [D]atabase playlist with weighted-random tracks.

        """

        result = input(message)

        if result.upper() == 'L':
            self.randomise_liked_tracks()
        elif result.upper() == 'S':
            self.make_someone_another_playlist()
        elif result.upper() == 'D':
            self.cook_perpetual_stew()

        #spotipy_manager.delete_liked_dupe_tracks()



if __name__ == '__main__':
    spotipy_manager = SpotifyManager()
    spotipy_manager.main()

