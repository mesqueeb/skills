# Task Board Setup

Plugin: [Task Board](https://github.com/tu2-atmanand/Task-Board)

## Board columns

After running the pipeline, tasks live in `Todos.md` as checkboxes. Task Board should be configured to filter by **checkbox character**, not frontmatter status.

| Column | Checkbox filter |
| --- | --- |
| Future | `- [>]` |
| Todo | `- [ ]` |
| In Progress | `- [/]` |
| Ready for Release | `- [\]` |
| Done | `- [x]` |
| Blocked | `- [?]` — hide from board or show in separate column |
| Won't Do | `- [-]` — hide from board |

## Scan scope

Point Task Board at `Todos.md` only (not the whole vault) to avoid picking up stray checkboxes in meeting notes, Swift notes, etc.

## Project filtering

Each task stub file (in the tasks dir) retains a `project:` frontmatter field. These are not surfaced in `Todos.md` directly, but can be used to filter by opening the stub file or via Dataview queries on the tasks folder.

## Future: converting to inline tags

When ready to go fully inline (drop stub files entirely):
- Add status tags (e.g. `#future`, `#todo`, `#done`) directly to the checkbox line in `Todos.md`
- Configure Task Board to filter columns by tag instead of checkbox character
- Delete stub files from the tasks folder
