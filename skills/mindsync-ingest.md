---
name: mindsync-ingest
description: Interactively ingest a new source into the LLM Wiki
trigger: /mindsync ingest
---

# /mindsync ingest

You are ingesting a new source into the wiki. Follow these steps exactly.

## Step 1: Session context

Read these files before doing anything else:
1. `_hot.md`
2. `index.md`
3. Last 10 entries of `log.md`

## Step 2: Identify the source

If a file path was passed as an argument, use it directly (go to Step 3A).

Otherwise ask: "What's the source?"
- A) Path already in raw/ — go to Step 3A
- B) URL (article or webpage) — go to Step 3B
- C) YouTube or podcast URL — go to Step 3B
- D) PDF file path — go to Step 3C
- E) Paste text — go to Step 3D
- F) Content already fetched this session (summarize or agent-browser output) — go to Step 3E

## Step 3: Fetch and save

**3A — File already in raw/:**
Read the file directly. Set SLUG = filename without extension. Set DATE = today's date.

**3B — URL:**
Run: `summarize <URL> > raw/<DATE>-<SLUG>.md`
Where SLUG is a kebab-case version of the article title. Then read the saved file.

**3C — PDF:**
Run: `summarize <PDF_PATH> > raw/<DATE>-<SLUG>.md`
Then read the saved file.

**3D — Paste text:**
Save the pasted content as `raw/<DATE>-freeform.md`. Then read it.

**3E — Session output (auto-filing):**
If during this session Claude already ran `summarize` or `agent-browser` and produced content that hasn't been saved yet, save it now:
```bash
cat > raw/<DATE>-<SLUG>.md << 'EOF'
<content>
EOF
```
Then read the saved file. This closes the loop on any content fetched during the session without an explicit save step.

**Auto-file trigger:** Any time Claude runs `summarize <URL>` or `agent-browser` and gets back substantial content (more than 200 words), offer immediately: "Want me to file this to raw/ and ingest it?" — don't wait for the user to think to ask. This is output auto-filing.

## Step 4: Detect source type and discuss

Detect the source type from the content:
- **Article / blog post** — has a byline, URL, publication date
- **Research paper** — has abstract, methodology, references section
- **Podcast / video transcript** — has speaker labels or timestamp markers
- **Journal entry** — first-person, dated, personal reflection
- **GitHub repo** — has README, code structure, technical documentation
- **Dataset / CSV** — tabular data with column headers and rows

Show the user: "Here are the key takeaways I see:" followed by a numbered list of 3-5 key points.

Then ask: "Anything to emphasize or skip before I write?"

Wait for the user's response before writing anything.

## Step 5: Write wiki pages

Use the source type detected in Step 4 to choose the right template:

**Article / blog post:**
- Summary: 2-3 sentence overview
- Key claims: bullet list of main points
- Notable quotes: 1-3 direct quotes
- Author's argument: what point is the author making overall?

**Research paper:**
- Summary: what was studied and what was found
- Methodology: how they studied it (1-2 sentences)
- Key findings: numbered list with effect sizes or stats where present
- Limitations: what the authors say the study can't conclude
- Notable quotes: 1-2 quotes from abstract or conclusion

**Podcast / video transcript:**
- Guest / host: who is speaking
- Summary: topic and main thread of conversation
- Key insights: bullet list of distinct ideas raised
- Memorable moments: notable exchanges or quotes
- Actionable takeaways: what to do or explore based on this

**Journal entry:**
- Date: when it was written
- Mood / tone: one word
- Key themes: what the entry is processing
- Insights: any conclusions or realizations reached
- Open questions: unresolved threads worth tracking

**GitHub repo:**
- What it does: one sentence
- Tech stack: languages, frameworks, dependencies
- Key components: main files or modules and their purpose
- How it's relevant: why this repo matters to the wiki domain
- Links: repo URL, any related papers or articles

**Dataset / CSV:**
- What it contains: rows represent X, columns are Y
- Source and date: where it came from, when collected
- Key statistics: row count, notable columns, value ranges
- Potential uses: what questions this data could answer
- Gaps: what's missing or unreliable

Write `wiki/sources/<DATE>-<SLUG>.md` with the chosen template plus:
- YAML frontmatter (title, type: source, tags, created, updated, sources array)
- Links to all entities and concepts touched using Obsidian double-bracket link syntax

For each entity and concept mentioned:
- If the page exists: open it, add or update content, update the `updated:` date, add source to `sources:` array
- If it does not exist: create it with full frontmatter and an initial section from this source

## Step 6: Update indexes

Update `index.md`:
- Add/update entry under Sources with a one-line summary
- Add/update entries for any new or updated entities and concepts

Append to `log.md`:
```
## [DATE] ingest | SOURCE_TITLE
Processed: wiki/sources/DATE-SLUG.md
Updated: list of touched pages
Key insight: one sentence
```

## Step 6b: Mark as ingested

After updating indexes, run:
```bash
rm -f raw/.pending-ingest
touch raw/.last-ingest
```

This clears the pending flag (so the hook stops firing) and updates the timestamp marker (so the launchd watcher knows what's already been processed).

## Step 7: Hot cache check

Ask: "Anything from this source worth adding to _hot.md? Here are my suggestions:" followed by any relevant suggestions.

Wait for user's response. Do not write to `_hot.md` directly — only suggest updates.
