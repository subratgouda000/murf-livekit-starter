import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "callers.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_caller(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?",
        (user_id.lower().strip(),),
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "user_id": row[0],
        "name": row[1],
        "language_preference": row[2],
        "facts": json.loads(row[3]) if row[3] else {},
        "last_interaction": row[4],
    }


def save_caller(user_id: str, name: str, language_preference: str, facts: dict):
    conn = sqlite3.connect(DB_PATH)
    existing = get_caller(user_id)
    merged_facts = {}
    if existing and existing.get("facts"):
        merged_facts.update(existing["facts"])
    if facts:
        merged_facts.update(facts)

    conn.execute(
        """
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            language_preference=excluded.language_preference,
            facts=excluded.facts,
            last_interaction=excluded.last_interaction
        """,
        (
            user_id.lower().strip(),
            name,
            language_preference,
            json.dumps(merged_facts),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
