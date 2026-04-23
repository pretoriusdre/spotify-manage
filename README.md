# spotify-manage

Tools to manage Spotify playlists via the Spotify API.

## Scripts

### `run_stew.py` — daily automation
Runs the full daily pipeline without interaction. Intended for cron.
1. **Cook perpetual stew** — picks weighted-random tracks from the local database and refreshes the perperual stew playlist
2. **Copy stew leftovers** — copies the last 7 days of stew tracks to a separate leftovers playlist
3. **Randomise liked songs** — shuffles all liked songs into a target playlist

### `copy_stew_leftovers.py`
Standalone script to copy the last 7 days of stew history to the leftovers playlist. Tracks are ordered chronologically by first appearance.

### `randomise_tracks.py` — interactive menu
Run directly for manual operations:
- `L` — randomise liked songs into the target playlist
- `S` — make someone another playlist (draws from a staging playlist, excludes previous selections)
- `D` — manually trigger perpetual stew

## Environment variables

Copy `.env sample` to `.env` and fill in the values.

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | API client ID from the [Spotify developer dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET` | API client secret |
| `SPOTIFY_REDIRECT_URI` | OAuth redirect URI (must match what's set in the dashboard) |
| `SPOTIFY_USERNAME` | Your Spotify username |
| `SPOTIFY_RANDOM_PLAYLIST_ID` | Target playlist for randomised liked songs |
| `SPOTIFY_INFINITE_STEW_PLAYLIST_ID` | Target playlist for the perpetual stew |
| `SPOTIFY_LEFTOVER_INFINITE_STEW_PLAYLIST_ID` | Target playlist for last week's stew tracks |
| `SPOTIFY_DATABASE_PATH` | Path to the SQLite database (defaults to `spotify-database.db` in cwd) |
| `SPOTIFY_DB_N_TRACKS` | Number of tracks to add per stew run (prompts if unset) |
| `SPOTIFY_DB_RETAIN_TRACKS` | Tracks to keep from the previous stew run (default: 1) |
| `NTFY_TOPIC` | [ntfy.sh](https://ntfy.sh) topic for failure push notifications |

The `.env` file, `.cache` (OAuth token), and `spotify-database.db` are gitignored and must never be committed.

## Setup

```bash
uv sync
# copy and fill in .env
python randomise_tracks.py
```

First run will open a browser for Spotify OAuth. The token is cached in `.cache`.

## Raspberry Pi deployment

The repo includes `run_stew.sh`, a cron wrapper that runs the daily pipeline and sends a push notification on failure via [ntfy.sh](https://ntfy.sh).

**One-time setup on the Pi:**

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.14
uv python install 3.14

# Clone and install
git clone https://github.com/pretoriusdre/spotify-manage.git ~/spotify-manage
cd ~/spotify-manage
uv sync
```

Copy the following files from your local machine (these are not in the repo):
```
.env
.cache
spotify-database.db
```

Update `SPOTIFY_DATABASE_PATH` in the Pi's `.env` to an absolute path, e.g. `/root/spotify-manage/spotify-database.db`.

**Cron job** (runs daily at 20:00 local time — adjust UTC offset as needed):
```
0 12 * * * /bin/bash /root/spotify-manage/run_stew.sh
```

**Updating the Pi:**
```bash
ssh root@raspberrypi "cd ~/spotify-manage && git pull"
```

**Failure notifications:** Install the [ntfy app](https://ntfy.sh) on your phone and subscribe to your `NTFY_TOPIC`. The Pi posts to `https://ntfy.sh/<topic>` on any non-zero exit.

If the OAuth token ever expires, re-run the script locally to refresh `.cache`, then re-copy it to the Pi.
