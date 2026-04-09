#!/bin/bash
# llm-wiki installer
# Copies skills to ~/.claude/skills/ so they're available in Claude Code

set -e

SKILLS_DIR="$HOME/.claude/skills"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing llm-wiki skills..."

mkdir -p "$SKILLS_DIR"

cp "$REPO_DIR/skills/llm-wiki-init.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/llm-wiki-ingest.md" "$SKILLS_DIR/"
cp "$REPO_DIR/skills/llm-wiki-lint.md" "$SKILLS_DIR/"

echo ""
echo "Done. 3 skills installed to $SKILLS_DIR:"
echo "  /llm-wiki init    — set up a new wiki vault"
echo "  /llm-wiki ingest  — ingest a new source"
echo "  /llm-wiki lint    — health-check your wiki"
echo ""
echo "Open Claude Code in your wiki directory and run: /llm-wiki init"
