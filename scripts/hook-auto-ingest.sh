#!/bin/bash
# hook-auto-ingest.sh — Claude Code PostToolUse hook for mindsync
# Fires after every Write tool call. If the file landed in raw/, triggers ingest.
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

# Only act on Write calls to raw/ (skip raw/assets/ and dotfiles)
if [[ "$TOOL_NAME" != "Write" ]]; then
  exit 0
fi

if [[ "$FILE_PATH" != */raw/* ]] || [[ "$FILE_PATH" == */raw/assets/* ]]; then
  exit 0
fi

FILENAME=$(basename "$FILE_PATH")

# Skip hidden files
if [[ "$FILENAME" == .* ]]; then
  exit 0
fi

# Output a message Claude will see and act on
echo "New file detected in raw/: $FILENAME"
echo "Please run /mindsync ingest to process this file into the wiki."
