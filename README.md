# Claude_Code_Token_Status

A Claude Code Stop hook that shows **token usage**, **session cost**, and **reset countdown** after every response.

Works with **all Claude Code plans**: Free, Pro, Max, and API (pay-per-token).
Cost display = equivalent API pricing; useful as reference for subscription users, accurate for API users.

```
Token [████████░░░░░░░░░░░░░░░░░░░░] 31.6%
Used 63,154 / 200,000   Remaining 136,846   Out 392,109   (618 turns)
Cost: ~$27.860 (sonnet-4.6)  [in $0.0127 + cw $5.6347 + cr $16.3305 + out $5.8816]
Session: fb90a0cb-352…
Reset in: 0h 58m  (19:13 local)
```

---

## Features

| Feature | Detail |
|---|---|
| **Context bar** | Visual progress bar (width configurable) + % used |
| **Token counts** | Used / remaining + output tokens + turn count |
| **Session cost** | Per-model USD estimate: input + cache-write + cache-read + output |
| **Model detection** | Auto-detects from session JSONL; unknown models flagged as `(est.)` |
| **Reset countdown** | Rolling-window estimate: earliest msg in last N hours → reset time |
| **75% warning** | Prompts to run `/session-summary` |
| **90%+ checkpoint** | Auto-saves last 30 user prompts to memory dir; once per hour max |
| **Zero deps** | Pure Python 3.9+, no pip install |

---

## Why

Claude Code has no built-in display for context usage, session cost, or reset time.
This hook reads the local session JSONL and calculates all three — no external API calls.

> **Reset time accuracy:** The Anthropic Rate Limits API (Apr 2026) is admin-only and
> not accessible to subscription users. Stop hooks don't receive rate-limit response
> headers ([issue #36056](https://github.com/anthropics/claude-code/issues/36056), pending).
> The rolling-window method used here is the most accurate available approach.

---

## Install

### 1. Copy the script

```bash
curl -o ~/claude_code_token_status.py \
  https://raw.githubusercontent.com/YOUR_USERNAME/Claude_Code_Token_Status/main/claude_code_token_status.py
```

Or clone:

```bash
git clone https://github.com/YOUR_USERNAME/Claude_Code_Token_Status
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
            "command": "python3 ~/claude_code_token_status.py"
          }
        ]
      }
    ]
  }
}
```

### 3. (Optional) Add the `/session-summary` slash command

```bash
mkdir -p ~/.claude/commands
cp session-summary.md ~/.claude/commands/session-summary.md
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

Example for US Eastern, wide bar:

```json
{
  "env": {
    "CLAUDE_TOKEN_TZ_OFFSET": "-5",
    "CLAUDE_TOKEN_BAR_WIDTH": "40"
  }
}
```

---

## Model Pricing (as of 2026-05)

Auto-detected from session JSONL. Verify current rates at [anthropic.com/pricing](https://www.anthropic.com/pricing).

| Model | Input | Output | Cache Write | Cache Read |
|---|---|---|---|---|
| claude-haiku-4.x | $1.00 | $5.00 | $1.25 | $0.10 |
| claude-sonnet-4.x | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-opus-4.x | $5.00 | $25.00 | $6.25 | $0.50 |

*(per 1M tokens)*

---

## Plan Compatibility

| Plan | Works | Notes |
|---|---|---|
| Free | ✅ | Same JSONL format |
| Pro | ✅ | Full support |
| Max | ✅ | Full support |
| API (pay-per-token) | ✅ | Cost display is actual cost |
| claude.ai Web | ❌ | No local JSONL, CLI only |

---

## How it works

**Project directory:** Auto-detects from `$PWD` → slug (`/home/user/proj` → `-home-user-proj`) → `~/.claude/projects/<slug>/`. Works for any user on any machine.

**Context window snapshot:** Uses the *last* assistant turn's token counts — not a sum.
`cache_read` grows each turn (entire cached context is re-read), so summing would overcount.

**Cost calculation:** Sums per-turn charges across the session:
`input × rate + cache_write × 1.25×rate + cache_read × 0.10×rate + output × out_rate`

**Reset countdown:** Rolling window — earliest timestamp within the last 5 hours marks when the window started; add 5h to get reset time. Accurate for long-running sessions spanning multiple windows.

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
- No external dependencies

---

## License

MIT
