import os
from datetime import datetime, timezone
from pathlib import Path

from sqlite_wrapper import SQLiteWrapper


class SpotifyDatabaseWrapper(SQLiteWrapper):

    ddl_creation_statements = [
        """
        CREATE TABLE IF NOT EXISTS track  (
            [uri]               TEXT PRIMARY KEY,
            [name]              TEXT,
            [artists]           TEXT,
            [album]             TEXT,
            [release_date]      TEXT,
            [popularity]        INTEGER,
            [duration_ms]       INTEGER,
            [explicit]          INTEGER,
            [is_liked]          INTEGER DEFAULT 0,
            [is_disliked]       INTEGER DEFAULT 0,
            [has_metadata]      INTEGER DEFAULT 0,
            [radio_playlist]    TEXT,
            [added_at]          DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ;"""
        ,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_track_uri
        ON track ([uri]);

        """
        ,
        """

        CREATE INDEX IF NOT EXISTS idx_track_radio_playlist
        ON track ([radio_playlist]);

        """
        ,
        """
        CREATE TABLE IF NOT EXISTS playlist_track  (
            [id]            TEXT PRIMARY KEY,
            [playlist]      TEXT NOT NULL,
            [track]         TEXT NOT NULL,
            [added_at]      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ;
        """
        ,
        """
        CREATE INDEX IF NOT EXISTS idx_playlist_track_playlist
        ON playlist_track ([playlist]);

        """
        ,
        """

        CREATE INDEX IF NOT EXISTS idx_playlist_track_track
        ON playlist_track ([track]);

        """
        ,
        """
        CREATE TABLE IF NOT EXISTS stew_history (
            [id]            INTEGER PRIMARY KEY AUTOINCREMENT,
            [uri]           TEXT NOT NULL,
            [playlist_date] DATETIME NOT NULL
        )
        ;
        """
        ,
        """
        CREATE INDEX IF NOT EXISTS idx_stew_history_playlist_date
        ON stew_history ([playlist_date]);

        """
    ]

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.environ.get('SPOTIFY_DATABASE_PATH', 'spotify-database.db')
        super().__init__(db_path=Path(db_path), create=True)
        for statement in SpotifyDatabaseWrapper.ddl_creation_statements:
            self.execute(statement)
        self._migrate_track_columns()

    def _migrate_track_columns(self):
        try:
            ddl = self.get_table_ddl('track')
        except ValueError:
            return
        if 'last_added_at' not in ddl:
            self.execute("ALTER TABLE track ADD COLUMN last_added_at DATETIME")
        if 'times_added' not in ddl:
            self.execute("ALTER TABLE track ADD COLUMN times_added INTEGER DEFAULT 0")

    def update_track_table(self):
        statement = """
            -- New recommended tracks to add to track table
            INSERT INTO track (uri)
            SELECT DISTINCT playlist_track.track AS uri
            FROM playlist_track
            LEFT JOIN track
            ON playlist_track.track = track.uri
            WHERE track.uri IS NULL;
        """
        self.execute(statement=statement)

    def get_tracks_for_weighted_selection(self):
        query = """
            SELECT uri, last_added_at, COALESCE(times_added, 0) AS times_added
            FROM track
            WHERE COALESCE(is_disliked, 0) = 0
        """
        return self.get_query(query)

    def save_stew_history(self, uris):
        playlist_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        self._executemany(
            "INSERT INTO stew_history (uri, playlist_date) VALUES (?, ?)",
            [(uri, playlist_date) for uri in uris]
        )

    def get_recent_stew_tracks(self, days=7):
        query = """
            SELECT uri
            FROM stew_history
            WHERE playlist_date >= datetime('now', ?)
            GROUP BY uri
            ORDER BY MIN(playlist_date)
        """
        return self.get_query(query, parameters=(f'-{days} days',))

    def update_selected_tracks(self, uris):
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        statement = """
            UPDATE track
            SET last_added_at = ?, times_added = COALESCE(times_added, 0) + 1
            WHERE uri = ?
        """
        self._executemany(statement, [(now, uri) for uri in uris])
