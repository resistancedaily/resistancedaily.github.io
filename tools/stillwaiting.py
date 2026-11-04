#!/usr/bin/env python3
"""Build the standalone "Still waiting" page (still-waiting/index.html), also the still-waiting thread (Nov 2026).

Usage (from the repo root):  python3 tools/stillwaiting.py      (run by publish.py on every edition)
Reads data/cases.json (verified every Sunday, see ROUTINE.md) and lists every case, longest held first, with the day
count to cases["asof"]. Older Sunday editions keep their own "Still waiting" section, so archive anchors still work.
"""
import os, json, html, datetime
import seo
import rdsite as S

E = html.escape
root = S.root

CSS = """
.swh{display:flex;flex-direction:column;gap:8px}
.swh h1{font-size:44px;margin:6px 0 2px}
.sw{display:flex;flex-direction:column;gap:14px}
.swg{font-size:24px;margin:10px 0 0}
.swc{background:var(--color-surface);border-radius:28px;padding:20px 24px;display:grid;grid-template-columns:1fr auto;gap:6px 24px;align-items:start}
.swc h3{font-size:20px;margin:0;line-height:1.2}
.swc .n{grid-row:span 3;text-align:right;font-family:var(--font-heading);font-size:32px;line-height:1;color:var(--color-text)}
.swc .n small{display:block;font-family:var(--font-body);font-size:12.5px;color:var(--color-neutral-700);margin-top:4px}
.swc .w{font-size:13.5px;color:var(--color-neutral-700)}
.swc p{margin:0;font-size:15px;grid-column:1/-1}
.swc .rd-src{grid-column:1/-1}
@media (max-width:720px){.swh h1{font-size:30px}.swc{padding:16px 18px}.swc .n{font-size:26px}}
"""


def build():
    c = S.load("data/cases.json")
    asof = datetime.date.fromisoformat(c["asof"])
    cases = c["cases"]
    for x in cases:
        x["_days"] = (asof - datetime.date.fromisoformat(x["since"])).days
    lo = max(cases, key=lambda x: x["_days"])

    def card(x):
        pairs = x["src"] if isinstance(x["src"][0], list) else [x["src"]]
        big = (f'{E(x["count"])}<small>{E(x.get("countcap", "people held"))}</small>' if x.get("count")
               else f'{x["_days"]:,}<small>days held</small>')
        since = datetime.date.fromisoformat(x["since"]).strftime("%d %b %Y").lstrip("0")
        return (f'<article class="swc"><h3>{E(x["name"])}</h3><span class="n">{big}</span>'
                f'<span class="w">{E(x["where"])} · since {since} · {E(x["law"])}</span>'
                f'<p>{E(x["status"])}</p><span class="rd-src">{S.src_links(pairs)}</span></article>')

    groups = ""
    for key, label in (("india", "India"), ("world", "World")):
        cs = sorted((x for x in cases if x.get("region", "india") == key), key=lambda x: -x["_days"])
        if cs:
            groups += f'<h2 class="swg">{label} <span class="rd-sub">· {len(cs)}</span></h2>' + "".join(card(x) for x in cs)
    url = f"{S.SITE}still-waiting/"
    desc = (f'{len(cases)} people and groups held for a long time after speaking out, protesting, reporting or providing care. '
            f'Longest: {lo["name"]}, {lo["_days"]:,} days. Every case verified weekly, every fact sourced.')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Jailed for speaking out", "description": desc,
          "url": url, "dateModified": c["asof"], "publisher": seo.PUBLISHER}
    extra = (f'<meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary">'
             + seo.jsonld(ld))
    page = (S.head("Jailed for speaking out · Still waiting · Resistance Daily", desc, "../", url, extra, css=CSS) + S.nav("../")
            + f"""<header class="swh"><span class="rd-kicker">Still waiting</span><h1>Jailed for speaking out</h1>
<p class="rd-stat">{len(cases)} held · longest: {E(lo["name"])}, {lo["_days"]:,} days</p>
<p class="rd-sub" style="margin:0">People held after speaking out, protesting, reporting or providing care, with or without a verdict. Cases are re-checked every Sunday; days are counted to {asof.strftime("%d %b %Y").lstrip("0")}.</p>
<div class="rd-row" style="margin-top:6px"><button class="btn btn-primary" data-rd-follow="still-waiting">Follow this thread</button></div></header>
<section class="sw" aria-label="Cases">{groups}</section>""" + S.footer("../"))
    os.makedirs(os.path.join(root, "still-waiting"), exist_ok=True)
    open(os.path.join(root, "still-waiting", "index.html"), "w").write(page)
    return len(cases)


if __name__ == "__main__":
    print("built still-waiting/index.html:", build(), "cases")
