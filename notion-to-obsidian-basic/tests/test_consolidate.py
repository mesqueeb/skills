"""Tests for consolidate.py — see tests/README.md for how to run."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from consolidate import _find_candidates, _rel_href, _update_links
import consolidate as _co_module


# ── _rel_href ────────────────────────────────────────────────────────────────


def test_rel_href_same_dir(tmp_path):
    src = tmp_path / "a.md"
    dst = tmp_path / "b.md"
    assert _rel_href(src, dst) == "./b.md"


def test_rel_href_into_subdir(tmp_path):
    src = tmp_path / "note.md"
    dst = tmp_path / "sub" / "note.md"
    assert _rel_href(src, dst) == "./sub/note.md"


def test_rel_href_up_one_level(tmp_path):
    src = tmp_path / "sub" / "note.md"
    dst = tmp_path / "other.md"
    assert _rel_href(src, dst) == "../other.md"


def test_rel_href_spaces_encoded(tmp_path):
    src = tmp_path / "note.md"
    dst = tmp_path / "My Folder" / "My Page.md"
    assert _rel_href(src, dst) == "./My%20Folder/My%20Page.md"


# ── _find_candidates ────────────────────────────────────────────────────────


def test_find_candidates_basic(tmp_path):
    folder = tmp_path / "vault"
    folder.mkdir()
    md = folder / "Page.md"
    md.write_text("", "utf-8")
    sibling = folder / "Page"
    sibling.mkdir()

    candidates = _find_candidates(folder)
    assert len(candidates) == 1
    old, new = candidates[0]
    assert old == md
    assert new == sibling / "Page.md"


def test_find_candidates_skips_conflict(tmp_path, capsys):
    folder = tmp_path / "vault"
    folder.mkdir()
    md = folder / "Page.md"
    md.write_text("", "utf-8")
    sibling = folder / "Page"
    sibling.mkdir()
    conflict = sibling / "Page.md"
    conflict.write_text("already here", "utf-8")

    candidates = _find_candidates(folder)
    assert candidates == []
    captured = capsys.readouterr()
    assert "SKIP" in captured.out


def test_find_candidates_no_sibling(tmp_path):
    folder = tmp_path / "vault"
    folder.mkdir()
    md = folder / "Standalone.md"
    md.write_text("", "utf-8")
    assert _find_candidates(folder) == []


def test_find_candidates_nested(tmp_path):
    # Recursively finds nested candidates
    folder = tmp_path / "vault"
    folder.mkdir()
    sub = folder / "Parent"
    sub.mkdir()
    md = sub / "Child.md"
    md.write_text("", "utf-8")
    (sub / "Child").mkdir()

    candidates = _find_candidates(folder)
    assert len(candidates) == 1


# ── _update_links ────────────────────────────────────────────────────────────


def test_update_links_rewrites_moved_file(tmp_path):
    old = (tmp_path / "Page.md").resolve()
    new = (tmp_path / "Page" / "Page.md").resolve()
    moved = {old: new}

    md = tmp_path / "other.md"
    content = "[Page](Page.md)"
    result = _update_links(content, md, tmp_path, moved)
    assert result == "[Page](./Page/Page.md)"


def test_update_links_http_unchanged(tmp_path):
    md = tmp_path / "note.md"
    content = "[link](https://example.com)"
    result = _update_links(content, md, tmp_path, {})
    assert result == content


def test_update_links_fixes_vault_root_absolute(tmp_path):
    target = tmp_path / "Notes" / "page.md"
    target.parent.mkdir()
    target.write_text("", "utf-8")

    sub = tmp_path / "other"
    sub.mkdir()
    md = sub / "note.md"

    content = "[page](Notes/page.md)"
    result = _update_links(content, md, tmp_path, {})
    assert result == "[page](../Notes/page.md)"


def test_update_links_image_links_rewritten(tmp_path):
    old = (tmp_path / "img.png").resolve()
    new = (tmp_path / "assets" / "img.png").resolve()
    moved = {old: new}

    md = tmp_path / "note.md"
    content = "![alt](img.png)"
    result = _update_links(content, md, tmp_path, moved)
    assert result == "![alt](./assets/img.png)"


# ── _update_links — non-http URL schemes (bug we fixed) ──────────────────────


def test_mailto_left_unchanged(tmp_path):
    md = tmp_path / "note.md"
    src = "[email](mailto:foo@example.com)"
    assert _update_links(src, md, tmp_path, {}) == src


def test_tel_left_unchanged(tmp_path):
    md = tmp_path / "note.md"
    src = "[call](tel:+15551234567)"
    assert _update_links(src, md, tmp_path, {}) == src


def test_obsidian_url_left_unchanged(tmp_path):
    md = tmp_path / "note.md"
    src = "[open](obsidian://open?vault=MyVault&file=Note)"
    assert _update_links(src, md, tmp_path, {}) == src


# ── Integration: full consolidate pipeline ───────────────────────────────────


def _run_main(vault: Path, folder_name: str) -> None:
    import argparse

    orig_parse = argparse.ArgumentParser.parse_args

    def patched_parse(self, args=None, namespace=None):
        return orig_parse(self, ["--vault", str(vault), "--folder", folder_name])

    argparse.ArgumentParser.parse_args = patched_parse
    try:
        _co_module.main()
    finally:
        argparse.ArgumentParser.parse_args = orig_parse


def test_consolidate_moves_index_into_folder(tmp_path):
    folder = tmp_path / "Export"
    folder.mkdir()

    index = folder / "Legal.md"
    index.write_text("# Legal\n", "utf-8")
    (folder / "Legal").mkdir()

    _run_main(tmp_path, "Export")

    assert (folder / "Legal" / "Legal.md").exists()
    assert not index.exists()


def test_consolidate_updates_links_to_moved_file(tmp_path):
    folder = tmp_path / "Export"
    folder.mkdir()

    index = folder / "Legal.md"
    index.write_text("# Legal\n", "utf-8")
    (folder / "Legal").mkdir()

    other = folder / "other.md"
    other.write_text("[Legal](Legal.md)\n", "utf-8")

    _run_main(tmp_path, "Export")

    result = other.read_text("utf-8")
    assert "./Legal/Legal.md" in result


def test_consolidate_fixes_links_from_moved_file(tmp_path):
    """Links inside the moved file that used to be root-relative must update."""
    folder = tmp_path / "Export"
    folder.mkdir()

    sub = folder / "Legal"
    sub.mkdir()
    (sub / "EULA.md").write_text("# EULA\n", "utf-8")

    # Legal.md at root level links to Legal/EULA.md — valid from root, but after
    # moving to Legal/Legal.md the link becomes ../Legal/EULA.md (or just EULA.md)
    index = folder / "Legal.md"
    index.write_text("[EULA](Legal/EULA.md)\n", "utf-8")

    _run_main(tmp_path, "Export")

    result = (folder / "Legal" / "Legal.md").read_text("utf-8")
    # From Legal/Legal.md, EULA.md is a sibling — should be just EULA.md
    assert "./EULA.md" in result
    assert "Legal/EULA.md" not in result


def test_consolidate_fixes_links_when_both_files_moved(tmp_path):
    """Both the linking file AND the link target are moved in the same run.

    Legal.md links to Legal/EULA.md. Both move:
      Legal.md        → Legal/Legal.md
      Legal/EULA.md   → Legal/EULA/EULA.md
    From Legal/Legal.md the correct link is ./EULA/EULA.md.
    """
    folder = tmp_path / "Export"
    folder.mkdir()

    sub = folder / "Legal"
    sub.mkdir()
    eula_sub = sub / "EULA"
    eula_sub.mkdir()
    (sub / "EULA.md").write_text("# EULA\n", "utf-8")

    index = folder / "Legal.md"
    index.write_text("[EULA](Legal/EULA.md)\n", "utf-8")

    _run_main(tmp_path, "Export")

    result = (folder / "Legal" / "Legal.md").read_text("utf-8")
    assert "./EULA/EULA.md" in result
    assert "Legal/EULA.md" not in result
