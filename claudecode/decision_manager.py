#!/usr/bin/env python3
"""
decision_manager.py — Record design decisions atomically to Postgres.

One command records a decision to:
  1. The decisions table in Postgres
  2. The current session record (via session_manager.py append-decision)
  3. Optionally: a channel post for visibility

Usage:
    python3 claudecode/decision_manager.py add D133 "session-in-db" "implemented" \
        "sessions table in Postgres; crash-safe accumulation pattern"
    python3 claudecode/decision_manager.py show [N]   — last N decisions (default 10)
    python3 claudecode/decision_manager.py get D133   — print one decision

Status values: implemented | defined | planned | implemented-poc | deprecated

Environment:
    CC_DB_URL  — Postgres connection string (required)
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DB_URL = os.getenv("CC_DB_URL")
_THIS_DIR = Path(__file__).parent


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _ensure_table():
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id          TEXT PRIMARY KEY,   -- e.g. "D133"
                    short_name  TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    description TEXT NOT NULL,
                    session_id  TEXT DEFAULT '',
                    created_at  TEXT
                )
            """)
        conn.commit()


def _upsert(conn, d: dict):
    with conn.cursor() as c:
        c.execute(
            """
            INSERT INTO decisions (id, short_name, status, description, session_id, created_at)
            VALUES (%(id)s, %(short_name)s, %(status)s, %(description)s, %(session_id)s, %(created_at)s)
            ON CONFLICT (id) DO UPDATE SET
                short_name  = EXCLUDED.short_name,
                status      = EXCLUDED.status,
                description = EXCLUDED.description
        """,
            d,
        )


def _append_to_session(decision_id: str):
    """Tell session_manager about this decision. Non-fatal."""
    try:
        subprocess.run(
            [
                sys.executable,
                str(_THIS_DIR / "session_manager.py"),
                "append-decision",
                decision_id,
            ],
            timeout=5,
            capture_output=True,
            env={**os.environ, "CC_DB_URL": DB_URL or ""},
        )
    except Exception:
        pass


def cmd_add(args: list):
    if len(args) < 4:
        print(
            'Usage: decision_manager.py add <id> <short_name> <status> "<description>"'
        )
        sys.exit(2)
    _ensure_table()
    did = args[0].upper()
    session_id = ""
    try:
        from session_manager import current_session_id

        session_id = current_session_id()
    except Exception:
        pass

    d = {
        "id": did,
        "short_name": args[1],
        "status": args[2],
        "description": args[3],
        "session_id": session_id,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M"),
    }
    with _conn() as conn:
        _upsert(conn, d)
        conn.commit()
    print(f"Decision recorded: {did}|{args[1]}|{args[2]}|{args[3]}")

    _append_to_session(did)


def cmd_show(n: int = 10):
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT %s", (n,))
            rows = c.fetchall()
    print(f"Last {n} decisions:")
    for r in rows:
        print(f"  {r['id']}|{r['short_name']}|{r['status']}|{r['description']}")


def cmd_get(did: str):
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM decisions WHERE id=%s", (did.upper(),))
            r = c.fetchone()
    if not r:
        print(f"Decision {did} not found")
        sys.exit(1)
    print(f"{r['id']}|{r['short_name']}|{r['status']}|{r['description']}")


def main():
    if not DB_URL:
        print("ERROR: CC_DB_URL not set", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "add":
        cmd_add(sys.argv[2:])
    elif cmd == "show":
        cmd_show(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: decision_manager.py get <id>")
            sys.exit(2)
        cmd_get(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}  (add|show|get)")
        sys.exit(2)


if __name__ == "__main__":
    main()
