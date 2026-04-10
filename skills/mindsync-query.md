---
name: mindsync-query
description: Research a question against the wiki, synthesize an answer, and optionally file it back as an analysis or Marp slide deck
trigger: /mindsync query
---

# /mindsync query

You are researching a question against the wiki. Follow these steps exactly.

## Step 1: Session context

Read in this exact order before doing anything else:
1. `_hot.md` — active context. If this answers the question, stop here.
2. `index.md` — find relevant page paths. Note which sections apply.
3. Read 1–2 of the most relevant pages. **Never read more than 5 pages per query.**

If the question requires information not covered by any page, run:
```bash
qmd query "<question>"
```
Use the results to supplement your answer. Do not read more pages than the limit.

## Step 2: Synthesize answer

Write a clear answer with:
- Citations using Obsidian `[[wiki/path/slug]]` link syntax for every claim
- Bullet structure preferred over prose
- If a claim is uncertain, flag it: "(unverified — check [[wiki/sources/...]])"

## Step 3: Choose output format

Ask: "How do you want this output?"
- **A) Plain answer** — text in this conversation (default)
- **B) Markdown file** — filed as `wiki/analyses/YYYY-MM-DD-slug.md`
- **C) Marp slide deck** — filed as `wiki/analyses/YYYY-MM-DD-slug.md` with Marp format
- **D) Both B and C** — markdown summary + slide deck

For option C or D, format the file as a Marp slide deck:

```
---
marp: true
theme: default
paginate: true
---

# Title

---

## Slide 1 Title

- Key point
- Key point

---

## Slide 2 Title

- Key point

---

## Sources

- [[wiki/sources/source-one]]
- [[wiki/sources/source-two]]
```

Keep each slide to 3–5 bullet points. One idea per slide.

## Step 4: File the output (if B, C, or D chosen)

Write the file to `wiki/analyses/YYYY-MM-DD-<slug>.md`.

Use this frontmatter:

```
---
title: <question as title>
type: analysis
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [list of wiki pages consulted]
format: markdown | marp
---
```

Update `index.md` — add entry under Analyses:
```
- [[analyses/YYYY-MM-DD-slug]] — one-line description
```

Append to `log.md`:
```
## [YYYY-MM-DD] query | "<question>"
Pages consulted: N
Filed as: wiki/analyses/YYYY-MM-DD-slug.md (format: markdown|marp)
```

## Step 5: Suggest next questions

After answering, say: "Related questions worth exploring:" and list 2–3 follow-up questions the wiki could answer. These help grow the wiki through natural exploration.
