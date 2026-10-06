"""Tests for strip_uuids.py — see tests/README.md for how to run."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from strip_uuids import (
    _GENERIC_NOTION_RE,
    _clean_name,
    _clean_path_parts,
    _fix_empty_bullets,
    _fix_image_blank_lines,
    _fix_media_embeds,
    _sanitize_stem,
    _strip_uuid,
    _update_links,
)
import strip_uuids as _su_module

UUID = "a" * 32  # 32-char hex string used throughout


# ── _strip_uuid ──────────────────────────────────────────────────────────────


def test_strip_uuid_from_md():
    # The regex matches " UUID" (space + 32 hex), so the space is stripped too
    assert _strip_uuid(f"My Page {UUID}.md") == "My Page.md"


def test_strip_uuid_from_folder():
    assert _strip_uuid(f"My Folder {UUID}") == "My Folder"


def test_strip_uuid_all_suffix():
    # Space before UUID is consumed, so the space before _all is gone too
    assert _strip_uuid(f"Export {UUID}_all.csv") == "Export_all.csv"


def test_strip_uuid_leaves_non_uuid():
    assert _strip_uuid("Normal File.md") == "Normal File.md"


def test_strip_uuid_uppercase():
    upper = "A" * 32
    assert _strip_uuid(f"Page {upper}.md") == "Page.md"


# ── _sanitize_stem ───────────────────────────────────────────────────────────


# Space is deliberately NOT in _UNSAFE_CHARS_RE — it's safe in filenames.
@pytest.mark.parametrize("char", list('#|^:%[]()*"\\<>?'))
def test_sanitize_removes_unsafe(char):
    assert char not in _sanitize_stem(f"file{char}name")


def test_sanitize_collapses_double_spaces():
    assert _sanitize_stem("foo  bar") == "foo bar"


def test_sanitize_never_returns_empty():
    # If all chars are unsafe, return original stem
    assert _sanitize_stem("###") == "###"


def test_sanitize_normal_stem_unchanged():
    assert _sanitize_stem("Normal Page") == "Normal Page"


# ── _clean_name ──────────────────────────────────────────────────────────────


def test_clean_name_strips_uuid_and_ext():
    result = _clean_name(f"My Page {UUID}.md")
    assert result == "My Page.md"


def test_clean_name_removes_unsafe_char():
    result = _clean_name("File #1.md")
    assert result == "File 1.md"


def test_clean_name_uuid_and_unsafe():
    result = _clean_name(f"File #1 {UUID}.md")
    assert result == "File 1.md"


def test_clean_name_no_change():
    assert _clean_name("Normal.md") == "Normal.md"


# ── _clean_path_parts ────────────────────────────────────────────────────────


def test_clean_path_strips_uuid_in_href():
    href = f"Folder%20{UUID}/Page%20{UUID}.md"
    cleaned, changed = _clean_path_parts(href)
    assert UUID not in cleaned
    assert changed


def test_clean_path_decodes_over_encoded():
    # %27 = apostrophe — should become literal '
    href = "Folder/Don%27t%20Touch.md"
    cleaned, changed = _clean_path_parts(href)
    assert "Don't%20Touch.md" in cleaned
    assert changed


def test_clean_path_keeps_spaces_as_percent20():
    href = "My Folder/My File.md"
    cleaned, _ = _clean_path_parts(href)
    assert "My%20Folder/My%20File.md" == cleaned


def test_clean_path_no_uuid_no_unsafe_unchanged():
    href = "Folder/File.md"
    cleaned, changed = _clean_path_parts(href)
    assert cleaned == "Folder/File.md"
    assert not changed


# ── _update_links — URL scheme passthrough ───────────────────────────────────


def _update(content, tmp_path):
    md = tmp_path / "note.md"
    return _update_links(content, md, tmp_path, {})


def test_mailto_left_unchanged(tmp_path):
    src = "[email me](mailto:foo@example.com)"
    assert _update(src, tmp_path) == src


def test_tel_left_unchanged(tmp_path):
    src = "[call](tel:+15551234567)"
    assert _update(src, tmp_path) == src


def test_obsidian_url_left_unchanged(tmp_path):
    src = "[open](obsidian://open?vault=MyVault&file=Note)"
    assert _update(src, tmp_path) == src


def test_external_http_left_unchanged(tmp_path):
    src = "[site](https://example.com/page)"
    assert _update(src, tmp_path) == src


# ── _update_links — Notion page URL → relative link ─────────────────────────


def test_notion_page_url_converted(tmp_path):
    target = tmp_path / "Page.md"
    target.write_text("", "utf-8")
    uuid_to_new = {UUID: target}
    md = tmp_path / "note.md"
    src = f"[Page](https://notion.so/workspace/PageTitle-{UUID})"
    result = _update_links(src, md, tmp_path, uuid_to_new)
    assert result == "[Page](./Page.md)"


def test_notion_page_url_unknown_uuid_unchanged(tmp_path):
    md = tmp_path / "note.md"
    src = f"[Page](https://notion.so/workspace/PageTitle-{UUID})"
    result = _update_links(src, md, tmp_path, {})
    assert result == src


# ── _update_links — vault-root-absolute link ─────────────────────────────────


def test_vault_root_absolute_rewritten(tmp_path):
    # target exists at vault root but not relative to the nested md file
    target = tmp_path / "Notes" / "page.md"
    target.parent.mkdir()
    target.write_text("", "utf-8")

    sub = tmp_path / "other"
    sub.mkdir()
    md = sub / "note.md"

    # href "Notes/page.md" resolves from vault root but not from sub/
    src = "[page](Notes/page.md)"
    result = _update_links(src, md, tmp_path, {})
    assert result == "[page](../Notes/page.md)"


# ── _update_links — internal href with UUID cleaned ─────────────────────────


def test_internal_uuid_href_cleaned(tmp_path):
    md = tmp_path / "note.md"
    src = f"[page](My%20Page%20{UUID}.md)"
    result = _update_links(src, md, tmp_path, {})
    assert UUID not in result
    assert "[page](./My%20Page.md)" == result


# ── Integration: recursive rename (previously shallow-only bug) ──────────────


def _run_main(vault: Path, folder_name: str) -> None:
    """Run strip_uuids main() with the given vault and folder."""
    import argparse

    orig_parse = argparse.ArgumentParser.parse_args

    def patched_parse(self, args=None, namespace=None):
        return orig_parse(self, ["--vault", str(vault), "--folder", folder_name])

    argparse.ArgumentParser.parse_args = patched_parse
    try:
        _su_module.main()
    finally:
        argparse.ArgumentParser.parse_args = orig_parse


def test_recursive_rename_renames_nested_files(tmp_path):
    """Files in subdirectories must have UUIDs stripped (not just top-level)."""
    folder = tmp_path / "Export"
    folder.mkdir()

    # Top-level file
    (folder / f"Page A {UUID}.md").write_text("", "utf-8")
    # Subdirectory
    subdir = folder / f"Page A {UUID}"
    subdir.mkdir()
    # Nested file inside the subdir
    nested_uuid = "b" * 32
    (subdir / f"SubPage {nested_uuid}.md").write_text("", "utf-8")

    _run_main(tmp_path, "Export")

    # Top-level file renamed
    assert (folder / "Page A.md").exists()
    assert not (folder / f"Page A {UUID}.md").exists()

    # Subdirectory renamed
    new_subdir = folder / "Page A"
    assert new_subdir.is_dir()

    # Nested file renamed (the bug: this was NOT happening before the fix)
    assert (new_subdir / "SubPage.md").exists()
    assert not (new_subdir / f"SubPage {nested_uuid}.md").exists()


def test_recursive_rename_updates_notion_url_for_nested_file(tmp_path):
    """uuid_to_new must track the final path after parent dir is also renamed."""
    folder = tmp_path / "Export"
    folder.mkdir()

    nested_uuid = "c" * 32
    subdir = folder / f"Parent {UUID}"
    subdir.mkdir()
    nested_file = subdir / f"Child {nested_uuid}.md"
    nested_file.write_text("", "utf-8")

    # Index file referencing the nested file via Notion URL
    index = folder / "index.md"
    index.write_text(
        f"[Child](https://notion.so/workspace/Child-{nested_uuid})\n", "utf-8"
    )

    _run_main(tmp_path, "Export")

    # After rename: Parent UUID/ → Parent/, Child UUID.md → Child.md
    result = (folder / "index.md").read_text("utf-8")
    # Link should point to the new relative path: Parent/Child.md
    assert "Parent/Child.md" in result
    assert nested_uuid not in result


# ── _GENERIC_NOTION_RE — generic Notion links stripped ───────────────────────


def test_generic_notion_homepage_stripped():
    result = _GENERIC_NOTION_RE.sub("", "[Notion](https://notion.so)")
    assert result == ""


def test_generic_notion_www_stripped():
    result = _GENERIC_NOTION_RE.sub("", "[Notion](https://www.notion.so)")
    assert result == ""


def test_generic_notion_help_stripped():
    result = _GENERIC_NOTION_RE.sub("", "[Help](https://notion.so/help/some-article)")
    assert result == ""


def test_generic_notion_blog_stripped():
    result = _GENERIC_NOTION_RE.sub("", "[Blog](https://notion.so/blog/post)")
    assert result == ""


def test_generic_notion_image_stripped():
    result = _GENERIC_NOTION_RE.sub("", "![logo](https://notion.so)")
    assert result == ""


def test_generic_notion_page_uuid_not_stripped():
    # A Notion page URL with a UUID must NOT be stripped by this regex (handled by _NOTION_PAGE_RE)
    src = f"[Page](https://notion.so/workspace/Title-{UUID})"
    result = _GENERIC_NOTION_RE.sub("", src)
    assert result == src


# ── _update_links — anchor fragment links ────────────────────────────────────


def test_anchor_fragment_gets_dot_slash(tmp_path):
    # '#' is in _UNSAFE_CHARS_RE but survives in hrefs (it's an anchor, not a filename char)
    # The link also gets the './' prefix for clarity
    src = "[section](page.md#heading)"
    assert _update(src, tmp_path) == "[section](./page.md#heading)"


def test_anchor_fragment_with_uuid_href_cleaned(tmp_path):
    # UUID stripped but anchor preserved
    src = f"[section](My%20Page%20{UUID}.md#heading)"
    result = _update(src, tmp_path)
    assert UUID not in result
    assert "#heading" in result


# ── _update_links — image links with UUID in strip_uuids ─────────────────────


def test_image_link_uuid_stripped(tmp_path):
    src = f"![screenshot](My%20Image%20{UUID}.png)"
    result = _update(src, tmp_path)
    assert UUID not in result
    assert "![screenshot](./My%20Image.png)" == result


def test_image_bang_preserved_through_uuid_strip(tmp_path):
    # ! must survive link rewriting — regression guard for accidental stripping
    src = f"![demo.mp4](demo%20{UUID}.mp4)"
    result = _update(src, tmp_path)
    assert result.startswith("!["), f"! was stripped: {result!r}"


def test_plain_link_to_media_not_given_bang(tmp_path):
    # Notion exports video blocks as [name.mp4](path) without !
    # The skill must NOT add ! during link rewriting — that's a separate pass
    src = f"[demo.mp4](demo%20{UUID}.mp4)"
    result = _update(src, tmp_path)
    assert not result.startswith("!["), f"! was wrongly added: {result!r}"


# ── _fix_image_blank_lines ────────────────────────────────────────────────────


def test_blank_line_before_indented_image_removed():
    src = "- item\n        \n        ![img](img.png)"
    assert _fix_image_blank_lines(src) == "- item\n        ![img](img.png)"


def test_empty_line_before_indented_image_removed():
    src = "- item\n\n        ![img](img.png)"
    assert _fix_image_blank_lines(src) == "- item\n        ![img](img.png)"


def test_blank_line_before_non_image_untouched():
    src = "- item\n\n    some text"
    assert _fix_image_blank_lines(src) == src


def test_blank_line_before_shallow_image_untouched():
    # Fewer than 5 leading spaces — not a problematic case
    src = "- item\n\n    ![img](img.png)"
    assert _fix_image_blank_lines(src) == src


def test_no_blank_line_before_image_untouched():
    src = "- item\n        ![img](img.png)"
    assert _fix_image_blank_lines(src) == src


# ── _fix_empty_bullets ───────────────────────────────────────────────────────


def test_empty_bullet_removed():
    src = "- item\n    - \n- next"
    assert _fix_empty_bullets(src) == "- item\n\n- next"


def test_empty_bullet_no_space_removed():
    src = "- item\n-\n- next"
    assert _fix_empty_bullets(src) == "- item\n\n- next"


def test_bullet_with_content_untouched():
    src = "- item\n- content"
    assert _fix_empty_bullets(src) == src


# ── _fix_media_embeds ─────────────────────────────────────────────────────────


def test_mp4_link_gets_bang():
    # Notion exports video blocks without ! — the skill must add it
    assert _fix_media_embeds("[demo.mp4](./demo.mp4)") == "![demo.mp4](./demo.mp4)"


def test_mov_link_gets_bang():
    assert _fix_media_embeds("[clip.mov](./clip.mov)") == "![clip.mov](./clip.mov)"


def test_already_bang_unchanged():
    src = "![demo.mp4](./demo.mp4)"
    assert _fix_media_embeds(src) == src


def test_non_media_link_unchanged():
    src = "[page.md](./page.md)"
    assert _fix_media_embeds(src) == src


def test_external_video_link_unchanged():
    # External URLs are left as plain links — only local media embeds get !
    src = "[watch](https://youtube.com/watch?v=abc)"
    assert _fix_media_embeds(src) == src
