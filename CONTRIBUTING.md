# Contributing to mindsync

## Adding or improving skills

Skills are markdown files in `skills/`. Each skill must be:
- **Self-contained** — no external file reads required to execute
- **Domain-agnostic** — works for personal, research, or project wikis
- **Tested manually** — run the skill in a fresh agent session before PRing
- **Portable** — avoid Claude-only assumptions unless the skill is explicitly documenting a Claude adapter

Codex packaging lives in `plugins/mindsync/`. OpenClaw compatibility metadata
belongs in `SKILL.md` frontmatter.

## Deterministic scripts

Mechanical behavior belongs in `scripts/mindsync.py` where possible:

- vault scaffold
- pending queues
- source hashes
- deterministic lint
- chart rendering
- training export
- state/checkpoint files

Keep LLM instructions focused on semantic work.

## Adding docs

Docs live in `docs/`. Keep them short and practical. One tool per file.

## Improving templates

Templates live in `templates/`. All placeholders use `{{PLACEHOLDER}}` syntax.
`AGENTS.md.template` is canonical; `CLAUDE.md.template` is a compatibility file.

## Pull requests

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Open a PR with a clear description of what changed and why
