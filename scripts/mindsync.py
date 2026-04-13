#!/usr/bin/env python3
"""Deterministic helper commands for mindsync vaults.

The LLM remains responsible for semantic compilation. This script owns the
repeatable work: scaffolding, queues, source hashes, lint checks, chart assets,
training export, and state files.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATE_DIR = REPO_ROOT / "templates"
if not TEMPLATE_DIR.exists():
    TEMPLATE_DIR = SCRIPT_DIR / "templates"
STATE_VERSION = 1
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tiff", ".bmp", ".heic"}
RAW_TEMP_SUFFIXES = {".crdownload", ".download", ".tmp", ".part"}
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
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@contextlib.contextmanager
def file_lock(vault: Path, name: str, timeout: float = 30.0):
    ensure_state(vault)
    lock_path = state_paths(vault)["state"] / f"{name}.lock"
    deadline = time.monotonic() + timeout
    fd: int | None = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {now_iso()}\n".encode("utf-8"))
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
                if age > timeout * 2:
                    lock_path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for lock: {lock_path}")
            time.sleep(0.1)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def automation_log_path(vault: Path) -> Path:
    return state_paths(vault)["state"] / "automation.log"


def log_automation(vault: Path, level: str, message: str) -> None:
    path = automation_log_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{now_iso()} {level.upper()} vault={vault} {message}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


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


def is_stable_raw_file(path: Path, min_age_seconds: int) -> bool:
    if path.name.startswith(".") or path.suffix.lower() in RAW_TEMP_SUFFIXES:
        return False
    if min_age_seconds <= 0:
        return True
    try:
        return time.time() - path.stat().st_mtime >= min_age_seconds
    except FileNotFoundError:
        return False


def raw_candidates(vault: Path, min_age_seconds: int = 0) -> list[tuple[Path, str]]:
    raw = vault / "raw"
    results: list[tuple[Path, str]] = []
    if not raw.exists():
        return results
    for path in sorted(raw.iterdir()):
        if path.is_file() and is_stable_raw_file(path, min_age_seconds):
            results.append((path, "source"))
    assets = raw / "assets"
    if assets.exists():
        for path in sorted(assets.rglob("*")):
            if path.is_file() and is_stable_raw_file(path, min_age_seconds) and path.suffix.lower() in IMAGE_EXTS:
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


def repair_pending(vault: Path, pending: dict[str, Any], known_hashes: dict[str, Any]) -> dict[str, int]:
    stats = {"missing": 0, "ingested": 0, "duplicate": 0}
    seen_pending: set[str] = set()
    for item in pending.get("items", []):
        if item.get("status") != "pending":
            continue
        digest = item.get("sha256")
        if digest and digest in known_hashes:
            item["status"] = "ingested"
            item["repaired_at"] = now_iso()
            stats["ingested"] += 1
            continue
        if digest and digest in seen_pending:
            item["status"] = "duplicate"
            item["repaired_at"] = now_iso()
            stats["duplicate"] += 1
            continue
        if digest:
            seen_pending.add(digest)
        path_value = item.get("path")
        if path_value and not (vault / path_value).exists():
            item["status"] = "missing"
            item["repaired_at"] = now_iso()
            stats["missing"] += 1
    return stats


def command_queue_scan(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    with file_lock(vault, "queue"):
        hashes = read_json(state_paths(vault)["hashes"], {"version": STATE_VERSION, "sources": {}})
        known = hashes.setdefault("sources", {})
        pending = load_pending(vault)
        repair_stats = repair_pending(vault, pending, known)
        existing_hashes = {item.get("sha256") for item in pending["items"] if item.get("status") == "pending"}
        added = 0

        for path, kind in raw_candidates(vault, args.min_age_seconds):
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
        print(json.dumps({"added": added, "pending": pending_count, "repaired": repair_stats, "items": pending["items"]}, indent=2))
    else:
        repaired = sum(repair_stats.values())
        suffix = f"; repaired {repaired}" if repaired else ""
        print(f"Queued {added} new source(s); {pending_count} pending{suffix}.")
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
    with file_lock(vault, "queue"):
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


def parse_iso_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    value = value.strip().strip("\"'")
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def age_days_from_mtime(path: Path) -> int:
    modified = dt.datetime.fromtimestamp(path.stat().st_mtime).date()
    return (dt.date.today() - modified).days


def stale_pages(vault: Path, pages: list[Path], stale_days: int) -> list[dict[str, Any]]:
    stale = []
    today_date = dt.date.today()
    for path in pages:
        text = path.read_text(encoding="utf-8", errors="ignore")
        frontmatter, _ = parse_frontmatter(text)
        updated = parse_iso_date(frontmatter.get("updated"))
        if updated:
            age = (today_date - updated).days
            source = "frontmatter"
            updated_value = updated.isoformat()
        else:
            age = age_days_from_mtime(path)
            source = "mtime"
            updated_value = dt.datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        if age > stale_days:
            stale.append(
                {
                    "path": page_id(path, vault),
                    "age_days": age,
                    "updated": updated_value,
                    "source": source,
                }
            )
    return stale


def qmd_report(vault: Path, pages: list[Path]) -> dict[str, Any]:
    last_embed = read_json(state_paths(vault)["last_embed"], {})
    newest_wiki = max((path.stat().st_mtime for path in pages), default=0)
    embed_at = last_embed.get("mtime", 0)
    stale = bool(newest_wiki and embed_at and newest_wiki > embed_at)
    unknown = not bool(embed_at)
    return {
        "stale": stale,
        "unknown": unknown,
        "last_embed_at": last_embed.get("at"),
        "last_embed_mtime": embed_at or None,
        "newest_wiki_mtime": newest_wiki or None,
    }


def hot_report(vault: Path) -> dict[str, Any]:
    path = vault / "_hot.md"
    if not path.exists():
        return {"exists": False, "word_count": 0, "too_long": False}
    text = path.read_text(encoding="utf-8", errors="ignore")
    words = re.findall(r"\S+", text)
    return {"exists": True, "word_count": len(words), "too_long": len(words) > 500}


def pending_lint(vault: Path) -> dict[str, list[dict[str, Any]]]:
    pending = read_json(state_paths(vault)["pending"], {"version": STATE_VERSION, "items": []})
    now = dt.datetime.now(dt.timezone.utc)
    old = []
    missing = []
    for item in pending.get("items", []):
        if item.get("status") != "pending":
            continue
        path_value = item.get("path")
        if path_value and not (vault / path_value).exists():
            missing.append({"id": item.get("id"), "path": path_value})
        created = item.get("created_at")
        try:
            created_dt = dt.datetime.fromisoformat(created) if created else None
        except ValueError:
            created_dt = None
        if created_dt:
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=dt.timezone.utc)
            age = (now - created_dt).days
            if age > 7:
                old.append({"id": item.get("id"), "path": path_value, "age_days": age})

    enrichment = read_json(state_paths(vault)["enrichment"], {"version": STATE_VERSION, "items": []})
    blocked_enrichment = [
        {"id": item.get("id"), "topic": item.get("topic"), "status": item.get("status"), "error": item.get("error")}
        for item in enrichment.get("items", [])
        if item.get("status") in {"blocked", "needs-url"}
    ]
    fetched_not_ingested = []
    hashes = read_json(state_paths(vault)["hashes"], {"version": STATE_VERSION, "sources": {}}).get("sources", {})
    ingested_paths = {entry.get("path") for entry in hashes.values() if isinstance(entry, dict)}
    for item in enrichment.get("items", []):
        raw_path = item.get("raw_path")
        if item.get("status") == "fetched" and raw_path and raw_path not in ingested_paths:
            fetched_not_ingested.append({"id": item.get("id"), "topic": item.get("topic"), "raw_path": raw_path})

    return {
        "old_pending": old,
        "missing_pending": missing,
        "blocked_enrichment": blocked_enrichment,
        "fetched_enrichment_not_ingested": fetched_not_ingested,
    }


def source_consistency(vault: Path, source_ids: list[str], index_text: str, log_text: str) -> dict[str, list[dict[str, Any]]]:
    source_index_gaps = [{"path": pid} for pid in source_ids if pid not in index_text and f"[[{pid}]]" not in index_text]
    source_log_gaps = [{"path": pid} for pid in source_ids if pid not in log_text and f"[[{pid}]]" not in log_text]
    hashes = read_json(state_paths(vault)["hashes"], {"version": STATE_VERSION, "sources": {}}).get("sources", {})
    missing_pages = []
    for digest, entry in hashes.items():
        if not isinstance(entry, dict):
            continue
        for page in entry.get("wiki_pages", []) or []:
            target = page.removesuffix(".md")
            if not (vault / f"{target}.md").exists():
                missing_pages.append({"sha256": digest, "raw_path": entry.get("path"), "wiki_page": page})
    return {
        "source_index_gaps": source_index_gaps,
        "source_log_gaps": source_log_gaps,
        "ingested_missing_pages": missing_pages,
    }


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
    log_text = (vault / "log.md").read_text(encoding="utf-8", errors="ignore") if (vault / "log.md").exists() else ""
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

    source_ids = [pid for pid in sorted(ids) if "/sources/" in pid]
    consistency = source_consistency(vault, source_ids, index_text, log_text)
    pending_report = pending_lint(vault)
    stale = stale_pages(vault, pages, args.stale_days)
    hot = hot_report(vault)
    qmd = qmd_report(vault, pages)

    report = {
        "frontmatter_gaps": frontmatter_gaps,
        "missing_pages": missing_pages,
        "orphans": orphans,
        "index_drift": index_drift,
        "duplicate_raw_sources": duplicates,
        "stale_pages": stale,
        "_hot": hot,
        "source_index_gaps": consistency["source_index_gaps"],
        "source_log_gaps": consistency["source_log_gaps"],
        "ingested_missing_pages": consistency["ingested_missing_pages"],
        "pending": pending_report,
        "qmd": qmd,
        "counts": {
            "pages": len(pages),
            "frontmatter_gaps": len(frontmatter_gaps),
            "missing_pages": len(missing_pages),
            "orphans": len(orphans),
            "index_drift": len(index_drift),
            "duplicate_raw_sources": len(duplicates),
            "stale_pages": len(stale),
            "source_index_gaps": len(consistency["source_index_gaps"]),
            "source_log_gaps": len(consistency["source_log_gaps"]),
            "ingested_missing_pages": len(consistency["ingested_missing_pages"]),
            "old_pending": len(pending_report["old_pending"]),
            "missing_pending": len(pending_report["missing_pending"]),
            "blocked_enrichment": len(pending_report["blocked_enrichment"]),
            "fetched_enrichment_not_ingested": len(pending_report["fetched_enrichment_not_ingested"]),
        },
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("# mindsync deterministic lint")
        for key in [
            "frontmatter_gaps",
            "missing_pages",
            "orphans",
            "index_drift",
            "duplicate_raw_sources",
            "stale_pages",
            "source_log_gaps",
            "ingested_missing_pages",
        ]:
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
        print("\n## _hot")
        print(f"words={hot['word_count']} too_long={hot['too_long']}")
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
        command_queue_scan(argparse.Namespace(vault=str(vault), json=False, min_age_seconds=0))
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


def command_embed(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    qmd = resolve_tool(vault, "qmd")
    if not qmd:
        message = "qmd not found; run ensure-tools"
        log_automation(vault, "error", f"embed skipped: {message}")
        print(message, file=sys.stderr)
        return 1
    try:
        with file_lock(vault, "embed", timeout=args.lock_timeout):
            log_automation(vault, "info", "qmd embed start")
            subprocess.run([qmd, "embed"], cwd=vault, check=True)
            write_json(state_paths(vault)["last_embed"], {"at": now_iso(), "mtime": dt.datetime.now().timestamp()})
            log_automation(vault, "info", "qmd embed complete")
    except Exception as exc:
        log_automation(vault, "error", f"qmd embed failed: {exc}")
        print(f"qmd embed failed: {exc}", file=sys.stderr)
        return 1
    print("Embedded wiki and recorded qmd timestamp.")
    return 0


def command_mark_embed(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    ensure_state(vault)
    write_json(state_paths(vault)["last_embed"], {"at": now_iso(), "mtime": dt.datetime.now().timestamp()})
    print("Recorded qmd embed timestamp.")
    return 0


def vault_label_suffix(vault: Path) -> str:
    digest = hashlib.sha256(str(vault).encode("utf-8")).hexdigest()[:8]
    return f"{slugify(vault.name)}.{digest}"


def launchd_labels(vault: Path) -> dict[str, str]:
    suffix = vault_label_suffix(vault)
    return {"wiki": f"com.mindsync.wiki.{suffix}", "raw": f"com.mindsync.raw.{suffix}"}


def latest_automation_error(vault: Path) -> str | None:
    path = automation_log_path(vault)
    if not path.exists():
        return None
    latest = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if " ERROR " in line:
            latest = line
    return latest


def json_readable(path: Path) -> tuple[bool, str | None]:
    if not path.exists():
        return False, "missing"
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True, None
    except json.JSONDecodeError as exc:
        return False, str(exc)


def command_doctor(args: argparse.Namespace) -> int:
    vault = vault_root(args.vault)
    pages = wiki_pages(vault)
    required_paths = [
        "raw",
        "raw/assets",
        "wiki",
        "wiki/sources",
        "wiki/entities",
        "wiki/concepts",
        "wiki/analyses",
        ".mindsync/state",
        "index.md",
        "log.md",
    ]
    checks = []

    for rel in required_paths:
        path = vault / rel
        checks.append({"name": f"path:{rel}", "ok": path.exists(), "detail": str(path)})

    for tool in ["qmd", "summarize"]:
        resolved = resolve_tool(vault, tool)
        checks.append({"name": f"tool:{tool}", "ok": bool(resolved), "detail": resolved or "not found"})

    pending_ok, pending_error = json_readable(state_paths(vault)["pending"])
    checks.append({"name": "state:pending-json", "ok": pending_ok, "detail": pending_error or "readable"})

    qmd = qmd_report(vault, pages)
    checks.append({"name": "qmd:last-embed-known", "ok": not qmd["unknown"], "detail": qmd.get("last_embed_at") or "unknown"})
    checks.append({"name": "qmd:not-stale", "ok": not qmd["stale"], "detail": json.dumps(qmd, sort_keys=True)})

    for rel in ["scripts/hook-prompt-submit.sh", "scripts/hook-session-end.sh", "scripts/on-raw-change.sh", "scripts/schedule-embed.sh"]:
        path = vault / rel
        checks.append({"name": f"script:{rel}", "ok": path.exists() and os.access(path, os.X_OK), "detail": str(path)})

    if sys.platform == "darwin":
        labels = launchd_labels(vault)
        for kind, label in labels.items():
            result = subprocess.run(["launchctl", "list", label], text=True, capture_output=True)
            checks.append({"name": f"launchd:{kind}", "ok": result.returncode == 0, "detail": label})
    else:
        checks.append({"name": "launchd", "ok": True, "detail": "skipped on non-macOS"})

    latest_error = latest_automation_error(vault)
    checks.append({"name": "automation:last-error", "ok": latest_error is None, "detail": latest_error or "none"})

    failed = [check for check in checks if not check["ok"]]
    report = {"ok": not failed, "checks": checks, "qmd": qmd, "latest_automation_error": latest_error}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("# mindsync doctor")
        for check in checks:
            status = "ok" if check["ok"] else "fail"
            print(f"{status:4} {check['name']} - {check['detail']}")
    return 0 if not failed else 1


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
    p.add_argument("--min-age-seconds", type=int, default=30)
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
    p.add_argument("--stale-days", type=int, default=90)
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

    p = sub.add_parser("embed")
    p.add_argument("--vault", default=".")
    p.add_argument("--lock-timeout", type=float, default=30.0)
    p.set_defaults(func=command_embed)

    p = sub.add_parser("mark-embed")
    p.add_argument("--vault", default=".")
    p.set_defaults(func=command_mark_embed)

    p = sub.add_parser("doctor")
    p.add_argument("--vault", default=".")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
