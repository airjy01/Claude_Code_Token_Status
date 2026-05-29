# Claude_Code_Token_Status

A Claude Code Stop hook that shows **token usage**, **session cost**, and **reset countdown** after every response.

Works with **all Claude Code plans**: Free, Pro, Max, and API (pay-per-token).  
Cost display = equivalent API pricing; useful as reference for subscription users, accurate for API users.

**Two modes:**
- **Estimate mode** (default, zero setup): rolling-window approximation from local JSONL
- **Official mode** (optional credentials): real plan utilization % and exact reset time from claude.ai API

```
Token [████████░░░░░░░░░░░░░░░░░░░░] 31.6%
Used 63,154 / 200,000   Remaining 136,846   Out 392,109   (618 turns)
API equiv. (est.): NT$217 (sonnet-4.6, NT$ ×31.43 (cached))  [in NT$0.03 + cw NT$24.6 + cr NT$124 + out NT$67.9]
Session: 067d788d-705…
Plan 5h: 20% used — reset in 2h 59m  (15:10 local)  ✓  |  7d: 2% (resets Thu 01:00)
```

Without credentials (estimate mode):
```
Rate limit: reset in 3h 07m  (15:40 local)  ~est
```

---

## Features

| Feature | Detail |
|---|---|
| **Context bar** | Visual progress bar (width configurable) + % used |
| **Token counts** | Used / remaining + output tokens + turn count |
| **Session cost** | Per-model estimate: input + cache-write + cache-read + output (NTD or USD) |
| **Official plan usage** | Real 5h utilization % + exact reset time from claude.ai API (requires credentials) |
| **Weekly usage** | 7-day utilization % and reset day (when official mode active) |
| **Reset countdown** | Official exact time `✓` or rolling-window estimate `~est` fallback |
| **Model detection** | Auto-detects from session JSONL; unknown models flagged as `(est.)` |
| **Cross-day tracking** | Shows today vs total turns for sessions spanning midnight |
| **75% warning** | Prompts to run `/session-summary` |
| **90%+ checkpoint** | Auto-saves last 30 user prompts to memory dir; once per hour max |
| **Exchange rate** | Live USD→NTD via open.er-api.com with 24h cache; falls back to Taiwan Bank rate |
| **Zero deps** | Pure Python 3.9+, no pip install |

---

## Install

### 1. Copy the script

```bash
curl -o ~/claude_code_token_status.py \
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

## Official API Setup (Optional)

Without setup, the reset countdown is a rolling-window estimate (`~est`).  
With setup, you get the **exact plan utilization % and reset time** (`✓`) — same data as claude.ai Settings → Usage.

**Why credentials are needed:** Claude Code CLI cannot access Anthropic's rate-limit data directly. The script calls the same internal API that the claude.ai web app uses, which requires browser session cookies.

### One-time setup (~2 minutes)

1. Open **chrome.ai/settings/usage** in Chrome
2. Press **F12** → **Network** tab → click **Fetch/XHR** filter → refresh the page (F5)
3. Click the **`usage`** request in the list
4. In the **Headers** panel, copy:
   - The full **Cookie:** header value (right-click → Copy value)
   - The org UUID from the **Request URL** (`/api/organizations/<UUID>/usage`)
5. Save to files:

```bash
echo '<paste full cookie string here>' > ~/.claude/.claude_cookies
echo '<paste UUID here>'               > ~/.claude/.claude_org_id
chmod 600 ~/.claude/.claude_cookies
```

**When to refresh:** The `cf_clearance` cookie expires periodically. When the `✓` disappears and `~est` returns, repeat steps 1–5.

### Environment variable alternative

```bash
export CLAUDE_COOKIES="<full cookie string>"
export CLAUDE_ORG_ID="<org UUID>"
```

Or use only `sessionKey` (may be blocked by Cloudflare without `cf_clearance`):

```bash
echo 'sk-ant-sid02-...' > ~/.claude/.claude_session_key
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CLAUDE_TOKEN_CONTEXT_WINDOW` | `200000` | Context window size |
| `CLAUDE_TOKEN_RESET_HOURS` | `5` | Usage window length for estimate fallback (hours) |
| `CLAUDE_TOKEN_TZ_OFFSET` | `8` | UTC offset (e.g. `-5` for US Eastern) |
| `CLAUDE_TOKEN_CHECKPOINT_DIR` | `~/.claude/projects/<slug>/memory` | Checkpoint save directory |
| `CLAUDE_TOKEN_MODEL` | auto | Override model for pricing |
| `CLAUDE_TOKEN_BAR_WIDTH` | `28` | Progress bar width in characters |
| `CLAUDE_TOKEN_CURRENCY` | `NTD` | Display currency: `NTD` or `USD` |
| `CLAUDE_TOKEN_USD_TO_NTD` | live rate | Manual USD→NTD override |
| `CLAUDE_COOKIES` | — | Full browser cookie string for official API |
| `CLAUDE_ORG_ID` | — | Organization UUID for official API |
| `CLAUDE_SESSION_KEY` | — | sessionKey cookie only (fallback) |

Example for US Eastern, USD display, wide bar:

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
| Free | ✅ | Estimate mode only |
| Pro | ✅ | Full support; official mode available |
| Max | ✅ | Full support; official mode available |
| API (pay-per-token) | ✅ | Cost display is actual cost |
| claude.ai Web | ❌ | No local JSONL, CLI only |

---

## How it works

**Project directory:** Auto-detects from `$PWD` → slug (`/home/user/proj` → `-home-user-proj`) → `~/.claude/projects/<slug>/`. Works for any user on any machine.

**Context window snapshot:** Uses the *last* assistant turn's token counts — not a sum.  
`cache_read` grows each turn (entire cached context is re-read), so summing would overcount.

**Cost calculation:** Sums per-turn charges across the session:  
`input × rate + cache_write × 1.25×rate + cache_read × 0.10×rate + output × out_rate`

**Official API mode:** Queries `https://claude.ai/api/organizations/{org_id}/usage` using browser session cookies. Returns `five_hour.utilization` (%) and `five_hour.resets_at` (exact UTC timestamp). Falls back silently to estimate if the request fails (expired cookies, network error, etc.).

**Estimate mode fallback:** Rolling window — earliest timestamp within the last 5 hours marks when the window started; add 5h to get reset time. Note: this only sees Claude Code activity; usage from claude.ai web or Claude Desktop (which shares the same pool per Anthropic's policy) is invisible to the estimate, causing it to drift later than the true reset.

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
