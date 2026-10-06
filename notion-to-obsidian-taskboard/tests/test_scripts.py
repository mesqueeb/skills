"""Lightweight tests for notion-to-obsidian-taskboard scripts — see conftest.py for path setup."""

import unittest

from common import (
    fuzzy_title_match,
    get_body,
    get_h1_title,
    normalize,
    parse_frontmatter,
    render_frontmatter,
)
from convert import STATUS_ORDER, _slugify, _tags_for_task, status_sort_key


# ── common.normalize ─────────────────────────────────────────────────────────


class TestNormalize(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(normalize("foo  bar"), "foo bar")

    def test_replaces_nbsp(self):
        self.assertEqual(normalize("foo\xa0bar"), "foo bar")

    def test_strips_leading_trailing(self):
        self.assertEqual(normalize("  hello  "), "hello")


# ── common.fuzzy_title_match ─────────────────────────────────────────────────


class TestFuzzyTitleMatch(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(fuzzy_title_match("Fix the bug", "Fix the bug"))

    def test_normalised_whitespace(self):
        self.assertTrue(fuzzy_title_match("Fix  the bug", "Fix the bug"))

    def test_notion_blocked_chars_stripped(self):
        # Notion strips : / \ ? * " < > | ! from filenames
        self.assertTrue(fuzzy_title_match("Fix: My Bug!", "Fix My Bug"))

    def test_prefix_match_long_enough(self):
        long = "a" * 50 + " extra words"
        self.assertTrue(fuzzy_title_match("a" * 50, long))

    def test_prefix_match_too_short(self):
        # Titles shorter than min_prefix=40 must match exactly — not prefix
        self.assertFalse(
            fuzzy_title_match("Short title", "Short title with more words")
        )

    def test_completely_different(self):
        self.assertFalse(fuzzy_title_match("Fix login bug", "Add dark mode"))

    def test_curly_apostrophe_normalised(self):
        self.assertTrue(fuzzy_title_match("Won\u2019t do", "Won't do"))


# ── common.parse_frontmatter / render_frontmatter ────────────────────────────


class TestFrontmatter(unittest.TestCase):
    def test_parse_basic(self):
        content = "---\nstatus: todo\nlabels: urgent\n---\n# My Task\n"
        fm, body = parse_frontmatter(content)
        self.assertEqual(fm["status"], "todo")
        self.assertEqual(fm["labels"], "urgent")
        self.assertIn("# My Task", body)

    def test_parse_empty(self):
        fm, body = parse_frontmatter("# No frontmatter\n")
        self.assertEqual(fm, {})
        self.assertIn("# No frontmatter", body)

    def test_roundtrip(self):
        fm = {"status": "in-progress", "project": "myapp"}
        body = "# Task\nsome content\n"
        rendered = render_frontmatter(fm, body)
        fm2, body2 = parse_frontmatter(rendered)
        self.assertEqual(fm2["status"], "in-progress")
        self.assertEqual(fm2["project"], "myapp")
        self.assertEqual(body2, body)

    def test_render_empty_fm_returns_body(self):
        self.assertEqual(render_frontmatter({}, "just body"), "just body")


# ── common.get_h1_title / get_body ───────────────────────────────────────────


class TestH1AndBody(unittest.TestCase):
    def test_get_h1_title(self):
        self.assertEqual(get_h1_title("# My Task\nsome body"), "My Task")

    def test_get_h1_title_missing(self):
        self.assertIsNone(get_h1_title("no heading here"))

    def test_get_body_strips_frontmatter_and_h1(self):
        content = "---\nstatus: todo\n---\n# My Task\nActual body here."
        self.assertEqual(get_body(content), "Actual body here.")


# ── convert._slugify ─────────────────────────────────────────────────────────


class TestSlugify(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(_slugify("High Priority"), "high-priority")

    def test_spaces_to_hyphens(self):
        self.assertEqual(_slugify("nice to have"), "nice-to-have")

    def test_dots_removed(self):
        self.assertEqual(_slugify("p.o.c."), "poc")

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(_slugify("  bug  "), "bug")


# ── convert._tags_for_task ───────────────────────────────────────────────────


class TestTagsForTask(unittest.TestCase):
    def test_labels_produce_flat_tags(self):
        tags = _tags_for_task({"labels": "urgent"})
        self.assertIn("#urgent", tags)
        self.assertNotIn("#labels/urgent", tags)

    def test_other_keys_produce_nested_tags(self):
        tags = _tags_for_task({"project": "myapp"})
        self.assertIn("#project/myapp", tags)

    def test_comma_separated_labels(self):
        tags = _tags_for_task({"labels": "urgent, nice-to-have"})
        self.assertIn("#urgent", tags)
        self.assertIn("#nice-to-have", tags)

    def test_skips_structural_keys(self):
        tags = _tags_for_task(
            {"status": "done", "notes": "Notes/foo.md", "assign": "Alice"}
        )
        self.assertEqual(tags, [])

    def test_skips_empty_values(self):
        tags = _tags_for_task({"project": ""})
        self.assertEqual(tags, [])


# ── convert.status_sort_key ──────────────────────────────────────────────────


class TestStatusSortKey(unittest.TestCase):
    def test_known_order(self):
        statuses = ["done", "todo", "future", "in-progress"]
        sorted_statuses = sorted(statuses, key=lambda s: status_sort_key({"status": s}))
        self.assertEqual(sorted_statuses, ["future", "todo", "in-progress", "done"])

    def test_unknown_status_goes_last(self):
        key = status_sort_key({"status": "mystery"})
        self.assertEqual(key, len(STATUS_ORDER))
