#!/usr/bin/env python3
"""
Step 0: Strip UUIDs and unsafe characters from filenames, update internal links,
fix Notion URLs, delete .DS_Store.
Run this on a fresh Notion export before any other processing.
Usage: python3 strip_uuids.py --vault ./MyVault --folder "My Folder"
"""

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).parent))
from common import add_dot_slash, resolve_vault

# Matches " <32 hex chars>" before an extension, "_all.<ext>", or end of string
_UUID_FILE_RE = re.compile(r" [0-9a-f]{32}(?=\.[^.]+$|_all\.[^.]+$|$)", re.IGNORECASE)

# Characters not allowed in filenames
_UNSAFE_CHARS_RE = re.compile(r'[#|^:%\[\]()*"\\<>?]')

# Matches both [text](href) and ![alt](href)
_MD_LINK_RE = re.compile(r"(!?\[)([^\]]*?)(\]\()([^)]+)(\))")

# Notion page URL ending in a 32-char hex UUID
_NOTION_PAGE_RE = re.compile(
    r"https://(?:www\.)?notion\.so/[^)?#\s]*([0-9a-f]{32})(?:\?[^)]*)?"
)

# Generic Notion homepage / product links with no page UUID
_GENERIC_NOTION_RE = re.compile(
    r"!?\[[^\]]*\]\(https://(?:www\.)?notion\.so(?:/(?:product|blog|help|pricing|enterprise|integrations)[^)]*?)?\)\n?"
)


def _strip_uuid(name: str) -> str:
    return _UUID_FILE_RE.sub("", name)


def _sanitize_stem(stem: str) -> str:
    """Remove unsafe characters from a file/folder stem."""
    clean = _UNSAFE_CHARS_RE.sub("", stem)
    clean = re.sub(r" {2,}", " ", clean).strip()
    return clean or stem  # never return empty


def _clean_name(name: str) -> str:
    """Strip UUID suffix and sanitize a filename (stem only, extension preserved)."""
    name = _strip_uuid(name)
    p = Path(name)
    new_stem = _sanitize_stem(p.stem)
    if new_stem == p.stem:
        return name
    return str(p.with_name(f"{new_stem}{p.suffix}"))


def _encode_path(path_str: str) -> str:
    """Encode only spaces in a path string."""
    return path_str.replace("\\", "/").replace(" ", "%20")


def _rel_path(from_file: Path, to_file: Path) -> str:
    """Compute a relative path from from_file to to_file, encoding only spaces."""
    return add_dot_slash(_encode_path(os.path.relpath(to_file, from_file.parent)))


def _clean_path_parts(href: str) -> tuple[str, bool]:
    """Strip UUIDs and unsafe chars from all components of an internal href.

    Decodes the href first (undoing any over-encoding), then re-encodes only
    spaces as %20. Returns (cleaned_href, was_changed).
    """
    decoded = unquote(href)
    parts = decoded.replace("\\", "/").split("/")
    new_parts = []
    changed = False
    for part in parts:
        p = Path(part)
        if p.suffix:
            new_stem = _sanitize_stem(_strip_uuid(p.stem))
            new_part = f"{new_stem}{p.suffix}"
        else:
            new_part = _sanitize_stem(_strip_uuid(part))
        if new_part != part:
            changed = True
        new_parts.append(new_part.replace(" ", "%20"))
    # Also flag as changed if decoding removed any %XX beyond %20
    if not changed and href != "/".join(new_parts):
        changed = True
    return "/".join(new_parts), changed


_MEDIA_EMBED_RE = re.compile(
    r"(?<!!)(\[[^\]]*\]\([^):]+\.(?:mp4|mov|webm|mp3|wav)\))",
    re.IGNORECASE,
)


_EMPTY_BULLET_RE = re.compile(r"^\s*-\s*$", re.MULTILINE)


def _fix_empty_bullets(content: str) -> str:
    """Remove empty bullet list items produced by Notion exports.

    Notion sometimes emits bare `- ` lines (with no content) as a side-effect
    of exporting nested media blocks or empty sub-items. They render as blank
    bullets in Obsidian and add no value.
    """
    return _EMPTY_BULLET_RE.sub("", content)


def _fix_media_embeds(content: str) -> str:
    """Add ! to local media links that are missing it.

    Notion exports video/audio blocks as [name.ext](path) without the !
    embed prefix. GitHub (since 2022) and Obsidian both render
    ![name.ext](path) as inline video/audio players, so we add the ! to
    make embeds work. External URLs (containing ':') are left as plain links.
    """
    return _MEDIA_EMBED_RE.sub(r"!\1", content)


def _fix_image_blank_lines(content: str) -> str:
    """Remove blank lines immediately preceding deeply-indented standalone image lines.

    Notion exports image embeds inside list items with a blank line before them,
    e.g.:

        - list item
                            ← blank line (8 spaces or empty)
            ![img](img.png) ← 8-space-indented image

    In CommonMark, the blank line causes the image to be parsed as a new block
    rather than a list-item continuation, making the indentation trigger an
    indented code block. Removing the blank line keeps the image as part of the
    list item, where indentation is relative to the list marker.
    """
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            line.strip() == ""
            and i + 1 < len(lines)
            and re.match(r"^ {5,}!\[", lines[i + 1])
        ):
            i += 1  # drop this blank line
            continue
        result.append(line)
        i += 1
    return "\n".join(result)


def _update_links(
    content: str, md_file: Path, vault: Path, uuid_to_new: dict[str, Path]
) -> str:
    def replace(m: re.Match) -> str:
        open_b, text, mid, href, close = m.groups()

        # Any URL scheme (http, https, mailto, tel, obsidian, etc.): : before first /
        if ":" in href.split("/")[0]:
            if href.startswith("http://") or href.startswith("https://"):
                nm = _NOTION_PAGE_RE.match(href)
                if nm and nm.group(1) in uuid_to_new:
                    return f"{open_b}{text}{mid}{_rel_path(md_file, uuid_to_new[nm.group(1)])}{close}"
            return m.group(0)

        # Clean UUID/unsafe chars from the href, then ensure './' prefix
        cleaned_href, _ = _clean_path_parts(href)
        cleaned_href = add_dot_slash(cleaned_href)
        cleaned_decoded = unquote(cleaned_href)

        # Resolve against both the current file and the vault root
        rel_target = (md_file.parent / cleaned_decoded).resolve()
        vault_target = (vault / cleaned_decoded.lstrip("/")).resolve()

        if not rel_target.exists() and vault_target.exists():
            # Link is vault-root-absolute (e.g. set by Obsidian's "absolute path" mode,
            # or starts with /). Rewrite as a proper relative path.
            return f"{open_b}{text}{mid}{_rel_path(md_file, vault_target)}{close}"

        if cleaned_href == href:
            return m.group(0)
        return f"{open_b}{text}{mid}{cleaned_href}{close}"

    return _MD_LINK_RE.sub(replace, content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument(
        "--folder", required=True, help="Subfolder inside the vault to process"
    )
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    folder = vault / args.folder
    if not folder.is_dir():
        print(f"ERROR: folder not found: {folder}")
        sys.exit(1)

    # ── Phase 1: Rename files & dirs, build UUID → new path map ────────────────
    uuid_to_new: dict[str, Path] = {}
    renamed = conflicts = 0

    all_items = sorted(folder.rglob("*"))
    files = [p for p in all_items if p.is_file()]
    # Process directories deepest-first so parent renames don't invalidate child paths
    dirs = sorted([p for p in all_items if p.is_dir()], key=lambda p: -len(p.parts))

    def _rename_item(item: Path) -> None:
        nonlocal renamed, conflicts
        new_name = _clean_name(item.name)
        if new_name == item.name:
            return
        dest = item.parent / new_name
        if dest.exists():
            conflicts += 1
            print(f"  SKIP (conflict): {item.name!r} → {new_name!r} already exists")
            return
        m = re.search(r" ([0-9a-f]{32})", item.stem, re.IGNORECASE)
        if m:
            uuid_to_new[m.group(1)] = dest
        item.rename(dest)
        renamed += 1

    for f in files:
        _rename_item(f)

    for d in dirs:
        new_name = _clean_name(d.name)
        if new_name != d.name:
            dest = d.parent / new_name
            if dest.exists():
                conflicts += 1
                print(f"  SKIP (conflict): {d.name!r} → {new_name!r} already exists")
            else:
                # Update any uuid_to_new paths that were under this directory
                for uuid, path in list(uuid_to_new.items()):
                    try:
                        uuid_to_new[uuid] = dest / path.relative_to(d)
                    except ValueError:
                        pass
                d.rename(dest)
                renamed += 1

    print(f"Renamed {renamed} items ({conflicts} conflict(s) skipped)")

    # ── Phase 2: Update links inside all MD files in folder ────────────────────
    updated = 0
    for md in sorted(folder.rglob("*.md")):
        original = md.read_text("utf-8", errors="ignore")
        content = _update_links(original, md, vault, uuid_to_new)
        content = _GENERIC_NOTION_RE.sub("", content)
        content = _fix_empty_bullets(content)
        content = _fix_media_embeds(content)
        content = _fix_image_blank_lines(content)
        if content != original:
            md.write_text(content, "utf-8")
            updated += 1

    print(f"Updated links in {updated} files")

    # ── Phase 3: Delete .DS_Store files ────────────────────────────────────────
    ds_count = 0
    for ds in folder.rglob(".DS_Store"):
        ds.unlink()
        ds_count += 1
    if ds_count:
        print(f"Deleted {ds_count} .DS_Store file(s)")


if __name__ == "__main__":
    main()
