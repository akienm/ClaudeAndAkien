#!/usr/bin/env python3
"""
session_manager.py — Crash-safe session accumulation in Postgres.

Sessions build up progressively throughout the day. A crash loses only the
delta since the last /decided call — not the whole session.

The pattern:
  context-load  → session_manager.py start   (creates record, writes state file)
  each /decided → session_manager.py append-change / append-decision
  end of day    → session_manager.py finalize (adds next + in_flight, optional)

Usage:
    python3 claudecode/session_manager.py current
        — print current session ID (no DB needed)
    python3 claudecode/session_manager.py start <id> "<theme>"
        — create partial session record + write state file
    python3 claudecode/session_manager.py append-change [<id>] "<one-line change>"
        — accumulate key changes (id defaults to current session)
    python3 claudecode/session_manager.py append-decision [<id>] <decision_id>
        — accumulate decision IDs
    python3 claudecode/session_manager.py finalize <id> "<next>" "<in_flight>"
        — add synthesis fields at clean session end (optional — crash-safe without it)
    python3 claudecode/session_manager.py show [N]    — last N sessions (default 5)
    python3 claudecode/session_manager.py get <id>    — print one session
    python3 claudecode/session_manager.py seed        — parse sessions.md → DB (first run)
    python3 claudecode/session_manager.py render      — write sessions.md from DB

Environment:
    CC_DB_URL          — Postgres connection string (required for most commands)
    CC_RUNTIME_DIR     — runtime state dir (default: ~/.channel)
    CC_SESSIONS_FILE   — path for rendered sessions.md (default: ./memory/sessions.md)
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

_RUNTIME = Path(os.getenv("CC_RUNTIME_DIR", Path.home() / ".channel"))
CURRENT_SESSION_FILE = _RUNTIME / "current_session.txt"
SESSIONS_MD = Path(os.getenv("CC_SESSIONS_FILE", Path.cwd() / "memory" / "sessions.md"))
DB_URL = os.getenv("CC_DB_URL")


# ── State file (no DB needed) ─────────────────────────────────────────────────


def current_session_id() -> str:
    try:
        return CURRENT_SESSION_FILE.read_text().strip()
    except OSError:
        return ""


def _write_current_session(sid: str):
    CURRENT_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_SESSION_FILE.write_text(sid + "\n")


# ── DB helpers ────────────────────────────────────────────────────────────────


def _conn():
    import psycopg2
    import psycopg2.extras

    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _ensure_table():
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id           TEXT PRIMARY KEY,
                    theme        TEXT NOT NULL,
                    decisions    TEXT DEFAULT '',
                    key_changes  TEXT DEFAULT '',
                    next_session TEXT DEFAULT '',
                    in_flight    TEXT DEFAULT 'NONE',
                    created_at   TEXT
                )
            """)
        conn.commit()


def _upsert(conn, s: dict):
    with conn.cursor() as c:
        c.execute(
            """
            INSERT INTO sessions (id, theme, decisions, key_changes, next_session, in_flight, created_at)
            VALUES (%(id)s, %(theme)s, %(decisions)s, %(key_changes)s,
                    %(next_session)s, %(in_flight)s, %(created_at)s)
            ON CONFLICT (id) DO UPDATE SET
                theme        = EXCLUDED.theme,
                decisions    = EXCLUDED.decisions,
                key_changes  = EXCLUDED.key_changes,
                next_session = EXCLUDED.next_session,
                in_flight    = EXCLUDED.in_flight
        """,
            s,
        )


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_start(args: list):
    if len(args) < 2:
        print("Usage: session_manager.py start <id> <theme>")
        sys.exit(2)
    sid, theme = args[0], args[1]
    s = {
        "id": sid,
        "theme": theme,
        "decisions": "",
        "key_changes": "",
        "next_session": "",
        "in_flight": "NONE",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute(
                """INSERT INTO sessions (id, theme, decisions, key_changes, next_session, in_flight, created_at)
                   VALUES (%(id)s, %(theme)s, %(decisions)s, %(key_changes)s,
                           %(next_session)s, %(in_flight)s, %(created_at)s)
                   ON CONFLICT (id) DO NOTHING""",
                s,
            )
        conn.commit()
    _write_current_session(sid)
    print(f"Session {sid} started: {theme}")
    print(f"State file: {CURRENT_SESSION_FILE}")


def cmd_append_change(args: list):
    if not args:
        print("Usage: session_manager.py append-change [<id>] <change>")
        sys.exit(2)
    if len(args) >= 2 and re.match(r"^\d{4}-\d{2}-\d{2}", args[0]):
        sid, change = args[0], args[1]
    else:
        sid = current_session_id()
        change = args[0]
        if not sid:
            print(
                "ERROR: no current session. Run: session_manager.py start <id> <theme>",
                file=sys.stderr,
            )
            sys.exit(1)
    if not change.startswith("- "):
        change = "- " + change
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute(
                """UPDATE sessions SET key_changes = CASE
                       WHEN key_changes = '' THEN %s
                       ELSE key_changes || E'\\n' || %s
                   END WHERE id = %s""",
                (change, change, sid),
            )
            if c.rowcount == 0:
                print(f"  [warn] Session {sid} not found", file=sys.stderr)
                return
        conn.commit()
    print(f"Change recorded → {sid}: {change}")


def cmd_append_decision(args: list):
    if not args:
        print("Usage: session_manager.py append-decision [<id>] <decision_id>")
        sys.exit(2)
    if len(args) >= 2 and re.match(r"^\d{4}-\d{2}-\d{2}", args[0]):
        sid, did = args[0], args[1].upper()
    else:
        sid = current_session_id()
        did = args[0].upper()
        if not sid:
            print(
                "ERROR: no current session. Run: session_manager.py start <id> <theme>",
                file=sys.stderr,
            )
            sys.exit(1)
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute(
                """UPDATE sessions SET decisions = CASE
                       WHEN decisions = '' THEN %s
                       ELSE decisions || ', ' || %s
                   END WHERE id = %s""",
                (did, did, sid),
            )
            if c.rowcount == 0:
                print(f"  [warn] Session {sid} not found", file=sys.stderr)
                return
        conn.commit()
    print(f"Decision recorded → {sid}: {did}")


def cmd_finalize(args: list):
    if len(args) < 2:
        print("Usage: session_manager.py finalize <id> <next_session> [in_flight]")
        sys.exit(2)
    sid, next_session = args[0], args[1]
    in_flight = args[2] if len(args) > 2 else "NONE"
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute(
                "UPDATE sessions SET next_session=%s, in_flight=%s WHERE id=%s",
                (next_session, in_flight, sid),
            )
            if c.rowcount == 0:
                print(f"  [warn] Session {sid} not found", file=sys.stderr)
                sys.exit(1)
        conn.commit()
    print(f"Session {sid} finalized.")


def cmd_show(n: int = 5):
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT %s", (n,))
            rows = c.fetchall()
    if not rows:
        print("No sessions in DB. Run: session_manager.py seed")
        return
    for r in rows:
        print(f"\n## Session {r['id']}")
        print(f"  Theme: {r['theme']}")
        if r.get("decisions"):
            print(f"  Decisions: {r['decisions']}")
        for line in (r.get("key_changes") or "").splitlines():
            print(f"    {line}")
        if r.get("next_session"):
            print(f"  Next: {r['next_session']}")
        if r.get("in_flight") and r["in_flight"] != "NONE":
            print(f"  In-flight: {r['in_flight']}")


def cmd_get(sid: str):
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM sessions WHERE id=%s", (sid,))
            r = c.fetchone()
    if not r:
        print(f"Session {sid} not found")
        sys.exit(1)
    print(f"## Session {r['id']}\n**Theme**: {r['theme']}")
    if r.get("decisions"):
        print(f"**Decisions**: {r['decisions']}")
    if r.get("key_changes"):
        print(f"**Key changes**:\n{r['key_changes']}")
    if r.get("next_session"):
        print(f"**Next session**: {r['next_session']}")
    print(f"**In-flight**: {r.get('in_flight', 'NONE')}")


def cmd_render():
    with _conn() as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM sessions ORDER BY id DESC")
            rows = c.fetchall()
    lines = []
    for r in rows:
        lines.append(f"## Session {r['id']}")
        lines.append(f"**Theme**: {r['theme']}")
        if r.get("decisions"):
            lines.append(f"**Decisions**: {r['decisions']}")
        kc = (r.get("key_changes") or "").strip()
        if kc:
            lines.append("**Key changes**:")
            for line in kc.splitlines():
                lines.append(line if line.startswith("- ") else "- " + line)
        if r.get("next_session"):
            lines.append(f"**Next session**: {r['next_session']}")
        lines.append(f"**In-flight**: {r.get('in_flight', 'NONE')}")
        lines.append("")
    SESSIONS_MD.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_MD.write_text("\n".join(lines))
    print(f"Rendered {len(rows)} sessions → {SESSIONS_MD}")


def cmd_seed():
    """Parse an existing sessions.md and upsert all sessions to DB."""
    _ensure_table()
    if not SESSIONS_MD.exists():
        print(f"Not found: {SESSIONS_MD}", file=sys.stderr)
        sys.exit(1)
    text = SESSIONS_MD.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"(?=^## Session )", text, flags=re.MULTILINE)
    count = 0
    with _conn() as conn:
        for block in blocks:
            block = block.strip()
            if not block.startswith("## Session "):
                continue
            m = re.match(r"## Session (\S+)", block)
            if not m:
                continue
            sid = m.group(1)

            def _f(name):
                fm = re.search(
                    rf"\*\*{name}\*\*:\s*(.+?)(?=\n\*\*|\Z)", block, re.DOTALL
                )
                return fm.group(1).strip() if fm else ""

            kc_m = re.search(r"\*\*Key changes\*\*:\s*\n((?:- .+\n?)*)", block)
            s = {
                "id": sid,
                "theme": _f("Theme"),
                "decisions": _f("Decisions"),
                "key_changes": kc_m.group(1).strip() if kc_m else "",
                "next_session": _f("Next session"),
                "in_flight": _f("In-flight") or "NONE",
                "created_at": sid[:10],
            }
            _upsert(conn, s)
            count += 1
        conn.commit()
    print(f"Seeded {count} sessions from {SESSIONS_MD}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"

    if cmd == "current":
        sid = current_session_id()
        print(sid if sid else "(no current session)")
        return

    if not DB_URL:
        print("ERROR: CC_DB_URL not set", file=sys.stderr)
        sys.exit(1)

    if cmd == "start":
        cmd_start(sys.argv[2:])
    elif cmd == "append-change":
        cmd_append_change(sys.argv[2:])
    elif cmd == "append-decision":
        cmd_append_decision(sys.argv[2:])
    elif cmd == "finalize":
        cmd_finalize(sys.argv[2:])
    elif cmd == "show":
        cmd_show(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: session_manager.py get <id>")
            sys.exit(2)
        cmd_get(sys.argv[2])
    elif cmd == "seed":
        cmd_seed()
    elif cmd == "render":
        cmd_render()
    else:
        print(f"Unknown command: {cmd}")
        print(
            "Commands: current | start | append-change | append-decision | finalize | show | get | seed | render"
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
