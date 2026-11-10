"""API tests for a11y-audit-forge. Run with: python3 -m unittest discover tests"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEMP_DB = os.path.join(tempfile.mkdtemp(prefix="a11y-test-"), "test.db")
os.environ["A11Y_DB"] = TEMP_DB

import app as server  # noqa: E402
from engine.samples import SAMPLES_BY_ID  # noqa: E402


class ApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "ok")
        self.assertGreater(body["rules"], 40)

    def test_index_page_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"a11y", response.data.lower())

    def test_profiles(self):
        body = self.client.get("/api/profiles").get_json()
        self.assertIn("general", [p["id"] for p in body["profiles"]])
        self.assertEqual(len(body["axes"]), 5)

    def test_samples_listing(self):
        body = self.client.get("/api/samples").get_json()
        self.assertEqual(len(body["samples"]), len(SAMPLES_BY_ID))

    def test_sample_fetch(self):
        body = self.client.get("/api/sample?id=clean_landing").get_json()
        self.assertIn("<html", body["html"])

    def test_unknown_sample_is_404(self):
        self.assertEqual(self.client.get("/api/sample?id=nope").status_code, 404)

    def test_analyze_returns_a_score(self):
        response = self.client.post("/api/analyze", json={
            "html": SAMPLES_BY_ID["signup_form"]["html"],
            "profile": "form_heavy",
        })
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("score", body)
        self.assertIn("findings", body)
        self.assertIn("fix_plan", body)
        self.assertIn("focus_order", body)
        self.assertEqual(body["profile"], "form_heavy")

    def test_analyze_rejects_empty_markup(self):
        response = self.client.post("/api/analyze", json={"html": "  "})
        self.assertEqual(response.status_code, 400)

    def test_unknown_profile_falls_back(self):
        response = self.client.post("/api/analyze", json={
            "html": "<html lang='en'><body></body></html>",
            "profile": "nonsense",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["profile"], "general")

    def test_session_lifecycle(self):
        response = self.client.post("/api/analyze", json={
            "html": SAMPLES_BY_ID["dashboard"]["html"],
            "source_name": "dashboard.html",
            "save": True,
        })
        body = response.get_json()
        session_id = body.get("session_id")
        self.assertIsNotNone(session_id)

        listing = self.client.get("/api/sessions").get_json()
        self.assertTrue(listing["sessions"])

        detail = self.client.get("/api/sessions/%d" % session_id).get_json()
        self.assertEqual(detail["session"]["source_name"], "dashboard.html")

        patched = self.client.patch("/api/sessions/%d" % session_id, json={
            "rating": 4, "notes": "fix the table headers first"})
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.get_json()["session"]["rating"], 4)

        markdown = self.client.get("/api/export/%d?fmt=md" % session_id)
        self.assertEqual(markdown.status_code, 200)
        self.assertIn(b"Accessibility audit", markdown.data)
        self.assertIn("attachment", markdown.headers["Content-Disposition"])

        export = self.client.get("/api/export/%d?fmt=json" % session_id)
        self.assertEqual(export.status_code, 200)
        payload = json.loads(export.data.decode("utf-8"))
        self.assertIn("axis_scores", payload)

    def test_rating_out_of_range_is_dropped(self):
        response = self.client.post("/api/analyze", json={
            "html": "<html lang='en'><body></body></html>", "save": True})
        session_id = response.get_json()["session_id"]
        patched = self.client.patch("/api/sessions/%d" % session_id,
                                    json={"rating": 9})
        self.assertIsNone(patched.get_json()["session"]["rating"])

    def test_missing_session_is_404(self):
        self.assertEqual(self.client.get("/api/sessions/99999").status_code, 404)

    def test_frontend_and_backend_agree_on_field_names(self):
        body = self.client.post("/api/analyze", json={
            "html": SAMPLES_BY_ID["clean_landing"]["html"]}).get_json()
        for field in ("score", "verdict", "verdict_label", "axis_scores",
                      "axis_labels", "counts", "findings", "fix_plan",
                      "name_map", "focus_order", "wcag_coverage",
                      "annotated_markup", "caps", "weights"):
            self.assertIn(field, body)


if __name__ == "__main__":
    unittest.main()
