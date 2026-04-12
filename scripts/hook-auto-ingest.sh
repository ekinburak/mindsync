#!/bin/bash
# hook-auto-ingest.sh - Claude Code PostToolUse hook for mindsync
# Fires after every Write tool call. If the file landed in raw/, queues ingest.
#
# Registered in VAULT_PATH/.claude/settings.json under hooks.PostToolUse
# Do not edit manually — managed by /mindsync init

set -e

INPUT=$(cat)

# Extract tool name and file path from the PostToolUse JSON payload
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_name', ''))
" 2>/dev/null)

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)

# Only act on Write calls to raw/ (skip dotfiles)
if [[ "$TOOL_NAME" != "Write" ]]; then
  exit 0
fi

if [[ "$FILE_PATH" != */raw/* ]]; then
  exit 0
fi

FILENAME=$(basename "$FILE_PATH")

# Skip hidden files
if [[ "$FILENAME" == .* ]]; then
  exit 0
fi

SCRIPT="scripts/mindsync.py"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$HOME/.claude/scripts/mindsync/mindsync.py"
fi

if [ -f "$SCRIPT" ]; then
  python3 "$SCRIPT" queue-scan --vault "$(pwd)" >/dev/null 2>&1 || true
fi

echo "New raw source queued: $FILENAME"
echo "Zero-touch mode: process pending mindsync sources now. Run python3 scripts/mindsync.py pending --vault . and compile each pending item into wiki/, then mark it ingested."
