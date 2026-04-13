---
name: mindsync-init
description: Initialize a portable LLM Wiki vault with AGENTS.md, Claude compatibility, deterministic state, scripts, qmd, and optional hooks
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
zero-touch automation unless the user explicitly asks otherwise.

## 1. Collect Inputs

Ask for any missing values:

- Name
- Wiki purpose/domain
- Assistant priority
- Vault path

Defaults:

- Agent adapters: `claude`, `codex`, `openclaw`
- Automation: `zero-touch`
- Scope: project-local

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
  --vault "VAULT_PATH" \
  --name "NAME" \
  --domain "DOMAIN" \
  --priority "PRIORITY" \
  --automation zero-touch \
  --agent claude \
  --agent codex \
  --agent openclaw
```

This creates:

- `AGENTS.md` as the canonical agent-neutral instruction file
- `CLAUDE.md` as Claude compatibility
- `_hot.md`, `index.md`, `log.md`
- `raw/`, `raw/assets/`, `wiki/`, `wiki/analyses/assets/`
- `.mindsync/config.json`
- `.mindsync/state/pending-ingest.json`
- `.mindsync/state/source-hashes.json`
- `.mindsync/state/enrichment-queue.json`
- local `scripts/`

## 4. Required Tool Setup

Check:

```bash
python3 scripts/mindsync.py tool-path --vault "VAULT_PATH" qmd || true
python3 scripts/mindsync.py tool-path --vault "VAULT_PATH" summarize || true
python3 scripts/mindsync.py tool-path --vault "VAULT_PATH" agent-browser || true
```

Offer project-local installs:

```bash
python3 scripts/mindsync.py ensure-tools --vault "VAULT_PATH" --tool qmd --tool summarize
```

Offer optional browser install only when the user wants autonomous browsing:

```bash
python3 scripts/mindsync.py ensure-tools --vault "VAULT_PATH" --tool agent-browser
```

If qmd is installed, run:

```bash
cd "VAULT_PATH"
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd)
"$QMD" collection add "VAULT_PATH/wiki" --name "WIKI_NAME" || true
"$QMD" context add "qmd://WIKI_NAME" "DOMAIN" || true
python3 scripts/mindsync.py embed --vault .
```

## 5. Zero-Touch Hooks

Ask before installing hooks if the agent runtime supports them. For Claude Code:

```bash
mkdir -p "VAULT_PATH/.claude"
```

Write or merge `VAULT_PATH/.claude/settings.json` with:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/hook-prompt-submit.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/hook-auto-ingest.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/hook-session-end.sh"
          }
        ]
      }
    ]
  }
}
```

Then schedule file watching:

```bash
bash "VAULT_PATH/scripts/schedule-embed.sh" "VAULT_PATH"
```

For Codex/OpenClaw, keep the deterministic queue active and use `AGENTS.md`;
runtime-specific hook installation can be added by the adapter.

## 6. Confirm

Report:

- Vault path
- Agent adapters
- Automation mode
- qmd status
- Hook/watch status
- First action: drop a source into `raw/` or `raw/assets/`, then run `/mindsync ingest`
