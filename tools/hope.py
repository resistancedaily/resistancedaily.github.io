#!/usr/bin/env python3
"""Build the "Signs of hope" page: where rights were upheld (owner's request, 4 Nov 2026).

Usage (from the repo root):  python3 tools/hope.py [YYYY-MM-DD]   (date for "this week"; default: today, IST)
Reads data/hope.json, writes hope/index.html, rebuilds sitemap.xml/robots.txt and the home page.

data/hope.json:
{ "updated": "YYYY-MM-DD",
  "items": [{
     "id", "date": "YYYY-MM-DD" (the day it happened),
     "kind": "Courts" | "Accountability" | "Releases" | "People helping people" | "Communities that won",
     "rights": [...], "place", "fig", "figcap",       # one key figure, shown when there is no photo
     "headline" (<= 9 words), "text" (<= 35 words: what was upheld, plus what is still open, e.g. "he has not been arrested"),
     "slide_head" (<= 26 chars, bold on the Instagram slide, e.g. "Freed after 15 months"),
     "slide" (<= 60 chars: the line under it on the Instagram "Signs of hope" slide),
     "src": [[name, url], ...], "photo"?: {same fields as an edition item photo},
     "link"?: [label, site path]                       # e.g. ["Kashmir Focus", "focus/kashmir.html"] }] }

Rules (see ROUTINE.md, SIGNS OF HOPE): rights upheld, not sides won; the same sourcing and official-position rules as every
item; never overstate; say what is still unresolved. The page lists items newest first.
"""
import sys, os, json, html, datetime, subprocess
import seo

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = seo.SITE
KINDS = ["Courts", "Accountability", "Releases", "People helping people", "Communities that won"]


def load():
    return json.load(open(os.path.join(root, "data", "hope.json")))


def counts(data, today):
    """(number, period) for the home card and the slide: this week if anything happened in it, else this month."""
    items = data["items"]
    for days, label in ((7, "this week"), (31, "this month")):
        n = sum(1 for i in items if 0 <= (today - datetime.date.fromisoformat(i["date"])).days < days)
        if n:
            return n, label
    return len(items), "so far"


def recent(data, n=3):
    return sorted(data["items"], key=lambda i: i["date"], reverse=True)[:n]


def card(i):
    p = i.get("photo")
    top = (f'<img src="../{E(p["src"])}" alt="{E(p["alt"])}" loading="lazy" decoding="async">' if p else
           f'<div class="fp"><b>{E(i["fig"])}</b><span>{E(i["figcap"])}</span></div>')
    d = datetime.date.fromisoformat(i["date"]).strftime("%d %b")
    src = " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in i["src"])
    if i.get("link"):
        src += f' · <a class="more" href="../{E(i["link"][1])}">{E(i["link"][0])} →</a>'
    cr = (f'<span class="cr">{"File photo · " + E(p["year"]) if p.get("kind") != "event" else "Photo from the event"}: '
          f'<a href="{E(p["page"])}">{E(p["credit"])}</a>, <a href="{E(p["licence_url"])}">{E(p["licence"])}</a></span>') if p else ""
    return (f'<article class="c" id="{E(i["id"])}" data-k="{E(i["kind"])}">{top}<div class="t">'
            f'<span class="k">{E(i["kind"])} · {E(" · ".join(i["rights"]))} · {d}</span><h3>{E(i["headline"])}</h3>'
            f'<p>{E(i["text"])}</p><span class="where">{E(i["place"])}</span><span class="src">{src}</span>{cr}</div></article>')


def build(today):
    data = load()
    items = sorted(data["items"], key=lambda i: i["date"], reverse=True)
    n, period = counts(data, today)
    kinds = ["All"] + [k for k in KINDS if any(i["kind"] == k for i in items)]
    title = "Signs of hope: where human rights were upheld"
    desc = (f"{n} rights upheld {period}: court rulings, accountability, releases and people helping each other, in India and "
            "around the world. Non-partisan, every fact sourced.")
    url = SITE + "hope/"
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url,
          "dateModified": data["updated"], "publisher": {"@type": "NewsMediaOrganization", "name": "Resistance Daily", "url": SITE}}
    CSS = """
:root{--bg:#f3f4f2;--paper:#fff;--ink:#15181d;--muted:#5b616b;--rule:#d9dcd8;--green:#1d7a4c;--gl:#e4f2e9;--chip:#eceee9;
--display:"Barlow Condensed","Arial Narrow",Arial,sans-serif;--body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--green:#3fb07a;--gl:#18291f;--chip:#22262c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--green:#3fb07a;--gl:#18291f;--chip:#22262c;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--body)}
.wrap{max-width:900px;margin:0 auto;padding:20px max(16px,env(safe-area-inset-left,0px)) 48px;display:grid;gap:22px}
a{color:inherit;text-decoration-color:var(--green);text-underline-offset:2px}
a:focus-visible,button:focus-visible{outline:2px solid var(--green);outline-offset:2px}
p{margin:0}
.top-nav{display:flex;justify-content:space-between;gap:12px;font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;border-bottom:3px solid var(--ink);padding-bottom:10px}
.top-nav b{font-weight:500}
h1{font:800 clamp(44px,9vw,72px)/.92 var(--display);text-transform:uppercase;margin:0}
h1 span{color:var(--green)}
.lede{color:var(--muted);max-width:60ch;margin-top:8px;font-size:16px}
.hero{background:var(--paper);border:1px solid var(--rule);border-top:6px solid var(--green);border-radius:8px;padding:18px;display:grid;grid-template-columns:auto 1fr;gap:4px 18px;align-items:center}
.hero b{font:800 96px/.85 var(--display);color:var(--green);grid-row:span 2}
.hero .cap{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.hero p{font-size:16px}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.filters button{font:600 12px var(--mono);text-transform:uppercase;letter-spacing:.04em;padding:7px 11px;border-radius:999px;background:var(--paper);color:var(--ink);border:1px solid var(--rule);cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--green);color:#fff;border-color:var(--green)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:12px}
.c{background:var(--paper);border:1px solid var(--rule);border-radius:8px;overflow:hidden;display:grid;align-content:start;scroll-margin-top:16px}
.c[hidden]{display:none}
.c img,.c .fp{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--chip)}
.c .fp{background:var(--gl);display:grid;place-content:center;text-align:center;gap:4px}
.fp b{font:800 64px/.9 var(--display);color:var(--green);text-transform:uppercase}.fp span{font:500 11px var(--mono);text-transform:uppercase;color:var(--muted)}
.c .t{padding:12px 14px;display:grid;gap:6px}
.k{font:600 10.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--green)}
.c h3{font:800 24px/1 var(--display);text-transform:uppercase;margin:0;text-wrap:balance}
.c p{font-size:14px}
.where{font:500 12px var(--mono);color:var(--muted)}
.src{font-size:12px;color:var(--muted)}.more{font-weight:600;color:var(--ink)}
.cr{font-size:11px;color:var(--muted)}
.back{display:flex;gap:10px;flex-wrap:wrap}
.back a{font-weight:600;font-size:14px;padding:10px 14px;border-radius:6px;background:var(--ink);color:var(--bg);text-decoration:none}
details{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 14px}
summary{font-weight:600;cursor:pointer}
details ul{margin:8px 0 0;padding-left:18px;display:grid;gap:4px;font-size:14px}
footer{font-size:12.5px;color:var(--muted);border-top:1px solid var(--rule);padding-top:12px;display:grid;gap:4px}
"""
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)} · Resistance Daily</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website">
<meta property="og:url" content="{url}"><meta property="og:site_name" content="Resistance Daily"><meta name="twitter:card" content="summary">
<link rel="canonical" href="{url}">
{seo.jsonld(ld)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<nav class="top-nav"><a href="../"><b>Resistance Daily</b></a><span><a href="../today/">Today</a> · <a href="../focus/">Focus</a></span></nav>
<header><h1>Signs of <span>hope</span></h1>
<p class="lede">Where rights were upheld: court rulings, accountability, releases, and people helping each other. Same rule as every page: every fact is sourced.</p></header>
<div class="hero"><b>{n}</b><span class="cap">rights upheld {E(period)}</span><p>Courts, accountability and people who held their ground. Updated {datetime.date.fromisoformat(data["updated"]).strftime("%d %b %Y")}.</p></div>
<div class="filters" role="group" aria-label="Filter by kind">{"".join(f'<button type="button" aria-pressed="{str(k == "All").lower()}" data-k="{E(k)}">{E(k)}</button>' for k in kinds)}</div>
<section class="cards" aria-label="Signs of hope">{"".join(card(i) for i in items)}</section>
<div class="back"><a href="../today/">Back to today's edition</a></div>
<details><summary>How we choose</summary><ul>
<li>Rights upheld, not sides won: we judge the outcome for people's rights, whoever governs.</li>
<li>Every fact links to its source, and the official position stays in.</li>
<li>Hope is not spin: we never overstate, and we say what is still unresolved (for example, "he has not been arrested").</li>
<li>Know of people helping each other, or a community that won its fight? Write to <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a>.</li></ul></details>
<footer><span>{seo.FOLLOW}</span></footer>
</div>
<script>
(function(){{document.querySelectorAll('.filters button').forEach(function(b){{b.addEventListener('click',function(){{
document.querySelectorAll('.filters button').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});
var k=b.dataset.k;document.querySelectorAll('.c').forEach(function(c){{c.hidden=!(k==='All'||c.dataset.k===k)}});}})}});}})();
</script></body></html>
"""
    os.makedirs(os.path.join(root, "hope"), exist_ok=True)
    open(os.path.join(root, "hope", "index.html"), "w").write(page)
    return n, period, len(items)


if __name__ == "__main__":
    ist = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else ist.date()
    n, period, total = build(today)
    seo.write_sitemap(root)
    subprocess.run([sys.executable, os.path.join(root, "tools", "home.py"), "index.html"], check=True)
    print(f"built hope/index.html: {total} items, {n} {period}")
