---
name: notion-to-obsidian-basic
description: Basic cleanup of a Notion export for Obsidian. Strips UUID suffixes and unsafe characters from filenames, rewrites internal links as proper relative paths, moves Notion index pages into their sibling folder, converts Notion page URLs to relative links, and deletes .DS_Store files. Use before any other Notion-to-Obsidian pipeline.
disable-model-invocation: true
---

# Notion to Obsidian — Basic Cleanup

Prepares a raw Notion export for use in Obsidian. Safe to run on any Notion export regardless of what comes next.

## What it does

1. **Strip UUIDs** — removes Notion's ` <32-hex>` suffixes from all filenames and subfolder names
2. **Sanitize filenames** — removes unsafe characters from file and folder stems: `# | ^ : % [ ] ( ) * " \ < > ?`
3. **Rewrite links** — updates internal markdown links to match renamed files (UUIDs stripped, unsafe chars removed, over-encoded percent-sequences decoded back to literal); detects vault-root-absolute links and rewrites as proper relative paths; converts `https://notion.so/...UUID` page links to relative local links; strips generic Notion homepage links
4. **Clean up** — deletes `.DS_Store` files
5. **Consolidate** — for every `PageName.md` that has a sibling `PageName/` folder, moves the file into the folder (`PageName/PageName.md`) and updates all internal links accordingly

## Link encoding rule

In internal markdown link hrefs, **only encode spaces** (`%20`). All other characters (`'`, `&`, `"`, `,`, emoji, etc.) must remain literal — do not percent-encode them. External URLs are left unchanged.

All same-level and deeper relative links are prefixed with `./` for clarity (e.g. `./Page.md`, `./Sub/Page.md`). Parent-relative links (`../`) are left as-is.

## Scoping

Always pass `--folder` to scope processing to a specific subfolder. Without it, the script walks the entire vault.

## Pipeline

See [PIPELINE.md](PIPELINE.md) for the full step-by-step with commands.

## Scripts

| Script | What it does |
| --- | --- |
| `scripts/strip_uuids.py` | Strips UUID suffixes, sanitizes filenames, rewrites links, cleans up |
| `scripts/consolidate.py` | Moves index pages into their sibling folder, updates all links |
