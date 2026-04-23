from dotenv import load_dotenv
load_dotenv()

from randomise_tracks import SpotifyManager

SpotifyManager().copy_stew_to_leftovers()
