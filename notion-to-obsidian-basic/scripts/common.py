"""Shared utilities for notion-to-obsidian-basic scripts."""

from pathlib import Path


def resolve_vault(path: Path) -> Path:
    return path.expanduser().resolve()


def add_dot_slash(href: str) -> str:
    """Prefix a relative link with './' for clarity.

    Leaves alone: already-prefixed './...', parent-relative '../...', absolute '/',
    and anchor-only '#...' links.
    """
    if href.startswith(("./", "../", "/", "#")):
        return href
    return "./" + href
