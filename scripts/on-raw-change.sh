#!/bin/bash
# on-raw-change.sh - Runs when launchd detects changes in raw/
# Updates .mindsync/state/pending-ingest.json.
#
# Called by launchd WatchPaths job — do not run manually.

WIKI_PATH="$1"

if [ -z "$WIKI_PATH" ] || [ ! -d "$WIKI_PATH/raw" ]; then
  exit 0
fi

mkdir -p "$WIKI_PATH/.mindsync/state"
LOG="$WIKI_PATH/.mindsync/state/automation.log"
MIN_AGE_SECONDS="${MIN_AGE_SECONDS:-10}"

SCRIPT="$WIKI_PATH/scripts/mindsync.py"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$HOME/.claude/scripts/mindsync/mindsync.py"
fi

if [ -f "$SCRIPT" ]; then
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") INFO vault=$WIKI_PATH raw watcher queue-scan start" >> "$LOG"
  sleep "$MIN_AGE_SECONDS"
  python3 "$SCRIPT" queue-scan --vault "$WIKI_PATH" --min-age-seconds "$MIN_AGE_SECONDS" >> "$LOG" 2>&1 || {
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") ERROR vault=$WIKI_PATH raw watcher queue-scan failed" >> "$LOG"
    exit 0
  }
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") INFO vault=$WIKI_PATH raw watcher queue-scan complete" >> "$LOG"
fi
