#!/usr/bin/env python3
"""
github_sync.py — Sync GitHub issues to Postgres (Organizer step 0).

DB becomes source of truth after sync. Run before any planning/summarization
so the Organizer works from DB not stale memory.

Usage:
    python3 claudecode/github_sync.py sync     — pull GitHub → DB, print delta
    python3 claudecode/github_sync.py list     — show open tickets from DB
    python3 claudecode/github_sync.py list all — show all tickets
    python3 claudecode/github_sync.py delta    — show recently changed tickets

Environment:
    CC_DB_URL    — Postgres connection string (required)
    CC_GH_REPO   — GitHub repo in owner/name format (required)
"""

import json
import os
import subprocess
import sys
from datetime import datetime

DB_URL = os.getenv("CC_DB_URL")
REPO = os.getenv("CC_GH_REPO", "")
OPEN_LIMIT = 100
CLOSED_LIMIT = 30


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _ensure_table():
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS github_tickets (
                    number     INTEGER PRIMARY KEY,
                    title      TEXT NOT NULL,
                    state      TEXT NOT NULL,
                    body       TEXT DEFAULT '',
                    labels     TEXT DEFAULT '',
                    updated_at TEXT,
                    synced_at  TEXT,
                    our_notes  TEXT DEFAULT ''
                )
            """)
        conn.commit()


def _upsert(conn, ticket: dict):
    with conn.cursor() as c:
        c.execute(
            """
            INSERT INTO github_tickets (number, title, state, body, labels, updated_at, synced_at)
            VALUES (%(number)s, %(title)s, %(state)s, %(body)s, %(labels)s, %(updated_at)s, %(synced_at)s)
            ON CONFLICT (number) DO UPDATE SET
                title=EXCLUDED.title, state=EXCLUDED.state, body=EXCLUDED.body,
                labels=EXCLUDED.labels, updated_at=EXCLUDED.updated_at, synced_at=EXCLUDED.synced_at
        """,
            ticket,
        )


def _gh_issues(state: str, limit: int) -> list:
    if not REPO:
        print("ERROR: CC_GH_REPO not set", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,body,labels,updatedAt",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: gh CLI failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"].lower(),
            "body": (i.get("body") or "")[:2000],
            "labels": ",".join(l["name"] for l in i.get("labels", [])),
            "updated_at": i.get("updatedAt", ""),
            "synced_at": now,
        }
        for i in json.loads(result.stdout)
    ]


def cmd_sync():
    _ensure_table()
    print(f"Syncing {REPO} → Postgres...")
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM github_tickets ORDER BY number")
            before = {r["number"]: dict(r) for r in c.fetchall()}

    all_issues = {
        i["number"]: i
        for i in _gh_issues("open", OPEN_LIMIT) + _gh_issues("closed", CLOSED_LIMIT)
    }
    new_open, new_closed, reopened, updated = [], [], [], []

    with _conn() as conn:
        for num, ticket in all_issues.items():
            prev = before.get(num)
            if not prev:
                (new_open if ticket["state"] == "open" else new_closed).append(ticket)
            elif prev["state"] == "open" and ticket["state"] == "closed":
                new_closed.append(ticket)
            elif prev["state"] == "closed" and ticket["state"] == "open":
                reopened.append(ticket)
            elif prev.get("updated_at") != ticket["updated_at"]:
                updated.append(ticket)
            _upsert(conn, ticket)
        conn.commit()

    total_open = sum(1 for i in all_issues.values() if i["state"] == "open")
    print(
        f"\nDB updated — {total_open} open, {len(all_issues) - total_open} recently closed"
    )

    for label, items in [
        ("New open", new_open),
        ("Newly closed", new_closed),
        ("Reopened", reopened),
        ("Updated", updated),
    ]:
        if items:
            print(f"\n{label} ({len(items)}):")
            for i in items:
                print(f"  #{i['number']}: {i['title']}")

    if not any([new_open, new_closed, reopened, updated]):
        print("\nNo changes since last sync.")


def cmd_list(state: str = "open"):
    with _conn() as conn:
        with conn.cursor() as c:
            if state == "all":
                c.execute(
                    "SELECT number, title, state, labels FROM github_tickets ORDER BY number DESC"
                )
            else:
                c.execute(
                    "SELECT number, title, state, labels FROM github_tickets WHERE state=%s ORDER BY number DESC",
                    (state,),
                )
            rows = c.fetchall()
    if not rows:
        print(f"No {state} tickets in DB. Run: github_sync.py sync")
        return
    for r in rows:
        label_str = f"  [{r['labels']}]" if r.get("labels") else ""
        print(f"  #{r['number']}: {r['title']}{label_str}")
    print(f"\n{len(rows)} tickets ({state})")


def main():
    if not DB_URL:
        print("ERROR: CC_DB_URL not set", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "sync":
        cmd_sync()
    elif cmd == "list":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        cmd_list(state)
    else:
        print(f"Unknown command: {cmd}  (sync|list)")
        sys.exit(2)


if __name__ == "__main__":
    main()
