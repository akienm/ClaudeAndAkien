#!/usr/bin/env python3
"""
slate_manager.py — Manage the active slate in Postgres.

A slate is a named, themed bundle of work (~1 day). It has:
  - position: 0=today, 1=next, 2=after, 3+=future (vaguer as position increases)
  - done_when: one-sentence completion criterion
  - tickets: [{id, title, type: primary|adopted_bug, status}]
  - notes: free-form shape description

Usage:
    python3 claudecode/slate_manager.py show          — print current slates
    python3 claudecode/slate_manager.py render        — write slate.md from DB
    python3 claudecode/slate_manager.py seed          — seed initial slates (edit cmd_seed first)
    python3 claudecode/slate_manager.py add-ticket <slate_pos> <ticket_id> <title> [--bug]
    python3 claudecode/slate_manager.py close-ticket <ticket_id>
    python3 claudecode/slate_manager.py advance       — close slate 0, shift 1→0 2→1 etc.

Environment:
    CC_DB_URL     — Postgres connection string (required)
    CC_SLATE_FILE — path for rendered slate.md (default: ~/.channel/slate.md)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

SLATE_MD = Path(os.getenv("CC_SLATE_FILE", Path.home() / ".channel" / "slate.md"))
DB_URL = os.getenv("CC_DB_URL")


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _ensure_table():
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS slates (
                    id         TEXT PRIMARY KEY,
                    position   INTEGER NOT NULL,
                    name       TEXT NOT NULL,
                    done_when  TEXT,
                    tickets    JSONB DEFAULT '[]',
                    notes      TEXT,
                    status     TEXT DEFAULT 'active',
                    created_at TEXT,
                    closed_at  TEXT
                )
            """)
        conn.commit()


def _load_slates() -> list:
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM slates WHERE status='active' ORDER BY position")
            return [dict(r) for r in c.fetchall()]


def _upsert_slate(s: dict):
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute(
                """
                INSERT INTO slates (id, position, name, done_when, tickets, notes, status, created_at)
                VALUES (%(id)s, %(position)s, %(name)s, %(done_when)s,
                        %(tickets)s::jsonb, %(notes)s, %(status)s, %(created_at)s)
                ON CONFLICT (id) DO UPDATE SET
                    position  = EXCLUDED.position,
                    name      = EXCLUDED.name,
                    done_when = EXCLUDED.done_when,
                    tickets   = EXCLUDED.tickets,
                    notes     = EXCLUDED.notes,
                    status    = EXCLUDED.status
            """,
                {**s, "tickets": json.dumps(s.get("tickets", []))},
            )
        conn.commit()


def cmd_seed():
    """Seed DB with initial slates. Edit this function for your project."""
    _ensure_table()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    slates = [
        {
            "id": "slate-0",
            "position": 0,
            "name": "Today's work",
            "done_when": "Edit this criterion",
            "tickets": [],
            "notes": None,
            "status": "active",
            "created_at": now,
        },
        {
            "id": "slate-1",
            "position": 1,
            "name": "Next up",
            "done_when": None,
            "tickets": [],
            "notes": "Shape TBD",
            "status": "active",
            "created_at": now,
        },
    ]
    for s in slates:
        _upsert_slate(s)
        print(f"  seeded: slate-{s['position']} — {s['name']}")
    print("Seed complete. Edit cmd_seed() before running again.")


def cmd_show():
    slates = _load_slates()
    for s in slates:
        label = ["TODAY", "NEXT", "AFTER NEXT", "FUTURE"][min(s["position"], 3)]
        print(f"\nSlate {s['position']} — {s['name']}  [{label}]")
        if s.get("done_when"):
            print(f"  Done when: {s['done_when']}")
        if s.get("notes"):
            print(f"  Shape: {s['notes']}")
        tickets = s.get("tickets") or []
        for t in tickets:
            mark = "✓" if t.get("status") == "done" else "·"
            bug = " [bug]" if t.get("type") == "adopted_bug" else ""
            print(f"    {mark}{bug} {t['id']}: {t['title']}")


def cmd_render():
    slates = _load_slates()
    now = datetime.now().strftime("%Y-%m-%d")
    labels = {0: "TODAY", 1: "NEXT", 2: "AFTER NEXT"}
    lines = [f"# Active Slate — {now}", ""]

    for s in slates:
        label = labels.get(s["position"], "FUTURE")
        lines += ["---", "", f"## Slate {s['position']} — {s['name']} ({label})"]
        if s.get("done_when"):
            lines.append(f"**Done when**: {s['done_when']}")
        if s.get("notes"):
            lines.append(f"**Shape**: {s['notes']}")
        lines.append("")
        tickets = s.get("tickets") or []
        open_t = [t for t in tickets if t.get("status") != "done"]
        done_t = [t for t in tickets if t.get("status") == "done"]
        if open_t:
            lines.append("### Tickets")
            for t in open_t:
                lines.append(f"- {t['id']}: {t['title']}")
            lines.append("")
        if done_t:
            lines.append("### Done this slate")
            for t in done_t:
                lines.append(f"- ~~{t['id']}~~ ✓  {t['title']}")
            lines.append("")

    SLATE_MD.parent.mkdir(parents=True, exist_ok=True)
    SLATE_MD.write_text("\n".join(lines) + "\n")
    print(f"Rendered → {SLATE_MD}")


def cmd_add_ticket(pos: int, ticket_id: str, title: str, is_bug: bool = False):
    slates = _load_slates()
    target = next((s for s in slates if s["position"] == pos), None)
    if not target:
        print(f"No active slate at position {pos}", file=sys.stderr)
        sys.exit(1)
    tickets = target.get("tickets") or []
    if any(t["id"] == ticket_id for t in tickets):
        print(f"{ticket_id} already in slate")
        return
    tickets.append(
        {
            "id": ticket_id,
            "title": title,
            "type": "adopted_bug" if is_bug else "primary",
            "status": "pending",
        }
    )
    target["tickets"] = tickets
    _upsert_slate(target)
    print(f"Added {ticket_id} to slate {pos}")


def cmd_close_ticket(ticket_id: str):
    slates = _load_slates()
    for s in slates:
        tickets = s.get("tickets") or []
        changed = False
        for t in tickets:
            if t["id"] == ticket_id and t.get("status") != "done":
                t["status"] = "done"
                changed = True
        if changed:
            s["tickets"] = tickets
            _upsert_slate(s)
            print(f"Closed {ticket_id} in slate {s['position']}")


def cmd_advance():
    slates = _load_slates()
    slate0 = next((s for s in slates if s["position"] == 0), None)
    if not slate0:
        print("No active slate 0", file=sys.stderr)
        sys.exit(1)
    now = datetime.now().isoformat()
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute(
                "UPDATE slates SET status='done', closed_at=%s WHERE id=%s",
                (now, slate0["id"]),
            )
            for s in slates:
                if s["position"] > 0:
                    c.execute(
                        "UPDATE slates SET position=%s WHERE id=%s",
                        (s["position"] - 1, s["id"]),
                    )
        conn.commit()
    print(f"Closed: {slate0['name']}")
    print("Remaining slates shifted down.")


def main():
    if not DB_URL:
        print("ERROR: CC_DB_URL not set", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "seed":
        cmd_seed()
    elif cmd == "show":
        cmd_show()
    elif cmd == "render":
        cmd_render()
    elif cmd == "add-ticket":
        if len(sys.argv) < 5:
            print(
                "Usage: slate_manager.py add-ticket <pos> <ticket_id> <title> [--bug]"
            )
            sys.exit(2)
        cmd_add_ticket(
            int(sys.argv[2]), sys.argv[3], sys.argv[4], is_bug="--bug" in sys.argv
        )
    elif cmd == "close-ticket":
        if len(sys.argv) < 3:
            print("Usage: slate_manager.py close-ticket <ticket_id>")
            sys.exit(2)
        cmd_close_ticket(sys.argv[2])
    elif cmd == "advance":
        cmd_advance()
    else:
        print(
            f"Unknown command: {cmd}  (seed|show|render|add-ticket|close-ticket|advance)"
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
