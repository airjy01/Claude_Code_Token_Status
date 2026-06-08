# Claude_Code_Token_Status

A Claude Code Stop hook that shows **context usage**, **session cost**, **official plan usage**, and **reset countdown** after every response.

Works with **all Claude Code plans**: Free, Pro, Max, and API (pay-per-token).

```
Context (65,575)  [█████████░░░░░░░░░░░░░░░░░░░] 33%  / 200,000   Rem 134,425   Out 60,121   (86 turns)
Token 5h:         [████████████████░░░░░░░░░░░░] 59% — reset in  0d 0h 57m  (13:00 06/08 Mon)
Token 7d:         [█████████████░░░░░░░░░░░░░░░] 48% — reset in  2d 12h 57m  (01:00 06/11 Thu)
API equiv. (est.): NT$75.8 (sonnet-4.6, NT$ ×31.65 (cached))  [in NT$0.01 + cw NT$12.0 + cr NT$35.2 + out NT$28.5]
Session: 27fd1a7a-59d8-4863-b5a4-23bebe09cd6c
```

---

## Features

| Feature | Detail |
|---|---|
| **Context bar** | Visual progress bar + % + remaining tokens, all on one line |
| **Token 5h bar** | Official claude.ai plan usage for the 5-hour window, with countdown + date/day |
| **Token 7d bar** | Official claude.ai plan usage for the 7-day window, with countdown + date/day |
| **Session cost** | Per-model estimate: input + cache-write + cache-read + output (NTD or USD) |
| **Model detection** | Auto-detects from session JSONL; unknown models flagged as `(est.)` |
| **75% warning** | Prompts to run `/session-summary` |
| **90%+ checkpoint** | Auto-saves last 30 user prompts to memory dir; once per hour max |
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

### 3. (Optional) Enable official plan usage display (Token 5h / 7d)

This requires a valid claude.ai session cookie. Without it, the Token 5h/7d bars won't appear.

**Step 1** — Run the one-time browser login (requires Playwright):

```bash
pip install playwright --break-system-packages
playwright install chromium
python3 ~/.claude/setup_playwright_auth.py
```

**Step 2** — Save your org UUID:

```bash
# Shown automatically during setup, or find it at:
# https://claude.ai/api/organizations  (field: "uuid")
echo 'your-org-uuid-here' > ~/.claude/.claude_org_id
```

**Step 3** — (Optional) Auto-refresh cookies daily via cron:

```bash
(crontab -l 2>/dev/null; echo "50 23 * * * python3 ~/.claude/refresh_cookies.py >> ~/.claude/cookie_refresh.log 2>&1") | crontab -
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CLAUDE_TOKEN_CONTEXT_WINDOW` | `200000` | Context window size |
| `CLAUDE_TOKEN_RESET_HOURS` | `5` | Usage window length (hours) |
| `CLAUDE_TOKEN_TZ_OFFSET` | `8` | UTC offset (e.g. `-5` for US Eastern) |
| `CLAUDE_TOKEN_CHECKPOINT_DIR` | `~/.claude/projects/<slug>/memory` | Checkpoint save directory |
| `CLAUDE_TOKEN_MODEL` | auto | Override model for pricing |
| `CLAUDE_TOKEN_BAR_WIDTH` | `28` | Progress bar width in characters |
| `CLAUDE_TOKEN_CURRENCY` | `NTD` | `NTD` or `USD` |
| `CLAUDE_COOKIES` | (file) | Full cookie string (overrides `~/.claude/.claude_cookies`) |

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

Cookie file locations (checked in order):

```
~/.claude/.claude_cookies   ← recommended (full cookie string, one line)
CLAUDE_COOKIES env var
CLAUDE_SESSION_KEY env var  ← sessionKey only (may be blocked by Cloudflare)
```

---

## Output explained

```
Context (65,575)  [█████████░░░░░░░░░░] 33%  / 200,000   Rem 134,425   Out 60,121   (86 turns)
│                  │                    │      │            │              │             │
│                  │                    │      total ctx    remaining      output        turns
│                  bar                  %
context tokens used (cache_read + cache_create + input)

Token 5h:  [████████████████░░░] 59% — reset in  0d 0h 57m  (13:00 06/08 Mon)
Token 7d:  [█████████████░░░░░░] 48% — reset in  2d 12h 57m  (01:00 06/11 Thu)
│           │                    │                │             │
│           bar                  plan %           countdown     local reset time + date + day
official claude.ai plan utilization (from usage API)
```

**Context tokens** = `cache_read + cache_creation + input` — the full context Claude processes each turn.  
**Out** = Claude's output tokens (not counted in context until the next turn).  
**Token 5h / 7d** = official plan usage percentage from `claude.ai/api/organizations/{org}/usage`. Only visible when cookies are configured.

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
| Free | ✅ | ✅ (with cookie) | |
| Pro | ✅ | ✅ (with cookie) | |
| Max | ✅ | ✅ (with cookie) | |
| API (pay-per-token) | ✅ | ✅ (with cookie) | Cost display is actual cost |
| claude.ai Web | ❌ | ❌ | No local JSONL, CLI only |

---

## How it works

**Session file:** Auto-detects from `$PWD` → slug (`/home/user/proj` → `-home-user-proj`) → `~/.claude/projects/<slug>/`. Falls back to scanning all projects for the most recent `.jsonl` if the current directory doesn't match (useful when Claude Code is launched from varying directories).

**Context window snapshot:** Uses the *last* assistant turn's token counts — not a sum. `cache_read` grows each turn (entire cached context is re-read), so summing would overcount.

**Cost calculation:** Sums per-turn charges across the session:  
`input × rate + cache_write × 1.25×rate + cache_read × 0.10×rate + output × out_rate`

**Token 5h/7d:** Calls `claude.ai/api/organizations/{org_id}/usage` with session cookies. Returns `utilization` (%) and `resets_at` (ISO timestamp). Raw token counts are not exposed by the API.

**90% checkpoint:** Writes `session_checkpoint_YYYYMMDD_HHMM.md` to memory dir with last 30 user prompts. Deduplication prevents multiple writes per hour.

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
- No external dependencies for core features
- `playwright` + Chromium for cookie auto-refresh (optional)

---

## License

MIT
