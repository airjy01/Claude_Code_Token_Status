#!/usr/bin/env python3
"""
claude-token-status: Claude Code token usage + reset countdown in Stop hook.

Auto-detects project directory from $PWD so it works for any user/project.
Set env vars to override defaults:
  CLAUDE_TOKEN_CONTEXT_WINDOW   (default: 200000)
  CLAUDE_TOKEN_RESET_HOURS      (default: 5)
  CLAUDE_TOKEN_TZ_OFFSET        (default: 8  — UTC+8, Taiwan/China/HK/SG)
  CLAUDE_TOKEN_CHECKPOINT_DIR   (default: ~/.claude/projects/<slug>/memory)
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Auto-detect project slug from $PWD ────────────────────────────────────────
# Claude Code stores sessions under ~/.claude/projects/<slug>/
# where <slug> = PWD with every "/" replaced by "-"
# e.g. /home/alice/myproject  →  -home-alice-myproject
_pwd  = os.environ.get("PWD", os.getcwd())
_slug = _pwd.replace("/", "-")          # leading "/" becomes leading "-"

CLAUDE_DIR   = Path.home() / ".claude"
PROJECT_DIR  = CLAUDE_DIR / "projects" / _slug

# ── Configurable via environment variables ────────────────────────────────────
CONTEXT_WINDOW    = int(os.environ.get("CLAUDE_TOKEN_CONTEXT_WINDOW", 200_000))
USAGE_RESET_HOURS = int(os.environ.get("CLAUDE_TOKEN_RESET_HOURS",    5))
_tz_offset        = int(os.environ.get("CLAUDE_TOKEN_TZ_OFFSET",      8))
LOCAL_TZ          = timezone(timedelta(hours=_tz_offset))

_checkpoint_dir   = os.environ.get("CLAUDE_TOKEN_CHECKPOINT_DIR", "")
MEMORY_DIR        = Path(_checkpoint_dir) if _checkpoint_dir else PROJECT_DIR / "memory"


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_current_session() -> Path | None:
    """Return the JSONL file for the current (or most recent) session."""
    if not PROJECT_DIR.exists():
        return None
    jsonl_files = sorted(
        PROJECT_DIR.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    # CLAUDE_CODE_SESSION_ID is set by the Claude Code process
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if session_id:
        for f in jsonl_files:
            if session_id in f.name:
                return f
    return jsonl_files[0] if jsonl_files else None


def parse_ts(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


def parse_usage(session_file: Path):
    """
    Scan session JSONL and return:
      last_inp, last_cache_create, last_cache_read,
      output_total, turn_count, window_start

    window_start = earliest timestamp within the rolling USAGE_RESET_HOURS window.
    Using the rolling window (not session start) gives accurate reset countdown
    even for long-running sessions that span multiple 5-hour periods.
    """
    last_inp = last_cache_create = last_cache_read = 0
    output_total = turns = 0
    window_start = None

    now    = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=USAGE_RESET_HOURS)

    with open(session_file, encoding="utf-8") as f:
        for raw in f:
            try:
                entry = json.loads(raw)
                ts    = parse_ts(entry.get("timestamp"))
                msg   = entry.get("message", {})
                usage = msg.get("usage")

                if usage and msg.get("role") == "assistant":
                    last_inp          = usage.get("input_tokens", 0)
                    last_cache_create = usage.get("cache_creation_input_tokens", 0)
                    last_cache_read   = usage.get("cache_read_input_tokens", 0)
                    output_total     += usage.get("output_tokens", 0)
                    turns            += 1

                if ts and ts >= cutoff:
                    if window_start is None or ts < window_start:
                        window_start = ts
            except Exception:
                continue

    return last_inp, last_cache_create, last_cache_read, output_total, turns, window_start


def extract_user_messages(session_file: Path, last_n: int = 30) -> list[tuple]:
    """Return the last N (timestamp, text) pairs for user turns."""
    messages = []
    with open(session_file, encoding="utf-8") as f:
        for raw in f:
            try:
                d   = json.loads(raw)
                msg = d.get("message", {})
                ts  = parse_ts(d.get("timestamp"))
                if msg.get("role") != "user":
                    continue
                content = msg.get("content", "")
                text = ""
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            text = c["text"].strip()
                            break
                elif isinstance(content, str):
                    text = content.strip()
                # skip tool-result echo lines
                if text and not text.startswith("[Tool result"):
                    messages.append((ts, text[:200]))
            except Exception:
                continue
    return messages[-last_n:]


def save_checkpoint(session_file: Path, pct_used: float, turns: int) -> Path | None:
    """
    Write a lightweight checkpoint markdown to MEMORY_DIR when usage ≥ 90 %.
    One file per hour maximum (deduplication by hour prefix in filename).
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    now_local = datetime.now(LOCAL_TZ)
    stamp     = now_local.strftime("%Y%m%d_%H%M")

    # dedup: skip if a checkpoint for this hour already exists
    if list(MEMORY_DIR.glob(f"session_checkpoint_{now_local.strftime('%Y%m%d_%H')}*.md")):
        return None

    out_path = MEMORY_DIR / f"session_checkpoint_{stamp}.md"
    messages = extract_user_messages(session_file)

    lines = [
        "---",
        f"name: session-checkpoint-{stamp}",
        f"description: Auto checkpoint at {pct_used:.0f}% token usage — {now_local.strftime('%Y-%m-%d %H:%M')}",
        "metadata:",
        "  type: project",
        "---",
        "",
        f"## Session Checkpoint  {now_local.strftime('%Y-%m-%d %H:%M')}  ({pct_used:.0f}% tokens used)",
        "",
        f"**Session:** `{session_file.name}` | **Turns:** {turns} | **Usage:** {pct_used:.1f}%",
        "",
        "### Recent user prompts (last 30)",
        "",
    ]
    for ts, text in messages:
        ts_str = ts.astimezone(LOCAL_TZ).strftime("%H:%M") if ts else "??:??"
        lines.append(f"- `{ts_str}` {text}")
    lines += [
        "",
        "> ⚠️  Auto checkpoint — run `/session-summary` for a full AI-generated summary.",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    session_file = find_current_session()
    if not session_file:
        print(json.dumps({"systemMessage": f"[claude-token-status] No session file found in {PROJECT_DIR}"}))
        return

    inp, cache_create, cache_read, _, turns, window_start = parse_usage(session_file)

    context_used      = cache_read + cache_create + inp
    context_remaining = CONTEXT_WINDOW - context_used
    pct_used          = context_used / CONTEXT_WINDOW * 100 if context_used else 0

    # progress bar
    bar_len = 28
    bar     = "█" * int(bar_len * pct_used / 100) + "░" * (bar_len - int(bar_len * pct_used / 100))

    # warning + auto-checkpoint
    warn = checkpoint_note = ""
    if pct_used >= 90:
        saved = save_checkpoint(session_file, pct_used, turns)
        if saved:
            checkpoint_note = f"\n📌 Checkpoint saved: {saved.name}"
        warn = f"  ⚠️  ≥90% — run /session-summary then open a new session{checkpoint_note}"
    elif pct_used >= 75:
        warn = "  ⚠️  ≥75% — consider /session-summary to preserve progress"

    # reset countdown
    if window_start:
        now      = datetime.now(timezone.utc)
        reset_at = window_start + timedelta(hours=USAGE_RESET_HOURS)
        remaining = reset_at - now
        if remaining.total_seconds() > 0:
            h, rem = divmod(int(remaining.total_seconds()), 3600)
            m = rem // 60
            reset_line = f"\nReset in: {h}h {m:02d}m  ({reset_at.astimezone(LOCAL_TZ).strftime('%H:%M')} local)"
        else:
            reset_line = "\nReset: window elapsed — usage available"
    else:
        reset_line = "\nReset: no recent activity (window reset)"

    msg = (
        f"Token [{bar}] {pct_used:.1f}%{warn}\n"
        f"Used {context_used:,} / {CONTEXT_WINDOW:,}   Remaining {context_remaining:,}   ({turns} turns)\n"
        f"Session: {session_file.name[:12]}…"
        f"{reset_line}"
    )
    print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    main()
