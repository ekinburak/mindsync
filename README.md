# mindsync

A Claude Code skill suite for building and maintaining personal knowledge bases using LLMs — based on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy.

Instead of RAG (re-discovering knowledge on every query), you build a **persistent, compounding wiki** — structured markdown files that get richer with every source you add. The LLM writes and maintains all of it. You curate sources and ask questions.

## Skills

| Command | What it does |
|---------|-------------|
| `/mindsync init` | One-time setup: creates vault structure, personalized CLAUDE.md, installs tools |
| `/mindsync ingest` | Interactive ingest of a new source (URL, file, paste, video, PDF) |
| `/mindsync search` | Semantic search across the wiki via qmd — returns ranked Obsidian links |
| `/mindsync query` | Research a question against the wiki — outputs as text, markdown, or Marp slides |
| `/mindsync lint` | Health-check: finds orphans, contradictions, gaps, article candidates, auto-fills via web |
| `/mindsync status` | Quick dashboard: page counts, last activity, hot cache size, qmd index freshness |

## Install

```bash
git clone https://github.com/ekinburak/mindsync.git
cd mindsync
bash install.sh
```

You can delete the repo after installing — everything needed is copied to `~/.claude/`:

| What | Where | Purpose |
|------|-------|---------|
| 6 skill files | `~/.claude/skills/mindsync-*.md` | Auto-loaded by Claude Code globally |
| 3 scripts | `~/.claude/scripts/mindsync/` | Used by skills at runtime (hook, embed, graph) |

**One install, works everywhere.** The skills are available in every Claude Code session on your machine — any folder, any project, any wiki.

## Requirements

- [Claude Code](https://claude.ai/code) (CLI)
- Node.js 18+

## Quickstart

1. Install (above) — once, then you can delete the repo
2. Open Claude Code **in any folder** — a new folder, an existing project, anywhere
3. Run `/mindsync init` and answer 4 questions:
   - Your name
   - What this wiki is for
   - The assistant's #1 priority
   - Where to create the vault (any path — created automatically if it doesn't exist)
4. Init sets up everything automatically:
   - Full vault structure (`raw/`, `wiki/`, indexes, log)
   - Personalized `CLAUDE.md` auto-loaded by Claude Code
   - qmd semantic search configured
   - Auto-ingest hook wired into the vault (optional)
   - File watcher for `raw/` (optional)
5. Drop a source into `raw/` and say "ingest" — or run `/mindsync ingest`

**Multiple wikis:** Run `/mindsync init` in any folder to create a separate wiki for a different domain. Each vault is fully independent with its own `CLAUDE.md`, qmd collection, and hook configuration.

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

## Graph view export

Generate a `graph.json` from all `[[wiki/links]]` across your wiki:

```bash
bash scripts/generate-graph.sh ~/Documents/mywiki
```

Output: `graph.json` in your vault root with nodes (pages) and edges (links between them). Import into:
- **Obsidian** — place in vault root, visible in graph view automatically
- **D3.js** — load directly as a force-directed graph
- **Gephi** — File > Import > JSON Graph File

## Multiple wikis

Each vault is fully self-contained. Run `/mindsync init` in any folder to create a new wiki for a different domain — a research project, a team knowledge base, a book companion. Each gets its own `CLAUDE.md` tuned to its purpose, its own qmd collection, and its own retrieval configuration.

## How automation works

This is the most important thing to understand about mindsync. **The wiki grows during sessions, not between them.** Every time you open Claude Code in your vault and run a skill, it compounds knowledge. Between sessions, background jobs keep the search index fresh.

### What happens automatically (no input needed)

| Trigger | What fires | Result |
|---------|-----------|--------|
| You drop a file in `raw/` via Finder, Obsidian Clipper, or terminal | `UserPromptSubmit` hook | Next message you send → ingest runs automatically |
| Claude writes a file to `raw/` (e.g. after fetching a URL) | `PostToolUse` hook | Ingest runs immediately, no message needed |
| Any Claude Code session ends in the vault | `Stop` hook | qmd index rebuilt silently in background |
| Every night at 2am | cron job (`schedule-embed.sh`) | qmd index rebuilt as a safety net |

### What needs a command from you

| You want | You say | What happens |
|----------|---------|-------------|
| An answer from your wiki | `/mindsync query` | Retrieval + synthesis + optional filing |
| To find something fast | `/mindsync search sleep habits` | Ranked Obsidian links returned |
| A health check | `/mindsync lint` | Gaps found, web enrichment offered |
| A dashboard | `/mindsync status` | Counts, last activity, index freshness |

### How raw/ → wiki/ works

Files in `raw/` don't move automatically — they are intentionally immutable source records. What happens is:
1. Claude **reads** the file in `raw/`
2. Claude **writes** structured pages into `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`
3. Claude **updates** `index.md` and appends to `log.md`
4. The `Stop` hook rebuilds qmd so the new pages are searchable

The `raw/` file stays untouched forever as your source of truth.

### How the qmd index stays fresh

There are three layers keeping the search index current — each fires at a different moment:

| Layer | When it fires | How |
|-------|--------------|-----|
| `Stop` hook | Every time you close a Claude Code session | `hook-session-end.sh` runs `qmd embed` in the background if wiki files changed |
| **launchd WatchPaths** (macOS) | Within 30 seconds of any file change in `wiki/` or `raw/` | OS-level file watcher — fires even when Claude isn't open |
| cron (Linux fallback) | Nightly at 2am | Standard cron job |

**The launchd layer is the important one.** It means qmd is always current — whether you're in a Claude session, clipping articles via Obsidian, or editing files directly in your vault. You don't need Claude Code open for the index to rebuild.

**Example timeline:**
```
3:00pm  You clip an article via Obsidian Clipper → lands in raw/
3:00:30 launchd detects the change → qmd embed runs silently
3:01pm  You open Claude Code, type anything
3:01pm  UserPromptSubmit hook detects unprocessed file → auto-ingests
3:01pm  Wiki pages written, Stop hook rebuilds qmd again
```

**Set up during init** — `/mindsync init` runs `bash scripts/schedule-embed.sh <vault-path>` which installs the launchd job. To verify it's running:

```bash
# Check the launchd job is loaded
launchctl list | grep mindsync

# Check the embed log
cat ~/.mindsync-embed.log
```

To remove: `launchctl unload ~/Library/LaunchAgents/com.mindsync.embed.<vault-name>.plist`

### Best practices for a living wiki

1. **Open Claude Code in your vault directory** — not a parent folder. This activates `CLAUDE.md` and all hooks.
2. **Drop sources freely** — via Obsidian Clipper, Finder, terminal, anything. The hooks handle detection and ingestion automatically.
3. **Start sessions with `/mindsync status`** — see what's unprocessed, last activity, index freshness at a glance.
4. **Run `/mindsync lint` weekly** — finds gaps, suggests new articles, auto-fills via web search.
5. **Keep `_hot.md` under 500 words** — your active context. Prune resolved items. Status warns you when it grows too long.
6. **Trust the compounding** — after 20 sources, queries start connecting dots you hadn't noticed.

## Roadmap / TODO

> Ideas sourced from building mindsync + Karpathy's original [tweet thread](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) on the LLM Wiki pattern.
> Legend: 🟢 easy build · 🟡 medium · 🔵 hard

### 🔴 High priority

- [x] **Level 3 auto-ingest via Claude Code hooks** 🔵 *(most impactful)*
  The current file watcher (`watch-raw.sh`) detects new files in `raw/` but you still run `/mindsync ingest` manually. The goal is **zero-touch ingestion**: a Claude Code `PostToolUse` hook fires on any write to `raw/`, automatically triggering the full ingest flow — wiki pages updated, index and log maintained — without you saying anything. Drop a file, the wiki updates itself.

- [x] **`/mindsync query` skill** 🟢
  A dedicated query skill enforcing the retrieval order (`_hot.md` → `index.md` → pages → `qmd`), always offering to file valuable answers as analyses, and enforcing the 5-page read limit. Currently queries rely on CLAUDE.md rules alone with no skill enforcement.

- [x] **Rich output formats: Marp + matplotlib** 🟢/🟡
  Karpathy: *"render markdown files, slide shows (Marp format), or matplotlib images, all viewable in Obsidian."*
  — Marp slide decks (easy — markdown with Marp frontmatter, auto-filed to `wiki/analyses/`) 🟢 ✅ done
  — matplotlib charts (medium — Python + chart code generated by Claude, saved as `.png`) 🟡 pending
  All outputs filed back into `wiki/analyses/` so they compound in the knowledge base.

- [x] **Web search during lint — missing data imputation** 🟡
  Karpathy: *"impute missing data with web searchers."*
  When lint finds a gap (thin concept page, outdated entity), trigger a web search via `agent-browser` or `summarize` to fill it automatically. Lint becomes an active wiki enhancer, not just a report.

- [x] **Scheduled `qmd embed`** 🟢
  A cron job or Claude Code scheduled trigger runs `qmd embed` nightly so the vector index stays fresh after bulk ingestion.

### 🟡 Medium priority

- [x] **`/mindsync status` skill** 🟢
  Quick dashboard at session start: source count, entity/concept/analysis counts, last ingest date, `_hot.md` token count, qmd index freshness.

- [x] **New article candidate suggestions during lint** 🟢
  Karpathy: *"find interesting connections for new article candidates."*
  Lint proactively suggests new concept/entity pages that don't exist yet — based on how often a term appears across sources without its own page. "You mention X in 5 sources but have no concept page for it."

- [x] **Repo and dataset ingestion** 🟡
  Karpathy: *"articles, papers, repos, datasets, images."*
  Add ingest support for GitHub repos (README + key files summary), CSV/JSON datasets (column descriptions + statistics), and image collections (captioned via vision model).

- [~] **Web UI for wiki search** — *not needed*
  Karpathy built this because he had no Obsidian. mindsync uses Obsidian as the vault IDE, which already provides search, graph view, backlinks, and previews. `/mindsync search` covers the semantic qmd layer inside Claude Code. No gap to fill.

- [x] **Output auto-filing** 🟡
  When `summarize` or `agent-browser` produces output during a session, automatically route it to `raw/` and queue it for ingest — no copy-paste. Requires Claude Code tool output hooks.

- [x] **Domain-specific ingest templates** 🟡
  Custom templates per source type: journal entries, research papers, podcast transcripts, and GitHub repos each get a purpose-built structure.

- [ ] **`/mindsync sync` for team wikis** 🔵
  Multi-user support: git branches per contributor, merge wiki updates, detect and resolve edit conflicts between pages.

### 🟢 Nice to have

- [x] **`/mindsync search <query>`** 🟢
  Shell alias wrapping `qmd query`, outputting results as clickable Obsidian links. Quick lookups without opening Claude.

- [x] **Graph view export** 🟢
  Parse all `[[wiki/links]]` across wiki pages, generate `graph.json` for visualization in D3.js, Gephi, or Obsidian graph view.

- [x] **Scale playbook** 🟢
  Karpathy's wiki: ~100 articles, ~400K words. Document the transition plan: when to introduce domain sub-indexes (`_index-health.md`), when to move to chunk-level retrieval, when fine-tuning is worth it. See [`docs/scale-playbook.md`](docs/scale-playbook.md).

- [x] **Contradiction resolution workflow** 🟡
  When lint flags a contradiction: show both conflicting claims side by side, ask which is correct, update both pages atomically, log the resolution.

- [ ] **Synthetic data generation + fine-tuning** 🔵
  Karpathy: *"synthetic data generation + finetuning to have your LLM 'know' the data in its weights instead of just context windows."*
  Export wiki as Q&A fine-tuning pairs. Fine-tune a local model (Mistral, Llama) to internalize your knowledge base. `/mindsync finetune` generates the dataset; training runs separately.

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
