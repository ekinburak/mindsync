# qmd Setup

qmd is a local semantic search engine for markdown files. The LLM uses it to search your wiki when index.md navigation isn't enough.

## Install

Project-local install:

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool qmd
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd)
```

Global install:

```bash
npm install -g @tobilu/qmd
```

## Add your wiki as a collection

```bash
"$QMD" collection add ~/path/to/wiki --name mywiki
"$QMD" context add qmd://mywiki "Personal second brain"
"$QMD" embed
```

Run `qmd embed` again after ingesting many new sources (rebuilds the vector index).

## CLI usage

```bash
"$QMD" query "sleep habits"        # hybrid search (recommended)
"$QMD" search "atomic habits"      # keyword only (fast)
"$QMD" vsearch "decision making"   # vector only (semantic)
```

## MCP server (recommended)

Add to your agent MCP config. For Claude Code, use `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"]
    }
  }
}
```

With MCP configured, supported agents call qmd natively without shell commands.

## Re-embed after bulk ingestion

```bash
qmd embed
```
