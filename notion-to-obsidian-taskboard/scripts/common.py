"""Shared utilities for vault-cleanup scripts."""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote


def trash(path: Path) -> None:
    """Move a file or directory to the macOS Trash. Aborts on non-macOS platforms."""
    if sys.platform != "darwin":
        print(
            f"ERROR: trash() requires macOS (got {sys.platform!r}). Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)
    trash_dir = Path.home() / ".Trash"
    dest = trash_dir / path.name
    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = trash_dir / f"{path.stem}-{stamp}{path.suffix}"
    shutil.move(str(path), str(dest))


_IMAGE_RE = re.compile(r"(!\[([^\]]*)\]\()([^)]+)(\))")
# Matches [text](path) but NOT ![alt](path) — used for non-image file attachments
_LINK_RE = re.compile(r"(?<!!)(\[([^\]]*)\]\()([^)]+)(\))")


def normalize(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def resolve_vault(path: Path) -> Path:
    return path.expanduser().resolve()


def get_h1_title(content: str) -> str | None:
    """Return the H1 title text (without the # prefix)."""
    m = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    return normalize(m.group(1)) if m else None


def get_h1_line(content: str) -> str | None:
    """Return the full H1 line including # prefix (for re-emitting into stubs)."""
    m = re.search(r"^(#\s+.+)", content, re.MULTILINE)
    return m.group(1) if m else None


# Frontmatter regex anchored to start-of-string to avoid matching --- in body
_FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_after_frontmatter)."""
    m = _FM_RE.match(content)
    if not m:
        return {}, content
    fm: dict = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([^:]+):\s*(.*)", line)
        if kv:
            fm[kv.group(1).strip()] = kv.group(2).strip()
    return fm, content[m.end() :]


def render_frontmatter(fm: dict, body: str) -> str:
    """Serialise frontmatter dict back into a markdown string."""
    if not fm:
        return body
    lines = ["---", *[f"{k}: {v}" for k, v in fm.items()], "---"]
    return "\n".join(lines) + "\n" + body


def get_body(content: str) -> str:
    """Content after frontmatter and H1."""
    body = _FM_RE.sub("", content)
    body = re.sub(r"^#[^\n]*\n?", "", body, flags=re.MULTILINE, count=1)
    return body.strip()


def get_csv_name_col(fieldnames: list[str]) -> str:
    """Return the name of the Name column, handling BOM prefix."""
    for k in fieldnames:
        if k == "Name" or k.endswith("Name"):
            return k
    raise ValueError(f"No 'Name' column found in: {fieldnames}")


# ---------------------------------------------------------------------------
# Fuzzy title matching
# ---------------------------------------------------------------------------


def _strip_for_match(s: str) -> str:
    """Normalise a title for fuzzy comparison.

    Strips characters that Notion drops from filenames (: ? ! * " < > | / \\)
    and typographic variants, then lowercases and collapses whitespace.
    Used only for matching — never mutates stored data.
    """
    s = s.replace("\u2019", "'").replace("\u2018", "'")  # curly quotes
    s = re.sub(r"[:/\\?*\"<>|!''`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def fuzzy_title_match(a: str, b: str, min_prefix: int = 40) -> bool:
    """Return True if two titles refer to the same task.

    Tries in order:
    1. Exact match after normalize()
    2. Exact match after _strip_for_match()
    3. Prefix match: one stripped title starts with the other (min_prefix chars)
    """
    if normalize(a) == normalize(b):
        return True
    sa, sb = _strip_for_match(a), _strip_for_match(b)
    if sa == sb:
        return True
    # Prefix match handles titles truncated mid-sentence
    short, long_ = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    return len(short) >= min_prefix and long_.startswith(short)


def find_csv_row(md_title: str, csv_by_title: dict) -> dict:
    """Return the CSV row that best matches md_title, or {} if none found."""
    for csv_title, row in csv_by_title.items():
        if fuzzy_title_match(md_title, csv_title):
            return row
    return {}


def unique_path(directory: Path, name: str, suffix: str) -> Path:
    """Return a non-colliding path in directory for a file named <name><suffix>."""
    candidate = directory / f"{name}{suffix}"
    if not candidate.exists():
        return candidate
    i = 2
    while (directory / f"{name} {i}{suffix}").exists():
        i += 1
    return directory / f"{name} {i}{suffix}"


def move_attachments(
    content: str,
    source_file: Path,
    attachments_dir: Path,
    moved: dict[Path, Path],
) -> str:
    """Move local files (images and linked files) to attachments_dir, update links.

    Handles both  ![alt](path)  and  [text](path)  syntax.
    Skips http/https URLs and .md cross-links — those are left unchanged.
    `moved` is a shared dict[original_path -> new_path] across all calls so that
    files referenced by multiple notes are only moved once.
    """
    attachments_dir.mkdir(parents=True, exist_ok=True)

    def replace(m: re.Match) -> str:
        prefix = m.group(1)  # e.g. '![alt](' or '[text]('
        href = m.group(3)
        suffix = m.group(4)  # ')'

        if href.startswith("http://") or href.startswith("https://"):
            return m.group(0)

        resolved = (source_file.parent / unquote(href)).resolve()

        # Leave .md cross-links (internal vault links) unchanged
        if resolved.suffix.lower() == ".md":
            return m.group(0)

        if resolved in moved:
            new_name = moved[resolved].name
        elif resolved.exists() and resolved.is_file():
            dest = unique_path(attachments_dir, resolved.stem, resolved.suffix)
            resolved.rename(dest)
            moved[resolved] = dest
            new_name = dest.name
        else:
            return m.group(0)

        return f"{prefix}./attachments/{quote(new_name)}{suffix}"

    content = _IMAGE_RE.sub(replace, content)
    content = _LINK_RE.sub(replace, content)
    return content


_SUBTASK_RE = re.compile(r"^(\s*- \[[ x/\\?>*!]\])\s+(?!#subtask)", re.MULTILINE)


def prefix_subtasks(body: str) -> str:
    """Prefix all checkbox lines with #subtask tag (idempotent)."""
    return _SUBTASK_RE.sub(r"\1 #subtask ", body)


def find_csv_md_pairs(vault: Path) -> list[tuple[Path, Path | None]]:
    """Find *_all.csv files and their matching MD subdirectory (sibling search)."""
    pairs = []
    for csv_path in sorted(vault.rglob("*_all.csv")):
        folder_stem = re.sub(r"\s+[0-9a-f]{32}_all$", "", csv_path.stem)
        # Search sibling dirs of the CSV, not just the vault root
        search_dir = csv_path.parent
        matches = [
            d
            for d in search_dir.iterdir()
            if d.is_dir() and d.name.startswith(folder_stem)
        ]
        if len(matches) > 1:
            print(
                f"  WARNING: multiple folders match {csv_path.name!r} — using {matches[0].name!r}"
            )
        # If no sibling folder found, fall back to the CSV's parent dir (CSV lives inside the tasks folder)
        md_dir = matches[0] if matches else csv_path.parent
        pairs.append((csv_path, md_dir))
    return pairs
