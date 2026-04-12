#!/bin/bash
# generate-graph.sh — Parse [[wiki/links]] across all wiki pages and output graph.json
# Usage: bash scripts/generate-graph.sh [wiki-path]
# Output: graph.json in the vault root — import into Obsidian, D3.js, or Gephi
#
# Format: { "nodes": [...], "edges": [...] }
# Each node: { "id": "wiki/path/slug", "type": "source|entity|concept|analysis", "title": "..." }
# Each edge: { "source": "wiki/path/slug", "target": "wiki/path/slug" }

set -e

WIKI_PATH="${1:-$(pwd)}"
WIKI_PATH="${WIKI_PATH/#\~/$HOME}"
WIKI_DIR="$WIKI_PATH/wiki"
OUTPUT="$WIKI_PATH/graph.json"

if [ ! -d "$WIKI_DIR" ]; then
  echo "Error: $WIKI_DIR not found. Run from your vault root or pass the vault path."
  exit 1
fi

echo "Scanning wiki pages..."

# Collect all wiki pages
PAGES=$(find "$WIKI_DIR" -name "*.md" | sort)
PAGE_COUNT=$(echo "$PAGES" | wc -l | tr -d ' ')
echo "Found $PAGE_COUNT pages"

# Build nodes and edges using python3
python3 << PYEOF
import os, re, json

wiki_dir = "$WIKI_DIR"
output = "$OUTPUT"

nodes = []
edges = []
node_ids = set()

# Walk all wiki pages
for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(root, fname)
        rel = os.path.relpath(fpath, os.path.dirname(wiki_dir))  # e.g. wiki/concepts/foo.md
        node_id = rel.replace('.md', '')

        # Detect type from path
        if '/sources/' in rel:
            ntype = 'source'
        elif '/entities/' in rel:
            ntype = 'entity'
        elif '/concepts/' in rel:
            ntype = 'concept'
        elif '/analyses/' in rel:
            ntype = 'analysis'
        else:
            ntype = 'other'

        # Extract title from frontmatter
        title = node_id.split('/')[-1]
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip().strip('"\'')

        nodes.append({"id": node_id, "type": ntype, "title": title})
        node_ids.add(node_id)

        # Extract all [[wiki/...]] links
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        for link in links:
            # Normalize: strip leading wiki/ if present, strip .md
            target = link.strip().replace('.md', '')
            if target.startswith('raw/') or target.startswith('./raw/'):
                continue
            if not target.startswith('wiki/'):
                target = 'wiki/' + target
            if target != node_id:
                edges.append({"source": node_id, "target": target})

# Deduplicate edges
unique_edges = list({(e['source'], e['target']): e for e in edges}.values())

# Filter edges where target exists as a node (skip broken links)
valid_edges = [e for e in unique_edges if e['target'] in node_ids]
broken = len(unique_edges) - len(valid_edges)

graph = {"nodes": nodes, "edges": valid_edges}
with open(output, 'w') as f:
    json.dump(graph, f, indent=2)

print(f"Nodes: {len(nodes)}")
print(f"Edges: {len(valid_edges)}")
if broken > 0:
    print(f"Skipped {broken} broken links (target page doesn't exist)")
print(f"Output: {output}")
PYEOF

echo ""
echo "graph.json written to $OUTPUT"
echo "Import options:"
echo "  Obsidian: place graph.json in vault root — visible in graph view"
echo "  D3.js:    load graph.json directly"
echo "  Gephi:    File > Import > JSON Graph File"
