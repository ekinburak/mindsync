---
name: llm-wiki-lint
description: Health-check the LLM Wiki for orphans, contradictions, stale claims, and gaps
trigger: /llm-wiki lint
---

# /llm-wiki lint

You are running a health check on the wiki. Follow these steps exactly.

## Step 1: Session context

Read:
1. `_hot.md`
2. `index.md`
3. Last 10 entries of `log.md`

## Step 2: Read all wiki pages

Read every file in `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/analyses/`.

## Step 3: Report

Produce a lint report with these sections:

### Orphan pages
Pages that exist in `wiki/` but are not linked from any other page.
For each: path and suggested fix.

### Missing pages
Concepts or entities linked in wiki pages but without their own page.
For each: the linked path and which source mentions it.

### Contradictions
Claims in one page that conflict with claims in another.
For each: both pages, the conflicting claims, and "needs resolution".

### Stale claims
Facts that newer sources have superseded. Check `updated:` dates vs source dates.
For each: the page, the claim, and the newer source that supersedes it.

### Frontmatter gaps
Pages missing required frontmatter fields (type, sources, created, updated).
For each: the page and which fields are missing.

### Suggestions
- New questions worth investigating
- New sources to look for
- `_hot.md` entries that appear resolved or stale

## Step 4: Log

Append to `log.md`:
```
## [DATE] lint | routine check
Orphans: N found
Missing pages: N found
Contradictions: N found
Suggestions: N
```
