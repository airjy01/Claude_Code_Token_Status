# Claude_Code_Token_Status

A Claude Code Stop hook that shows **context usage**, **session cost**, **official plan usage**, and **reset countdown** after every response.

Works with **all Claude Code plans**: Free, Pro, Max, and API (pay-per-token).

Zero setup: the plan bars read the OAuth token Claude Code already writes to
`~/.claude/.credentials.json`. If it is missing, the reset countdown falls back
to a rolling-window estimate and the plan bars are hidden.

```
Context (225,925)  [█████████████████████░░░░░░░] 75%  / 300,000   Rem 74,075   Out 167,678   (147 turns)
Token 5h:          [██████████░░░░░░░░░░░░░░░░░░] 38% — reset in  0d 2h 31m  (18:00 07/31 Fri)
Token 7d:          [█░░░░░░░░░░░░░░░░░░░░░░░░░░░] 7% — reset in  5d 9h 31m  (01:00 08/06 Thu)
API equiv. (est.): NT$347 (claude-opus-5 (est.), NT$ ×32.38 (cached))  [in NT$0.03 + cw NT$45.7 + cr NT$221 + out NT$79.9]
Session: 4260e9cf-632b-4a66-8b08-dceb7b3e97cb
```

---

## Features

| Feature | Detail |
|---|---|
| **Context bar** | Visual progress bar + % + remaining tokens, all on one line |
| **Self-calibrating window** | Claude Code never writes the real context window to disk. Rather than guess, the denominator ratchets up from prompts that actually got a reply, so the bar can't read >100 % |
| **Token 5h bar** | Official plan usage for the 5-hour window, with countdown + date/day |
| **Token 7d bar** | Official plan usage for the 7-day window, with countdown + date/day |
| **Session cost** | Per-model estimate: input + cache-write + cache-read + output (NTD or USD) |
| **Model detection** | Auto-detects from session JSONL; unknown models flagged as `(est.)` |
| **75% warning** | Prompts to run `/session-summary` |
| **85%+ checkpoint** | Auto-saves recent *typed* prompts to memory dir; once per hour max |
| **Cross-project fallback** | Finds the most recent session JSONL even if Claude started from a different directory |
| **Zero deps** | Pure Python 3.9+, no pip install required |

---

## Why

Claude Code has no built-in display for context usage, session cost, or reset time.
This hook reads the local session JSONL and the official claude.ai usage API to show all of it — aligned, at a glance, after every response.

---

## Install

### 1. Copy the script

```bash
curl -o ~/scripts/claude_code_token_status.py \
  https://raw.githubusercontent.com/airjy01/Claude_Code_Token_Status/main/claude_code_token_status.py
```

Or clone:

```bash
git clone https://github.com/airjy01/Claude_Code_Token_Status
```

### 2. Add the Stop hook to `~/.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/scripts/claude_code_token_status.py"
          }
        ]
      }
    ]
  }
}
```

### 3. Official plan usage (Token 5h / 7d) — no setup

Claude Code writes an OAuth access token to `~/.claude/.credentials.json` and
refreshes it every session. The script reads that token and calls
`api.anthropic.com/api/oauth/usage` for real plan utilization and reset times.
Nothing to configure — the bars appear on the next response.

If you need to override the token (CI, a second account):

```bash
export CLAUDE_OAUTH_TOKEN='sk-ant-oat01-...'
```

Without a usable token the plan bars are hidden and the reset countdown falls
back to a rolling-window estimate (`~est`) computed from local timestamps.

> Earlier versions scraped `claude.ai` with browser session cookies
> (`.claude_cookies` / `.claude_org_id` / Playwright refresh). That path is gone —
> delete those files if you still have them.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CLAUDE_TOKEN_CONTEXT_WINDOW` | `200000` | Starting context window size. Treated as a floor: if a larger prompt is seen, the denominator ratchets up to the next 100k and persists in `~/.claude/.token_status` |
| `CLAUDE_TOKEN_RESET_HOURS` | `5` | Usage window length for estimate fallback (hours) |
| `CLAUDE_TOKEN_TZ_OFFSET` | `8` | UTC offset (e.g. `-5` for US Eastern) |
| `CLAUDE_TOKEN_CHECKPOINT_DIR` | `~/.claude/projects/<slug>/memory` | Checkpoint save directory |
| `CLAUDE_TOKEN_MODEL` | auto | Override model for pricing |
| `CLAUDE_TOKEN_BAR_WIDTH` | `28` | Progress bar width in characters |
| `CLAUDE_TOKEN_CURRENCY` | `NTD` | `NTD` or `USD` |
| `CLAUDE_TOKEN_USD_TO_NTD` | live rate | Pin the exchange rate instead of fetching it |
| `CLAUDE_OAUTH_TOKEN` | (auto) | Override the token read from `~/.claude/.credentials.json` |

Example (US Eastern, USD, wider bar):

```json
{
  "env": {
    "CLAUDE_TOKEN_TZ_OFFSET": "-5",
    "CLAUDE_TOKEN_BAR_WIDTH": "40",
    "CLAUDE_TOKEN_CURRENCY": "USD"
  }
}
```

---

## Output explained

```
Context (225,925)  [█████████████████████░░░░░░░] 75%  / 300,000   Rem 74,075   Out 167,678   (147 turns)
│                   │                             │      │            │             │             │
│                   │                             │      total ctx    remaining     output        turns
│                   bar                           %
context tokens used (cache_read + cache_create + input)

Token 5h:  [████████████████░░░] 59% — reset in  0d 0h 57m  (13:00 06/08 Mon)
Token 7d:  [█████████████░░░░░░] 48% — reset in  2d 12h 57m  (01:00 06/11 Thu)
│           │                    │                │             │
│           bar                  plan %           countdown     local reset time + date + day
official claude.ai plan utilization (from usage API)
```

**Context tokens** = `cache_read + cache_creation + input` — the full context Claude processes each turn.  
**total ctx** = calibrated window, not a published number. It is a *lower bound* proven by prompts that got a reply, rounded up to the next 100k.  
**Out** = Claude's output tokens (not counted in context until the next turn).  
**Token 5h / 7d** = official plan usage from `api.anthropic.com/api/oauth/usage`.

---

## Model Pricing (as of 2026-06)

Auto-detected from session JSONL. Verify current rates at [anthropic.com/pricing](https://www.anthropic.com/pricing).

| Model | Input | Output | Cache Write | Cache Read |
|---|---|---|---|---|
| claude-haiku-4.x | $1.00 | $5.00 | $1.25 | $0.10 |
| claude-sonnet-4.x | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-opus-4.x | $5.00 | $25.00 | $6.25 | $0.50 |

*(per 1M tokens)*

---

## Plan Compatibility

| Plan | Context bar | Token 5h/7d | Notes |
|---|---|---|---|
| Free | ✅ | ✅ | |
| Pro | ✅ | ✅ | |
| Max | ✅ | ✅ | |
| API (pay-per-token) | ✅ | — | No subscription window; cost display is actual cost |
| claude.ai Web | ❌ | ❌ | No local JSONL, CLI only |

---

## How it works

**Session file:** Auto-detects from `$PWD` → slug (`/home/user/proj` → `-home-user-proj`) → `~/.claude/projects/<slug>/`. Falls back to scanning all projects for the most recent `.jsonl` if the current directory doesn't match (useful when Claude Code is launched from varying directories).

**Context window snapshot:** Uses the *last* assistant turn's token counts — not a sum. `cache_read` grows each turn (entire cached context is re-read), so summing would overcount. Sub-agent turns (`isSidechain`) share the same JSONL and are skipped, so a sub-agent's smaller prompt can't be mistaken for the main loop's context.

**Window calibration:** Claude Code does not publish the real context window anywhere on disk, and a hardcoded 200 000 under-reports on larger models — a 297 316-token prompt was observed getting a normal reply, which the old code displayed as 149 %. The denominator now starts at `CLAUDE_TOKEN_CONTEXT_WINDOW` and ratchets upward whenever a bigger prompt succeeds, rounded up to the next 100k (context grows monotonically within a session, so calibrating to the exact maximum would pin the bar at 100 % forever). The calibrated value persists in `~/.claude/.token_status` and only ever moves up.

**Cost calculation:** Sums per-turn charges across the session:  
`input × rate + cache_write × 1.25×rate + cache_read × 0.10×rate + output × out_rate`

**Token 5h/7d:** Calls `api.anthropic.com/api/oauth/usage` with the Bearer token from `~/.claude/.credentials.json`. Returns `utilization` (%) and `resets_at` (ISO timestamp). Raw token counts are not exposed by the API.

**85% checkpoint:** Writes `session_checkpoint_YYYYMMDD_HHMM.md` to the memory dir with recent user prompts. Deduplication prevents multiple writes per hour. Turns Claude Code injected rather than ones you typed (`isMeta`: slash-command bodies, skill preambles, hook output) are filtered out, along with tool results and image placeholders — otherwise they bury the real prompts. The checkpoint captures *prompts only*; it cannot record what was done or verified, so treat it as a breadcrumb and run `/session-summary` for the real handoff.

---

## Files

| File | Purpose |
|---|---|
| `claude_code_token_status.py` | Main script — wire into Stop hook |
| `session-summary.md` | `/session-summary` slash command — AI-generated session summary |

---

## Requirements

- Python 3.9+
- Claude Code CLI (any version)
- No external dependencies

---

## License

MIT
