"""Obsidian vault connector for Claude (MCP server).

Gives Claude five tools: list_notes, search_notes, read_note, create_note,
append_to_note. It can never delete or overwrite a note, and it can't reach
files outside the vault.

Set OBSIDIAN_VAULT to your vault's folder before starting.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

SKIP_DIRS = {".obsidian", ".trash", ".git"}
MAX_RESULTS = 50


def _vault() -> Path:
    raw = os.environ.get("OBSIDIAN_VAULT")
    if not raw:
        sys.exit("Set OBSIDIAN_VAULT to the full path of your Obsidian vault.")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"OBSIDIAN_VAULT is not a folder: {vault}")
    return vault


VAULT = _vault()
mcp = MCPServer(
    "obsidian",
    instructions=(
        "Tools for the user's Obsidian vault. Paths are relative to the vault "
        "root, e.g. 'Projects/Idea.md'. Search before creating to avoid duplicates."
    ),
)


def _resolve(rel: str) -> Path:
    """Turn a vault-relative path into an absolute one, refusing escapes."""
    rel = rel.strip().lstrip("/\\")
    if not rel:
        raise ToolError("Path is empty.")
    if not rel.lower().endswith(".md"):
        rel += ".md"
    path = (VAULT / rel).resolve()
    if not path.is_relative_to(VAULT):
        raise ToolError("Path is outside the vault.")
    if any(part in SKIP_DIRS for part in path.relative_to(VAULT).parts):
        raise ToolError("That folder is off limits.")
    return path


def _notes():
    for path in sorted(VAULT.rglob("*.md")):
        rel = path.relative_to(VAULT)
        if not any(part in SKIP_DIRS for part in rel.parts):
            yield path, rel.as_posix()


@mcp.tool()
def list_notes(folder: str = "") -> str:
    """List notes in the vault, optionally only those under a folder."""
    prefix = folder.strip().strip("/")
    names = [rel for _, rel in _notes() if not prefix or rel.startswith(prefix + "/")]
    if not names:
        return "No notes found."
    extra = f"\n...and {len(names) - 500} more" if len(names) > 500 else ""
    return "\n".join(names[:500]) + extra


@mcp.tool()
def search_notes(query: str) -> str:
    """Case-insensitive search of note titles and contents. Returns matching
    notes with the lines that matched."""
    q = query.strip().lower()
    if not q:
        return "Query is empty."
    results = []
    for path, rel in _notes():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = [ln.strip() for ln in text.splitlines() if q in ln.lower()][:3]
        if hits or q in rel.lower():
            snippet = "\n".join(f"    {h[:200]}" for h in hits)
            results.append(f"- {rel}" + (f"\n{snippet}" if snippet else ""))
        if len(results) >= MAX_RESULTS:
            results.append(f"(stopped at {MAX_RESULTS} results; refine the query)")
            break
    return "\n".join(results) or f"No notes match '{query}'."


@mcp.tool()
def read_note(path: str) -> str:
    """Read the full text of a note, e.g. 'Projects/Idea.md'."""
    p = _resolve(path)
    if not p.is_file():
        return f"No note at {path}. Try search_notes."
    return p.read_text(encoding="utf-8", errors="replace")


@mcp.tool()
def create_note(path: str, content: str) -> str:
    """Create a new note. Fails if the note already exists (use append_to_note)."""
    p = _resolve(path)
    if p.exists():
        return f"{path} already exists. Use append_to_note instead."
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Created {p.relative_to(VAULT).as_posix()}"


@mcp.tool()
def append_to_note(path: str, content: str) -> str:
    """Add text to the end of an existing note."""
    p = _resolve(path)
    if not p.is_file():
        return f"No note at {path}. Use create_note instead."
    existing = p.read_text(encoding="utf-8", errors="replace")
    sep = "" if existing.endswith("\n") or not existing else "\n"
    with p.open("a", encoding="utf-8") as f:
        f.write(f"{sep}{content}\n")
    return f"Appended to {p.relative_to(VAULT).as_posix()} at {datetime.now():%Y-%m-%d %H:%M}"


if __name__ == "__main__":
    mcp.run()
