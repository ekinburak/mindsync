# mindsync Scale Playbook

> When your wiki grows large, the default single-index retrieval pattern starts to strain. This playbook documents the transition points and what to do at each stage.
>
> Karpathy's reference point: ~100 articles, ~400K words.

---

## Stage 1: 0–50 pages (default setup)

**Retrieval:** `_hot.md` → `index.md` → read 1–2 pages → qmd fallback

**Signs everything is working:**
- `index.md` fits in one read (~2000 tokens)
- `/mindsync query` answers most questions in 2–3 page reads
- `/mindsync lint` completes in one pass

**Nothing to change.** The defaults handle this comfortably.

---

## Stage 2: 50–150 pages

**Symptoms:**
- `index.md` is getting long and crowds the agent context
- Queries often need 4–5 page reads to get a full answer
- Lint takes noticeably longer

**Interventions:**

### Split index.md by domain

Instead of one flat index, create domain sub-indexes:

```
_index-health.md     ← health, habits, sleep, nutrition
_index-work.md       ← projects, skills, career
_index-ideas.md      ← concepts, frameworks, mental models
index.md             ← master index, links to sub-indexes
```

Update `AGENTS.md` and compatibility retrieval protocol:
```
2. Master index. Read index.md. If the question falls in a specific domain,
   read the relevant _index-<domain>.md instead of the full index.
```

### Trim _hot.md ruthlessly

Keep it under 400 tokens. Anything resolved or older than 2 weeks belongs in a wiki page, not hot cache.

### Run qmd embed after every bulk ingest

After adding 5+ sources at once:
```bash
qmd embed
```

---

## Stage 3: 150–400 pages (Karpathy range)

**Symptoms:**
- Even sub-indexes are getting long
- `/mindsync search` returns many results, hard to filter
- Some concept pages have grown to 1000+ words and need their own sub-pages

**Interventions:**

### Move to chunk-level retrieval

Instead of reading full pages, index individual sections. Update `AGENTS.md`:

```
3. Deep read. Open 1–2 pages. For long pages (> 500 words), read only
   the sections relevant to the query — use qmd to identify which section.
```

### Introduce page hierarchies

Long concept pages can spawn sub-pages:

```
wiki/concepts/sleep.md           ← overview + links to sub-pages
wiki/concepts/sleep-stages.md    ← deep dive on stages
wiki/concepts/sleep-tracking.md  ← tracking methods and tools
```

The parent page stays short (~200 words) and links to sub-pages.

### Add a `_digest.md`

A weekly auto-generated digest of what changed:
```
wiki/analyses/YYYY-MM-DD-weekly-digest.md
```
Run `/mindsync query` at the end of each week: "Summarize what changed in the wiki this week" and file the result.

---

## Stage 4: 400+ pages

**At this scale, the LLM context window becomes the primary constraint.**

**Interventions:**

### Fine-tuning (Karpathy's end state)

Export wiki as Q&A pairs and fine-tune a local model to internalize the knowledge base. The fine-tuned model "knows" your wiki without reading it at query time.

```bash
python3 scripts/mindsync.py export-training --vault . --output wiki/analyses/training-export.jsonl
# Generates JSONL Q&A examples from compiled wiki pages.
# Training remains a separate explicit step.
```

### Dedicated retrieval layer

Move qmd to MCP server mode so supported agents call it as a native tool rather than a shell command. Configure the agent MCP settings, for example Claude Code's `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"]
    }
  }
}
```

This lets the agent run multiple qmd queries per session without shell overhead and stream results incrementally.

### Archive old sources

Sources older than 2 years that have been fully synthesized into concept and entity pages can be moved to `raw/archive/`. They stay in the qmd index but don't clutter active reads.

---

## Quick reference

| Pages | index.md | Retrieval | Action |
|-------|----------|-----------|--------|
| 0–50 | Single flat | Default 5-step | Nothing |
| 50–150 | Split by domain | Sub-indexes | Split index, trim _hot.md |
| 150–400 | Hierarchical | Chunk-level | Page hierarchies, digest |
| 400+ | MCP + fine-tune | Internalized | Fine-tune, archive sources |

---

## Signals to watch in /mindsync status

- **`_hot.md` over 500 words** → trim immediately
- **Total pages > 50** → consider splitting index.md
- **qmd index stale > 3 days** → run `qmd embed`
- **Raw sources unprocessed > 5** → batch ingest session needed
