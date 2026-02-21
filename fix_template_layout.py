from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
PARTIALS = TEMPLATES / "partials"

INCLUDE_REPLACEMENTS = [
    ("components/", "partials/"),
]

BLOCK_LINE_RE = re.compile(r"^\s*\{%\s*(block\s+\w+|endblock)\s*%\}\s*$")
EXTENDS_RE = re.compile(r"^\s*\{%\s*extends\s+\"base.html\"\s*%\}\s*$")


def update_include_paths() -> None:
    for path in TEMPLATES.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        updated = text
        for src, dst in INCLUDE_REPLACEMENTS:
            updated = updated.replace(src, dst)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def normalize_partials() -> None:
    if not PARTIALS.exists():
        return
    for path in PARTIALS.rglob("*.html"):
        lines = path.read_text(encoding="utf-8").splitlines()
        cleaned: list[str] = []
        for line in lines:
            if EXTENDS_RE.match(line):
                continue
            if BLOCK_LINE_RE.match(line):
                continue
            cleaned.append(line)
        text = "\n".join(cleaned).rstrip() + "\n"
        path.write_text(text, encoding="utf-8")


def main() -> None:
    update_include_paths()
    normalize_partials()


if __name__ == "__main__":
    main()