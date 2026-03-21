import json
import os
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]


def init_db():
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orientation (
                id SERIAL PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'nouvelle',
                created_at TEXT NOT NULL,
                person_first_name TEXT NOT NULL,
                person_last_name TEXT NOT NULL,
                person_phone TEXT,
                person_email TEXT,
                person_birthdate TEXT,
                person_address TEXT,
                sender_name TEXT NOT NULL,
                sender_type TEXT NOT NULL,
                sender_organization TEXT,
                sender_email TEXT,
                sender_message TEXT,
                modalite TEXT,
                diagnostic_data TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS message (
                id SERIAL PRIMARY KEY,
                orientation_id INTEGER NOT NULL REFERENCES orientation(id),
                author_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history_event (
                id SERIAL PRIMARY KEY,
                orientation_id INTEGER NOT NULL REFERENCES orientation(id),
                event_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def get_all_orientations(status_filter: list[str] | None = None) -> list[dict]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT * FROM orientation WHERE status = ANY(%s) ORDER BY created_at DESC",
                (status_filter,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM orientation ORDER BY created_at DESC"
            ).fetchall()
    return rows


def get_orientation(orientation_id: int) -> dict | None:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        row = conn.execute(
            "SELECT * FROM orientation WHERE id = %s", (orientation_id,)
        ).fetchone()
    if row is None:
        return None
    if row["diagnostic_data"]:
        row["diagnostic_data"] = json.loads(row["diagnostic_data"])
    return row


def update_orientation_status(orientation_id: int, new_status: str):
    now = datetime.now().isoformat()
    event_type = {"acceptee": "accepted", "refusee": "refused"}[new_status]
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE orientation SET status = %s WHERE id = %s",
            (new_status, orientation_id),
        )
        conn.execute(
            "INSERT INTO history_event (orientation_id, event_type, created_at) VALUES (%s, %s, %s)",
            (orientation_id, event_type, now),
        )
        conn.commit()


def get_messages(orientation_id: int) -> list[dict]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        rows = conn.execute(
            "SELECT * FROM message WHERE orientation_id = %s ORDER BY created_at DESC",
            (orientation_id,),
        ).fetchall()
    return rows


def add_message(orientation_id: int, author_name: str, content: str):
    now = datetime.now().isoformat()
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO message (orientation_id, author_name, content, created_at) VALUES (%s, %s, %s, %s)",
            (orientation_id, author_name, content, now),
        )
        conn.commit()


def get_history(orientation_id: int) -> list[dict]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        rows = conn.execute(
            "SELECT * FROM history_event WHERE orientation_id = %s ORDER BY created_at ASC",
            (orientation_id,),
        ).fetchall()
    return rows
