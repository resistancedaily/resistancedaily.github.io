#!/usr/bin/env python3
"""Resistance Daily home page: the front door to every section.

Usage (from the repo root):  python3 tools/home.py [OUT]     (OUT: index.html, the live home page; any other name
                                                              builds a preview that search engines skip)
Run automatically by publish.py and focus.py.
Reads the latest data/YYYY-MM-DD.json, data/focus/*.json, data/cases.json and archive/editions.json.
Sections, top to bottom (kept minimal: numbers first, one line each): Today, In focus (4 compact cards with each
story's key number), Tracking (Still waiting + Accountability Watch), Past editions (one headline each), How we report
(folded). Follow links sit in the masthead chips and the footer.
"""
import sys, os, json, glob, html, datetime
import seo

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else "index.html"
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

def lead_fig(f):
    x = (f.get("figs") or [{}])[0]
    return f'<span class="kf"><b>{E(x["fig"])}</b> {E(x["figcap"])}</span>' if x.get("fig") else ""


cards = "".join(f'''<a class="fcard" href="focus/{E(f["slug"])}.html"><img src="{E(f["photos"][0]["src"])}" alt="" loading="lazy" decoding="async">
<div><span class="k">{E(f["kicker"].replace("Focus · ", "").split(", ")[0])} · {datetime.date.fromisoformat(f["updated"]).strftime("%d %b")}{" · New" if f.get("whats_new") else ""}</span><h3>{E(f["title"])}</h3>{lead_fig(f)}</div></a>''' for f in focus[:4])  # phones show the first 2 (CSS below)

asof = datetime.date.fromisoformat(cases["asof"])
cs = cases["cases"]
longest = min(cs, key=lambda c: c["since"])
ldays = (asof - datetime.date.fromisoformat(longest["since"])).days
tracker = max((k for k, v in log.items() if v["design"] == "tracker"), default=None)
# Accountability Watch (tools/accountability.py): open cases and the share still without an arrest.
acc = load("data/accountability.json") if os.path.exists(os.path.join(root, "data", "accountability.json")) else None
if acc:
    acc_open = [c for c in acc["cases"] if not c.get("closed")]
    acc_noarrest = sum(1 for c in acc_open if any(s["step"].lower().startswith("arrest") for s in c["steps"])
                       and not any(s["step"].lower().startswith("arrest") and s["status"] == "done" for s in c["steps"]))
    acc_states = len({c["state"] for c in acc_open if c.get("region", "india") == "india"})
    acc_countries = len({c["state"] for c in acc_open if c.get("region") == "world"})

def ed_line(k):
    try:
        x = load(f"data/{k}.json")
        h = sorted(x["items"], key=lambda i: (not i.get("lead"), SEV[i["sev"]]))
        s = f'{h[0].get("short", h[0]["place"])}: {h[0]["headline"]}'
    except Exception:
        s = log[k]["summary"]
    return (f'<li><a href="archive/{k}.html"><b>{datetime.date.fromisoformat(k).strftime("%a %d %b")}</b></a>'
            f'<span class="t">{E(NAMES.get(log[k]["design"], log[k]["design"]))}</span><p>{E(s)}</p></li>')
past = "".join(ed_line(k) for k in sorted(log, reverse=True)[1:5])

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
.wrap{max-width:900px;margin:0 auto;padding:20px max(16px,env(safe-area-inset-left,0px)) 48px;display:grid;gap:26px}
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
.focs{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:8px}
.fcard{background:var(--paper);border:1px solid var(--rule);border-left:4px solid var(--accent);border-radius:6px;display:grid;grid-template-columns:84px minmax(0,1fr);overflow:hidden;text-decoration:none;color:inherit}
.fcard img{display:block;width:84px;height:100%;min-height:84px;object-fit:cover;background:var(--chip)}
.fcard div{padding:8px 12px;display:grid;gap:3px;align-content:center;min-width:0}
.fcard .k{font:500 10.5px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--accent);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fcard h3{font-size:21px;font-weight:800;text-wrap:balance}
.kf{font-size:13px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.kf b{font:800 17px var(--display);color:var(--red)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:8px}
.stat{background:var(--paper);border:1px solid var(--rule);border-top:5px solid var(--red);border-radius:6px;padding:12px 14px;display:grid;gap:2px;text-decoration:none;color:inherit;align-content:start}
.stat .k{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--accent)}
.stat b{font:800 52px/0.95 var(--display);color:var(--red)}
.stat span{font-size:14px}.stat .sub{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.past{list-style:none;margin:0;padding:0;display:grid;gap:0;background:var(--paper);border:1px solid var(--rule);border-radius:6px}
.past li{padding:8px 14px;border-top:1px solid var(--rule);display:flex;gap:10px;align-items:baseline;min-width:0}
.past li:first-child{border-top:0}
.past li a{white-space:nowrap;flex:none}
.past .t{display:none}
.past p{color:var(--muted);font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.how{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 14px}
.how summary{cursor:pointer;font-weight:600}
.how ul{margin:8px 0 0;padding-left:18px;display:grid;gap:4px;color:var(--muted);font-size:14px}
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
<p class="tag">Human rights in India and the world, daily. Non-partisan. Every fact sourced.</p>
<nav class="chips" aria-label="Follow Resistance Daily">{chips}</nav></header>

<section aria-labelledby="h-today"><div class="sec-h"><h2 id="h-today">Today</h2><a href="{full}">Full edition →</a></div>
<div class="today"><span class="when">{dt.strftime("%a %d %b %Y")} · {E(NAMES.get(log.get(date, {}).get("design", ""), ""))} · {len(d["items"])} stories</span><ul>{today}</ul>
<a class="go" href="{full}">Read today's edition →</a></div></section>

<section aria-labelledby="h-focus"><div class="sec-h"><h2 id="h-focus">In focus</h2><a href="focus/">All {len(focus)} →</a></div>
<div class="focs">{cards}</div></section>

<section aria-labelledby="h-track"><div class="sec-h"><h2 id="h-track">Tracking</h2></div><div class="stats">
<a class="stat" href="{f'archive/{tracker}.html#still-waiting' if tracker else 'archive/'}"><span class="k">Still waiting</span><b>{len(cs)}</b><span>people and groups held after speaking out</span><span class="sub">Longest: {ldays:,} days, {E(longest["name"])}</span></a>
{f'''<a class="stat" href="accountability/"><span class="k">Accountability Watch</span><b>{len(acc_open)}</b><span>abuse-of-power cases in {acc_states} states{f" and {acc_countries} countries" if acc_countries else ""}</span><span class="sub">{acc_noarrest} with no arrest reported</span></a>''' if acc else ""}
</div></section>

<section aria-labelledby="h-past"><div class="sec-h"><h2 id="h-past">Past editions</h2><a href="archive/">All →</a></div>
<ul class="past">{past}</ul></section>

<details class="how"><summary>How we report</summary><ul>
<li>Rights, not parties: life and safety, assembly, expression, press freedom, due process, land and livelihood.</li>
<li>Every number links to its source, with ground-level reporting first.</li>
<li>The official position sits next to every allegation; when sources disagree we show the range.</li>
<li>Photos are freely licensed and credited; protesters' and children's faces are blurred.</li></ul></details>

<footer><span>Tips, photos or corrections: <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a></span>
<span>{seo.FOLLOW}</span></footer>
</div></body></html>
"""
open(os.path.join(root, out), "w").write(page)
print("built home", out, date)
