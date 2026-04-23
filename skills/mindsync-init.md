---
name: mindsync-init
description: Initialize a portable LLM Wiki vault with AGENTS.md, Claude compatibility, deterministic state, scripts, qmd, and explicit user-action ingest
trigger: /mindsync init
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd", "@steipete/summarize"]
    optional:
      npm: ["agent-browser"]
---

# /mindsync init

Initialize a project-local mindsync vault. Prefer project-local install and
explicit user-action ingest. Do not install hooks, watchers, cron jobs, or
background activity.

## 1. Collect Inputs

Ask for any missing values:

- Name
- Wiki purpose/domain
- Assistant priority
- Vault path (`./mindsync` by default; use `.` only for the legacy root-vault layout)

Defaults:

- Agent adapters: `claude`, `codex`, `openclaw`
- Mode: `action-first`
- Scope: project-local
- Vault path: `./mindsync`

## 2. Locate Helper

Prefer the project helper:

```bash
HELPER="scripts/mindsync.py"
```

Fallback after global Claude install:

```bash
HELPER="$HOME/.claude/scripts/mindsync/mindsync.py"
```

## 3. Scaffold Vault

Run:

```bash
python3 "$HELPER" init \
  --vault "./mindsync" \
  --name "NAME" \
  --domain "DOMAIN" \
  --priority "PRIORITY" \
  --mode action-first \
  --agent claude \
  --agent codex \
  --agent openclaw
```

This creates:

- a root `AGENTS.md` pointer if one does not already exist
- `mindsync/AGENTS.md` as the canonical agent-neutral instruction file
- `mindsync/CLAUDE.md` as Claude compatibility
- `mindsync/_hot.md`, `mindsync/index.md`, `mindsync/log.md`
- `mindsync/raw/`, `mindsync/raw/assets/`, `mindsync/wiki/`, `mindsync/wiki/analyses/assets/`
- `mindsync/.mindsync/config.json`
- `mindsync/.mindsync/state/pending-ingest.json`
- `mindsync/.mindsync/state/source-hashes.json`
- `mindsync/.mindsync/state/enrichment-queue.json`
- local `mindsync/scripts/`

If root `AGENTS.md` already exists, do not overwrite it. Print the suggested
MindSync pointer snippet and ask the user before changing their root project
instructions.

Legacy root layout remains available when the user explicitly chooses:

```bash
python3 "$HELPER" init --vault . --name "NAME" --domain "DOMAIN" --priority "PRIORITY"
```

## 4. Required Tool Setup

Check:

```bash
python3 mindsync/scripts/mindsync.py tool-path --vault mindsync qmd || true
python3 mindsync/scripts/mindsync.py tool-path --vault mindsync summarize || true
python3 mindsync/scripts/mindsync.py tool-path --vault mindsync agent-browser || true
```

Offer project-local installs:

```bash
python3 mindsync/scripts/mindsync.py ensure-tools --vault mindsync --tool qmd --tool summarize
```

Offer optional browser install only when the user wants autonomous browsing:

```bash
python3 mindsync/scripts/mindsync.py ensure-tools --vault mindsync --tool agent-browser
```

If qmd is installed, run:

```bash
QMD=$(python3 mindsync/scripts/mindsync.py tool-path --vault mindsync qmd)
"$QMD" collection add "mindsync/wiki" --name "WIKI_NAME" || true
"$QMD" context add "qmd://WIKI_NAME" "DOMAIN" || true
python3 mindsync/scripts/mindsync.py embed --vault mindsync
```

## 5. Action-First Ingest

Do not install Claude hooks, Codex hooks, launchd jobs, cron jobs, or file
watchers. Raw files are source records. They are processed only when the user
asks an agent to ingest them.

When the user asks to ingest, run:

```bash
python3 mindsync/scripts/mindsync.py queue-scan --vault mindsync
python3 mindsync/scripts/mindsync.py pending --vault mindsync
```

Then compile pending items into `wiki/`, update `index.md` and `log.md`, mark
sources ingested, and refresh qmd:

```bash
python3 mindsync/scripts/mindsync.py mark-ingested --vault mindsync --path "raw/path.md" --page "wiki/sources/YYYY-MM-DD-slug.md"
python3 mindsync/scripts/mindsync.py embed --vault mindsync
```

## 6. Confirm

Report:

- Vault path
- Agent adapters
- Mode
- qmd status
- Action-first ingest status
- First action: drop a source into `mindsync/raw/` or `mindsync/raw/assets/`, then run `/mindsync ingest`
