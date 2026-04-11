#!/bin/bash
# schedule-embed.sh — Keep qmd index fresh whenever wiki files change
# Usage: bash scripts/schedule-embed.sh <wiki-path>
# Example: bash scripts/schedule-embed.sh ~/Documents/mywiki
#
# On macOS: installs a launchd job that watches wiki/ and raw/ for changes,
#           running qmd embed within seconds of any file modification.
# On Linux: falls back to a nightly cron job at 2am.

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

if ! which qmd &>/dev/null; then
  echo "Error: qmd is not installed. Run: npm install -g @tobilu/qmd"
  exit 1
fi

QMD_PATH="$(which qmd)"
LOG="$HOME/.mindsync-embed.log"
LABEL="com.mindsync.embed.$(basename "$WIKI_PATH")"

# ── macOS: launchd with WatchPaths ────────────────────────────��───────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

  # Remove existing job if present
  if launchctl list "$LABEL" &>/dev/null; then
    launchctl unload "$PLIST" 2>/dev/null || true
  fi

  cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>$QMD_PATH</string>
    <string>embed</string>
  </array>

  <!-- Fire when wiki/ or raw/ files change — not on a fixed schedule -->
  <key>WatchPaths</key>
  <array>
    <string>$WIKI_PATH/wiki</string>
    <string>$WIKI_PATH/raw</string>
  </array>

  <!-- Debounce: wait 30s after last change before running -->
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

  launchctl load "$PLIST"
  echo "Installed: launchd job '$LABEL'"
  echo "Trigger:   any change to $WIKI_PATH/wiki/ or $WIKI_PATH/raw/"
  echo "Debounce:  runs 30 seconds after the last file change"
  echo "Log:       $LOG"
  echo ""
  echo "To remove: launchctl unload $PLIST && rm $PLIST"

# ── Linux: fallback to cron ───────────────────────────────────────────────────
else
  CRON_JOB="0 2 * * * $QMD_PATH embed >> $LOG 2>&1"

  if crontab -l 2>/dev/null | grep -q "qmd embed"; then
    echo "qmd embed is already scheduled in crontab."
    crontab -l | grep "qmd embed"
  else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Scheduled: qmd embed runs nightly at 2am (cron fallback — launchd not available on Linux)"
    echo "Log: $LOG"
    echo ""
    echo "To remove: crontab -e and delete the qmd embed line"
  fi
fi
