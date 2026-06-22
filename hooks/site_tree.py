"""
MkDocs build hook — makes each page's H1 heading the single source of truth
for titles and tree views:

* on_nav: every page's (and section's) nav title is set from its H1, so the
  left sidebar and the home site-tree follow the H1, not hardcoded labels.
* <!-- site-tree --> : nested linked tree of the whole nav (used on the home).
* <!-- subtree -->   : nested linked tree of the current section's children
  (used on section landing pages), so their child lists follow the H1 too.

Edit a page's "# Title" and the nav, the home map, and the parent landing
page all update on the next build.
"""
import os
import re
from urllib.parse import quote

SITE_MARKER = "<!-- site-tree -->"
SUB_MARKER = "<!-- subtree -->"
_NAV = None
_h1_cache = {}

# Pre-filled content for the "+ New page" button (the standard embed stub).
_NEW_PAGE_TEMPLATE = (
    "---\ntags:\n  - Untagged\n---\n# New Entry\n\n"
    '<div class="embed">\n'
    '  <iframe src="https://docs.google.com/document/d/'
    '1aiY9f2HM-02mXnasioowZZki9z0Ce4GV1IvVnlJlIHg/preview"\n'
    '          loading="lazy" title="Citadel Field Library Transcriptions"></iframe>\n'
    "</div>\n\n"
    "[Open in Google Docs ↗](https://docs.google.com/document/d/"
    "1aiY9f2HM-02mXnasioowZZki9z0Ce4GV1IvVnlJlIHg/preview){target=_blank}\n"
)
_REPO_NEW = "https://github.com/ihavedna/citadel-wiki/new/main/docs"

# Landing pages that should NOT show the "+ New page" button (grouping sections
# where entries live in sub-folders, not directly here).
_NO_NEW_PAGE = {
    "delve-reports/index.md",
    "reports-on-vigil/index.md",
}


def _new_page_button(page):
    folder = os.path.dirname(page.file.src_uri)
    url = (f"{_REPO_NEW}/{folder}/?filename=new-entry.md"
           f"&value={quote(_NEW_PAGE_TEMPLATE, safe='')}")
    return (
        f'<a class="new-entry-btn" href="{url}" target="_blank" rel="noopener" '
        f'title="Create a new page in this section, pre-filled with the embed template">'
        f"➕ New page in this section</a>\n\n"
    )


def _h1(file):
    """First Markdown H1 of a page's source file, or None."""
    if file is None:
        return None
    path = file.abs_src_path
    if path in _h1_cache:
        return _h1_cache[path]
    title = None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^#\s+(.+?)\s*$", line)
                if m:
                    title = m.group(1)
                    break
    except OSError:
        pass
    _h1_cache[path] = title
    return title


def _index_of(section):
    return next(
        (c for c in section.children
         if getattr(c, "is_page", False) and c.file and c.file.name == "index"),
        None,
    )


def _descendant_pages(section):
    out = []
    for c in section.children:
        if getattr(c, "is_page", False) and c.file:
            out.append(c)
        elif getattr(c, "is_section", False):
            out += _descendant_pages(c)
    return out


def _attach_indexes(items, config, files):
    """awesome-pages drops a section's index.md from its children, which breaks
    navigation.indexes. Re-insert it as the first child so section landings are
    linked again (and our title-sync can read the H1)."""
    from mkdocs.structure.pages import Page
    for it in items:
        if not getattr(it, "is_section", False):
            continue
        _attach_indexes(it.children, config, files)
        if _index_of(it) is not None:
            continue
        pages = _descendant_pages(it)
        dirs = [os.path.dirname(p.file.src_uri) for p in pages if p.file]
        if not dirs:
            continue
        common = os.path.commonpath(dirs)
        idx_uri = (common + "/index.md") if common else "index.md"
        f = files.get_file_from_path(idx_uri)
        if f is None:
            continue
        if getattr(f, "page", None) is None:
            Page(None, f, config)  # sets f.page
        it.children.insert(0, f.page)


def on_nav(nav, config, files):
    global _NAV
    _NAV = nav
    _h1_cache.clear()
    _attach_indexes(nav.items, config, files)
    _sync_titles(nav.items)
    return nav


def _sync_titles(items):
    for item in items:
        if getattr(item, "is_section", False):
            idx = _index_of(item)
            if idx:
                t = _h1(idx.file)
                if t:
                    item.title = t
            _sync_titles(item.children)
        elif getattr(item, "is_page", False) and item.file:
            t = _h1(item.file)
            if t:
                item.title = t


def _render(items, base, depth):
    """Nested markdown list of nav items; links made relative to `base` dir."""
    out = []
    pad = "    " * depth
    for item in items:
        if getattr(item, "is_section", False):
            idx = _index_of(item)
            if idx:
                rel = os.path.relpath(idx.file.src_uri, base) if base else idx.file.src_uri
                out.append(f"{pad}- [{item.title}]({rel})")
                kids = [c for c in item.children if c is not idx]
            else:
                out.append(f"{pad}- **{item.title}**")
                kids = item.children
            out += _render(kids, base, depth + 1)
        elif getattr(item, "is_page", False) and item.file:
            rel = os.path.relpath(item.file.src_uri, base) if base else item.file.src_uri
            out.append(f"{pad}- [{item.title}]({rel})")
        elif getattr(item, "is_link", False):
            out.append(f"{pad}- [{item.title}]({item.url})")
    return out


def _section_for(items, page):
    """The section whose index page is `page`, searched recursively."""
    for item in items:
        if getattr(item, "is_section", False):
            idx = _index_of(item)
            if idx and idx.file and page.file and idx.file.src_uri == page.file.src_uri:
                return item
            found = _section_for(item.children, page)
            if found:
                return found
    return None


def on_page_markdown(markdown, page, config, files, **kwargs):
    if _NAV is None:
        return markdown
    if SITE_MARKER in markdown:
        body = "\n".join(_render(_NAV.items, "", 0)) + "\n"
        markdown = markdown.replace(SITE_MARKER, body)
    if SUB_MARKER in markdown:
        button = "" if (page.file and page.file.src_uri in _NO_NEW_PAGE) else _new_page_button(page)
        section = _section_for(_NAV.items, page)
        if section is not None:
            base = os.path.dirname(page.file.src_uri)
            idx = _index_of(section)
            kids = [c for c in section.children if c is not idx]
            body = "\n".join(_render(kids, base, 0)) + "\n"
        else:
            body = "_No sub-pages._\n"
        markdown = markdown.replace(SUB_MARKER, button + body)
    return markdown
