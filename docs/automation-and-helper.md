# Automation and Helper

`scripts/mindsync.py` owns deterministic work so the LLM can focus on semantic
wiki maintenance.

## State

State lives under `.mindsync/`:

- `config.json` - vault config and enabled adapters
- `state/pending-ingest.json` - queued raw files and image assets
- `state/source-hashes.json` - ingested source hashes for duplicate prevention
- `state/enrichment-queue.json` - missing-data tasks
- `state/last-embed.json` - qmd freshness timestamp
- `state/checkpoints/` - git diff checkpoints before automated writes
- `tools/` - project-local npm CLI dependencies

## Common Commands

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool qmd --tool summarize
python3 scripts/mindsync.py tool-path --vault . qmd
python3 scripts/mindsync.py queue-scan --vault .
python3 scripts/mindsync.py pending --vault .
python3 scripts/mindsync.py mark-ingested --vault . --path raw/example.md --page wiki/sources/example.md
python3 scripts/mindsync.py lint --vault .
python3 scripts/mindsync.py queue-enrichment --vault . --topic "Topic" --reason "Thin concept page"
python3 scripts/mindsync.py fetch-enrichment --vault . --limit 3
python3 scripts/mindsync.py chart --vault . --data data.csv --title "Chart title"
python3 scripts/mindsync.py export-training --vault .
python3 scripts/mindsync.py checkpoint --vault .
```

## Zero-Touch Boundary

Hooks and watchers can queue sources automatically. An active agent session still
performs semantic compilation because summarizing, linking, contradiction checks,
and image captioning require model judgment.
