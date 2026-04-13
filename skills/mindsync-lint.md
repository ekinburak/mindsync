---
name: mindsync-lint
description: Run deterministic and LLM health checks for broken links, frontmatter, orphans, contradictions, stale claims, and enrichment gaps
trigger: /mindsync lint
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd", "@steipete/summarize"]
    optional:
      npm: ["agent-browser"]
---

# /mindsync lint

Lint has two phases:

1. Deterministic checks handled by scripts.
2. Semantic checks handled by the LLM.

## 1. Deterministic Lint

Run:

```bash
python3 scripts/mindsync.py lint --vault .
```

Use this report for:

- missing frontmatter
- broken wiki links
- orphan pages
- duplicate raw sources
- stale qmd embed state
- index drift
- stale pages older than 90 days
- `_hot.md` over 500 words
- stale or broken pending queue entries
- source/index/log consistency gaps

Do not use LLM time for these mechanical checks.

## 2. Semantic Lint

Read `_hot.md`, `index.md`, and enough relevant pages to assess:

- contradictions between claims
- stale claims superseded by newer source pages
- synthesis gaps
- article candidates
- resolved `_hot.md` items

For contradictions, show both claims side by side and ask before changing pages.
Only start semantic contradiction cleanup when deterministic lint output is small
enough to reason about clearly.

## 3. Enrichment Queue

For missing or thin concepts that need external data, create queue items:

```bash
python3 scripts/mindsync.py queue-enrichment --vault . \
  --topic "topic name" \
  --reason "why this improves the wiki" \
  --query "specific search query"
```

If the user or browser tooling provides a URL, include:

```bash
--url "https://example.com/source"
```

Fetch queued URL-backed enrichments:

```bash
python3 scripts/mindsync.py fetch-enrichment --vault . --limit 3
```

Fetched sources land in `raw/` and are queued for `/mindsync ingest`.

## 4. Log

Append to `log.md`:

```markdown
## [YYYY-MM-DD] lint | routine check
Deterministic issues: N
Contradictions: N
Article candidates: N
Enrichment queued: N
Enrichment fetched: N
```
