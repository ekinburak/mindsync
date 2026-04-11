#!/bin/bash
# on-raw-change.sh — Runs when launchd detects changes in raw/
# Does two things:
#   1. Writes raw/.pending-ingest flag so Claude knows files are waiting
#   2. Runs qmd embed so new raw/ files are immediately searchable
#
# Called by launchd WatchPaths job — do not run manually.

WIKI_PATH="$1"

if [ -z "$WIKI_PATH" ] || [ ! -d "$WIKI_PATH/raw" ]; then
  exit 0
fi

# Write the pending flag — UserPromptSubmit hook checks this
# Only list actual files (not hidden, not assets/)
PENDING=$(find "$WIKI_PATH/raw" -maxdepth 1 -type f -not -name ".*" -newer "$WIKI_PATH/raw/.last-ingest" 2>/dev/null | xargs -I{} basename {} | tr '\n' ' ')

if [ -n "$PENDING" ]; then
  echo "$PENDING" > "$WIKI_PATH/raw/.pending-ingest"
fi

# Also rebuild qmd index so new raw files are searchable immediately
if which qmd &>/dev/null; then
  qmd embed >> "$HOME/.mindsync-embed.log" 2>&1
fi
