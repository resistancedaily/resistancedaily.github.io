#!/usr/bin/env python3
"""Resistance Daily page generator.
Usage: python3 design.py DESIGN data.json [maps.json] > page.html
DESIGN: map | numbers | ledger | front | clock | tracker
Rotation (IST weekday): Mon map, Tue numbers, Wed ledger, Thu front, Fri clock, Sat map, Sun tracker.
The output is page content for the Artifact tool (no doctype/html/body; the tool adds them).
Tracker cases: region "india"|"world"; optional "count"+"countcap" for group detentions (shown instead of days).
Photos (optional; shown wherever an item has a summary, not in one-line lists such as front-page briefs or the
  tracker's news list): item "photo" = {src, alt, caption, credit, licence, licence_url, page, kind: "file"|"event",
  year, changes?, pos?}. "file" photos are labelled "File photo · YEAR". src is a site path (images/...) or a hotlinkable URL.
Focus (optional): item "focus" = slug of focus/SLUG.html (built by tools/focus.py); adds a "Photos and full story" link.
  data "focus" = [{slug, kicker, title, dek, src, alt, photos}] shows "In focus" cards above "Act today".
"""
import json, sys, html, datetime

D = sys.argv[1]
data = json.load(open(sys.argv[2]))
maps = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
E = html.escape
items = data["items"]
by_n = {i["n"]: i for i in items}

def src(i):
    s = " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in i["src"])
    if i.get("focus"):
        s += f' <a class="more" href="focus/{E(i["focus"])}.html">Photos and full story →</a>'
    return s

def photo_label(p):
    return "Photo from the event" if p.get("kind") == "event" else f"File photo · {p['year']}"

def photo_credit(p):
    ch = f" ({E(p['changes'])})" if p.get("changes") else ""
    return (f'Photo: <a href="{E(p["page"])}">{E(p["credit"])}</a>, '
            f'<a href="{E(p["licence_url"])}">{E(p["licence"])}</a>{ch}')

def photo(i, cls="ph"):
    p = i.get("photo")
    if not p:
        return ""
    pos = f' style="object-position:{E(p["pos"])}"' if p.get("pos") else ""
    return (f'<figure class="{cls}"><img src="{E(p["src"])}" alt="{E(p["alt"])}" loading="lazy" decoding="async"{pos}>'
            f'<figcaption><b>{photo_label(p)}</b>{E(p["caption"])} <span class="cr">{photo_credit(p)}</span></figcaption></figure>')

def rights(i):
    return " · ".join(i["rights"])

CSS = r"""
:root{
  --bg:#f3f4f2; --paper:#ffffff; --ink:#15181d; --muted:#5b616b; --rule:#d9dcd8;
  --land:#dfe2dd; --accent:#d9661a; --red:#b3261e; --orange:#d9661a; --grey:#7a808a; --green:#1d7a4c; --chip:#eceee9;
  --display:"Barlow Condensed","Arial Narrow",Arial,sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#111317; --paper:#181b20; --ink:#eceae5; --muted:#9ba1aa; --rule:#2b2f36;
  --land:#262a31; --accent:#f08a3c; --red:#ef6b62; --orange:#f08a3c; --grey:#8d939c; --green:#3fb07a; --chip:#22262c; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#111317; --paper:#181b20; --ink:#eceae5; --muted:#9ba1aa; --rule:#2b2f36;
  --land:#262a31; --accent:#f08a3c; --red:#ef6b62; --orange:#f08a3c; --grey:#8d939c; --green:#3fb07a; --chip:#22262c; color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.45}
.wrap{max-width:900px;margin:0 auto;padding-block:20px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}
a{color:inherit;text-decoration-color:var(--accent);text-underline-offset:2px}
a:focus-visible,summary:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3{font-family:var(--display);margin:0;text-transform:uppercase;letter-spacing:.01em;line-height:.95}
p{margin:0}
.mast{display:grid;gap:8px;border-bottom:3px solid var(--ink);padding-bottom:12px}
.mast .bar{height:5px;width:72px;background:var(--accent);border-radius:2px}
.mast h1{font-size:clamp(40px,8vw,64px);font-weight:800}
.mast .tag{color:var(--muted);max-width:62ch}
.mast .meta{font-family:var(--mono);font-size:12px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 16px}
.mast .meta b{color:var(--accent);font-weight:500;text-transform:uppercase;letter-spacing:.06em}
.key{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:13px;color:var(--muted);align-items:center}
.key b{color:var(--ink);font-weight:600;margin-right:4px}
.key>span{white-space:nowrap}
@media (max-width:620px){.key{gap:8px 14px;flex-wrap:nowrap}.key .l{display:none}}
.dot{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin-right:6px;flex:none}
.dot.red,.bg-red{background:var(--red)} .dot.orange,.bg-orange{background:var(--orange)} .dot.grey,.bg-grey{background:var(--grey)}
.c-red{color:var(--red)} .c-orange{color:var(--orange)} .c-grey{color:var(--grey)}
section{display:grid;gap:12px}
.sec-h{display:flex;align-items:baseline;justify-content:space-between;gap:12px;border-bottom:1px solid var(--rule);padding-bottom:6px}
.sec-h h2{font-size:32px;font-weight:800}
.sec-h span{font-family:var(--mono);font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.right{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.src{font-size:12px;color:var(--muted)}
.num{width:28px;height:28px;border-radius:50%;color:#fff;font:700 14px var(--body);display:grid;place-items:center;flex:none}
.acts{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}
.act{background:var(--paper);border:1px solid var(--rule);border-left:4px solid var(--green);border-radius:6px;padding:10px 12px;display:grid;gap:2px}
.act b{font:800 20px var(--display);text-transform:uppercase}
.act span{font-size:12.5px;color:var(--muted)}
details{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 14px}
summary{cursor:pointer;font-weight:600}
details[open] summary{margin-bottom:10px}
details ul{margin:0;padding-left:18px;display:grid;gap:4px;font-size:13.5px}
pre{white-space:pre-wrap;font-family:var(--body);font-size:14px;margin:0 0 10px}
button{font:600 14px var(--body);background:var(--ink);color:var(--bg);border:0;border-radius:4px;padding:9px 14px;cursor:pointer}
footer{font-size:12.5px;color:var(--muted);border-top:1px solid var(--rule);padding-top:12px;display:grid;gap:4px}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:12px;min-width:0}
.ph{margin:0;display:grid;gap:5px;min-width:0}
.ph img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:4px;background:var(--chip)}
.ph figcaption{font-size:12px;line-height:1.4;color:var(--muted)}
.ph figcaption b{font:500 10.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin-right:6px}
.ph .cr{display:block;font-size:11px}
.more{font-weight:600;color:var(--ink);white-space:nowrap}
.pics{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.pic{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px;display:grid;gap:6px;align-content:start;min-width:0}
.pic>.right{display:flex;align-items:center}
.fwrap{display:grid;gap:4px;justify-items:end}
.fstrip{width:100%;box-sizing:border-box;display:flex;align-items:center;flex-wrap:wrap;gap:6px 12px;background:var(--paper);border:1px solid var(--rule);border-left:5px solid var(--accent);border-radius:6px;padding:10px 14px;text-decoration:none;color:inherit}
.fstrip img{width:56px;height:56px;object-fit:cover;border-radius:4px;flex:none;background:var(--chip)}
.fstrip .k{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:var(--accent)}
.fstrip b{font:800 24px/1 var(--display);text-transform:uppercase;flex:1 1 220px}
.fstrip .go{font-weight:600;font-size:14px;white-space:nowrap}
.fwrap .all{font-size:12.5px;color:var(--muted)}
.focs{display:grid;gap:10px}
.fcard{background:var(--paper);border:1px solid var(--rule);border-left:5px solid var(--accent);border-radius:6px;display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);overflow:hidden;text-decoration:none;color:inherit}
.fcard img{display:block;width:100%;height:100%;min-height:150px;object-fit:cover;background:var(--chip)}
.fcard div{padding:14px 16px;display:grid;gap:6px;align-content:center}
.fcard .k{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:var(--accent)}
.fcard h3{font:800 30px/0.95 var(--display);text-transform:uppercase;text-wrap:balance}
.fcard p{font-size:14px;color:var(--muted)}
@media (max-width:560px){.fcard{grid-template-columns:1fr}.fcard img{aspect-ratio:16/9;min-height:0}}
"""

DESIGN_CSS = {
"map": r"""
.board{display:grid;gap:16px;grid-template-columns:minmax(0,5fr) minmax(0,6fr);align-items:start}
.board.world{grid-template-columns:1fr}
@media (max-width:700px){.board{grid-template-columns:1fr}}
.mapbox{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:8px;min-width:0}
.map{width:100%;height:auto;display:block}
.land{fill:var(--land)}
.pin circle{stroke:var(--paper);stroke-width:3}
.pin text{font:700 15px var(--body);fill:#fff}
.pin text.pl{font:600 15px var(--body);fill:var(--ink);paint-order:stroke;stroke:var(--land);stroke-width:4px}
.pin.red circle{fill:var(--red)} .pin.orange circle{fill:var(--orange)} .pin.grey circle{fill:var(--grey)}
.list{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.world .list{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.item{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 12px;display:grid;grid-template-columns:30px 1fr auto;gap:2px 10px;align-items:start;min-width:0;align-content:start}
.item .num{grid-row:span 3}
.place{font-weight:600}
.item .right{display:block;margin-top:1px}
.fig{grid-row:span 2;font:800 30px var(--display);line-height:1;text-align:right;white-space:nowrap}
.fig small{display:block;font:500 10.5px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-top:2px}
.what{grid-column:2/4;font-size:14px}
.item .src{grid-column:2/4}
""",
"numbers": r"""
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.tile{background:var(--paper);border:1px solid var(--rule);border-top:5px solid var(--grey);border-radius:6px;padding:16px;display:grid;gap:6px;align-content:start;min-width:0}
.tile.red{border-top-color:var(--red)} .tile.orange{border-top-color:var(--orange)}
.tile .big{font:800 64px var(--display);line-height:.9}
.tile .cap{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.tile .where{font-weight:600;font-size:16px;display:flex;gap:8px;align-items:center}
.tile p{font-size:14px}
.tile .right{display:block}
""",
"ledger": r"""
.ledger{display:grid;gap:14px}
.row{background:var(--paper);border:1px solid var(--rule);border-radius:6px;min-width:0;overflow:hidden}
.row .head{padding:12px 14px;border-bottom:1px solid var(--rule);display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px}
.row .head h3{font-size:26px;font-weight:800;white-space:nowrap}
.meter{display:flex;gap:4px}
.meter i{width:14px;height:14px;border-radius:50%}
.row .head .cnt{font:500 11px var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.row.empty .head{border-bottom:0}
.row .none{padding:12px 14px;color:var(--muted);font-size:14px}
.cards{list-style:none;margin:0;padding:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.st{border:1px solid var(--rule);border-top:5px solid var(--grey);border-radius:6px;overflow:hidden;display:flex;flex-direction:column;min-width:0;background:var(--bg);scroll-margin-top:12px}
.st.red{border-top-color:var(--red)} .st.orange{border-top-color:var(--orange)}
.st>.ph{gap:0}
.st>.ph img{border-radius:0}
.st>.ph figcaption{padding:6px 12px 0}
.st .figp{aspect-ratio:16/9;background:var(--chip);display:grid;place-content:center;justify-items:center;gap:4px;padding:8px;text-align:center}
.st .figp b{font:800 64px/0.9 var(--display)}
.st .figp span{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.st .tx{padding:10px 12px 12px;display:grid;gap:5px;align-content:start}
.st .where{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;font-weight:600;font-size:14px}
.st .where .fig{font:800 22px var(--display);margin-left:auto;white-space:nowrap}
.st h4{font:800 22px/1 var(--display);text-transform:uppercase;margin:0;text-wrap:balance}
.st p{font-size:14px}
.st .also{font:500 10.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.xref{padding:0 14px 12px;font-size:13px;color:var(--muted)}
.xref a{font-weight:600;color:var(--ink)}
""",
"front": r"""
.lead{background:var(--paper);border:1px solid var(--rule);border-top:6px solid var(--red);border-radius:6px;padding:18px;display:grid;grid-template-columns:auto 1fr;gap:6px 22px;align-items:center}
.lead .big{font:800 clamp(72px,14vw,120px) var(--display);line-height:.85;grid-row:span 3}
.lead h2{font-size:clamp(30px,5vw,44px);font-weight:800;text-wrap:balance}
.lead p{font-size:16px;max-width:60ch}
@media (max-width:560px){.lead{grid-template-columns:1fr}.lead .big{grid-row:auto}}
.lead>.ph{grid-column:1/-1;margin-bottom:6px}
.lead>.ph img{aspect-ratio:21/9}
.seconds{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}
.second{background:var(--paper);border:1px solid var(--rule);border-top:4px solid var(--grey);border-radius:6px;padding:14px;display:grid;gap:6px;align-content:start}
.second.red{border-top-color:var(--red)} .second.orange{border-top-color:var(--orange)}
.second .big{font:800 44px var(--display);line-height:.9}
.second h3{font-size:22px;font-weight:800;text-wrap:balance}
.second p{font-size:14px}
.briefs{list-style:none;margin:0;padding:0;background:var(--paper);border:1px solid var(--rule);border-radius:6px}
.briefs li{display:grid;grid-template-columns:auto 150px 1fr;gap:10px;align-items:baseline;padding:9px 14px;border-top:1px solid var(--rule);font-size:14px}
.briefs li:first-child{border-top:0}
.briefs .place{font-weight:600}
@media (max-width:560px){.briefs li{grid-template-columns:auto 1fr}.briefs li span:last-child{grid-column:2}}
""",
"clock": r"""
.clock{list-style:none;margin:0;padding:0 0 0 0;position:relative;display:grid;gap:0}
.clock:before{content:"";position:absolute;left:96px;top:6px;bottom:6px;width:3px;background:var(--rule)}
.ev{display:grid;grid-template-columns:84px 28px 1fr;gap:12px;align-items:start;padding:8px 0;position:relative}
.ev time{font:500 13px var(--mono);color:var(--muted);text-align:right;padding-top:5px}
.ev .num{position:relative;z-index:1}
.ev .body{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 12px;display:grid;gap:2px;min-width:0}
.ev .place{font-weight:600}
.ev p{font-size:14.5px}
.ev .ph{margin-top:6px;max-width:420px}
@media (max-width:480px){.clock:before{left:70px}.ev{grid-template-columns:58px 28px 1fr;gap:8px}}
""",
"tracker": r"""
.cases{display:grid;gap:10px}
.case{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:14px;display:grid;gap:8px;min-width:0}
.case .top{display:flex;justify-content:space-between;gap:12px;align-items:baseline;flex-wrap:wrap}
.case h3{font-size:26px;font-weight:800}
.case .days{font:800 44px var(--display);line-height:.9;color:var(--orange)}
.case .days small{font:500 12px var(--mono);color:var(--muted);text-transform:uppercase;margin-left:6px}
.track{height:14px;background:var(--chip);border-radius:3px;position:relative;overflow:hidden}
.track i{position:absolute;inset:0 auto 0 0;background:var(--orange);border-radius:3px;min-width:4px}
.case .meta{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:13.5px;color:var(--muted)}
.scale{font:500 11px var(--mono);color:var(--muted)}
.grp{font-size:22px;font-weight:800;display:flex;justify-content:space-between;align-items:baseline;margin-top:10px;border-bottom:2px solid var(--ink);padding-bottom:4px}
.grp span{font:500 11px var(--mono);color:var(--muted);letter-spacing:.06em}
.case .meta b{color:var(--ink);font-weight:600}
.news{list-style:none;margin:0;padding:0;background:var(--paper);border:1px solid var(--rule);border-radius:6px}
.news li{display:grid;grid-template-columns:auto 1fr auto;gap:2px 10px;align-items:baseline;padding:8px 14px;border-top:1px solid var(--rule);min-width:0}
.news li:first-child{border-top:0}
.news .place{font-weight:600}
.news .fig{font:800 20px var(--display);white-space:nowrap}
.news li>span:nth-child(2){font-size:14.5px;min-width:0}
.news .src{grid-column:2/4}
""",
}

def head(subtitle_tag):
    return f"""<title>Resistance Daily</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>/* Resistance Daily · design: {D}. Shared tokens; one simple layout per weekday. */{CSS}{DESIGN_CSS[D]}</style>
<div class="wrap">
<header class="mast">
  <div class="bar" aria-hidden="true"></div>
  <h1>Resistance Daily</h1>
  <p class="tag">Where people's rights were at risk in the last 24 hours. Non-partisan, and every fact links to its source.</p>
  <div class="meta"><span>{E(data['date_long'])}</span><span>Covers {E(data['window'])}</span><span>2-minute read</span><b>{E(subtitle_tag)}</b></div>
</header>{focus_strip()}"""

def focus_strip():
    """Highlighted link under the masthead, so readers arriving from an Instagram Focus post find the full story at once."""
    fs = data.get("focus", [])
    if not fs:
        return '\n<a class="fstrip" href="focus/"><span class="k">In focus</span><b>In-depth stories, every fact sourced</b><span class="go">All stories →</span></a>'
    f = fs[0]
    more = f'<a class="all" href="focus/">All Focus stories</a>'
    return (f'\n<div class="fwrap"><a class="fstrip" href="focus/{E(f["slug"])}.html"><img src="{E(f["src"])}" alt="" loading="eager" decoding="async">'
            f'<span class="k">In focus</span><b>{E(f["title"])}</b><span class="go">Read the full story →</span></a>{more}</div>')

KEY = """<div class="key" aria-label="Colour key"><b>Key</b>
<span><i class="dot red"></i>Lives lost<span class="l"> or violence</span></span>
<span><i class="dot orange"></i>Detention<span class="l"> or restriction</span></span>
<span><i class="dot grey"></i>Ongoing<span class="l">, no major change</span></span></div>"""

def focus_cards():
    fs = data.get("focus", [])
    if not fs:
        return ""
    cards = "".join(f'''<a class="fcard" href="focus/{E(f["slug"])}.html"><img src="{E(f["src"])}" alt="{E(f["alt"])}" loading="lazy" decoding="async">
<div><span class="k">{E(f["kicker"])}</span><h3>{E(f["title"])}</h3><p>{E(f["dek"])}</p><span class="more">See {f["photos"]} photos and the full story →</span></div></a>''' for f in fs)
    return f'''
<section aria-labelledby="h-foc"><div class="sec-h"><h2 id="h-foc">In focus</h2><span>The full story</span></div><div class="focs">{cards}</div></section>'''

def tail():
    acts = "".join(f'<div class="act"><b>{E(t)}</b><span>{E(s)}</span></div>' for t, s in data["acts"])
    top4 = sorted(items, key=lambda i: {"red": 0, "orange": 1, "grey": 2}[i["sev"]])[:4]
    share = f"Resistance Daily, {data['date_short']}\n" + "\n".join(f"• {i.get('short', i['place'])}: {i['headline']}" for i in top4) + f"\nSources for every fact, in the full edition: https://resistancedaily.github.io/archive/{data['date']}.html"
    return focus_cards() + f"""
<section aria-labelledby="h-act"><div class="sec-h"><h2 id="h-act">Act today</h2><span>Whatever your politics</span></div><div class="acts">{acts}</div></section>
<details><summary>Copy for WhatsApp</summary><pre id="share-text">{E(share)}</pre><button id="copy" type="button">Copy text</button></details>
<details><summary>How we report</summary><ul>
<li>We cover rights, not parties: life, assembly, expression, press, due process, land.</li>
<li>Every number links to its source, with ground reporting first.</li>
<li>Official positions appear next to allegations; claims are labelled as claims.</li>
<li>When sources disagree, we show the range. Maps show land only, with no political borders.</li>
<li>Photos are freely licensed and credited. "File photo" marks an older picture of the place, not of the event. We blur protesters' faces.</li></ul></details>
<footer><span>A new edition is published every morning at 9:00 IST, in a different layout each day: Mon map · Tue numbers · Wed rights ledger · Thu front page · Fri 24-hour clock · Sat map · Sun "Still waiting".</span><span>Seen something? Send photos with the date, the place and your permission to publish to <a href="mailto:resistancedaily.in@gmail.com?subject=Photo%20for%20Resistance%20Daily">resistancedaily.in@gmail.com</a>. We check every photo and blur faces.</span></footer>
</div>
<script>
(function(){{var b=document.getElementById('copy');if(!b)return;b.addEventListener('click',function(){{
var t=document.getElementById('share-text').innerText;
function done(){{b.textContent='Copied';setTimeout(function(){{b.textContent='Copy text'}},1800)}}
function fb(){{var r=document.createRange();r.selectNodeContents(document.getElementById('share-text'));var s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected. Press copy'}}
try{{navigator.clipboard.writeText(t).then(done,fb)}}catch(e){{fb()}}}});}})();
</script>"""

def item_li(i):
    return f"""<li class="item"><span class="num bg-{i['sev']}">{i['n']}</span><span><span class="place">{E(i['place'])}</span><span class="right">{E(rights(i))}</span></span><span class="fig c-{i['sev']}">{E(i['fig'])}<small>{E(i['figcap'])}</small></span>
<p class="what">{E(i['text'])}</p>{photo(i, "ph what")}<span class="src">{src(i)}</span></li>"""

def design_map():
    ind = [i for i in items if i["region"] == "india"]; wor = [i for i in items if i["region"] == "world"]
    return f"""{KEY}
<section aria-labelledby="h-india"><div class="sec-h"><h2 id="h-india">India</h2><span>{len(ind)} places</span></div>
<div class="board"><div class="mapbox">{maps.get('india','')}</div><ol class="list">{''.join(item_li(i) for i in ind)}</ol></div></section>
<section aria-labelledby="h-world"><div class="sec-h"><h2 id="h-world">World</h2><span>{len(wor)} places</span></div>
<div class="board world"><div class="mapbox">{maps.get('world','')}</div><ol class="list">{''.join(item_li(i) for i in wor)}</ol></div></section>"""

def design_numbers():
    tiles = "".join(f"""<div class="tile {i['sev']}">{photo(i)}<span class="big c-{i['sev']}">{E(i['fig'])}</span><span class="cap">{E(i['figcap'])}</span>
<span class="where"><i class="dot {i['sev']}"></i>{E(i['place'])}</span><span class="right">{E(rights(i))}</span><p>{E(i['text'].split('. ')[0].rstrip('.'))}.</p><span class="src">{src(i)}</span></div>""" for i in items)
    return f"""{KEY}<section aria-labelledby="h-num"><div class="sec-h"><h2 id="h-num">The day in numbers</h2><span>{len(items)} places</span></div><div class="tiles">{tiles}</div></section>"""

RIGHTS = [("Life & safety", "Killings, injuries, attacks on civilians"), ("Assembly", "Protests, marches, gathering bans"),
          ("Expression", "Speech, press, art, online posts"), ("Due process", "Detention, charges, courts, legal access"),
          ("Land", "Land, forests, homes, livelihoods")]
def design_ledger():
    """Each place appears once, under its first right, as a card: photo (or its key figure when there is no photo),
    headline, summary, sources. Cards with photos come first. Other rights a place touches link back to its card."""
    def card(i):
        p = i.get("photo")
        top = photo(i) if p else f'<div class="figp"><b class="c-{i["sev"]}">{E(i["fig"])}</b><span>{E(i["figcap"])}</span></div>'
        fig = f'<span class="fig c-{i["sev"]}">{E(i["fig"])} <span class="right">{E(i["figcap"])}</span></span>' if p else ""
        also = f'<span class="also">Also: {E(" · ".join(i["rights"][1:]))}</span>' if len(i["rights"]) > 1 else ""
        return (f'<li id="i{i["n"]}" class="st {i["sev"]}">{top}<div class="tx"><span class="where">{E(i["place"])}{fig}</span>'
                f'<h4>{E(i["headline"])}</h4><p>{E(i["text"])}</p>{also}<span class="src">{src(i)}</span></div></li>')
    rows = []
    for r, desc in RIGHTS:
        hits = [i for i in items if r in i["rights"]]
        own = sorted((i for i in hits if i["rights"][0] == r), key=lambda i: not i.get("photo"))
        xref = [i for i in hits if i["rights"][0] != r]
        meter = "".join(f'<i class="bg-{i["sev"]}"></i>' for i in hits) or '<i style="background:var(--chip)"></i>'
        body = f'<ul class="cards">{"".join(card(i) for i in own)}</ul>' if own else ""
        if xref:
            body += '<p class="xref">Also here: ' + " · ".join(f'<a href="#i{i["n"]}">{E(i.get("short", i["place"]))}</a>' for i in xref) + "</p>"
        if not hits:
            body = '<p class="none">No new reports in this window.</p>'
        rows.append(f"""<div class="row{' empty' if not hits else ''}"><div class="head"><h3>{E(r)}</h3><div class="meter" aria-label="{len(hits)} places">{meter}</div><span class="cnt">{len(hits)} place{'s' if len(hits)!=1 else ''} · {E(desc)}</span></div>{body}</div>""")
    return f"""{KEY}<section aria-labelledby="h-led"><div class="sec-h"><h2 id="h-led">Which rights were at risk</h2><span>Each place is listed once</span></div><div class="ledger">{''.join(rows)}</div></section>"""

def design_front():
    order = sorted(items, key=lambda i: (not i.get("lead"), {"red": 0, "orange": 1, "grey": 2}[i["sev"]], i["n"]))
    lead, seconds, briefs = order[0], order[1:4], order[4:]
    sec = "".join(f"""<article class="second {i['sev']}">{photo(i)}<span class="right">{E(i['place'])} · {E(rights(i))}</span><span class="big c-{i['sev']}">{E(i['fig'])}</span><h3>{E(i['headline'])}</h3><p>{E(i['text'])}</p><span class="src">{src(i)}</span></article>""" for i in seconds)
    br = "".join(f"""<li><i class="dot {i['sev']}"></i><span class="place">{E(i['place'])}</span><span>{E(i['headline'])} <span class="src">· {src(i)}</span></span></li>""" for i in briefs)
    return f"""{KEY}
<article class="lead">{photo(lead)}<span class="big c-{lead['sev']}">{E(lead['fig'])}</span><span class="right">{E(lead['place'])} · {E(rights(lead))}</span><h2>{E(lead['headline'])}</h2><p>{E(lead['text'])} <span class="src">{src(lead)}</span></p></article>
<div class="seconds">{sec}</div>
<section aria-labelledby="h-br"><div class="sec-h"><h2 id="h-br">Briefly</h2><span>{len(briefs)} more</span></div><ul class="briefs">{br}</ul></section>"""

def design_clock():
    evs = sorted(data.get("events", []), key=lambda e: -e["sort"])
    first = {}
    for e in evs:
        first.setdefault(e["n"], e)
    lis = "".join(f"""<li class="ev"><time>{E(e['t'])}</time><span class="num bg-{by_n[e['n']]['sev']}">{e['n']}</span><div class="body"><span class="place">{E(by_n[e['n']]['place'])} <span class="right">· {E(rights(by_n[e['n']]))}</span></span><p>{E(e['text'])}</p>{photo(by_n[e['n']]) if e is first[e['n']] else ""}<span class="src">{src(by_n[e['n']])}</span></div></li>""" for e in evs)
    covered = {e["n"] for e in evs}
    rest = [i for i in items if i["n"] not in covered]
    restli = "".join(f"""<li class="ev"><time>—</time><span class="num bg-{i['sev']}">{i['n']}</span><div class="body"><span class="place">{E(i['place'])}</span><p>{E(i['headline'])}</p>{photo(i)}<span class="src">{src(i)}</span></div></li>""" for i in rest)
    return f"""{KEY}<section aria-labelledby="h-clk"><div class="sec-h"><h2 id="h-clk">The last 24 hours</h2><span>Newest first · IST</span></div><ol class="clock">{lis}</ol></section>
{'<section aria-labelledby="h-also"><div class="sec-h"><h2 id="h-also">Also reported</h2><span>Time not reported</span></div><ol class="clock">'+restli+'</ol></section>' if rest else ''}"""

def design_tracker():
    asof = datetime.date.fromisoformat(data["asof"])
    for c in data["cases"]:
        c["days"] = (asof - datetime.date.fromisoformat(c["since"])).days
    mx = max(c["days"] for c in data["cases"])
    def csrc(c):
        # src is one [name, url] pair or a list of them
        pairs = c["src"] if isinstance(c["src"][0], list) else [c["src"]]
        return " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in pairs)
    def card(c):
        w = max(c["days"] / mx * 100, 0.6)
        yrs = f" (~{c['days']/365.25:.1f} years)" if c["days"] > 400 else ""
        if c.get("count"):
            big = f'{E(c["count"])}<small>{E(c.get("countcap","people held"))}</small>'
        else:
            big = f'{c["days"]:,}<small>days held{yrs}</small>'
        return f"""<div class="case"><div class="top"><h3>{E(c['name'])}</h3><span class="days">{big}</span></div>
<div class="track" aria-hidden="true"><i style="width:{w:.1f}%"></i></div>
<div class="meta"><span><b>{E(c['where'])}</b></span><span>Since {datetime.date.fromisoformat(c['since']).strftime('%d %b %Y')}</span><span>{E(c['law'])}</span><span>{E(c['status'])}</span><span class="src">{csrc(c)}</span></div></div>"""
    groups = [("india", "India"), ("world", "World")]
    out = []
    for key, label in groups:
        cs = sorted([c for c in data["cases"] if c.get("region", "india") == key], key=lambda c: -c["days"])
        if cs:
            out.append(f'<h3 class="grp">{label}<span>{len(cs)} case{"s" if len(cs)!=1 else ""}</span></h3>' + "".join(card(c) for c in cs))
    news = "".join(f"""<li><i class="dot {i['sev']}"></i><span><span class="place">{E(i.get('short', i['place']))}</span> · {E(i['headline'])}</span><span class="fig c-{i['sev']}">{E(i['fig'])}</span><span class="src">{src(i)}</span></li>""" for i in items)
    news_sec = f"""{KEY}<section aria-labelledby="h-news"><div class="sec-h"><h2 id="h-news">Today's news</h2><span>{len(items)} places</span></div><ul class="news">{news}</ul></section>
""" if items else ""
    return news_sec + f"""<section aria-labelledby="h-sw"><div class="sec-h"><h2 id="h-sw">Still waiting</h2><span>Weekly · days counted to {asof.strftime('%d %b %Y')}</span></div>
<p style="color:var(--muted);max-width:66ch">People held for a long time after speaking out, protesting, reporting or providing care, with or without a verdict, around the world. All bars use one scale: the longest detention fills the bar.</p>
<div class="cases">{''.join(out)}</div></section>"""

TAGS = {"map": "Map edition", "numbers": "Numbers edition", "ledger": "Rights ledger", "front": "Front page", "clock": "24-hour clock", "tracker": "Still waiting · weekly"}
body = {"map": design_map, "numbers": design_numbers, "ledger": design_ledger, "front": design_front, "clock": design_clock, "tracker": design_tracker}[D]()
sys.stdout.write(head(TAGS[D]) + body + tail())
