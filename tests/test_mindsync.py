import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "mindsync.py"


def run_cmd(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


class MindsyncHelperTests(unittest.TestCase):
    def test_init_scaffolds_portable_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd(
                "init",
                "--vault",
                str(vault),
                "--name",
                "Tester",
                "--domain",
                "test research",
                "--priority",
                "keep facts clean",
            )

            self.assertTrue((vault / "AGENTS.md").exists())
            self.assertTrue((vault / "CLAUDE.md").exists())
            self.assertTrue((vault / ".mindsync" / "config.json").exists())
            self.assertTrue((vault / ".mindsync" / "state" / "pending-ingest.json").exists())
            self.assertTrue((vault / "wiki" / "analyses" / "assets").is_dir())
            config = json.loads((vault / ".mindsync" / "config.json").read_text())
            self.assertEqual(config["automation"], "zero-touch")
            self.assertIn("codex", config["adapters"])

    def test_queue_scan_and_mark_ingested_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            (vault / "raw" / "source one.md").write_text("hello", encoding="utf-8")
            (vault / "raw" / "assets" / "diagram.png").write_bytes(b"fake-image")

            result = run_cmd("queue-scan", "--vault", str(vault), "--json", "--min-age-seconds", "0")
            data = json.loads(result.stdout)
            self.assertEqual(data["pending"], 2)
            paths = {item["path"] for item in data["items"]}
            self.assertIn("raw/source one.md", paths)
            self.assertIn("raw/assets/diagram.png", paths)

            run_cmd("mark-ingested", "--vault", str(vault), "--path", "raw/source one.md")
            result = run_cmd("queue-scan", "--vault", str(vault), "--json", "--min-age-seconds", "0")
            data = json.loads(result.stdout)
            pending_paths = {item["path"] for item in data["items"] if item["status"] == "pending"}
            self.assertNotIn("raw/source one.md", pending_paths)

    def test_queue_scan_skips_temp_and_too_recent_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            (vault / "raw" / "clip.md").write_text("fresh", encoding="utf-8")
            (vault / "raw" / "clip.tmp").write_text("temp", encoding="utf-8")
            (vault / "raw" / "clip.crdownload").write_text("download", encoding="utf-8")

            result = run_cmd("queue-scan", "--vault", str(vault), "--json")
            data = json.loads(result.stdout)
            self.assertEqual(data["pending"], 0)

            result = run_cmd("queue-scan", "--vault", str(vault), "--json", "--min-age-seconds", "0")
            data = json.loads(result.stdout)
            pending_paths = {item["path"] for item in data["items"] if item["status"] == "pending"}
            self.assertEqual(pending_paths, {"raw/clip.md"})

    def test_queue_scan_repairs_pending_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            known = vault / "raw" / "known.md"
            known.write_text("known", encoding="utf-8")
            known_digest = hashlib.sha256(known.read_bytes()).hexdigest()
            duplicate = vault / "raw" / "duplicate.md"
            duplicate.write_text("duplicate", encoding="utf-8")
            duplicate_digest = hashlib.sha256(duplicate.read_bytes()).hexdigest()
            state = vault / ".mindsync" / "state"
            (state / "source-hashes.json").write_text(
                json.dumps({"version": 1, "sources": {known_digest: {"path": "raw/known.md"}}}),
                encoding="utf-8",
            )
            (state / "pending-ingest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "items": [
                            {"id": "known", "path": "raw/known.md", "sha256": known_digest, "status": "pending"},
                            {"id": "missing", "path": "raw/missing.md", "sha256": "missinghash", "status": "pending"},
                            {"id": "dup1", "path": "raw/duplicate.md", "sha256": duplicate_digest, "status": "pending"},
                            {"id": "dup2", "path": "raw/duplicate.md", "sha256": duplicate_digest, "status": "pending"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = run_cmd("queue-scan", "--vault", str(vault), "--json", "--min-age-seconds", "0")
            data = json.loads(result.stdout)
            statuses = {item["id"]: item["status"] for item in data["items"]}
            self.assertEqual(statuses["known"], "ingested")
            self.assertEqual(statuses["missing"], "missing")
            self.assertEqual(statuses["dup1"], "pending")
            self.assertEqual(statuses["dup2"], "duplicate")

    def test_lint_reports_missing_frontmatter_and_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            page = vault / "wiki" / "concepts" / "alpha.md"
            page.write_text("No frontmatter\n\nLinks to [[wiki/concepts/missing]].", encoding="utf-8")

            result = run_cmd("lint", "--vault", str(vault), "--json")
            data = json.loads(result.stdout)
            self.assertEqual(data["counts"]["frontmatter_gaps"], 1)
            self.assertEqual(data["counts"]["missing_pages"], 1)

    def test_lint_reports_stale_page_from_frontmatter_updated(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            old = dt.date.today() - dt.timedelta(days=100)
            page = vault / "wiki" / "concepts" / "old.md"
            page.write_text(
                "---\n"
                "title: Old\n"
                "type: concept\n"
                "tags: []\n"
                "created: 2026-01-01\n"
                f"updated: {old.isoformat()}\n"
                "sources: []\n"
                "---\n"
                "# Old\n",
                encoding="utf-8",
            )

            result = run_cmd("lint", "--vault", str(vault), "--json", "--stale-days", "90")
            data = json.loads(result.stdout)
            self.assertEqual(data["counts"]["stale_pages"], 1)
            self.assertEqual(data["stale_pages"][0]["source"], "frontmatter")

    def test_lint_reports_stale_page_from_mtime_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            page = vault / "wiki" / "concepts" / "mtime-old.md"
            page.write_text("# Mtime Old\n", encoding="utf-8")
            old_ts = (dt.datetime.now() - dt.timedelta(days=100)).timestamp()
            os.utime(page, (old_ts, old_ts))

            result = run_cmd("lint", "--vault", str(vault), "--json", "--stale-days", "90")
            data = json.loads(result.stdout)
            stale_paths = {item["path"]: item["source"] for item in data["stale_pages"]}
            self.assertEqual(stale_paths["wiki/concepts/mtime-old"], "mtime")

    def test_lint_reports_qmd_stale_from_last_embed(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            page = vault / "wiki" / "concepts" / "alpha.md"
            page.write_text(
                "---\n"
                "title: Alpha\n"
                "type: concept\n"
                "tags: []\n"
                "created: 2026-04-12\n"
                "updated: 2026-04-12\n"
                "sources: []\n"
                "---\n"
                "# Alpha\n",
                encoding="utf-8",
            )
            old_ts = page.stat().st_mtime - 10
            (vault / ".mindsync" / "state" / "last-embed.json").write_text(
                json.dumps({"at": "2026-04-12T00:00:00+00:00", "mtime": old_ts}),
                encoding="utf-8",
            )

            result = run_cmd("lint", "--vault", str(vault), "--json")
            data = json.loads(result.stdout)
            self.assertTrue(data["qmd"]["stale"])

    def test_state_json_writes_are_readable_and_temp_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            run_cmd("queue-scan", "--vault", str(vault), "--json", "--min-age-seconds", "0")

            state = vault / ".mindsync" / "state"
            for path in state.glob("*.json"):
                json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(list(state.glob(".*.tmp")))

    def test_raw_watcher_scripts_do_not_embed_qmd(self):
        raw_script = (ROOT / "scripts" / "on-raw-change.sh").read_text(encoding="utf-8")
        schedule_script = (ROOT / "scripts" / "schedule-embed.sh").read_text(encoding="utf-8")
        self.assertNotIn("qmd embed", raw_script)
        self.assertIn("raw/ changes -> queue pending ingest only", schedule_script)

    def test_export_training_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            page = vault / "wiki" / "concepts" / "alpha.md"
            page.write_text(
                "---\n"
                "title: Alpha\n"
                "type: concept\n"
                "tags: []\n"
                "created: 2026-04-12\n"
                "updated: 2026-04-12\n"
                "sources: []\n"
                "---\n"
                "# Alpha\n\nAlpha is a useful concept.",
                encoding="utf-8",
            )

            out = vault / "wiki" / "analyses" / "training.jsonl"
            run_cmd("export-training", "--vault", str(vault), "--output", str(out))
            lines = out.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            first = json.loads(lines[0])
            self.assertEqual(first["messages"][1]["role"], "user")

    def test_ensure_tools_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            result = run_cmd("ensure-tools", "--vault", str(vault), "--tool", "qmd", "--dry-run")
            self.assertIn("@tobilu/qmd", result.stdout)
            self.assertTrue((vault / ".mindsync" / "tools" / "package.json").exists())

    @unittest.skipIf(shutil.which("python3") is None, "python3 missing")
    def test_chart_output_when_matplotlib_available(self):
        try:
            import matplotlib  # noqa: F401
        except Exception:
            self.skipTest("matplotlib not installed")

        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            run_cmd("init", "--vault", str(vault), "--no-copy-scripts")
            data = Path(tmp) / "chart.csv"
            data.write_text("label,value\nA,1\nB,2\n", encoding="utf-8")
            result = run_cmd("chart", "--vault", str(vault), "--data", str(data), "--title", "Test Chart")
            self.assertIn("![[wiki/analyses/assets/", result.stdout)
            self.assertTrue(any((vault / "wiki" / "analyses" / "assets").glob("*.png")))


if __name__ == "__main__":
    unittest.main()
