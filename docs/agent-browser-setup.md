# agent-browser Setup (Optional)

agent-browser lets Claude browse the web autonomously — fetch live articles, extract content, take screenshots — without you copy-pasting anything.

## Install

```bash
npm install -g agent-browser
agent-browser install   # downloads Chrome for Testing
```

## MCP server

Add to Claude Code `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "agent-browser": {
      "command": "agent-browser",
      "args": ["mcp"]
    }
  }
}
```

## How it works with the wiki

With agent-browser configured, Claude can:
- Browse a URL you mention and extract the content for ingestion
- Search the web for sources related to a query
- Screenshot pages for visual reference

## Without agent-browser

Use `summarize <url>` instead — it covers most ingest use cases without a full browser.
