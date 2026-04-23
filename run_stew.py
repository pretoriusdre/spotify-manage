from dotenv import load_dotenv
load_dotenv()

from randomise_tracks import SpotifyManager

manager = SpotifyManager()
manager.cook_perpetual_stew()
manager.copy_stew_to_leftovers()
manager.randomise_liked_tracks(require_confirmation=False)
