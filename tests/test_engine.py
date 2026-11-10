"""Engine tests for a11y-audit-forge. Run with: python3 -m unittest discover tests"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.audit import analyze
from engine.dom import parse_html
from engine.exports import to_markdown
from engine.names import accessible_name
from engine.rules import AXES, PROFILES, RULES
from engine.samples import SAMPLES, SAMPLES_BY_ID


def rules_fired(result):
    return set(finding["rule"] for finding in result["findings"])


class DomTests(unittest.TestCase):
    def test_parses_document_structure(self):
        doc = parse_html(
            "<!DOCTYPE html><html lang=\"en\"><head>"
            "<title>Hi</title></head><body><p>Hello</p></body></html>")
        self.assertIsNotNone(doc.html())
        self.assertEqual(doc.title(), "Hi")
        self.assertIsNotNone(doc.body())
        self.assertEqual(doc.body().text_content().strip(), "Hello")

    def test_implied_closing_of_list_items(self):
        doc = parse_html("<ul><li>one<li>two</ul>")
        self.assertEqual(len(doc.root.find_all("li")), 2)

    def test_void_elements_do_not_swallow_siblings(self):
        doc = parse_html("<div><img src=\"a.png\"><p>text</p></div>")
        self.assertEqual(len(doc.root.find_all("p")), 1)

    def test_attribute_names_are_case_insensitive_for_lookup(self):
        doc = parse_html("<div ID=\"x\" data-Foo=\"1\"></div>")
        node = doc.root.elements().__next__()
        self.assertEqual(node.attrs.get("id"), "x")
        self.assertEqual(node.attrs.get("data-foo"), "1")


class NameTests(unittest.TestCase):
    def test_label_for_gives_the_name(self):
        doc = parse_html("<label for=\"e\">Email</label><input id=\"e\">")
        node = doc.root.find_all("input")[0]
        name, source = accessible_name(node, doc)
        self.assertEqual(name, "Email")
        self.assertEqual(source, "label")

    def test_aria_label_wins(self):
        doc = parse_html("<input id=\"e\" aria-label=\"Your email\">")
        node = doc.root.find_all("input")[0]
        name, source = accessible_name(node, doc)
        self.assertEqual(name, "Your email")
        self.assertEqual(source, "aria-label")

    def test_aria_labelledby_resolves_the_reference(self):
        doc = parse_html("<h2 id=\"t\">Heading</h2>"
                         "<button aria-labelledby=\"t\"></button>")
        node = doc.root.find_all("button")[0]
        name, source = accessible_name(node, doc)
        self.assertEqual(name, "Heading")
        self.assertEqual(source, "aria-labelledby")

    def test_img_alt_is_the_name(self):
        doc = parse_html("<img src=\"a.png\" alt=\"A cat\">")
        node = doc.root.find_all("img")[0]
        self.assertEqual(accessible_name(node, doc)[0], "A cat")

    def test_button_text_is_the_name(self):
        doc = parse_html("<button>Save</button>")
        node = doc.root.find_all("button")[0]
        self.assertEqual(accessible_name(node, doc)[0], "Save")

    def test_unnamed_control_has_no_name(self):
        doc = parse_html("<input type=\"text\">")
        node = doc.root.find_all("input")[0]
        name, source = accessible_name(node, doc)
        self.assertEqual(name, "")
        self.assertIsNone(source)


class RuleTests(unittest.TestCase):
    def test_clean_page_has_no_findings(self):
        result = analyze(SAMPLES_BY_ID["clean_landing"]["html"],
                         profile="marketing")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["verdict"], "audit_ready")

    def test_missing_language_is_critical(self):
        result = analyze("<html><body><p>hi</p></body></html>")
        self.assertIn("html-missing-lang", rules_fired(result))
        severity = [f["severity"] for f in result["findings"]
                    if f["rule"] == "html-missing-lang"][0]
        self.assertEqual(severity, "critical")

    def test_valid_language_is_accepted(self):
        result = analyze("<html lang=\"en-GB\"><body><p>hi</p></body></html>")
        self.assertNotIn("html-invalid-lang", rules_fired(result))

    def test_placeholder_only_field_is_flagged(self):
        result = analyze("<html lang=\"en\"><body><form>"
                         "<input type=\"email\" placeholder=\"Email\">"
                         "</form></body></html>")
        self.assertIn("placeholder-as-label", rules_fired(result))

    def test_missing_alt_is_critical(self):
        result = analyze("<html lang=\"en\"><body><img src=\"a.png\">"
                         "</body></html>")
        self.assertIn("img-missing-alt", rules_fired(result))

    def test_decorative_alt_is_accepted(self):
        result = analyze("<html lang=\"en\"><body><img src=\"a.png\" alt=\"\">"
                         "</body></html>")
        self.assertNotIn("img-missing-alt", rules_fired(result))

    def test_broken_aria_reference_is_critical(self):
        result = analyze("<html lang=\"en\"><body><div role=\"region\" "
                         "aria-labelledby=\"nope\">x</div></body></html>")
        self.assertIn("aria-ref-missing", rules_fired(result))

    def test_aria_hidden_focusable_is_critical(self):
        result = analyze("<html lang=\"en\"><body><button aria-hidden=\"true\">"
                         "Go</button></body></html>")
        self.assertIn("aria-hidden-focusable", rules_fired(result))

    def test_duplicate_ids_are_flagged(self):
        result = analyze("<html lang=\"en\"><body>"
                         "<input id=\"a\"><input id=\"a\"></body></html>")
        self.assertIn("duplicate-id", rules_fired(result))

    def test_positive_tabindex_is_flagged(self):
        result = analyze("<html lang=\"en\"><body><a href=\"/a\" tabindex=\"3\">"
                         "A</a></body></html>")
        self.assertIn("positive-tabindex", rules_fired(result))

    def test_viewport_zoom_block_is_flagged(self):
        result = analyze("<html lang=\"en\"><head><meta name=\"viewport\" "
                         "content=\"width=device-width, user-scalable=no\">"
                         "<title>x</title></head><body></body></html>")
        self.assertIn("viewport-blocks-zoom", rules_fired(result))

    def test_autoplay_and_captions(self):
        result = analyze(SAMPLES_BY_ID["media_player"]["html"])
        fired = rules_fired(result)
        self.assertIn("autoplay-media", fired)
        self.assertIn("video-no-captions", fired)
        self.assertIn("iframe-no-title", fired)
        self.assertIn("no-reduced-motion", fired)

    def test_radio_group_needs_a_fieldset(self):
        result = analyze(SAMPLES_BY_ID["signup_form"]["html"])
        self.assertIn("radio-without-group", rules_fired(result))

    def test_table_without_headers_is_flagged(self):
        result = analyze(SAMPLES_BY_ID["dashboard"]["html"])
        self.assertIn("table-missing-header", rules_fired(result))

    def test_list_structure_is_flagged(self):
        result = analyze(SAMPLES_BY_ID["aria_mess"]["html"])
        self.assertIn("list-structure", rules_fired(result))


class ScoringTests(unittest.TestCase):
    def test_every_sample_scores_below_the_clean_page(self):
        clean = analyze(SAMPLES_BY_ID["clean_landing"]["html"],
                        profile="marketing")["score"]
        for sample in SAMPLES:
            if sample["id"] == "clean_landing":
                continue
            score = analyze(sample["html"], profile=sample["profile"])["score"]
            self.assertLess(score, clean, sample["id"])

    def test_critical_findings_cap_the_score(self):
        result = analyze(SAMPLES_BY_ID["signup_form"]["html"])
        self.assertTrue(result["caps"])
        self.assertLessEqual(result["score"], 55)

    def test_axis_scores_are_in_range(self):
        result = analyze(SAMPLES_BY_ID["broken_nav"]["html"])
        for axis in AXES:
            self.assertIn(axis, result["axis_scores"])
            self.assertGreaterEqual(result["axis_scores"][axis], 0)
            self.assertLessEqual(result["axis_scores"][axis], 100)

    def test_weights_are_used_for_the_overall_score(self):
        result = analyze(SAMPLES_BY_ID["signup_form"]["html"], profile="general")
        self.assertAlmostEqual(sum(result["weights"].values()), 1.0, places=6)
        self.assertIn(result["profile"], PROFILES)

    def test_fix_plan_ends_at_a_clean_score(self):
        result = analyze(SAMPLES_BY_ID["clean_landing"]["html"])
        self.assertEqual(result["fix_plan"], [])

    def test_fix_plan_gains_are_not_negative(self):
        result = analyze(SAMPLES_BY_ID["broken_nav"]["html"])
        for step in result["fix_plan"]:
            self.assertGreaterEqual(step["gain"], 0)
            self.assertGreaterEqual(step["score_after"], step["score_before"])

    def test_broken_page_improves_as_you_fix_it(self):
        result = analyze(SAMPLES_BY_ID["dashboard"]["html"])
        self.assertGreater(result["fix_plan"][-1]["score_after"],
                           result["score"])


class OutputTests(unittest.TestCase):
    def test_annotated_markup_contains_fix_comments(self):
        result = analyze(SAMPLES_BY_ID["signup_form"]["html"])
        self.assertIn("a11y-fix", result["annotated_markup"])

    def test_focus_order_lists_positive_tabindex_first(self):
        result = analyze(SAMPLES_BY_ID["broken_nav"]["html"])
        order = result["focus_order"]
        self.assertTrue(order)
        positives = [entry for entry in order if entry["tabindex"] > 0]
        if positives:
            self.assertEqual(order[0]["tabindex"], positives[0]["tabindex"])

    def test_name_map_reports_the_source(self):
        result = analyze(SAMPLES_BY_ID["clean_landing"]["html"])
        sources = set(entry["source"] for entry in result["name_map"])
        self.assertIn("content", sources)

    def test_wcag_coverage_is_listed(self):
        result = analyze(SAMPLES_BY_ID["dashboard"]["html"])
        codes = set(row["code"] for row in result["wcag_coverage"])
        self.assertIn("1.1.1", codes)
        self.assertIn("4.1.2", codes)

    def test_markdown_export_mentions_the_score(self):
        result = analyze(SAMPLES_BY_ID["clean_landing"]["html"])
        markdown = to_markdown(result)
        self.assertIn("Accessibility audit", markdown)
        self.assertIn("Score", markdown)

    def test_every_rule_has_the_required_metadata(self):
        for name, rule in RULES.items():
            self.assertIn(rule["axis"], AXES, name)
            self.assertIn(rule["severity"],
                          ("critical", "high", "medium", "low"), name)
            self.assertTrue(rule["title"], name)
            self.assertTrue(rule["why"], name)
            self.assertTrue(rule["fix"], name)


if __name__ == "__main__":
    unittest.main()
