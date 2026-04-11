#!/bin/bash
# hook-prompt-submit.sh — Claude Code UserPromptSubmit hook for mindsync
# Fires before every user message in the vault session.
# Checks for a .pending-ingest flag written by the launchd raw/ watcher.
# If the flag exists, injects an ingest request into the conversation.
#
# This hook does a single file-existence check — no find, no scanning.
# The detection work is done by the OS-level launchd watcher (on-raw-change.sh).
#
# Registered in VAULT_PATH/.claude/settings.json under hooks.UserPromptSubmit

PENDING_FLAG="$(pwd)/raw/.pending-ingest"

# Nothing pending — silent exit (microseconds)
if [ ! -f "$PENDING_FLAG" ]; then
  exit 0
fi

# Read the pending filenames from the flag
FILES=$(cat "$PENDING_FLAG")
COUNT=$(echo "$FILES" | wc -w | tr -d ' ')

echo "New file(s) detected in raw/ ($COUNT pending): $FILES"
echo "Please run /mindsync ingest to process them before responding to the user's message."
