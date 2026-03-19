#!/usr/bin/env python3
"""
channel.py — Shared coordination channel for Claude Code sessions and Igor.

Append-only JSONL log at ~/.TheIgors/cc_channel/messages.jsonl
Any process can post. Any process can read the tail.
No Igor required. No web server required.

Usage:
    channel.py post "message"               # post as current session
    channel.py post "message" --as tab2     # post with explicit author
    channel.py read [N]                     # print last N messages (default 20)
    channel.py listen                       # tail -f style, print new messages
    channel.py sessions                     # list active sessions (posted in last 10min)

Also importable:
    from claudecode.channel import post, read, listen
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

_RUNTIME_ROOT = Path(os.getenv("IGOR_RUNTIME_ROOT", Path.home() / ".TheIgors"))
_CHANNEL_DIR = _RUNTIME_ROOT / "cc_channel"
_MESSAGES_FILE = _CHANNEL_DIR / "messages.jsonl"
_SESSION_NAME = os.getenv("CC_SESSION_NAME", f"cc-{os.getpid()}")

# Postgres optional — use if IGOR_HOME_DB_URL set and psycopg2 available
_USE_PG = False
_PG_URL = os.getenv("IGOR_HOME_DB_URL", "")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Storage backend ───────────────────────────────────────────────────────────


def _ensure_dir():
    _CHANNEL_DIR.mkdir(parents=True, exist_ok=True)


def _append(entry: dict):
    """Append one JSON entry to the messages file. Atomic enough for our purposes."""
    _ensure_dir()
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with open(_MESSAGES_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _read_tail(n: int = 20) -> list[dict]:
    """Read last N entries from messages file."""
    if not _MESSAGES_FILE.exists():
        return []
    lines = []
    try:
        with open(_MESSAGES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except OSError:
        return []
    return lines[-n:]


def _file_size() -> int:
    try:
        return _MESSAGES_FILE.stat().st_size
    except OSError:
        return 0


# ── Public API ────────────────────────────────────────────────────────────────


def post(content: str, author: str = "", msg_type: str = "message") -> dict:
    """Post a message to the shared channel."""
    entry = {
        "ts": _ts(),
        "author": author or _SESSION_NAME,
        "type": msg_type,
        "content": content,
    }
    _append(entry)
    return entry


def read(n: int = 20) -> list[dict]:
    """Return last N channel messages."""
    return _read_tail(n)


def listen(poll_interval: float = 1.0):
    """Generator: yield new entries as they are appended. Ctrl-C to stop."""
    last_size = _file_size()
    # Yield existing tail first
    for entry in _read_tail(20):
        yield entry
    while True:
        time.sleep(poll_interval)
        size = _file_size()
        if size <= last_size:
            continue
        # Read new lines
        try:
            with open(_MESSAGES_FILE, "r", encoding="utf-8") as f:
                f.seek(last_size)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            pass
            last_size = size
        except OSError:
            pass


def active_sessions(within_minutes: int = 10) -> list[str]:
    """Return list of session names that posted within the last N minutes."""
    cutoff = time.time() - within_minutes * 60
    entries = _read_tail(200)
    seen = {}
    for e in entries:
        try:
            ts = datetime.strptime(e["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            if ts.timestamp() >= cutoff:
                seen[e["author"]] = ts.strftime("%H:%M:%S")
        except (KeyError, ValueError):
            pass
    return [f"{name} (last: {t})" for name, t in seen.items()]


def format_entry(e: dict, color: bool = True) -> str:
    """Format a channel entry for terminal display."""
    ts = e.get("ts", "")[-8:-1] if e.get("ts") else "?"  # HH:MM:SS
    author = e.get("author", "?")
    content = e.get("content", "")
    msg_type = e.get("type", "message")

    if color and sys.stdout.isatty():
        # Simple ANSI colors
        colors = {
            "igor": "\033[36m",  # cyan
            "claude-code": "\033[32m",  # green
            "user": "\033[33m",  # yellow
        }
        reset = "\033[0m"
        c = colors.get(author, "\033[35m")  # magenta for unknown
        prefix = f"\033[2m{ts}\033[0m {c}{author}{reset}"
    else:
        prefix = f"{ts} {author}"

    if msg_type == "system":
        return f"\033[2m{prefix}: {content}\033[0m" if color else f"{prefix}: {content}"
    return f"{prefix}: {content}"


# ── CLI ───────────────────────────────────────────────────────────────────────


def _cli():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "post":
        if len(args) < 2:
            print("Usage: channel.py post <message> [--as <author>]", file=sys.stderr)
            sys.exit(1)
        content = args[1]
        author = ""
        if "--as" in args:
            idx = args.index("--as")
            author = args[idx + 1] if idx + 1 < len(args) else ""
        entry = post(content, author=author)
        print(f"Posted: {format_entry(entry)}")

    elif cmd == "read":
        n = int(args[1]) if len(args) > 1 else 20
        entries = read(n)
        if not entries:
            print("(channel is empty)")
        for e in entries:
            print(format_entry(e))

    elif cmd == "listen":
        print(f"Listening on {_MESSAGES_FILE} (Ctrl-C to stop)...")
        try:
            for entry in listen():
                print(format_entry(entry), flush=True)
        except KeyboardInterrupt:
            pass

    elif cmd == "sessions":
        sessions = active_sessions()
        if not sessions:
            print("(no active sessions in last 10 minutes)")
        else:
            print("Active sessions:")
            for s in sessions:
                print(f"  {s}")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Commands: post, read, listen, sessions")
        sys.exit(1)


if __name__ == "__main__":
    _cli()
