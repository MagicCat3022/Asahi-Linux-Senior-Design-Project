"""Documentation layout checks from docs/README.md."""
import importlib.machinery
import importlib.util
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
            (root / "docs/guides/a-guide.md").write_text("# A guide\n\n## Real heading\n")
            (root / "docs/guides/Bad Name.md").write_text("# Bad\n\n**Last verified:** today\n")
            (root / "docs/experiments/README.md").write_text("# Experiments\n")
            (root / "docs/experiments/2026-10-14-run/README.md").write_text("# Run\n")
            (root / "docs/failures/README.md").write_text("# Failures\n")
            (root / "docs/failures/F-001-a.md").write_text("# F-001\n")
            (root / "docs/failures/F-001-b.md").write_text("# F-001 again\n")
            problems = "\n".join(check_docs.check(root))
            for expected in ("broken link docs/missing.md", "missing anchor docs/guides/a-guide.md#nope",
                             "Bad Name.md: name is not lowercase", "a-guide.md: missing **Last verified:**",
                             "2026-10-14-run: not listed", "F-001-b.md: duplicate ID", "F-001-a.md: not listed"):
                self.assertIn(expected, problems)

    def test_github_anchor_slugs(self):
        text = "# Title\n## 2. Install m1n1\n## Power workaround (4)\n## Overview of `atc.c`\n## Title\n"
        self.assertEqual(check_docs.anchors(text),
                         {"title", "2-install-m1n1", "power-workaround-4", "overview-of-atcc", "title-1"})


if __name__ == "__main__":
    unittest.main()
