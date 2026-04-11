#!/bin/bash
# schedule-embed.sh — Watch vault for changes, keep qmd fresh, flag pending ingests
# Usage: bash scripts/schedule-embed.sh <wiki-path>
# Example: bash scripts/schedule-embed.sh ~/Documents/mywiki
#
# Installs two launchd jobs (macOS) or one cron job (Linux):
#   1. Watch wiki/  → run qmd embed when wiki pages change
#   2. Watch raw/   → write .pending-ingest flag + run qmd embed when sources arrive
#
# The .pending-ingest flag is read by hook-prompt-submit.sh (UserPromptSubmit hook)
# which triggers Claude to ingest the files. This avoids running `find` on every
# user message — the hook only does a single file-existence check.

set -e

WIKI_PATH="${1:-}"

if [ -z "$WIKI_PATH" ]; then
  echo "Usage: bash scripts/schedule-embed.sh <path-to-wiki>"
  echo "Example: bash scripts/schedule-embed.sh ~/Documents/mywiki"
  exit 1
fi

WIKI_PATH="${WIKI_PATH/#\~/$HOME}"

if [ ! -d "$WIKI_PATH/wiki" ]; then
  echo "Error: $WIKI_PATH/wiki does not exist. Is this a mindsync vault?"
  exit 1
fi

if ! which qmd &>/dev/null; then
  echo "Error: qmd is not installed. Run: npm install -g @tobilu/qmd"
  exit 1
fi

QMD_PATH="$(which qmd)"
SCRIPT_DIR="$HOME/.claude/scripts/mindsync"
LOG="$HOME/.mindsync-embed.log"
VAULT_NAME="$(basename "$WIKI_PATH")"

# ── macOS: two launchd jobs ───────────────────────────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then

  install_plist() {
    local label="$1"
    local watch_path="$2"
    local plist="$HOME/Library/LaunchAgents/$label.plist"
    local program_args="$3"

    if launchctl list "$label" &>/dev/null; then
      launchctl unload "$plist" 2>/dev/null || true
    fi

    cat > "$plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  $program_args
  <key>WatchPaths</key>
  <array>
    <string>$watch_path</string>
  </array>
  <key>ThrottleInterval</key>
  <integer>30</integer>
  <key>StandardOutPath</key>
  <string>$LOG</string>
  <key>StandardErrorPath</key>
  <string>$LOG</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF
    launchctl load "$plist"
    echo "  Installed: $label"
    echo "  Watches:   $watch_path"
  }

  echo "Installing launchd watchers for $VAULT_NAME..."
  echo ""

  # Job 1: wiki/ changes → qmd embed only
  install_plist \
    "com.mindsync.wiki.$VAULT_NAME" \
    "$WIKI_PATH/wiki" \
    "<array><string>$QMD_PATH</string><string>embed</string></array>"

  echo ""

  # Job 2: raw/ changes → flag .pending-ingest + qmd embed
  install_plist \
    "com.mindsync.raw.$VAULT_NAME" \
    "$WIKI_PATH/raw" \
    "<array><string>$SCRIPT_DIR/on-raw-change.sh</string><string>$WIKI_PATH</string></array>"

  echo ""
  echo "Debounce:  30s after last file change"
  echo "Log:       $LOG"
  echo ""
  echo "To remove:"
  echo "  launchctl unload ~/Library/LaunchAgents/com.mindsync.wiki.$VAULT_NAME.plist"
  echo "  launchctl unload ~/Library/LaunchAgents/com.mindsync.raw.$VAULT_NAME.plist"

# ── Linux: cron fallback ──────────────────────────────────────────────────────
else
  CRON_JOB="0 2 * * * $QMD_PATH embed >> $LOG 2>&1"

  if crontab -l 2>/dev/null | grep -q "qmd embed"; then
    echo "qmd embed is already scheduled in crontab."
    crontab -l | grep "qmd embed"
  else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Scheduled: qmd embed nightly at 2am (Linux — launchd not available)"
    echo "Log: $LOG"
    echo ""
    echo "To remove: crontab -e and delete the qmd embed line"
  fi
fi
