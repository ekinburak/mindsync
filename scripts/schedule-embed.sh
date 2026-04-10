#!/bin/bash
# schedule-embed.sh — Set up nightly cron job to keep qmd index fresh
# Usage: bash scripts/schedule-embed.sh <wiki-path>
# Example: bash scripts/schedule-embed.sh ~/Documents/mywiki

set -e

WIKI_PATH="${1:-}"

if [ -z "$WIKI_PATH" ]; then
  echo "Usage: bash scripts/schedule-embed.sh <path-to-wiki>"
  echo "Example: bash scripts/schedule-embed.sh ~/Documents/mywiki"
  exit 1
fi

# Expand ~ to full path
WIKI_PATH="${WIKI_PATH/#\~/$HOME}"

if [ ! -d "$WIKI_PATH/wiki" ]; then
  echo "Error: $WIKI_PATH/wiki does not exist. Is this a mindsync vault?"
  exit 1
fi

# Check qmd is installed
if ! which qmd &>/dev/null; then
  echo "Error: qmd is not installed. Run: npm install -g @tobilu/qmd"
  exit 1
fi

# Add cron job: run qmd embed at 2am every night
CRON_JOB="0 2 * * * $(which qmd) embed >> $HOME/.mindsync-embed.log 2>&1"

# Check if already scheduled
if crontab -l 2>/dev/null | grep -q "qmd embed"; then
  echo "qmd embed is already scheduled in crontab."
  crontab -l | grep "qmd embed"
else
  # Add to crontab
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo "Scheduled: qmd embed runs nightly at 2am"
  echo "Log: $HOME/.mindsync-embed.log"
  echo ""
  echo "To remove: crontab -e and delete the qmd embed line"
fi
