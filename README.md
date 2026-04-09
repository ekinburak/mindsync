# mindsync

A Claude Code skill suite for building and maintaining personal knowledge bases using LLMs — based on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy.

Instead of RAG (re-discovering knowledge on every query), you build a **persistent, compounding wiki** — structured markdown files that get richer with every source you add. The LLM writes and maintains all of it. You curate sources and ask questions.

## Skills

| Command | What it does |
|---------|-------------|
| `/mindsync init` | One-time setup: creates vault structure, personalized CLAUDE.md, installs tools |
| `/mindsync ingest` | Interactive ingest of a new source (URL, file, paste, video, PDF) |
| `/mindsync lint` | Health-check: finds orphans, contradictions, gaps, stale claims |

## Install

```bash
git clone https://github.com/ekinburak/mindsync.git
cd mindsync
bash install.sh
```

Or one-liner (requires repo to be public):

```bash
curl -s https://raw.githubusercontent.com/ekinburak/mindsync/main/install.sh | bash
```

## Requirements

- [Claude Code](https://claude.ai/code) (CLI)
- Node.js 18+

## Quickstart

1. Install skills (above)
2. Open Claude Code in any empty folder
3. Run `/mindsync init` and answer 4 questions:
   - Your name
   - What this wiki is for
   - The assistant's #1 priority
   - Where to create the vault (any path — created automatically)
4. Drop a source into `raw/` and run `/mindsync ingest`

## Vault structure (created by init)

```
your-wiki/
├── CLAUDE.md        ← personalized schema, auto-loaded by Claude Code
├── _hot.md          ← active context: goals, open questions, key numbers (~500 tokens)
├── index.md         ← full content catalog (LLM reads before every query)
├── log.md           ← append-only history of every ingest, query, and lint
├── raw/             ← your source files — immutable, LLM never edits these
│   └── assets/      ← downloaded images and attachments
└── wiki/
    ├── entities/    ← people, habits, projects, goals, places
    ├── concepts/    ← ideas, frameworks, themes, mental models
    ├── sources/     ← one summary page per ingested source
    └── analyses/    ← filed query results, comparisons, syntheses
```

## How the tools work together

mindsync integrates three external tools that are automatically detected and installed during `/mindsync init`. Here's what each one does and where it fits in your workflow:

### qmd — Wiki search engine
**GitHub:** [tobi/qmd](https://github.com/tobi/qmd)

qmd is a local semantic search engine for markdown files. It runs entirely on your device — no data leaves your machine. mindsync uses it as the last-resort retrieval step when the index file isn't enough to answer a query.

**How it's used:**
- During `init`: your `wiki/` folder is registered as a qmd collection and embeddings are built
- During queries: if `_hot.md` and `index.md` don't resolve the question, Claude runs `qmd query "<question>"` to search across all wiki pages semantically
- After bulk ingestion: run `qmd embed` to rebuild the index

```bash
qmd query "sleep habits"       # hybrid search (recommended)
qmd search "atomic habits"     # keyword only, fast
qmd vsearch "decision making"  # vector/semantic only
```

You can also configure qmd as an MCP server so Claude calls it as a native tool rather than a shell command — `/mindsync init` shows you the config snippet.

---

### summarize — Source converter
**GitHub:** [steipete/summarize](https://github.com/steipete/summarize)

summarize converts web articles, YouTube videos, podcasts, and PDFs into clean markdown — ready to drop directly into your wiki's `raw/` folder for ingestion. It's the fastest way to get external content into mindsync without copy-pasting.

**How it's used:**
- During `/mindsync ingest`: if you provide a URL or PDF path, Claude runs summarize automatically and saves the output to `raw/` before processing it
- You can also pipe it manually:

```bash
# Article
summarize https://example.com/article > raw/2026-04-09-article-title.md

# YouTube video
summarize https://youtube.com/watch?v=xxx > raw/2026-04-09-video-title.md

# PDF
summarize /path/to/paper.pdf > raw/2026-04-09-paper.md

# Auto-date filename
summarize https://example.com/article > raw/$(date +%Y-%m-%d)-article.md
```

After the file lands in `raw/`, run `/mindsync ingest` — or let the file watcher handle it automatically.

---

### agent-browser — Autonomous web browsing
**GitHub:** [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)

agent-browser is a Rust-based CLI that lets Claude control a browser autonomously — navigate pages, extract content, take screenshots, fill forms — without you copy-pasting anything. It's optional and most useful for power users who want Claude to actively fetch and browse sources during sessions.

**How it's used:**
- Configured as an MCP server so Claude can call it as a native tool
- During queries: Claude can browse a URL you mention and extract content for ingestion
- During research: Claude can search the web for sources related to your question
- During ingest: Claude can fetch a live page, screenshot it, and extract structured content

```bash
# Install
npm install -g agent-browser
agent-browser install   # downloads Chrome for Testing

# MCP config (shown during /mindsync init)
{
  "mcpServers": {
    "agent-browser": {
      "command": "agent-browser",
      "args": ["mcp"]
    }
  }
}
```

If you don't install agent-browser, `summarize` covers most ingest use cases with less setup.

---

## Multiple wikis

Each vault is fully self-contained. Run `/mindsync init` in any folder to create a new wiki for a different domain — a research project, a team knowledge base, a book companion. Each gets its own `CLAUDE.md` tuned to its purpose, its own qmd collection, and its own retrieval configuration.

## Auto-ingest with file watcher

During `/mindsync init`, you can optionally set up a file watcher (`scripts/watch-raw.sh`). Once running, any file dropped into `raw/` automatically triggers the ingest flow. Requires `fswatch`:

```bash
brew install fswatch
bash your-wiki/scripts/watch-raw.sh
```

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
Custom templates per source type: journal entries get a different structure than research papers, which differ from podcast transcripts.

### 🟢 Nice to have

**Graph view export**
Generate a `graph.json` from wiki cross-references for visualization in Obsidian, D3.js, or Gephi.

**`/mindsync export`**
Export wiki as: Marp slide deck, PDF report, structured JSON, or Anki flashcards.

**Contradiction resolution workflow**
When lint flags a contradiction, a guided workflow to resolve it: show both claims, pick the correct one, update both pages, log the resolution.

**`/mindsync search <query>`**
Shell alias that calls `qmd query` and formats results as clickable Obsidian links. Skip opening Claude for quick lookups.

---

## Kudos & References

mindsync is built on the shoulders of these projects and ideas:

| Project | Author | What it contributes |
|---------|--------|---------------------|
| [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) | [@karpathy](https://github.com/karpathy) | The core idea: LLM as wiki maintainer, not just retriever. The pattern this entire project implements. |
| [qmd](https://github.com/tobi/qmd) | [@tobi](https://github.com/tobi) | Local hybrid BM25/vector search for markdown files. Powers semantic search across the wiki. |
| [summarize](https://github.com/steipete/summarize) | [@steipete](https://github.com/steipete) | Converts URLs, PDFs, YouTube, and podcasts into markdown. The primary source ingestion accelerator. |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | [Vercel Labs](https://github.com/vercel-labs) | Rust-based browser automation CLI for AI agents. Lets Claude browse the web autonomously. |
| [Memex (1945)](https://en.wikipedia.org/wiki/Memex) | Vannevar Bush | The original vision of a personal, associative knowledge machine. LLM Wiki is its modern realization. |
| [Obsidian](https://obsidian.md) | Obsidian | Optional markdown editor with graph view, backlinks, and Web Clipper. The recommended vault IDE. |

---

## License

MIT
