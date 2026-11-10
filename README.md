# a11y audit forge

Paste your HTML. Get a WCAG 2.2 accessibility audit you can actually act on:
a 0-100 score across five axes, every finding with the evidence that
triggered it, the focus order your users will hit, and a prioritised fix
plan that shows the score after each change.

Runs entirely on your machine. No API keys, no network calls, no LLM.

---

## Why it matters

Most accessibility advice stops at "use alt text". That is not useful when
you have 300 images and a deadline. This tool does the part that is actually
hard:

1. **It finds the real problems in your markup.** Unlabelled fields,
   placeholder-as-label, ARIA attributes pointing at ids that do not exist,
   aria-hidden on a focusable button, icon-only buttons with no name,
   positive tabindex that scrambles the focus order, tables with no header
   cells, autoplay video with no captions track.
2. **It tells you the order to fix them in.** The fix plan is sorted by
   severity and axis weight, and each step shows the score before and after,
   so you can stop when the remaining work is not worth the effort.
3. **It shows you the things a linter cannot.** The computed focus order,
   the accessible name of every interactive element and where that name came
   from, and a WCAG 2.2 criterion-by-criterion pass/fail/review table.
4. **It marks your markup up.** Every fix is written as a comment above the
   element it applies to, so you can paste the annotated markup back into your
   editor and work through it.

## What you get

| Output | What it is |
| --- | --- |
| Score | 0-100, weighted across five axes, with structural caps |
| Axis pills | Structure and ARIA, Forms and Labels, Images and Media, Keyboard and Focus, Motion and Timing |
| Findings | 60+ rules, each with severity, WCAG criterion, evidence, why it matters and a concrete fix |
| Fix plan | Prioritised, with the score after each individual fix |
| Focus order | Every focusable element in tab order, with its accessible name and where the name came from |
| Names map | Every interactive element with its computed accessible name and source |
| WCAG coverage | 20 success criteria, each pass / fail / review / not checked |
| Annotated markup | Your HTML with each fix written above the element it applies to |
| Exports | Markdown and JSON |
| History | SQLite log with a 1-5 star self-rating and notes |

## Quick start

```bash
cd a11y-audit-forge
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Then open <http://127.0.0.1:8765>.

Set PORT to use a different port. Set A11Y_DB to point the SQLite log
somewhere else.

## How the score works

Each axis starts at 100 and loses points for the findings in it:
critical 26, high 12, medium 6, low 2. The overall score is the weighted sum
of the five axes, where the weights depend on the profile you pick:

| Profile | Structure | Forms | Media | Keyboard | Motion |
| --- | --- | --- | --- | --- | --- |
| General page | 0.25 | 0.20 | 0.15 | 0.25 | 0.15 |
| Reusable component | 0.15 | 0.25 | 0.20 | 0.30 | 0.10 |
| Form or checkout | 0.15 | 0.40 | 0.10 | 0.25 | 0.10 |
| Marketing / content page | 0.30 | 0.15 | 0.20 | 0.25 | 0.10 |
| E-commerce / product page | 0.20 | 0.25 | 0.25 | 0.25 | 0.05 |
| Embedded widget | 0.15 | 0.20 | 0.15 | 0.40 | 0.10 |

Structural caps stop a page from scoring well by skipping the hard part:

- one critical finding caps the score at 55, two at 45, four at 35
- a missing page language caps the score at 60
- an unlabelled form control caps the score at 50
- three or more nameless controls in the tab order cap the score at 55
- a fragment (no html element) caps the score at 75

Verdict bands: 85 audit ready, 70 mostly accessible, 55 needs fixes,
40 tight but usable, below 40 not accessible.

## The rules

**Structure and ARIA** - missing or invalid page language, missing title,
missing charset, missing viewport, viewport that blocks zoom, missing h1,
skipped heading levels, empty headings, duplicate ids, missing main and nav
landmarks, ARIA references to ids that do not exist, ambiguous ARIA
references, unknown roles, unknown aria-* attributes, invalid ARIA values,
missing required child roles, role and native element conflicts,
presentational focusable elements, aria-hidden on focusable elements, broken
list markup, tables with no header cells or no scope or no caption, clickable
divs.

**Forms and labels** - controls with no accessible name, placeholder used as
the only label, labels pointing at ids that do not exist, inputs with no
type, error messages not tied to their field, radio groups with no fieldset
and legend, fieldsets with no legend, buttons with no accessible name, submit
inputs with no value, missing autocomplete, password fields with no
autocomplete mode, image submit buttons with no alt, unassociated labels,
required fields not exposed, forms with no name.

**Images and media** - images with no alt, alt text that is a file name, alt
text that repeats the word image, alt text that is too long, inline SVG with
no accessible name or no title, video with no captions track, audio with no
transcript, iframe with no title, object and embed with no title, image map
areas with no alt.

**Keyboard and focus** - links with no accessible name, focusable elements
with no accessible name, positive tabindex, tabindex on non-interactive
elements, keyboard handlers on elements with no role, no skip link, focus
order that disagrees with the DOM order, modal dialogs with no focus target,
ARIA widget roles with no name, custom controls that do not expose their
state.

**Motion and timing** - animation with no prefers-reduced-motion handling,
autoplay audio or video, marquee and blink, meta refresh, heavy animation.

## API

```
GET  /api/health                     service status, rule count
GET  /api/profiles                   the six profiles and their axis weights
GET  /api/samples                    the six built-in samples
GET  /api/sample?id=<id>             one sample, with its markup
POST /api/analyze                    {html, profile, source_name, save}
GET  /api/sessions                   recent audits
GET  /api/sessions/<id>              one audit with its full result
PATCH /api/sessions/<id>             {rating, notes}
GET  /api/export/<id>?fmt=md|json    download the audit
GET  /                               the UI
```

POST /api/analyze with save: true writes a row to the SQLite log and
returns session_id.

## Built-in samples

| Sample | Profile | What it shows |
| --- | --- | --- |
| Clean landing page | marketing | The control case: lang, landmarks, skip link, scoped table headers, reduced motion honoured. Zero findings, score 100 |
| Signup form | form_heavy | Placeholder-only labels, an orphaned error message, a radio group with no fieldset, an icon-only submit button |
| Broken store navigation | e-commerce | Clickable divs, positive tabindex, missing alt text, zoom blocked in the viewport meta |
| Product tour player | marketing | Autoplay video with no captions, untitled iframe, a marquee, no prefers-reduced-motion handling |
| ARIA mistakes | general | ARIA references that point nowhere, an invalid role, a focusable aria-hidden button, duplicate ids, broken list markup |
| Operations dashboard | general | An unlabelled chart, a table with no header cells, an icon-only link |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Architecture

```
app.py                  Flask routes, SQLite session log, exports
engine/dom.py           dependency free HTML parser that builds a small DOM
engine/names.py         accessible name computation (HTML-AAM subset)
engine/rules.py         the rule catalogue, ARIA data, profiles, WCAG list
engine/audit.py         the analyzer and the scoring model
engine/exports.py       Markdown and JSON exports
engine/samples.py       the six built-in sample pages
static/                 dark vanilla JS UI, no build step
tests/                  51 engine and API tests
```

Flask + SQLite + vanilla JS. The engine is pure standard library: the HTML
parser, the name computation and the scoring maths are all written here, so
the tool runs offline and never sends your markup anywhere.

## Honest limitations

This is a static analyser. It reads markup, not rendered pixels.

- It cannot judge whether your alt text is actually accurate, only whether
  one exists and whether it looks like a file name.
- It cannot check colour contrast. That needs the rendered colours.
- It cannot tell whether a skip link works, only whether one is there.
- It cannot see content injected by JavaScript after load. Audit the
  rendered DOM if your app is a single page app.
- A page with no findings scores 100, which is not the same as being
  accessible. Automated checks cover a fraction of WCAG. Always test with a
  keyboard and a real screen reader.
