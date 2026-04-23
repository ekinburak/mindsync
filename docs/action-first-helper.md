# Action-First Helper

`scripts/mindsync.py` owns deterministic work so the LLM can focus on semantic
wiki maintenance.

## State

State lives under `.mindsync/`:

- `config.json` - vault config and enabled adapters
- `state/pending-ingest.json` - queued raw files and image assets
- `state/source-hashes.json` - ingested source hashes for duplicate prevention
- `state/enrichment-queue.json` - missing-data tasks
- `state/last-embed.json` - qmd freshness timestamp
- `state/helper.log` - helper events from explicit embed commands
- `state/checkpoints/` - git diff checkpoints before durable writes
- `tools/` - project-local npm CLI dependencies

## Common Commands

```bash
python3 mindsync/scripts/mindsync.py ensure-tools --vault mindsync --tool qmd --tool summarize
python3 mindsync/scripts/mindsync.py tool-path --vault mindsync qmd
python3 mindsync/scripts/mindsync.py queue-scan --vault mindsync
python3 mindsync/scripts/mindsync.py pending --vault mindsync
python3 mindsync/scripts/mindsync.py mark-ingested --vault mindsync --path raw/example.md --page wiki/sources/example.md
python3 mindsync/scripts/mindsync.py lint --vault mindsync
python3 mindsync/scripts/mindsync.py queue-enrichment --vault mindsync --topic "Topic" --reason "Thin concept page"
python3 mindsync/scripts/mindsync.py fetch-enrichment --vault mindsync --limit 3
python3 mindsync/scripts/mindsync.py chart --vault mindsync --data data.csv --title "Chart title"
python3 mindsync/scripts/mindsync.py export-training --vault mindsync
python3 mindsync/scripts/mindsync.py checkpoint --vault mindsync
python3 mindsync/scripts/mindsync.py embed --vault mindsync
python3 mindsync/scripts/mindsync.py doctor --vault mindsync
```

## Action-First Boundary

Raw files are source records. They are processed only when the user asks an
agent to ingest them. The ingest workflow explicitly scans `raw/`, reads the
pending queue, compiles sources into `wiki/`, records source hashes, and refreshes
qmd after compiled pages change.

There are no file watchers, launchd jobs, cron jobs, or session hooks in the
default flow. An active agent session performs semantic compilation because
summarizing, linking, contradiction checks, and image captioning require model
judgment.
