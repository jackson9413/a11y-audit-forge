"""Markdown and JSON exports for an audit result."""

import json

from .rules import AXIS_LABELS

SEVERITY_LABEL = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}


def to_markdown(result):
    lines = []
    title = result.get("page_title") or result.get("source_name") or "Untitled page"
    lines.append("# Accessibility audit - %s" % title)
    lines.append("")
    lines.append("**Score: %s / 100** (%s)" % (result["score"],
                                              result["verdict_label"]))
    lines.append("")
    lines.append("Profile: %s | Findings: %d | Critical: %d | High: %d | "
                 "Medium: %d | Low: %d" % (
                     result["profile_label"], result["finding_count"],
                     result["counts"]["critical"], result["counts"]["high"],
                     result["counts"]["medium"], result["counts"]["low"]))
    lines.append("")
    lines.append("## Axis scores")
    lines.append("")
    lines.append("| Axis | Score |")
    lines.append("| --- | --- |")
    for axis, score in result["axis_scores"].items():
        lines.append("| %s | %s |" % (AXIS_LABELS.get(axis, axis), score))
    lines.append("")
    if result.get("caps"):
        lines.append("### Score caps applied")
        lines.append("")
        for cap in result["caps"]:
            lines.append("- Capped at %s because %s." % (cap["cap"],
                                                          cap["reason"]))
        lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not result["findings"]:
        lines.append("No findings. Automated checks never cover everything - "
                     "still test with a keyboard and a real screen reader.")
    for finding in result["findings"]:
        lines.append("### [%s] %s" % (SEVERITY_LABEL[finding["severity"]],
                                       finding["title"]))
        lines.append("")
        lines.append("- Rule: %s | Axis: %s | WCAG: %s" % (
            finding["rule"], finding["axis_label"], finding["wcag"]))
        if finding.get("path"):
            lines.append("- Element: %s" % finding["path"])
        if finding.get("evidence"):
            lines.append("- Evidence: %s" % finding["evidence"][:300])
        lines.append("- Why it matters: %s" % finding["why"])
        lines.append("- Fix: %s" % finding["fix"])
        lines.append("")
    lines.append("## Prioritised fix plan")
    lines.append("")
    if not result["fix_plan"]:
        lines.append("Nothing to fix.")
    for index, step in enumerate(result["fix_plan"], 1):
        lines.append("%d. **[%s] %s** (+%s points, %s -> %s) - %s" % (
            index, SEVERITY_LABEL[step["severity"]], step["title"],
            step["gain"], step["score_before"], step["score_after"],
            step["fix"]))
    lines.append("")
    lines.append("## Focus order")
    lines.append("")
    if not result["focus_order"]:
        lines.append("Nothing focusable was found.")
    for index, entry in enumerate(result["focus_order"], 1):
        lines.append("%d. <%s> %s (name source: %s) - %s" % (
            index, entry["tag"], entry["name"], entry["source"], entry["path"]))
    lines.append("")
    lines.append("## WCAG 2.2 coverage")
    lines.append("")
    lines.append("| Criterion | Name | Status | Issues |")
    lines.append("| --- | --- | --- | --- |")
    for row in result["wcag_coverage"]:
        lines.append("| %s | %s | %s | %d |" % (row["code"], row["title"],
                                               row["status"], row["issues"]))
    lines.append("")
    return "\n".join(lines)


def to_json(result):
    return json.dumps(result, indent=2, ensure_ascii=False)
