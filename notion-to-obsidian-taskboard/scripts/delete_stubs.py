#!/usr/bin/env python3
"""
Step 6: Delete task stubs — remove original MD files from the tasks folder after Todos.md is generated.
Only deletes .md files directly inside --tasks-dir; subdirectories are not touched.
Usage: python3 delete_stubs.py --vault ./MyVault --tasks-dir "My Tasks Folder"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import resolve_vault, trash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--tasks-dir", required=True)
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    tasks_dir = vault / args.tasks_dir
    if not tasks_dir.is_dir():
        print(f"ERROR: tasks-dir not found: {tasks_dir}")
        sys.exit(1)

    stubs = [f for f in tasks_dir.glob("*.md") if f.name != "Todos.md"]
    if not stubs:
        print("No stub files found — nothing to delete.")
        return

    for md in stubs:
        trash(md)

    print(f"Trashed {len(stubs)} stub files from {args.tasks_dir!r}")


if __name__ == "__main__":
    main()
