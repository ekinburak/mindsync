#!/bin/bash
# hook-prompt-submit.sh — Claude Code UserPromptSubmit hook for mindsync
# Fires before every user message in the vault session.
# If new files exist in raw/ that haven't been ingested yet, injects an ingest request.
#
# Registered in VAULT_PATH/.claude/settings.json under hooks.UserPromptSubmit
# Do not edit manually — managed by /mindsync init

RAW_DIR="$(pwd)/raw"
MARKER="$RAW_DIR/.last-ingest"

# Only act if this looks like a mindsync vault with a raw/ directory
if [ ! -d "$RAW_DIR" ]; then
  exit 0
fi

# On first ever use (no marker yet), create it and exit — don't flood with existing files
if [ ! -f "$MARKER" ]; then
  touch "$MARKER"
  exit 0
fi

# Find files in raw/ that are newer than the last ingest marker
# Skip hidden files and the assets/ subdirectory
PENDING=()
while IFS= read -r -d '' file; do
  PENDING+=("$(basename "$file")")
done < <(find "$RAW_DIR" -maxdepth 1 -type f -not -name ".*" -newer "$MARKER" -print0 2>/dev/null)

# Nothing new — silent exit
if [ ${#PENDING[@]} -eq 0 ]; then
  exit 0
fi

# Inject ingest request into the conversation
COUNT=${#PENDING[@]}
FILES=$(printf '"%s" ' "${PENDING[@]}")

echo "New file(s) detected in raw/ that haven't been ingested yet ($COUNT file(s)): $FILES"
echo "Please run /mindsync ingest to process them before responding to the user's message."
