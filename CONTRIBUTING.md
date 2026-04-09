# Contributing to mindsync

## Adding or improving skills

Skills are markdown files in `skills/`. Each skill must be:
- **Self-contained** — no external file reads required to execute
- **Domain-agnostic** — works for personal, research, or project wikis
- **Tested manually** — run the skill in a fresh Claude Code session before PRing

## Adding docs

Docs live in `docs/`. Keep them short and practical. One tool per file.

## Improving templates

Templates live in `templates/`. All placeholders use `{{PLACEHOLDER}}` syntax.

## Pull requests

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Open a PR with a clear description of what changed and why
