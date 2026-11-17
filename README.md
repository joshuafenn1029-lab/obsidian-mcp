# Obsidian connector for Claude

A small local server that lets Claude (Desktop or Claude Code) work with your Obsidian vault.

**What Claude can do:** list notes, search notes, read a note, create a new note, append to a note.
**What it can't do:** delete or overwrite notes, or touch anything outside your vault (or inside `.obsidian`, `.trash`, `.git`).

## 1. Install (once)

You need Python 3.10 or newer.

```bash
cd obsidian-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

On Windows, use `.venv\Scripts\pip` instead of `.venv/bin/pip`.

## 2. Connect it to Claude

You need two full paths:
- **PYTHON**: `/full/path/to/obsidian-mcp/.venv/bin/python` (Windows: `...\.venv\Scripts\python.exe`)
- **VAULT**: the folder Obsidian opens, e.g. `/Users/you/Documents/MyVault`

### Claude Desktop

Open Settings → Developer → Edit Config, and add:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "PYTHON",
      "args": ["/full/path/to/obsidian-mcp/server.py"],
      "env": { "OBSIDIAN_VAULT": "VAULT" }
    }
  }
}
```

Then restart Claude Desktop. "obsidian" should appear in the tools menu.

### Claude Code

```bash
claude mcp add obsidian -e OBSIDIAN_VAULT="VAULT" -- PYTHON /full/path/to/obsidian-mcp/server.py
```

## 3. Try it

- "Search my vault for notes about tomatoes."
- "Read Projects/Garden and summarize it."
- "Create a note in Daily/ for today with what we just discussed."

## Notes

- Paths are relative to the vault, e.g. `Projects/Idea.md` (the `.md` is optional).
- Search is a plain text match on titles and contents, and returns up to 50 notes.
- Back up your vault (or use Obsidian Sync / git) as you would before letting any tool write to it.
