---
name: mindsync-ingest
description: Zero-touch ingest pending raw sources and image assets into the compiled markdown wiki
trigger: /mindsync ingest
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd", "@steipete/summarize"]
---

# /mindsync ingest

Ingest pending sources from the append-only `raw/` archive into the compiled
wiki. Use deterministic scripts for queueing, hashing, checkpoints, and embed
state. Use the LLM for understanding and wiki writing.

## 1. Prepare Queue

Run:

```bash
python3 scripts/mindsync.py queue-scan --vault .
python3 scripts/mindsync.py pending --vault .
```

If there are no pending sources, stop.

Before automated writes:

```bash
python3 scripts/mindsync.py checkpoint --vault .
```

## 2. Process Each Pending Item

For `kind: source`:

1. Read the raw file without modifying it.
2. Detect source type: article, paper, transcript, journal, repo, dataset, or freeform.
3. Write `wiki/sources/YYYY-MM-DD-slug.md` with frontmatter, summary, key claims, quotes, and source-specific sections.
4. Create or update related `wiki/entities/*.md` and `wiki/concepts/*.md`.
5. Add Obsidian links using `[[wiki/path/slug]]`.

For `kind: image`:

1. Inspect the image if the runtime supports vision or local image viewing.
2. Create or update a source page that includes:
   - local asset link
   - caption
   - visible entities and concepts
   - why it matters to the wiki domain
3. Link the image from related entity/concept pages when useful.

## 3. Update Wiki State

For every ingested item:

1. Update `index.md`.
2. Append to `log.md`:

```markdown
## [YYYY-MM-DD] ingest | Source Title
Processed: wiki/sources/YYYY-MM-DD-slug.md
Updated: wiki pages touched
Key insight: one sentence
```

3. Mark the source hash:

```bash
python3 scripts/mindsync.py mark-ingested --vault . --path "raw/path.md" --page "wiki/sources/YYYY-MM-DD-slug.md"
```

## 4. Refresh Search

If qmd is available:

```bash
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd)
"$QMD" embed
python3 scripts/mindsync.py mark-embed --vault .
```

## 5. Hot Cache

Suggest `_hot.md` updates if the source changes active priorities or open
questions. Do not write `_hot.md` unless the user explicitly asks.
