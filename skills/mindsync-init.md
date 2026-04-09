---
name: mindsync-init
description: Initialize a new LLM Wiki vault with full structure, tooling, and personalized CLAUDE.md
trigger: /mindsync init
---

# /mindsync init

You are setting up a new LLM Wiki vault. Follow these steps exactly and in order.

## Step 1: Personalize

Ask the following questions one at a time. Wait for each answer before asking the next.

1. "What's your name?"
2. "What is this wiki for? (one sentence — e.g. 'my personal second brain' or 'research on climate tech')"
3. "What is the #1 priority for this assistant? (e.g. 'help me understand my patterns and make better decisions')"
4. "What is the full path to the vault directory? (e.g. ~/Documents/mywiki)"

Store answers as: NAME, DOMAIN, PRIORITY, VAULT_PATH.

Set WIKI_NAME = last segment of VAULT_PATH (e.g. "mywiki").
Set DATE = today's date in YYYY-MM-DD format.

## Step 2: Detect and install tools

Check each tool. If missing, offer to install.

Run these checks:
```bash
which qmd || echo "NOT FOUND"
which summarize || echo "NOT FOUND"
which agent-browser || echo "NOT FOUND"
```

If qmd is NOT FOUND:
- Say: "qmd (wiki search) is not installed. Installing now..."
- Run: `npm install -g @tobilu/qmd`

If summarize is NOT FOUND:
- Say: "summarize (URL to markdown converter) is not installed. Installing now..."
- Run: `npm install -g @steipete/summarize`

If agent-browser is NOT FOUND:
- Say: "agent-browser (autonomous web browsing) is optional. Install it? (y/n)"
- If yes: Run: `npm install -g agent-browser && agent-browser install`

## Step 3: Scaffold the vault

Create all directories:

```bash
mkdir -p VAULT_PATH/raw/assets
mkdir -p VAULT_PATH/wiki/entities
mkdir -p VAULT_PATH/wiki/concepts
mkdir -p VAULT_PATH/wiki/sources
mkdir -p VAULT_PATH/wiki/analyses
mkdir -p VAULT_PATH/docs/superpowers/specs
```

Write VAULT_PATH/CLAUDE.md using the CLAUDE.md.template content below, substituting:
- WIKI_NAME placeholder with the wiki name
- NAME placeholder with the user's name
- DOMAIN placeholder with the domain description
- PRIORITY placeholder with the priority statement
- DOMAIN_DESCRIPTION placeholder with the domain description
- VAULT_PATH placeholder with the full vault path (e.g. /Users/name/Documents/mywiki)

CLAUDE.md template content:
---
# WIKI_NAME

You are NAME's DOMAIN assistant. Your #1 priority is PRIORITY.

Everything you do serves this. Do not read from the wiki unless the task needs knowledge context — execution, generation, and technical work often do not.

---

## Identity

You maintain this wiki. You write and update all files in `wiki/`, `index.md`, `_hot.md` suggestions, and `log.md`. NAME curates raw sources and asks questions. You do the rest.

**Every session:** Read `_hot.md` first, then `index.md`, then the last 10 entries of `log.md` before doing anything else.

---

## Knowledge Base

Wiki lives at: `VAULT_PATH/wiki/`

When a task needs knowledge context, follow this retrieval protocol in order:

1. **Hot cache first.** Read `_hot.md` (~500 tokens). Contains active threads, current goals, and key numbers. Resolves most queries without reading further.
2. **Master index.** Read `index.md` if hot cache isn't enough. Check the Entities, Concepts, Sources, and Analyses sections for relevant pages.
3. **Deep read.** Open 1–2 relevant wiki pages. Never open more than 5 pages per query.
4. **Grep fallback.** Search `wiki/**/*.md` by keyword if the page isn't indexed.
5. **qmd search.** Run `qmd query "<question>"` for semantic search across the full wiki.

**Do NOT read from the wiki** unless the task genuinely needs knowledge context. Execution, content generation, and technical work often do not.

---

## Ownership Rules

| Path | Owner | Rule |
|------|-------|------|
| `raw/` | Human | Read-only for you. Never create, edit, or delete files here. |
| `wiki/` | LLM | You own every file here. Create, update, cross-reference freely. |
| `_hot.md` | Human | You may suggest updates, never write directly. |
| `index.md` | LLM | Update on every ingest or filed analysis. |
| `log.md` | LLM | Append only. Never edit past entries. |
| `CLAUDE.md` | Human | Only edit if explicitly asked. |

---

## Page Conventions

Every file in `wiki/` uses this frontmatter:

```yaml
---
title:
type: entity | concept | source | analysis
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
---
```

| Type | Folder | Contents |
|------|--------|----------|
| `source` | `wiki/sources/` | Summary of one raw source. Key claims, quotes, takeaways. |
| `entity` | `wiki/entities/` | A person, habit, project, goal, or place. |
| `concept` | `wiki/concepts/` | An idea, framework, theme, or mental model. |
| `analysis` | `wiki/analyses/` | Filed query result: comparison, synthesis, reflection. |

**File naming:**
- Sources & analyses: `YYYY-MM-DD-slug.md`
- Entities & concepts: `slug.md`

**Cross-references:** Always use Obsidian double-bracket link syntax. Link every entity and concept mention, every time.

---

## Workflows

### INGEST
Run `/mindsync ingest` or triggered automatically by file watcher.

1. Read source
2. Discuss key takeaways with NAME — ask what to emphasize/skip
3. Wait for input before writing
4. Write `wiki/sources/YYYY-MM-DD-slug.md`
5. Update relevant `wiki/entities/` and `wiki/concepts/` pages
6. Update `index.md`
7. Append to `log.md`: `## [YYYY-MM-DD] ingest | Source Title`
8. Suggest `_hot.md` updates if relevant

### QUERY
1. Read `_hot.md` then `index.md` then relevant pages
2. Answer with wiki citations using Obsidian link syntax
3. If synthesis is non-trivial — offer to file as `wiki/analyses/YYYY-MM-DD-slug.md`
4. If filed — update `index.md`, append to `log.md`

### LINT
Run `/mindsync lint`.

1. Read all `wiki/` pages
2. Report: orphans, missing pages, contradictions, stale claims
3. Suggest: new questions, new sources, stale `_hot.md` entries
4. Append to `log.md`: `## [YYYY-MM-DD] lint | routine check`

---

## Style Rules

- Entity pages: second person ("You tend to..." / "NAME tends to...")
- Concept & source pages: neutral third person
- Keep summaries tight — one claim per sentence
- Prefer bullet lists over paragraphs
- Flag contradictions explicitly
- Never delete a cross-reference without replacing it

---

## Domain: DOMAIN_DESCRIPTION
---

Write VAULT_PATH/_hot.md:
---
# _hot.md — Active Context

> Human-maintained. Update this when priorities shift. Claude reads this first on every session.
> Keep total length under 500 tokens.

---

## Active right now
<!-- What you're working on, reading, or thinking about this week -->

## Key numbers
<!-- Metrics, streaks, targets that matter right now -->

## Open questions
<!-- Things you're trying to figure out -->
---

Write VAULT_PATH/index.md substituting WIKI_NAME, DOMAIN_DESCRIPTION, DATE:
---
# WIKI_NAME index

> DOMAIN_DESCRIPTION — maintained by LLM. Last updated: DATE.

---

## Entities
*(empty — add sources to populate)*

## Concepts
*(empty — add sources to populate)*

## Sources
*(empty — ingest your first source to begin)*

## Analyses
*(empty)*
---

Write VAULT_PATH/log.md substituting WIKI_NAME, DATE:
---
# WIKI_NAME log

> Append-only. Format: `## [YYYY-MM-DD] <type> | <title>`
> Types: ingest | query | lint | schema

---

## [DATE] schema | Initial setup
Vault scaffolded by /mindsync init.
Structure: raw/, wiki/entities/, wiki/concepts/, wiki/sources/, wiki/analyses/
Ready for first ingest.
---

Delete any Welcome.md boilerplate if present.

## Step 4: Configure qmd

Run:
```bash
qmd collection add VAULT_PATH/wiki --name WIKI_NAME
qmd context add qmd://WIKI_NAME "DOMAIN"
qmd embed
```

## Step 5: File watcher (optional)

Ask: "Want auto-ingest when files land in raw/? This requires fswatch. Set it up? (y/n)"

If yes:
- Check: `which fswatch || echo "NOT FOUND"`
- If not found: say "Install fswatch with: brew install fswatch. Run setup again after installing."
- If found: write VAULT_PATH/scripts/watch-raw.sh:

```bash
#!/bin/bash
# watch-raw.sh — Auto-trigger /mindsync ingest when files land in raw/
# Usage: bash scripts/watch-raw.sh
# Requires: fswatch (brew install fswatch)

RAW_DIR="$(dirname "$0")/../raw"

echo "Watching $RAW_DIR for new files..."
fswatch -0 --event Created "$RAW_DIR" | while IFS= read -r -d '' filepath; do
  filename=$(basename "$filepath")
  if [[ "$filepath" == *"/assets/"* ]] || [[ "$filename" == .* ]]; then
    continue
  fi
  echo "[$(date '+%Y-%m-%d %H:%M')] New file detected: $filename"
  echo "Run: /mindsync ingest $filepath"
done
```

Then run: `chmod +x VAULT_PATH/scripts/watch-raw.sh`

## Step 6: MCP config (optional)

Ask: "Want to configure qmd and agent-browser as MCP tools in Claude Code? (y/n)"

If yes, show this JSON to add to Claude Code settings (~/.claude/settings.json under mcpServers):

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"]
    },
    "agent-browser": {
      "command": "agent-browser",
      "args": ["mcp"]
    }
  }
}
```

## Step 7: Confirm

Print a summary showing what was created and next steps:
- Vault path
- CLAUDE.md written (personalized for NAME)
- _hot.md, index.md, log.md created
- qmd configured
- Watcher status
- MCP status
- Next steps: open vault, drop source in raw/, run /mindsync ingest
