#!/bin/bash
# mindsync installer

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SCOPE="project"
AGENT="all"
TARGET="$PWD"

usage() {
  cat << USAGE
Usage: bash install.sh [--scope project|global] [--agent claude|codex|openclaw|all] [--target PATH]

Defaults:
  --scope project
  --agent all
  --target current directory
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --scope)
      SCOPE="${2:-}"
      shift 2
      ;;
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

TARGET="${TARGET/#\~/$HOME}"

want_agent() {
  [ "$AGENT" = "all" ] || [ "$AGENT" = "$1" ]
}

copy_scripts() {
  local dest="$1"
  mkdir -p "$dest"
  find "$REPO_DIR/scripts" -maxdepth 1 -type f -exec cp {} "$dest/" \;
  chmod +x "$dest"/*.sh "$dest"/mindsync.py 2>/dev/null || true
}

copy_templates() {
  local root="$1"
  mkdir -p "$root/templates"
  find "$REPO_DIR/templates" -maxdepth 1 -type f -exec cp {} "$root/templates/" \;
}

install_claude_project() {
  mkdir -p "$TARGET/.claude/skills"
  cp "$REPO_DIR"/skills/*.md "$TARGET/.claude/skills/"
  copy_scripts "$TARGET/scripts"
  copy_templates "$TARGET"
}

install_claude_global() {
  mkdir -p "$HOME/.claude/skills"
  cp "$REPO_DIR"/skills/*.md "$HOME/.claude/skills/"
  copy_scripts "$HOME/.claude/scripts/mindsync"
  copy_templates "$HOME/.claude/scripts/mindsync"
}

install_codex_project() {
  mkdir -p "$TARGET/plugins" "$TARGET/.agents/plugins"
  rm -rf "$TARGET/plugins/mindsync"
  cp -R "$REPO_DIR/plugins/mindsync" "$TARGET/plugins/mindsync"
  cp "$REPO_DIR/.agents/plugins/marketplace.json" "$TARGET/.agents/plugins/marketplace.json"
  copy_scripts "$TARGET/scripts"
  copy_templates "$TARGET"
}

install_codex_global() {
  mkdir -p "$HOME/plugins" "$HOME/.agents/plugins"
  rm -rf "$HOME/plugins/mindsync"
  cp -R "$REPO_DIR/plugins/mindsync" "$HOME/plugins/mindsync"
  cp "$REPO_DIR/.agents/plugins/marketplace.json" "$HOME/.agents/plugins/marketplace.json"
  copy_scripts "$HOME/plugins/mindsync/scripts"
  copy_templates "$HOME/plugins/mindsync"
}

install_openclaw_project() {
  mkdir -p "$TARGET/.openclaw/skills"
  cp "$REPO_DIR"/skills/*.md "$TARGET/.openclaw/skills/"
  copy_scripts "$TARGET/scripts"
  copy_templates "$TARGET"
}

install_openclaw_global() {
  mkdir -p "$HOME/.openclaw/skills"
  cp "$REPO_DIR"/skills/*.md "$HOME/.openclaw/skills/"
  copy_scripts "$HOME/.openclaw/scripts/mindsync"
  copy_templates "$HOME/.openclaw/scripts/mindsync"
}

case "$SCOPE" in
  project|global) ;;
  *)
    echo "--scope must be project or global" >&2
    exit 1
    ;;
esac

case "$AGENT" in
  claude|codex|openclaw|all) ;;
  *)
    echo "--agent must be claude, codex, openclaw, or all" >&2
    exit 1
    ;;
esac

echo "Installing mindsync ($SCOPE, $AGENT)..."

if [ "$SCOPE" = "project" ]; then
  mkdir -p "$TARGET"
  want_agent claude && install_claude_project
  want_agent codex && install_codex_project
  want_agent openclaw && install_openclaw_project
else
  want_agent claude && install_claude_global
  want_agent codex && install_codex_global
  want_agent openclaw && install_openclaw_global
fi

echo ""
echo "Installed mindsync."
echo "Target: $TARGET"
echo "Next:"
echo "  python3 scripts/mindsync.py init --vault <vault-path> --name <name> --domain <domain> --priority <priority>"
