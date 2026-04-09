---
name: mindsync-ingest
description: Interactively ingest a new source into the LLM Wiki
trigger: /mindsync ingest
---

# /mindsync ingest

You are ingesting a new source into the wiki. Follow these steps exactly.

## Step 1: Session context

Read these files before doing anything else:
1. `_hot.md`
2. `index.md`
3. Last 10 entries of `log.md`

## Step 2: Identify the source

If a file path was passed as an argument, use it directly (go to Step 3A).

Otherwise ask: "What's the source?"
- A) Path already in raw/ — go to Step 3A
- B) URL (article or webpage) — go to Step 3B
- C) YouTube or podcast URL — go to Step 3B
- D) PDF file path — go to Step 3C
- E) Paste text — go to Step 3D

## Step 3: Fetch and save

**3A — File already in raw/:**
Read the file directly. Set SLUG = filename without extension. Set DATE = today's date.

**3B — URL:**
Run: `summarize <URL> > raw/<DATE>-<SLUG>.md`
Where SLUG is a kebab-case version of the article title. Then read the saved file.

**3C — PDF:**
Run: `summarize <PDF_PATH> > raw/<DATE>-<SLUG>.md`
Then read the saved file.

**3D — Paste text:**
Save the pasted content as `raw/<DATE>-freeform.md`. Then read it.

## Step 4: Discuss

Show the user: "Here are the key takeaways I see:" followed by a numbered list of 3-5 key points.

Then ask: "Anything to emphasize or skip before I write?"

Wait for the user's response before writing anything.

## Step 5: Write wiki pages

Write `wiki/sources/<DATE>-<SLUG>.md` with:
- YAML frontmatter (title, type: source, tags, created, updated, sources array)
- Summary: 2-3 sentence overview
- Key claims: bullet list of main points
- Notable quotes: 1-3 direct quotes if present
- Links to all entities and concepts touched using Obsidian double-bracket link syntax

For each entity and concept mentioned:
- If the page exists: open it, add or update content, update the `updated:` date, add source to `sources:` array
- If it does not exist: create it with full frontmatter and an initial section from this source

## Step 6: Update indexes

Update `index.md`:
- Add/update entry under Sources with a one-line summary
- Add/update entries for any new or updated entities and concepts

Append to `log.md`:
```
## [DATE] ingest | SOURCE_TITLE
Processed: wiki/sources/DATE-SLUG.md
Updated: list of touched pages
Key insight: one sentence
```

## Step 7: Hot cache check

Ask: "Anything from this source worth adding to _hot.md? Here are my suggestions:" followed by any relevant suggestions.

Wait for user's response. Do not write to `_hot.md` directly — only suggest updates.
