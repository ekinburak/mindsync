---
name: mindsync-query
description: Query the wiki and optionally file outputs as markdown, Marp slides, charts, or markdown plus chart assets
trigger: /mindsync query
metadata:
  openclaw:
    requires:
      bins: ["python3", "node"]
      npm: ["@tobilu/qmd"]
---

# /mindsync query

Research a question against the compiled wiki. Output modes are:

- `plain`
- `markdown`
- `marp`
- `chart`
- `markdown+chart`

## 1. Retrieve Context

Read in order:

1. `_hot.md`
2. `index.md`
3. One or two relevant wiki pages, never more than five for a normal query
4. `QMD=$(python3 scripts/mindsync.py tool-path --vault . qmd) && "$QMD" query "<question>"` if index navigation is insufficient

Use `[[wiki/path/slug]]` citations for wiki-backed claims. Flag uncertain claims.

## 2. Choose Output

If no output mode is specified, ask. Default to `plain`.

For `plain`, answer in the conversation.

For `markdown`, write `wiki/analyses/YYYY-MM-DD-slug.md` with:

```yaml
---
title:
type: analysis
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
format: markdown
---
```

For `marp`, use Marp frontmatter and keep slides to one idea each.

For `chart` or `markdown+chart`:

1. Create a small CSV or JSON data file under `.mindsync/state/` if the data is derived during the query.
2. Run:

```bash
python3 scripts/mindsync.py chart --vault . --data ".mindsync/state/chart-data.csv" --title "Title" --kind bar
```

3. Save the returned `![[wiki/analyses/assets/...png]]` link in the analysis markdown.

## 3. File Valuable Outputs

When a query produces durable synthesis, file it under `wiki/analyses/`, update
`index.md`, and append:

```markdown
## [YYYY-MM-DD] query | "Question"
Pages consulted: N
Filed as: wiki/analyses/YYYY-MM-DD-slug.md
Output: plain | markdown | marp | chart | markdown+chart
```

## 4. Follow-Ups

End with two or three related questions worth exploring when they would help the
wiki compound.
