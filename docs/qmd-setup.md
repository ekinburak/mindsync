# qmd Setup

qmd is a local semantic search engine for markdown files. The LLM uses it to search your wiki when index.md navigation isn't enough.

## Install

```bash
npm install -g @tobilu/qmd
```

## Add your wiki as a collection

```bash
qmd collection add ~/path/to/wiki --name mywiki
qmd context add qmd://mywiki "Personal second brain"
qmd embed
```

Run `qmd embed` again after ingesting many new sources (rebuilds the vector index).

## CLI usage

```bash
qmd query "sleep habits"        # hybrid search (recommended)
qmd search "atomic habits"      # keyword only (fast)
qmd vsearch "decision making"   # vector only (semantic)
```

## MCP server (recommended)

Add to Claude Code `~/.claude/settings.json`:

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

With MCP configured, Claude calls qmd natively without shell commands.

## Re-embed after bulk ingestion

```bash
qmd embed
```
