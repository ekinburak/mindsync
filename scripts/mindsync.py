#!/usr/bin/env python3
"""Deterministic helper commands for mindsync vaults.

The LLM remains responsible for semantic compilation. This script owns the
repeatable work: scaffolding, queues, source hashes, lint checks, chart assets,
training export, and state files.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATE_DIR = REPO_ROOT / "templates"
if not TEMPLATE_DIR.exists():
    TEMPLATE_DIR = SCRIPT_DIR / "templates"
STATE_VERSION = 1
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tiff", ".bmp", ".heic"}
REQUIRED_FRONTMATTER = {"title", "type", "tags", "created", "updated", "sources"}
TOOL_SPECS = {
    "qmd": {"package": "@tobilu/qmd", "bin": "qmd"},
    "summarize": {"package": "@steipete/summarize", "bin": "summarize"},
    "agent-browser": {"package": "agent-browser", "bin": "agent-browser"},
}


def today() -> str:
    return dt.date.today().isoformat()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def vault_root(path: str | None) -> Path:
    root = Path(path or ".").expanduser().resolve()
    return root


def rel_to_vault(path: Path, vault: Path) -> str:
    return path.resolve().relative_to(vault.resolve()).as_posix()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def render_template(name: str, values: dict[str, str]) -> str:
    path = TEMPLATE_DIR / name
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def state_paths(vault: Path) -> dict[str, Path]:
    state = vault / ".mindsync" / "state"
    return {
        "config": vault / ".mindsync" / "config.json",
        "state": state,
        "pending": state / "pending-ingest.json",
        "hashes": state / "source-hashes.json",
        "enrichment": state / "enrichment-queue.json",
        "last_ingest": state / "last-ingest.json",
        "last_embed": state / "last-embed.json",
        "checkpoints": state / "checkpoints",
        "tools": vault / ".mindsync" / "tools",
    }


def npm_bin_dir(vault: Path) -> Path:
    return state_paths(vault)["tools"] / "node_modules" / ".bin"


def resolve_tool(vault: Path, tool: str) -> str | None:
    spec = TOOL_SPECS[tool]
    local = npm_bin_dir(vault) / spec["bin"]
    if local.exists():
        return str(local)
    return shutil.which(spec["bin"])


def package_json(vault: Path) -> dict[str, Any]:
    return {
        "private": True,
        "name": f"mindsync-tools-{slugify(vault.name)}",
        "version": "0.0.0",
        "description": "Project-local CLI dependencies for a mindsync vault.",
        "dependencies": {},
    }


def ensure_state(vault: Path) -> None:
    paths = state_paths(vault)
    paths["state"].mkdir(parents=True, exist_ok=True)
    paths["checkpoints"].mkdir(parents=True, exist_ok=True)
    paths["tools"].mkdir(parents=True, exist_ok=True)
    if not paths["pending"].exists():
        write_json(paths["pending"], {"version": STATE_VERSION, "items": []})
    if not paths["hashes"].exists():
        write_json(paths["hashes"], {"version": STATE_VERSION, "sources": {}})
    if not paths["enrichment"].exists():
        write_json(paths["enrichment"], {"version": STATE_VERSION, "items": []})


def command_ensure_tools(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    tools = args.tool or ["qmd", "summarize"]
    unknown = sorted(set(tools) - set(TOOL_SPECS))
    if unknown:
        print(f"Unknown tool(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    npm = shutil.which("npm")
    if not npm:
        print("npm is required to install local mindsync tools.", file=sys.stderr)
        return 2

    tools_dir = state_paths(vault)["tools"]
    pkg_path = tools_dir / "package.json"
    pkg = read_json(pkg_path, package_json(vault))
    pkg.setdefault("dependencies", {})
    changed = False
    for tool in tools:
        spec = TOOL_SPECS[tool]
        if spec["package"] not in pkg["dependencies"]:
            pkg["dependencies"][spec["package"]] = "latest"
            changed = True
    if changed or not pkg_path.exists():
        write_json(pkg_path, pkg)

    packages = [TOOL_SPECS[tool]["package"] for tool in tools if not resolve_tool(vault, tool) or args.force]
    if packages:
        cmd = [npm, "install", "--prefix", str(tools_dir), *packages]
        print(f"Installing local tool dependencies: {' '.join(packages)}")
        if args.dry_run:
            print(" ".join(cmd))
            return 0
        else:
            subprocess.run(cmd, check=True)

    for tool in tools:
        path = resolve_tool(vault, tool)
        if path:
            print(f"{tool}: {path}")
        else:
            print(f"{tool}: not found after install", file=sys.stderr)
            return 1
    return 0


def command_tool_path(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    if args.tool not in TOOL_SPECS:
        print(f"Unknown tool: {args.tool}", file=sys.stderr)
        return 2
    path = resolve_tool(vault, args.tool)
    if not path:
        print(f"{args.tool} not found. Run: python3 scripts/mindsync.py ensure-tools --vault . --tool {args.tool}", file=sys.stderr)
        return 1
    print(path)
    return 0


def command_init(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    wiki_name = args.wiki_name or vault.name
    values = {
        "WIKI_NAME": wiki_name,
        "NAME": args.name,
        "DOMAIN": args.domain,
        "DOMAIN_DESCRIPTION": args.domain,
        "PRIORITY": args.priority,
        "VAULT_PATH": str(vault),
        "DATE": today(),
    }

    for folder in [
        vault / "raw" / "assets",
        vault / "wiki" / "entities",
        vault / "wiki" / "concepts",
        vault / "wiki" / "sources",
        vault / "wiki" / "analyses" / "assets",
        vault / "docs" / "superpowers" / "specs",
        vault / "scripts",
        vault / ".mindsync" / "state",
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    files = {
        "AGENTS.md": render_template("AGENTS.md.template", values),
        "CLAUDE.md": render_template("CLAUDE.md.template", values),
        "_hot.md": render_template("_hot.md.template", values),
        "index.md": render_template("index.md.template", values),
        "log.md": render_template("log.md.template", values),
    }
    for rel, text in files.items():
        path = vault / rel
        if args.force or not path.exists():
            path.write_text(text, encoding="utf-8")

    agents = args.agent or ["claude", "codex", "openclaw"]
    config = {
        "version": STATE_VERSION,
        "vault": str(vault),
        "wiki_name": wiki_name,
        "domain": args.domain,
        "automation": args.automation,
        "adapters": sorted(set(agents)),
        "qmd_collection": wiki_name,
        "raw_policy": "append-only",
        "git_checkpoint": True,
        "created_at": now_iso(),
    }
    write_json(state_paths(vault)["config"], config)
    ensure_state(vault)

    # Keep a legacy marker so older watcher scripts do not fail.
    legacy_marker = vault / "raw" / ".last-ingest"
    if not legacy_marker.exists():
        legacy_marker.touch()

    if not args.no_copy_scripts:
        for script in (REPO_ROOT / "scripts").iterdir():
            should_copy = (
                script.is_file()
                and (
                    script.name.startswith("mindsync")
                    or script.name.startswith("hook-")
                    or script.name
                    in {
                "on-raw-change.sh",
                "schedule-embed.sh",
                "generate-graph.sh",
                    }
                )
            )
            if should_copy:
                target = vault / "scripts" / script.name
                shutil.copy2(script, target)
                target.chmod(target.stat().st_mode | 0o111)

    print(f"Initialized mindsync vault: {vault}")
    print(f"Automation: {args.automation}")
    print(f"Adapters: {', '.join(sorted(set(agents)))}")
    return 0


def raw_candidates(vault: Path) -> list[tuple[Path, str]]:
    raw = vault / "raw"
    results: list[tuple[Path, str]] = []
    if not raw.exists():
        return results
    for path in sorted(raw.iterdir()):
        if path.is_file() and not path.name.startswith("."):
            results.append((path, "source"))
    assets = raw / "assets"
    if assets.exists():
        for path in sorted(assets.rglob("*")):
            if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in IMAGE_EXTS:
                results.append((path, "image"))
    return results


def load_pending(vault: Path) -> dict[str, Any]:
    ensure_state(vault)
    pending = read_json(state_paths(vault)["pending"], {"version": STATE_VERSION, "items": []})
    pending.setdefault("version", STATE_VERSION)
    pending.setdefault("items", [])
    return pending


def save_pending(vault: Path, pending: dict[str, Any]) -> None:
    write_json(state_paths(vault)["pending"], pending)


def command_queue_scan(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    hashes = read_json(state_paths(vault)["hashes"], {"version": STATE_VERSION, "sources": {}})
    known = hashes.setdefault("sources", {})
    pending = load_pending(vault)
    existing_hashes = {item.get("sha256") for item in pending["items"] if item.get("status") == "pending"}
    added = 0

    for path, kind in raw_candidates(vault):
        digest = sha256_file(path)
        if digest in known or digest in existing_hashes:
            continue
        item = {
            "id": digest[:16],
            "path": rel_to_vault(path, vault),
            "kind": kind,
            "sha256": digest,
            "status": "pending",
            "created_at": now_iso(),
        }
        pending["items"].append(item)
        existing_hashes.add(digest)
        added += 1

    save_pending(vault, pending)
    pending_count = sum(1 for item in pending["items"] if item.get("status") == "pending")
    if args.json:
        print(json.dumps({"added": added, "pending": pending_count, "items": pending["items"]}, indent=2))
    else:
        print(f"Queued {added} new source(s); {pending_count} pending.")
        for item in pending["items"]:
            if item.get("status") == "pending":
                print(f"- {item['path']} ({item['kind']})")
    return 0


def command_pending(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    pending = load_pending(vault)
    items = [item for item in pending["items"] if item.get("status") == "pending"]
    if args.json:
        print(json.dumps({"items": items}, indent=2))
    else:
        if not items:
            print("No pending sources.")
        for item in items:
            print(f"{item['id']} {item['kind']} {item['path']}")
    return 0


def command_mark_ingested(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    target = (vault / args.path).resolve()
    if not target.exists():
        print(f"Missing source: {target}", file=sys.stderr)
        return 1
    digest = sha256_file(target)
    hashes = read_json(state_paths(vault)["hashes"], {"version": STATE_VERSION, "sources": {}})
    hashes.setdefault("sources", {})[digest] = {
        "path": rel_to_vault(target, vault),
        "ingested_at": now_iso(),
        "wiki_pages": args.page or [],
    }
    write_json(state_paths(vault)["hashes"], hashes)

    pending = load_pending(vault)
    for item in pending["items"]:
        if item.get("sha256") == digest or item.get("path") == rel_to_vault(target, vault):
            item["status"] = "ingested"
            item["ingested_at"] = now_iso()
            if args.page:
                item["wiki_pages"] = args.page
    save_pending(vault, pending)
    write_json(state_paths(vault)["last_ingest"], {"at": now_iso(), "path": rel_to_vault(target, vault)})
    (vault / "raw" / ".last-ingest").touch()
    print(f"Marked ingested: {rel_to_vault(target, vault)}")
    return 0


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    block = text[4:end].strip()
    body = text[end + 4 :]
    data: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, body


def wiki_pages(vault: Path) -> list[Path]:
    wiki = vault / "wiki"
    if not wiki.exists():
        return []
    return sorted(path for path in wiki.rglob("*.md") if path.is_file())


def normalize_link(link: str) -> str | None:
    target = link.split("|", 1)[0].split("#", 1)[0].strip()
    target = target.removesuffix(".md")
    if target.startswith("raw/") or target.startswith("./raw/"):
        return None
    if not target.startswith("wiki/"):
        target = f"wiki/{target}"
    return target


def page_id(path: Path, vault: Path) -> str:
    return rel_to_vault(path, vault).removesuffix(".md")


def command_lint(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    pages = wiki_pages(vault)
    ids = {page_id(path, vault): path for path in pages}
    incoming: dict[str, set[str]] = {pid: set() for pid in ids}
    frontmatter_gaps = []
    missing_pages = []
    links_by_source: dict[str, list[str]] = {}

    for path in pages:
        pid = page_id(path, vault)
        text = path.read_text(encoding="utf-8", errors="ignore")
        frontmatter, _ = parse_frontmatter(text)
        missing_fields = sorted(REQUIRED_FRONTMATTER - set(frontmatter))
        if missing_fields:
            frontmatter_gaps.append({"path": pid, "missing": missing_fields})
        links = [link for link in (normalize_link(link) for link in re.findall(r"\[\[([^\]]+)\]\]", text)) if link]
        links_by_source[pid] = links
        for link in links:
            if link in incoming:
                incoming[link].add(pid)
            else:
                missing_pages.append({"from": pid, "target": link})

    orphans = [
        {"path": pid}
        for pid, sources in sorted(incoming.items())
        if not sources and "/sources/" not in pid
    ]

    index_text = (vault / "index.md").read_text(encoding="utf-8", errors="ignore") if (vault / "index.md").exists() else ""
    index_drift = [
        {"path": pid}
        for pid in sorted(ids)
        if pid not in index_text and f"[[{pid}]]" not in index_text
    ]

    raw_hashes: dict[str, list[str]] = {}
    for path, _kind in raw_candidates(vault):
        raw_hashes.setdefault(sha256_file(path), []).append(rel_to_vault(path, vault))
    duplicates = [
        {"sha256": digest, "paths": paths}
        for digest, paths in sorted(raw_hashes.items())
        if len(paths) > 1
    ]

    last_embed = read_json(state_paths(vault)["last_embed"], {})
    newest_wiki = max((path.stat().st_mtime for path in pages), default=0)
    embed_at = last_embed.get("mtime", 0)
    qmd_stale = bool(newest_wiki and embed_at and newest_wiki > embed_at)
    qmd_unknown = not bool(embed_at)

    report = {
        "frontmatter_gaps": frontmatter_gaps,
        "missing_pages": missing_pages,
        "orphans": orphans,
        "index_drift": index_drift,
        "duplicate_raw_sources": duplicates,
        "qmd": {"stale": qmd_stale, "unknown": qmd_unknown},
        "counts": {
            "pages": len(pages),
            "frontmatter_gaps": len(frontmatter_gaps),
            "missing_pages": len(missing_pages),
            "orphans": len(orphans),
            "index_drift": len(index_drift),
            "duplicate_raw_sources": len(duplicates),
        },
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("# mindsync deterministic lint")
        for key in ["frontmatter_gaps", "missing_pages", "orphans", "index_drift", "duplicate_raw_sources"]:
            print(f"\n## {key.replace('_', ' ').title()}")
            items = report[key]
            if not items:
                print("None.")
            else:
                for item in items:
                    print(f"- {json.dumps(item, sort_keys=True)}")
        qmd = report["qmd"]
        print("\n## Qmd")
        print(f"stale={qmd['stale']} unknown={qmd['unknown']}")
    return 0


def command_queue_enrichment(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    queue = read_json(state_paths(vault)["enrichment"], {"version": STATE_VERSION, "items": []})
    item = {
        "id": hashlib.sha256(f"{args.topic}|{args.reason}|{now_iso()}".encode()).hexdigest()[:16],
        "topic": args.topic,
        "reason": args.reason,
        "query": args.query or f"{args.topic} overview",
        "url": args.url,
        "status": "pending",
        "created_at": now_iso(),
    }
    queue.setdefault("items", []).append(item)
    write_json(state_paths(vault)["enrichment"], queue)
    print(f"Queued enrichment: {item['id']} {args.topic}")
    return 0


def command_fetch_enrichment(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    queue = read_json(state_paths(vault)["enrichment"], {"version": STATE_VERSION, "items": []})
    summarize = shutil.which("summarize")
    fetched = 0
    for item in queue.get("items", []):
        if fetched >= args.limit:
            break
        if item.get("status") != "pending":
            continue
        url = item.get("url")
        if not url:
            item["status"] = "needs-url"
            item["updated_at"] = now_iso()
            continue
        summarize = resolve_tool(vault, "summarize")
        if not summarize:
            item["status"] = "blocked"
            item["error"] = "summarize not found; run ensure-tools"
            item["updated_at"] = now_iso()
            continue
        slug = slugify(item["topic"])
        out = vault / "raw" / f"{today()}-{slug}-supplement.md"
        if out.exists():
            out = vault / "raw" / f"{today()}-{slug}-{item['id']}-supplement.md"
        with out.open("w", encoding="utf-8") as f:
            subprocess.run([summarize, url], check=True, stdout=f)
        item["status"] = "fetched"
        item["raw_path"] = rel_to_vault(out, vault)
        item["updated_at"] = now_iso()
        fetched += 1
    write_json(state_paths(vault)["enrichment"], queue)
    if fetched:
        command_queue_scan(argparse.Namespace(vault=str(vault), json=False))
    print(f"Fetched {fetched} enrichment source(s).")
    return 0


def load_chart_rows(path: Path) -> tuple[list[str], list[tuple[str, float]]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows = [(str(k), float(v)) for k, v in data.items()]
        else:
            rows = [(str(item["label"]), float(item["value"])) for item in data]
        return ["label", "value"], rows
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) < 2:
            raise ValueError("CSV chart data needs at least two columns")
        label_col, value_col = reader.fieldnames[0], reader.fieldnames[1]
        rows = [(row[label_col], float(row[value_col])) for row in reader]
        return [label_col, value_col], rows


def command_chart(args: argparse.Namespace) -> int:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on environment
        print(f"matplotlib is required for chart output: {exc}", file=sys.stderr)
        return 2

    vault = vault_root(args.vault)
    data_path = Path(args.data).expanduser().resolve()
    _headers, rows = load_chart_rows(data_path)
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    slug = slugify(args.slug or args.title)
    assets = vault / "wiki" / "analyses" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    out = assets / f"{today()}-{slug}.png"

    fig, ax = plt.subplots(figsize=(9, 5))
    if args.kind == "line":
        ax.plot(labels, values, marker="o")
    else:
        ax.bar(labels, values)
    ax.set_title(args.title)
    ax.set_ylabel(args.ylabel or "Value")
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)

    rel = rel_to_vault(out, vault)
    print(f"![[{rel}]]")
    return 0


def stripped_markdown(text: str) -> str:
    _frontmatter, body = parse_frontmatter(text)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"!\[\[[^\]]+\]\]", "", body)
    body = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", body)
    body = re.sub(r"^#+\s*", "", body, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def command_export_training(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = vault / output
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as f:
        for path in wiki_pages(vault):
            text = path.read_text(encoding="utf-8", errors="ignore")
            frontmatter, _body = parse_frontmatter(text)
            title = frontmatter.get("title") or path.stem.replace("-", " ").title()
            content = stripped_markdown(text)
            if not content:
                continue
            answer = content[: args.max_chars].strip()
            pairs = [
                {
                    "messages": [
                        {"role": "system", "content": "Answer from the mindsync wiki."},
                        {"role": "user", "content": f"Summarize {title}."},
                        {"role": "assistant", "content": answer},
                    ],
                    "source": rel_to_vault(path, vault),
                },
                {
                    "messages": [
                        {"role": "system", "content": "Answer from the mindsync wiki."},
                        {"role": "user", "content": f"What are the key points about {title}?"},
                        {"role": "assistant", "content": answer},
                    ],
                    "source": rel_to_vault(path, vault),
                },
            ]
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                count += 1
    print(f"Wrote {count} training examples to {output}")
    return 0


def command_checkpoint(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    if not (vault / ".git").exists():
        print("No git repository in vault; checkpoint skipped.")
        return 0
    out_dir = state_paths(vault)["checkpoints"]
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    patch = out_dir / f"{stamp}.patch"
    untracked = out_dir / f"{stamp}-untracked.txt"
    diff = subprocess.run(["git", "-C", str(vault), "diff", "--binary"], text=True, capture_output=True)
    patch.write_text(diff.stdout, encoding="utf-8")
    files = subprocess.run(["git", "-C", str(vault), "ls-files", "--others", "--exclude-standard"], text=True, capture_output=True)
    untracked.write_text(files.stdout, encoding="utf-8")
    print(f"Checkpoint written: {rel_to_vault(patch, vault)}")
    return 0


def command_mark_embed(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    write_json(state_paths(vault)["last_embed"], {"at": now_iso(), "mtime": dt.datetime.now().timestamp()})
    print("Recorded qmd embed timestamp.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mindsync")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ensure-tools")
    p.add_argument("--vault", default=".")
    p.add_argument("--tool", action="append", choices=sorted(TOOL_SPECS))
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=command_ensure_tools)

    p = sub.add_parser("tool-path")
    p.add_argument("--vault", default=".")
    p.add_argument("tool", choices=sorted(TOOL_SPECS))
    p.set_defaults(func=command_tool_path)

    p = sub.add_parser("init")
    p.add_argument("--vault", required=True)
    p.add_argument("--name", default="Human")
    p.add_argument("--domain", default="personal knowledge base")
    p.add_argument("--priority", default="maintain an accurate, useful wiki")
    p.add_argument("--wiki-name")
    p.add_argument("--automation", choices=["zero-touch", "queued", "manual"], default="zero-touch")
    p.add_argument("--agent", action="append", choices=["claude", "codex", "openclaw"])
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-copy-scripts", action="store_true")
    p.set_defaults(func=command_init)

    p = sub.add_parser("queue-scan")
    p.add_argument("--vault", default=".")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_queue_scan)

    p = sub.add_parser("pending")
    p.add_argument("--vault", default=".")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_pending)

    p = sub.add_parser("mark-ingested")
    p.add_argument("--vault", default=".")
    p.add_argument("--path", required=True)
    p.add_argument("--page", action="append")
    p.set_defaults(func=command_mark_ingested)

    p = sub.add_parser("lint")
    p.add_argument("--vault", default=".")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_lint)

    p = sub.add_parser("queue-enrichment")
    p.add_argument("--vault", default=".")
    p.add_argument("--topic", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--query")
    p.add_argument("--url")
    p.set_defaults(func=command_queue_enrichment)

    p = sub.add_parser("fetch-enrichment")
    p.add_argument("--vault", default=".")
    p.add_argument("--limit", type=int, default=3)
    p.set_defaults(func=command_fetch_enrichment)

    p = sub.add_parser("chart")
    p.add_argument("--vault", default=".")
    p.add_argument("--data", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--slug")
    p.add_argument("--kind", choices=["bar", "line"], default="bar")
    p.add_argument("--ylabel")
    p.set_defaults(func=command_chart)

    p = sub.add_parser("export-training")
    p.add_argument("--vault", default=".")
    p.add_argument("--output", default="wiki/analyses/training-export.jsonl")
    p.add_argument("--max-chars", type=int, default=1800)
    p.set_defaults(func=command_export_training)

    p = sub.add_parser("checkpoint")
    p.add_argument("--vault", default=".")
    p.set_defaults(func=command_checkpoint)

    p = sub.add_parser("mark-embed")
    p.add_argument("--vault", default=".")
    p.set_defaults(func=command_mark_embed)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
