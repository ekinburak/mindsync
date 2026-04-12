import json
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

            result = run_cmd("queue-scan", "--vault", str(vault), "--json")
            data = json.loads(result.stdout)
            self.assertEqual(data["pending"], 2)
            paths = {item["path"] for item in data["items"]}
            self.assertIn("raw/source one.md", paths)
            self.assertIn("raw/assets/diagram.png", paths)

            run_cmd("mark-ingested", "--vault", str(vault), "--path", "raw/source one.md")
            result = run_cmd("queue-scan", "--vault", str(vault), "--json")
            data = json.loads(result.stdout)
            pending_paths = {item["path"] for item in data["items"] if item["status"] == "pending"}
            self.assertNotIn("raw/source one.md", pending_paths)

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
