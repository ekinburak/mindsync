# mindsync

A Claude Code skill suite for building and maintaining personal knowledge bases using LLMs — based on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy.

Instead of RAG (re-discovering knowledge on every query), you build a **persistent, compounding wiki** — structured markdown files that get richer with every source you add. The LLM writes and maintains all of it. You curate sources and ask questions.

## Skills

| Command | What it does |
|---------|-------------|
| `/mindsync init` | One-time setup: creates vault structure, personalized CLAUDE.md, installs tools |
| `/mindsync ingest` | Interactive ingest of a new source (URL, file, paste, video, PDF) |
| `/mindsync query` | Research a question against the wiki — outputs as text, markdown, or Marp slides |
| `/mindsync lint` | Health-check: finds orphans, contradictions, gaps, article candidates |
| `/mindsync status` | Quick dashboard: page counts, last activity, hot cache size, qmd index freshness |

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

## Auto-ingest

mindsync has two levels of auto-ingest, set up during `/mindsync init`:

### Level 2 — File watcher (notifies you)

`scripts/watch-raw.sh` uses `fswatch` to detect new files dropped into `raw/` and prints a terminal notification. You then tell Claude to ingest. Requires `fswatch`:

```bash
brew install fswatch
bash your-wiki/scripts/watch-raw.sh
```

### Level 3 — Claude Code hook (acts automatically)

`scripts/hook-auto-ingest.sh` is a Claude Code `PostToolUse` hook. It fires whenever Claude itself writes a file to `raw/` — for example, after fetching a URL with `summarize` or browsing with `agent-browser`. Claude sees the hook output and immediately runs the ingest flow without you typing anything.

**What's automatic vs. manual:**

| How the file lands in raw/ | What happens |
|----------------------------|-------------|
| Claude fetched it (summarize, agent-browser) | Hook fires → ingest runs automatically |
| You dropped it manually (Finder, terminal) | Say "ingest" → Claude processes it |
| You forgot you dropped something | `/mindsync status` shows unprocessed count |

The manual drop case is intentionally one word. Curation — deciding what enters the wiki — is a deliberate act. The hook closes the loop for the cases where Claude is already doing the work.

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

- [ ] **Web search during lint — missing data imputation** 🟡
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

- [ ] **Repo and dataset ingestion** 🟡
  Karpathy: *"articles, papers, repos, datasets, images."*
  Add ingest support for GitHub repos (README + key files summary), CSV/JSON datasets (column descriptions + statistics), and image collections (captioned via vision model).

- [ ] **Web UI for wiki search** 🟡
  Karpathy: *"vibe coded a small search engine over the wiki, which I use directly in a web UI."*
  A minimal local web interface (`localhost:3000`) wrapping `qmd` — search results as cards with backlinks, previews, and one-click Obsidian deep links.

- [ ] **Output auto-filing** 🟡
  When `summarize` or `agent-browser` produces output during a session, automatically route it to `raw/` and queue it for ingest — no copy-paste. Requires Claude Code tool output hooks.

- [ ] **Domain-specific ingest templates** 🟡
  Custom templates per source type: journal entries, research papers, podcast transcripts, and GitHub repos each get a purpose-built structure.

- [ ] **`/mindsync sync` for team wikis** 🔵
  Multi-user support: git branches per contributor, merge wiki updates, detect and resolve edit conflicts between pages.

### 🟢 Nice to have

- [ ] **`/mindsync search <query>`** 🟢
  Shell alias wrapping `qmd query`, outputting results as clickable Obsidian links. Quick lookups without opening Claude.

- [ ] **Graph view export** 🟢
  Parse all `[[wiki/links]]` across wiki pages, generate `graph.json` for visualization in D3.js, Gephi, or Obsidian graph view.

- [ ] **Scale playbook** 🟢
  Karpathy's wiki: ~100 articles, ~400K words. Document the transition plan: when to introduce domain sub-indexes (`_index-health.md`), when to move to chunk-level retrieval, when fine-tuning is worth it.

- [ ] **Contradiction resolution workflow** 🟡
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
