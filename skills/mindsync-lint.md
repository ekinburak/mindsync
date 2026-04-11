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

After listing all contradictions, offer to resolve them interactively (see Step 3B).

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

## Step 3B: Contradiction resolution (interactive)

If Step 3 found contradictions, ask once:

> "Found N contradictions. Resolve them now? (y / s to select / n to skip)"

**If n:** Skip to Step 4.

**If y or s:**

For each confirmed contradiction, present it side by side:

```
CONTRADICTION: [[page-a]] vs [[page-b]]

Page A claims:
"<exact quote or paraphrase of claim from page-a>"
Source: [[sources/...]] (dated YYYY-MM-DD)

Page B claims:
"<exact quote or paraphrase of claim from page-b>"
Source: [[sources/...]] (dated YYYY-MM-DD)

Which is correct? (a / b / both / neither / skip)
```

Wait for the user's response, then:

- **a** — Update page-b to match page-a. Add a note: `> Updated: conflicts with [[page-a]] resolved on DATE — [[page-a]] is authoritative.`
- **b** — Update page-a to match page-b. Add the same note in reverse.
- **both** — Both claims are true in different contexts. Add a nuance note to both pages explaining when each applies.
- **neither** — Both are wrong. Ask: "What's the correct claim?" Then update both pages with the correction.
- **skip** — Leave as-is, keep "needs resolution" flag.

After updating, remove the "needs resolution" flag from both pages and update their `updated:` dates.

Log each resolved contradiction:
```
Resolved: [[page-a]] vs [[page-b]] — user chose: a/b/both/neither
```

## Step 4: Web enrichment (missing data imputation)

Karpathy: *"impute missing data with web searchers."*

Collect all enrichable items from the report — items where a web search would actually help:
- Article candidates (concepts mentioned 3+ times, no page)
- Thin pages (existing pages under 100 words)
- Stale claims (facts flagged as outdated)

If there are 0 enrichable items, skip to Step 5.

If there are enrichable items, present the list and ask once:

> "Found N items I can enrich with web data: [list]. Auto-fill them? (y / s to select / n to skip)"

**If n:** Skip to Step 5.

**If y or s (user selects a subset):**

For each confirmed item:

1. Check if agent-browser is available:
```bash
which agent-browser || echo "NOT FOUND"
```

2. **If agent-browser is available:** Search for the topic and fetch the top result:
```bash
agent-browser search "<concept or topic name> overview"
```
Take the most relevant URL from results, then:
```bash
summarize <URL> > raw/$(date +%Y-%m-%d)-<slug>-supplement.md
```

3. **If agent-browser is NOT available but summarize is:** Ask the user for a URL:
> "agent-browser isn't installed — paste a URL for '<topic>' and I'll fetch it, or press Enter to skip."
If URL provided: run `summarize <URL> > raw/$(date +%Y-%m-%d)-<slug>-supplement.md`

4. **If neither is available:** List specific search terms the user can look up:
> "Neither agent-browser nor summarize is available. To fill these gaps manually, search for:
> - '<topic 1>': suggested query
> - '<topic 2>': suggested query"

After saving each file to `raw/`, Claude Code's PostToolUse hook will automatically trigger `/mindsync ingest` for each one. Wait for each ingest to complete before fetching the next.

After all enrichment is done, report:
```
Enriched: N pages
Skipped: N (user skipped or no tool available)
```

## Step 5: Log

Append to `log.md`:
```
## [DATE] lint | routine check
Orphans: N found
Missing pages: N found
Contradictions: N found
Article candidates: N suggested
Enriched via web: N pages
Suggestions: N
```
