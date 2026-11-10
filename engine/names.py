"""Accessible name computation.

A pragmatic subset of the HTML-AAM / AccName algorithm: enough to decide
whether a control has a usable name, where that name came from, and to catch
the classic failures (icon-only buttons, unlabelled inputs, ARIA references
that point nowhere).
"""

import re

LABELABLE = {
    "button", "input", "select", "textarea", "meter", "output", "progress",
}

# Roles that carry an interactive or widget meaning for keyboard users.
WIDGET_ROLES = {
    "button", "link", "checkbox", "radio", "switch", "tab", "menuitem",
    "menuitemcheckbox", "menuitemradio", "option", "slider", "spinbutton",
    "textbox", "searchbox", "combobox", "listbox", "treeitem", "gridcell",
    "scrollbar", "separator", "progressbar", "toolbar", "grid",
}

NATIVE_FOCUSABLE = {
    "a", "area", "button", "input", "select", "textarea", "iframe", "object",
    "embed", "audio", "video", "summary", "details",
}

SPACE_RE = re.compile(r"\s+")


def clean(text):
    return SPACE_RE.sub(" ", (text or "")).strip()


def visible_text(node):
    """Text content ignoring script/style subtrees."""
    if node is None:
        return ""
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag not in ("script", "style"):
            parts.append(child.text_content())
    return clean(" ".join(parts))


def referenced_text(doc, ref_id):
    node = doc.by_id(ref_id)
    if node is None:
        return ""
    return visible_text(node)


def _label_for(node, doc):
    node_id = node.attrs.get("id")
    if node_id:
        for label in doc.labels_for(node_id):
            text = visible_text(label)
            if text:
                return text
    wrapper = doc.wrapping_label(node)
    if wrapper is not None:
        text = visible_text(wrapper)
        if text:
            return text
    return ""


def accessible_name(node, doc):
    """Return a (name, source) pair for the given node.

    source is None when the element has no accessible name at all.
    """
    if node is None:
        return ("", None)

    labelledby = node.attrs.get("aria-labelledby")
    if labelledby:
        chunks = [referenced_text(doc, ref) for ref in labelledby.split()]
        joined = clean(" ".join(c for c in chunks if c))
        if joined:
            return (joined, "aria-labelledby")

    aria_label = node.attrs.get("aria-label")
    if aria_label and clean(aria_label):
        return (clean(aria_label), "aria-label")

    tag = node.tag

    if tag == "img":
        alt = node.attrs.get("alt")
        if alt is not None:
            if clean(alt):
                return (clean(alt), "alt")
            return ("", "alt (decorative)")

    if tag == "input":
        input_type = (node.attrs.get("type") or "text").lower()
        if input_type in ("button", "submit", "reset"):
            value = node.attrs.get("value")
            if value and clean(value):
                return (clean(value), "value")
            if input_type == "submit":
                return ("Submit", "default label")
            if input_type == "reset":
                return ("Reset", "default label")
            return ("", None)
        if input_type == "image":
            alt = node.attrs.get("alt")
            if alt is not None and clean(alt):
                return (clean(alt), "alt")
            return ("", None)
        label = _label_for(node, doc)
        if label:
            return (label, "label")
        return ("", None)

    if tag in ("select", "textarea", "meter", "output", "progress"):
        label = _label_for(node, doc)
        if label:
            return (label, "label")
        return ("", None)

    if tag in ("button", "a", "summary"):
        text = visible_text(node)
        if text:
            return (text, "content")
        return ("", None)

    if tag == "label":
        target = node.attrs.get("for")
        if target:
            control = doc.by_id(target)
            if control is not None:
                name, _source = accessible_name(control, doc)
                if name:
                    return (name, "label")
        text = visible_text(node)
        return (text, "content") if text else ("", None)

    if tag == "legend":
        return (visible_text(node), "content")

    if tag == "caption":
        return (visible_text(node), "content")

    if tag in ("th", "td"):
        headers = node.attrs.get("headers")
        if headers:
            chunks = [referenced_text(doc, ref) for ref in headers.split()]
            joined = clean(" ".join(c for c in chunks if c))
            if joined:
                return (joined, "headers")
        return ("", None)

    if tag == "table":
        caption = node.first_child("caption")
        if caption is not None:
            text = visible_text(caption)
            if text:
                return (text, "caption")
        return ("", None)

    if tag == "svg":
        title = node.first_child("title")
        if title is not None:
            text = visible_text(title)
            if text:
                return (text, "title element")
        return ("", None)

    if tag == "fieldset":
        legend = node.first_child("legend")
        if legend is not None:
            text = visible_text(legend)
            if text:
                return (text, "legend")
        return ("", None)

    if tag == "optgroup":
        text = visible_text(node)
        return (text, "content") if text else ("", None)

    if tag == "option":
        text = clean(node.attrs.get("label") or visible_text(node))
        return (text, "content") if text else ("", None)

    text = visible_text(node)
    if text:
        return (text, "content")

    title_attr = node.attrs.get("title")
    if title_attr and clean(title_attr):
        return (clean(title_attr), "title")

    return ("", None)


def is_focusable(node):
    """True when the element can receive keyboard focus."""
    tag = node.tag
    attrs = node.attrs
    if attrs.get("disabled") is not None and tag in (
        "input", "button", "select", "textarea", "fieldset", "optgroup",
        "option",
    ):
        return False
    if tag == "a" and attrs.get("href") is not None:
        return True
    if tag == "input":
        return (attrs.get("type") or "text").lower() != "hidden"
    if tag in ("button", "select", "textarea", "iframe", "summary"):
        return True
    if tag in ("audio", "video", "object", "embed", "area"):
        return True
    if "tabindex" in attrs:
        try:
            return int(attrs["tabindex"]) >= 0
        except (TypeError, ValueError):
            return False
    if attrs.get("contenteditable") is not None:
        return True
    return False


def is_interactive(node):
    """True when the element behaves like a control for a user."""
    tag = node.tag
    attrs = node.attrs
    if tag in ("a", "button", "select", "textarea", "summary"):
        return True
    if tag == "input":
        return (attrs.get("type") or "text").lower() != "hidden"
    if tag in ("audio", "video") and attrs.get("controls") is not None:
        return True
    if tag == "details":
        return True
    if attrs.get("onclick") is not None or attrs.get("onkeydown") is not None:
        return True
    if attrs.get("role") in WIDGET_ROLES:
        return True
    return False
