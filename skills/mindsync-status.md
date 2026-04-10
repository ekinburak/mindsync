---
name: mindsync-status
description: Quick dashboard showing wiki health — page counts, last ingest, hot cache size, and qmd index freshness
trigger: /mindsync status
---

# /mindsync status

You are generating a quick status dashboard for this wiki. Follow these steps exactly.

## Step 1: Count wiki pages

Run these commands:

```bash
echo "Sources: $(ls wiki/sources/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Entities: $(ls wiki/entities/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Concepts: $(ls wiki/concepts/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Analyses: $(ls wiki/analyses/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Total wiki pages: $(find wiki/ -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
echo "Raw sources: $(find raw/ -name '*' -not -path '*/assets/*' -not -name '.DS_Store' -type f 2>/dev/null | wc -l | tr -d ' ')"
```

## Step 2: Check last activity

Run:

```bash
grep "^## \[" log.md | tail -5
```

Note the type and date of the last 5 log entries.

## Step 3: Check _hot.md size

Run:

```bash
wc -w _hot.md | awk '{print $1}'
```

The result is the approximate token count (words ≈ tokens). Flag if over 500.

## Step 4: Check qmd index freshness

Run:

```bash
qmd status 2>/dev/null || echo "qmd not installed or not configured"
```

If qmd is installed, note when the index was last built. If it hasn't been run since the last ingest, flag it as stale.

## Step 5: Output the dashboard

Print this exact format, filling in values from Steps 1–4:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 mindsync status — [VAULT_NAME]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Wiki pages
   Sources:   N
   Entities:  N
   Concepts:  N
   Analyses:  N
   Total:     N

 Raw sources (unprocessed): N

 Last activity
   [most recent log entry type + date]
   [second most recent]
   [third most recent]

 _hot.md: ~N words  [OK | ⚠ over 500 — consider trimming]

 qmd index: [fresh | ⚠ stale — run: qmd embed | not configured]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

After the dashboard, add one line of commentary if anything needs attention:
- If raw sources > 0: "You have N unprocessed files in raw/ — run /mindsync ingest to process them."
- If _hot.md is over 500 words: "_hot.md is getting long — consider pruning resolved items."
- If qmd is stale: "Vector index is stale — run: qmd embed"
- If no issues: "Everything looks healthy."

Do not append to log.md — status is read-only.
