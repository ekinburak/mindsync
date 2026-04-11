#!/bin/bash
# mindsync installer
# Copies skills and scripts to ~/.claude/ so they're available in Claude Code

set -e

SKILLS_DIR="$HOME/.claude/skills"
SCRIPTS_DIR="$HOME/.claude/scripts/mindsync"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing mindsync skills..."

mkdir -p "$SKILLS_DIR"
mkdir -p "$SCRIPTS_DIR"

# Skills
cp "$REPO_DIR/skills/mindsync-init.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-ingest.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-lint.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-query.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-status.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-search.md" "$SKILLS_DIR/"

# Scripts (referenced by skills at runtime)
cp "$REPO_DIR/scripts/hook-auto-ingest.sh" "$SCRIPTS_DIR/"
cp "$REPO_DIR/scripts/hook-session-end.sh" "$SCRIPTS_DIR/"
cp "$REPO_DIR/scripts/hook-prompt-submit.sh" "$SCRIPTS_DIR/"
cp "$REPO_DIR/scripts/schedule-embed.sh" "$SCRIPTS_DIR/"
cp "$REPO_DIR/scripts/generate-graph.sh" "$SCRIPTS_DIR/"
chmod +x "$SCRIPTS_DIR/"*.sh

echo ""
echo "Done. 6 skills installed to $SKILLS_DIR:"
echo "  /mindsync init    — set up a new wiki vault"
echo "  /mindsync ingest  — ingest a new source"
echo "  /mindsync search  — semantic search across the wiki"
echo "  /mindsync query   — research a question, output as text or Marp slides"
echo "  /mindsync lint    — health-check your wiki"
echo "  /mindsync status  — quick dashboard: counts, last activity, index health"
echo ""
echo "Scripts installed to $SCRIPTS_DIR"
echo ""
echo "Open Claude Code in any folder and run: /mindsync init"
