#!/usr/bin/env python3
"""
Step 5: Convert — generate Todos.md from task stubs.
Output file is written inside --tasks-dir by default (configurable via --output).
Usage: python3 convert.py --vault ./MyVault --tasks-dir "My Tasks Folder" [--output Todos.md]

Format:
- Flat list, no section headers, no blank lines between items
- Tags appended to each line: labels as #label-value, other FM keys as #key-value
- Tasks with a notes: field get an indented link on the next line
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import get_h1_title, parse_frontmatter, resolve_vault

STATUS_ORDER = ["future", "todo", "in-progress", "ready", "blocked", "done", "wont-do"]

CHECKBOX = {
    "future": "- [>]",
    "todo": "- [ ]",
    "in-progress": "- [/]",
    "ready": "- [\\]",
    "blocked": "- [?]",
    "done": "- [x]",
    "wont-do": "- [-]",
}

# FM keys that are not emitted as tags (handled structurally)
_SKIP_TAG_KEYS = {"status", "notes", "assign", "related"}

# FM keys whose values are used as tags without a key prefix
_NO_PREFIX_KEYS = {"labels"}


def _slugify(value: str) -> str:
    """Convert a value to a tag-safe slug: lowercase, spaces to hyphens, dots removed."""
    slug = value.strip().lower()
    slug = slug.replace(".", "")  # dots end tags in most renderers
    slug = re.sub(r"\s+", "-", slug)  # spaces to hyphens
    return slug


def _tags_for_task(fm: dict) -> list[str]:
    """Build tag list from frontmatter fields, excluding structural keys."""
    tags = []
    for key, value in fm.items():
        k = key.strip().lower()
        if k in _SKIP_TAG_KEYS or not value or not value.strip():
            continue
        # Labels may be comma-separated
        values = [v.strip() for v in value.split(",") if v.strip()]
        for v in values:
            if k in _NO_PREFIX_KEYS:
                tags.append(f"#{_slugify(v)}")
            else:
                tags.append(f"#{k}/{_slugify(v)}")
    return tags


def _notes_href(notes_path: str) -> str:
    """Return a URL-safe relative href for a notes path."""
    return notes_path.replace(" ", "%20")


def status_sort_key(task: dict) -> int:
    try:
        return STATUS_ORDER.index(task["status"])
    except ValueError:
        return len(STATUS_ORDER)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--tasks-dir", required=True)
    parser.add_argument("--output", default="Todos.md")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    tasks_dir = vault / args.tasks_dir
    output_path = tasks_dir / args.output

    tasks = []
    for md in sorted(tasks_dir.glob("*.md")):
        content = md.read_text("utf-8", errors="ignore")
        fm, _ = parse_frontmatter(content)
        status = fm.get("status", "future").lower()
        status = status.replace("won't-do", "wont-do").replace(
            "won\u2019t-do", "wont-do"
        )
        tasks.append(
            {
                "title": get_h1_title(content) or md.stem,
                "status": status,
                "notes": fm.get("notes", "").strip(),
                "tags": _tags_for_task(fm),
            }
        )

    tasks.sort(key=status_sort_key)

    lines = []
    for t in tasks:
        box = CHECKBOX.get(t["status"], "- [ ]")
        tag_str = (" " + " ".join(t["tags"])) if t["tags"] else ""
        lines.append(f"{box} {t['title']}{tag_str}")
        if t["notes"]:
            lines.append(f"  [notes](./{_notes_href(t['notes'])})")

    output_path.write_text("\n".join(lines) + "\n", "utf-8")
    print(f"Written {len(tasks)} tasks to {output_path.relative_to(vault)}")


if __name__ == "__main__":
    main()
