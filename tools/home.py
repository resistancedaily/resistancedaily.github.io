#!/usr/bin/env python3
"""Resistance Daily home page = today's edition (the "Threads" redesign, Nov 2026; spec: design handoff 5a/5b).

Usage (from the repo root):
  python3 tools/home.py [OUT]       builds the latest edition as OUT (default index.html; another name = noindex preview)
Imported by publish.py, which builds the same page three ways with build():
  index.html (prefix ""), today/index.html and archive/DATE.html (prefix "../", canonical archive/DATE.html).

Top of the page = today: hero with "Play today", thread cards (threads that moved; followed quiet threads appear via
assets/rd.js), "Also today" (one-off stories), Rights upheld + Today on the map. Below "When you have more time":
All threads, Past editions, Act today, How we report, and "All stories this day" (every item in full with its photo,
sources and anchor #iN: the complete sourced record). Tags are calm words (Lives lost, Right upheld, Assembly...),
never red. Thread logic lives in tools/threads.py.
"""
import sys, os, json, math, html, datetime
import seo
import rdsite as S
import threads as T

E = html.escape
root = S.root


def esc_json(o):
    return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")


def item_rank(i, date):
    return (not T.upheld(i, date), S.SEV[i["sev"]], i["n"])


def build(date, out, prefix, canonical, kind="home", og_image=None, noindex=False, inline=False):
    """kind: "home" (index.html), "today" or "archive". inline=True embeds CSS/JS (backup artifact)."""
    d = S.load(f"data/{date}.json")
    dt = datetime.date.fromisoformat(date)
    ups = T.all_updates(date)
    reg = T.registry()
    regs = {t["slug"]: t for t in reg}
    items = d["items"]
    by_thread = {}
    oneoffs = []
    for i in items:
        s = T.thread_of(i)
        if s in regs:
            by_thread.setdefault(s, []).append(i)
        else:
            oneoffs.append(i)
    # Order: upheld first, then most serious, then registry order.
    moved = sorted(by_thread, key=lambda s: (min(item_rank(i, date) for i in by_thread[s]), [t["slug"] for t in reg].index(s)))
    quiet = [t["slug"] for t in reg if t["slug"] not in by_thread]
    words = sum(len(i.get("text", "").split()) for s in moved for i in by_thread[s])
    mins = max(1, math.ceil(words / 200))

    def card(s, is_moved):
        t = regs[s]
        u = ups.get(s, [])
        p = T.photo_of(t, u)
        ring = (f'<img class="washed" src="{E(S.rel(p["src"], prefix))}" alt="" loading="lazy" decoding="async">' if p and is_moved else "<i></i>")
        if is_moved:
            top = sorted(by_thread[s], key=lambda i: item_rank(i, date))[0]
            tg, cls = T.tag(top, date)
            n = len(by_thread[s])
            up = T.upheld(top, date)
            return (f'<a class="rd-thread{" is-upheld" if up else ""}" data-thread="{E(s)}" href="{T.link(t, prefix)}">'
                    f'<span class="rd-ring">{ring}</span><span class="rd-tx"><span class="rd-tx-top"><h3>{E(t["name"])}</h3>'
                    f'<span class="{cls}">{E(tg)}</span><span class="rd-state rd-state-m">{n} new</span></span>'
                    f'<p>{E(top["headline"])}</p><span class="rd-state">{n} new</span></span></a>')
        return (f'<a class="rd-thread is-quiet" data-thread="{E(s)}" href="{T.link(t, prefix)}" hidden>'
                f'<span class="rd-ring"><i></i></span><span class="rd-tx"><span class="rd-tx-top"><h3>{E(t["name"])}</h3>'
                f'<span class="tag tag-neutral">Quiet</span><span class="rd-state rd-state-m">Quiet</span></span>'
                f'<p>No new report today</p><span class="rd-state">Quiet</span></span></a>')

    # Only threads that moved today (the ones Play today plays) get a card (owner's request, 5 Nov 2026).
    grid = "".join(card(s, True) for s in moved)

    # Full stories live on their own page, stories/DATE.html (owner's request, 5 Nov 2026: tap a story, read it, press
    # Back and land where you were). The inlined backup artifact is one file, so it keeps them on the page (#iN).
    sref = "" if inline else f"{prefix}stories/{date}.html"
    # Also today: one-off stories (rows open the full story).
    also_rows = "".join(f'<li><b>{E(i.get("short", i["place"]))}</b><a href="{sref}#i{i["n"]}">{E(i["headline"])}</a></li>'
                        for i in sorted(oneoffs, key=lambda i: item_rank(i, date)))
    also = (f'<details class="rd-also"><summary><b>Also today</b><span class="rd-sub"><span class="rd-sub-d"> · {len(oneoffs)} '
            f'stor{"y" if len(oneoffs) == 1 else "ies"} outside a thread</span><span class="rd-k-m"> · {len(oneoffs)}</span></span>'
            f'<span class="rd-show"><span class="rd-show-t">Show</span><span class="rd-hide">Hide</span></span></summary>'
            f'<ul>{also_rows}</ul></details>') if oneoffs else ""

    # Rights upheld (data/hope.json via hope.py) + today's upheld item.
    upheld_html = ""
    if os.path.exists(os.path.join(root, "data", "hope.json")):
        import hope as H
        n, period = H.counts(H.load(), dt)
        todays = sorted((i for i in items if T.upheld(i, date)), key=lambda i: i["n"])
        line = (f"Today: {todays[0]['headline']}." if todays else
                f"Latest: {H.recent(H.load(), 1)[0]['headline']}." if H.load()["items"] else "")
        upheld_html = (f'<a class="rd-upheld" href="{prefix}hope/" style="text-decoration:none"><span class="rd-n">{n}</span><span>'
                       f'<h2>Rights upheld {E(period)}</h2><p>{E(line)}</p><span style="font-weight:600;text-decoration:underline">See all {n} →</span></span></a>')

    # Today on the map: the edition's SVG maps in a dialog.
    mp = os.path.join(root, "data", f"{date}.maps.json")
    maps = json.load(open(mp)) if os.path.exists(mp) else {}
    n_in = sum(1 for i in items if i["region"] == "india")
    n_w = len(items) - n_in
    map_html = ""
    if maps.get("india") or maps.get("world"):
        place_line = f"{len(items)} places · {n_in} in India, {n_w} worldwide"
        fix = lambda svg: svg.replace('href="#i', f'href="{sref}#i')
        # Owner's request (5 Nov 2026): the map is always open on the page, not behind a button.
        map_html = (f'<section class="rd-sec rd-mapsec" aria-label="Today on the map"><div class="rd-hd"><h2 class="rd-h">Today on the map</h2></div>'
                    f'<p class="rd-sub" style="margin:0">{place_line}. Tap a number to read that story.</p>'
                    f'<p class="rd-legend"><span><i class="lg lg-red"></i>Lives lost</span><span><i class="lg"></i>Other stories</span></p>'
                    f'<div class="rd-mapd rd-mapin"><div class="rd-mapd-g"><div>{fix(maps.get("india", ""))}</div><div class="rd-mapw">{fix(zoom_world(maps.get("world", "")))}</div></div></div></section>')
    two = map_html + upheld_html

    # All threads (key fact each) and past editions.
    tlink = lambda t: (f'{prefix}{t["page"]}' if t.get("page") else
                       f'{prefix}focus/{t["focus"]}.html' if t.get("focus") and os.path.exists(os.path.join(root, "focus", f'{t["focus"]}.html'))
                       else T.link(t, prefix))
    pills = "".join(f'<a href="{tlink(t)}">{E(t["name"])}</a>' for t in reg)
    tcards = [f'<a class="rd-tcard" href="{tlink(t)}"><b>{E(t["name"])}</b><span>{E(T.stat(t) or "Every update, newest first")}</span></a>' for t in reg]
    allth = (f'<div class="rd-all">{"".join(tcards[:6])}</div>'
             + (f'<details class="rd-allmore"><summary class="rd-sub" style="font-family:var(--font-heading);color:var(--color-accent-700)">'
                f'<span class="a">All {len(reg)} threads ↓</span><span class="b">Fewer ↑</span></summary><div class="rd-all">{"".join(tcards[6:])}</div></details>' if len(tcards) > 6 else "")
             + f'<div class="rd-pills">{pills}</div>')
    eds = [e for e in S.editions() if e < date][-4:][::-1]
    past = "".join(f'<li><a href="{prefix}archive/{e}.html"><b>{E(S.nice(e))}</b><span>{E(S.top_line(e))}</span></a></li>' for e in eds)
    acts = "".join(f'<div class="rd-act"><b>{E(a)}</b><span>{E(b)}</span></div>' for a, b in d.get("acts", []))

    # All stories this day: the full sourced record (anchors #iN).
    def story(i):
        p = i.get("photo")
        tg, cls = T.tag(i, date)
        s = T.thread_of(i)
        th = (f' · <a href="{T.link(regs[s], prefix)}">{E(regs[s]["name"])} thread →</a>' if s in regs else "")
        fig = (f'<figure><img class="washed" src="{E(S.rel(p["src"], prefix))}" alt="{E(p["alt"])}" loading="lazy" decoding="async">'
               f'<figcaption><b>{E(S.photo_label(p))}</b> · {E(p.get("caption", ""))} {S.photo_credit(p)}</figcaption></figure>') if p else ""
        foc = (f' · <a href="{prefix}focus/{E(i["focus"])}.html">Photos and full story →</a>'
               if i.get("focus") and os.path.exists(os.path.join(root, "focus", f'{i["focus"]}.html')) else "")
        return (f'<article class="rd-story{"" if p else " nophoto"}" id="i{i["n"]}">{fig}<div><div class="rd-meta"><span class="{cls}">{E(tg)}</span>'
                f'<span>{E(i["place"])}</span></div><h3>{E(i["headline"])}</h3><p>{E(i.get("text", ""))}</p>'
                f'<span class="rd-src">{S.src_links(i.get("src", []))}{foc}{th}</span></div></article>')
    stories = "".join(story(i) for i in sorted(items, key=lambda i: i["n"]))
    SL = ("All stories today" if kind in ("home", "today") else "All stories this day")
    if inline:
        stories_block = (f'<details class="rd-stories" id="stories"><summary><b>{SL}</b><span class="rd-sub"> · {len(items)}, each with its sources</span>'
                         f'</summary>{stories}<button type="button" class="btn btn-secondary rd-collapse" data-rd-collapse>Hide all stories &minus;</button></details>')
    else:
        stories_block = (f'<a class="rd-storylink" href="{sref}"><b>{SL}</b><span class="rd-sub"> · {len(items)}, each with its photo and sources</span>'
                         f'<span class="rd-go" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg></span></a>')
        build_stories(date, d, stories, kind, regs)

    pdata = {"date": date, "order": moved + quiet, "threads": T.player_data(date, prefix, ups)}
    kicker_d = f'{S.nice(date)} · covers {d.get("window", "")}'
    kicker_m = f'{S.nice(date)} · {len(moved)} thread{"s" if len(moved) != 1 else ""} moved'
    page_title = ("Resistance Daily · Human rights, every fact sourced" if kind == "home" else f'Resistance Daily · {d["date_long"]}')
    top3 = sorted(items, key=lambda i: item_rank(i, date))[:3]
    desc = S.DESC if kind == "home" else "; ".join(f'{i.get("short", i["place"])}: {i["headline"]}' for i in top3)
    if kind == "home":
        ld = [{"@context": "https://schema.org", "@type": "NewsMediaOrganization", "name": "Resistance Daily", "url": S.SITE,
               "email": "resistancedaily.in@gmail.com", "sameAs": seo.SAME_AS, "description": S.DESC},
              {"@context": "https://schema.org", "@type": "WebSite", "name": "Resistance Daily", "url": S.SITE, "inLanguage": "en"}]
    else:
        ld = [{"@context": "https://schema.org", "@type": "NewsArticle", "headline": page_title, "description": desc, "url": canonical,
               "mainEntityOfPage": canonical, "datePublished": seo.iso(date), "dateModified": seo.iso(date),
               "author": seo.PUBLISHER, "publisher": seo.PUBLISHER, "isAccessibleForFree": True, "inLanguage": "en"}]
        if og_image:
            ld[0]["image"] = [S.SITE + og_image]
    og = (f'<meta property="og:image" content="{S.SITE}{og_image}"><meta property="og:image:width" content="1200">'
          f'<meta property="og:image:height" content="630">' if og_image else "")
    extra = (og + f'<meta property="og:type" content="{"website" if kind == "home" else "article"}"><meta property="og:url" content="{canonical}">'
             + (f'<meta property="article:published_time" content="{seo.iso(date)}">' if kind != "home" else "")
             + '<meta name="twitter:card" content="summary_large_image">' + "".join(seo.jsonld(x) for x in ld))

    body = f"""{S.nav(prefix)}
<header class="rd-hero"><div><span class="rd-kicker"><span class="rd-k-d">{E(kicker_d)}</span><span class="rd-k-m">{E(kicker_m)}</span></span>
<h1>Where things stand today</h1><p>Human rights in India and the world. Non-partisan. Every fact sourced.</p></div>
{f'<button class="btn btn-primary rd-play" data-rd-play-all>▶&nbsp; Play today · {mins} min</button>' if moved else ''}</header>
<div class="rd-caught" data-rd-caught-up hidden><b>You're caught up.</b> {upheld_count_line(dt)}</div>
<div class="rd-grid" data-rd-thread-grid>{grid}</div>
{also}
{two}
<div class="rd-divider">When you have more time</div>
<div class="rd-more2"><section class="rd-sec"><div class="rd-hd"><h2 class="rd-h">All threads</h2><a href="{prefix}focus/">All {len(reg)} →</a></div>
<p class="rd-sub" style="margin:0">Long-running stories, including the In focus pieces, Accountability Watch and Still waiting.</p>{allth}</section>
<section class="rd-sec"><div class="rd-hd"><h2 class="rd-h">Past editions</h2><a href="{prefix}archive/">All →</a></div><ul class="rd-past">{past}</ul></section></div>
<section class="rd-sec"><h2 class="rd-h">Act today <span class="rd-sub">· whatever your politics</span></h2><div class="rd-acts">{acts}</div></section>
{stories_block}
<details class="rd-how" id="how"><summary>How we report</summary><ul>{S.HOW}</ul></details>
<script type="application/json" id="rd-threads">{esc_json(pdata)}</script>"""
    html_ = S.head(page_title, desc, prefix, canonical, extra, noindex) + body + S.footer(prefix)
    if inline:
        css = open(os.path.join(root, "assets", "organic.css")).read() + open(os.path.join(root, "assets", "rd.css")).read()
        js = open(os.path.join(root, "assets", "rd.js")).read()
        html_ = (html_.replace(f'<link rel="stylesheet" href="{prefix}assets/organic.css?v={S.ver("organic.css")}"><link rel="stylesheet" href="{prefix}assets/rd.css?v={S.ver("rd.css")}">',
                               f"<style>{css}</style>")
                 .replace(f'<script src="{prefix}assets/rd.js?v={S.ver("rd.js")}" defer></script>', f"<script>{js}</script>"))
    os.makedirs(os.path.dirname(os.path.join(root, out)) or root, exist_ok=True)
    open(os.path.join(root, out), "w").write(html_)
    return html_


def zoom_world(svg):
    """Crop the world map's viewBox to the area around today's pins, so pins and labels stay readable on a phone."""
    import re
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    pts = [(float(x), float(y)) for x, y in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', svg)]
    if not m or not pts:
        return svg
    W, H = float(m.group(1)), float(m.group(2))
    x0, x1 = min(p[0] for p in pts) - 110, max(p[0] for p in pts) + 150   # room for labels on the right
    y0, y1 = min(p[1] for p in pts) - 70, max(p[1] for p in pts) + 70
    w = max(x1 - x0, 360); h = max(y1 - y0, w / 2.0)
    w = max(w, h * 1.6)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # The ocean is the element's background, so the box may run past the drawn land (e.g. south of the map's edge).
    w, h = min(w, W), min(h, H)
    x0 = min(max(cx - w / 2, 0), max(W - w, 0)); y0 = max(min(cy - h / 2, H + 40 - h), 0)
    return svg.replace(m.group(0), f'viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}"', 1)


def build_stories(date, d, _unused, kind, regs):
    """stories/DATE.html: every item of the edition in full (photo, text, sources, #iN anchors)."""
    prefix = "../"
    items = d["items"]
    def story(i):
        p = i.get("photo")
        tg, cls = T.tag(i, date)
        s = T.thread_of(i)
        th = (f' · <a href="{T.link(regs[s], prefix)}">{E(regs[s]["name"])} thread →</a>' if s in regs else "")
        fig = (f'<figure><img class="washed" src="{E(S.rel(p["src"], prefix))}" alt="{E(p["alt"])}" loading="lazy" decoding="async">'
               f'<figcaption><b>{E(S.photo_label(p))}</b> · {E(p.get("caption", ""))} {S.photo_credit(p)}</figcaption></figure>') if p else ""
        foc = (f' · <a href="{prefix}focus/{E(i["focus"])}.html">Photos and full story →</a>'
               if i.get("focus") and os.path.exists(os.path.join(root, "focus", f'{i["focus"]}.html')) else "")
        return (f'<article class="rd-story{"" if p else " nophoto"}" id="i{i["n"]}">{fig}<div><div class="rd-meta"><span class="{cls}">{E(tg)}</span>'
                f'<span>{E(i["place"])}</span></div><h3>{E(i["headline"])}</h3><p>{E(i.get("text", ""))}</p>'
                f'<span class="rd-src">{S.src_links(i.get("src", []))}{foc}{th}</span></div></article>')
    body_s = "".join(story(i) for i in sorted(items, key=lambda i: i["n"]))
    ed = f"{prefix}archive/{date}.html"
    url = f"{S.SITE}stories/{date}.html"
    title = f'All stories · {d["date_long"]} · Resistance Daily'
    desc = "; ".join(f'{i.get("short", i["place"])}: {i["headline"]}' for i in sorted(items, key=lambda i: item_rank(i, date))[:3])
    back = (f'<a class="rd-back" href="{ed}" data-rd-back>← Back to the edition</a>')
    page = (S.head(title, desc, prefix, url, '<meta property="og:type" content="article">') + S.nav(prefix)
            + f'<header class="rd-stories-h">{back}<span class="rd-kicker">{E(S.nice(date))} · covers {E(d.get("window", ""))}</span>'
            + f'<h1>All stories · {E(S.nice(date))}</h1><p class="rd-sub" style="margin:0">{len(items)} stories, each with its photo, the official position and its sources.</p></header>'
            + f'<section class="rd-stories rd-stories-page">{body_s}</section><p>{back}</p>'
            + """<script>document.querySelectorAll('[data-rd-back]').forEach(function(a){a.addEventListener('click',function(e){
try{if(document.referrer&&new URL(document.referrer).origin===location.origin&&history.length>1){e.preventDefault();history.back();}}catch(x){}});});</script>"""
            + S.footer(prefix))
    os.makedirs(os.path.join(root, "stories"), exist_ok=True)
    open(os.path.join(root, "stories", f"{date}.html"), "w").write(page)


def upheld_count_line(dt):
    try:
        import hope as H
        n, period = H.counts(H.load(), dt)
        return f"{n} right{'s were' if n != 1 else ' was'} upheld {period}."
    except Exception:
        return ""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    date = S.editions()[-1]
    share = f"images/{date}/share.jpg" if os.path.exists(os.path.join(root, "images", date, "share.jpg")) else None
    build(date, out, "", S.SITE, "home", share, noindex=os.path.basename(out) != "index.html")
    print("built home", out, date)
