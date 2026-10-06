#!/usr/bin/env python3
"""
Step 1: Audit — compare CSVs vs MD files, report gaps.
Also auto-merges any extra (non-_all) CSVs found inside the MD folder into the _all.csv and deletes them.
Usage: python3 audit.py --vault ./MyVault --tasks-dir "My Tasks Folder"
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    find_csv_md_pairs,
    find_csv_row,
    fuzzy_title_match,
    get_csv_name_col,
    get_h1_title,
    normalize,
    parse_frontmatter,
    resolve_vault,
    trash,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument(
        "--tasks-dir", help="Limit audit to this folder (and subfolders) only"
    )
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    pairs = find_csv_md_pairs(vault)

    if args.tasks_dir:
        scope = (vault / args.tasks_dir).resolve()
        pairs = [
            (csv_path, md_dir)
            for csv_path, md_dir in pairs
            if md_dir
            and (md_dir.resolve() == scope or scope in md_dir.resolve().parents)
        ]

    if not pairs:
        if args.tasks_dir:
            print(
                f"No *_all.csv found scoped to --tasks-dir {args.tasks_dir!r}. Check the folder name."
            )
        else:
            print("No *_all.csv files found.")
        return

    for csv_path, md_dir in pairs:
        print(f"\n{'=' * 60}")
        print(f"CSV:    {csv_path.relative_to(vault)}")
        print(f"Folder: {md_dir.relative_to(vault) if md_dir else 'NOT FOUND'}")

        if not md_dir or not md_dir.exists():
            print("  ERROR: no matching MD folder — skipping")
            continue

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("  CSV is empty — skipping")
            continue

        name_col = get_csv_name_col(list(rows[0].keys()))
        csv_by_title = {normalize(r[name_col]): r for r in rows if r[name_col].strip()}

        md_by_title: dict[str, Path] = {}
        for md in md_dir.glob("*.md"):
            content = md.read_text("utf-8", errors="ignore")
            title = get_h1_title(content) or md.stem
            md_by_title[title] = md

        print(f"\n  CSV rows:  {len(csv_by_title)}")
        print(f"  MD files:  {len(md_by_title)}")

        statuses = Counter(r.get("Status", "?") for r in rows)
        print(f"  Statuses:  {dict(statuses)}")

        md_titles = list(md_by_title.keys())
        missing_md = [
            (t, r)
            for t, r in csv_by_title.items()
            if not any(fuzzy_title_match(t, mdt) for mdt in md_titles)
        ]
        if missing_md:
            print(f"\n  In CSV but no MD ({len(missing_md)}):")
            for title, row in missing_md[:20]:
                print(f"    [{row.get('Status', '?'):10s}] {title!r}")
            if len(missing_md) > 20:
                print(f"    ... and {len(missing_md) - 20} more")
        else:
            print(f"\n  All CSV rows have a matching MD file.")

        print(f"\n  MD files missing CSV metadata:")
        missing_meta: dict[str, list[str]] = {}
        for title, md_path in md_by_title.items():
            content = md_path.read_text("utf-8", errors="ignore")
            fm, _ = parse_frontmatter(content)
            csv_row = find_csv_row(title, csv_by_title)
            gaps = [
                f"{field.lower()}={csv_row[field]!r}"
                for field in ("Status", "Labels", "Project")
                if field.lower() not in fm and csv_row.get(field, "").strip()
            ]
            if gaps:
                missing_meta[title] = gaps

        if missing_meta:
            for title, gaps in list(missing_meta.items())[:15]:
                print(f"    {title!r}: {', '.join(gaps)}")
            if len(missing_meta) > 15:
                print(f"    ... and {len(missing_meta) - 15} more")
        else:
            print("    None — all frontmatter complete.")

        # Check for CSV columns and frontmatter keys outside the known schema
        _check_unknown_schema(rows, md_by_title)

        # Check for non-_all CSVs inside the MD folder (Notion sometimes exports these)
        _check_extra_csvs(md_dir, csv_path, vault)


# CSV columns and frontmatter keys the skill knows how to handle
_KNOWN_CSV_COLS = {"name", "status", "labels", "project", "assign", "related"}
_KNOWN_FM_KEYS = {"status", "labels", "project", "notes"}


def _check_unknown_schema(rows: list[dict], md_by_title: dict[str, Path]) -> None:
    """Report CSV columns and frontmatter keys outside the known schema.

    Unknown CSV columns are silently dropped by unify unless --extra-cols is passed.
    Unknown frontmatter keys already in MD files are left untouched by all scripts.
    Surfaces both so the user can decide what to keep before running unify.
    """
    # Unknown CSV columns (present in any row, not in known set)
    all_csv_cols = set()
    for row in rows:
        all_csv_cols.update(k.strip().lower() for k in row.keys() if k and k.strip())
    unknown_csv = sorted(all_csv_cols - _KNOWN_CSV_COLS)

    # Unknown frontmatter keys already present across all MD files
    unknown_fm: set[str] = set()
    for md_path in md_by_title.values():
        content = md_path.read_text("utf-8", errors="ignore")
        fm, _ = parse_frontmatter(content)
        for key in fm:
            if key.strip().lower() not in _KNOWN_FM_KEYS:
                unknown_fm.add(key.strip())

    print(f"\n  Schema check:")
    if unknown_csv:
        print(f"    Unknown CSV columns (ignored by unify unless --extra-cols is set):")
        for col in unknown_csv:
            print(f"      {col!r}")
        suggestion = ",".join(unknown_csv)
        print(
            f'    To preserve all in frontmatter, pass to unify: --extra-cols "{suggestion}"'
        )
        print(
            f'    Or map selectively, e.g.:  --extra-cols "priority:priority,sprint:sprint"'
        )
    else:
        print(f"    All CSV columns are within the known schema.")

    if unknown_fm:
        print(
            f"    Unknown frontmatter keys already in MD files (left untouched by all scripts):"
        )
        for key in sorted(unknown_fm):
            print(f"      {key!r}")
    else:
        print(f"    No unknown frontmatter keys in MD files.")


def _check_extra_csvs(md_dir: Path, all_csv: Path, vault: Path) -> None:
    """Merge any *.csv files inside the MD folder that aren't the *_all.csv into the _all.csv.

    Rows already present in _all.csv (by title) are skipped.
    Unique rows are appended using the _all.csv's column order, then the extra CSV is deleted.
    """
    extra = [p for p in md_dir.glob("*.csv") if "_all" not in p.stem]
    if not extra:
        return

    print(f"\n  Extra CSVs inside {md_dir.name!r}:")

    # Read the _all.csv so we know its column order and existing titles
    with open(all_csv, encoding="utf-8-sig") as f:
        all_content = f.read()
    with open(all_csv, encoding="utf-8-sig") as f:
        all_reader = list(csv.DictReader(f))

    try:
        all_name_col = (
            get_csv_name_col(list(all_reader[0].keys())) if all_reader else "Name"
        )
        all_fieldnames = list(all_reader[0].keys()) if all_reader else []
        all_titles = {
            normalize(r[all_name_col])
            for r in all_reader
            if r.get(all_name_col, "").strip()
        }
    except (ValueError, IndexError):
        print(f"    Could not parse {all_csv.name} — skipping extra CSV merge")
        return

    for extra_csv in extra:
        with open(extra_csv, encoding="utf-8-sig") as f:
            try:
                extra_rows = list(csv.DictReader(f))
            except Exception:
                print(f"    {extra_csv.name}: could not parse — skipping")
                continue

        if not extra_rows:
            trash(extra_csv)
            print(f"    {extra_csv.name}: empty — deleted")
            continue

        try:
            extra_name_col = get_csv_name_col(list(extra_rows[0].keys()))
        except ValueError:
            print(f"    {extra_csv.name}: no Name column — skipping")
            continue

        rows_to_merge = [
            r
            for r in extra_rows
            if r.get(extra_name_col, "").strip()
            and normalize(r[extra_name_col]) not in all_titles
        ]

        if rows_to_merge:
            # Append missing rows to _all.csv using its column order
            with open(all_csv, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=all_fieldnames, extrasaction="ignore"
                )
                for row in rows_to_merge:
                    # Remap extra CSV's name col to _all's name col if they differ
                    if extra_name_col != all_name_col and all_name_col not in row:
                        row[all_name_col] = row.get(extra_name_col, "")
                    writer.writerow(row)
            for r in rows_to_merge:
                print(f"    Merged into _all.csv: {r.get(extra_name_col, '?')!r}")

        trash(extra_csv)
        skipped = len(extra_rows) - len(rows_to_merge)
        print(
            f"    {extra_csv.name}: merged {len(rows_to_merge)} row(s), skipped {skipped} duplicate(s) — deleted"
        )


if __name__ == "__main__":
    main()
