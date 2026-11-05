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
import rdsite as S

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
    """Sage card, decluttered (owner's request, 5 Nov 2026): photo (credit behind the (i) button) or the key number in its
    place, kind · date, headline, a quiet "place · source" line; the story and its thread link sit under "Details"."""
    p = i.get("photo")
    d = datetime.date.fromisoformat(i["date"]).strftime("%d %b").lstrip("0")
    src = " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in i["src"])
    if p:
        lab = ("File photo · " + E(p["year"])) if p.get("kind") != "event" else "Photo from the event"
        media = (f'<figure class="hm"><img class="washed" src="../{E(p["src"])}" alt="{E(p["alt"])}" loading="lazy" decoding="async">'
                 f'<details class="rd-info"><summary aria-label="About this photo">i</summary><figcaption>{lab}. {E(p.get("caption", ""))} '
                 f'Photo: <a href="{E(p["page"])}">{E(p["credit"])}</a>, <a href="{E(p["licence_url"])}">{E(p["licence"])}</a></figcaption></details></figure>')
    else:
        media = f'<div class="hm hfig"><b>{E(i.get("fig", ""))}</b><span>{E(i.get("figcap", ""))}</span></div>'
    part = f'<a class="rd-more" href="../{E(i["link"][1])}">Part of {E(i["link"][0])} →</a>' if i.get("link") else ""
    return (f'<article class="hc" id="{E(i["id"])}" data-k="{E(i["kind"])}">{media}<div class="t">'
            f'<span class="hk">{E(i["kind"])} · {d}</span><h3>{E(i["headline"])}</h3>'
            f'<span class="src">{E(i["place"].split(",")[0])} · {src}</span>'
            f'<details class="hd"><summary>Details</summary><p>{E(i["text"])}</p>{part}</details></div></article>')


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
    month = sum(1 for i in items if 0 <= (today - datetime.date.fromisoformat(i["date"])).days < 31)
    week = sum(1 for i in items if 0 <= (today - datetime.date.fromisoformat(i["date"])).days < 7)
    CSS = """
.hhero{padding:34px 40px 32px;background:var(--color-accent-2-200);color:var(--color-accent-2-900);border-radius:32px}
.hhero h1{font-size:52px;margin:6px 0 6px;color:inherit}
.hhero .rd-kicker{color:var(--color-accent-2-800)}
.hhero p{margin:0;font-size:17px}
.hhero .n{font-family:var(--font-heading);font-size:22px;margin-top:14px;display:block}
.hc .tag-accent-2{background:var(--color-accent-2-200)}
.filters{display:flex;gap:8px;flex-wrap:wrap}
.filters button{font:600 13px var(--font-body);padding:8px 14px;border-radius:999px;background:var(--color-accent-2-100);color:var(--color-accent-2-900);border:0;cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--color-accent-2);color:#fff}
.hcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:16px;align-items:start}
.hc{background:var(--color-accent-2-100);color:var(--color-accent-2-900);border-radius:28px;overflow:hidden;display:flex;flex-direction:column;scroll-margin-top:16px}
.hc[hidden]{display:none}
.hm{position:relative;margin:0;line-height:0;aspect-ratio:16/9;overflow:hidden;min-height:0}.hm img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.hm .rd-info{z-index:1}
.hm .rd-info,.hm .rd-info figcaption{line-height:1.35}
.hfig{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--color-accent-2-200);line-height:1.1;text-align:center;padding:0 20px}
.hfig b{font-family:var(--font-heading);font-weight:400;font-size:54px}.hfig span{font-size:14px}
.hd>summary{font-weight:600;font-size:13.5px;color:var(--color-accent-2-800)}.hd>summary::before{content:'+ '}.hd[open]>summary::before{content:'− '}
.hd p{margin:8px 0 6px}
.hc .t{padding:18px 20px 20px;display:flex;flex-direction:column;gap:8px}
.hc h3{font-family:var(--font-body);font-weight:600;font-size:18px;line-height:1.3;margin:0;color:inherit;letter-spacing:0}
.hc p{margin:0;font-size:15px}
.hk{font-size:12.5px;color:var(--color-accent-2-800)}
.hc .src{font-size:13px;opacity:.85}.hc a{color:var(--color-accent-2-900)}
.hc .cr{font-size:11.5px;opacity:.85}
.rd-how ul a{color:inherit}
@media (max-width:720px){.hhero{padding:22px 20px 22px;border-radius:28px}.hhero h1{font-size:34px}.hhero p{font-size:15px}.hhero .n{font-size:19px}}
"""
    extra = (f'<meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary">'
             + seo.jsonld(ld))
    page = (S.head(f"{title} · Resistance Daily", desc, "../", url, extra, css=CSS) + S.nav("../") + f"""
<header class="hhero"><span class="rd-kicker">Signs of hope</span><h1>Rights upheld</h1>
<span class="n">{week} this week · {month} this month</span></header>
<div class="filters" role="group" aria-label="Filter by kind">{"".join(f'<button type="button" aria-pressed="{str(k == "All").lower()}" data-k="{E(k)}">{E(k)}</button>' for k in kinds)}</div>
<section class="hcards" aria-label="Rights upheld">{"".join(card(i) for i in items)}</section>
<details class="rd-how"><summary>How we choose</summary><ul>
<li>Rights upheld, not sides won: we judge the outcome for people's rights, whoever governs.</li>
<li>Every fact links to its source, and the official position stays in.</li>
<li>Hope is not spin: we never overstate, and we say what is still unresolved (for example, "he has not been arrested").</li>
<li>Know of people helping each other, or a community that won its fight? Write to <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a>.</li></ul></details>
<script>
(function(){{document.querySelectorAll('.filters button').forEach(function(b){{b.addEventListener('click',function(){{
document.querySelectorAll('.filters button').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});
var k=b.dataset.k;document.querySelectorAll('.hc').forEach(function(c){{c.hidden=!(k==='All'||c.dataset.k===k)}});}})}});}})();
</script>""" + S.footer("../"))
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
