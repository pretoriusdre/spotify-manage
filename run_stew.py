from dotenv import load_dotenv
load_dotenv()

from randomise_tracks import SpotifyManager

SpotifyManager().populate_from_database()

SpotifyManager().randomise_liked_tracks(require_confirmation=False)
