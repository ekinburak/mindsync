# summarize Setup

summarize converts URLs, PDFs, YouTube videos, and podcasts into markdown summaries — ready to drop into your wiki's `raw/` folder.

## Install

```bash
npm install -g @steipete/summarize
```

## Usage

```bash
# Article or webpage
summarize https://example.com/article > raw/2026-04-09-article-title.md

# YouTube video
summarize https://youtube.com/watch?v=xxx > raw/2026-04-09-video-title.md

# PDF
summarize /path/to/paper.pdf > raw/2026-04-09-paper-title.md

# Podcast episode
summarize https://podcast-url > raw/2026-04-09-episode-title.md
```

After saving to `raw/`, run `/llm-wiki ingest` to process it into the wiki.

## Auto-ingest combo

```bash
summarize https://example.com/article > raw/$(date +%Y-%m-%d)-article.md
# Then tell Claude: "ingest this" — or let the file watcher handle it
```
