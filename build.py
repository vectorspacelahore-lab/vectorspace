#!/usr/bin/env python3
"""
=============================================================================
 VECTOR SPACE — SITE BUILDER
 Run it with:   python3 build.py
 It reads  content/  and  templates/  and writes the finished website
 into  docs/  , which is the folder GitHub Pages publishes.

 Uses nothing but the Python standard library. No installing anything.

 You should not need to edit this file to add topics, courses or pages.
 If you want to change how a page LOOKS, edit templates/base.html or
 static/assets/site.css instead.
=============================================================================
"""

import html
import json
import re
import shutil
from urllib.parse import quote
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "docs"


# ===========================================================================
#  1. READING THE CONTENT FILES
# ===========================================================================

def read_sections(path):
    """Split a content file into its  === name ===  sections.

    Returns a dict of {section name: list of lines}. Comment lines starting
    with # are dropped, so you can annotate your own files freely.
    """
    sections, current = {}, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        # A single # starts a comment and is dropped.
        # TWO hashes (## Heading) is a real heading, so it must survive.
        stripped = line.lstrip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            continue
        m = re.match(r"^\s*===\s*(.+?)\s*===\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def kv(lines):
    """Turn 'name: value' lines into a dict. Blank lines ignored."""
    out = {}
    for line in lines:
        if ":" in line and line.strip():
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def rows(lines, count=None):
    """Turn 'a | b | c' lines into lists. Blank lines ignored.

    If count is given, every row is padded with empty strings to that
    length, so a missing trailing field never crashes the build.
    """
    out = []
    for line in lines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if count:
            parts += [""] * (count - len(parts))
        out.append(parts)
    return out


def bullets(lines):
    """Lines beginning with '- ' become a list of strings."""
    return [l.strip()[2:].strip() for l in lines if l.strip().startswith("- ")]


# ===========================================================================
#  2. TURNING PLAIN TEXT INTO HTML
# ===========================================================================

def inline(text):
    """**bold**, *italic*, [links](/url) and {highlight}yellow{/highlight}."""
    t = html.escape(text)
    t = re.sub(r"\{highlight\}(.+?)\{/highlight\}", r'<span class="hl">\1</span>', t, flags=re.S)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a class="inline-link" href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t, flags=re.S)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", t)
    return t


def prose(lines):
    """Blank-line-separated paragraphs, '## ' headings and '- ' bullets."""
    out, para, bullet = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if bullet:
            items = "".join(f"<li>{inline(b)}</li>" for b in bullet)
            out.append(f'<ul class="prose-list">{items}</ul>')
            bullet.clear()

    for line in lines:
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("## "):
            flush()
            out.append(f'<h2 class="section-title">{inline(s[3:])}</h2>')
        elif s.startswith("- "):
            if para:
                flush()
            bullet.append(s[2:])
        else:
            if bullet:
                flush()
            para.append(s)
    flush()
    return "\n".join(out)


# ===========================================================================
#  3. SHARED PIECES OF PAGE
# ===========================================================================

FORMULAS = {
    "home": [("8%", "3%", "∫ f(x) dx"), ("24%", "70%", "x² + y² = r²"),
             ("64%", "5%", "sinθ · cosθ"), ("76%", "62%", "z = a + bi"),
             ("44%", "40%", "Σ"), ("14%", "44%", "dy/dx")],
    "further-maths": [("14%", "4%", "α + β + γ = −b/a"), ("32%", "70%", "r = a(1 + cosθ)"),
                      ("72%", "6%", "Σ r³"), ("78%", "62%", "M⁻¹")],
    "add-maths": [("14%", "4%", "y = ax² + bx + c"), ("32%", "72%", "logₐ x"),
                  ("72%", "6%", "s = rθ"), ("78%", "64%", "ⁿCᵣ")],
    "page": [("16%", "5%", "f(x)"), ("34%", "72%", "Σ"), ("74%", "8%", "dy/dx"), ("80%", "64%", "∫")],
}


def formulas(kind):
    picks = FORMULAS.get(kind, FORMULAS["page"])
    spans = "\n".join(f'    <span style="top:{t}; left:{l};">{html.escape(x)}</span>'
                      for t, l, x in picks)
    return f'  <div class="hero-formulas" aria-hidden="true">\n{spans}\n  </div>\n'


def hero(eyebrow="", headline="", sub="", meta=None, crumb="", kind="page"):
    parts = ['<header class="hero">', formulas(kind)]
    if crumb:
        parts.append(f'  <div class="crumb">{crumb}</div>')
    if eyebrow:
        parts.append(f'  <div class="eyebrow">{html.escape(eyebrow)}</div>')
    if headline:
        parts.append(f'  <h1 class="title">{inline(headline)}</h1>')
    if sub:
        parts.append(f'  <p class="hero-sub">{inline(sub)}</p>')
    if meta:
        chips = "".join(f"<span>{html.escape(m)}</span>" for m in meta)
        parts.append(f'  <div class="hero-meta">{chips}</div>')
    parts.append("</header>")
    return "\n".join(parts)


def block_label(text):
    return f'<div class="block-label">{html.escape(text)}</div>'


# --- "coming soon" handling -------------------------------------------------
# Nothing on this site is ever allowed to be a dead link. If a PDF is named in
# a content file but hasn't been uploaded to static/ yet, the build notices and
# shows a "Coming soon" tag instead of a link that would 404.

WA_ICON = ('<svg class="wa-icon" viewBox="0 0 24 24" width="18" height="18" '
           'aria-hidden="true" focusable="false"><path fill="currentColor" '
           'd="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.46 1.32 4.96L2 22l5.25-1.38a9.9 '
           '9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 '
           '9.82 0 0 0 12.04 2Zm0 18.15h-.01a8.23 8.23 0 0 1-4.19-1.15l-.3-.18-3.12.82.83-3.04'
           '-.2-.31a8.19 8.19 0 0 1-1.26-4.38c0-4.54 3.7-8.23 8.25-8.23 2.2 0 4.27.86 5.83 '
           '2.41a8.18 8.18 0 0 1 2.41 5.83c0 4.54-3.7 8.23-8.24 8.23Zm4.52-6.16c-.25-.12-1.47'
           '-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.24-.64.8-.78.97-.14.16-.29.18-.54.06-.25'
           '-.13-1.05-.39-1.99-1.23-.74-.66-1.23-1.47-1.38-1.72-.14-.25-.01-.38.11-.5.11-.11'
           '.25-.29.37-.43.12-.15.16-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84'
           '-.2-.48-.4-.42-.56-.43h-.47c-.16 0-.43.06-.65.31-.22.25-.85.83-.85 2.02s.87 2.34 '
           '.99 2.5c.12.16 1.71 2.61 4.15 3.66.58.25 1.03.4 1.39.51.58.19 1.11.16 1.53.1.47'
           '-.07 1.47-.6 1.67-1.18.21-.58.21-1.07.15-1.18-.06-.11-.22-.17-.47-.29Z"/></svg>')

SOON_TAG = '<span class="soon">Coming soon</span>'
MISSING = []          # every file named but not yet uploaded, reported at the end


def asset_ready(folder, fname):
    if not fname:
        return False
    if (STATIC / folder / fname).exists():
        return True
    MISSING.append(f"{folder}/{fname}")
    return False


def file_link(folder, fname, label, cls="resource-link"):
    """A link that OPENS the PDF, or a Coming soon tag if it isn't there yet.

    PDFs open in a new tab so the student views the document and keeps the
    page they came from. They can still save it from the viewer — we just
    don't lead with "download".
    """
    if asset_ready(folder, fname):
        return (f'<a class="{cls}" href="/{folder}/{fname}" target="_blank" '
                f'rel="noopener">{html.escape(label)}</a>')
    return SOON_TAG


def mistake_banner():
    """Shown on every page that carries documents.

    Students are the best proof-readers a resource site has, but only if
    asking is made easy and obvious — so this is a full-width Ink band, not
    a footnote.
    """
    em = S.get("email", "")
    if not em:
        return ""
    return (f'<aside class="mistake-band">'
            f'<span class="course-badge">Help us improve these documents</span>'
            f'<h2 class="mistake-title">Found a mistake?</h2>'
            f'<p>Every document here gets better because someone took a minute to '
            f'say something. A typo, a wrong answer, a step that does not follow, '
            f'an explanation that could be clearer — tell me and I will fix it and '
            f're-upload, usually the same day.</p>'
            f'<p>Whatever you report is fixed for every student who comes after you. '
            f'That is your part in making maths more accessible.</p>'
            f'<a class="mistake-mail" href="mailto:{em}?subject=Mistake%20on%20vectorspace.pk">'
            f'{html.escape(em)}</a></aside>')


def coming_soon_panel(what="This topic"):
    ig = S.get("instagram", "")
    link = (f'<a class="course-cta" href="{ig}" target="_blank" rel="noopener">'
            f'Follow on Instagram</a>' if ig else "")
    return (f'<section class="soon-panel"><span class="course-badge">Coming soon</span>'
            f'<h2 class="course-strip-name">{html.escape(what)} is on its way</h2>'
            f'<p>I\'m working through the syllabus one topic at a time. New lessons, '
            f'notes and worked solutions are announced on Instagram the moment they '
            f'go up — that\'s the fastest way to hear about this one.</p>{link}</section>')


def crumb_trail(items):
    """items = [(label, url or None), ...]; the last one is the current page."""
    out = []
    for label, url in items:
        out.append(f'<a href="{url}">{html.escape(label)}</a>' if url else html.escape(label))
    return ' <span class="sep">/</span> '.join(out)


# ===========================================================================
#  4. LOADING THE SITE
# ===========================================================================

site_file = read_sections(CONTENT / "site.txt")
S = kv(site_file.get("settings", []))
DOMAIN = S.get("domain", "").rstrip("/")

SUBJECTS = []
for slug, name, codes, level, glyph, status, desc in rows(site_file.get("subjects", []), 7):
    SUBJECTS.append(dict(slug=slug, name=name, codes=codes, level=level,
                         glyph=glyph, status=status.lower(), desc=desc))
LIVE = [s for s in SUBJECTS if s["status"] == "live"]

PAPERS = {}
for subj, pslug, plabel, pname, pdesc in rows(site_file.get("papers", []), 5):
    PAPERS.setdefault(subj, []).append(
        dict(slug=pslug, label=plabel, name=pname, desc=pdesc))

# how each subject shows its papers: "cards" (default) or "dropdowns"
LAYOUTS = {s: l.lower() for s, l in rows(site_file.get("layouts", []), 2)}

BASE = (TEMPLATES / "base.html").read_text(encoding="utf-8")

# A short hash of the stylesheet, appended to its URL as ?v=...
# When the CSS changes the URL changes, so browsers are forced to fetch the
# new file instead of serving a stale cached copy. Without this, edits to
# site.css can appear to do nothing until you hard-refresh.
import hashlib
_css = STATIC / "assets" / "site.css"
CSS_VERSION = hashlib.md5(_css.read_bytes()).hexdigest()[:8] if _css.exists() else "1"

NAV_ITEMS = [("Home", "/")] + [(s["name"], f"/{s['slug']}/") for s in LIVE]
NAV_ITEMS += [("Courses", "/courses/"), ("About", "/about/"), ("Contact", "/contact/")]

ALL_PAGES = []      # every page built, for the sitemap
ALL_RESOURCES = []  # every downloadable file, for /resources/


def nav_html(active):
    out = []
    for label, url in NAV_ITEMS:
        cls = ' class="active"' if url == active else ""
        out.append(f'<a href="{url}"{cls}>{html.escape(label)}</a>')
    return "\n    ".join(out)


def footer_links():
    links = [("Resources", "/resources/"), ("Courses", "/courses/"),
             ("About", "/about/"), ("Privacy", "/privacy/")]
    return " · ".join(f'<a href="{u}">{html.escape(l)}</a>' for l, u in links)


def write_page(url, title, description, content, hero_html="", schema=None, og_title=None):
    """Render one page through the layout and save it into docs/."""
    canonical = DOMAIN + url
    page = BASE
    graph = schema or [org_schema(), website_schema()]
    swaps = {
        "{{ TITLE }}": html.escape(title),
        "{{ OG_TITLE }}": html.escape(og_title or title),
        "{{ DESCRIPTION }}": html.escape(description, quote=True),
        "{{ CANONICAL }}": canonical,
        "{{ SITE_NAME }}": html.escape(S.get("site_name", "")),
        "{{ OG_IMAGE }}": DOMAIN + S.get("og_image", "/img/og-default.png"),
        "{{ HANDLE }}": html.escape(S.get("handle", "")),
        "{{ EMAIL }}": html.escape(S.get("email", "")),
        "{{ CSS_VERSION }}": CSS_VERSION,
        "{{ NAV }}": nav_html(url),
        "{{ FOOTER_LINKS }}": footer_links(),
        "{{ HERO }}": hero_html,
        "{{ CONTENT }}": content,
        "{{ SCHEMA }}": json.dumps(graph, ensure_ascii=False, indent=None),
    }
    for k, v in swaps.items():
        page = page.replace(k, v)

    target = OUT / (url.strip("/") + "/index.html" if url != "/" else "index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    ALL_PAGES.append(url)


# ===========================================================================
#  5. SCHEMA (the machine-readable bit Google reads)
# ===========================================================================

def org_schema():
    same = [u for u in (S.get("instagram"), S.get("youtube")) if u]
    return {"@context": "https://schema.org", "@type": "Organization",
            "name": S.get("site_name"), "url": DOMAIN + "/",
            "email": S.get("email"), "sameAs": same,
            "founder": {"@type": "Person", "name": S.get("author")}}


def website_schema():
    return {"@context": "https://schema.org", "@type": "WebSite",
            "name": S.get("site_name"), "url": DOMAIN + "/"}


def person_schema():
    same = [u for u in (S.get("instagram"), S.get("youtube")) if u]
    return {"@context": "https://schema.org", "@type": "Person",
            "name": S.get("author"), "jobTitle": S.get("job_title"),
            "url": DOMAIN + "/about/", "sameAs": same,
            "address": {"@type": "PostalAddress",
                        "addressLocality": S.get("locality"),
                        "addressCountry": S.get("country")}}


def breadcrumb_schema(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name,
                 "item": DOMAIN + url}
                for i, (name, url) in enumerate(items)]}


def video_schema(title, caption, vid):
    return {"@context": "https://schema.org", "@type": "VideoObject",
            "name": f"{title} — {caption}",
            "description": f"{caption}. Part of the {title} lesson.",
            "thumbnailUrl": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "uploadDate": date.today().isoformat(),
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}",
            "publisher": {"@type": "Organization", "name": S.get("site_name")}}


def course_schema(name, desc, url):
    return {"@context": "https://schema.org", "@type": "Course",
            "name": name, "description": desc, "url": DOMAIN + url,
            "provider": {"@type": "Organization", "name": S.get("site_name"),
                         "sameAs": DOMAIN + "/"}}


def faq_schema(pairs):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in pairs]}


# ===========================================================================
#  6. BUILDING EACH KIND OF PAGE
# ===========================================================================

def build_topic(path, subject, paper):
    """One topic page, e.g. /further-maths/further-pure-1/matrices/"""
    sec = read_sections(path)
    meta = kv(sec.get("meta", []))
    slug = path.stem
    title = meta.get("title", slug.replace("-", " ").title())
    url = f"/{subject['slug']}/{paper['slug']}/{slug}/" if paper else f"/{subject['slug']}/{slug}/"
    desc = meta.get("description", f"{title} — videos, notes and worked solutions.")
    heading = f"{title} — {paper['name']} ({subject['codes']})" if paper \
        else f"{title} — {subject['name']} ({subject['codes']})"

    trail = [(subject["name"], f"/{subject['slug']}/")]
    if paper:
        trail.append((paper["name"], f"/{subject['slug']}/{paper['slug']}/"))
    trail.append((title, None))

    body, graph = [], [org_schema(), breadcrumb_schema(
        [("Home", "/")] + [(n, u) for n, u in trail[:-1]] + [(title, url)])]

    # A topic marked "status: soon" shows ONLY the coming-soon panel. The rest
    # of the file is ignored, so a half-finished skeleton can sit in the repo
    # without any of its placeholder text ever reaching the site.
    soon = meta.get("status", "").lower() in ("soon", "coming-soon", "coming soon")
    if soon:
        body.append(coming_soon_panel(title))
        if paper:
            body.append(f'<p class="see-also">In the meantime, the other '
                        f'{html.escape(paper["name"])} topics are '
                        f'<a class="inline-link" href="/{subject["slug"]}/{paper["slug"]}/">'
                        f'here</a>.</p>')
        body.append(byline())
        hero_html = hero(crumb=crumb_trail(trail), headline=title, kind=subject["slug"])
        write_page(url, f"{heading} | {S.get('site_name')}", desc,
                   "\n".join(body), hero_html, graph, og_title=heading)
        return dict(title=title, url=url, order=int(meta.get("order", "99") or 99),
                    slug=slug, soon=True)

    if sec.get("intro"):
        body.append(f'<div class="topic-intro">{prose(sec["intro"])}</div>')

    if sec.get("syllabus"):
        items = "".join(f"<li>{inline(b)}</li>" for b in bullets(sec["syllabus"]))
        body.append('<h2 class="section-title">Syllabus points covered</h2>'
                    f'<ul class="syllabus-list">{items}</ul>')

    # common mistakes belong with the teaching, above the downloads
    if sec.get("mistakes"):
        items = "".join(f"<li>{inline(b)}</li>" for b in bullets(sec["mistakes"]))
        body.append('<h2 class="section-title">Common mistakes</h2>'
                    f'<ol class="mistakes-list">{items}</ol>')

    if sec.get("tips"):
        items = "".join(f"<li>{inline(b)}</li>" for b in bullets(sec["tips"]))
        body.append('<h2 class="section-title">Exam tips</h2>'
                    f'<ul class="tips-list">{items}</ul>')

    vids = rows(sec.get("videos", []), 2)
    if vids:
        body.append(f'<h2 class="section-title">Lecture videos '
                    f'<span class="count">{len(vids)} '
                    f'{"video" if len(vids) == 1 else "videos"}</span></h2>')
        for caption, vid in vids:
            body.append(video_block(caption, vid))
            if vid and "VIDEO_ID" not in vid:
                graph.append(video_schema(title, caption, vid))

    # An "extra" block: any resource that doesn't fit notes / worksheets /
    # topical. The content file supplies its own heading and blurb, so a topic
    # can carry something one-off — a printable grid, a formula card, a table.
    for gname, items in parse_grouped_extra(sec.get("extra", [])):
        body.append(f'<h2 class="section-title">{inline(gname)}</h2>')
        blurb, files = items
        if blurb:
            body.append(f'<p class="use-when">{inline(blurb)}</p>')
        lis = []
        for lbl, fname, fold in files:
            fold = fold or "notes"
            if asset_ready(fold, fname):
                lis.append(f'<li><a class="resource-link" href="/{fold}/{fname}" '
                           f'target="_blank" rel="noopener">{html.escape(lbl)}</a></li>')
                ALL_RESOURCES.append(dict(label=lbl, kind=gname, subject=subject["name"],
                                          topic=title, url=f"/{fold}/{fname}", page=url))
            else:
                lis.append(f'<li class="pending-row"><span>{html.escape(lbl)}</span>'
                           f'{SOON_TAG}</li>')
        body.append(f'<ul class="notes-list">{"".join(lis)}</ul>')

    # Resources come AFTER the teaching content above, in the order a student
    # should meet them: learn it, practise it, then attempt exam questions.
    # Each block carries a line explaining when to use it.
    BLOCKS = [
        ("notes", "Lecture notes", "notes", None),
        ("worksheets", "Worksheets", "worksheets",
         "Use these as soon as you've learned the topic and need to practise it. "
         "Start with the worksheet, check yourself against the answers, and only "
         "then look at the step-by-step solutions."),
        ("topical", "Topical past papers", "papers",
         "Move on to these once you've worked through the worksheets and are ready "
         "for harder, exam-style questions. Real past-paper questions on this topic, "
         "with the official mark scheme and full worked solutions."),
    ]
    for key, label, folder, blurb in BLOCKS:
        files = rows(sec.get(key, []), 3)
        if not files:
            continue
        body.append(f'<h2 class="section-title">{label}</h2>')
        if blurb:
            body.append(f'<p class="use-when">{blurb}</p>')
        lis = []
        for lbl, fname, alt in files:
            # a row may name a file in a second folder (e.g. solutions live in
            # static/solutions/ even though the row sits under Worksheets)
            fold = "solutions" if alt.strip().lower() == "solutions" else folder
            if asset_ready(fold, fname):
                lis.append(f'<li><a class="resource-link" href="/{fold}/{fname}" '
                           f'target="_blank" rel="noopener">'
                           f'{html.escape(lbl)}</a></li>')
                ALL_RESOURCES.append(dict(label=lbl, kind=label, subject=subject["name"],
                                          topic=title, url=f"/{fold}/{fname}", page=url))
            else:
                lis.append(f'<li class="pending-row"><span>{html.escape(lbl)}</span>'
                           f'{SOON_TAG}</li>')
        body.append(f'<ul class="notes-list">{"".join(lis)}</ul>')

    # a pointer to the full yearly archive, rather than repeating it per topic
    if has_past_papers(subject["slug"]):
        body.append(f'<p class="see-also">Looking for whole papers by session? '
                    f'<a class="inline-link" href="/{subject["slug"]}/past-papers/">'
                    f'All {html.escape(subject["name"])} past papers</a></p>')

    body.append(mistake_banner())

    pairs = qa_pairs(sec.get("faq", []))
    if pairs:
        body.append('<h2 class="section-title">Questions students ask</h2>')
        body.append("".join(
            f'<details class="faq"><summary>{inline(q)}</summary>'
            f'<div class="faq-a">{inline(a)}</div></details>' for q, a in pairs))
        graph.append(faq_schema(pairs))

    body.append(byline())

    hero_html = hero(crumb=crumb_trail(trail), headline=title,
                     kind=subject["slug"])
    write_page(url, f"{heading} | {S.get('site_name')}", desc,
               "\n".join(body), hero_html, graph, og_title=heading)
    return dict(title=title, url=url, order=int(meta.get("order", "99") or 99),
                slug=slug, soon=soon)


def video_block(caption, vid):
    safe = html.escape(vid)
    if not vid or "VIDEO_ID" in vid:
        return (f'<div class="video-block"><div class="video-label">'
                f'{html.escape(caption)}</div>'
                f'<div class="video-wrap video-pending">Video coming soon</div></div>')
    return (f'<div class="video-block"><div class="video-label">{html.escape(caption)}</div>'
            f'<div class="video-wrap"><button class="video-facade" data-id="{safe}" '
            f'data-title="{html.escape(caption, quote=True)}" '
            f'style="background-image:url(https://i.ytimg.com/vi/{safe}/hqdefault.jpg)" '
            f'aria-label="Play: {html.escape(caption, quote=True)}">'
            f'<span class="video-play" aria-hidden="true">▶</span></button></div></div>')


def papers_table(papers, subject_name="", session=""):
    """Rows of:  Variant | question paper | mark scheme | solved paper

    The session (e.g. "May/June 2025") is the dropdown heading above, so it
    isn't repeated on every row.
    """
    out = ['<div class="table-wrap"><table class="papers"><thead><tr>'
           '<th>Paper</th><th>Question paper</th>'
           '<th>Mark scheme</th><th>Solved paper</th></tr></thead><tbody>']
    for variant, qp, ms, solved in papers:
        cells = [("Question paper", file_link("papers", qp, "View PDF")),
                 ("Mark scheme", file_link("papers", ms, "View PDF")),
                 ("Solved paper", file_link("solutions", solved, "View PDF"))]
        if subject_name and asset_ready("solutions", solved):
            ALL_RESOURCES.append(dict(label=f"{session} paper {variant} — solved",
                                      kind="Solved papers", subject=subject_name,
                                      topic=session, url=f"/solutions/{solved}", page="/"))
        tds = "".join(f'<td data-label="{k}">{v}</td>' for k, v in cells)
        out.append(f'<tr><td><span class="tag">Paper {html.escape(variant)}</span></td>'
                   f'{tds}</tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def parse_grouped_extra(lines):
    """An extra resource block with its own heading and explanation.

        > Trouble sketching polar curves?
        A line of plain text explaining when to use it.
        Label | filename.pdf | notes

    The third column is the folder in static/ (defaults to notes).
    Returns [(heading, (blurb, [(label, file, folder), ...])), ...]
    """
    groups, head, blurb, files = [], None, "", []

    def flush():
        if head and files:
            groups.append((head, (blurb, list(files))))

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith(">"):
            flush()
            head, blurb, files = s[1:].strip(), "", []
        elif "|" in s:
            parts = [p.strip() for p in s.split("|")] + ["", ""]
            files.append((parts[0], parts[1], parts[2]))
        elif head:
            blurb = (blurb + " " + s).strip()
    flush()
    return groups


def parse_grouped(lines, nfields):
    """Rows split into groups. A line starting with '>' opens a new group."""
    groups, current = [], None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith(">"):
            current = (s[1:].strip(), [])
            groups.append(current)
        elif "|" in s:
            parts = [p.strip() for p in s.split("|")] + [""] * nfields
            if current is None:
                current = ("All", [])
                groups.append(current)
            current[1].append(tuple(parts[:nfields]))
    return [g for g in groups if g[1]]


def qa_pairs(lines):
    pairs, q = [], None
    for line in lines:
        s = line.strip()
        if s.upper().startswith("Q:"):
            q = s[2:].strip()
        elif s.upper().startswith("A:") and q:
            pairs.append((q, s[2:].strip()))
            q = None
    return pairs


def byline():
    return (f'<p class="byline">Written and taught by '
            f'<a href="/about/">{html.escape(S.get("author", ""))}</a>, '
            f'{html.escape(S.get("job_title", "").lower())}.</p>')


def build_subject(subject, topics_by_paper, loose_topics):
    """A subject hub, e.g. /further-maths/"""
    url = f"/{subject['slug']}/"
    body = []
    papers = PAPERS.get(subject["slug"], [])
    total = sum(len(v) for v in topics_by_paper.values()) + len(loose_topics)

    if papers:
        word = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}.get(len(papers), len(papers))
        body.append(block_label(f"The {word} papers"))

        if LAYOUTS.get(subject["slug"], "cards") == "dropdowns":
            # one dropdown per paper, with its chapters listed inside
            for i, p in enumerate(papers):
                tops = sorted(topics_by_paper.get(p["slug"], []), key=lambda t: t["order"])
                ready = sum(1 for t in tops if not t.get("soon"))
                state = f"{ready} of {len(tops)} ready" if tops else "Coming soon"
                lis = "".join(
                    f'<li class="topical-row"><span class="topical-name">'
                    f'<a class="resource-link" href="{t["url"]}">{html.escape(t["title"])}</a>'
                    f'</span><span class="topical-links">'
                    f'{"" if not t.get("soon") else SOON_TAG}</span></li>' for t in tops)
                inner = (f'<ul class="topical-list">{lis}</ul>' if tops else
                         '<p class="empty-note">Topics for this paper are being written.</p>')
                body.append(
                    f'<details class="paper-drop">'
                    f'<summary><span class="paper-num">{html.escape(p["label"])}</span>'
                    f'<span class="drop-name">{html.escape(p["name"])}</span>'
                    f'<span class="drop-count">{state}</span></summary>'
                    f'<p class="drop-desc">{html.escape(p["desc"])}</p>'
                    f'{inner}'
                    f'<p class="drop-more"><a class="inline-link" '
                    f'href="/{subject["slug"]}/{p["slug"]}/">Open {html.escape(p["label"])}</a></p>'
                    f'</details>')
        else:
            # a card per paper
            cards = []
            for p in papers:
                n = len(topics_by_paper.get(p["slug"], []))
                cards.append(
                    f'<a class="paper-card" href="/{subject["slug"]}/{p["slug"]}/">'
                    f'<span class="paper-num">{html.escape(p["label"])}</span>'
                    f'<h2 class="paper-title">{html.escape(p["name"])}</h2>'
                    f'<p class="paper-desc">{html.escape(p["desc"])}</p>'
                    f'<span class="paper-go">{n} topic{"s" if n != 1 else ""}</span></a>')
            body.append(f'<div class="paper-grid">{"".join(cards)}</div>')

    else:
        body.append(block_label("Chapters — syllabus order"))
        body.append(chapter_grid(sorted(loose_topics, key=lambda t: t["order"]), url))

    # the past papers band sits at the foot of every subject page that has one
    if has_past_papers(subject["slug"]):
        body.append(f'''<a class="papers-band" href="/{subject['slug']}/past-papers/">
          <div><span class="course-badge">Past papers</span>
          <h2 class="course-strip-name">Past papers</h2>
          <p>Whole papers by session, and the same questions sorted by topic.</p></div>
          <span class="course-cta">Open</span></a>''')

    hero_html = hero(eyebrow=subject["level"], headline=subject["name"],
                     sub=subject["desc"],
                     meta=[f"Syllabus {subject['codes']}",
                           f"{total} topic{'s' if total != 1 else ''}",
                           "Free — no sign-up"],
                     kind=subject["slug"])
    write_page(url, f"{subject['name']} ({subject['codes']}) | {S.get('site_name')}",
               subject["desc"], "\n".join(body), hero_html,
               [org_schema(), course_schema(
                   f"{subject['name']} {subject['codes']}", subject["desc"], url),
                breadcrumb_schema([("Home", "/"), (subject["name"], url)])])


def has_past_papers(subject_slug):
    return (CONTENT / subject_slug / "past-papers.txt").exists()


def parse_topical(lines):
    """Topical papers, grouped by paper.

    A line starting with '>' opens a new group (one dropdown on the page).
    Every line after it is:
        Topic name | questions file | mark scheme file | worked solutions file
    Questions and mark schemes live in static/papers/ , worked solutions in
    static/solutions/ . Any of the three may be left blank.
    """
    groups, current = [], None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith(">"):
            current = (s[1:].strip(), [])
            groups.append(current)
        elif "|" in s:
            parts = [p.strip() for p in s.split("|")] + ["", "", ""]
            if current is None:
                current = ("All topics", [])
                groups.append(current)
            current[1].append((parts[0], parts[1], parts[2], parts[3]))
    return [g for g in groups if g[1]]


def build_past_papers(subject):
    """The past papers page for a subject, e.g. /further-maths/past-papers/

    Built from  content/<subject>/past-papers.txt  — a file with that exact
    name is treated as this page rather than as a topic.
    """
    path = CONTENT / subject["slug"] / "past-papers.txt"
    sec = read_sections(path)
    meta = kv(sec.get("meta", []))
    url = f"/{subject['slug']}/past-papers/"
    body = []

    if sec.get("intro"):
        body.append(f'<div class="topic-intro">{prose(sec["intro"])}</div>')

    groups = parse_topical(sec.get("topical", []))
    if groups:
        body.append('<h2 class="section-title">Past papers by topic '
                    '<span class="count">topicals</span></h2>')
        body.append('<p class="see-also">Every past question on a single topic, '
                    'collected into one file. Open a paper to see its topics.</p>')
        for gi, (gname, items) in enumerate(groups):
            lis = []
            for name, qfile, mfile, sfile in items:
                # one table row per topic, so the three columns line up down
                # the whole list instead of wrapping differently on each row
                cells = []
                for folder, fname, label, kind in (
                        ("papers", qfile, "Questions", "Topical past papers"),
                        ("papers", mfile, "Mark scheme", "Mark schemes"),
                        ("solutions", sfile, "Worked solutions", "Worked solutions")):
                    if asset_ready(folder, fname):
                        cells.append(f'<td data-label="{label}">'
                                     f'<a class="resource-link" href="/{folder}/{fname}" '
                                     f'target="_blank" rel="noopener">View PDF</a></td>')
                        ALL_RESOURCES.append(dict(label=f"{name} — {label.lower()}",
                                                  kind=kind, subject=subject["name"],
                                                  topic=name, url=f"/{folder}/{fname}", page=url))
                    else:
                        cells.append(f'<td data-label="{label}">'
                                     f'<span class="soon-lite">Soon</span></td>')
                lis.append(f'<tr><td class="topical-name">{html.escape(name)}</td>'
                           f'{"".join(cells)}</tr>')
            ready = sum(1 for n, q, m, s in items
                        if (STATIC / "papers" / q).exists() or (STATIC / "papers" / m).exists()
                        or (STATIC / "solutions" / s).exists())
            state = f"{ready} of {len(items)} ready" if ready else "Coming soon"
            body.append(
                f'<details class="paper-drop">'
                f'<summary><span class="drop-name">{html.escape(gname)}</span>'
                f'<span class="drop-count">{state}</span></summary>'
                f'<div class="table-wrap"><table class="papers topical-table">'
                f'<thead><tr><th>Topic</th><th>Questions</th><th>Mark scheme</th>'
                f'<th>Worked solutions</th></tr></thead>'
                f'<tbody>{"".join(lis)}</tbody></table></div></details>')

    yearly = parse_grouped(sec.get("yearly", []), 4)
    if yearly:
        body.append('<h2 class="section-title">Past papers by session '
                    '<span class="count">whole papers</span></h2>')
        body.append('<p class="see-also">Whole papers under timed conditions. '
                    'Open a session to see its variants.</p>')
        for session, items in yearly:
            ready = sum(1 for v, q, m, so in items if (STATIC / "papers" / q).exists())
            state = f"{ready} of {len(items)} papers" if ready else "Coming soon"
            body.append(
                f'<details class="paper-drop">'
                f'<summary><span class="paper-num">{html.escape(session)}</span>'
                f'<span class="drop-count">{state}</span></summary>'
                f'{papers_table(items, subject["name"], session)}</details>')

    body.append(mistake_banner())

    trail = [(subject["name"], f"/{subject['slug']}/"), ("Past papers", None)]
    hero_html = hero(crumb=crumb_trail(trail),
                     headline=meta.get("headline", "Past papers"),
                     sub=meta.get("sub", ""), kind=subject["slug"])
    write_page(url, f"{subject['name']} ({subject['codes']}) past papers | {S.get('site_name')}",
               meta.get("description", ""), "\n".join(body), hero_html,
               [org_schema(), breadcrumb_schema(
                   [("Home", "/"), (subject["name"], f"/{subject['slug']}/"),
                    ("Past papers", url)])])


def build_paper(subject, paper, topics):
    """A paper hub, e.g. /further-maths/further-pure-1/"""
    url = f"/{subject['slug']}/{paper['slug']}/"
    tops = sorted(topics, key=lambda t: t["order"])
    body = [block_label("Topics — syllabus order"), chapter_grid(tops, url)]
    trail = [(subject["name"], f"/{subject['slug']}/"), (paper["name"], None)]
    hero_html = hero(crumb=crumb_trail(trail), eyebrow=paper["label"],
                     headline=paper["name"], sub=paper["desc"],
                     meta=[f"{len(tops)} topic{'s' if len(tops) != 1 else ''}"],
                     kind=subject["slug"])
    write_page(url, f"{paper['name']} — {subject['name']} ({subject['codes']}) | {S.get('site_name')}",
               paper["desc"], "\n".join(body), hero_html,
               [org_schema(), course_schema(paper["name"], paper["desc"], url),
                breadcrumb_schema([("Home", "/"), (subject["name"], f"/{subject['slug']}/"),
                                   (paper["name"], url)])])


def chapter_grid(topics, base_url):
    if not topics:
        return ('<p class="empty-note">Topics for this paper are being written. '
                'Follow along on Instagram to hear when they go up.</p>')
    cards = []
    for i, t in enumerate(topics, 1):
        tag = '<span class="card-soon">Soon</span>' if t.get("soon") else ""
        cls = "chapter-card is-soon" if t.get("soon") else "chapter-card"
        cards.append(f'<a class="{cls}" href="{t["url"]}">'
                     f'<span class="chapter-num">{i:02d}</span>'
                     f'<span class="chapter-name">{html.escape(t["title"])}</span>'
                     f'{tag}</a>')
    return f'<div class="chapter-grid">{"".join(cards)}</div>'


def build_home():
    sec = read_sections(CONTENT / "pages" / "home.txt")
    meta, h = kv(sec.get("meta", [])), kv(sec.get("hero", []))
    body = []

    # courses come FIRST — they're the thing being sold. Free resources follow.
    strip = course_strip()
    if strip:
        body.append(strip)

    body.append('<section class="resources-block">')
    body.append('<div class="home-head">'
                '<h2 class="home-head-title"><span class="hl">Free</span> resources</h2>'
                '<p class="home-head-sub">Every topic, every past paper, every mark scheme. '
                'No sign-up, no paywall, no catch.</p>'
                '</div>')

    # every subject gets a card. The ones not started yet are greyed out and
    # marked Coming soon rather than hidden, so students can see what's planned.
    cards = []
    for s in SUBJECTS:
        glyph = html.escape(s["glyph"])
        tag = f'{html.escape(s["level"])} · {html.escape(s["codes"])}'
        if s["status"] == "live":
            n = count_topics(s["slug"])
            cards.append(
                f'<a class="subject-card" href="/{s["slug"]}/" data-glyph="{glyph}">'
                f'<span class="subject-tag">{tag}</span>'
                f'<div class="subject-title">{html.escape(s["name"])}</div>'
                f'<div class="subject-desc">{html.escape(s["desc"])}</div>'
                f'<span class="subject-go">{n} chapter{"s" if n != 1 else ""}</span></a>')
        else:
            cards.append(
                f'<div class="subject-card is-soon" data-glyph="{glyph}">'
                f'<span class="subject-tag">{tag}</span>'
                f'<div class="subject-title">{html.escape(s["name"])}</div>'
                f'<div class="subject-desc">{html.escape(s["desc"])}</div>'
                f'<span class="subject-go">Coming soon</span></div>')
    body.append(f'<div class="subject-grid">{"".join(cards)}</div>')
    body.append('</section>')

    # a short "who's behind this" strip that sends people to the About page,
    # rather than repeating the whole story on the home page
    if sec.get("about"):
        body.append('<section class="about-strip">'
                    + '<div class="home-head">'
                      '<h2 class="home-head-title"><span class="hl">Who\'s</span> behind this</h2>'
                      '</div>'
                    + '<div class="about-strip-inner">'
                    + f'<img src="/img/ali-hashir-small.jpg" alt="Ali Hashir" '
                      f'width="600" height="450" loading="lazy">'
                    + '<div>' + prose(sec["about"])
                    + '<p><a class="course-cta" href="/about/">More about me</a></p>'
                    + '</div></div></section>')

    hero_html = hero(eyebrow=h.get("eyebrow", ""), headline=h.get("headline", ""),
                     sub=h.get("sub", ""),
                     meta=[l.strip() for l in sec.get("hero_meta", []) if l.strip()],
                     kind="home")
    write_page("/", f"{S.get('site_name')} — {S.get('tagline')}",
               meta.get("description", ""), "\n".join(body), hero_html,
               [org_schema(), website_schema(), person_schema()])


def aside_panel(heading, items):
    lis = "".join(f'<li><span><strong>{html.escape(a)}</strong> — {html.escape(b)}</span></li>'
                  for a, b in items)
    return (f'<aside class="about-aside"><h3>{html.escape(heading)}</h3>'
            f'<ul>{lis}</ul></aside>')


def count_topics(subject_slug):
    """How many chapters a subject has. past-papers.txt isn't a chapter."""
    d = CONTENT / subject_slug
    if not d.exists():
        return 0
    return len([f for f in d.rglob("*.txt") if f.name != "past-papers.txt"])


def parse_courses(lines):
    """Courses are separated by a line of three dashes."""
    out, block = [], []
    for line in lines:
        if line.strip() == "---":
            if block:
                out.append(kv(block))
            block = []
        else:
            block.append(line)
    if block:
        out.append(kv(block))
    return [c for c in out if c.get("name")]


COURSES = []


def build_courses():
    global COURSES
    sec = read_sections(CONTENT / "pages" / "courses.txt")
    meta = kv(sec.get("meta", []))
    COURSES = parse_courses(sec.get("courses", []))
    body, graph = [], [org_schema()]

    if sec.get("intro"):
        body.append(f'<div class="topic-intro">{prose(sec["intro"])}</div>')

    if sec.get("timetable"):
        body.append(timetable(sec["timetable"]))

    for status, label in (("open", "Open for enrolment"),
                          ("soon", "Announced — not open yet"),
                          ("past", "Previously run")):
        group = [c for c in COURSES if c.get("status", "").lower() == status]
        if not group:
            continue
        body.append(f'<h2 class="section-title">{label}</h2>')
        for c in group:
            body.append(course_card(c, status))
            graph.append(course_schema(c["name"], c.get("summary", ""), "/courses/"))

    if sec.get("fee_note"):
        body.append(f'<p class="fee-note">{prose(sec["fee_note"])}</p>')

    body.append('<h2 class="section-title" id="enquire">How to register</h2>')
    if sec.get("form_intro"):
        body.append(f'<div class="topic-intro">{prose(sec["form_intro"])}</div>')
    body.append(whatsapp_block())
    write_page("/courses/", f"Courses | {S.get('site_name')}",
               meta.get("description", ""), "\n".join(body),
               hero(eyebrow=meta.get("eyebrow", ""), headline=meta.get("headline", ""),
                    kind="page"), graph)


def timetable(lines):
    """Course | Days | Time  ->  a small schedule table."""
    rowsx = rows(lines, 3)
    if not rowsx:
        return ""
    trs = "".join(
        f'<tr><td>{html.escape(c)}</td>'
        f'<td data-label="Days">{html.escape(d)}</td>'
        f'<td data-label="Time"><span class="tag">{html.escape(t)}</span></td></tr>'
        for c, d, t in rowsx)
    return ('<h2 class="section-title">Weekly timetable</h2>'
            '<div class="table-wrap"><table class="papers"><thead><tr>'
            '<th>Course</th><th>Days</th><th>Time</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div>'
            '<p class="table-note">All times are Pakistan Standard Time. '
            'Every session is recorded, and recordings are sent to anyone who '
            'misses a class.</p>')


def course_card(c, status):
    fields = [("Syllabus", c.get("syllabus")), ("Starts", c.get("starts")),
              ("For examination", c.get("exam")), ("Format", c.get("format")),
              ("Duration", c.get("duration")), ("Schedule", c.get("schedule")),
              ("Fee", c.get("fee"))]
    dl = "".join(f'<div class="course-field"><dt>{html.escape(k)}</dt>'
                 f'<dd>{html.escape(v)}</dd></div>'
                 for k, v in fields if v)
    badge = {"open": "Open now", "soon": "Coming soon", "past": "Finished"}.get(status, "")
    # Registration happens on the Google Form. WhatsApp is for questions.
    wa, form = S.get("whatsapp", ""), S.get("registration_form", "")
    msg = f"Hi Ali, I have a question about the {c['name']} course."
    buttons = []
    if status in ("open", "soon"):
        if form:
            buttons.append(f'<a class="course-cta" href="{form}" target="_blank" '
                           f'rel="noopener">Register</a>')
        if wa:
            buttons.append(f'<a class="course-cta course-cta-wa" '
                           f'href="https://wa.me/{wa}?text={quote(msg)}" '
                           f'target="_blank" rel="noopener">{WA_ICON}'
                           f'Ask a question on WhatsApp</a>')
    cta = f'<div class="course-actions">{"".join(buttons)}</div>' if buttons else ""
    return (f'<article class="course-card course-{status}">'
            f'<span class="course-badge">{html.escape(badge)}</span>'
            f'<h3 class="course-name">{html.escape(c["name"])}</h3>'
            f'<p class="course-summary">{html.escape(c.get("summary", ""))}</p>'
            f'<dl class="course-fields">{dl}</dl>{cta}</article>')


def whatsapp_block():
    """Registration is a Google Form; WhatsApp is for questions. No forms on-site."""
    wa, form = S.get("whatsapp", ""), S.get("registration_form", "")
    out = []
    if form:
        out.append(f'<a class="wa-block" href="{form}" target="_blank" rel="noopener">'
                   f'<span class="course-badge">Step 1</span>'
                   f'<h3 class="course-strip-name">Fill in the registration form</h3>'
                   f'<p>Takes a couple of minutes. Tell me which course you want and '
                   f'how to reach you, and I\'ll follow up with the joining details '
                   f'and payment information.</p>'
                   f'<span class="wa-number">Open the form</span></a>')
    if wa:
        msg = "Hi Ali, I have a question about your courses."
        out.append(f'<a class="wa-block wa-block-alt" '
                   f'href="https://wa.me/{wa}?text={quote(msg)}" '
                   f'target="_blank" rel="noopener">'
                   f'<span class="course-badge course-badge-wa">{WA_ICON}WhatsApp</span>'
                   f'<h3 class="course-strip-name">Message me on WhatsApp</h3>'
                   f'<p>Not sure which course fits, or anything else you want to ask '
                   f'before registering — this is the fastest way to reach me.</p>'
                   f'<span class="wa-number">{WA_ICON}+{html.escape(wa)}</span></a>')
    return f'<div class="wa-grid">{"".join(out)}</div>' if out else ""



def course_strip():
    """The 'next course' band on the home page. Hidden if nothing is announced."""
    live = [c for c in COURSES if c.get("status", "").lower() in ("open", "soon")]
    if not live:
        return ""
    n = len(live)
    starts = sorted({c.get("starts", "") for c in live if c.get("starts")})
    when = f" starting {starts[0]}" if len(starts) == 1 else ""
    return (f'<a class="course-strip" href="/courses/">'
            f'<div><span class="course-badge">Enrolling now</span>'
            f'<h2 class="course-strip-name">{n} taught course'
            f'{"s" if n != 1 else ""}{html.escape(when)}</h2>'
            f'<p>Live online classes with recordings, four evenings a week, '
            f'run straight through to the exam. Small groups so questions '
            f'actually get answered.</p></div>'
            f'<span class="course-cta">Explore our courses</span></a>')


def build_simple(name, url, kind="page", schema=None):
    """About, Contact, Privacy — a hero plus a body of prose."""
    sec = read_sections(CONTENT / "pages" / f"{name}.txt")
    meta = kv(sec.get("meta", []))
    body = []
    if sec.get("intro"):
        body.append(f'<div class="topic-intro">{prose(sec["intro"])}</div>')

    # the portrait card, laid out like the Instagram post: photo, then a
    # headline with the first words highlighted, then the standfirst.
    card = kv(sec.get("card", []))
    if card.get("photo"):
        stat = f'<p class="pcard-stat">{inline(card["stat"])}</p>' if card.get("stat") else ""
        body.append(f'''<section class="portrait-card">
  <img src="{card["photo"]}" alt="{html.escape(card.get("alt", ""), quote=True)}" width="1200" height="900" loading="eager">
  <div class="pcard-text">
    <span class="pcard-eyebrow">{html.escape(card.get("eyebrow", ""))}</span>
    <h2 class="pcard-headline">{inline(card.get("headline", ""))}</h2>
    <p class="pcard-lede">{inline(card.get("lede", ""))}</p>
    {stat}
    <span class="pcard-handle">{html.escape(S.get("handle", ""))}</span>
  </div>
</section>''')

    if name == "contact":
        body.append(contact_cards())
        if sec.get("note"):
            body.append(f'<p class="form-note">{prose(sec["note"])}</p>')

    if sec.get("body"):
        inner = prose(sec["body"])
        aside = rows(sec.get("aside", []), 2)
        if aside:
            body.append(f'<div class="about-section"><div class="about-prose">{inner}</div>'
                        + aside_panel("At a glance", aside) + "</div>")
        else:
            body.append(f'<div class="about-prose">{inner}</div>')

    write_page(url, f"{meta.get('title', name.title())} | {S.get('site_name')}",
               meta.get("description", ""), "\n".join(body),
               hero(eyebrow=meta.get("eyebrow", ""), headline=meta.get("headline", ""),
                    kind=kind),
               schema or [org_schema(), breadcrumb_schema(
                   [("Home", "/"), (meta.get("title", name.title()), url)])])


def contact_cards():
    wa = S.get("whatsapp", "")
    cards = [f'<a class="contact-card" href="mailto:{S.get("email")}">'
             f'<span class="contact-icon">Email</span>'
             f'<div class="contact-title">Send an email</div>'
             f'<div class="contact-detail">{html.escape(S.get("email", ""))}</div></a>']
    if wa:
        cards.append(f'<a class="contact-card" href="https://wa.me/{wa}" target="_blank" rel="noopener">'
                     f'<span class="contact-icon contact-icon-wa">{WA_ICON}WhatsApp</span>'
                     f'<div class="contact-title">Message on WhatsApp</div>'
                     f'<div class="contact-detail">+{html.escape(wa)}</div></a>')
    if S.get("instagram"):
        cards.append(f'<a class="contact-card" href="{S["instagram"]}" target="_blank" rel="noopener">'
                     f'<span class="contact-icon">Instagram</span>'
                     f'<div class="contact-title">{html.escape(S.get("handle", ""))}</div>'
                     f'<div class="contact-detail">Where everything gets posted first</div></a>')
    return (block_label("Fastest ways to reach me")
            + f'<div class="contact-grid">{"".join(cards)}</div>')


def build_resources():
    """One filterable table of every downloadable file on the site."""
    if not ALL_RESOURCES:
        body = (coming_soon_panel("The resource library")
                + '<div class="topic-intro"><p>Notes, worksheets and worked solutions '
                  'will all be listed here as they go up. Nothing to download just yet.</p></div>')
        write_page("/resources/", f"All resources | {S.get('site_name')}",
                   "Revision notes, worksheets and worked solutions for CIE Further "
                   "Mathematics and Additional Mathematics.", body,
                   hero(eyebrow="Everything in one place", headline="Resources", kind="page"))
        return
    else:
        rowshtml = []
        for r in sorted(ALL_RESOURCES, key=lambda x: (x["subject"], x["topic"], x["kind"])):
            rowshtml.append(
                f'<tr data-kind="{html.escape(r["kind"], quote=True)}" '
                f'data-subject="{html.escape(r["subject"], quote=True)}">'
                f'<td><a class="resource-link" href="{r["page"]}">{html.escape(r["topic"])}</a></td>'
                f'<td data-label="Subject">{html.escape(r["subject"])}</td>'
                f'<td data-label="Type"><span class="tag">{html.escape(r["kind"])}</span></td>'
                f'<td data-label="File"><a class="resource-link" href="{r["url"]}" '
                f'target="_blank" rel="noopener">View PDF</a></td></tr>')
        table = ('<div class="table-wrap"><table class="papers" id="restable"><thead><tr>'
                 '<th>Topic</th><th>Subject</th><th>Type</th><th>File</th>'
                 f'</tr></thead><tbody>{"".join(rowshtml)}</tbody></table></div>')

    kinds = sorted({r["kind"] for r in ALL_RESOURCES})
    subs = sorted({r["subject"] for r in ALL_RESOURCES})
    filters = ('<div class="filters">'
               '<input type="search" id="resfilter" placeholder="Search topics and files…" '
               'aria-label="Search resources">'
               + "".join(f'<button class="chip" data-f="{html.escape(k, quote=True)}">'
                         f'{html.escape(k)}</button>' for k in kinds + subs)
               + '<button class="chip is-on" data-f="">All</button></div>')

    script = """<script>
(function(){
  var t=document.getElementById('restable'); if(!t) return;
  var q=document.getElementById('resfilter'), chips=[].slice.call(document.querySelectorAll('.chip')), f='';
  function apply(){
    var s=(q.value||'').toLowerCase();
    [].forEach.call(t.tBodies[0].rows,function(r){
      var txt=r.textContent.toLowerCase();
      var tags=(r.dataset.kind||'')+' '+(r.dataset.subject||'');
      r.style.display=(!s||txt.indexOf(s)>-1)&&(!f||tags.indexOf(f)>-1)?'':'none';
    });
  }
  q.addEventListener('input',apply);
  chips.forEach(function(c){c.addEventListener('click',function(){
    chips.forEach(function(x){x.classList.remove('is-on');});
    c.classList.add('is-on'); f=c.dataset.f; apply();
  });});
})();
</script>"""

    body = ('<div class="topic-intro">'
            '<p>Every note, worksheet, answer sheet and set of worked solutions on the '
            'site, in one place. Search by topic or filter by type.</p>'
            '<p><strong>These documents are kept under version control.</strong> They are '
            'living documents, not finished ones — a better question gets added, a '
            'reported mistake gets corrected, a clearer explanation replaces an older '
            'one, and the file is re-uploaded. What you open here is always the current '
            'version.</p></div>'
            + filters + table + script + mistake_banner())
    write_page("/resources/", f"All resources | {S.get('site_name')}",
               "Every set of revision notes, worksheet and worked solution on Vector Space, "
               "in one searchable list.", body,
               hero(eyebrow="Everything in one place", headline="Resources",
                    meta=[f"{len(ALL_RESOURCES)} files"], kind="page"))


def build_404():
    links = "".join(f'<li><a class="resource-link" href="/{s["slug"]}/">'
                    f'{html.escape(s["name"])}</a></li>' for s in LIVE)
    body = (coming_soon_panel("Whatever you were looking for")
            + '<div class="topic-intro"><p>Either this page hasn\'t been written yet, '
              'or the link has a typo in it. Nothing is broken on your end.</p></div>'
            + f'<h2 class="section-title">Try these instead</h2><ul class="notes-list">{links}'
              '<li><a class="resource-link" href="/resources/">All resources</a></li>'
              '<li><a class="resource-link" href="/">Home</a></li></ul>')
    page = BASE
    for k, v in {"{{ TITLE }}": "Page not found", "{{ OG_TITLE }}": "Page not found",
                 "{{ DESCRIPTION }}": "Page not found", "{{ CANONICAL }}": DOMAIN + "/404.html",
                 "{{ SITE_NAME }}": S.get("site_name", ""),
                 "{{ OG_IMAGE }}": DOMAIN + S.get("og_image", ""),
                 "{{ HANDLE }}": S.get("handle", ""), "{{ EMAIL }}": S.get("email", ""),
                 "{{ CSS_VERSION }}": CSS_VERSION,
                 "{{ NAV }}": nav_html(""), "{{ FOOTER_LINKS }}": footer_links(),
                 "{{ HERO }}": hero(eyebrow="404", headline="Page not found", kind="page"),
                 "{{ CONTENT }}": body,
                 "{{ SCHEMA }}": json.dumps([org_schema()])}.items():
        page = page.replace(k, v)
    (OUT / "404.html").write_text(page, encoding="utf-8")


def build_sitemap():
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{DOMAIN}{u}</loc><lastmod>{today}</lastmod></url>"
                   for u in sorted(set(ALL_PAGES)))
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    host = DOMAIN.replace("https://", "").replace("http://", "")
    (OUT / "CNAME").write_text(host + "\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


# ===========================================================================
#  7. THE MAIN RUN
# ===========================================================================

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # copy everything in static/ straight across (PDFs, CSS, images)
    for item in STATIC.iterdir():
        dest = OUT / item.name
        shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(item, dest)

    topic_count = 0
    for subject in LIVE:
        sdir = CONTENT / subject["slug"]
        by_paper, loose = {}, []
        if sdir.exists():
            for f in sorted(sdir.rglob("*.txt")):
                # a file named past-papers.txt is the past papers page,
                # not a topic. It's handled separately below.
                if f.name == "past-papers.txt":
                    continue
                rel = f.relative_to(sdir).parts
                paper = None
                if len(rel) > 1:
                    pslug = rel[0]
                    paper = next((p for p in PAPERS.get(subject["slug"], [])
                                  if p["slug"] == pslug), None)
                    if paper is None:
                        print(f"  ! skipped {f.name}: no paper '{pslug}' in site.txt")
                        continue
                t = build_topic(f, subject, paper)
                topic_count += 1
                (by_paper.setdefault(paper["slug"], []) if paper else loose).append(t)

        for p in PAPERS.get(subject["slug"], []):
            build_paper(subject, p, by_paper.get(p["slug"], []))
        if has_past_papers(subject["slug"]):
            build_past_papers(subject)
        build_subject(subject, by_paper, loose)

    build_courses()      # must run before build_home — the home strip needs COURSES
    build_home()
    build_simple("about", "/about/", schema=[org_schema(), person_schema()])
    build_simple("contact", "/contact/")
    build_simple("privacy", "/privacy/")
    build_resources()
    build_404()
    build_sitemap()

    print(f"\n  Built {len(ALL_PAGES)} pages · {topic_count} topics · "
          f"{len(ALL_RESOURCES)} downloadable files")
    if MISSING:
        uniq = sorted(set(MISSING))
        print(f"\n  {len(uniq)} file(s) named in your content but not yet in static/.")
        print("  These show as 'Coming soon' on the site — nothing is broken.")
        for f in uniq[:8]:
            print(f"     · {f}")
        if len(uniq) > 8:
            print(f"     · …and {len(uniq) - 8} more")
    print(f"  Output is in:  {OUT}")
    print("  Preview it with:  python3 -m http.server -d docs 8000")
    print("  then open http://localhost:8000 in your browser.\n")


if __name__ == "__main__":
    main()
