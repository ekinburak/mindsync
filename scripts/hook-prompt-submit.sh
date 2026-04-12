#!/bin/bash
# hook-prompt-submit.sh - Claude Code UserPromptSubmit hook for mindsync
# Fires before every user message in the vault session.
# Scans/reads the deterministic pending ingest queue.
#
# Registered in VAULT_PATH/.claude/settings.json under hooks.UserPromptSubmit

SCRIPT="scripts/mindsync.py"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$HOME/.claude/scripts/mindsync/mindsync.py"
fi

if [ ! -f "$SCRIPT" ]; then
  exit 0
fi

python3 "$SCRIPT" queue-scan --vault "$(pwd)" >/dev/null 2>&1 || true
PENDING_JSON=$(python3 "$SCRIPT" pending --vault "$(pwd)" --json 2>/dev/null || echo '{"items":[]}')
COUNT=$(printf "%s" "$PENDING_JSON" | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("items", [])))' 2>/dev/null || echo 0)

if [ "$COUNT" = "0" ]; then
  exit 0
fi

FILES=$(printf "%s" "$PENDING_JSON" | python3 -c 'import json,sys; print(" ".join(i["path"] for i in json.load(sys.stdin).get("items", [])))' 2>/dev/null)

echo "mindsync has $COUNT pending raw source(s): $FILES"
echo "Zero-touch mode: process these before responding. Compile source/image items into wiki/, update index.md and log.md, then run python3 scripts/mindsync.py mark-ingested --vault . --path <raw-path> --page <wiki-page> for each item."
