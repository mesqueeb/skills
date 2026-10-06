# Pipeline

## Setup

```bash
SKILL_DIR=~/.claude/skills/notion-to-obsidian-taskboard
VAULT=/path/to/your/vault        # absolute or relative path to the vault root
TASKS_DIR="Your Tasks Folder"    # name of the folder containing task MD files
```

## Execution guidelines

- Always pass `--tasks-dir` to scope every step to the target folder. Never run scripts without it unless explicitly asked to process the entire vault.
- Before running any step that **modifies or deletes files** (Steps 1–6), tell the user: which script you're about to run, what files will change, and ask for confirmation.
- After each step, report what was found/changed (counts, surprises, errors).
- Log any issues or edge cases encountered — these are candidates for improving the skill.

## Step 0 — Basic cleanup (fresh Notion exports only)

**Delegates to the `notion-to-obsidian-basic` skill.**

On a fresh Notion export, run the `notion-to-obsidian-basic` skill first. It strips UUID suffixes from filenames, rewrites internal links, converts Notion page URLs to relative links, and deletes `.DS_Store` files.

Invoke it as a separate skill: `/notion-to-obsidian-basic` with `--folder "$TASKS_DIR"`.

Do not re-implement Step 0 here — it lives in `notion-to-obsidian-basic`.

## Step 1 — Audit: find gaps between CSV and MD

**Modifies files: auto-merges extra CSVs into _all.csv and deletes them. All other checks are read-only.**

```bash
python3 "$SKILL_DIR/scripts/audit.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR"
```

Prints:
- Which CSVs have a matching MD folder
- Tasks in CSV with no MD file
- Metadata in CSV missing from MD frontmatter (labels, project, status)

After running, report findings to the user. Before proceeding, resolve:

1. **Extra CSVs** — automatically merged into the `_all.csv` (column order preserved) and deleted. Just verify the reported merged rows look correct.
2. **Unknown CSV columns** — ask the user which (if any) they want preserved in frontmatter. Use their answer to build the `--extra-cols` flag for Step 2.
3. **Unknown frontmatter keys** — these are already in MD files; confirm the user wants them left as-is.
4. **Statuses** — compare the printed `Statuses:` counts against the defaults in SKILL.md. For any other value, ask the user which board status it should become and use the answers to build the `--status-map` flag for Step 2.

Only proceed to Step 2 once the user has decided on all of the above.

## Step 2 — Unify: merge CSV metadata into MD frontmatter

**Modifies MD files. Ask user before running.**
Tell the user: how many MD files will be updated and what fields will be filled in.

If the audit found statuses outside the defaults, pass `--status-map "Not started:todo,In progress:in-progress"` (with the user's mapping) alongside the commands below.

If the user chose to preserve extra CSV columns (from the schema check), pass them:

```bash
python3 "$SKILL_DIR/scripts/unify.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR" \
  --extra-cols "ColumnName:fm-key,AnotherCol:another-key"
```

Otherwise, without extra columns:

```bash
python3 "$SKILL_DIR/scripts/unify.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR"
```

Fills missing `status`, `labels`, `project` frontmatter from the `_all.csv`.
Drops `assign` and `related` by default. MD content always wins over CSV.

After this step, MD files are the sole source of truth.

## Step 3 — Delete CSVs

**Deletes files. Ask user before running.**
Tell the user exactly which CSV files will be deleted.

```bash
python3 "$SKILL_DIR/scripts/unify.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR" --delete-csvs
```

The `--delete-csvs` flag re-runs unify (idempotent) then deletes matching `*_all.csv` files.

## Step 4 — Extract notes: move body content to Notes/

**Modifies and moves files. Ask user before running.**
Tell the user: how many tasks have bodies above threshold, where Notes/ will be created.

```bash
python3 "$SKILL_DIR/scripts/extract_notes.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR" --threshold 200
```

Tasks with body > `--threshold` chars:
- Full file moved to `Notes/<title>.md`
- Local images referenced in the note moved to `Notes/attachments/`, renamed if collision
- Image links in the note rewritten to `./attachments/<filename>`
- Original task file replaced with stub (frontmatter + H1 only)
- `notes: Notes/<title>.md` added to stub frontmatter

Images shared between multiple notes are moved once; subsequent notes get the updated link.
Tasks at or under threshold are left as stubs.

## Step 5 — Convert: generate Todos.md

**Creates/overwrites Todos.md. Ask user before running.**
Tell the user: how many tasks will be written, where Todos.md will land.

```bash
python3 "$SKILL_DIR/scripts/convert.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR" --output Todos.md
```

Reads every task stub. Writes one checkbox line per task to `Todos.md`, sorted by status. Tasks with a `notes:` frontmatter field get an indented link on the next line.

```
- [ ] Task title
  [notes](./Notes/Task%20title.md)
```

Status is encoded in the checkbox character — see SKILL.md for the mapping.

## Step 6 — Delete task stubs

**Deletes files. Ask user before running.**
Tell the user: how many MD files will be deleted from the tasks folder.

Once `Todos.md` exists and all notes have been extracted to `Notes/`, the original task stub files in the tasks folder are redundant. Delete them:

```bash
python3 "$SKILL_DIR/scripts/delete_stubs.py" --vault "$VAULT" --tasks-dir "$TASKS_DIR"
```

This deletes all `.md` files directly inside `--tasks-dir` (except `Todos.md`). Subdirectories (asset folders, `Notes/`) are not touched.

## Step 7 — Configure Task Board

See [TASK_BOARD_SETUP.md](TASK_BOARD_SETUP.md).

## Idempotency

**Steps 1–5 are all idempotent** — safe to re-run. Each script checks existing state before writing. Exception: Step 3 (`--delete-csvs`) deletes the `_all.csv`; after that, Steps 1–2 have nothing to process.
Step 6 is destructive and non-idempotent — only run it after Step 5 is confirmed correct.

## Re-running after a fresh Notion export
1. Drop new MD files into the tasks folder
2. Replace the `_all.csv`
3. Re-run Steps 0–5
