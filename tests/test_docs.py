"""Documentation layout checks from docs/README.md."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("check_docs", str(ROOT / "tools/check-docs.py"))
spec = importlib.util.spec_from_loader("check_docs", loader)
check_docs = importlib.util.module_from_spec(spec)
loader.exec_module(check_docs)


class Documentation(unittest.TestCase):
    def test_repository_documentation_passes(self):
        self.assertEqual(check_docs.check(ROOT), [])

    def test_reports_broken_links_names_headers_and_indexes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ("guides", "experiments/2026-10-14-run", "failures"):
                (root / "docs" / folder).mkdir(parents=True)
            (root / "README.md").write_text("[gone](docs/missing.md) [anchor](docs/guides/a-guide.md#nope)\n")
            (root / "tools").mkdir()
            (root / "tools/asahi").write_text('fail("see docs/guides/gone.md or docs/guides/a-guide.md#real-heading")\n')
            (root / "docs/guides/a-guide.md").write_text("# A guide\n\n## Real heading\n")
            (root / "docs/guides/Bad Name.md").write_text("# Bad\n\n**Last verified:** today\n")
            (root / "docs/experiments/README.md").write_text("# Experiments\n")
            (root / "docs/experiments/2026-10-14-run/README.md").write_text("# Run\n\n| Hardware | FILL IN |\n")
            (root / "docs/failures/README.md").write_text("# Failures\n")
            (root / "docs/failures/F-001-a.md").write_text("# F-001\n")
            (root / "docs/failures/F-001-b.md").write_text("# F-001 again\n")
            problems = "\n".join(check_docs.check(root))
            for expected in ("broken link docs/missing.md", "missing anchor docs/guides/a-guide.md#nope",
                             "Bad Name.md: name is not lowercase", "a-guide.md: missing **Last verified:**",
                             "2026-10-14-run: not listed", "F-001-b.md: duplicate ID", "F-001-a.md: not listed",
                             "tools/asahi: points to missing docs/guides/gone.md", "README.md: replace every FILL IN"):
                self.assertIn(expected, problems)
            self.assertNotIn("a-guide.md#real-heading", problems)

    def test_github_anchor_slugs(self):
        text = "# Title\n## 2. Install m1n1\n## Power workaround (4)\n## Overview of `atc.c`\n## Title\n"
        self.assertEqual(check_docs.anchors(text),
                         {"title", "2-install-m1n1", "power-workaround-4", "overview-of-atcc", "title-1"})

    def test_pending_evidence_and_mutable_private_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "docs/experiments/2026-10-15-run/evidence/RUN_ID"
            evidence.mkdir(parents=True)
            (evidence.parents[2] / "README.md").write_text("# Experiments\n\n[Run](2026-10-15-run/)\n")
            report = evidence.parents[1] / "README.md"
            report.write_text("# Run\n\n[log](https://github.com/team/asahi-sdp-evidence/blob/main/run/log)\n")
            manifest = evidence / "private-evidence.json"
            manifest.write_text(json.dumps({"commit": None, "files_sha256": {"serial.log": "a" * 64}}))
            problems = "\n".join(check_docs.check(root))
            self.assertIn("not finalized", problems)
            self.assertIn("must use a full commit hash", problems)
            commit = "b" * 40
            url = f"https://github.com/team/asahi-sdp-evidence/blob/{commit}/run/"
            manifest.write_text(json.dumps({"commit": commit, "url": url, "files_sha256": {"serial.log": "a" * 64}}))
            (evidence / "logs.md").write_text(f"# Logs\n\n[serial.log]({url}serial.log)\n")
            report.write_text(f"# Run\n\n[log]({url}serial.log)\n")
            self.assertEqual(check_docs.check(root), [])


if __name__ == "__main__":
    unittest.main()
