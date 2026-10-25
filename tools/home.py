#!/usr/bin/env python3
"""Resistance Daily home page: the front door to every section.

Usage (from the repo root):  python3 tools/home.py [OUT]     (OUT defaults to preview.html; index.html once live)
Reads the latest data/YYYY-MM-DD.json, data/focus/*.json, data/cases.json and archive/editions.json.
Sections, top to bottom: Today (top headlines + link to the full edition), In focus, Still waiting, Past editions,
Follow us (one line on what each channel is for), How we report.
"""
import sys, os, json, glob, html, datetime
import seo

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else "preview.html"
preview = os.path.basename(out) != "index.html"
SITE = seo.SITE
SEV = {"red": 0, "orange": 1, "grey": 2}


def load(p):
    return json.load(open(os.path.join(root, p)))


dates = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(root, "data", "????-??-??.json")))
date = dates[-1]
d = load(f"data/{date}.json")
dt = datetime.date.fromisoformat(date)
focus = sorted((load(p[len(root) + 1:]) for p in glob.glob(os.path.join(root, "data", "focus", "*.json"))
                if os.path.exists(os.path.join(root, "focus", os.path.basename(p)[:-5] + ".html"))),
               key=lambda f: f["updated"], reverse=True)
cases = load("data/cases.json")
log = load("archive/editions.json")
NAMES = {"map": "Map", "numbers": "Day in numbers", "ledger": "Rights ledger", "front": "Front page", "clock": "24-hour clock", "tracker": "Still waiting"}
# The full edition: /today/ once the hub is live, the dated archive page while previewing.
full = f"archive/{date}.html" if preview else "today/"

top = sorted(d["items"], key=lambda i: (not i.get("lead"), SEV[i["sev"]]))[:4]
today = "".join(f'<li><i class="dot {i["sev"]}"></i><span><b>{E(i.get("short", i["place"]))}</b> · {E(i["headline"])}</span></li>' for i in top)

cards = "".join(f'''<a class="fcard" href="focus/{E(f["slug"])}.html"><img src="{E(f["photos"][0]["src"])}" alt="{E(f["photos"][0]["alt"])}" loading="lazy" decoding="async">
<div><span class="k">{E(f["kicker"].replace("Focus · ", ""))}</span><h3>{E(f["title"])}</h3><p>{E(f["dek"])}</p>
<span class="upd">Updated {datetime.date.fromisoformat(f["updated"]).strftime("%d %b")}{" · What's new" if f.get("whats_new") else ""}</span></div></a>''' for f in focus[:3])  # phones show the first 2 (CSS below)

asof = datetime.date.fromisoformat(cases["asof"])
cs = cases["cases"]
longest = min(cs, key=lambda c: c["since"])
ldays = (asof - datetime.date.fromisoformat(longest["since"])).days
tracker = max((k for k, v in log.items() if v["design"] == "tracker"), default=None)

def ed_line(k):
    try:
        x = load(f"data/{k}.json")
        h = sorted(x["items"], key=lambda i: (not i.get("lead"), SEV[i["sev"]]))
        s = "; ".join(f'{i.get("short", i["place"])}: {i["headline"]}' for i in h[:2])
    except Exception:
        s = log[k]["summary"]
    return (f'<li><a href="archive/{k}.html"><b>{datetime.date.fromisoformat(k).strftime("%a %d %b")}</b></a>'
            f'<span class="t">{E(NAMES.get(log[k]["design"], log[k]["design"]))}</span><p>{E(s)}</p></li>')
past = "".join(ed_line(k) for k in sorted(log, reverse=True)[1:8])  # phones show the first 4

CH = [("Instagram", seo.INSTAGRAM, "Photo stories and the day's slides"),
      ("WhatsApp", seo.WHATSAPP, "Each morning's headlines on your phone"),
      ("X", seo.X, "Short updates and links"),
      ("Facebook", seo.FACEBOOK, "Editions and Focus stories to share")]
follow = "".join(f'<a class="ch" href="{u}"><b>{n}</b><span>{E(t)}</span></a>' for n, u, t in CH)
chips = "".join(f'<a href="{u}">{n}</a>' for n, u, t in CH)

desc = "A non-partisan daily record of human-rights and civil-liberties events in India and around the world. Every fact links to its source."
ld = [{"@context": "https://schema.org", "@type": "NewsMediaOrganization", "name": "Resistance Daily", "url": SITE,
       "email": "resistancedaily.in@gmail.com", "sameAs": seo.SAME_AS, "description": desc},
      {"@context": "https://schema.org", "@type": "WebSite", "name": "Resistance Daily", "url": SITE, "inLanguage": "en"}]
share = next((f"images/focus/{f['slug']}/share.jpg" for f in focus if os.path.exists(os.path.join(root, "images", "focus", f["slug"], "share.jpg"))), None)
og = f'<meta property="og:image" content="{SITE}{share}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if share else ""
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%2315181d'/%3E"
        "%3Crect x='14' y='18' width='22' height='6' rx='2' fill='%23d9661a'/%3E%3Ctext x='14' y='50' font-family='Arial' font-weight='900' font-size='26' fill='%23f3f4f2'%3ERD%3C/text%3E%3C/svg%3E")

CSS = """
:root{--bg:#f3f4f2;--paper:#fff;--ink:#15181d;--muted:#5b616b;--rule:#d9dcd8;--accent:#d9661a;--red:#b3261e;--grey:#7a808a;--green:#1d7a4c;--chip:#eceee9;
--display:"Barlow Condensed","Arial Narrow",Arial,sans-serif;--body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;--red:#ef6b62;--grey:#8d939c;--green:#3fb07a;--chip:#22262c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;--red:#ef6b62;--grey:#8d939c;--green:#3fb07a;--chip:#22262c;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--body)}
.wrap{max-width:900px;margin:0 auto;padding:20px max(16px,env(safe-area-inset-left,0px)) 48px;display:grid;gap:34px}
a{color:inherit;text-decoration-color:var(--accent);text-underline-offset:2px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3{font-family:var(--display);margin:0;text-transform:uppercase;line-height:.95}
p{margin:0}
.mast{display:grid;gap:10px;border-bottom:3px solid var(--ink);padding-bottom:14px}
.mast .bar{height:5px;width:72px;background:var(--accent);border-radius:2px}
.mast h1{font-size:clamp(44px,9vw,72px);font-weight:800}
.mast .tag{color:var(--muted);max-width:60ch;font-size:16px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips a{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;text-decoration:none;border:1px solid var(--rule);background:var(--paper);border-radius:999px;padding:6px 12px}
section{display:grid;gap:12px}
.sec-h{display:flex;align-items:baseline;justify-content:space-between;gap:12px;border-bottom:1px solid var(--rule);padding-bottom:6px}
.sec-h h2{font-size:34px;font-weight:800}
.sec-h a{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);white-space:nowrap}
.lede{color:var(--muted);max-width:66ch}
.today{background:var(--paper);border:1px solid var(--rule);border-left:5px solid var(--accent);border-radius:6px;padding:16px 18px;display:grid;gap:12px}
.today .when{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--accent)}
.today ul{list-style:none;margin:0;padding:0;display:grid;gap:8px;font-size:16px}
.today li{display:flex;gap:10px;align-items:baseline}
.dot{display:inline-block;width:11px;height:11px;border-radius:50%;flex:none;transform:translateY(1px)}
.dot.red{background:var(--red)}.dot.orange{background:var(--accent)}.dot.grey{background:var(--grey)}
.go{justify-self:start;font-weight:600;background:var(--ink);color:var(--bg);text-decoration:none;border-radius:4px;padding:10px 16px}
.focs{display:grid;gap:10px}
.fcard{background:var(--paper);border:1px solid var(--rule);border-left:5px solid var(--accent);border-radius:6px;display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);overflow:hidden;text-decoration:none;color:inherit}
.fcard img{display:block;width:100%;height:100%;min-height:150px;object-fit:cover;background:var(--chip)}
.fcard div{padding:14px 16px;display:grid;gap:6px;align-content:center}
.fcard .k,.upd{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:var(--accent)}
.upd{color:var(--muted)}
.fcard h3{font-size:30px;font-weight:800;text-wrap:balance}
.fcard p{font-size:14px;color:var(--muted)}
@media (max-width:560px){.fcard{grid-template-columns:1fr}.fcard img{aspect-ratio:16/9;min-height:0}}
.sw{background:var(--paper);border:1px solid var(--rule);border-top:5px solid var(--red);border-radius:6px;padding:16px 18px;display:grid;gap:10px}
.sw .big{display:flex;flex-wrap:wrap;gap:6px 26px;align-items:baseline}
.sw .big b{font:800 64px/0.9 var(--display);color:var(--red)}
.sw .big span{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.past{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.past li{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 14px}
.past .t{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin-left:8px}
.past p{color:var(--muted);font-size:14px;margin-top:2px}
.chs{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}
.ch{background:var(--paper);border:1px solid var(--rule);border-left:4px solid var(--green);border-radius:6px;padding:10px 12px;display:grid;gap:2px;text-decoration:none}
.ch b{font:800 22px var(--display);text-transform:uppercase}
.ch span{font-size:13px;color:var(--muted)}
.how{margin:0;padding-left:18px;display:grid;gap:4px;color:var(--muted);max-width:66ch}
/* Phones: a shorter page, so readers see every section rather than stopping in one. */
@media (max-width:620px){.fcard:nth-child(n+3){display:none}.past li:nth-child(n+5){display:none}
.sw .big{display:grid;gap:12px}.sw .big>div{display:grid;gap:4px}}
footer{font-size:12.5px;color:var(--muted);border-top:1px solid var(--rule);padding-top:12px;display:grid;gap:4px}
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Resistance Daily · Human rights, every fact sourced</title>
<meta name="description" content="{E(desc)}">{'<meta name="robots" content="noindex">' if preview else ''}
<meta property="og:title" content="Resistance Daily"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website">
<meta property="og:url" content="{SITE}"><meta property="og:site_name" content="Resistance Daily">{og}<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}"><link rel="icon" href="{ICON}">
{"".join(seo.jsonld(x) for x in ld)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<header class="mast"><div class="bar" aria-hidden="true"></div><h1>Resistance Daily</h1>
<p class="tag">A non-partisan daily record of human rights and civil liberties in India and around the world. Every fact links to its source.</p>
<nav class="chips" aria-label="Follow Resistance Daily">{chips}</nav></header>

<section aria-labelledby="h-today"><div class="sec-h"><h2 id="h-today">Today</h2><a href="{full}">Full edition →</a></div>
<p class="lede">What happened to people's rights in the last 24 hours, with the official position next to every claim. A new edition every morning at 9:00 IST.</p>
<div class="today"><span class="when">{dt.strftime("%A %d %B %Y")} · {E(NAMES.get(log.get(date, {}).get("design", ""), ""))}</span><ul>{today}</ul>
<a class="go" href="{full}">Read today's full edition →</a></div></section>

<section aria-labelledby="h-focus"><div class="sec-h"><h2 id="h-focus">In focus</h2><a href="focus/">All {len(focus)} stories →</a></div>
<p class="lede">One place or issue told in depth, with photos and a source for every fact. Updated whenever something changes.</p>
<div class="focs">{cards}</div></section>

<section aria-labelledby="h-sw"><div class="sec-h"><h2 id="h-sw">Still waiting</h2>{f'<a href="archive/{tracker}.html#still-waiting">Weekly tracker →</a>' if tracker else ''}</div>
<p class="lede">People held for a long time after speaking out, protesting, reporting or providing care, in India and around the world. Checked against sources every Sunday.</p>
<div class="sw"><div class="big"><div><b>{len(cs)}</b> <span>people and groups tracked</span></div><div><b>{ldays:,}</b> <span>days: the longest, {E(longest["name"])}, {E(longest["where"])}</span></div></div>
{f'<a class="go" href="archive/{tracker}.html#still-waiting">See every case, {datetime.date.fromisoformat(tracker).strftime("%a %d %b")} →</a>' if tracker else ''}</div></section>

<section aria-labelledby="h-past"><div class="sec-h"><h2 id="h-past">Past editions</h2><a href="archive/">All editions →</a></div>
<p class="lede">Every edition is kept permanently, each in its own layout.</p>
<ul class="past">{past}</ul></section>

<section aria-labelledby="h-follow"><div class="sec-h"><h2 id="h-follow">Follow us your way</h2></div><div class="chs">{follow}</div></section>

<section aria-labelledby="h-how"><div class="sec-h"><h2 id="h-how">How we report</h2></div><ul class="how">
<li>We cover rights, not parties: life and safety, assembly, expression, press freedom, due process, land and livelihood.</li>
<li>Every number links to its source, with ground-level reporting first.</li>
<li>Official positions appear next to allegations; claims are labelled as claims; when sources disagree we show the range.</li>
<li>Photos are freely licensed and credited; we blur protesters' and children's faces.</li></ul></section>

<footer><span>Seen something? Send photos with the date, the place and your permission to publish, or a tip or correction, to <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a>.</span>
<span>{seo.FOLLOW}</span></footer>
</div></body></html>
"""
open(os.path.join(root, out), "w").write(page)
print("built home", out, date)
