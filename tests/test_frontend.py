"""Frontend contract test.

The UI is vanilla JS, so this checks the two things that actually break:
an element id that the script expects but the page does not have, and a
response field the script reads that the API does not send.
"""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(BASE, "static", "index.html")
JS_PATH = os.path.join(BASE, "static", "app.js")

with open(HTML_PATH, "r", encoding="utf-8") as handle:
    HTML = handle.read()
with open(JS_PATH, "r", encoding="utf-8") as handle:
    JS = handle.read()

HTML_IDS = set(re.findall(r'id="([^"]+)"', HTML))
JS_IDS = set(re.findall(r'el\("([^"]+)"\)', JS))
DYNAMIC_IDS = set(re.findall(r'el\("(tab-|filter)', JS))


class FrontendContractTests(unittest.TestCase):
    def test_every_element_the_script_uses_exists_in_the_page(self):
        missing = sorted(
            name for name in JS_IDS
            if name not in HTML_IDS and not name.startswith(DYNAMIC_PREFIXES)
        )
        self.assertEqual(missing, [])

    def test_the_page_has_the_panels_the_script_switches_between(self):
        for name in ("findings", "fixes", "focus", "names", "wcag", "markup"):
            self.assertIn("tab-" + name, HTML_IDS)

    def test_tabs_are_declared_for_every_panel(self):
        for name in ("findings", "fixes", "focus", "names", "wcag", "markup"):
            self.assertIn('data-tab="%s"' % name, HTML)

    def test_the_api_fields_the_script_reads_are_returned(self):
        import app as server
        from engine.samples import SAMPLES_BY_ID
        client = server.app.test_client()
        body = client.post("/api/analyze", json={
            "html": SAMPLES_BY_ID["dashboard"]["html"],
            "profile": "general",
            "save": True,
        }).get_json()
        for field in ("score", "verdict_label", "axis_scores", "axis_labels",
                      "counts", "caps", "findings", "fix_plan", "focus_order",
                      "name_map", "wcag_coverage", "annotated_markup",
                      "page_title", "profile_label"):
            self.assertIn(field, body)
        for finding in body["findings"]:
            for field in ("rule", "severity", "axis", "axis_label", "wcag",
                          "title", "why", "fix", "path", "evidence"):
                self.assertIn(field, finding)

    def test_the_static_page_is_served(self):
        import app as server
        client = server.app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"a11y", response.data.lower())
        self.assertIn(b"/static/app.js", response.data)


DYNAMIC_PREFIXES = ("tab-",)


if __name__ == "__main__":
    unittest.main()
