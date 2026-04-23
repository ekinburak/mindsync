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

Read `AGENTS.md` first if it exists. New project-local vaults usually live in
`mindsync/`; the project root `AGENTS.md` may be a pointer to
`mindsync/AGENTS.md`. Use the vault-local `scripts/mindsync.py` for deterministic
work. If the helper is missing, ask the user to run the project-local installer
from the mindsync repo.

## Core Commands

```bash
python3 mindsync/scripts/mindsync.py ensure-tools --vault mindsync --tool qmd --tool summarize
python3 mindsync/scripts/mindsync.py queue-scan --vault mindsync
python3 mindsync/scripts/mindsync.py pending --vault mindsync
python3 mindsync/scripts/mindsync.py lint --vault mindsync
python3 mindsync/scripts/mindsync.py chart --vault mindsync --data <data.csv> --title "<title>"
python3 mindsync/scripts/mindsync.py export-training --vault mindsync
python3 mindsync/scripts/mindsync.py embed --vault mindsync
python3 mindsync/scripts/mindsync.py doctor --vault mindsync
```

## Agent Responsibilities

- Use the helper for queues, hashes, scaffolding, charts, deterministic lint, and exports.
- Use the model for semantic compilation, summaries, cross-links, contradictions, captions, and synthesis.
- Treat `raw/` as append-only. Create new raw records when fetching sources, but never edit or delete existing raw files.
- Update `index.md` and append to `log.md` after every durable wiki change.
- For Codex, this plugin is the discovery layer; `AGENTS.md` is the project instruction layer.
- For OpenClaw, use this `SKILL.md` metadata for required binaries and install hints.

## Execution Guardrails

- Think before writing: surface assumptions and ambiguity before durable wiki changes.
- Simplicity first: make the minimum page/file updates needed; avoid speculative structure.
- Surgical changes: touch only the files required for the task and clean up only the artifacts you created.
- Goal-driven execution: define a verification path up front and use helper commands to prove the vault is still consistent.
