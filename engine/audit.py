"""The accessibility analysis engine.

Static, standard-library only. It parses markup into a small DOM, then runs
a rule set across five axes: structure and ARIA, forms and labels, images and
media, keyboard and focus, and motion and timing.
"""

import re

from .dom import VOID_ELEMENTS, parse_html
from .names import (
    accessible_name,
    clean,
    is_focusable,
    is_interactive,
    visible_text,
)
from .rules import (
    ARIA_ATTRIBUTES,
    AXES,
    AXIS_LABELS,
    ID_REFERENCE_ATTRS,
    PROFILES,
    REQUIRED_CHILDREN,
    RULES,
    SEVERITY_ORDER,
    SEVERITY_PENALTY,
    VALID_ROLES,
    VERDICT_BANDS,
    WCAG_CRITERIA,
)

FILENAME_RE = re.compile(r"^[\w\-.]+\.(png|jpe?g|gif|svg|webp|bmp|avif)$", re.I)
REDUNDANT_ALT_RE = re.compile(
    r"^\s*(image|picture|photo|graphic|icon|logo|screenshot|diagram|\w+)\s+of\b", re.I
)
IMG_ID_RE = re.compile(r"^(img|image|dsc|photo|untitled)[\-_ ]?\d+$", re.I)
SKIP_RE = re.compile(r"skip\s+(to|link|navigation|content|main)", re.I)
ERROR_HINT_RE = re.compile(r"(error|invalid|has-error|field-error|form-error|msg-error)", re.I)

ARIA_BOOLEAN_VALUES = {
    "aria-hidden": {"true", "false"},
    "aria-disabled": {"true", "false"},
    "aria-required": {"true", "false"},
    "aria-readonly": {"true", "false"},
    "aria-modal": {"true", "false"},
    "aria-multiline": {"true", "false"},
    "aria-multiselectable": {"true", "false"},
    "aria-busy": {"true", "false"},
    "aria-grabbed": {"true", "false"},
    "aria-atomic": {"true", "false"},
}
ARIA_TRISTATE_VALUES = {
    "aria-checked": {"true", "false", "mixed", "undefined"},
    "aria-pressed": {"true", "false", "mixed", "undefined"},
    "aria-expanded": {"true", "false", "undefined"},
}

HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")

NATIVE_ROLE = {
    "a": "link",
    "article": "article",
    "aside": "complementary",
    "button": "button",
    "footer": "contentinfo",
    "form": "form",
    "h1": "heading", "h2": "heading", "h3": "heading",
    "h4": "heading", "h5": "heading", "h6": "heading",
    "header": "banner",
    "img": "img",
    "input": "textbox",
    "li": "listitem",
    "main": "main",
    "nav": "navigation",
    "ol": "list",
    "option": "option",
    "progress": "progressbar",
    "section": "region",
    "select": "combobox",
    "table": "table",
    "tbody": "rowgroup",
    "td": "cell",
    "textarea": "textbox",
    "tfoot": "rowgroup",
    "th": "columnheader",
    "thead": "rowgroup",
    "tr": "row",
    "ul": "list",
}

INPUT_TYPE_ROLE = {
    "checkbox": "checkbox",
    "radio": "radio",
    "range": "slider",
    "number": "spinbutton",
    "search": "searchbox",
    "email": "textbox",
    "tel": "textbox",
    "text": "textbox",
    "url": "textbox",
    "password": "textbox",
}

AUTOCOMPLETE_HINTS = {
    "name": "name",
    "firstname": "given-name",
    "first-name": "given-name",
    "lastname": "family-name",
    "last-name": "family-name",
    "email": "email",
    "e-mail": "email",
    "mail": "email",
    "phone": "tel",
    "tel": "tel",
    "mobile": "tel",
    "address": "street-address",
    "street": "street-address",
    "city": "address-level2",
    "state": "address-level1",
    "zip": "postal-code",
    "postal": "postal-code",
    "postcode": "postal-code",
    "country": "country-name",
    "company": "organization",
    "org": "organization",
    "title": "organization-title",
    "username": "username",
    "user": "username",
    "login": "username",
    "birthday": "bday",
    "dob": "bday",
}


def _role_of(node):
    role = node.attrs.get("role")
    if role:
        return role.split()[0].strip().lower()
    if node.tag == "input":
        return INPUT_TYPE_ROLE.get((node.attrs.get("type") or "text").lower(),
                                   "textbox")
    if node.tag in NATIVE_ROLE:
        return NATIVE_ROLE[node.tag]
    return "generic"


class Audit:
    """Collects findings for one parsed document."""

    def __init__(self, markup, profile="general", source_name=""):
        self.markup = markup
        self.profile = profile if profile in PROFILES else "general"
        self.source_name = source_name
        self.doc = parse_html(markup)
        self.findings = []
        self._reported_nodes = {}

    # -- helpers -------------------------------------------------------
    def add(self, rule_id, node=None, evidence=None, detail=None, count=1):
        rule = RULES[rule_id]
        if node is not None:
            path = node.path()
            snippet = evidence if evidence is not None else node.snippet()
            line = node.line
        else:
            path = ""
            snippet = evidence or ""
            line = 0
        self.findings.append({
            "rule": rule_id,
            "axis": rule["axis"],
            "severity": rule["severity"],
            "wcag": rule["wcag"],
            "title": rule["title"],
            "why": rule["why"],
            "fix": rule["fix"],
            "path": path,
            "evidence": snippet,
            "line": line,
            "detail": detail,
            "count": count,
            "axis_label": AXIS_LABELS[rule["axis"]],
        })

    def add_many(self, rule_id, nodes, make_detail=None):
        for node in nodes:
            detail = make_detail(node) if make_detail else None
            self.add(rule_id, node=node, detail=detail)

    def seen(self, rule_id, node):
        key = (rule_id, id(node))
        if key in self._reported_nodes:
            return True
        self._reported_nodes[key] = True
        return False

    # -- entry point ---------------------------------------------------
    def run(self):
        doc = self.doc
        elements = list(doc.root.elements())
        self._check_document(elements)
        self._check_headings(elements)
        self._check_landmarks(elements)
        self._check_ids_and_aria(elements)
        self._check_roles(elements)
        self._check_lists(elements)
        self._check_tables(elements)
        self._check_click_handlers(elements)
        self._check_forms(elements)
        self._check_media(elements)
        self._check_keyboard(elements)
        self._check_motion(elements)
        return self.findings

    # -- document level ------------------------------------------------
    def _check_document(self, elements):
        doc = self.doc
        html = doc.html()
        if html is None:
            self.add("html-missing-lang", evidence="The pasted markup has no "
                     "<html> element, so it is audited as a fragment.",
                     detail="fragment")
        else:
            lang = (html.attrs.get("lang") or "").strip()
            if not lang:
                self.add("html-missing-lang", node=html,
                         evidence="<html> with no lang attribute")
            elif not re.match(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$", lang):
                self.add("html-invalid-lang", node=html,
                         evidence="<html lang=\"%s\">" % lang)

        if not doc.title():
            self.add("page-missing-title", evidence="No <title> element found")

        head = doc.head()
        has_charset = False
        has_viewport = False
        viewport_content = ""
        for meta in doc.root.find_all("meta"):
            if meta.attrs.get("charset"):
                has_charset = True
            if meta.attrs.get("http-equiv", "").lower() == "content-type":
                if "charset" in (meta.attrs.get("content") or "").lower():
                    has_charset = True
            if (meta.attrs.get("name") or "").lower() == "viewport":
                has_viewport = True
                viewport_content = meta.attrs.get("content") or ""
        if not has_charset:
            self.add("missing-charset", evidence="No <meta charset> found")
        if not has_viewport:
            self.add("missing-viewport", evidence="No viewport meta tag found")
        else:
            low = viewport_content.lower()
            m = re.search(r"user-scalable\s*=\s*(\S+)", low)
            blocked = bool(m and m.group(1).strip(",") == "no")
            m2 = re.search(r"maximum-scale\s*=\s*([0-9.]+)", low)
            if m2 and float(m2.group(1)) < 2:
                blocked = True
            if blocked:
                self.add("viewport-blocks-zoom",
                         evidence=viewport_content,
                         detail="viewport blocks pinch zoom")

    # -- headings ------------------------------------------------------
    def _check_headings(self, elements):
        headings = []
        for node in elements:
            if node.tag in HEADING_TAGS:
                headings.append(node)
        if not headings:
            self.add("missing-h1", evidence="No h1 to h6 elements found")
            return
        h1s = [h for h in headings if h.tag == "h1"]
        if not h1s:
            self.add("missing-h1",
                     evidence="First heading is %s" % headings[0].tag)
        if len(h1s) > 1:
            self.add("multiple-h1", node=h1s[1],
                     evidence="%d h1 elements found" % len(h1s))
        previous = 0
        for head in headings:
            if not visible_text(head):
                self.add("empty-heading", node=head,
                         evidence=head.snippet())
            level = int(head.tag[1])
            if previous and level > previous + 1:
                self.add("heading-skip", node=head,
                         evidence="h%d follows h%d" % (level, previous),
                         detail="h%d -> h%d" % (previous, level))
            previous = level

    # -- landmarks -----------------------------------------------------
    def _check_landmarks(self, elements):
        has_main = any(n.tag == "main" or _role_of(n) == "main"
                       for n in elements)
        if not has_main:
            self.add("missing-main-landmark", evidence="No main landmark found")
        has_nav = any(n.tag == "nav" or _role_of(n) == "navigation"
                      for n in elements)
        if not has_nav:
            self.add("missing-nav-landmark", evidence="No navigation landmark "
                     "found")

    # -- ids and aria references ---------------------------------------
    def _check_ids_and_aria(self, elements):
        seen = {}
        for node in elements:
            node_id = node.attrs.get("id")
            if not node_id:
                continue
            seen.setdefault(node_id, []).append(node)
        for node_id, nodes in seen.items():
            if len(nodes) > 1:
                self.add("duplicate-id", node=nodes[1],
                         evidence="id=\"%s\" used %d times" % (node_id,
                                                               len(nodes)),
                         detail=node_id)

        for node in elements:
            for attr, mode in ID_REFERENCE_ATTRS.items():
                if attr not in node.attrs:
                    continue
                refs = [r for r in node.attrs[attr].split() if r]
                if not refs:
                    continue
                missing = [r for r in refs if self.doc.by_id(r) is None]
                if missing:
                    self.add("aria-ref-missing", node=node,
                             evidence="%s=\"%s\" -> missing id %s" % (
                                 attr, node.attrs[attr], ", ".join(missing)),
                             detail=", ".join(missing))
                if mode == "single" and len(refs) > 1:
                    self.add("aria-ref-ambiguous", node=node,
                             evidence="%s=\"%s\"" % (attr, node.attrs[attr]),
                             detail=", ".join(refs))

    # -- roles ---------------------------------------------------------
    def _check_roles(self, elements):
        for node in elements:
            role_attr = node.attrs.get("role")
            if role_attr:
                for role in role_attr.split():
                    if role.lower() not in VALID_ROLES:
                        self.add("invalid-role", node=node,
                                 evidence="role=\"%s\"" % role,
                                 detail=role)
                        break

            for attr in node.attrs:
                if attr.startswith("aria-") and attr not in ARIA_ATTRIBUTES:
                    self.add("aria-attr-invalid", node=node,
                             evidence="%s on <%s>" % (attr, node.tag),
                             detail=attr)
                    continue
                value = (node.attrs[attr] or "").strip().lower()
                if attr in ARIA_BOOLEAN_VALUES and value not in ARIA_BOOLEAN_VALUES[attr]:
                    self.add("aria-attr-bad-value", node=node,
                             evidence="%s=\"%s\"" % (attr, value),
                             detail=attr)
                if attr in ARIA_TRISTATE_VALUES and value not in ARIA_TRISTATE_VALUES[attr]:
                    self.add("aria-attr-bad-value", node=node,
                             evidence="%s=\"%s\"" % (attr, value),
                             detail=attr)
            if "aria-level" in node.attrs:
                try:
                    int(node.attrs["aria-level"])
                except (TypeError, ValueError):
                    self.add("aria-attr-bad-value", node=node,
                             evidence="aria-level=\"%s\"" %
                             node.attrs["aria-level"], detail="aria-level")

            role = _role_of(node)
            if role in ("presentation", "none") and is_focusable(node):
                self.add("presentation-focusable", node=node,
                         evidence=node.snippet())
            if node.attrs.get("aria-hidden", "").strip().lower() == "true":
                if is_focusable(node):
                    self.add("aria-hidden-focusable", node=node,
                             evidence=node.snippet())
                else:
                    for descendant in node.elements():
                        if is_focusable(descendant):
                            self.add("aria-hidden-focusable", node=descendant,
                                     evidence=descendant.snippet(),
                                     detail="inside aria-hidden parent")
                            break

            required = REQUIRED_CHILDREN.get(role)
            if required:
                children = node.children_elements()
                bad = []
                for child in children:
                    if child.tag in ("ul", "ol", "table", "tbody", "thead",
                                     "tfoot", "tr"):
                        continue
                    child_role = _role_of(child)
                    if child_role in required:
                        continue
                    if child.attrs.get("role") in ("none", "presentation"):
                        continue
                    if child.tag in ("script", "style", "template"):
                        continue
                    bad.append(child)
                if children and bad and len(bad) == len(children):
                    self.add("aria-required-children", node=node,
                             evidence="role=\"%s\" with %d child element(s) "
                                     "of the wrong role" % (role, len(bad)),
                             detail=role)

            self._check_role_conflicts(node, role)

    def _check_role_conflicts(self, node, role):
        tag = node.tag
        input_type = (node.attrs.get("type") or "text").lower() if tag == "input" else ""
        if role in ("checkbox", "radio", "switch") and tag == "input":
            expected = "radio" if role == "radio" else "checkbox"
            if input_type not in (expected, ""):
                self.add("role-attr-conflict", node=node,
                         evidence="<input type=\"%s\" role=\"%s\">" % (
                             input_type, role), detail=role)
        if role == "textbox" and tag == "input" and input_type in (
            "checkbox", "radio", "submit", "button", "range"
        ):
            self.add("role-attr-conflict", node=node,
                     evidence="<input type=\"%s\" role=\"textbox\">" %
                     input_type, detail=role)
        if role == "link" and tag in ("button", "input"):
            self.add("role-attr-conflict", node=node,
                     evidence="<%s role=\"link\">" % tag, detail=role)
        explicit_role = (node.attrs.get("role") or "").strip().lower()
        if explicit_role == "heading" and "aria-level" not in node.attrs:
            self.add("role-attr-conflict", node=node,
                     evidence="role=\"heading\" without aria-level",
                     detail="heading")
        if explicit_role in ("checkbox", "switch", "radio") and \
                "aria-checked" not in node.attrs:
            if tag not in ("input",):
                self.add("custom-control-no-state", node=node,
                         evidence="role=\"%s\" without aria-checked" % role,
                         detail=role)
        if explicit_role == "tab" and "aria-selected" not in node.attrs:
            self.add("custom-control-no-state", node=node,
                     evidence="role=\"tab\" without aria-selected", detail=role)

    # -- lists ---------------------------------------------------------
    def _check_lists(self, elements):
        for node in elements:
            if node.tag == "li":
                parent = node.parent
                if parent is None or parent.tag not in ("ul", "ol"):
                    self.add("list-structure", node=node,
                             evidence="<li> outside a list")
            elif node.tag in ("ul", "ol"):
                bad = [
                    child for child in node.children_elements()
                    if child.tag not in ("li", "script", "style", "template")
                ]
                if bad:
                    self.add("list-structure", node=node,
                             evidence="<%s> contains <%s>" % (node.tag,
                                                             bad[0].tag))

    # -- tables --------------------------------------------------------
    def _check_tables(self, elements):
        for node in elements:
            if node.tag != "table":
                continue
            rows = node.find_all("tr")
            if len(rows) > 1:
                headers = node.find_all("th")
                if not headers:
                    self.add("table-missing-header", node=node,
                             evidence="<table> with %d rows and no th" %
                             len(rows))
                else:
                    for head in headers:
                        if "scope" not in head.attrs:
                            self.add("table-missing-scope", node=head,
                                     evidence=head.snippet())
            if node.first_child("caption") is None:
                self.add("table-missing-caption", node=node,
                         evidence="<table> with no caption")

    # -- click handlers ------------------------------------------------
    def _check_click_handlers(self, elements):
        for node in elements:
            if node.tag not in ("div", "span", "p", "li", "td", "section",
                                "article", "strong", "b", "i", "em"):
                continue
            if "onclick" not in node.attrs:
                continue
            role = node.attrs.get("role")
            if role:
                continue
            if node.tag == "a" and "href" in node.attrs:
                continue
            self.add("div-as-button", node=node, evidence=node.snippet())

    # -- forms ---------------------------------------------------------
    def _check_forms(self, elements):
        doc = self.doc
        described = set()
        for node in elements:
            for attr in ("aria-describedby", "aria-errormessage"):
                for ref in (node.attrs.get(attr) or "").split():
                    described.add(ref)

        for node in elements:
            tag = node.tag
            if tag == "label":
                target = node.attrs.get("for")
                if target:
                    control = doc.by_id(target)
                    if control is None:
                        self.add("label-for-mismatch", node=node,
                                 evidence="<label for=\"%s\"> with no such "
                                 "element" % target, detail=target)
                    elif control.tag not in ("input", "select", "textarea",
                                             "button", "meter", "output",
                                             "progress"):
                        self.add("label-for-mismatch", node=node,
                                 evidence="<label for=\"%s\"> points at "
                                         "<%s>" % (target, control.tag),
                                 detail=target)
                else:
                    wrapper = doc.wrapping_label(node)
                    if wrapper is None and not node.children_elements():
                        self.add("label-not-associated", node=node,
                                 evidence=node.snippet())
                continue

            if tag not in ("input", "select", "textarea"):
                continue

            if tag == "input" and (node.attrs.get("type") or "").lower() == "hidden":
                continue

            name, source = accessible_name(node, doc)
            placeholder = node.attrs.get("placeholder")
            if not name:
                if placeholder and clean(placeholder):
                    self.add("placeholder-as-label", node=node,
                             evidence=node.snippet(), detail=clean(placeholder))
                else:
                    self.add("input-no-label", node=node,
                             evidence=node.snippet())
            elif placeholder and clean(placeholder) and source == "title":
                self.add("placeholder-as-label", node=node,
                         evidence=node.snippet(),
                         detail="name comes from the title attribute")

            if tag == "input":
                if "type" not in node.attrs:
                    self.add("input-no-type", node=node,
                             evidence=node.snippet())
                input_type = (node.attrs.get("type") or "text").lower()
                if input_type == "image" and not (node.attrs.get("alt") or ""):
                    self.add("input-image-no-alt", node=node,
                             evidence=node.snippet())
                if input_type == "password" and not node.attrs.get("autocomplete"):
                    self.add("password-no-autocomplete", node=node,
                             evidence=node.snippet())
                elif input_type in ("text", "email", "tel", "url", "search",
                                    "number", "password") and not \
                        node.attrs.get("autocomplete"):
                    hint = self._autocomplete_hint(node)
                    if hint:
                        self.add("autocomplete-missing", node=node,
                                 evidence=node.snippet(), detail=hint)
                if "required" in node.attrs and \
                        node.attrs.get("aria-required") is None:
                    self.add("required-not-exposed", node=node,
                             evidence=node.snippet())

            if tag == "button":
                button_name, _ = accessible_name(node, doc)
                if not button_name:
                    self.add("button-no-name", node=node,
                             evidence=node.snippet())

            if tag == "input" and (node.attrs.get("type") or "").lower() in (
                "submit", "reset"
            ):
                if not (node.attrs.get("value") or "").strip():
                    self.add("submit-input-no-name", node=node,
                             evidence=node.snippet())

        # radio groups
        groups = {}
        for node in elements:
            if node.tag == "input" and (node.attrs.get("type") or "").lower() == "radio":
                groups.setdefault(node.attrs.get("name") or "", []).append(node)
        for name, radios in groups.items():
            if len(radios) < 2:
                continue
            in_fieldset = False
            for radio in radios:
                for ancestor in radio.ancestors():
                    if ancestor.tag == "fieldset":
                        in_fieldset = True
                        break
                if in_fieldset:
                    break
            if not in_fieldset:
                self.add("radio-without-group", node=radios[0],
                         evidence="%d radio inputs named \"%s\" with no "
                                 "fieldset" % (len(radios), name), detail=name)

        for node in elements:
            if node.tag == "fieldset" and node.first_child("legend") is None:
                self.add("fieldset-missing-legend", node=node,
                         evidence=node.snippet())

        # error messages that are not linked to a field
        for node in elements:
            if node.tag in ("input", "select", "textarea"):
                continue
            hint = " ".join([
                node.attrs.get("class", ""),
                node.attrs.get("id", ""),
                node.attrs.get("data-error", ""),
            ])
            role = (node.attrs.get("role") or "").lower()
            if not ERROR_HINT_RE.search(hint) and role != "alert":
                continue
            if not visible_text(node):
                continue
            node_id = node.attrs.get("id")
            if node_id and node_id in described:
                continue
            if role == "alert" and not node_id:
                continue
            self.add("error-not-associated", node=node,
                     evidence=node.snippet())

        for node in elements:
            if node.tag != "form":
                continue
            name, _ = accessible_name(node, doc)
            if not name:
                self.add("no-form-landmark", node=node, evidence=node.snippet())

    def _autocomplete_hint(self, node):
        for key in ("name", "id", "placeholder", "aria-label"):
            value = clean(node.attrs.get(key) or "").lower()
            if not value:
                continue
            token = re.sub(r"[^a-z-]", "", value)
            if token in AUTOCOMPLETE_HINTS:
                return AUTOCOMPLETE_HINTS[token]
            for key_word, hint in AUTOCOMPLETE_HINTS.items():
                if key_word in value:
                    return hint
        return None

    # -- media ---------------------------------------------------------
    def _check_media(self, elements):
        doc = self.doc
        for node in elements:
            tag = node.tag
            if tag == "img":
                if "alt" not in node.attrs:
                    self.add("img-missing-alt", node=node,
                             evidence=node.snippet())
                    continue
                alt = clean(node.attrs.get("alt") or "")
                if alt:
                    if FILENAME_RE.match(alt) or IMG_ID_RE.match(alt):
                        self.add("img-alt-filename", node=node,
                                 evidence=node.snippet(), detail=alt)
                    if REDUNDANT_ALT_RE.match(alt):
                        self.add("img-alt-redundant", node=node,
                                 evidence=node.snippet(), detail=alt)
                    if len(alt) > 125:
                        self.add("img-alt-too-long", node=node,
                                 evidence=node.snippet(),
                                 detail="%d characters" % len(alt))
            elif tag == "svg":
                role = (node.attrs.get("role") or "").lower()
                labelled = node.attrs.get("aria-label") or \
                    node.attrs.get("aria-labelledby") or \
                    node.first_child("title") is not None
                hidden = (node.attrs.get("aria-hidden") or "").lower() == "true"
                if not hidden and not labelled and role not in ("presentation",
                                                                 "none"):
                    self.add("svg-no-name", node=node, evidence=node.snippet())
                elif role == "img" and not node.first_child("title") and \
                        not node.attrs.get("aria-label"):
                    self.add("svg-no-title", node=node, evidence=node.snippet())
            elif tag == "video":
                tracks = node.find_all("track")
                caption = [t for t in tracks
                           if (t.attrs.get("kind") or "").lower() == "captions"]
                if not caption:
                    self.add("video-no-captions", node=node,
                             evidence=node.snippet())
            elif tag == "audio":
                self.add("audio-no-transcript", node=node, evidence=node.snippet())
            elif tag == "iframe":
                if not (node.attrs.get("title") or "").strip():
                    self.add("iframe-no-title", node=node,
                             evidence=node.snippet())
            elif tag in ("object", "embed"):
                if not (node.attrs.get("title") or "").strip():
                    self.add("object-embed-no-title", node=node,
                             evidence=node.snippet())
            elif tag == "area":
                if not (node.attrs.get("alt") or "").strip():
                    self.add("area-no-alt", node=node, evidence=node.snippet())

    # -- keyboard ------------------------------------------------------
    def _check_keyboard(self, elements):
        doc = self.doc
        named_nodes = set()
        unnamed_nodes = set()
        for node in elements:
            if node.tag == "a" and "href" in node.attrs:
                name, _ = accessible_name(node, doc)
                if not name:
                    self.add("link-no-name", node=node, evidence=node.snippet())
                    unnamed_nodes.add(id(node))
                else:
                    named_nodes.add(id(node))
            elif node.tag == "button":
                name, _ = accessible_name(node, doc)
                if not name:
                    self.add("button-no-name", node=node, evidence=node.snippet())
                    unnamed_nodes.add(id(node))
                else:
                    named_nodes.add(id(node))

        role = None
        for node in elements:
            if not is_focusable(node):
                continue
            tabindex = node.attrs.get("tabindex")
            if tabindex is not None:
                try:
                    value = int(tabindex)
                except (TypeError, ValueError):
                    value = None
                if value is not None and value > 0:
                    self.add("positive-tabindex", node=node,
                             evidence=node.snippet(),
                             detail="tabindex=%d" % value)
                elif value == 0 and node.tag in (
                    "div", "span", "li", "p", "section", "article", "td", "tr"
                ) and not node.attrs.get("role"):
                    self.add("tabindex-on-static", node=node,
                             evidence=node.snippet())
            if id(node) in named_nodes or id(node) in unnamed_nodes:
                continue
            name, _ = accessible_name(node, doc)
            explicit_role = (node.attrs.get("role") or "").strip().lower()
            if not name:
                if node.tag in ("input", "select", "textarea"):
                    continue
                if node.tag in ("iframe", "object", "embed"):
                    continue
                if explicit_role in ("button", "link", "checkbox", "radio",
                                     "tab", "menuitem", "switch", "option",
                                     "slider", "spinbutton", "textbox",
                                     "searchbox", "combobox", "listbox",
                                     "treeitem"):
                    self.add("widget-role-no-name", node=node,
                             evidence=node.snippet())
                else:
                    self.add("focusable-no-name", node=node,
                             evidence=node.snippet())

        for node in elements:
            has_key = any(key in node.attrs for key in
                          ("onkeydown", "onkeyup", "onkeypress"))
            if not has_key:
                continue
            if node.tag in ("input", "button", "select", "textarea", "a",
                            "summary", "body"):
                continue
            if node.attrs.get("role"):
                continue
            self.add("keyboard-handler-no-role", node=node,
                     evidence=node.snippet())

        focusables = [n for n in elements if is_focusable(n)]
        if len(focusables) > 3 and self.doc.html() is not None:
            has_skip = False
            for node in focusables:
                if node.tag == "a":
                    name, _ = accessible_name(node, doc)
                    href = node.attrs.get("href") or ""
                    if href.startswith("#") and (SKIP_RE.search(name or "") or
                                                 SKIP_RE.search(href)):
                        has_skip = True
                        break
                hint = " ".join([node.attrs.get("class", ""),
                                 node.attrs.get("id", "")])
                if SKIP_RE.search(hint):
                    has_skip = True
                    break
            if not has_skip:
                self.add("no-skip-link", evidence="No skip link found in the "
                         "markup")

        for node in elements:
            if (node.attrs.get("role") or "").lower() != "dialog":
                continue
            modal = (node.attrs.get("aria-modal") or "").lower()
            if modal != "true":
                continue
            focusable_inside = [n for n in node.elements() if is_focusable(n)]
            if node.attrs.get("tabindex") is None and not focusable_inside:
                self.add("modal-no-focus-management", node=node,
                         evidence=node.snippet())

        # focus order check: positive tabindex moves focus ahead of the DOM
        positives = []
        for position, node in enumerate(focusables):
            tabindex = node.attrs.get("tabindex")
            if tabindex is None:
                continue
            try:
                value = int(tabindex)
            except (TypeError, ValueError):
                continue
            if value > 0:
                positives.append((position, node))
        if positives and positives[0][0] != 0:
            self.add("focus-order-risk", node=positives[0][1],
                     evidence="focusable element with tabindex=%s appears at "
                             "position %d in the DOM" % (
                                 positives[0][1].attrs.get("tabindex"),
                                 positives[0][0] + 1))

    # -- motion --------------------------------------------------------
    def _check_motion(self, elements):
        animated = []
        for node in elements:
            style = node.attrs.get("style") or ""
            if re.search(r"(animation|transition|transform|@keyframes)", style,
                         re.I):
                animated.append(node)
        style_text = " ".join(
            visible_text(node) for node in self.doc.root.find_all("style")
        )
        has_keyframes = bool(re.search(r"@keyframes|animation\s*:", style_text,
                                       re.I))
        marquees = [n for n in elements if n.tag in ("marquee", "blink")]
        autoplay = [n for n in elements
                    if n.tag in ("video", "audio") and "autoplay" in n.attrs]
        refresh = [n for n in self.doc.root.find_all("meta")
                   if (n.attrs.get("http-equiv") or "").lower() == "refresh"]

        for node in marquees:
            self.add("marquee-blink", node=node, evidence=node.snippet())
        for node in autoplay:
            self.add("autoplay-media", node=node, evidence=node.snippet())
        for node in refresh:
            self.add("meta-refresh", node=node, evidence=node.snippet())

        page_text = (self.markup or "").lower()
        reduced = "prefers-reduced-motion" in page_text
        if (animated or has_keyframes or marquees or autoplay) and not reduced:
            detail = []
            if animated:
                detail.append("%d element(s) with CSS animation" % len(animated))
            if has_keyframes:
                detail.append("a keyframes block")
            if marquees:
                detail.append("a marquee element")
            if autoplay:
                detail.append("autoplay media")
            self.add("no-reduced-motion", evidence="; ".join(detail),
                     detail="; ".join(detail))
        if len(animated) >= 5:
            self.add("animation-heavy", evidence="%d animated elements" %
                     len(animated))


# ---------------------------------------------------------------- scoring
def _verdict(score):
    for threshold, key, label in VERDICT_BANDS:
        if score >= threshold:
            return key, label
    return VERDICT_BANDS[-1][1], VERDICT_BANDS[-1][2]


def _score(findings, weights, fragment=False):
    """Compute the axis scores, the overall score and the applied caps."""
    axis_scores = {}
    for axis in AXES:
        penalty = sum(SEVERITY_PENALTY[f["severity"]] for f in findings
                      if f["axis"] == axis)
        axis_scores[axis] = max(0, 100 - penalty)
    overall = sum(axis_scores[a] * weights[a] for a in AXES)

    caps = []
    criticals = [f for f in findings if f["severity"] == "critical"]
    if criticals:
        if len(criticals) >= 4:
            cap = 35
        elif len(criticals) >= 2:
            cap = 45
        else:
            cap = 55
        caps.append({
            "cap": cap,
            "reason": "%d critical finding%s" % (len(criticals),
                                                 "" if len(criticals) == 1
                                                 else "s"),
        })
    if any(f["rule"] == "html-missing-lang" for f in findings):
        caps.append({"cap": 60, "reason": "the page does not declare a "
                                          "language"})
    form_criticals = [f for f in criticals if f["axis"] == "forms"]
    if form_criticals:
        caps.append({"cap": 50, "reason": "a form control has no accessible "
                                          "name"})
    nameless = [f for f in findings
                if f["rule"] in ("focusable-no-name", "widget-role-no-name",
                                 "link-no-name")]
    if len(nameless) >= 3:
        caps.append({"cap": 55, "reason": "%d controls in the tab order have "
                                          "no accessible name" % len(nameless)})
    if not findings and fragment:
        caps.append({"cap": 75, "reason": "this is a fragment, not a whole "
                                          "page, so the page level checks "
                                          "could not run"})

    for entry in caps:
        if overall > entry["cap"]:
            overall = entry["cap"]
    return {
        "overall": round(overall, 1),
        "axes": axis_scores,
        "caps": caps,
    }


def _prioritise(findings, weights):
    def key(finding):
        return (
            SEVERITY_ORDER[finding["severity"]],
            -weights.get(finding["axis"], 0.2),
            finding["rule"],
            finding["path"],
        )
    return sorted(findings, key=key)


def _fix_plan(findings, weights, fragment=False):
    remaining = list(findings)
    current = _score(remaining, weights, fragment=fragment)
    plan = []
    ordered = _prioritise(findings, weights)
    for finding in ordered:
        trial = [f for f in remaining if f is not finding]
        after = _score(trial, weights, fragment=fragment)
        gain = round(after["overall"] - current["overall"], 1)
        plan.append({
            "rule": finding["rule"],
            "severity": finding["severity"],
            "axis": finding["axis"],
            "axis_label": AXIS_LABELS[finding["axis"]],
            "wcag": finding["wcag"],
            "title": finding["title"],
            "why": finding["why"],
            "fix": finding["fix"],
            "path": finding["path"],
            "evidence": finding["evidence"],
            "score_before": current["overall"],
            "score_after": after["overall"],
            "gain": gain,
        })
        remaining = trial
        current = after
    return plan


def _name_map(doc):
    rows = []
    for node in doc.root.elements():
        if not is_interactive(node) and not is_focusable(node):
            continue
        name, source = accessible_name(node, doc)
        rows.append({
            "tag": node.tag,
            "role": _role_of(node),
            "name": name,
            "source": source or "none",
            "path": node.path(),
            "focusable": is_focusable(node),
            "tabindex": node.attrs.get("tabindex", ""),
        })
    return rows


def _focus_order(doc):
    entries = []
    for node in doc.root.elements():
        if not is_focusable(node):
            continue
        tabindex = node.attrs.get("tabindex")
        try:
            value = int(tabindex)
        except (TypeError, ValueError):
            value = None
        if value is not None and value < 0:
            continue
        name, source = accessible_name(node, doc)
        entries.append({
            "tag": node.tag,
            "name": name or "(no name)",
            "source": source or "none",
            "tabindex": value if value is not None else 0,
            "path": node.path(),
        })
    positive = [e for e in entries if e["tabindex"] > 0]
    positive.sort(key=lambda e: e["tabindex"])
    rest = [e for e in entries if e["tabindex"] == 0]
    return positive + rest


def _wcag_coverage(findings):
    by_criterion = {}
    for finding in findings:
        by_criterion.setdefault(finding["wcag"], []).append(finding)

    covered = set()
    for rule in RULES.values():
        if rule["wcag"]:
            covered.add(rule["wcag"])

    rows = []
    for code, title in WCAG_CRITERIA:
        hits = by_criterion.get(code, [])
        if any(f["severity"] in ("critical", "high") for f in hits):
            status = "fail"
        elif hits:
            status = "review"
        elif code in covered:
            status = "pass"
        else:
            status = "not_checked"
        rows.append({
            "code": code,
            "title": title,
            "status": status,
            "issues": len(hits),
        })
    return rows


def _serialize(node, out, annotations):
    if isinstance(node, str):
        out.append(node)
        return
    for comment in annotations.get(id(node), []):
        out.append("<!-- %s -->" % comment)
    if node.tag == "#document":
        for child in node.children:
            _serialize(child, out, annotations)
        return
    attrs = "".join(' %s="%s"' % (key, value.replace('"', "&quot;"))
                     for key, value in node.raw_attrs.items())
    out.append("<%s%s>" % (node.tag, attrs))
    if node.tag in VOID_ELEMENTS:
        return
    for child in node.children:
        _serialize(child, out, annotations)
    out.append("</%s>" % node.tag)


def _annotated_markup(doc, findings):
    annotations = {}
    for finding in findings:
        node = None
        path = finding.get("path")
        if path:
            for candidate in doc.root.elements():
                if candidate.path() == path:
                    node = candidate
                    break
        if node is None:
            continue
        comment = "a11y-fix [%s] %s" % (finding["rule"].upper(),
                                        finding["fix"].replace("--", "-"))
        annotations.setdefault(id(node), []).append(comment)
    out = []
    _serialize(doc.root, out, annotations)
    return "".join(out)


def analyze(markup, profile="general", source_name=""):
    """Run the full audit and return a result dictionary."""
    markup = markup or ""
    audit = Audit(markup, profile=profile, source_name=source_name)
    findings = audit.run()
    doc = audit.doc
    weights = PROFILES[audit.profile]["weights"]
    scored = _score(findings, weights,
                            fragment=doc.html() is None)
    verdict_key, verdict_label = _verdict(scored["overall"])

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        counts[finding["severity"]] += 1

    return {
        "profile": audit.profile,
        "profile_label": PROFILES[audit.profile]["label"],
        "source_name": source_name,
        "score": scored["overall"],
        "verdict": verdict_key,
        "verdict_label": verdict_label,
        "axis_scores": scored["axes"],
        "axis_labels": AXIS_LABELS,
        "weights": weights,
        "caps": scored["caps"],
        "counts": counts,
        "finding_count": len(findings),
        "findings": sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER[f["severity"]], f["rule"], f["path"]),
        ),
        "fix_plan": _fix_plan(findings, weights,
                                 fragment=doc.html() is None),
        "name_map": _name_map(doc),
        "focus_order": _focus_order(doc),
        "wcag_coverage": _wcag_coverage(findings),
        "annotated_markup": _annotated_markup(doc, findings),
        "page_title": doc.title(),
    }
