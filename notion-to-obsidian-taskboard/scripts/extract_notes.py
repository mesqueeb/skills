#!/usr/bin/env python3
"""
Step 4: Extract notes — move body content to Notes/, add notes: frontmatter.
All local file links (images, video, PDFs, etc.) are moved to Notes/attachments/ and links updated.
Tasks with body <= threshold chars are left as stubs (frontmatter + H1 only).
Asset subfolders from stubs are moved to asset-orphans/ for user review.
Usage: python3 extract_notes.py --vault ./MyVault --tasks-dir "My Tasks Folder" [--threshold 200]
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    get_body,
    get_h1_line,
    get_h1_title,
    move_attachments,
    parse_frontmatter,
    prefix_subtasks,
    render_frontmatter,
    resolve_vault,
    unique_path,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--tasks-dir", required=True)
    parser.add_argument(
        "--threshold",
        type=int,
        default=200,
        help="Body char count above which a Note is created (default: 200)",
    )
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    tasks_dir = vault / args.tasks_dir
    if not tasks_dir.is_dir():
        print(f"ERROR: tasks-dir not found: {tasks_dir}")
        sys.exit(1)
    notes_dir = tasks_dir / "Notes"
    attachments_dir = notes_dir / "attachments"
    notes_dir.mkdir(exist_ok=True)

    # Shared map of original_path -> new_path so files referenced by multiple
    # notes are only moved once; subsequent notes just get the updated link.
    moved_attachments: dict[Path, Path] = {}

    orphans_dir = vault / "asset-orphans"
    moved = stubbed = skipped = orphaned = 0

    for md in sorted(tasks_dir.glob("*.md")):
        content = md.read_text("utf-8", errors="ignore")
        fm, _ = parse_frontmatter(content)

        if "notes" in fm:
            skipped += 1
            continue

        body = get_body(content)
        h1_line = get_h1_line(content)
        stub_body = f"{h1_line}\n" if h1_line else ""

        # Notion puts a task's attachments in a subfolder named after the MD stem
        asset_dir = tasks_dir / md.stem

        if len(body) <= args.threshold:
            new_content = render_frontmatter(fm, stub_body)
            if new_content != content:
                md.write_text(new_content, "utf-8")
                stubbed += 1
            # Body stripped — any asset subfolder is now unreferenced; move to orphans
            if asset_dir.is_dir() and any(asset_dir.iterdir()):
                orphans_dir.mkdir(exist_ok=True)
                dest = unique_path(orphans_dir, md.stem, "")
                shutil.move(str(asset_dir), str(dest))
                orphaned += 1
            continue

        # Move all local files (images, videos, PDFs, etc.) to Notes/attachments/
        note_content = move_attachments(content, md, attachments_dir, moved_attachments)

        # Use H1 title for note filename so truncated MD names don't propagate
        note_stem = get_h1_title(content) or md.stem
        note_stem = re.sub(r'[:/\\?*"<>|]', "", note_stem).strip()
        note_path = unique_path(notes_dir, note_stem, ".md")
        _, note_body = parse_frontmatter(note_content)
        # Strip Notion inline property lines (e.g. "Status: Done") left in the body
        note_body = re.sub(
            r"^(?:Status|Labels|Project|Assign|Related):[^\n]*\n?",
            "",
            note_body,
            flags=re.MULTILINE,
        )
        note_body = re.sub(r"\n{3,}", "\n\n", note_body)
        # Prefix all checkbox lines (including indented) with #subtask
        note_body = prefix_subtasks(note_body)
        note_path.write_text(note_body, "utf-8")

        fm["notes"] = note_path.relative_to(tasks_dir).as_posix()
        md.write_text(render_frontmatter(fm, stub_body), "utf-8")
        moved += 1

        # Clean up the now-empty asset subfolder; orphan it if anything was missed
        if asset_dir.is_dir():
            remaining = list(asset_dir.iterdir())
            if not remaining:
                asset_dir.rmdir()
            else:
                orphans_dir.mkdir(exist_ok=True)
                dest = unique_path(orphans_dir, md.stem, "")
                shutil.move(str(asset_dir), str(dest))
                orphaned += 1
                print(
                    f"  WARNING: {len(remaining)} unhandled file(s) in {asset_dir.name!r} → asset-orphans/"
                )

    print(f"Notes extracted:    {moved}")
    print(f"Stubs trimmed:      {stubbed}")
    print(f"Already done:       {skipped}")
    print(f"Attachments moved:  {len(moved_attachments)}")
    if moved_attachments:
        print(f"Attachments dir:    {attachments_dir.relative_to(vault)}/")
    print(f"Orphaned asset dirs: {orphaned}")
    if orphaned:
        print(f"Review orphans in:  {orphans_dir.relative_to(vault)}/")


if __name__ == "__main__":
    main()
