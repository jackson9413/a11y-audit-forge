"""Dependency-free HTML parser that builds a small DOM tree.

Only the standard library is used. The tree is deliberately shallow: every node
knows its tag, attributes, children and parent, which is everything the
accessibility engine needs to reason about names, roles and focus order.
"""

from html.parser import HTMLParser

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Tags that implicitly close an open element of the same/related kind.
IMPLIED_END = {
    "li": {"li"},
    "dt": {"dt", "dd"},
    "dd": {"dt", "dd"},
    "td": {"td", "th"},
    "th": {"td", "th"},
    "tr": {"tr", "td", "th"},
    "option": {"option"},
    "optgroup": {"option", "optgroup"},
    "tbody": {"tbody", "thead", "tfoot", "tr", "td", "th"},
    "thead": {"thead", "tbody"},
    "tfoot": {"tfoot"},
    "p": {"p"},
}

# Block-level start tags that close an open <p>.
BLOCK_CLOSES_P = {
    "address", "article", "aside", "blockquote", "details", "div", "dl",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "hr", "main", "menu", "nav", "ol", "p",
    "pre", "section", "table", "ul",
}

RAW_TEXT = {"script", "style"}


class Node:
    """A single element in the parsed tree."""

    __slots__ = ("tag", "attrs", "raw_attrs", "children", "parent",
                 "line", "index")

    def __init__(self, tag, attrs=None, parent=None, line=0, index=0,
                 raw_attrs=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.raw_attrs = raw_attrs if raw_attrs is not None else dict(self.attrs)
        self.children = []
        self.parent = parent
        self.line = line
        self.index = index

    # -- traversal -----------------------------------------------------
    def elements(self):
        """Yield every descendant element in document order."""
        for child in self.children:
            if isinstance(child, Node):
                yield child
                for sub in child.elements():
                    yield sub

    def find_all(self, tag):
        return [n for n in self.elements() if n.tag == tag]

    def children_elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def first_child(self, tag):
        for child in self.children_elements():
            if child.tag == tag:
                return child
        return None

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    # -- content -------------------------------------------------------
    def text_content(self):
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            else:
                parts.append(child.text_content())
        return " ".join(parts)

    def own_text(self):
        return " ".join(c for c in self.children if isinstance(c, str))

    # -- identity ------------------------------------------------------
    def path(self):
        """A human readable path such as body > div.card > a."""
        steps = []
        node = self
        while node is not None and node.tag != "#document":
            parent = node.parent
            if parent is None:
                steps.append(node.tag)
                break
            same = [c for c in parent.children_elements() if c.tag == node.tag]
            if len(same) > 1:
                steps.append("%s[%d]" % (node.tag, same.index(node) + 1))
            else:
                steps.append(node.tag)
            node = parent
        return " > ".join(reversed(steps))

    def snippet(self, limit=160):
        """A short outer-ish HTML snippet used as evidence."""
        parts = ["<" + self.tag]
        for key, value in list(self.attrs.items())[:6]:
            parts.append(' %s="%s"' % (key, value[:60]))
        parts.append(">")
        text = self.text_content().strip()
        if text:
            parts.append(" " + text[:limit])
        return "".join(parts)

    def __repr__(self):  # pragma: no cover - debugging helper
        return "<Node %s %r>" % (self.tag, self.attrs)


class Document:
    """The parsed page plus lookup helpers."""

    def __init__(self, root):
        self.root = root
        self._by_id = {}
        self._labels = {}
        for node in root.elements():
            node_id = node.attrs.get("id")
            if node_id:
                self._by_id.setdefault(node_id, []).append(node)
        for node in root.find_all("label"):
            target = node.attrs.get("for")
            if target:
                self._labels.setdefault(target, []).append(node)

    # -- lookups -------------------------------------------------------
    def by_id(self, node_id):
        matches = self._by_id.get(node_id)
        return matches[0] if matches else None

    def ids_for(self, node_id):
        return self._by_id.get(node_id, [])

    def labels_for(self, node_id):
        return self._labels.get(node_id, [])

    def wrapping_label(self, node):
        for ancestor in node.ancestors():
            if ancestor.tag == "label":
                return ancestor
        return None

    def html(self):
        return self.root.first_child("html")

    def body(self):
        html = self.html()
        if html is not None:
            node = html.first_child("body")
            if node is not None:
                return node
        candidates = self.root.find_all("body")
        return candidates[0] if candidates else None

    def head(self):
        return self.root.first_child("head")

    def title(self):
        head = self.head()
        node = head.first_child("title") if head is not None else None
        if node is None:
            candidates = self.root.find_all("title")
            node = candidates[0] if candidates else None
        if node is None:
            return ""
        return node.text_content().strip()


class _TreeBuilder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#document")
        self.stack = [self.root]
        self._counter = 0
        self.unclosed = []

    # -- helpers -------------------------------------------------------
    def _push(self, node):
        self._counter += 1
        node.index = self._counter
        self.stack[-1].children.append(node)

    # -- HTMLParser hooks ---------------------------------------------
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in BLOCK_CLOSES_P and self.stack[-1].tag == "p":
            self.stack.pop()
        implied = IMPLIED_END.get(tag)
        while implied and len(self.stack) > 1 and self.stack[-1].tag in implied:
            self.stack.pop()
        clean = {}
        raw = {}
        for key, value in attrs:
            key_lower = key.lower()
            value = value if value is not None else ""
            clean[key_lower] = value
            raw.setdefault(key, value)
        node = Node(tag, clean, parent=self.stack[-1], line=self.getpos()[0],
                    raw_attrs=raw)
        self._push(node)
        if tag in VOID_ELEMENTS:
            return
        if tag not in RAW_TEXT:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID_ELEMENTS:
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                for dropped in self.stack[index:]:
                    if dropped.tag not in VOID_ELEMENTS:
                        self.unclosed.append(dropped.tag)
                del self.stack[index:]
                return

    def handle_data(self, data):
        if not data:
            return
        if not data.strip():
            # Keep meaningful whitespace out of the tree but keep single spaces
            # so inline text does not get glued together.
            if self.stack[-1].children and isinstance(self.stack[-1].children[-1], str):
                return
        self.stack[-1].children.append(data)

    def handle_comment(self, data):
        return

    def error(self, message):  # pragma: no cover - py<3.10 compat
        return


def parse_html(markup):
    """Parse *markup* and return a :class:`Document`."""
    builder = _TreeBuilder()
    try:
        builder.feed(markup)
        builder.close()
    except Exception:
        pass
    return Document(builder.root)


def escape_attr(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
