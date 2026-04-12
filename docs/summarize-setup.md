# summarize Setup

summarize converts URLs, PDFs, YouTube videos, and podcasts into markdown summaries — ready to drop into your wiki's `raw/` folder.

## Install

Project-local install:

```bash
python3 scripts/mindsync.py ensure-tools --vault . --tool summarize
SUMMARIZE=$(python3 scripts/mindsync.py tool-path --vault . summarize)
```

Global install:

```bash
npm install -g @steipete/summarize
```

## Usage

```bash
# Article or webpage
"$SUMMARIZE" https://example.com/article > raw/2026-04-09-article-title.md

# YouTube video
"$SUMMARIZE" https://youtube.com/watch?v=xxx > raw/2026-04-09-video-title.md

# PDF
"$SUMMARIZE" /path/to/paper.pdf > raw/2026-04-09-paper-title.md

# Podcast episode
"$SUMMARIZE" https://podcast-url > raw/2026-04-09-episode-title.md
```

After saving to `raw/`, run `/mindsync ingest` to process it into the wiki.

## Auto-ingest combo

```bash
"$SUMMARIZE" https://example.com/article > raw/$(date +%Y-%m-%d)-article.md
# Then tell your agent: "ingest this" — or let the file watcher queue it
```
