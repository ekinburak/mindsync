---
name: mindsync-finetune
description: Export wiki pages as JSONL Q&A examples for future fine-tuning without training a model
trigger: /mindsync finetune
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# /mindsync finetune

Export synthetic training data from the compiled wiki. This workflow creates a
dataset only; it does not train or upload a model.

## Export

Run:

```bash
python3 scripts/mindsync.py export-training --vault . --output wiki/analyses/training-export.jsonl
```

Then append to `log.md`:

```markdown
## [YYYY-MM-DD] export | fine-tuning dataset
Output: wiki/analyses/training-export.jsonl
Mode: export only
```

## Rules

- Do not include raw source files directly.
- Prefer compiled wiki pages because they contain cleaned, linked knowledge.
- Flag the export as synthetic and derived from the wiki.
- Do not start training unless the user explicitly asks for a training workflow.
