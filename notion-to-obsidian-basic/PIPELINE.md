# Pipeline

## Setup

```bash
SKILL_DIR=~/.claude/skills/notion-to-obsidian-basic
VAULT=/path/to/your/vault        # absolute path to the vault root
FOLDER="Your Folder"             # subfolder to process (required)
```

## Execution guidelines

- Always pass `--folder` to scope processing. Without it, the script walks the entire vault.
- Before running, tell the user what will change and ask for confirmation.
- After running, report counts (renamed, links updated, .DS_Store deleted) and any conflicts or surprises.
- Log edge cases — these are candidates for improving the skill.

## Step 0 — Strip UUIDs, sanitize filenames, and clean links

**Renames files and rewrites links. Ask user before running.**

Check if filenames have UUID suffixes or unsafe characters. Run this step on every fresh Notion export.

```bash
python3 "$SKILL_DIR/scripts/strip_uuids.py" --vault "$VAULT" --folder "$FOLDER"
```

Does three things in order:

1. **Rename** — strips ` <32-hex UUID>` from all filenames and subfolder names inside `--folder`. Also removes unsafe characters from stems: `# | ^ : % [ ] ( ) * " \ < > ?`. Handles the `_all.csv` suffix correctly. Skips conflicts and reports them.
2. **Rewrite links** — updates all internal markdown links: strips UUIDs and unsafe characters from all path components, decodes any over-encoded percent-sequences back to literal characters (only spaces stay as `%20`). Detects vault-root-absolute links (links that resolve from the vault root but not from the current file — e.g. set by Obsidian's "absolute path" link mode) and rewrites them as proper relative paths. Converts Notion page URLs (e.g. `https://notion.so/...UUID`) to relative local links where a matching file exists. Strips generic Notion homepage links.
3. **Clean up** — deletes any `.DS_Store` files found inside `--folder`.

## Step 1 — Consolidate: move index files into their folder

**Moves files and rewrites links. Ask user before running.**

Notion exports a page with subpages as `PageName.md` + `PageName/` at the same level. This step moves the index file into its folder so page and subpages live together.

```bash
python3 "$SKILL_DIR/scripts/consolidate.py" --vault "$VAULT" --folder "$FOLDER"
```

For every `PageName.md` that has a sibling `PageName/` directory (at any depth):
- Moves `PageName.md` → `PageName/PageName.md`
- Updates all links **to** the moved file across all `.md` files in `--folder`
- Fixes links **from** the moved file: paths like `[EULA](PageName/EULA.md)` that were correct at the old root-level location become `[EULA](./EULA.md)` at the new nested location

Run AFTER Step 0. Report how many files were moved and how many link files were updated.

## Idempotency

Step 0 is idempotent — safe to re-run. Files without UUIDs are skipped.
Step 1 is idempotent — files already inside their folder (no matching sibling folder at the same level) are skipped.
