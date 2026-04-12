#!/bin/bash
# on-raw-change.sh - Runs when launchd detects changes in raw/
# Does two things:
#   1. Updates .mindsync/state/pending-ingest.json
#   2. Runs qmd embed so new raw/ files are immediately searchable
#
# Called by launchd WatchPaths job — do not run manually.

WIKI_PATH="$1"

if [ -z "$WIKI_PATH" ] || [ ! -d "$WIKI_PATH/raw" ]; then
  exit 0
fi

SCRIPT="$WIKI_PATH/scripts/mindsync.py"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$HOME/.claude/scripts/mindsync/mindsync.py"
fi

if [ -f "$SCRIPT" ]; then
  python3 "$SCRIPT" queue-scan --vault "$WIKI_PATH" >> "$HOME/.mindsync-embed.log" 2>&1 || true
fi

# Also rebuild qmd index so new raw files are searchable immediately
QMD_PATH=""
if [ -x "$WIKI_PATH/.mindsync/tools/node_modules/.bin/qmd" ]; then
  QMD_PATH="$WIKI_PATH/.mindsync/tools/node_modules/.bin/qmd"
elif which qmd &>/dev/null; then
  QMD_PATH="$(which qmd)"
fi

if [ -n "$QMD_PATH" ]; then
  "$QMD_PATH" embed >> "$HOME/.mindsync-embed.log" 2>&1
  if [ -f "$SCRIPT" ]; then
    python3 "$SCRIPT" mark-embed --vault "$WIKI_PATH" >> "$HOME/.mindsync-embed.log" 2>&1 || true
  fi
fi
