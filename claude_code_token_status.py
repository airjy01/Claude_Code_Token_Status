#!/usr/bin/env python3
"""
Claude_Code_Token_Status — Claude Code Stop hook.

Displays after every response:
  - Context window usage bar + %
  - Token counts (used / remaining / turns) + output tokens
  - Estimated session cost (per-model, with cache pricing)
  - Usage-window reset countdown (rolling-window estimate)
  - Auto-checkpoint at 90%+ usage; warns at 75%+

Works for Free / Pro / Max / API users — any plan that runs Claude Code CLI.
Cost display is equivalent API pricing; subscription users see a reference value.

Auto-detects project directory from $PWD — no hardcoded paths.

Environment variables (all optional):
  CLAUDE_TOKEN_CONTEXT_WINDOW   context window size          (default: 200000)
  CLAUDE_TOKEN_RESET_HOURS      usage window length hours    (default: 5)
  CLAUDE_TOKEN_TZ_OFFSET        UTC offset, e.g. -5 for EST  (default: 8)
  CLAUDE_TOKEN_CHECKPOINT_DIR   where to save checkpoints    (default: ~/.claude/projects/<slug>/memory)
  CLAUDE_TOKEN_MODEL            override model for pricing   (default: auto from JSONL)
  CLAUDE_TOKEN_BAR_WIDTH        progress bar character width (default: 28)
  CLAUDE_TOKEN_CURRENCY         display currency: NTD or USD (default: NTD)
  CLAUDE_TOKEN_USD_TO_NTD       USD → NTD exchange rate      (default: 31.5)
"""

from __future__ import annotations   # Python 3.9 compat for str | None hints

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Model pricing (USD per 1M tokens) ─────────────────────────────────────────
# Last updated: 2026-05 — verify current rates at https://www.anthropic.com/pricing
# Cache write = 1.25× input rate;  cache read = 0.10× input rate
_PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4":    (1.00,  5.00),
    "claude-sonnet-4":   (3.00, 15.00),
    "claude-opus-4":     (5.00, 25.00),
    # legacy claude-3.x
    "claude-3-5-haiku":  (0.80,  4.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-opus":     (15.0, 75.00),
}

_M = 1_000_000   # tokens per pricing unit


def _model_pricing(model_id: str | None) -> tuple[float, float, str]:
    """Return (inp_per_mtok, out_per_mtok, label).

    Label examples: "sonnet-4.6" from "claude-sonnet-4-6",
                    "haiku-4.5" from "claude-haiku-4-5-20251001".
    Unknown models return sonnet-4 rates with label marked "(est.)".
    """
    mid = (model_id or "").lower()
    for key, rates in _PRICING.items():
        if key in mid:
            base = key.replace("claude-", "")
            idx = mid.find(key)
            suffix = mid[idx + len(key):]
            version_digits = [p for p in suffix.split("-") if p.isdigit()]
            if version_digits:
                base += f".{version_digits[0]}"
            return rates[0], rates[1], base
    # unknown model — use sonnet-4 as safe default, flag as estimate
    return 3.00, 15.00, f"{(model_id or 'unknown')[:16]} (est.)"


# ── Auto-detect project slug from $PWD ────────────────────────────────────────
# Claude Code stores sessions under ~/.claude/projects/<slug>/
# slug = PWD with every "/" replaced by "-"  e.g. /home/alice/proj → -home-alice-proj
_pwd  = os.environ.get("PWD", os.getcwd())
_slug = _pwd.replace("/", "-")

CLAUDE_DIR  = Path.home() / ".claude"
PROJECT_DIR = CLAUDE_DIR / "projects" / _slug

# ── Configurable via environment variables ────────────────────────────────────
CONTEXT_WINDOW    = int(os.environ.get("CLAUDE_TOKEN_CONTEXT_WINDOW", 200_000))
USAGE_RESET_HOURS = int(os.environ.get("CLAUDE_TOKEN_RESET_HOURS",    5))
BAR_WIDTH         = int(os.environ.get("CLAUDE_TOKEN_BAR_WIDTH",      28))
_tz_offset        = int(os.environ.get("CLAUDE_TOKEN_TZ_OFFSET",      8))
LOCAL_TZ          = timezone(timedelta(hours=_tz_offset))

_checkpoint_dir   = os.environ.get("CLAUDE_TOKEN_CHECKPOINT_DIR", "")
MEMORY_DIR        = Path(_checkpoint_dir) if _checkpoint_dir else PROJECT_DIR / "memory"

CURRENCY         = os.environ.get("CLAUDE_TOKEN_CURRENCY",   "NTD").upper()
_ENV_USD_TO_NTD  = os.environ.get("CLAUDE_TOKEN_USD_TO_NTD", "")   # manual override
_RATE_CACHE_FILE = CLAUDE_DIR / ".usd_twd_cache"
_RATE_CACHE_TTL  = 86_400   # 24 hours in seconds


def _fetch_usd_to_ntd() -> tuple[float, str]:
    """Return (rate, source) where source is 'live', 'cached', 'stale', 'manual', or 'est.'

    Priority:
      1. CLAUDE_TOKEN_USD_TO_NTD env var       → 'manual'
      2. Cache file younger than 24 h          → 'cached'
      3. Live: open.er-api.com (primary)       → 'live', writes cache
         Live: rate.bot.com.tw spot mid-rate   → 'live', fallback
      4. Stale cache (network failed)          → 'stale'
      5. Hard-coded fallback 31.5              → 'est.'
    """
    import time

    # 1. manual env override
    if _ENV_USD_TO_NTD:
        try:
            return float(_ENV_USD_TO_NTD), "manual"
        except ValueError:
            pass

    # helper: read cache file
    def _read_cache() -> tuple[float, int] | None:
        try:
            data = json.loads(_RATE_CACHE_FILE.read_text())
            return float(data["rate"]), int(data["ts"])
        except Exception:
            return None

    now_ts = int(time.time())

    # 2. fresh cache
    cached = _read_cache()
    if cached and (now_ts - cached[1]) < _RATE_CACHE_TTL:
        return cached[0], "cached"

    # 3. live fetch (stdlib urllib only — no pip needed)
    from urllib.request import urlopen, Request

    def _try_fetch(url: str, json_path: list) -> float | None:
        try:
            req = Request(url, headers={"User-Agent": "Claude_Code_Token_Status/1.0"})
            with urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read())
            val = data
            for key in json_path:
                val = val[key]
            return float(val)
        except Exception:
            return None

    # primary: open.er-api.com (free, no API key)
    rate = _try_fetch("https://open.er-api.com/v6/latest/USD", ["rates", "TWD"])
    # fallback: Taiwan Bank spot mid-rate ((buy+sell)/2) — CSV format
    if rate is None:
        try:
            req = Request("https://rate.bot.com.tw/xrt/flcsv/0/day",
                          headers={"User-Agent": "curl/7.68"})
            with urlopen(req, timeout=4) as resp:
                for line in resp.read().decode("utf-8").splitlines():
                    if line.startswith("USD,"):
                        parts = line.split(",")
                        # col 3 = spot buy, col 13 = spot sell
                        rate = (float(parts[3]) + float(parts[13])) / 2
                        break
        except Exception:
            pass

    if rate is not None:
        _RATE_CACHE_FILE.write_text(json.dumps({"rate": rate, "ts": now_ts}))
        return rate, "live"

    # 4. stale cache (network failed but we have something)
    if cached:
        return cached[0], "stale"

    # 5. hard-coded fallback
    return 31.5, "est."


def _fmt_cost(usd: float, rate: float) -> str:
    """Format a USD amount using the given rate (NTD) or as-is (USD)."""
    if CURRENCY == "USD":
        if usd >= 1.0:  return f"${usd:.3f}"
        if usd >= 0.1:  return f"${usd:.4f}"
        return f"${usd:.5f}"
    ntd = usd * rate
    if ntd >= 100:  return f"NT${ntd:.0f}"
    if ntd >= 1:    return f"NT${ntd:.1f}"
    return f"NT${ntd:.2f}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_current_session() -> Path | None:
    """Return the JSONL for the current session, falling back to most recent."""
    if not PROJECT_DIR.exists():
        return None
    jsonl_files = sorted(
        PROJECT_DIR.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
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
    """Scan session JSONL; return usage snapshot, cost breakdown, and reset anchor.

    Returns:
      last_inp, last_cc, last_cr   — context snapshot from last assistant turn
                                     (NOT summed — cache_read grows each turn;
                                      summing would wildly overcount context size)
      output_total                 — cumulative output tokens across session
      turns                        — assistant turn count
      window_start                 — earliest timestamp within rolling reset window
      cost_inp, cost_cc, cost_cr,
      cost_out                     — cumulative USD costs per category
      last_model                   — model id from last assistant turn

    Reset note: Anthropic Rate Limits API (Apr 2026) is admin-only; Stop hooks
    don't receive rate-limit response headers (issue #36056, pending).
    Rolling-window calculation is the best available method for subscription users.
    """
    last_inp = last_cc = last_cr = 0
    output_total = turns = 0
    cost_inp = cost_cc = cost_cr = cost_out = 0.0
    window_start = None
    last_model: str = os.environ.get("CLAUDE_TOKEN_MODEL", "")

    now    = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=USAGE_RESET_HOURS)

    with open(session_file, encoding="utf-8") as fh:
        for raw in fh:
            try:
                entry = json.loads(raw)
                ts    = parse_ts(entry.get("timestamp"))
                msg   = entry.get("message", {})
                usage = msg.get("usage")

                if usage and msg.get("role") == "assistant":
                    t_inp = usage.get("input_tokens", 0)
                    t_cc  = usage.get("cache_creation_input_tokens", 0)
                    t_cr  = usage.get("cache_read_input_tokens", 0)
                    t_out = usage.get("output_tokens", 0)

                    last_inp      = t_inp
                    last_cc       = t_cc
                    last_cr       = t_cr
                    output_total += t_out
                    turns        += 1

                    if msg.get("model"):
                        last_model = msg["model"]

                    ir, or_, _ = _model_pricing(last_model)
                    cost_inp += t_inp * ir          / _M
                    cost_cc  += t_cc  * (ir * 1.25) / _M
                    cost_cr  += t_cr  * (ir * 0.10) / _M
                    cost_out += t_out * or_          / _M

                if ts and ts >= cutoff:
                    if window_start is None or ts < window_start:
                        window_start = ts
            except Exception:
                continue

    return (last_inp, last_cc, last_cr,
            output_total, turns, window_start,
            cost_inp, cost_cc, cost_cr, cost_out, last_model)


def extract_user_messages(session_file: Path, last_n: int = 30) -> list[tuple]:
    """Return the last N (timestamp, text) pairs for user turns."""
    messages = []
    with open(session_file, encoding="utf-8") as fh:
        for raw in fh:
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
                if text and not text.startswith("[Tool result"):
                    messages.append((ts, text[:200]))
            except Exception:
                continue
    return messages[-last_n:]


def save_checkpoint(session_file: Path, pct_used: float, turns: int) -> Path | None:
    """Write a checkpoint markdown to MEMORY_DIR; at most one per hour."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    now_local = datetime.now(LOCAL_TZ)
    stamp     = now_local.strftime("%Y%m%d_%H%M")

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
        "> Auto checkpoint — run `/session-summary` for a full AI-generated summary.",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    session_file = find_current_session()
    if not session_file:
        print(json.dumps({"systemMessage": f"[Claude_Code_Token_Status] No session file found in {PROJECT_DIR}"}))
        return

    (inp, cache_create, cache_read,
     output_total, turns, window_start,
     cost_inp, cost_cc, cost_cr, cost_out,
     last_model) = parse_usage(session_file)

    context_used      = cache_read + cache_create + inp
    context_remaining = max(0, CONTEXT_WINDOW - context_used)
    pct_used          = context_used / CONTEXT_WINDOW * 100 if context_used else 0

    # progress bar (width configurable via CLAUDE_TOKEN_BAR_WIDTH)
    filled = int(BAR_WIDTH * pct_used / 100)
    bar    = "█" * filled + "░" * (BAR_WIDTH - filled)

    # warnings + auto-checkpoint
    warn = checkpoint_note = ""
    if pct_used >= 90:
        saved = save_checkpoint(session_file, pct_used, turns)
        if saved:
            checkpoint_note = f"\n📌 Checkpoint saved: {saved.name}"
        warn = f"  ⚠️  ≥90% — run /session-summary then open a new session{checkpoint_note}"
    elif pct_used >= 75:
        warn = "  ⚠️  ≥75% — consider /session-summary to preserve progress"

    # reset countdown (rolling window — best available for Claude Code subscriptions)
    if window_start:
        now       = datetime.now(timezone.utc)
        reset_at  = window_start + timedelta(hours=USAGE_RESET_HOURS)
        remaining = reset_at - now
        if remaining.total_seconds() > 0:
            h, rem = divmod(int(remaining.total_seconds()), 3600)
            m = rem // 60
            reset_line = f"\nReset in: {h}h {m:02d}m  ({reset_at.astimezone(LOCAL_TZ).strftime('%H:%M')} local)"
        else:
            reset_line = "\nReset: window elapsed — usage available"
    else:
        reset_line = "\nReset: no recent activity (window reset)"

    # cost display
    session_cost = cost_inp + cost_cc + cost_cr + cost_out
    _, _, model_label = _model_pricing(last_model)
    rate, rate_src = (1.0, "USD") if CURRENCY == "USD" else _fetch_usd_to_ntd()
    if CURRENCY == "NTD":
        cur_label = f"NT$ ×{rate:.2f} ({rate_src})"
    else:
        cur_label = "USD"
    breakdown_parts = []
    if cost_inp > 0: breakdown_parts.append(f"in {_fmt_cost(cost_inp, rate)}")
    if cost_cc  > 0: breakdown_parts.append(f"cw {_fmt_cost(cost_cc,  rate)}")
    if cost_cr  > 0: breakdown_parts.append(f"cr {_fmt_cost(cost_cr,  rate)}")
    if cost_out > 0: breakdown_parts.append(f"out {_fmt_cost(cost_out, rate)}")
    breakdown  = "  [" + " + ".join(breakdown_parts) + "]" if breakdown_parts else ""
    cost_line  = f"\nAPI equiv. (est.): {_fmt_cost(session_cost, rate)} ({model_label}, {cur_label}){breakdown}"

    msg = (
        f"Token [{bar}] {pct_used:.1f}%{warn}\n"
        f"Used {context_used:,} / {CONTEXT_WINDOW:,}   "
        f"Remaining {context_remaining:,}   "
        f"Out {output_total:,}   ({turns} turns)"
        f"{cost_line}\n"
        f"Session: {session_file.name[:12]}…"
        f"{reset_line}"
    )
    print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    main()
