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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calls (
            call_id TEXT PRIMARY KEY,
            room_name TEXT,
            started_at TEXT,
            ended_at TEXT,
            outcome TEXT
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


def start_call(call_id: str, room_name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO calls (call_id, room_name, started_at, ended_at, outcome) VALUES (?, ?, ?, NULL, 'in_progress')",
        (call_id, room_name, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def end_call(call_id: str, outcome: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE calls SET ended_at = ?, outcome = ? WHERE call_id = ?",
        (datetime.now(timezone.utc).isoformat(), outcome, call_id),
    )
    conn.commit()
    conn.close()


def get_call_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT outcome, COUNT(*) FROM calls GROUP BY outcome")
    rows = cur.fetchall()
    conn.close()
    stats = {"total": 0, "successful": 0, "failed": 0, "in_progress": 0}
    for outcome, count in rows:
        stats["total"] += count
        if outcome == "successful":
            stats["successful"] = count
        elif outcome == "failed":
            stats["failed"] = count
        elif outcome == "in_progress":
            stats["in_progress"] = count
    return stats
