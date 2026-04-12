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

# Only rebuild if wiki files were modified in the last hour (session likely touched them)
RECENTLY_MODIFIED=$(find "$WIKI_DIR" -name "*.md" -newer "$(pwd)/log.md" 2>/dev/null | head -1)

if [ -z "$RECENTLY_MODIFIED" ]; then
  exit 0
fi

# Rebuild qmd index silently. Prefer the vault-local dependency.
QMD_PATH=""
if [ -x "$(pwd)/.mindsync/tools/node_modules/.bin/qmd" ]; then
  QMD_PATH="$(pwd)/.mindsync/tools/node_modules/.bin/qmd"
elif which qmd &>/dev/null; then
  QMD_PATH="$(which qmd)"
fi

if [ -n "$QMD_PATH" ]; then
  (
    "$QMD_PATH" embed >> "$HOME/.mindsync-embed.log" 2>&1
    SCRIPT="scripts/mindsync.py"
    if [ ! -f "$SCRIPT" ]; then
      SCRIPT="$HOME/.claude/scripts/mindsync/mindsync.py"
    fi
    if [ -f "$SCRIPT" ]; then
      python3 "$SCRIPT" mark-embed --vault "$(pwd)" >> "$HOME/.mindsync-embed.log" 2>&1 || true
    fi
  ) &
fi
