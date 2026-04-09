# mindsync

A Claude Code skill suite for building and maintaining personal knowledge bases using LLMs — based on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy.

Instead of RAG (re-discovering knowledge on every query), you build a **persistent, compounding wiki** — structured markdown files that get richer with every source you add. The LLM writes and maintains all of it. You curate sources and ask questions.

## Skills

| Command | What it does |
|---------|-------------|
| `/mindsync init` | One-time setup: creates vault structure, personalized CLAUDE.md, configures tools |
| `/mindsync ingest` | Interactive ingest of a new source (URL, file, paste, video) |
| `/mindsync lint` | Health-check: finds orphans, contradictions, gaps, stale claims |

## Install

```bash
git clone https://github.com/ekinburak/mindsync.git
cd mindsync
bash install.sh
```

Or one-liner (after repo is public on GitHub):

```bash
curl -s https://raw.githubusercontent.com/ekinburak/mindsync/main/install.sh | bash
```

## Requirements

- [Claude Code](https://claude.ai/code) (CLI)
- Node.js 18+

## Recommended tools (installed automatically by `/mindsync init`)

| Tool | Purpose |
|------|---------|
| [qmd](https://github.com/tobi/qmd) | Semantic search over your wiki |
| [summarize](https://github.com/steipete/summarize) | Convert URLs/PDFs/videos to markdown |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | Claude browses web autonomously (optional) |

## Quickstart

1. Install skills (above)
2. Create a folder for your wiki (e.g. `~/Documents/mywiki`)
3. Open Claude Code in that folder
4. Run `/mindsync init` and follow the prompts
5. Drop a source into `raw/` and run `/mindsync ingest`

## Vault structure (created by init)

```
your-wiki/
├── CLAUDE.md        ← personalized schema, auto-loaded by Claude Code
├── _hot.md          ← active context: goals, open questions, key numbers
├── index.md         ← full content catalog
├── log.md           ← append-only history
├── raw/             ← your source files (immutable)
└── wiki/
    ├── entities/    ← people, habits, projects, goals
    ├── concepts/    ← ideas, frameworks, mental models
    ├── sources/     ← one page per ingested source
    └── analyses/    ← filed query results and syntheses
```

## Multiple wikis

Each vault is self-contained. Run `/mindsync init` in a different folder to create a new wiki (e.g. a research wiki, a project wiki). Each gets its own `CLAUDE.md` tuned to its domain.

## Auto-ingest with file watcher

During `/mindsync init`, you can optionally set up a file watcher. Once running, any file dropped into `raw/` automatically triggers the ingest flow. Requires `fswatch` (`brew install fswatch`).

## License

MIT
