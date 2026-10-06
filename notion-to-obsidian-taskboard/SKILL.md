---
name: notion-to-obsidian-taskboard
description: Convert a Notion task export into a clean Obsidian task board. Unifies CSV and MD files into a single source of truth, merges metadata into frontmatter, extracts task notes into a Notes/ folder, and converts all tasks into a single Todos.md with markdown checkboxes. Expects a Notion task database with Name, Status, Labels and Project columns; other status values can be mapped with --status-map. Requires notion-to-obsidian-basic to be run first on fresh exports.
disable-model-invocation: true
---

# Notion to Obsidian — Task Board

Converts a Notion task export (CSV + MD files) into clean Obsidian markdown with a single `Todos.md` and an Obsidian task board.

## Philosophy

1. **CSVs and MD files are redundant** — pick one source of truth (MD wins for content, CSV wins for metadata gaps)
2. **Frontmatter first** — unify all metadata into frontmatter before doing anything structural
3. **No data loss** — Done and Won't Do tasks are preserved as `- [x]` and `- [-]`
4. **Notes stay linked** — tasks with real body content become separate Note files, linked from the task line

## Expected Notion database

- **Columns:** `Name`, `Status`, `Labels`, `Project` (plus `Assign` and `Related`, which are dropped). Other columns are ignored unless passed to `unify.py --extra-cols`.
- **Statuses:** `Future`, `Todo`, `In Progress`, `Ready for Release`, `Done`, `Blocked`, `Won't do` map out of the box. Any other Notion status needs `unify.py --status-map "Notion value:status"` onto one of the board statuses in the mapping table below, e.g. `--status-map "Not started:todo,In progress:in-progress"`.

## Final Todos.md format

Tasks are a flat list. Each task is one checkbox line; tasks with body content get an indented notes link.

```markdown
- [ ] Build the login screen #project/myapp #nice-to-have
  [notes](./Notes/Build%20the%20login%20screen.md)
- [x] Set up CI pipeline #project/myapp
- [-] Rewrite in Rust
```

> **Link encoding:** All spaces in markdown link paths must be replaced with `%20`. This applies to notes links in Todos.md (`./Notes/Some%20File.md`) and attachment links in Notes files (`./attachments/some%20image.png`). Obsidian renders both encoded and unencoded links, but encoded links are required for correct rendering in standard markdown viewers and GitHub.

> **Tag format:** Tags are lowercase kebab-case. `labels` values become flat tags (`#nice-to-have`). Other frontmatter keys use Obsidian nested tag syntax with a forward slash: `#project/myapp`, `#epic/phase-1`. Dots are removed from tag values (`p.o.c.` → `poc`).

## Scoping

Always pass `--tasks-dir "<folder name>"` to every script to limit processing to a single task folder. Without it, scripts walk the entire vault.

## Pipeline

See [PIPELINE.md](PIPELINE.md) for the full step-by-step with commands.

## Scripts

| Script | What it does |
| --- | --- |
| `scripts/audit.py` | Compares CSVs vs MD files, reports gaps |
| `scripts/unify.py` | Merges CSV metadata into MD frontmatter |
| `scripts/extract_notes.py` | Moves body content to Notes/, adds `notes:` frontmatter |
| `scripts/convert.py` | Generates Todos.md from all task frontmatter |
| `scripts/delete_stubs.py` | Deletes original task MD stubs after Todos.md is generated |

Run in order. Each script is idempotent.

## Status → checkbox mapping

| Frontmatter `status` | Checkbox |
| --- | --- |
| future | `- [>]` |
| todo | `- [ ]` |
| in-progress | `- [/]` |
| ready | `- [\]` |
| blocked | `- [?]` |
| done | `- [x]` |
| wont-do | `- [-]` |
