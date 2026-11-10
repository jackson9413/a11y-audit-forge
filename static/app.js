var state = {
  result: null,
  samples: [],
  profiles: [],
  severityFilter: null,
  axisFilter: null,
  sessionId: null
};

function el(id) { return document.getElementById(id); }

function escapeHtml(text) {
  return String(text === undefined || text === null ? "" : text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function scoreColour(score) {
  if (score >= 85) { return "#7ee787"; }
  if (score >= 70) { return "#58a6ff"; }
  if (score >= 55) { return "#f2cc60"; }
  if (score >= 40) { return "#ff9f45"; }
  return "#ff6b6b";
}

function request(url, options) {
  return fetch(url, options || {}).then(function (response) {
    if (!response.ok) {
      return response.json().then(function (body) {
        throw new Error(body.error || ("request failed: " + response.status));
      }, function () {
        throw new Error("request failed: " + response.status);
      });
    }
    return response.json();
  });
}

function boot() {
  request("/api/profiles").then(function (data) {
    state.profiles = data.profiles;
    var select = el("profile");
    data.profiles.forEach(function (profile) {
      var option = document.createElement("option");
      option.value = profile.id;
      option.textContent = profile.label;
      select.appendChild(option);
    });
    el("rule-count").textContent = data.rule_count + " rules";
  }).catch(function () {});

  request("/api/samples").then(function (data) {
    state.samples = data.samples;
    var box = el("sample-list");
    box.innerHTML = "";
    data.samples.forEach(function (sample) {
      var button = document.createElement("button");
      button.className = "sample-btn";
      button.type = "button";
      button.title = sample.blurb;
      button.textContent = sample.label;
      button.addEventListener("click", function () { loadSample(sample.id); });
      box.appendChild(button);
    });
  }).catch(function () {});

  el("run").addEventListener("click", runAudit);
  el("load-sample").addEventListener("click", function () {
    if (state.samples.length) { loadSample(state.samples[0].id); }
  });
  el("refresh-history").addEventListener("click", loadHistory);
  el("copy-markup").addEventListener("click", copyMarkup);

  var tabs = document.querySelectorAll(".tab");
  Array.prototype.forEach.call(tabs, function (tab) {
    tab.addEventListener("click", function () {
      Array.prototype.forEach.call(tabs, function (other) {
        other.classList.remove("active");
      });
      tab.classList.add("active");
      ["findings", "fixes", "focus", "names", "wcag", "markup"].forEach(
        function (name) {
          el("tab-" + name).classList.toggle("hidden", name !== tab.dataset.tab);
        });
    });
  });

  loadHistory();
}

function loadSample(id) {
  request("/api/sample?id=" + encodeURIComponent(id)).then(function (sample) {
    el("markup").value = sample.html;
    el("source-name").value = sample.id;
    el("profile").value = sample.profile;
    runAudit();
  }).catch(function (error) {
    window.alert(error.message);
  });
}

function runAudit() {
  var markup = el("markup").value;
  if (!markup.trim()) {
    window.alert("Paste some markup first.");
    return;
  }
  el("run").disabled = true;
  el("run").textContent = "Auditing...";
  request("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      html: markup,
      profile: el("profile").value,
      source_name: el("source-name").value,
      save: el("save").checked
    })
  }).then(function (result) {
    state.result = result;
    state.sessionId = result.session_id || null;
    render(result);
    if (state.sessionId) { loadHistory(); }
  }).catch(function (error) {
    window.alert(error.message);
  }).then(function () {
    el("run").disabled = false;
    el("run").textContent = "Run audit";
  });
}

function render(result) {
  el("empty-state").classList.add("hidden");
  el("results").classList.remove("hidden");

  var score = el("score");
  score.textContent = result.score;
  score.style.color = scoreColour(result.score);

  var verdict = el("verdict");
  verdict.textContent = result.verdict_label;
  verdict.style.borderColor = scoreColour(result.score);
  verdict.style.color = scoreColour(result.score);

  el("page-title").textContent =
    (result.page_title || result.source_name || "Untitled page") +
    "  |  " + result.profile_label;

  var chips = el("count-chips");
  chips.innerHTML = "";
  ["critical", "high", "medium", "low"].forEach(function (level) {
    var chip = document.createElement("span");
    chip.className = "chip " + level;
    chip.textContent = level + ": " + result.counts[level];
    chips.appendChild(chip);
  });

  var pills = el("axis-pills");
  pills.innerHTML = "";
  Object.keys(result.axis_scores).forEach(function (axis) {
    var value = result.axis_scores[axis];
    var pill = document.createElement("div");
    pill.className = "axis-pill";
    pill.innerHTML =
      '<div class="an">' + escapeHtml(result.axis_labels[axis]) + "</div>" +
      '<div class="av" style="color:' + scoreColour(value) + '">' + value + "</div>" +
      '<div class="ab"><i style="width:' + Math.max(0, Math.min(100, value)) +
      "%;background:" + scoreColour(value) + '"></i></div>';
    pills.appendChild(pill);
  });

  var caps = el("caps");
  caps.innerHTML = "";
  result.caps.forEach(function (cap) {
    var node = document.createElement("div");
    node.className = "cap";
    node.textContent = "Score capped at " + cap.cap + " because " + cap.reason;
    caps.appendChild(node);
  });

  renderFilters(result);
  renderFindings(result);
  renderFixes(result);
  renderFocus(result);
  renderNames(result);
  renderWcag(result);
  el("annotated").textContent = result.annotated_markup;
  renderExports();
}

function renderFilters(result) {
  var box = el("severity-filters");
  box.innerHTML = "";
  ["critical", "high", "medium", "low"].forEach(function (level) {
    if (!result.counts[level]) { return; }
    var button = document.createElement("button");
    button.className = "filter";
    button.type = "button";
    button.textContent = level + " (" + result.counts[level] + ")";
    button.addEventListener("click", function () {
      state.severityFilter = state.severityFilter === level ? null : level;
      renderFilters(result);
      renderFindings(result);
    });
    if (state.severityFilter === level) { button.classList.add("on"); }
    box.appendChild(button);
  });
  Object.keys(result.axis_scores).forEach(function (axis) {
    var button = document.createElement("button");
    button.className = "filter";
    button.type = "button";
    button.textContent = result.axis_labels[axis];
    button.addEventListener("click", function () {
      state.axisFilter = state.axisFilter === axis ? null : axis;
      renderFilters(result);
      renderFindings(result);
    });
    if (state.axisFilter === axis) { button.classList.add("on"); }
    box.appendChild(button);
  });
}

function renderFindings(result) {
  var list = el("findings-list");
  list.innerHTML = "";
  var shown = 0;
  result.findings.forEach(function (finding) {
    if (state.severityFilter && finding.severity !== state.severityFilter) { return; }
    if (state.axisFilter && finding.axis !== state.axisFilter) { return; }
    shown += 1;
    var card = document.createElement("div");
    card.className = "finding " + finding.severity;
    var meta = [
      finding.rule,
      "WCAG " + finding.wcag,
      finding.axis_label
    ];
    if (finding.path) { meta.push(finding.path); }
    card.innerHTML =
      "<h4>" + escapeHtml(finding.title) + "</h4>" +
      '<div class="meta">' + meta.map(escapeHtml).join("  |  ") + "</div>" +
      (finding.evidence
        ? '<div class="evidence">' + escapeHtml(finding.evidence) + "</div>"
        : "") +
      '<div class="why">' + escapeHtml(finding.why) + "</div>" +
      '<div class="fix">Fix: ' + escapeHtml(finding.fix) + "</div>";
    list.appendChild(card);
  });
  if (!shown) {
    var empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = result.findings.length
      ? "No findings match this filter."
      : "No findings. Automated checks never cover everything - test with a keyboard and a real screen reader.";
    list.appendChild(empty);
  }
}

function renderFixes(result) {
  var list = el("fix-list");
  list.innerHTML = "";
  if (!result.fix_plan.length) {
    list.innerHTML = '<p class="muted">Nothing to fix.</p>';
    return;
  }
  result.fix_plan.forEach(function (step, index) {
    var row = document.createElement("div");
    row.className = "fix";
    row.innerHTML =
      '<div class="n">' + (index + 1) + "</div>" +
      '<div class="body"><h4>' + escapeHtml(step.title) + "</h4>" +
      '<div class="muted">' + escapeHtml(step.rule) + "  |  WCAG " +
      escapeHtml(step.wcag) + "  |  " + escapeHtml(step.axis_label) + "</div>" +
      '<div class="fix">' + escapeHtml(step.fix) + "</div>" +
      (step.evidence
        ? '<div class="evidence">' + escapeHtml(step.evidence) + "</div>"
        : "") +
      '<div class="gain">' + step.score_before + " to " + step.score_after +
      "  (+" + step.gain + " points)</div></div>";
    list.appendChild(row);
  });
}

function renderFocus(result) {
  var box = el("focus-table");
  if (!result.focus_order.length) {
    box.innerHTML = '<p class="muted">Nothing focusable was found.</p>';
    return;
  }
  var rows = result.focus_order.map(function (entry, index) {
    return "<tr><td>" + (index + 1) + "</td><td><code>&lt;" +
      escapeHtml(entry.tag) + "&gt;</code></td><td>" +
      escapeHtml(entry.name) + "</td><td>" + escapeHtml(entry.source) +
      "</td><td>" + escapeHtml(entry.tabindex) + "</td><td><code>" +
      escapeHtml(entry.path) + "</code></td></tr>";
  }).join("");
  box.innerHTML =
    "<table><thead><tr><th>#</th><th>Element</th><th>Accessible name</th>" +
    "<th>Name from</th><th>tabindex</th><th>Path</th></tr></thead><tbody>" +
    rows + "</tbody></table>";
}

function renderNames(result) {
  var box = el("name-table");
  if (!result.name_map.length) {
    box.innerHTML = '<p class="muted">No interactive elements were found.</p>';
    return;
  }
  var rows = result.name_map.map(function (entry) {
    var missing = entry.name ? "" : " style=\"color:#ff6b6b\"";
    return "<tr><td><code>&lt;" + escapeHtml(entry.tag) + "&gt;</code></td><td>" +
      escapeHtml(entry.role) + "</td><td" + missing + ">" +
      (escapeHtml(entry.name) || "(no name)") + "</td><td>" +
      escapeHtml(entry.source) + "</td><td><code>" +
      escapeHtml(entry.path) + "</code></td></tr>";
  }).join("");
  box.innerHTML =
    "<table><thead><tr><th>Element</th><th>Role</th><th>Accessible name</th>" +
    "<th>Name from</th><th>Path</th></tr></thead><tbody>" + rows +
    "</tbody></table>";
}

function renderWcag(result) {
  var box = el("wcag-table");
  var rows = result.wcag_coverage.map(function (row) {
    return "<tr><td>" + escapeHtml(row.code) + "</td><td>" +
      escapeHtml(row.title) + '</td><td class="status-' + row.status + '">' +
      escapeHtml(row.status.replace("_", " ")) + "</td><td>" +
      row.issues + "</td></tr>";
  }).join("");
  box.innerHTML =
    "<table><thead><tr><th>Criterion</th><th>Name</th><th>Status</th>" +
    "<th>Issues</th></tr></thead><tbody>" + rows + "</tbody></table>";
}

function renderExports() {
  var md = el("export-md");
  var json = el("export-json");
  var note = el("export-note");
  if (state.sessionId) {
    md.href = "/api/export/" + state.sessionId + "?fmt=md";
    json.href = "/api/export/" + state.sessionId + "?fmt=json";
    md.onclick = null;
    json.onclick = null;
    note.textContent = "saved as session " + state.sessionId;
  } else {
    md.href = "#";
    json.href = "#";
    note.textContent = "not saved - enable save to history for server side exports";
    md.onclick = function () { downloadResult("md"); };
    json.onclick = function () { downloadResult("json"); };
  }
}

function downloadResult(fmt) {
  if (!state.result) { return; }
  var body = fmt === "json"
    ? JSON.stringify(state.result, null, 2)
    : buildMarkdown(state.result);
  var blob = new Blob([body], { type: "text/plain" });
  var link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "a11y-audit." + fmt;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function buildMarkdown(result) {
  var lines = [];
  lines.push("# Accessibility audit - " + (result.page_title || "Untitled page"));
  lines.push("");
  lines.push("Score: " + result.score + "/100 (" + result.verdict_label + ")");
  lines.push("");
  lines.push("## Findings");
  result.findings.forEach(function (finding) {
    lines.push("");
    lines.push("### [" + finding.severity.toUpperCase() + "] " + finding.title);
    lines.push("- Rule: " + finding.rule + " | WCAG " + finding.wcag);
    if (finding.path) { lines.push("- Element: " + finding.path); }
    lines.push("- Why: " + finding.why);
    lines.push("- Fix: " + finding.fix);
  });
  return lines.join("\n");
}

function copyMarkup() {
  var node = el("annotated");
  if (!node) { return; }
  if (navigator.clipboard) {
    navigator.clipboard.writeText(node.textContent).then(function () {
      el("copy-markup").textContent = "Copied";
      setTimeout(function () {
        el("copy-markup").textContent = "Copy";
      }, 1500);
    });
  }
}

function loadHistory() {
  request("/api/sessions?limit=25").then(function (data) {
    var box = el("history");
    box.innerHTML = "";
    if (!data.sessions.length) {
      box.innerHTML = '<p class="muted">No saved audits yet.</p>';
      return;
    }
    data.sessions.forEach(function (session) {
      var row = document.createElement("div");
      row.className = "history-row";

      var score = document.createElement("span");
      score.className = "score";
      score.textContent = session.score;
      score.style.color = scoreColour(session.score);

      var name = document.createElement("span");
      name.className = "name";
      name.textContent = session.page_title || session.source_name ||
        ("audit #" + session.id);
      name.style.cursor = "pointer";
      name.title = "Reopen this audit";
      name.addEventListener("click", function () { reopen(session.id); });

      var stars = document.createElement("span");
      stars.className = "stars";
      for (var i = 1; i <= 5; i += 1) {
        (function (value) {
          var star = document.createElement("span");
          star.className = "star";
          star.textContent = "★";
          if (session.rating && session.rating >= value) {
            star.classList.add("on");
          }
          star.addEventListener("click", function () {
            request("/api/sessions/" + session.id, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ rating: value })
            }).then(loadHistory);
          });
          stars.appendChild(star);
        })(i);
      }

      var notes = document.createElement("input");
      notes.className = "notes";
      notes.type = "text";
      notes.placeholder = "notes";
      notes.value = session.notes || "";
      notes.addEventListener("change", function () {
        request("/api/sessions/" + session.id, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            notes: notes.value,
            rating: session.rating
          })
        });
      });

      var when = document.createElement("span");
      when.className = "muted";
      when.textContent = (session.created_at || "").replace("T", " ").slice(0, 16);

      var exportLink = document.createElement("a");
      exportLink.className = "link-btn";
      exportLink.href = "/api/export/" + session.id + "?fmt=md";
      exportLink.textContent = "md";

      row.appendChild(score);
      row.appendChild(name);
      row.appendChild(stars);
      row.appendChild(notes);
      row.appendChild(when);
      row.appendChild(exportLink);
      box.appendChild(row);
    });
  }).catch(function () {});
}

function reopen(sessionId) {
  request("/api/sessions/" + sessionId).then(function (result) {
    state.result = result;
    state.sessionId = sessionId;
    el("source-name").value = result.source_name || "";
    el("profile").value = result.profile || "general";
    render(result);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

document.addEventListener("DOMContentLoaded", boot);
