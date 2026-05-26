# Session Summary & Memory Save

Review the current session, generate a structured summary of all tasks completed, and save it to memory for future sessions.

## Instructions

1. Review the conversation history in this session
2. Generate a structured summary following the format below
3. Save it as a new memory file using the Write tool at:
   `~/.claude/projects/-home-airjy/memory/session_summary_YYYYMMDD.md`
4. Update `~/.claude/projects/-home-airjy/memory/MEMORY.md` to include a pointer to the new file
5. Report what was saved

## Summary Format

```markdown
---
name: session-summary-YYYYMMDD
description: Session summary — YYYY-MM-DD: <3-5 word topic description>
metadata:
  type: project
---

## Session Summary YYYY-MM-DD HH:MM 台灣時間

### ✅ 完成的任務
- Task 1: <what was done and what files were changed>
- Task 2: ...

### 📁 修改的檔案
- `path/to/file` — <what changed>

### 🔧 關鍵技術決策
- <decision and why>

### ⏳ 未完成 / 待追蹤
- <pending items or known issues>

### 💡 重要發現
- <non-obvious things discovered that future sessions should know>
```

## Arguments
$ARGUMENTS — optional focus area or tag (e.g., "hermes", "daily-monitor"). If provided, emphasize that area in the summary.

## Notes
- Be concise but complete — future sessions will rely on this
- Include file paths and specific function/variable names where relevant
- Do NOT include conversation meta-commentary ("the user asked...", "I then...")
- Focus on WHAT changed and WHY, not the back-and-forth
