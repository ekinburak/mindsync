#!/bin/bash
# schedule-embed.sh - Watch vault for changes, keep qmd fresh, flag pending ingests
# Usage: bash scripts/schedule-embed.sh <wiki-path>
# Example: bash scripts/schedule-embed.sh ~/Documents/mywiki
#
# Installs two launchd jobs (macOS) or one cron job (Linux):
#   1. Watch wiki/  -> run qmd embed when wiki pages change
#   2. Watch raw/   -> update pending queue when sources arrive
#
# The deterministic queue is read by hook-prompt-submit.sh.

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

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WIKI_PATH/.mindsync/state"
LOG="$WIKI_PATH/.mindsync/state/automation.log"
LABEL_SUFFIX=$(python3 -c 'import hashlib,re,sys; p=sys.argv[1]; name=p.rstrip("/").split("/")[-1].lower(); name=re.sub(r"[^a-z0-9]+","-",name).strip("-") or "vault"; print(f"{name}.{hashlib.sha256(p.encode()).hexdigest()[:8]}")' "$WIKI_PATH")

if [ -x "$WIKI_PATH/.mindsync/tools/node_modules/.bin/qmd" ]; then
  QMD_PATH="$WIKI_PATH/.mindsync/tools/node_modules/.bin/qmd"
elif which qmd &>/dev/null; then
  QMD_PATH="$(which qmd)"
else
  echo "Error: qmd is not installed. Run: python3 $SCRIPT_DIR/mindsync.py ensure-tools --vault '$WIKI_PATH' --tool qmd"
  exit 1
fi

MARK_EMBED="<array><string>/usr/bin/env</string><string>python3</string><string>$SCRIPT_DIR/mindsync.py</string><string>embed</string><string>--vault</string><string>$WIKI_PATH</string></array>"

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

  echo "Installing launchd watchers for $WIKI_PATH..."
  echo ""

  # Job 1: wiki/ changes -> qmd embed only
  install_plist \
    "com.mindsync.wiki.$LABEL_SUFFIX" \
    "$WIKI_PATH/wiki" \
    "$MARK_EMBED"

  echo ""

  # Job 2: raw/ changes -> queue pending ingest only
  install_plist \
    "com.mindsync.raw.$LABEL_SUFFIX" \
    "$WIKI_PATH/raw" \
    "<array><string>$SCRIPT_DIR/on-raw-change.sh</string><string>$WIKI_PATH</string></array>"

  echo ""
  echo "Debounce:  30s after last file change"
  echo "Log:       $LOG"
  echo ""
  echo "To remove:"
  echo "  launchctl unload ~/Library/LaunchAgents/com.mindsync.wiki.$LABEL_SUFFIX.plist"
  echo "  launchctl unload ~/Library/LaunchAgents/com.mindsync.raw.$LABEL_SUFFIX.plist"

# ── Linux: cron fallback ──────────────────────────────────────────────────────
else
  CRON_JOB="0 2 * * * /usr/bin/env python3 $SCRIPT_DIR/mindsync.py embed --vault '$WIKI_PATH' >> $LOG 2>&1"

  if crontab -l 2>/dev/null | grep -q "mindsync.py embed --vault"; then
    echo "mindsync embed is already scheduled in crontab."
    crontab -l | grep "mindsync.py embed --vault"
  else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Scheduled: mindsync embed nightly at 2am (Linux — launchd not available)"
    echo "Log: $LOG"
    echo ""
    echo "To remove: crontab -e and delete the mindsync embed line"
  fi
fi
