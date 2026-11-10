"""a11y-audit-forge - local-first accessibility audit workbench.

Flask + SQLite + vanilla JS. No API keys, no network calls, no LLM.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, request, send_from_directory

from engine.audit import analyze
from engine.exports import to_json, to_markdown
from engine.rules import AXES, AXIS_LABELS, PROFILES, RULES, WCAG_CRITERIA
from engine.samples import get_sample, sample_list

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("A11Y_DB", os.path.join(BASE_DIR, "a11y.db"))

app = Flask(__name__, static_folder="static", static_url_path="/static")


# ------------------------------------------------------------------ database
def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_name TEXT NOT NULL DEFAULT '',
            profile TEXT NOT NULL DEFAULT 'general',
            page_title TEXT NOT NULL DEFAULT '',
            score REAL NOT NULL DEFAULT 0,
            verdict TEXT NOT NULL DEFAULT '',
            finding_count INTEGER NOT NULL DEFAULT 0,
            rating INTEGER,
            notes TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    connection.commit()
    connection.close()


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def save_session(result, source_name):
    connection = get_db()
    cursor = connection.execute(
        """
        INSERT INTO sessions (created_at, source_name, profile, page_title,
                              score, verdict, finding_count, payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now_iso(), source_name or "", result["profile"],
         result.get("page_title") or "", result["score"], result["verdict"],
         result["finding_count"], json.dumps(result)),
    )
    connection.commit()
    session_id = cursor.lastrowid
    connection.close()
    return session_id


def session_row(session_id):
    connection = get_db()
    row = connection.execute("SELECT * FROM sessions WHERE id = ?",
                             (session_id,)).fetchone()
    connection.close()
    return row


def session_summary(row):
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "source_name": row["source_name"],
        "profile": row["profile"],
        "page_title": row["page_title"],
        "score": row["score"],
        "verdict": row["verdict"],
        "finding_count": row["finding_count"],
        "rating": row["rating"],
        "notes": row["notes"],
    }


# --------------------------------------------------------------------- routes
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "a11y-audit-forge",
        "rules": len(RULES),
        "axes": AXES,
        "wcag_criteria": len(WCAG_CRITERIA),
        "time": now_iso(),
    })


@app.route("/api/profiles")
def profiles():
    return jsonify({
        "profiles": [
            {"id": key, "label": value["label"], "weights": value["weights"]}
            for key, value in PROFILES.items()
        ],
        "axes": [{"id": axis, "label": AXIS_LABELS[axis]} for axis in AXES],
        "rule_count": len(RULES),
    })


@app.route("/api/samples")
def samples():
    return jsonify({"samples": sample_list()})


@app.route("/api/sample")
def sample():
    sample_id = request.args.get("id", "")
    found = get_sample(sample_id)
    if not found:
        return jsonify({"error": "unknown sample"}), 404
    return jsonify(found)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    payload = request.get_json(silent=True) or {}
    markup = payload.get("html") or ""
    profile = payload.get("profile") or "general"
    source_name = payload.get("source_name") or ""
    if profile not in PROFILES:
        profile = "general"
    if not isinstance(markup, str) or not markup.strip():
        return jsonify({"error": "paste some markup first"}), 400

    result = analyze(markup, profile=profile, source_name=source_name)
    if payload.get("save"):
        result["session_id"] = save_session(result, source_name)
    return jsonify(result)


@app.route("/api/sessions")
def sessions():
    limit = min(int(request.args.get("limit", 40)), 200)
    connection = get_db()
    rows = connection.execute(
        "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    connection.close()
    return jsonify({"sessions": [session_summary(row) for row in rows]})


@app.route("/api/sessions/<int:session_id>")
def get_session(session_id):
    row = session_row(session_id)
    if row is None:
        return jsonify({"error": "not found"}), 404
    result = json.loads(row["payload"])
    result["session"] = session_summary(row)
    return jsonify(result)


@app.route("/api/sessions/<int:session_id>", methods=["PATCH"])
def patch_session(session_id):
    row = session_row(session_id)
    if row is None:
        return jsonify({"error": "not found"}), 404
    payload = request.get_json(silent=True) or {}
    rating = payload.get("rating", row["rating"])
    notes = payload.get("notes", row["notes"])
    if rating is not None:
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = None
        if rating is not None and not 1 <= rating <= 5:
            rating = None
    connection = get_db()
    connection.execute(
        "UPDATE sessions SET rating = ?, notes = ? WHERE id = ?",
        (rating, notes or "", session_id),
    )
    connection.commit()
    connection.close()
    updated = session_row(session_id)
    return jsonify({"session": session_summary(updated)})


@app.route("/api/export/<int:session_id>")
def export_session(session_id):
    row = session_row(session_id)
    if row is None:
        return jsonify({"error": "not found"}), 404
    result = json.loads(row["payload"])
    fmt = (request.args.get("fmt") or "md").lower()
    stem = "a11y-audit-%s" % session_id
    if fmt == "json":
        body = to_json(result)
        mimetype = "application/json"
        filename = stem + ".json"
    else:
        body = to_markdown(result)
        mimetype = "text/markdown"
        filename = stem + ".md"
    return Response(
        body,
        mimetype=mimetype,
        headers={"Content-Disposition": "attachment; filename=%s" % filename},
    )


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "not found"}), 404


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    app.run(host="127.0.0.1", port=port, debug=False)
