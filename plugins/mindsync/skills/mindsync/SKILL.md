---
name: mindsync
description: Use when initializing, ingesting, querying, linting, charting, searching, or exporting a mindsync LLM Wiki vault. Supports Codex and OpenClaw through AGENTS.md plus the deterministic scripts/mindsync.py helper.
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd", "@steipete/summarize"]
    optional:
      npm:
        agent-browser: "agent-browser"
---

# mindsync

mindsync implements the LLM Wiki pattern: immutable/append-only raw sources are
compiled by an agent into a linked markdown wiki, then queried, linted, visualized,
and exported.

## First Checks

Work from the vault root when possible. Read `AGENTS.md` first if it exists.
Use `scripts/mindsync.py` for deterministic work. If the helper is missing, ask
the user to run the project-local installer from the mindsync repo.

## Core Commands

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool qmd --tool summarize
python3 scripts/mindsync.py queue-scan --vault .
python3 scripts/mindsync.py pending --vault .
python3 scripts/mindsync.py lint --vault .
python3 scripts/mindsync.py chart --vault . --data <data.csv> --title "<title>"
python3 scripts/mindsync.py export-training --vault .
python3 scripts/mindsync.py embed --vault .
python3 scripts/mindsync.py doctor --vault .
```

## Agent Responsibilities

- Use the helper for queues, hashes, scaffolding, charts, deterministic lint, and exports.
- Use the model for semantic compilation, summaries, cross-links, contradictions, captions, and synthesis.
- Treat `raw/` as append-only. Create new raw records when fetching sources, but never edit or delete existing raw files.
- Update `index.md` and append to `log.md` after every durable wiki change.
- For Codex, this plugin is the discovery layer; `AGENTS.md` is the project instruction layer.
- For OpenClaw, use this `SKILL.md` metadata for required binaries and install hints.
