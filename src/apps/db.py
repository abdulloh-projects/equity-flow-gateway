import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "gateway.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                participant_a TEXT NOT NULL,
                participant_b TEXT NOT NULL,
                last_message  TEXT,
                last_sender   TEXT,
                created_at    TEXT NOT NULL,
                updated_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id),
                sender_id       TEXT NOT NULL,
                text            TEXT NOT NULL,
                created_at      TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conv_participants
                ON conversations(participant_a, participant_b);

            CREATE INDEX IF NOT EXISTS idx_msg_conv
                ON messages(conversation_id);

            CREATE TABLE IF NOT EXISTS startup_bank_info (
                startup_id   INTEGER PRIMARY KEY,
                bank_info_id INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS startup_videos (
                startup_id  INTEGER PRIMARY KEY,
                youtube_url TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS startup_documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                startup_id  INTEGER NOT NULL,
                title       TEXT NOT NULL,
                doc_type    TEXT NOT NULL,
                file_url    TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_startup_documents
                ON startup_documents(startup_id);
        """)
