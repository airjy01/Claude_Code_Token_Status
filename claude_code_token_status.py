#!/usr/bin/env python3
"""
Claude_Code_Token_Status — Claude Code Stop hook.

Displays after every response:
  - Context window usage bar + %
  - Token counts (used / remaining / turns) + output tokens
  - Estimated session cost (per-model, with cache pricing)
  - Official plan usage % + exact reset time (when credentials configured)
  - Usage-window reset countdown (rolling-window estimate fallback)
  - Auto-checkpoint at 85%+ usage; warns at 75%+

Works for Free / Pro / Max / API users — any plan that runs Claude Code CLI.
Cost display is equivalent API pricing; subscription users see a reference value.

Auto-detects project directory from $PWD — no hardcoded paths.

Environment variables (all optional):
  CLAUDE_TOKEN_CONTEXT_WINDOW   context window size          (default: 200000,
                                then calibrated upward from the largest prompt
                                that actually got a reply — see observed_window_floor)
  CLAUDE_TOKEN_RESET_HOURS      usage window length hours    (default: 5)
  CLAUDE_TOKEN_TZ_OFFSET        UTC offset, e.g. -5 for EST  (default: 8)
  CLAUDE_TOKEN_CHECKPOINT_DIR   where to save checkpoints    (default: ~/.claude/projects/<slug>/memory)
  CLAUDE_TOKEN_MODEL            override model for pricing   (default: auto from JSONL)
  CLAUDE_TOKEN_BAR_WIDTH        progress bar character width (default: 28)
  CLAUDE_TOKEN_CURRENCY         display currency: NTD or USD (default: NTD)
  CLAUDE_TOKEN_USD_TO_NTD       USD → NTD exchange rate      (default: 31.5)

Official plan usage (5h/7d bars) — no setup needed:
  Reads OAuth token automatically from ~/.claude/.credentials.json (written by Claude Code).
  Token auto-refreshed each Claude Code session. Override via env var:
    CLAUDE_OAUTH_TOKEN            OAuth access token (sk-ant-oat01-...)
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

def _default_context_window() -> int:
    # settings.json model 帶 [1m] 尾碼 = 1M context beta
    try:
        model = json.loads((Path.home() / ".claude" / "settings.json").read_text()).get("model", "")
        if "[1m]" in model:
            return 1_000_000
    except Exception:
        pass
    return 200_000

# ── Configurable via environment variables ────────────────────────────────────
CONTEXT_WINDOW    = int(os.environ.get("CLAUDE_TOKEN_CONTEXT_WINDOW", 0)) or _default_context_window()
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

# ── Official API credentials (optional) ───────────────────────────────────────
_ORG_ID_FILE      = CLAUDE_DIR / ".claude_org_id"   # legacy, unused but kept for compat


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
    """Return the JSONL for the current session, falling back to most recent across all projects."""
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")

    def _search_dir(d: Path):
        if not d.exists():
            return []
        files = sorted(d.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        if session_id:
            for f in files:
                if session_id in f.name:
                    return [f]
        return files

    # 1. 先找當前 project 目錄
    files = _search_dir(PROJECT_DIR)
    if files:
        return files[0]

    # 2. Fallback：搜尋所有 projects 目錄中最新的 .jsonl（跨 project 支援）
    projects_root = CLAUDE_DIR / "projects"
    if projects_root.exists():
        all_jsonl = []
        for proj_dir in projects_root.iterdir():
            if proj_dir.is_dir():
                all_jsonl.extend(proj_dir.glob("*.jsonl"))
        if all_jsonl:
            all_jsonl.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            if session_id:
                for f in all_jsonl:
                    if session_id in f.name:
                        return f
            return all_jsonl[0]

    return None


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
      max_prompt                   — largest single-turn prompt seen this session;
                                     used to self-calibrate CONTEXT_WINDOW upward
      output_total                 — cumulative output tokens across session
      turns                        — assistant turn count (all-time in session)
      turns_today                  — assistant turn count for today's date only
      window_start                 — earliest timestamp within rolling reset window
      cost_inp, cost_cc, cost_cr,
      cost_out                     — cumulative USD costs per category
      last_model                   — model id from last assistant turn

    Reset note: Anthropic Rate Limits API (Apr 2026) is admin-only; Stop hooks
    don't receive rate-limit response headers (issue #36056, pending).
    Rolling-window calculation is the best available method for subscription users.
    """
    last_inp = last_cc = last_cr = max_prompt = 0
    output_total = turns = turns_today = 0
    cost_inp = cost_cc = cost_cr = cost_out = 0.0
    window_start = None
    last_model: str = os.environ.get("CLAUDE_TOKEN_MODEL", "")

    now    = datetime.now(timezone.utc)
    today  = now.date()
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

                    # Sub-agent turns live in the same JSONL; they must not be
                    # mistaken for the main loop's context snapshot.
                    if not entry.get("isSidechain"):
                        last_inp   = t_inp
                        last_cc    = t_cc
                        last_cr    = t_cr
                        max_prompt = max(max_prompt, t_inp + t_cc + t_cr)
                    output_total += t_out
                    turns        += 1
                    if ts and ts.date() == today:
                        turns_today += 1

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

    return (last_inp, last_cc, last_cr, max_prompt,
            output_total, turns, turns_today, window_start,
            cost_inp, cost_cc, cost_cr, cost_out, last_model)


def observed_window_floor() -> int:
    """Window already calibrated in a previous run (0 if none).

    Claude Code does not write the real context window anywhere on disk, so the
    hardcoded 200 000 default under-reports on models with a bigger window and
    the bar reads >100 % (observed: a 297 316-token prompt answered normally).
    Ratcheting the denominator up from prompts that actually got a reply keeps
    the bar honest without inventing a number; it only ever moves upward.
    """
    try:
        return int(json.loads((CLAUDE_DIR / ".token_status").read_text()).get("limit", 0))
    except Exception:
        return 0


# Not typed by the user: slash-command plumbing, skill preambles injected as user
# turns, image placeholders, tool plumbing. Keeping them buries the real prompts.
_NOISE_PREFIXES = (
    "[Tool result", "[Image:", "[Request interrupted",
    "<local-command-", "<command-name>", "<command-message>", "<command-args>",
    "<system-reminder>", "<bash-", "<user-prompt-submit-hook>",
    "Caveat: The messages below",
    "Base directory for this skill:",
)


def extract_user_messages(session_file: Path, last_n: int = 30) -> list[tuple]:
    """Return the last N (timestamp, text) pairs for genuine user turns."""
    messages = []
    with open(session_file, encoding="utf-8") as fh:
        for raw in fh:
            try:
                d   = json.loads(raw)
                msg = d.get("message", {})
                ts  = parse_ts(d.get("timestamp"))
                # isMeta marks turns Claude Code injected rather than ones the
                # user typed: slash-command bodies, skill preambles, hook output.
                if msg.get("role") != "user" or d.get("isMeta") or d.get("isSidechain"):
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
                if text and not text.startswith(_NOISE_PREFIXES):
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
        f"### Recent user prompts (last {len(messages)})",
        "",
    ]
    for ts, text in messages:
        ts_str = ts.astimezone(LOCAL_TZ).strftime("%H:%M") if ts else "??:??"
        lines.append(f"- `{ts_str}` {text}")
    lines += [
        "",
        "> Auto checkpoint — prompts only. Run `/session-summary` before opening a new"
        " session; this file cannot record what was done, verified, or left unfinished.",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def session_start_ts(session_file: Path) -> datetime | None:
    """Return the timestamp of the first entry in the session file."""
    with open(session_file, encoding="utf-8") as fh:
        for raw in fh:
            try:
                d  = json.loads(raw)
                ts = parse_ts(d.get("timestamp"))
                if ts:
                    return ts
            except Exception:
                continue
    return None


# ── Official usage API (via OAuth token from ~/.claude/.credentials.json) ──────
# Uses api.anthropic.com/api/oauth/usage — no browser cookies needed.
# Access token auto-refreshed by Claude Code each session (~60min TTL).
# Endpoint discovered: anthropic-beta: oauth-2025-04-20

_CREDENTIALS_FILE = CLAUDE_DIR / ".credentials.json"
_LAST_USAGE_ERROR = ""


def _read_oauth_token() -> str | None:
    """Return OAuth accessToken from ~/.claude/.credentials.json, or None."""
    # env var override
    token = os.environ.get("CLAUDE_OAUTH_TOKEN", "").strip()
    if token:
        return token
    try:
        data = json.loads(_CREDENTIALS_FILE.read_text())
        token = data.get("claudeAiOauth", {}).get("accessToken", "").strip()
        return token or None
    except Exception:
        return None


def _fetch_official_usage(token: str, _unused: str = "") -> dict | None:
    """Query api.anthropic.com/api/oauth/usage with Bearer token. Returns JSON or None."""
    global _LAST_USAGE_ERROR
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError

    _LAST_USAGE_ERROR = ""
    req = Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
            "content-type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return json.loads(resp.read())
            _LAST_USAGE_ERROR = f"http_{resp.status}"
    except HTTPError as e:
        _LAST_USAGE_ERROR = f"http_{e.code}"
    except Exception:
        _LAST_USAGE_ERROR = "request_failed"
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    session_file = find_current_session()
    if not session_file:
        print(json.dumps({"systemMessage": f"[Claude_Code_Token_Status] No session file found in {PROJECT_DIR}"}))
        return

    (inp, cache_create, cache_read, max_prompt,
     output_total, turns, turns_today, window_start,
     cost_inp, cost_cc, cost_cr, cost_out,
     last_model) = parse_usage(session_file)

    # A prompt that got a reply proves the window is at least that big. Context
    # grows monotonically within a session, so calibrating to max_prompt exactly
    # would pin the bar at 100 % forever — round up to the next 100k instead.
    window = max(CONTEXT_WINDOW, observed_window_floor())
    if max_prompt > window:
        window = -(-max_prompt // 100_000) * 100_000

    # Try official API for accurate plan usage (non-blocking; falls back to estimate)
    # Uses OAuth token from ~/.claude/.credentials.json — no browser cookies needed.
    oauth_token = _read_oauth_token()
    official = _fetch_official_usage(oauth_token) if oauth_token else None
    token_expired = (oauth_token is not None) and (official is None) and _LAST_USAGE_ERROR in {"http_401", "http_403"}

    context_used      = cache_read + cache_create + inp
    context_remaining = max(0, window - context_used)
    pct_used          = context_used / window * 100 if context_used else 0

    # progress bar (width configurable via CLAUDE_TOKEN_BAR_WIDTH)
    filled = int(BAR_WIDTH * pct_used / 100)
    bar    = "█" * filled + "░" * (BAR_WIDTH - filled)

    # warnings + auto-checkpoint
    warn = checkpoint_note = ""
    if pct_used >= 85:
        saved = save_checkpoint(session_file, pct_used, turns)
        if saved:
            checkpoint_note = f"\n📌 Checkpoint saved: {saved.name}"
        warn = f"  ⚠️  ≥85% — run /session-summary then open a new session{checkpoint_note}"
    elif pct_used >= 75:
        warn = "  ⚠️  ≥75% — consider /session-summary to preserve progress"

    # cross-day session note
    now_local   = datetime.now(LOCAL_TZ)
    start_ts    = session_start_ts(session_file)
    cross_day_note = ""
    if start_ts:
        start_local = start_ts.astimezone(LOCAL_TZ)
        if start_local.date() < now_local.date():
            turns_prev = turns - turns_today
            cross_day_note = (
                f"\n📅 Session from {start_local.strftime('%b %d')} — "
                f"{turns_prev} turns carried from previous day(s)"
            )

    # turns display: show today vs total when session spans multiple days
    if turns_today < turns:
        turns_display = f"({turns_today} today / {turns} total turns)"
    else:
        turns_display = f"({turns} turns)"

    # Rate limit line: official API data takes priority over rolling-window estimate
    now_utc = datetime.now(timezone.utc)
    ctx_label = f"Context ({context_used:,})"
    COL = max(len(ctx_label), len("Token 5h:"), len("Token 7d:")) + 2

    if official and official.get("five_hour"):
        fh       = official["five_hour"]
        util_5h  = fh["utilization"]
        filled_5h = int(BAR_WIDTH * util_5h / 100)
        bar_5h    = "█" * filled_5h + "░" * (BAR_WIDTH - filled_5h)
        reset_dt = parse_ts(fh.get("resets_at"))
        lbl_5h = "Token 5h:".ljust(COL)
        if reset_dt and (remaining := reset_dt - now_utc).total_seconds() > 0:
            total_sec_5h = int(remaining.total_seconds())
            d5, r5 = divmod(total_sec_5h, 86400)
            h5, r5m = divmod(r5, 3600)
            m5 = r5m // 60
            reset_local = reset_dt.astimezone(LOCAL_TZ)
            reset_line = (
                f"\n{lbl_5h}[{bar_5h}] {util_5h:.0f}% — reset in  {d5}d {h5}h {m5:02d}m"
                f"  ({reset_local.strftime('%H:%M %m/%d %a')})"
            )
        else:
            reset_line = f"\n{lbl_5h}[{bar_5h}] ✅ RESET — fresh capacity"
        if official.get("seven_day"):
            sd = official["seven_day"]
            util_7d = sd["utilization"]
            filled_7d = int(BAR_WIDTH * util_7d / 100)
            bar_7d = "█" * filled_7d + "░" * (BAR_WIDTH - filled_7d)
            lbl_7d = "Token 7d:".ljust(COL)
            reset_7d_dt = parse_ts(sd.get("resets_at"))
            if reset_7d_dt and (rem_7d := reset_7d_dt - now_utc).total_seconds() > 0:
                total_sec_7d = int(rem_7d.total_seconds())
                d7, r7 = divmod(total_sec_7d, 86400)
                h7, r7m = divmod(r7, 3600)
                m7 = r7m // 60
                reset_7d_local = reset_7d_dt.astimezone(LOCAL_TZ)
                reset_line += (
                    f"\n{lbl_7d}[{bar_7d}] {util_7d:.0f}% — reset in  {d7}d {h7}h {m7:02d}m"
                    f"  ({reset_7d_local.strftime('%H:%M %m/%d %a')})"
                )
            elif reset_7d_dt:
                reset_line += f"\n{lbl_7d}[{bar_7d}] ✅ RESET — fresh capacity"
    elif window_start:
        reset_at  = window_start + timedelta(hours=USAGE_RESET_HOURS)
        remaining = reset_at - now_utc
        if remaining.total_seconds() > 0:
            h, rem = divmod(int(remaining.total_seconds()), 3600)
            m = rem // 60
            reset_line = f"\nRate limit: reset in {h}h {m:02d}m  ({reset_at.astimezone(LOCAL_TZ).strftime('%H:%M')} local)  ~est"
        else:
            reset_line = "\n✅ Rate limit: RESET — fresh capacity"
    else:
        reset_line = "\n✅ Rate limit: RESET — fresh capacity"

    if token_expired:
        reset_line += "\n⚠️  Token 5h/7d: OAuth token expired — run `claude` once to auto-refresh"
    elif oauth_token and official is None and _LAST_USAGE_ERROR:
        if _LAST_USAGE_ERROR == "http_429":
            reset_line += "\n⚠️  Token 5h/7d: usage API rate limited (429) — 暫時限流，稍後自動恢復"
        else:
            reset_line += f"\n⚠️  Token 5h/7d unavailable: usage API request failed ({_LAST_USAGE_ERROR})"

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
        f"\n{ctx_label.ljust(COL)}[{bar}] {pct_used:.0f}%"
        f"  / {window:,}   Rem {context_remaining:,}   Out {output_total:,}   {turns_display}{warn}"
        f"{reset_line}"
        f"{cross_day_note}"
        f"{cost_line}\n"
        f"Session: {session_file.stem}"
    )
    print(json.dumps({"systemMessage": msg}))

    # Persist for CLAUDE.md "每次回覆前讀取" rule
    try:
        now_utc = datetime.now(timezone.utc)
        pct_5h = official["five_hour"]["utilization"] if official and official.get("five_hour") else None
        reset_5h = ""
        if official and official.get("five_hour", {}).get("resets_at"):
            rt = parse_ts(official["five_hour"]["resets_at"])
            if rt and (rt - now_utc).total_seconds() > 0:
                h, rem = divmod(int((rt - now_utc).total_seconds()), 3600)
                reset_5h = f"{h}h {rem // 60:02d}m"
        pct_7d = official["seven_day"]["utilization"] if official and official.get("seven_day") else None
        reset_7d = ""
        if official and official.get("seven_day", {}).get("resets_at"):
            rt7 = parse_ts(official["seven_day"]["resets_at"])
            if rt7 and (rt7 - now_utc).total_seconds() > 0:
                d7, rem7 = divmod(int((rt7 - now_utc).total_seconds()), 86400)
                h7, rem7m = divmod(rem7, 3600)
                reset_7d = f"{d7}d {h7}h {rem7m // 60:02d}m"
        remaining_pct = round(100 - pct_used, 1)
        cache_data = {
            "used": context_used, "limit": window,
            "remaining": context_remaining,
            "output_total": output_total,
            "remaining_pct": remaining_pct, "pct_used": round(pct_used, 1),
            "reset_in": reset_5h,
            "plan_5h_pct": pct_5h, "plan_5h_reset": reset_5h,
            "plan_7d_pct": pct_7d, "plan_7d_reset": reset_7d,
            "session": session_file.name[:8],
            "updated_at": now_utc.isoformat(),
        }
        (CLAUDE_DIR / ".token_status").write_text(
            json.dumps(cache_data, ensure_ascii=False)
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
