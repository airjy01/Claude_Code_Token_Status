# claude-token-status

A Claude Code Stop hook that shows **token usage**, **context remaining**, and **usage-window reset countdown** after every response.

Also auto-saves a checkpoint when usage reaches 90 %, and provides a `/session-summary` slash command to generate a full AI-written summary saved to memory.

![screenshot](https://i.imgur.com/placeholder.png)

```
Token [█████████████████░░░░░░░░░░░] 62.3%
Used 124,651 / 200,000   Remaining 75,349   (47 turns)
Session: fb90a0cb-352…
Reset in: 3h 12m  (21:00 local)
```

---

## Why

Claude Code has no built-in display for:
- How much of the context window is used
- When the 5-hour usage window resets

This hook reads the local session JSONL file and calculates both — with no external API calls.

---

## Install

### 1. Copy the script

```bash
curl -o ~/claude_token_status.py \
  https://raw.githubusercontent.com/YOUR_USERNAME/claude-token-status/main/claude_token_status.py
```

Or clone and symlink:

```bash
git clone https://github.com/YOUR_USERNAME/claude-token-status
ln -s $(pwd)/claude-token-status/claude_token_status.py ~/claude_token_status.py
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
            "command": "python3 ~/claude_token_status.py"
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

Then run `/session-summary` in Claude Code to get a full AI-generated summary saved to memory.

---

## Configuration

All defaults can be overridden via environment variables in `~/.claude/settings.json` or your shell profile:

| Variable | Default | Description |
|---|---|---|
| `CLAUDE_TOKEN_CONTEXT_WINDOW` | `200000` | Model context window size |
| `CLAUDE_TOKEN_RESET_HOURS` | `5` | Claude Code Pro usage window (hours) |
| `CLAUDE_TOKEN_TZ_OFFSET` | `8` | Local timezone UTC offset (e.g. `-5` for EST) |
| `CLAUDE_TOKEN_CHECKPOINT_DIR` | `~/.claude/projects/<slug>/memory` | Where to save 90%+ checkpoints |

Example for US Eastern time with Claude Max (longer window):

```json
{
  "env": {
    "CLAUDE_TOKEN_TZ_OFFSET": "-5",
    "CLAUDE_TOKEN_RESET_HOURS": "5"
  }
}
```

---

## How it works

**Project directory detection**

Claude Code stores session files under `~/.claude/projects/<slug>/` where `<slug>` is your working directory path with `/` replaced by `-`. The script auto-detects this from `$PWD` — no hardcoded paths.

**Reset countdown**

Uses a rolling window: finds the earliest message timestamp within the last `RESET_HOURS` hours, not the session start time. This gives accurate countdowns even for long-running sessions that span multiple usage windows.

**90% checkpoint**

When usage hits 90%+, the script automatically writes a lightweight markdown file listing the last 30 user prompts to the memory directory. One checkpoint per hour maximum. Pair with `/session-summary` for a full AI-generated summary.

---

## Files

| File | Purpose |
|---|---|
| `claude_token_status.py` | Main script — wire into Stop hook |
| `session-summary.md` | Custom slash command — generates full session summary |

---

## Requirements

- Python 3.9+
- Claude Code (any version)
- No external dependencies

---

## License

MIT
