#!/usr/bin/env python3
"""Check documentation layout rules from docs/README.md: links, names, headers, indexes."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
NAME = re.compile(r"[a-z0-9][a-z0-9.-]*")
FAILURE = re.compile(r"F-\d{3}-[a-z0-9-]+\.md")
WEEK = re.compile(r"\d{4}-W\d{2}\.md")
EXPERIMENT = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+")


def anchors(text):
    """GitHub heading anchors for a Markdown file."""
    result, counts = set(), {}
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.lower().replace("`", "")).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def markdown_files(root):
    files = [root / name for name in ("README.md", "AGENTS.md", "CONTRIBUTING.md") if (root / name).exists()]
    for folder in ("docs", "deliverables"):
        files += sorted(path for path in (root / folder).rglob("*.md")
                        if "evidence" not in path.relative_to(root).parts
                        and "templates" not in path.relative_to(root).parts)
    return files


def check(root):
    root = Path(root).resolve()
    problems = []
    for path in markdown_files(root):
        text = path.read_text()
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in LINK.findall(prose):
            if re.match(r"[a-z]+:", target):
                continue
            file_part, _, anchor = target.partition("#")
            destination = (path.parent / unquote(file_part)).resolve() if file_part else path
            if not destination.exists():
                problems.append(f"{path.relative_to(root)}: broken link {target}")
            elif anchor and destination.suffix == ".md" and anchor not in anchors(destination.read_text()):
                problems.append(f"{path.relative_to(root)}: missing anchor {target}")
    docs = root / "docs"
    for path in docs.rglob("*"):
        parts = path.relative_to(docs).parts
        if "evidence" in parts or path.name == "README.md":
            continue
        if not (NAME.fullmatch(path.name) or FAILURE.fullmatch(path.name) or WEEK.fullmatch(path.name)):
            problems.append(f"docs/{path.relative_to(docs)}: name is not lowercase kebab-case")
    for guide in sorted((docs / "guides").glob("*.md")):
        if guide.name != "README.md" and "**Last verified:**" not in guide.read_text():
            problems.append(f"docs/guides/{guide.name}: missing **Last verified:** line")
    experiments = docs / "experiments"
    index = (experiments / "README.md").read_text() if (experiments / "README.md").exists() else ""
    for folder in sorted(path for path in experiments.iterdir() if path.is_dir()) if experiments.is_dir() else []:
        if not EXPERIMENT.fullmatch(folder.name):
            problems.append(f"docs/experiments/{folder.name}: name must be YYYY-MM-DD-slug")
        if not (folder / "README.md").exists():
            problems.append(f"docs/experiments/{folder.name}: missing README.md report")
        if f"({folder.name}/)" not in index:
            problems.append(f"docs/experiments/{folder.name}: not listed in docs/experiments/README.md")
    failures = docs / "failures"
    index = (failures / "README.md").read_text() if (failures / "README.md").exists() else ""
    seen = {}
    for entry in sorted(failures.glob("F-*.md")) if failures.is_dir() else []:
        number = entry.name[:5]
        if number in seen:
            problems.append(f"docs/failures/{entry.name}: duplicate ID with {seen[number]}")
        seen[number] = entry.name
        if f"({entry.name})" not in index:
            problems.append(f"docs/failures/{entry.name}: not listed in docs/failures/README.md")
    return problems


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    problems = check(root)
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s)" if problems else "Documentation checks passed.")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
