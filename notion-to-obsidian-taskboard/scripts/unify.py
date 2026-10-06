#!/usr/bin/env python3
"""
Step 2: Unify — merge CSV metadata into MD frontmatter.
MD content always wins. This only fills gaps (status, labels, project).
Drops 'assign' and 'related' by default (always, regardless of --drop).
Usage: python3 unify.py --vault ./MyVault --tasks-dir "My Tasks Folder" [--status-map "Notion:status"] [--extra-cols "Col:key"] [--delete-csvs]
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    find_csv_md_pairs,
    find_csv_row,
    get_csv_name_col,
    get_h1_title,
    normalize,
    parse_frontmatter,
    render_frontmatter,
    resolve_vault,
    trash,
)

STATUS_MAP = {
    "Future": "future",
    "Todo": "todo",
    "In Progress": "in-progress",
    "Ready for Release": "ready",
    "Done": "done",
    "Blocked": "blocked",
    "Won't do": "wont-do",
    # Unicode right single quotation mark variant — normalize() doesn't convert quotes
    "Won\u2019t do": "wont-do",
}

BOARD_STATUSES = ("future", "todo", "in-progress", "ready", "blocked", "done", "wont-do")

# Default keys to drop (case-insensitive matching handles variants)
DEFAULT_DROP = {"assign", "related"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument(
        "--tasks-dir", help="Limit unify to this folder (and subfolders) only"
    )
    parser.add_argument(
        "--drop",
        default="assign,related",
        help="Comma-separated frontmatter keys to remove (default: assign,related)",
    )
    parser.add_argument(
        "--status-map",
        default="",
        help="Map Notion status values onto the board statuses, on top of the defaults. "
        f"Format: 'Notion value:status,...' where status is one of: {', '.join(BOARD_STATUSES)}. "
        'Example: --status-map "Not started:todo,In progress:in-progress"',
    )
    parser.add_argument(
        "--extra-cols",
        default="",
        help="Extra CSV columns to copy into frontmatter. "
        "Format: 'CsvCol:fm-key,...' or just 'CsvCol' (auto-lowercased). "
        'Example: --extra-cols "Priority:priority,Sprint:sprint"',
    )
    parser.add_argument(
        "--delete-csvs",
        action="store_true",
        help="Delete _all.csv files after unifying",
    )
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    drop_keys = {k.strip().lower() for k in args.drop.split(",")} | DEFAULT_DROP

    status_map = dict(STATUS_MAP)
    for entry in args.status_map.split(","):
        if not entry.strip():
            continue
        if ":" not in entry:
            parser.error(f"--status-map entry {entry!r} must be 'Notion value:status'")
        notion_value, status = (s.strip() for s in entry.rsplit(":", 1))
        if status not in BOARD_STATUSES:
            parser.error(f"--status-map target {status!r} must be one of: {', '.join(BOARD_STATUSES)}")
        status_map[notion_value] = status

    # Parse extra column mappings: csv_col -> fm_key
    extra_col_map: dict[str, str] = {}
    if args.extra_cols.strip():
        for entry in args.extra_cols.split(","):
            entry = entry.strip()
            if not entry:
                continue
            if ":" in entry:
                csv_col, fm_key = entry.split(":", 1)
                extra_col_map[csv_col.strip()] = fm_key.strip().lower()
            else:
                extra_col_map[entry] = entry.lower()
    if extra_col_map:
        print(f"Extra columns: {extra_col_map}")

    pairs = find_csv_md_pairs(vault)
    if args.tasks_dir:
        scope = (vault / args.tasks_dir).resolve()
        pairs = [
            (csv_path, md_dir)
            for csv_path, md_dir in pairs
            if md_dir
            and (md_dir.resolve() == scope or scope in md_dir.resolve().parents)
        ]

    for csv_path, md_dir in pairs:
        if not md_dir or not md_dir.exists():
            print(f"Skipping {csv_path.name} — no matching MD folder")
            continue

        print(f"\nProcessing: {csv_path.relative_to(vault)}")

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            print("  CSV is empty — skipping")
            continue

        name_col = get_csv_name_col(list(rows[0].keys()))
        csv_by_title = {normalize(r[name_col]): r for r in rows if r[name_col].strip()}

        updated = skipped = no_csv_match = 0

        for md in sorted(md_dir.glob("*.md")):
            content = md.read_text("utf-8", errors="ignore")
            fm, body = parse_frontmatter(content)
            title = get_h1_title(content) or md.stem
            csv_row = find_csv_row(title, csv_by_title)

            if not csv_row:
                no_csv_match += 1

            changed = False

            if "status" not in fm:
                raw = csv_row.get("Status", "future")
                if not csv_row:
                    print(
                        f"  WARNING: no CSV row for {md.name!r} — defaulting status to 'future'"
                    )
                mapped = status_map.get(raw)
                if mapped is None and raw:
                    mapped = raw.lower()
                    if mapped not in BOARD_STATUSES:
                        print(
                            f"  WARNING: unrecognised status {raw!r} for {md.name!r} — stored as {mapped!r}"
                        )
                fm["status"] = mapped or "future"
                changed = True

            if csv_row:
                for csv_col, fm_key in (("Labels", "labels"), ("Project", "project")):
                    if fm_key not in fm and csv_row.get(csv_col, "").strip():
                        fm[fm_key] = csv_row[csv_col].strip()
                        changed = True
                # Extra columns requested via --extra-cols
                for csv_col, fm_key in extra_col_map.items():
                    if fm_key not in fm and csv_row.get(csv_col, "").strip():
                        fm[fm_key] = csv_row[csv_col].strip()
                        changed = True

            for key in list(fm.keys()):
                if key.lower() in drop_keys:
                    del fm[key]
                    changed = True

            if changed:
                md.write_text(render_frontmatter(fm, body), "utf-8")
                updated += 1
            else:
                skipped += 1

        print(
            f"  Updated: {updated}  |  Already complete: {skipped}  |  No CSV match: {no_csv_match}"
        )

        if args.delete_csvs:
            trash(csv_path)
            print(f"  Trashed: {csv_path.name}")


if __name__ == "__main__":
    main()
