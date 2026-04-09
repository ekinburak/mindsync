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

## Roadmap / TODO

### 🔴 High priority

**Level 3 auto-ingest via Claude Code hooks** *(most important)*
The current file watcher (`watch-raw.sh`) detects new files in `raw/` and prints a message — but you still have to manually run `/mindsync ingest`. The real goal is **zero-touch ingestion**: Claude Code supports hooks (shell commands that fire on events). A `PostToolUse` hook watching for file writes to `raw/` could automatically trigger the full ingest flow — discuss, write wiki pages, update index and log — without you saying anything. You drop a file, the wiki updates itself.

**`/mindsync query` skill**
A dedicated query skill that enforces the retrieval order (`_hot.md` → `index.md` → pages → `qmd`), always offers to file valuable answers as analyses, and enforces the 5-page read limit. Currently queries rely on CLAUDE.md rules alone.

**Scheduled `qmd embed`**
After bulk ingestion the vector index goes stale. A cron job (or Claude Code scheduled trigger) should run `qmd embed` nightly to keep semantic search accurate.

### 🟡 Medium priority

**`/mindsync status` skill**
Quick dashboard: how many sources, entities, concepts, analyses; last ingest date; `_hot.md` token count; whether qmd index is fresh. Useful at the start of every session.

**Output auto-filing**
When `summarize` or `agent-browser` produces output during a session, automatically route it to `raw/` and queue it for ingest — without copy-paste. Requires hooking into tool output events.

**`/mindsync sync` for team wikis**
Multi-user support: merge wiki updates from multiple contributors, detect conflicts between pages edited by different people, use git branches per contributor.

**Domain-specific ingest templates**
The current ingest skill uses a generic template. Custom templates per source type: journal entries get a different structure than research papers, which differ from podcast transcripts.

### 🟢 Nice to have

**Graph view export**
Generate a `graph.json` from wiki cross-references that tools like Obsidian, D3.js, or Gephi can visualize. Makes the "shape" of your knowledge visible.

**`/mindsync export`**
Export wiki as: Marp slide deck, PDF report, structured JSON, or Anki flashcards. Useful for sharing knowledge or studying from it.

**Contradiction resolution workflow**
When lint flags a contradiction between two pages, a guided workflow to resolve it: show both claims, ask which is correct, update both pages, log the resolution.

**Search CLI integration**
`/mindsync search <query>` — shell alias that calls `qmd query` and formats results as clickable Obsidian links. Skip opening Claude entirely for quick lookups.

---

## License

MIT
