#!/usr/bin/env python3
"""
Step 1: Consolidate — move index files into their sibling folder.

For any PageName.md that has a sibling PageName/ directory at the same level,
moves PageName.md → PageName/PageName.md and updates all internal links.

This applies recursively: Legal/EULA.md + Legal/EULA/ → Legal/EULA/EULA.md.

Links TO moved files are rewritten to the new location.
Links FROM moved files that were vault-root-relative (e.g. [EULA](Legal/EULA.md)
inside Legal.md, now Legal/Legal.md) are fixed to proper relative paths.

Run AFTER strip_uuids.py (Step 0).
Usage: python3 consolidate.py --vault ./MyVault --folder "My Folder"
"""

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).parent))
from common import add_dot_slash, resolve_vault

_MD_LINK_RE = re.compile(r"(!?\[)([^\]]*?)(\]\()([^)]+)(\))")


def _rel_href(from_file: Path, to_file: Path) -> str:
    """Relative path from from_file to to_file, with only spaces encoded."""
    return add_dot_slash(
        os.path.relpath(to_file, from_file.parent)
        .replace("\\", "/")
        .replace(" ", "%20")
    )


def _find_candidates(folder: Path) -> list[tuple[Path, Path]]:
    """Find all PageName.md files that have a sibling PageName/ directory."""
    result = []
    for md in sorted(folder.rglob("*.md")):
        sibling = md.parent / md.stem
        if sibling.is_dir():
            dest = sibling / md.name
            if dest.exists():
                print(f"  SKIP (conflict): {dest.relative_to(folder)} already exists")
            else:
                result.append((md, dest))
    return result


def _update_links(
    content: str, md_file: Path, vault: Path, moved: dict[Path, Path]
) -> str:
    """Rewrite internal links:
    - Links pointing to moved files → updated to new location
    - Vault-root-absolute links (resolve from vault root but not from current file) → made relative
    - Links inside a moved file that resolved from its old location → fixed to new relative path
    """
    # Reverse map: new path → old path, for fixing links inside moved files
    new_to_old = {v: k for k, v in moved.items()}

    def replace(m: re.Match) -> str:
        open_b, text, mid, href, close = m.groups()

        if ":" in href.split("/")[0]:
            return m.group(0)

        decoded = unquote(href)

        # Resolve from both current file and vault root
        rel_resolved = (md_file.parent / decoded).resolve()
        vault_resolved = (vault / decoded.lstrip("/")).resolve()

        # Check if link points to a moved file (check both resolutions)
        for resolved in (rel_resolved, vault_resolved):
            if resolved in moved:
                return (
                    f"{open_b}{text}{mid}{_rel_href(md_file, moved[resolved])}{close}"
                )

        # Fix vault-root-absolute links: resolves from vault root but not from current file
        if not rel_resolved.exists() and vault_resolved.exists():
            return f"{open_b}{text}{mid}{_rel_href(md_file, vault_resolved)}{close}"

        # Fix links inside a moved file: try resolving from the old location
        old_location = new_to_old.get(md_file.resolve())
        if old_location is not None:
            old_rel_resolved = (old_location.parent / decoded).resolve()
            if old_rel_resolved in moved:
                # Target was also moved in this run — redirect to its new location
                return f"{open_b}{text}{mid}{_rel_href(md_file, moved[old_rel_resolved])}{close}"
            if old_rel_resolved.exists():
                return f"{open_b}{text}{mid}{_rel_href(md_file, old_rel_resolved)}{close}"

        return m.group(0)

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

    # ── Phase 1: Find candidates ────────────────────────────────────────────────
    candidates = _find_candidates(folder)
    if not candidates:
        print("No files to consolidate.")
        return

    print(f"Found {len(candidates)} file(s) to consolidate:")
    for old, new in candidates:
        print(f"  {old.relative_to(folder)} → {new.relative_to(folder)}")

    # ── Phase 2: Build old→new map, then move ──────────────────────────────────
    # Build map BEFORE moving so resolved old paths are valid
    moved: dict[Path, Path] = {old.resolve(): new.resolve() for old, new in candidates}
    for old, new in candidates:
        old.rename(new)

    # ── Phase 3: Update links in all MD files ───────────────────────────────────
    updated = 0
    for md in sorted(folder.rglob("*.md")):
        original = md.read_text("utf-8", errors="ignore")
        content = _update_links(original, md, vault, moved)
        if content != original:
            md.write_text(content, "utf-8")
            updated += 1

    print(f"Moved {len(candidates)} file(s), updated links in {updated} file(s)")


if __name__ == "__main__":
    main()
