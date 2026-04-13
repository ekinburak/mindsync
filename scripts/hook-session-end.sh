#!/bin/bash
# hook-session-end.sh - Claude Code Stop hook for mindsync
# Fires when a Claude Code session ends in the vault directory.
# Keeps the qmd search index fresh after every session that touched the wiki.
#
# Registered in VAULT_PATH/.claude/settings.json under hooks.Stop
# Do not edit manually — managed by /mindsync init

set -e

WIKI_DIR="$(pwd)/wiki"

# Only act if this looks like a mindsync vault
if [ ! -d "$WIKI_DIR" ]; then
  exit 0
fi

SCRIPT="scripts/mindsync.py"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$HOME/.claude/scripts/mindsync/mindsync.py"
fi

if [ ! -f "$SCRIPT" ]; then
  exit 0
fi

mkdir -p "$(pwd)/.mindsync/state"

NEEDS_EMBED=$(python3 - "$(pwd)" <<'PY'
import json
import os
import sys
from pathlib import Path

vault = Path(sys.argv[1])
wiki = vault / "wiki"
state = vault / ".mindsync" / "state" / "last-embed.json"
try:
    last = json.loads(state.read_text()).get("mtime", 0)
except Exception:
    last = 0
newest = 0
for root, _dirs, files in os.walk(wiki):
    for name in files:
        if name.endswith(".md"):
            newest = max(newest, (Path(root) / name).stat().st_mtime)
print("yes" if newest and newest > last else "no")
PY
)

if [ "$NEEDS_EMBED" = "yes" ]; then
  (
    python3 "$SCRIPT" embed --vault "$(pwd)" >> "$(pwd)/.mindsync/state/automation.log" 2>&1 || true
  ) &
fi
