---
name: mindsync-search
description: Search the wiki semantically using qmd and return results as clickable Obsidian links
trigger: /mindsync search
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd"]
---

# /mindsync search

You are running a fast semantic search across the wiki. Follow these steps exactly.

## Step 1: Get the query

If a query was passed as an argument, use it directly.

Otherwise ask: "What are you searching for?"

## Step 2: Check qmd

```bash
python3 scripts/mindsync.py tool-path --vault . qmd || echo "NOT FOUND"
```

If NOT FOUND:
- Say: "qmd is not installed. Run: python3 scripts/mindsync.py ensure-tools --vault . --tool qmd"
- Fall back to grep search:
```bash
rg -l "<query>" wiki/ -g "*.md" | head -10
```
Format grep results as Obsidian links and stop here.

## Step 3: Run search

Run all three search modes in parallel for the best results:

```bash
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd)
"$QMD" query "<query>"
```

This runs hybrid BM25 + vector search. It is the recommended default.

For keyword-heavy queries also run:
```bash
"$QMD" search "<query>"
```

## Step 4: Format and return results

Present results as a ranked list with Obsidian links:

```
Results for "<query>":

1. [[wiki/sources/2026-01-15-slug]] — one-line description of why this matches
2. [[wiki/concepts/concept-name]] — one-line description
3. [[wiki/entities/entity-name]] — one-line description
...
```

- Show up to 10 results
- Include only results with a relevance score above 0.3 (qmd shows scores)
- If a result has no wiki page (qmd indexed it but it was deleted), skip it

## Step 5: Offer next action

After results, ask:
> "Want me to read any of these and answer a question, or file a query as an analysis?"

If yes — run `/mindsync query` with the user's question using these pages as the starting point.
If no — done.
