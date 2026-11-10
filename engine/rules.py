"""Rule catalogue for the accessibility engine.

Each rule carries the axis it belongs to, a severity, the WCAG 2.2 success
criterion it maps to, why it matters and a concrete fix.
"""

AXES = ["structure", "forms", "media", "keyboard", "motion"]

AXIS_LABELS = {
    "structure": "Structure & ARIA",
    "forms": "Forms & Labels",
    "media": "Images & Media",
    "keyboard": "Keyboard & Focus",
    "motion": "Motion & Timing",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

SEVERITY_PENALTY = {"critical": 26, "high": 12, "medium": 6, "low": 2}

PROFILES = {
    "general": {
        "label": "General page",
        "weights": {"structure": 0.25, "forms": 0.20, "media": 0.15,
                    "keyboard": 0.25, "motion": 0.15},
    },
    "component": {
        "label": "Reusable component",
        "weights": {"structure": 0.15, "forms": 0.25, "media": 0.20,
                    "keyboard": 0.30, "motion": 0.10},
    },
    "form_heavy": {
        "label": "Form or checkout",
        "weights": {"structure": 0.15, "forms": 0.40, "media": 0.10,
                    "keyboard": 0.25, "motion": 0.10},
    },
    "marketing": {
        "label": "Marketing / content page",
        "weights": {"structure": 0.30, "forms": 0.15, "media": 0.20,
                    "keyboard": 0.25, "motion": 0.10},
    },
    "ecommerce": {
        "label": "E-commerce / product page",
        "weights": {"structure": 0.20, "forms": 0.25, "media": 0.25,
                    "keyboard": 0.25, "motion": 0.05},
    },
    "widget": {
        "label": "Embedded widget",
        "weights": {"structure": 0.15, "forms": 0.20, "media": 0.15,
                    "keyboard": 0.40, "motion": 0.10},
    },
}

VERDICT_BANDS = [
    (85, "audit_ready", "Audit ready"),
    (70, "mostly_accessible", "Mostly accessible"),
    (55, "needs_fixes", "Needs fixes"),
    (40, "tight_but_usable", "Tight but usable"),
    (0, "not_accessible", "Not accessible"),
]

VALID_ROLES = {
    "alert", "alertdialog", "application", "article", "banner", "blockquote",
    "button", "caption", "cell", "checkbox", "code", "columnheader", "combobox",
    "complementary", "contentinfo", "definition", "deletion", "dialog",
    "directory", "document", "emphasis", "feed", "figure", "form", "generic",
    "grid", "gridcell", "group", "heading", "img", "insertion", "link", "list",
    "listbox", "listitem", "log", "main", "marquee", "math", "menu", "menubar",
    "menuitem", "menuitemcheckbox", "menuitemradio", "meter", "navigation",
    "none", "note", "option", "paragraph", "presentation", "progressbar",
    "radio", "radiogroup", "region", "row", "rowgroup", "rowheader", "scrollbar",
    "search", "searchbox", "section", "sectionhead", "select", "separator",
    "slider", "spinbutton", "status", "strong", "structure", "subscript",
    "superscript", "switch", "tab", "table", "tablist", "tabpanel", "term",
    "textbox", "time", "timer", "toolbar", "tooltip", "tree", "treegrid",
    "treeitem", "widget", "window",
}

# Roles whose children must be owned by a specific role.
REQUIRED_CHILDREN = {
    "list": {"listitem"},
    "listbox": {"option"},
    "menu": {"menuitem", "menuitemcheckbox", "menuitemradio"},
    "menubar": {"menuitem", "menuitemcheckbox", "menuitemradio"},
    "tablist": {"tab"},
    "grid": {"row", "rowgroup"},
    "table": {"row", "rowgroup"},
    "row": {"cell", "columnheader", "gridcell", "rowheader"},
    "tree": {"treeitem", "group"},
    "radiogroup": {"radio"},
}

ARIA_ATTRIBUTES = {
    "aria-activedescendant", "aria-atomic", "aria-autocomplete", "aria-busy",
    "aria-checked", "aria-colcount", "aria-colindex", "aria-colspan",
    "aria-controls", "aria-current", "aria-describedby", "aria-description",
    "aria-details", "aria-disabled", "aria-dropeffect", "aria-errormessage",
    "aria-expanded", "aria-flowto", "aria-grabbed", "aria-haspopup",
    "aria-hidden", "aria-invalid", "aria-keyshortcuts", "aria-label",
    "aria-labelledby", "aria-level", "aria-live", "aria-modal",
    "aria-multiline", "aria-multiselectable", "aria-orientation",
    "aria-owns", "aria-placeholder", "aria-posinset", "aria-pressed",
    "aria-readonly", "aria-relevant", "aria-required", "aria-roledescription",
    "aria-rowcount", "aria-rowindex", "aria-rowspan", "aria-selected",
    "aria-setsize", "aria-sort", "aria-valuemax", "aria-valuemin",
    "aria-valuenow", "aria-valuetext",
}

# aria-* attributes that must point at one or more existing ids.
ID_REFERENCE_ATTRS = {
    "aria-labelledby": "multiple",
    "aria-describedby": "multiple",
    "aria-controls": "single",
    "aria-owns": "single",
    "aria-flowto": "multiple",
    "aria-activedescendant": "single",
    "aria-errormessage": "single",
    "aria-details": "single",
}

RULES = {
    # ---------------------------------------------------------------- structure
    "html-missing-lang": {
        "axis": "structure", "severity": "critical", "wcag": "3.1.1",
        "title": "The html element has no lang attribute",
        "why": "Screen readers pick a pronunciation voice from the document "
               "language. Without it, assistive tech may read English words "
               "with a Chinese or Hindi voice and become unintelligible.",
        "fix": 'Add a lang attribute to the root element, for example '
               '<html lang="en">.',
    },
    "html-invalid-lang": {
        "axis": "structure", "severity": "medium", "wcag": "3.1.1",
        "title": "The lang attribute is not a valid language tag",
        "why": "An invalid tag such as lang=english is ignored by assistive "
               "technology, which silently loses the pronunciation and "
               "translation benefits.",
        "fix": 'Use a valid BCP 47 tag such as lang="en" or lang="en-GB".',
    },
    "page-missing-title": {
        "axis": "structure", "severity": "high", "wcag": "2.4.2",
        "title": "The page has no title",
        "why": "The title is how screen reader users identify a tab, how "
               "browser history is labelled and how search results are "
               "distinguished.",
        "fix": "Add a unique title element inside the head, for example "
               "Order summary - Acme.",
    },
    "missing-charset": {
        "axis": "structure", "severity": "medium", "wcag": "3.1.2",
        "title": "No character encoding is declared",
        "why": "Without a declared encoding the browser guesses, and a wrong "
               "guess mangles quotes and dashes so copy and screen reader "
               "output break.",
        "fix": "Add a meta charset element set to utf-8 as the first element "
               "in the head.",
    },
    "missing-viewport": {
        "axis": "structure", "severity": "medium", "wcag": "1.4.4",
        "title": "No viewport meta tag",
        "why": "On a phone the page renders at desktop width and the user "
               "has to pinch to zoom before they can read anything.",
        "fix": "Add a viewport meta tag with width=device-width and "
               "initial-scale=1.",
    },
    "viewport-blocks-zoom": {
        "axis": "structure", "severity": "high", "wcag": "1.4.4",
        "title": "The viewport meta blocks zooming",
        "why": "user-scalable=no or maximum-scale=1 stops low vision users "
               "from magnifying the page. It is a WCAG 1.4.4 failure.",
        "fix": "Remove user-scalable=no and any maximum-scale below 2 from "
               "the viewport meta tag.",
    },
    "missing-h1": {
        "axis": "structure", "severity": "medium", "wcag": "1.3.1",
        "title": "The page has no level one heading",
        "why": "The h1 is the top of the heading structure that screen reader "
               "users navigate with heading shortcuts.",
        "fix": "Give the page a single h1 that names what the page is.",
    },
    "heading-skip": {
        "axis": "structure", "severity": "medium", "wcag": "1.3.1",
        "title": "Heading levels are skipped",
        "why": "A jump from h2 to h4 breaks the outline. Users who navigate "
               "by heading land on the wrong level and miss the section "
               "context.",
        "fix": "Use heading levels in order, or set the level explicitly with "
               "a heading role and an aria-level of 3.",
    },
    "multiple-h1": {
        "axis": "structure", "severity": "low", "wcag": "1.3.1",
        "title": "The page has more than one h1",
        "why": "Multiple h1 elements flatten the outline and make it hard for "
               "a screen reader user to know where the page begins.",
        "fix": "Keep one h1 for the page title and demote the rest to h2.",
    },
    "empty-heading": {
        "axis": "structure", "severity": "medium", "wcag": "1.3.1",
        "title": "A heading has no text",
        "why": "An empty heading is announced as just the word heading, which "
               "tells the user nothing and adds noise to the outline.",
        "fix": "Give the heading real text, or remove it from the outline "
               "with a presentational role.",
    },
    "missing-main-landmark": {
        "axis": "structure", "severity": "medium", "wcag": "1.3.1",
        "title": "No main landmark",
        "why": "The main landmark is the skip target that lets keyboard and "
               "screen reader users jump past repeated navigation.",
        "fix": "Wrap the primary content in a main element.",
    },
    "missing-nav-landmark": {
        "axis": "structure", "severity": "low", "wcag": "1.3.1",
        "title": "No navigation landmark",
        "why": "Grouping the site navigation in a nav landmark lets users "
               "jump between the menu and the content.",
        "fix": "Wrap the primary navigation in a nav element.",
    },
    "duplicate-id": {
        "axis": "structure", "severity": "high", "wcag": "4.1.1",
        "title": "An id is used more than once",
        "why": "Duplicate ids break every id reference: label for, "
               "aria-labelledby and aria-controls may point at the wrong "
               "element, so the wrong name is announced.",
        "fix": "Make every id unique on the page.",
    },
    "aria-ref-missing": {
        "axis": "structure", "severity": "critical", "wcag": "4.1.2",
        "title": "An ARIA attribute points at an id that does not exist",
        "why": "The reference resolves to nothing, so the element loses the "
               "name or description it was supposed to get and screen reader "
               "users hear a bare, nameless control.",
        "fix": "Correct the referenced id, or add the missing element with "
               "that id to the page.",
    },
    "aria-ref-ambiguous": {
        "axis": "structure", "severity": "medium", "wcag": "4.1.2",
        "title": "An ARIA attribute references several ids where only one is "
                 "allowed",
        "why": "aria-controls and aria-owns take a single element. With "
               "several ids the relationship is undefined and support is "
               "inconsistent.",
        "fix": "Reference exactly one id for aria-controls and aria-owns.",
    },
    "invalid-role": {
        "axis": "structure", "severity": "high", "wcag": "4.1.2",
        "title": "An unknown role is used",
        "why": "An unrecognised role falls back to the generic role, so the "
               "element loses the semantics you were trying to give it.",
        "fix": "Use a role from the ARIA 1.2 specification.",
    },
    "aria-attr-invalid": {
        "axis": "structure", "severity": "medium", "wcag": "4.1.2",
        "title": "An unknown aria-* attribute is used",
        "why": "Misspelled ARIA attributes are silently ignored, so the "
               "state you meant to expose never reaches the accessibility "
               "tree.",
        "fix": "Check the attribute spelling against the ARIA specification.",
    },
    "aria-attr-bad-value": {
        "axis": "structure", "severity": "medium", "wcag": "4.1.2",
        "title": "An ARIA attribute has an invalid value",
        "why": "Values such as aria-hidden=maybe or aria-level=high are not "
               "in the allowed set, so the state is dropped and the element "
               "is exposed with the wrong semantics.",
        "fix": "Use the documented token for the attribute, for example "
               "aria-hidden set to true.",
    },
    "aria-required-children": {
        "axis": "structure", "severity": "high", "wcag": "4.1.2",
        "title": "A role is missing its required child roles",
        "why": "A list with no listitem children, or a tablist with no tabs, "
               "is an invalid structure. Screen readers announce the count "
               "of items and get it wrong or report nothing.",
        "fix": "Add the required child roles or change the role to match the "
               "content.",
    },
    "role-attr-conflict": {
        "axis": "structure", "severity": "high", "wcag": "4.1.2",
        "title": "A role conflicts with the native element or the ARIA state",
        "why": "Overriding a native element with a conflicting role breaks "
               "the behaviour and the announcement at the same time.",
        "fix": "Keep the native element where it fits, or remove the "
               "conflicting role and ARIA state.",
    },
    "presentation-focusable": {
        "axis": "structure", "severity": "high", "wcag": "4.1.2",
        "title": "A focusable element is marked as presentational",
        "why": "A presentational role removes the semantics from the "
               "accessibility tree, but the element still takes focus. Users "
               "land on something that announces nothing.",
        "fix": "Remove the presentational role, or take the element out of "
               "the tab order.",
    },
    "aria-hidden-focusable": {
        "axis": "structure", "severity": "critical", "wcag": "4.1.2",
        "title": "A focusable element is hidden from assistive technology",
        "why": "aria-hidden set to true on a focusable element, or on a "
               "parent of one, hides content from screen readers while "
               "leaving it in the tab order. Keyboard users focus controls "
               "that announce nothing.",
        "fix": "Remove aria-hidden, or remove the element from the tab order "
               "with a tabindex of -1 if it must stay hidden.",
    },
    "list-structure": {
        "axis": "structure", "severity": "medium", "wcag": "1.3.1",
        "title": "List markup does not match the content",
        "why": "A li outside a list, or a ul whose children are not li, "
               "loses the item count that screen readers announce for every "
               "list.",
        "fix": "Nest li elements directly inside ul or ol elements.",
    },
    "table-missing-header": {
        "axis": "structure", "severity": "high", "wcag": "1.3.1",
        "title": "A data table has no header cells",
        "why": "Without th a screen reader user has no way to know what a "
               "column means, so the table becomes a grid of meaningless "
               "numbers.",
        "fix": "Use th for header cells and give each one a scope.",
    },
    "table-missing-scope": {
        "axis": "structure", "severity": "medium", "wcag": "1.3.1",
        "title": "A header cell has no scope",
        "why": "scope tells assistive technology whether the header applies "
               "to a column or a row. Without it complex tables get guessed "
               "wrong.",
        "fix": 'Add scope="col" or scope="row" to the header cell.',
    },
    "table-missing-caption": {
        "axis": "structure", "severity": "low", "wcag": "1.3.1",
        "title": "A table has no caption",
        "why": "The caption gives the table a name in the screen reader "
               "list of tables, which is often the only way to tell two "
               "similar tables apart.",
        "fix": "Add a caption element as the first child of the table.",
    },
    "div-as-button": {
        "axis": "structure", "severity": "high", "wcag": "4.1.2",
        "title": "A clickable div is used instead of a button",
        "why": "A div is not focusable and has no role, so keyboard and "
               "screen reader users cannot find or trigger it.",
        "fix": 'Use a button element with type="button" for the action.',
    },
    # ------------------------------------------------------------------- forms
    "input-no-label": {
        "axis": "forms", "severity": "critical", "wcag": "3.3.2",
        "title": "A form control has no label",
        "why": "Without a label a screen reader announces the field type and "
               "nothing else. The user cannot tell what belongs in the box.",
        "fix": "Add a label element with a for attribute that matches the "
               "control id, or give the control an aria-label.",
    },
    "placeholder-as-label": {
        "axis": "forms", "severity": "high", "wcag": "3.3.2",
        "title": "A placeholder is used as the only label",
        "why": "Placeholders disappear as soon as the user types, so the "
               "label is gone by the time it is needed, and low contrast "
               "placeholder text is often unreadable.",
        "fix": "Add a real label and keep the placeholder as a short hint.",
    },
    "label-for-mismatch": {
        "axis": "forms", "severity": "high", "wcag": "1.3.1",
        "title": "A label points at an element that does not exist",
        "why": "The click target and the announced name are wired to the "
               "wrong element, so the field is announced with no label at "
               "all.",
        "fix": "Make the label for value match the id of the control.",
    },
    "input-no-type": {
        "axis": "forms", "severity": "medium", "wcag": "3.3.2",
        "title": "An input has no type attribute",
        "why": "The default type is text, which breaks mobile keyboards, "
               "autofill and password managers.",
        "fix": "Set an explicit type such as email or tel.",
    },
    "error-not-associated": {
        "axis": "forms", "severity": "high", "wcag": "3.3.1",
        "title": "An error message is not tied to its field",
        "why": "A red paragraph next to a box is invisible to a screen "
               "reader user. The failure is only discovered after submitting "
               "and hunting for it.",
        "fix": "Link the message with aria-describedby on the field and set "
               "aria-invalid to true.",
    },
    "radio-without-group": {
        "axis": "forms", "severity": "high", "wcag": "1.3.1",
        "title": "A radio group has no fieldset and legend",
        "why": "Screen readers announce each radio separately, so the user "
               "never hears the question the group answers.",
        "fix": "Wrap the radios in a fieldset with a legend that names the "
               "question.",
    },
    "fieldset-missing-legend": {
        "axis": "forms", "severity": "medium", "wcag": "1.3.1",
        "title": "A fieldset has no legend",
        "why": "The legend is the group name. Without it the group is "
               "announced as an unnamed group.",
        "fix": "Add a legend as the first child of the fieldset.",
    },
    "button-no-name": {
        "axis": "forms", "severity": "high", "wcag": "4.1.2",
        "title": "A button has no accessible name",
        "why": "Icon-only buttons are announced as just button. The user "
               "cannot tell what it does.",
        "fix": "Add visible text, or an aria-label with the action spelled "
               "out.",
    },
    "submit-input-no-name": {
        "axis": "forms", "severity": "high", "wcag": "4.1.2",
        "title": "A submit button has no value",
        "why": "A submit input with no value announces Submit, which loses "
               "the meaning of the action.",
        "fix": 'Give the input a value, for example "Create account".',
    },
    "autocomplete-missing": {
        "axis": "forms", "severity": "medium", "wcag": "1.3.5",
        "title": "A common field has no autocomplete attribute",
        "why": "Autocomplete lets browsers and password managers fill known "
               "fields, which is a cognitive and motor help for many users.",
        "fix": "Add an autocomplete value such as name, email, tel, "
               "street-address, organization or current-password.",
    },
    "password-no-autocomplete": {
        "axis": "forms", "severity": "medium", "wcag": "1.3.5",
        "title": "A password field has no autocomplete mode",
        "why": "Without a current-password or new-password autocomplete "
               "value, browsers block password managers and show the wrong "
               "prompt.",
        "fix": "Add autocomplete set to current-password for sign in and "
               "new-password for registration.",
    },
    "input-image-no-alt": {
        "axis": "forms", "severity": "high", "wcag": "1.1.1",
        "title": "An image submit button has no alt text",
        "why": "The image button is the only label for the submit action and "
               "it is skipped entirely when alt is missing.",
        "fix": 'Add alt text describing the action, for example alt="Search".',
    },
    "label-not-associated": {
        "axis": "forms", "severity": "medium", "wcag": "1.3.1",
        "title": "A label is not associated with a control",
        "why": "A label with no for attribute and no wrapped control names "
               "nothing. It reads as loose text.",
        "fix": "Add a for attribute to the label or wrap the control inside "
               "it.",
    },
    "required-not-exposed": {
        "axis": "forms", "severity": "low", "wcag": "3.3.2",
        "title": "A required field is not marked up as required",
        "why": "The required attribute is only announced by some screen "
               "reader and browser combinations when it is also reflected in "
               "the accessibility tree.",
        "fix": "Keep the required attribute and add aria-required set to "
               "true.",
    },
    "no-form-landmark": {
        "axis": "forms", "severity": "low", "wcag": "1.3.1",
        "title": "A form has no accessible name",
        "why": "Named forms appear in the screen reader landmark list, which "
               "is the fastest way to find the checkout form on a long page.",
        "fix": "Give the form an aria-label or a visible heading tied to it.",
    },
    # ------------------------------------------------------------------- media
    "img-missing-alt": {
        "axis": "media", "severity": "critical", "wcag": "1.1.1",
        "title": "An image has no alt attribute",
        "why": "Assistive technology may read out the file name, or nothing "
               "at all, so the content of the image is lost.",
        "fix": "Add alt with a short description, or an empty alt value if "
               "the image is purely decorative.",
    },
    "img-alt-filename": {
        "axis": "media", "severity": "high", "wcag": "1.1.1",
        "title": "The alt text is a file name",
        "why": "Screen readers read the file name aloud character by "
               "character, which tells the user nothing about the content.",
        "fix": "Describe the purpose of the image in a short phrase.",
    },
    "img-alt-redundant": {
        "axis": "media", "severity": "low", "wcag": "1.1.1",
        "title": "The alt text repeats the word image",
        "why": "Every screen reader already announces image, so an alt of "
               "image of a cat is read out as image image of a cat.",
        "fix": "Drop the redundant words and describe the content or the "
               "purpose directly.",
    },
    "img-alt-too-long": {
        "axis": "media", "severity": "low", "wcag": "1.1.1",
        "title": "The alt text is very long",
        "why": "Alt text longer than about 125 characters is usually a "
               "description rather than a label, and it interrupts the "
               "reading flow.",
        "fix": "Shorten the alt text and describe the detail in surrounding "
               "text or a long description.",
    },
    "svg-no-name": {
        "axis": "media", "severity": "high", "wcag": "4.1.2",
        "title": "An inline SVG has no accessible name",
        "why": "An unlabelled SVG is announced as graphic or image, so a "
               "meaningful chart or icon has no name at all.",
        "fix": 'Add role="img" with an aria-label, or role="presentation" '
               'with aria-hidden set to true for decoration.',
    },
    "svg-no-title": {
        "axis": "media", "severity": "medium", "wcag": "1.1.1",
        "title": "An inline SVG has no title element",
        "why": "A title child gives the graphic a name that works with the "
               "name from content for older screen reader and browser pairs.",
        "fix": "Add a title element as the first child of the SVG.",
    },
    "video-no-captions": {
        "axis": "media", "severity": "high", "wcag": "1.2.2",
        "title": "A video has no captions track",
        "why": "Captions are the only way a deaf or hard of hearing user can "
               "follow the content, and they are also needed for people who "
               "cannot hear audio in a noisy place.",
        "fix": 'Add a track element with kind="captions", srclang="en" and '
               'label="English" inside the video.',
    },
    "audio-no-transcript": {
        "axis": "media", "severity": "low", "wcag": "1.2.1",
        "title": "An audio clip has no transcript",
        "why": "A transcript gives an alternative way to consume the audio "
               "and is the only option for many screen reader users.",
        "fix": "Provide a transcript in text near the player and link it.",
    },
    "iframe-no-title": {
        "axis": "media", "severity": "high", "wcag": "4.1.2",
        "title": "An iframe has no title",
        "why": "Screen reader users get a list of iframes with nothing in it, "
               "so they cannot tell which one holds the map or the video.",
        "fix": "Add a title attribute that names the content of the frame.",
    },
    "object-embed-no-title": {
        "axis": "media", "severity": "medium", "wcag": "4.1.2",
        "title": "An object or embed has no title",
        "why": "The title is the only name the accessibility tree can offer "
               "for embedded content.",
        "fix": "Add a title attribute describing the embedded content.",
    },
    "area-no-alt": {
        "axis": "media", "severity": "high", "wcag": "1.1.1",
        "title": "An image map area has no alt text",
        "why": "The area is a separate link with its own name, and without "
               "alt it is announced as an empty link.",
        "fix": "Add alt text describing the destination of the area.",
    },
    # ---------------------------------------------------------------- keyboard
    "link-no-name": {
        "axis": "keyboard", "severity": "critical", "wcag": "4.1.2",
        "title": "A link has no accessible name",
        "why": "A nameless link is announced as just link. The user cannot "
               "tell where it goes.",
        "fix": "Add link text, or an aria-label that names the destination.",
    },
    "focusable-no-name": {
        "axis": "keyboard", "severity": "critical", "wcag": "4.1.2",
        "title": "A focusable element has no accessible name",
        "why": "Anything in the tab order with no name is announced as "
               "nothing at all, which makes the page unusable with a screen "
               "reader.",
        "fix": "Give the element visible text, an aria-label or an "
               "aria-labelledby.",
    },
    "positive-tabindex": {
        "axis": "keyboard", "severity": "high", "wcag": "2.4.3",
        "title": "A positive tabindex is used",
        "why": "Positive tabindex values create a second tab order that "
               "usually does not match the visual order, so focus jumps "
               "around the page.",
        "fix": "Remove the tabindex, or set it to 0 to keep the element in "
               "the natural order.",
    },
    "tabindex-on-static": {
        "axis": "keyboard", "severity": "medium", "wcag": "2.4.3",
        "title": "tabindex is put on a non-interactive element",
        "why": "It puts a non-control into the tab order without giving it "
               "any role or behaviour, which is confusing for screen reader "
               "users.",
        "fix": "Remove the tabindex, or give the element a role and "
               "keyboard handling.",
    },
    "keyboard-handler-no-role": {
        "axis": "keyboard", "severity": "high", "wcag": "2.1.1",
        "title": "A keyboard handler sits on an element with no role",
        "why": "If it responds to keys it must be reachable by keyboard and "
               "announced as the kind of control it behaves like.",
        "fix": "Use a native button, or add a role, a tabindex of 0 and "
               "Enter and Space handling.",
    },
    "no-skip-link": {
        "axis": "keyboard", "severity": "medium", "wcag": "2.4.1",
        "title": "There is no skip link",
        "why": "Keyboard users have to tab through the whole navigation on "
               "every page before reaching the content.",
        "fix": "Add a visually hidden link that points at the main "
               "landmark as the first focusable element.",
    },
    "focus-order-risk": {
        "axis": "keyboard", "severity": "medium", "wcag": "2.4.3",
        "title": "The DOM order and the focus order disagree",
        "why": "When focus moves in a different order from the visual "
               "layout the user loses track of where they are.",
        "fix": "Order the markup the same way the page reads, and use CSS "
               "for layout instead of reordering with flex order or "
               "absolute positioning.",
    },
    "modal-no-focus-management": {
        "axis": "keyboard", "severity": "high", "wcag": "2.4.3",
        "title": "A modal dialog has no focus target",
        "why": "Focus stays behind the dialog, so the screen reader user is "
               "still reading the page they thought they left.",
        "fix": "Give the dialog a tabindex of -1 and focus it on open, then "
               "trap focus inside while it is open.",
    },
    "widget-role-no-name": {
        "axis": "keyboard", "severity": "high", "wcag": "4.1.2",
        "title": "An ARIA widget role has no accessible name",
        "why": "Roles such as button, tab or checkbox with no name are "
               "announced as the role alone, which tells the user nothing.",
        "fix": "Add an aria-label, an aria-labelledby or visible text "
               "content.",
    },
    "custom-control-no-state": {
        "axis": "keyboard", "severity": "medium", "wcag": "4.1.2",
        "title": "A custom control does not expose its state",
        "why": "A toggle that never reports aria-pressed or aria-checked is "
               "announced identically whether it is on or off.",
        "fix": "Set the matching aria state attribute and keep it in sync "
               "with the control.",
    },
    # ------------------------------------------------------------------ motion
    "no-reduced-motion": {
        "axis": "motion", "severity": "medium", "wcag": "2.3.3",
        "title": "The page animates but ignores prefers-reduced-motion",
        "why": "Large motion can trigger nausea and migraines for people with "
               "vestibular disorders.",
        "fix": "Wrap the animation in a prefers-reduced-motion media query "
               "with a no-preference condition, or turn it off under "
               "prefers-reduced-motion set to reduce.",
    },
    "autoplay-media": {
        "axis": "motion", "severity": "medium", "wcag": "1.4.2",
        "title": "Audio or video starts playing automatically",
        "why": "Unexpected sound is disruptive, and WCAG 1.4.2 requires a "
               "way to stop it.",
        "fix": "Remove the autoplay attribute, or provide a visible pause "
               "control.",
    },
    "marquee-blink": {
        "axis": "motion", "severity": "medium", "wcag": "2.2.2",
        "title": "Moving or blinking content is used",
        "why": "Anything that moves for more than five seconds needs a way "
               "to pause it.",
        "fix": "Replace the effect with static content, or provide a pause "
               "control and honour prefers-reduced-motion.",
    },
    "meta-refresh": {
        "axis": "motion", "severity": "medium", "wcag": "2.2.1",
        "title": "The page uses a meta refresh",
        "why": "A timed redirect gives the user no warning and can move "
               "focus unexpectedly, and WCAG 2.2.1 requires the user to be "
               "able to extend a time limit.",
        "fix": "Remove the meta refresh and redirect from the server or with "
               "JavaScript that announces what happens.",
    },
    "animation-heavy": {
        "axis": "motion", "severity": "low", "wcag": "2.3.3",
        "title": "The page defines a large amount of animation",
        "why": "Many concurrent animations compete for attention and are "
               "hard to track for anyone with a cognitive disability.",
        "fix": "Keep animation purposeful and provide a reduced motion "
               "variant.",
    },
}

# WCAG success criteria the engine can speak to, with a short name.
WCAG_CRITERIA = [
    ("1.1.1", "Non-text Content"),
    ("1.2.1", "Audio-only and Video-only (Prerecorded)"),
    ("1.2.2", "Captions (Prerecorded)"),
    ("1.3.1", "Info and Relationships"),
    ("1.3.5", "Identify Input Purpose"),
    ("1.4.2", "Audio Control"),
    ("1.4.4", "Resize Text"),
    ("2.1.1", "Keyboard"),
    ("2.2.1", "Timing Adjustable"),
    ("2.2.2", "Pause, Stop, Hide"),
    ("2.3.3", "Animation from Interactions"),
    ("2.4.1", "Bypass Blocks"),
    ("2.4.2", "Page Titled"),
    ("2.4.3", "Focus Order"),
    ("3.1.1", "Language of Page"),
    ("3.1.2", "Language of Parts"),
    ("3.3.1", "Error Identification"),
    ("3.3.2", "Labels or Instructions"),
    ("4.1.1", "Parsing"),
    ("4.1.2", "Name, Role, Value"),
]
