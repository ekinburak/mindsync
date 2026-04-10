---
name: mindsync-lint
description: Health-check the LLM Wiki for orphans, contradictions, stale claims, and gaps
trigger: /mindsync lint
---

# /mindsync lint

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

### Article candidates
Karpathy: *"find interesting connections for new article candidates."*

For each term, concept, or entity that:
- Appears in 3 or more source or entity pages WITHOUT its own concept page, OR
- Is cross-referenced frequently but only has a stub (under 100 words)

List it as an article candidate:

**Candidate:** [[concepts/candidate-name]]
**Mentioned in:** [[sources/a]], [[sources/b]], [[entities/c]]
**Suggested angle:** one sentence on what the page should cover

### Suggestions
- New questions worth investigating based on gaps in the wiki
- New external sources to look for (be specific: "a paper on X", "an article about Y")
- `_hot.md` entries that appear resolved or no longer active

## Step 4: Log

Append to `log.md`:
```
## [DATE] lint | routine check
Orphans: N found
Missing pages: N found
Contradictions: N found
Article candidates: N suggested
Suggestions: N
```
