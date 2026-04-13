---
name: mindsync-status
description: Show wiki health, pending ingest queue, page counts, hot cache size, qmd freshness, and enrichment queue status
trigger: /mindsync status
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd"]
---

# /mindsync status

Generate a read-only dashboard.

## Commands

Run:

```bash
python3 scripts/mindsync.py queue-scan --vault .
python3 scripts/mindsync.py pending --vault .
python3 scripts/mindsync.py lint --vault . --json
python3 scripts/mindsync.py doctor --vault . --json || true
```

Also count:

```bash
find wiki/sources -name '*.md' 2>/dev/null | wc -l
find wiki/entities -name '*.md' 2>/dev/null | wc -l
find wiki/concepts -name '*.md' 2>/dev/null | wc -l
find wiki/analyses -name '*.md' 2>/dev/null | wc -l
wc -w _hot.md
grep '^## \[' log.md | tail -5
```

If qmd exists, run:

```bash
QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd 2>/dev/null) && "$QMD" status 2>/dev/null || true
```

## Output

Report:

- page counts by type
- pending ingest items
- deterministic lint counts
- stale page count
- `_hot.md` word count
- last five log entries
- qmd status or stale/unknown state
- watcher health from `doctor`
- latest automation error from `.mindsync/state/automation.log`
- enrichment queue counts from `.mindsync/state/enrichment-queue.json`

Do not append to `log.md`.
