#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/root/spotify-manage"
PYTHON="$REPO_DIR/.venv/bin/python"
NTFY_TOPIC=$(grep '^NTFY_TOPIC=' "$REPO_DIR/.env" | cut -d'=' -f2-)

mkdir -p "$REPO_DIR/logs"
exec >> "$REPO_DIR/logs/run_stew.log" 2>&1

echo "--- $(date '+%Y-%m-%d %H:%M:%S') START ---"

# cd is critical: SpotifyOAuth reads .cache from cwd; load_dotenv() searches upward from cwd
cd "$REPO_DIR"

if ! "$PYTHON" run_stew.py; then
    EXIT_CODE=$?
    curl -s \
        -H "Title: spotify-manage failed" \
        -H "Priority: high" \
        -H "Tags: warning" \
        -d "run_stew.py exited with code $EXIT_CODE on $(hostname) at $(date '+%Y-%m-%d %H:%M')" \
        "https://ntfy.sh/$NTFY_TOPIC"
    echo "--- $(date '+%Y-%m-%d %H:%M:%S') FAILED ($EXIT_CODE) ---"
    exit $EXIT_CODE
fi

echo "--- $(date '+%Y-%m-%d %H:%M:%S') SUCCESS ---"
