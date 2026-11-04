#!/usr/bin/env python3
"""Threads: long-running stories, the backbone of the "Threads" redesign (Nov 2026).

Usage (from the repo root):  python3 tools/threads.py        builds threads/SLUG.html for every registry thread
Imported by home.py (thread cards, player data) and focus.py.

Registry: data/threads.json {"threads": [{slug, name, focus?, page?, stat?, stat_from?}]}. Timelines are derived,
not stored: every data/YYYY-MM-DD.json item is assigned with thread_of(item), newest first.

Per item (data/YYYY-MM-DD.json):
  "thread": "<slug>"   explicit thread (set by the routine when an item continues a registered thread)
  "upheld": true       a right was upheld (court relief, release, accountability step); shown with the sage tag.
                       Also upheld: a data/hope.json item whose "edition" is "YYYY-MM-DD#N" for this item.
"""
import os, json, html, datetime
import seo
import rdsite as S

E = html.escape
root = S.root


def registry():
    return S.load("data/threads.json")["threads"]


def thread_of(item):
    """The one place that decides an item's thread. None = a one-off story ("Also today")."""
    if item.get("thread"):
        return item["thread"]
    if item.get("focus"):
        return item["focus"]
    if "Accountability Watch" in item.get("rights", []):
        return "accountability"
    return None


_hope_eds = None


def upheld(item, date):
    global _hope_eds
    if item.get("upheld"):
        return True
    if _hope_eds is None:
        try:
            _hope_eds = {h["edition"] for h in S.load("data/hope.json")["items"] if h.get("edition")}
        except Exception:
            _hope_eds = set()
    return f"{date}#{item['n']}" in _hope_eds


def tag(item, date):
    """Calm word tag (never red): (text, class)."""
    r = [x.lower() for x in item.get("rights", [])]
    if upheld(item, date):
        return "Right upheld", "tag tag-accent-2"
    if item.get("sev") == "red":
        return "Lives lost", "tag tag-accent"
    if any(x.startswith("assembly") for x in r):
        return "Assembly", "tag tag-neutral"
    if any(x.startswith(("expression", "press")) for x in r):
        return "Speech", "tag tag-neutral"
    if any(x.startswith(("due process", "detention")) for x in r):
        return "Detention", "tag tag-neutral"
    return (item["rights"][0] if item.get("rights") else "Today"), "tag tag-neutral"


def all_updates(upto=None):
    """{slug: [update, ...]} newest first, from every edition up to and including `upto`."""
    out = {}
    for date in S.editions():
        if upto and date > upto:
            continue
        d = S.load(f"data/{date}.json")
        for i in d["items"]:
            s = thread_of(i)
            if not s:
                continue
            out.setdefault(s, []).append({
                "date": date, "d": S.nice(date, "%d %b"), "n": i["n"], "t": i["headline"], "text": i.get("text", ""),
                "src": i.get("src", []), "sev": i["sev"], "upheld": upheld(i, date), "photo": i.get("photo"),
                "place": i.get("short", i["place"]), "tag": tag(i, date)})
    for s in out:
        out[s].sort(key=lambda u: (u["date"], -u["n"]), reverse=True)
    return out


def focus_data(slug):
    p = os.path.join(root, "data", "focus", f"{slug}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def stat(t):
    """One sourced line for a thread card: registry stat, computed stat, or the focus page's first key figure."""
    if t.get("stat_from") == "data/cases.json":
        c = S.load("data/cases.json")
        asof = datetime.date.fromisoformat(c["asof"])
        lo = min(c["cases"], key=lambda x: x["since"])
        return f'{len(c["cases"])} held · longest: {lo["name"]}, {(asof - datetime.date.fromisoformat(lo["since"])).days:,} days'
    if t.get("stat_from") == "data/accountability.json":
        a = S.load("data/accountability.json")
        op = [c for c in a["cases"] if not c.get("closed")]
        noarr = sum(1 for c in op if any(s["step"].lower().startswith("arrest") for s in c["steps"])
                    and not any(s["step"].lower().startswith("arrest") and s["status"] == "done" for s in c["steps"]))
        return f"{len(op)} cases followed · {noarr} with no arrest"
    if t.get("stat"):
        return t["stat"]
    f = focus_data(t.get("focus")) if t.get("focus") else None
    if f and f.get("figs"):
        x = f["figs"][0]
        return f'{x["fig"]} {x["figcap"]}'
    return ""


def link(t, prefix):
    """Where a thread's own page lives."""
    return f"{prefix}threads/{t['slug']}.html"


def photo_of(t, ups):
    """Latest update's photo, else the focus cover."""
    for u in ups:
        if u.get("photo"):
            return u["photo"]
    f = focus_data(t.get("focus")) if t.get("focus") else None
    return f["photos"][0] if f and f.get("photos") else None


def player_data(date, prefix, ups=None):
    """JSON for assets/rd.js: every registry thread with its last 6 updates (today's flagged isNew)."""
    ups = ups if ups is not None else all_updates(date)
    th = {}
    for t in registry():
        u = ups.get(t["slug"], [])[:6]
        p = photo_of(t, u)
        f = focus_data(t.get("focus")) if t.get("focus") else None
        th[t["slug"]] = {
            "name": t["name"], "stat": stat(t), "page": link(t, prefix),
            "img": S.rel(p["src"], prefix) if p else "", "photoTag": S.photo_label(p) if p else "",
            "credit": f'{p["credit"]}, {p["licence"]}' if p else "", "creditUrl": p.get("page", "") if p else "",
            "focusUrl": f'{prefix}focus/{t["focus"]}.html' if f else (f'{prefix}{t["page"]}' if t.get("page") else ""),
            "focusLabel": (f.get("short") or f["title"]) if f else (t["name"] if t.get("page") else ""),
            "updates": [{"d": x["d"], "t": x["t"], "text": x["text"] if x["date"] == date else "",
                         "src": x["src"] if x["date"] == date else [], "isNew": x["date"] == date,
                         "upheld": x["upheld"]} for x in u]}
    return th


# ── standalone thread pages ─────────────────────────────────────────────────

def timeline_html(ups, latest, prefix, limit=None):
    """Newest first, grouped by month; the dot is accent for the latest edition."""
    out, month = [], None
    for u in ups[:limit] if limit else ups:
        m = datetime.date.fromisoformat(u["date"]).strftime("%B %Y")
        if m != month:
            out.append(f'<li class="rd-tl-m">{E(m)}</li>')
            month = m
        tg, cls = u["tag"]
        para = f'<p>{E(u["text"])}</p>' if u["text"] else ""
        out.append(f'<li class="rd-tl-e{" is-new" if u["date"] == latest else ""}"><i></i><time datetime="{u["date"]}">{E(u["d"])}</time>'
                   f'<div><h3>{E(u["t"])}</h3><span class="{cls}">{E(tg)}</span>'
                   f'{para}'
                   f'<span class="rd-src">{S.src_links(u["src"])} · <a href="{prefix}archive/{u["date"]}.html#i{u["n"]}">Edition of {E(S.nice(u["date"]))}</a></span></div></li>')
    return f'<ol class="rd-tl">{"".join(out)}</ol>'


def page(t, ups, latest):
    prefix = "../"
    p = photo_of(t, ups)
    f = focus_data(t.get("focus")) if t.get("focus") else None
    url = f"{S.SITE}threads/{t['slug']}.html"
    st = stat(t)
    desc = f'{t["name"]}: every update, newest first, with sources. ' + (st if st else "")
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": t["name"], "description": desc, "url": url,
          "mainEntityOfPage": url, "datePublished": seo.iso(ups[-1]["date"]) if ups else seo.iso(latest),
          "dateModified": seo.iso(ups[0]["date"]) if ups else seo.iso(latest),
          "author": seo.PUBLISHER, "publisher": seo.PUBLISHER, "isAccessibleForFree": True, "inLanguage": "en"}
    og = (f'<meta property="og:image" content="{S.SITE}{p["src"]}">' if p and not p["src"].startswith("http") else "")
    extra = og + f'<meta property="og:type" content="article"><meta property="og:url" content="{url}">' + seo.jsonld(ld)
    more = ""
    if f:
        more = f'<a class="rd-more" href="../focus/{t["focus"]}.html">In focus: {E(f.get("short") or f["title"])} →</a>'
    elif t.get("page"):
        more = f'<a class="rd-more" href="../{t["page"]}">Open {E(t["name"])} →</a>'
    photo = (f'<figure class="rd-arch"><img class="washed" src="{E(S.rel(p["src"], prefix))}" alt="{E(p.get("alt", ""))}">'
             f'<span class="rd-ptag">{E(S.photo_label(p))}</span><details class="rd-info"><summary aria-label="About this photo">i</summary>'
             f'<figcaption>{S.photo_credit(p)}</figcaption></details></figure>') if p else ""
    body = (f'<header class="rd-th-hero"><div><span class="rd-kicker">Thread</span><h1>{E(t["name"])}</h1>'
            f'{f"<p class=rd-stat>{E(st)}</p>" if st else ""}'
            f'<div class="rd-row"><button class="btn btn-primary" data-rd-follow="{E(t["slug"])}">Follow this thread</button>{more}</div></div>{photo}</header>'
            f'<section class="rd-sec"><h2>Every update</h2>'
            f'{timeline_html(ups, latest, prefix) if ups else "<p>No reports yet.</p>"}</section>')
    html_ = S.head(f'{t["name"]} · Resistance Daily', desc, prefix, url, extra) + S.nav(prefix) + body + S.footer(prefix)
    os.makedirs(os.path.join(root, "threads"), exist_ok=True)
    open(os.path.join(root, "threads", f'{t["slug"]}.html'), "w").write(html_)


def build_all():
    latest = S.editions()[-1]
    ups = all_updates()
    for t in registry():
        page(t, ups.get(t["slug"], []), latest)
    print("built threads", len(registry()))
    return ups


if __name__ == "__main__":
    build_all()
