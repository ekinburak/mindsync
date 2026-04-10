#!/bin/bash
# mindsync installer
# Copies skills to ~/.claude/skills/ so they're available in Claude Code

set -e

SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing mindsync skills..."

mkdir -p "$SKILLS_DIR"

cp "$REPO_DIR/skills/mindsync-init.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-ingest.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-lint.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-query.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/mindsync-status.md" "$SKILLS_DIR/"

echo ""
echo "Done. 5 skills installed to $SKILLS_DIR:"
echo "  /mindsync init    — set up a new wiki vault"
echo "  /mindsync ingest  — ingest a new source"
echo "  /mindsync query   — research a question, output as text or Marp slides"
echo "  /mindsync lint    — health-check your wiki"
echo "  /mindsync status  — quick dashboard: counts, last activity, index health"
echo ""
echo "Open Claude Code in your wiki directory and run: /mindsync init"
