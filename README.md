# mindsync

A portable Claude/Codex/OpenClaw skill suite for building and maintaining personal knowledge bases using LLMs — based on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by Andrej Karpathy.

Instead of RAG (re-discovering knowledge on every query), you build a **persistent, compounding wiki** — structured markdown files that get richer with every source you add. The LLM writes and maintains all of it. You curate sources and ask questions.

**mindsync helps an agent deeply understand a bounded corpus.** It is more
project/domain-specific than life-wide: one vault is usually one focused area of
knowledge.

Good fits:

- a research topic
- a product idea
- a codebase
- a book or course
- a company/project wiki
- a thesis area
- a "learn everything about X" workspace

## Skills

| Command | What it does |
|---------|-------------|
| `/mindsync init` | One-time setup: creates vault structure, AGENTS.md/CLAUDE.md, installs tools |
| `/mindsync ingest` | Interactive ingest of a new source (URL, file, paste, video, PDF) |
| `/mindsync search` | Semantic search across the wiki via qmd — returns ranked Obsidian links |
| `/mindsync query` | Research a question against the wiki — outputs as text, markdown, or Marp slides |
| `/mindsync lint` | Health-check: finds orphans, contradictions, gaps, article candidates, auto-fills via web |
| `/mindsync status` | Quick dashboard: page counts, last activity, hot cache size, qmd index freshness |
| `/mindsync finetune` | Export wiki-derived JSONL Q&A pairs for future fine-tuning |

## Install

```bash
git clone https://github.com/ekinburak/mindsync.git
cd mindsync
bash install.sh
```

Project-local install is the default:

```bash
bash install.sh --scope project --agent all --target .
```

Global install is opt-in:

```bash
bash install.sh --scope global --agent all
```

Installed components depend on the selected agent:

| What | Where | Purpose |
|------|-------|---------|
| Claude skills | `.claude/skills/` or `~/.claude/skills/` | Claude Code commands |
| Codex plugin | `plugins/mindsync/` plus `.agents/plugins/marketplace.json` | Codex plugin discovery |
| OpenClaw skills | `.openclaw/skills/` or `~/.openclaw/skills/` | OpenClaw-compatible skills |
| Scripts | `scripts/` or agent-local script folder | Deterministic queues, lint, charts, exports |
| Local tools | `.mindsync/tools/` | Required project-local npm CLIs: qmd and summarize |

The canonical project instruction file is `AGENTS.md`. `CLAUDE.md` is generated for Claude compatibility.

## Requirements

- Node.js 18+
- Python 3.10+
- npm for project-local CLI dependencies
- Claude Code, Codex, or OpenClaw

## Dependency Tiers

| Tier | Tool | Why it exists | Default? |
|------|------|---------------|----------|
| Required | Python 3 | Runs `scripts/mindsync.py`, queues, lint, hashes, exports, and scaffold logic | Yes |
| Required | qmd | Local wiki search and embedding fallback when `index.md` is not enough | Yes |
| Required | summarize | Converts URLs, PDFs, YouTube, and podcasts into raw markdown sources | Yes |
| Optional power-user | agent-browser | Browser automation for JavaScript-heavy pages, interactive sites, screenshots, and autonomous web research | No |
| Optional visual output | matplotlib | Renders generated data charts into PNGs under `wiki/analyses/assets/` | No |

Install required tools project-locally inside a vault:

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool qmd --tool summarize
```

They install under `.mindsync/tools/`, not globally. Use `tool-path` to resolve
the runnable binary:

```bash
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd)
"$QMD" search "zero touch ingest"
```

`agent-browser` and `matplotlib` are deliberately optional. The core wiki loop
expects `qmd` and `summarize`.

## Quickstart

1. Install (above) — once, then you can delete the repo
2. Install project-local adapters with `bash install.sh --scope project --agent all --target .`
3. Initialize a vault:
   ```bash
   python3 scripts/mindsync.py init --vault ~/Documents/mywiki --name "Your Name" --domain "research on X" --priority "maintain an accurate wiki"
   ```
   Or run `/mindsync init` in an agent session and answer 4 questions:
   - Your name
   - What this wiki is for
   - The assistant's #1 priority
   - Where to create the vault (any path — created automatically if it doesn't exist)
4. Init sets up everything automatically:
   - Full vault structure (`raw/`, `wiki/`, indexes, log)
   - Personalized `AGENTS.md` plus Claude-compatible `CLAUDE.md`
   - `.mindsync/` deterministic state, queues, source hashes, and checkpoints
   - qmd semantic search configured
   - Required local CLI dependencies under `.mindsync/tools/`
   - Auto-ingest hook wired into the vault (optional)
   - File watcher for `raw/` (optional)
5. Drop a source into `raw/` and say "ingest" — or run `/mindsync ingest`

**Multiple wikis:** Run `/mindsync init` in any folder to create a separate wiki for a different domain. Each vault is fully independent with its own `AGENTS.md`, Claude compatibility file, qmd collection, and hook configuration.

## Vault structure (created by init)

```
your-wiki/
├── AGENTS.md        ← canonical agent-neutral vault instructions
├── CLAUDE.md        ← Claude compatibility file
├── _hot.md          ← active context: goals, open questions, key numbers (~500 tokens)
├── index.md         ← full content catalog (LLM reads before every query)
├── log.md           ← append-only history of every ingest, query, and lint
├── .mindsync/       ← config, pending queues, hashes, checkpoints
├── raw/             ← append-only source files
│   └── assets/      ← downloaded images and attachments
└── wiki/
    ├── entities/    ← people, habits, projects, goals, places
    ├── concepts/    ← ideas, frameworks, themes, mental models
    ├── sources/     ← one summary page per ingested source
    └── analyses/    ← filed query results, charts, slides, exports
        └── assets/  ← generated PNGs and other analysis assets
```

## How ingestion works

**Your active LLM agent is the ingestion model.** There is no separate extraction pipeline. When you run `/mindsync ingest`, the agent reads the source file and writes structured wiki pages using its own language understanding.

### mindsync vs RAG

Most knowledge tools use RAG (Retrieval-Augmented Generation): embed raw text, store vectors, retrieve at query time. The source stays as-is and retrieval does all the work.

mindsync does the opposite:

```
RAG (retrieve-then-understand):
  source → embed raw text → store vectors
  query  → retrieve chunks → LLM reads raw text → answer

mindsync (understand-then-store):
  source → agent reads + understands → writes structured wiki pages → embed pages
  query  → read index + pages → answer from already-synthesized knowledge
```

The expensive, intelligent step happens **once at ingest time**. Queries search against structured, cross-referenced knowledge — not raw chunks of text. This is why the wiki compounds: every source makes the whole knowledge base smarter, not just bigger.

### Two AI layers

| Layer | Model | Runs when | Does what |
|-------|-------|-----------|-----------|
| **Ingestion & queries** | Active LLM agent | During `/mindsync ingest`, `/mindsync query`, `/mindsync lint` | Reads sources, extracts entities and concepts, writes wiki pages, synthesizes answers |
| **Deterministic helper** | `scripts/mindsync.py` | During init, ingest, lint, charts, export | Owns queues, hashes, lint checks, chart rendering, state, and checkpoints |
| **Semantic search index** | qmd's local embedding model (on-device, no data leaves your machine) | After ingest via watcher/Stop hook | Embeds wiki pages for vector search — used as fallback when index.md isn't enough |

### What the agent actually does during ingest

1. Reads the raw source file
2. Identifies the source type (article, paper, podcast, journal, repo, dataset)
3. Extracts key claims, entities, concepts, and quotes using the appropriate template
4. Writes `wiki/sources/YYYY-MM-DD-slug.md` — structured summary
5. Creates or updates `wiki/entities/*.md` and `wiki/concepts/*.md` — cross-referenced pages
6. Updates `index.md` and appends to `log.md`
7. Records the source hash so duplicate raw files are skipped later

`raw/` is append-only. Agents may create new raw source records from URLs, PDFs, pasted text, or browser output, but existing raw files are never edited or deleted.

## How the tools work together

mindsync uses `qmd` and `summarize` as required local tools. `agent-browser` and `matplotlib` are optional.

### qmd — Wiki search engine
**GitHub:** [tobi/qmd](https://github.com/tobi/qmd)

qmd is a local semantic search engine for markdown files. It runs entirely on your device — no data leaves your machine. mindsync uses it as the last-resort retrieval step when the index file isn't enough to answer a query.

**How it's used:**
- During `init`: `python3 scripts/mindsync.py ensure-tools --vault . --tool qmd` can install qmd locally under `.mindsync/tools/`
- Your `wiki/` folder is registered as a qmd collection and embeddings are built
- During queries: if `_hot.md` and `index.md` don't resolve the question, the agent runs `qmd query "<question>"` to search across all wiki pages semantically
- After bulk ingestion: run `python3 scripts/mindsync.py embed --vault .` to rebuild the index with mindsync's embed lock

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool qmd
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd)
"$QMD" query "sleep habits"       # hybrid search (recommended)
"$QMD" search "atomic habits"     # keyword only, fast
"$QMD" vsearch "decision making"  # vector/semantic only
```

You can also configure qmd as an MCP server so supported agents call it as a native tool rather than a shell command — `/mindsync init` shows you the config snippet.

---

### summarize — Source converter
**GitHub:** [steipete/summarize](https://github.com/steipete/summarize)

summarize converts web articles, YouTube videos, podcasts, and PDFs into clean markdown — ready to drop directly into your wiki's `raw/` folder for ingestion. It's the fastest way to get external content into mindsync without copy-pasting.

**How it's used:**
- During `/mindsync ingest`: if you provide a URL or PDF path, the agent runs summarize automatically and saves the output to `raw/` before processing it
- You can also pipe it manually:

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool summarize
SUMMARIZE=$(python3 scripts/mindsync.py tool-path --vault . summarize)

# Article
"$SUMMARIZE" https://example.com/article > raw/2026-04-09-article-title.md

# YouTube video
"$SUMMARIZE" https://youtube.com/watch?v=xxx > raw/2026-04-09-video-title.md

# PDF
"$SUMMARIZE" /path/to/paper.pdf > raw/2026-04-09-paper.md

# Auto-date filename
"$SUMMARIZE" https://example.com/article > raw/$(date +%Y-%m-%d)-article.md
```

After the file lands in `raw/`, run `/mindsync ingest` — or let the file watcher handle it automatically.

---

### agent-browser — Autonomous web browsing (optional)
**GitHub:** [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)

agent-browser is a Rust-based CLI that lets an agent control a browser autonomously — navigate pages, extract content, take screenshots, fill forms — without you copy-pasting anything.

You do **not** need agent-browser for the core mindsync flow. Use it only when
`summarize` is not enough:

- JavaScript-rendered pages
- pages requiring clicks, scrolling, tabs, or forms
- visual inspection of layouts, charts, dashboards, or screenshots
- autonomous web research across several pages

**How it's used:**
- Configured as an MCP server so supported agents can call it as a native tool
- During queries: the agent can browse a URL you mention and extract content for ingestion
- During research: the agent can search the web for sources related to your question
- During ingest: the agent can fetch a live page, screenshot it, and extract structured content

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool agent-browser
AGENT_BROWSER=$(python3 scripts/mindsync.py tool-path --vault . agent-browser)
"$AGENT_BROWSER" install   # downloads Chrome for Testing

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

If you do not install agent-browser, `summarize` still covers most ingest use cases with less setup.

---

### matplotlib — Chart rendering (optional)

matplotlib is only for generated visual analysis outputs, not for understanding
source images. Source images in `raw/assets/` should be interpreted by the active
agent's vision model.

Use matplotlib when wiki data should become a durable chart:

```bash
python3 scripts/mindsync.py chart --vault . --data .mindsync/state/chart.csv --title "Sources by Concept"
```

The output is a PNG in `wiki/analyses/assets/` and can be embedded in Obsidian:

```markdown
![[wiki/analyses/assets/2026-04-12-sources-by-concept.png]]
```

If matplotlib is missing, only chart output is unavailable. Ingest, query, lint,
search, graph export, and training export still work.

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

Each vault is fully self-contained. Run `/mindsync init` in any folder to create a new wiki for a different domain — a research project, a team knowledge base, a book companion. Each gets its own `AGENTS.md`, Claude compatibility file, qmd collection, and retrieval configuration.

## How automation works

This is the most important thing to understand about mindsync. **The wiki grows during agent sessions, not between them.** Every time you open an agent in your vault and run a skill, it compounds knowledge. Between sessions, background jobs keep the search index fresh.

See [`docs/automation-and-helper.md`](docs/automation-and-helper.md) for the deterministic queue, hash, lint, chart, export, and checkpoint commands.

### What happens automatically (no input needed)

| Trigger | What fires | Result |
|---------|-----------|--------|
| You drop a file in `raw/` via Finder, Obsidian Clipper, or terminal | watcher + `queue-scan` | Source is added to `.mindsync/state/pending-ingest.json` |
| Agent writes a new file to `raw/` | runtime hook where supported | Source is queued immediately |
| Next agent turn in zero-touch mode | pending queue | Agent compiles queued sources into `wiki/`, updates index/log, and records hashes |
| Any Claude Code session ends in the vault | `Stop` hook | qmd index rebuilt silently in background if `wiki/` changed |
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
1. `scripts/mindsync.py queue-scan` hashes the file and queues it if new
2. The agent **reads** the file in `raw/`
3. The agent **writes** structured pages into `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`
4. The agent **updates** `index.md` and appends to `log.md`
5. `scripts/mindsync.py mark-ingested` records the source hash
6. The wiki watcher, ingest workflow, or `Stop` hook rebuilds qmd so the new compiled pages are searchable

Existing `raw/` files stay untouched forever as your source of truth.

### How the qmd index stays fresh

There are three layers keeping the search index current — each fires at a different moment:

| Layer | When it fires | How |
|-------|--------------|-----|
| `Stop` hook | Every time you close a Claude Code session | `hook-session-end.sh` runs `python3 scripts/mindsync.py embed --vault .` in the background if wiki files changed |
| **launchd WatchPaths** (macOS) | Within 30 seconds of file changes | `raw/` changes queue sources only; `wiki/` changes refresh qmd |
| cron (Linux fallback) | Nightly at 2am | Standard cron job |

**The launchd layer is the important one.** It keeps capture and search maintenance separate: clipped raw sources are queued without embedding raw text, and qmd is refreshed only after compiled wiki pages change.

**Example timeline:**
```
3:00pm  You clip an article via Obsidian Clipper → lands in raw/
3:00:30 launchd detects the change → source is queued
3:01pm  You open your agent in the vault, type anything
3:01pm  UserPromptSubmit hook detects queued source → agent compiles wiki pages
3:01pm  Source hash recorded, ingest/Stop hook rebuilds qmd
```

**Set up during init** — `/mindsync init` runs `bash scripts/schedule-embed.sh <vault-path>` which installs the launchd job. To verify it's running:

```bash
# Check the launchd job is loaded
launchctl list | grep mindsync

# Check the automation log
cat .mindsync/state/automation.log
```

To remove a watcher, use the exact `launchctl unload` command printed by `scripts/schedule-embed.sh`. Labels include a short vault-path hash to avoid collisions.

### Automation roadmap

The target experience is: you manually add source material through Obsidian
Clipper, Finder, or another capture tool, and mindsync handles everything after
the file lands in `raw/`.

- [x] **Detect clipped raw sources automatically**
  Watch `raw/`, ignore temporary downloads, wait for files to settle, hash new
  sources, and add them to `.mindsync/state/pending-ingest.json`.

- [x] **Keep qmd fresh without embedding raw sources**
  Watch `wiki/` for compiled-page changes and run
  `python3 scripts/mindsync.py embed --vault .` under a lock. Raw watcher only
  queues sources.

- [x] **Repair the pending queue automatically**
  Mark missing pending files, duplicate pending hashes, and already-ingested
  hashes so the queue does not silently rot.

- [x] **Expose automation health**
  `python3 scripts/mindsync.py doctor --vault .` checks structure, tools,
  watcher labels, pending JSON, qmd freshness, hook scripts, and latest
  automation errors.

- [ ] **Install and verify automation during init**
  `/mindsync init` should install watchers, run `doctor`, and show a clear
  pass/fail summary without requiring manual verification commands.

- [ ] **Auto-ingest pending sources in unattended mode**
  Add an explicit opt-in background worker that processes pending raw sources
  into wiki pages, updates `index.md`/`log.md`, marks sources ingested, and
  embeds qmd. This must preserve raw append-only behavior and write checkpoints.

- [ ] **Automate weekly lint**
  Schedule deterministic lint, write a short report to
  `wiki/analyses/YYYY-MM-DD-lint-report.md`, and queue enrichment tasks for thin
  or stale areas. Semantic page edits still require agent judgment.

- [ ] **Automate stale-page review**
  Report pages not updated in 90 days and suggest whether to refresh, archive,
  or leave alone. Do not auto-edit stale pages.

- [ ] **Automate enrichment fetches**
  For enrichment items with URLs, fetch via `summarize`, save into `raw/`, and
  let the normal pending ingest flow handle compilation.

- [ ] **Automate recovery**
  Detect watcher failures, corrupted state, stale qmd, and stuck locks; repair
  what is safe and leave a visible action item for anything requiring judgment.

- [ ] **Optional notification layer**
  Surface pending counts, failed automation, and weekly lint summaries through
  the user's preferred local channel instead of requiring `/mindsync status`.

### Best practices for a living wiki

1. **Open your agent in the vault directory** — not a parent folder. This activates `AGENTS.md`/`CLAUDE.md` and local scripts.
2. **Drop sources freely** — via Obsidian Clipper, Finder, terminal, anything. The hooks handle detection and ingestion automatically.
3. **Start sessions with `/mindsync status`** — see what's unprocessed, last activity, index freshness at a glance.
4. **Run `/mindsync lint` weekly** — finds gaps, suggests new articles, auto-fills via web search.
5. **Keep `_hot.md` under 500 words** — your active context. Prune resolved items. Status warns you when it grows too long.
6. **Trust the compounding** — after 20 sources, queries start connecting dots you hadn't noticed.

## Roadmap / TODO

> Ideas sourced from building mindsync + Karpathy's original [tweet thread](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) on the LLM Wiki pattern.
> Legend: 🟢 easy build · 🟡 medium · 🔵 hard

### 🔴 High priority

- [x] **Level 3 zero-touch queue via hooks** 🔵 *(most impactful)*
  New raw files are hashed into `.mindsync/state/pending-ingest.json`. Runtime hooks inject the pending work into the next agent turn, and the agent compiles sources, updates index/log, and records source hashes.

- [x] **`/mindsync query` skill** 🟢
  A dedicated query skill enforces the retrieval order (`_hot.md` -> `index.md` -> pages -> `qmd`), files valuable answers as analyses, and enforces the 5-page read limit.

- [x] **Rich output formats: Marp + matplotlib** 🟢/🟡
  Karpathy: *"render markdown files, slide shows (Marp format), or matplotlib images, all viewable in Obsidian."*
  — Marp slide decks (easy — markdown with Marp frontmatter, auto-filed to `wiki/analyses/`) 🟢 done
  — matplotlib charts via `scripts/mindsync.py chart`, saved to `wiki/analyses/assets/` and embedded with Obsidian image links 🟡 done
  All outputs filed back into `wiki/analyses/` so they compound in the knowledge base.

- [x] **Web search during lint — missing data imputation queue** 🟡
  Karpathy: *"impute missing data with web searchers."*
  Lint creates enrichment tasks in `.mindsync/state/enrichment-queue.json`; URL-backed tasks are fetched with `summarize` into `raw/` and then ingested.

- [x] **Scheduled `qmd embed`** 🟢
  A watcher, cron job, or runtime stop hook runs `python3 scripts/mindsync.py embed --vault .` so the vector index stays fresh after compiled wiki pages change.

### 🟡 Medium priority

- [x] **`/mindsync status` skill** 🟢
  Quick dashboard at session start: source count, entity/concept/analysis counts, last ingest date, `_hot.md` token count, qmd index freshness.

- [x] **New article candidate suggestions during lint** 🟢
  Karpathy: *"find interesting connections for new article candidates."*
  Lint proactively suggests new concept/entity pages that don't exist yet — based on how often a term appears across sources without its own page. "You mention X in 5 sources but have no concept page for it."

- [x] **Repo, dataset, and image ingestion** 🟡
  Karpathy: *"articles, papers, repos, datasets, images."*
  Ingest supports repo/dataset source templates and queues image assets from `raw/assets/` for captioning and concept/entity linking.

- [~] **Web UI for wiki search** — *not needed*
  Karpathy built this because he had no Obsidian. mindsync uses Obsidian as the vault IDE, which already provides search, graph view, backlinks, and previews. `/mindsync search` covers the semantic qmd layer inside agent sessions. No gap to fill.

- [x] **Output auto-filing** 🟡
  When `summarize` or `agent-browser` produces output during a session, automatically route it to `raw/` and queue it for ingest. Runtime hooks improve this when available.

- [x] **Domain-specific ingest templates** 🟡
  Custom templates per source type: journal entries, research papers, podcast transcripts, and GitHub repos each get a purpose-built structure.

- [ ] **`/mindsync sync` for team wikis** 🔵
  Multi-user support: git branches per contributor, merge wiki updates, detect and resolve edit conflicts between pages.

### 🟢 Nice to have

- [x] **`/mindsync search <query>`** 🟢
  Shell/skill wrapper around `qmd query`, outputting results as clickable Obsidian links. Quick lookups without deep manual search.

- [x] **Graph view export** 🟢
  Parse all `[[wiki/links]]` across wiki pages, generate `graph.json` for visualization in D3.js, Gephi, or Obsidian graph view.

- [x] **Scale playbook** 🟢
  Karpathy's wiki: ~100 articles, ~400K words. Document the transition plan: when to introduce domain sub-indexes (`_index-health.md`), when to move to chunk-level retrieval, when fine-tuning is worth it. See [`docs/scale-playbook.md`](docs/scale-playbook.md).

- [x] **Contradiction resolution workflow** 🟡
  When lint flags a contradiction: show both conflicting claims side by side, ask which is correct, update both pages atomically, log the resolution.

- [x] **Synthetic data generation + fine-tuning export** 🔵
  Karpathy: *"synthetic data generation + finetuning to have your LLM 'know' the data in its weights instead of just context windows."*
  `/mindsync finetune` exports wiki-derived JSONL Q&A pairs. Training remains explicit and separate.

---

## Kudos & References

mindsync is built on the shoulders of these projects and ideas:

| Project | Author | What it contributes |
|---------|--------|---------------------|
| [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) | [@karpathy](https://github.com/karpathy) | The core idea: LLM as wiki maintainer, not just retriever. The pattern this entire project implements. |
| [qmd](https://github.com/tobi/qmd) | [@tobi](https://github.com/tobi) | Local hybrid BM25/vector search for markdown files. Powers semantic search across the wiki. |
| [summarize](https://github.com/steipete/summarize) | [@steipete](https://github.com/steipete) | Converts URLs, PDFs, YouTube, and podcasts into markdown. The primary source ingestion accelerator. |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | [Vercel Labs](https://github.com/vercel-labs) | Rust-based browser automation CLI for AI agents. Lets agents browse the web autonomously. |
| [Memex (1945)](https://en.wikipedia.org/wiki/Memex) | Vannevar Bush | The original vision of a personal, associative knowledge machine. LLM Wiki is its modern realization. |
| [Obsidian](https://obsidian.md) | Obsidian | Optional markdown editor with graph view, backlinks, and Web Clipper. The recommended vault IDE. |

---

## License

MIT
