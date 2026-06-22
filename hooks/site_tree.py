"""
MkDocs build hook: replaces a `<!-- site-tree -->` marker with a nested,
linked tree of the entire site navigation (sections + pages), in nav order.

Sections that have a landing page (index.md) link to it; grouping-only
sections (no index) render as plain labels. Auto-updates with the IA.
"""
MARKER = "<!-- site-tree -->"
_NAV = None


def on_nav(nav, config, files):
    global _NAV
    _NAV = nav
    return nav


def _render(items, depth):
    out = []
    pad = "    " * depth
    for item in items:
        if getattr(item, "is_section", False):
            idx = next(
                (c for c in item.children
                 if getattr(c, "is_page", False) and c.file and c.file.name == "index"),
                None,
            )
            if idx is not None:
                out.append(f"{pad}- [{item.title}]({idx.file.src_uri})")
                kids = [c for c in item.children if c is not idx]
            else:
                out.append(f"{pad}- **{item.title}**")
                kids = item.children
            out += _render(kids, depth + 1)
        elif getattr(item, "is_page", False):
            title = item.title or (item.file.name if item.file else "page")
            if item.file is not None:
                out.append(f"{pad}- [{title}]({item.file.src_uri})")
            else:
                out.append(f"{pad}- {title}")
        elif getattr(item, "is_link", False):
            out.append(f"{pad}- [{item.title}]({item.url})")
    return out


def on_page_markdown(markdown, page, config, files, **kwargs):
    if MARKER not in markdown or _NAV is None:
        return markdown
    tree = "\n".join(_render(_NAV.items, 0)) + "\n"
    return markdown.replace(MARKER, tree)
