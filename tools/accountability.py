#!/usr/bin/env python3
"""Build the Accountability Watch page: abuse of power by those with a uniform, an office, money or social dominance,
and what happens next. Each case is followed to its outcome (complaint -> arrest -> chargesheet -> verdict).

Usage (from the repo root):  python3 tools/accountability.py [YYYY-MM-DD]   (date for "days since"; default: today, IST)
Reads data/accountability.json, writes accountability/index.html, rebuilds sitemap.xml/robots.txt and the home page.

data/accountability.json:
{ "updated": "YYYY-MM-DD",
  "figures": [{"fig", "cap", "src": [name, url]}],                    # 2-4 national anchor numbers
  "states": {"State": {"cm", "party", "src": [name, url]}},             # who governs each state with a case (balance log)
  "cases": [{
     "id", "kind": "Custody"|"Caste"|"Political power"|"RTI & whistleblowers"|"Workers"|"Land",
     "state", "place", "date": "YYYY-MM-DD" (the incident), "power": who held power, by ROLE (e.g. "Police"),
     "head" (<= 9 words, neutral), "text" (2 sentences: what is alleged, by whom), "official" (police/official version,
     or that none was reported), "steps": [{"step", "status": "done"|"unknown"|"open", "date"?, "note"?}],
     "src": [[name, url], ...], "checked": "YYYY-MM-DD" (last source check), "closed"?: "outcome text" }] }

Rules (see ROUTINE.md, ACCOUNTABILITY WATCH): a clear power gap; a named source AND an official step; the accused by role
unless police or a court have named them; never identify sexual-assault survivors or child victims; no photos of bodies.
"""
import sys, os, json, html, datetime, subprocess
import seo

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = seo.SITE
data = json.load(open(os.path.join(root, "data", "accountability.json")))
ist = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else ist.date()
fmt = lambda d: datetime.date.fromisoformat(d).strftime("%d %b %Y")
cases = data["cases"]
open_cases = [c for c in cases if not c.get("closed")]
states = data.get("states", {})


def next_check(c):
    d = datetime.date.fromisoformat(c["date"])
    for n in (30, 90, 180):
        if d + datetime.timedelta(days=n) > today:
            return d + datetime.timedelta(days=n)
    return today + datetime.timedelta(days=30)


def card(c):
    days = (today - datetime.date.fromisoformat(c["date"])).days
    arrested = any(s["step"].lower().startswith("arrest") and s["status"] == "done" for s in c["steps"])
    st = states.get(c["state"])
    gov = f' · Governed by {E(st["party"])}' if st else ""
    steps = "".join(
        f'<li class="{E(s["status"])}"><b>{E(s["step"])}</b>'
        + (f'<small>{fmt(s["date"])}</small>' if s.get("date") else "")
        + (f'<small>{E(s["note"])}</small>' if s.get("note") else "")
        + (f'<small>not reported</small>' if s["status"] == "unknown" and not s.get("note") else "") + "</li>"
        for s in c["steps"])
    if c.get("closed"):
        line = f'<p class="outcome">Outcome: {E(c["closed"])}</p>'
    elif arrested:
        line = f'<p class="ok">{days} days since the incident</p>'
    else:
        line = f'<p class="stall">{days} days since the incident · no arrest reported</p>'
    src = " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in c["src"])
    return (f'<article class="case" id="{E(c["id"])}" data-k="{E(c["kind"])}"><div class="top"><span class="chip">{E(c["kind"])}</span>'
            f'<span class="pw">Power: {E(c["power"])}</span></div><h3>{E(c["head"])}</h3>'
            f'<p class="where">{E(c["place"])} · {fmt(c["date"])}{gov}</p><p>{E(c["text"])}</p>'
            f'<p class="off"><b>Official version:</b> {E(c["official"])}</p><ol class="steps" aria-label="Case progress">{steps}</ol>{line}'
            f'<p class="src">Sources: {src} · Last checked {fmt(c["checked"])}'
            + ("" if c.get("closed") else f' · Next check {next_check(c).strftime("%d %b")}') + '</p></article>')


kinds = ["All"] + sorted({c["kind"] for c in cases})
case_states = sorted({c["state"] for c in open_cases})
parties = {}
for s in case_states:
    if s in states:
        parties.setdefault(states[s]["party"], []).append(s)
bal = "; ".join(f'{E(p)}: {", ".join(E(x) for x in v)}' for p, v in sorted(parties.items(), key=lambda kv: -len(kv[1])))
gov_src = " · ".join(f'<a href="{E(states[s]["src"][1])}">{E(s)}</a>' for s in case_states if s in states)
figs = "".join(f'<div class="fig"><b>{E(f["fig"])}</b><span>{E(f["cap"])}</span><a href="{E(f["src"][1])}">{E(f["src"][0])}</a></div>'
               for f in data.get("figures", []))
ordered = sorted(open_cases, key=lambda c: c["date"], reverse=True) + [c for c in cases if c.get("closed")]
title = "Accountability Watch: abuse of power in India, tracked to the outcome"
desc = (f"{len(open_cases)} open cases from {len(case_states)} states: custodial deaths, caste violence, attacks on RTI activists "
        "and abuse by the powerful, each followed from complaint to arrest, chargesheet and verdict. Non-partisan, every fact sourced.")
url = SITE + "accountability/"
ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url,
      "dateModified": data["updated"], "publisher": {"@type": "NewsMediaOrganization", "name": "Resistance Daily", "url": SITE}}

CSS = """
:root{--bg:#f3f4f2;--paper:#fff;--ink:#15181d;--muted:#5b616b;--rule:#d9dcd8;--accent:#d9661a;--red:#b3261e;--green:#1d7a4c;--chip:#eceee9;
--display:"Barlow Condensed","Arial Narrow",Arial,sans-serif;--body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;--red:#ef6b62;--green:#3fb07a;--chip:#22262c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;--red:#ef6b62;--green:#3fb07a;--chip:#22262c;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--body)}
.wrap{max-width:900px;margin:0 auto;padding:20px max(16px,env(safe-area-inset-left,0px)) 48px;display:grid;gap:22px}
a{color:inherit;text-decoration-color:var(--accent);text-underline-offset:2px}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3{font-family:var(--display);text-transform:uppercase;margin:0;line-height:.95}
p{margin:0}
.top-nav{display:flex;justify-content:space-between;gap:12px;font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;border-bottom:3px solid var(--ink);padding-bottom:10px}
.top-nav b{font-weight:500}
.k{font:500 12px var(--mono);color:var(--accent);text-transform:uppercase;letter-spacing:.07em}
h1{font-size:clamp(40px,8vw,60px);font-weight:800;margin-top:6px}
.lede{color:var(--muted);max-width:66ch;margin-top:8px;font-size:16px}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.fig{background:var(--paper);border:1px solid var(--rule);border-top:5px solid var(--red);border-radius:6px;padding:12px 14px;display:grid;gap:4px;align-content:start}
.fig b{font:800 40px/1 var(--display);color:var(--red)}
.fig span{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.fig a{font-size:12px;color:var(--muted)}
.bal{background:var(--paper);border:1px solid var(--rule);border-left:5px solid var(--ink);border-radius:6px;padding:10px 14px;font-size:14px;display:grid;gap:4px}
.bal small{color:var(--muted);font-size:12px}
.filters{display:flex;flex-wrap:wrap;gap:6px}
.filters button{font:600 13px var(--body);border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:999px;padding:6px 12px;cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.cases{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:12px}
.case{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:14px;display:grid;gap:8px;align-content:start;min-width:0;scroll-margin-top:16px}
.case .top{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.chip{font:600 10.5px var(--mono);text-transform:uppercase;padding:4px 8px;border-radius:999px;background:var(--chip)}
.pw{font:500 11px var(--mono);color:var(--muted);text-transform:uppercase}
.case h3{font-size:26px;font-weight:800;text-wrap:balance}
.where{font:500 12px var(--mono);color:var(--muted)}
.off{font-size:14px;color:var(--muted)}.off b{color:var(--ink);font-weight:600}
.steps{list-style:none;margin:4px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr));gap:6px}
.steps li{border-top:5px solid var(--rule);padding-top:5px;font-size:12px;color:var(--muted);min-width:0}
.steps li b{display:block;color:var(--ink);font-weight:600}
.steps li.done{border-color:var(--green)}.steps li.done b:before{content:"\\2713  ";color:var(--green)}
.steps li.unknown{border-color:var(--accent);border-top-style:dashed}.steps li.unknown b:before{content:"? ";color:var(--accent)}
.steps small{display:block}
.stall{font:600 13px var(--mono);color:var(--red)}.ok{font:600 13px var(--mono);color:var(--muted)}.outcome{font-weight:600}
.src{font-size:12px;color:var(--muted)}
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
<nav class="top-nav"><a href="../"><b>Resistance Daily</b></a><span><a href="../focus/">Focus</a> · <a href="../archive/">Past editions</a></span></nav>
<header><span class="k">Accountability Watch</span><h1>The weak against the powerful</h1>
<p class="lede">Abuse by those with a uniform, an office, money or social dominance, and what happens next. We judge each case by the act and the imbalance of power, not by who governs the state, and we follow every case to its outcome.</p></header>
<section class="figs" aria-label="Key figures">{figs}</section>
<div class="bal"><span><b>Balance:</b> {len(open_cases)} open cases from {len(case_states)} states. {bal}.</span>
<small>We log which party governs each state with a case and say openly when coverage is uneven. Who governs: {gov_src}. Updated {fmt(data["updated"])}.</small></div>
<div class="filters" role="group" aria-label="Filter cases by type">{"".join(f'<button type="button" aria-pressed="{str(k == "All").lower()}" data-k="{E(k)}">{E(k)}</button>' for k in kinds)}</div>
<section class="cases" aria-label="Cases">{"".join(card(c) for c in ordered)}</section>
<details><summary>How cases are chosen</summary><ul>
<li>A clear power gap: police or officials, elected leaders and their supporters, employers, landlords, or a dominant group over a weaker one.</li>
<li>A named source and an official step (an FIR, a suspension or a court notice). No bare accusations.</li>
<li>The accused are described by role, and named only once police or a court have named them. The police or official version sits beside every allegation.</li>
<li>Sexual-assault survivors and child victims are never identifiable. No photos of bodies.</li>
<li>Every case is re-checked 30, 90 and 180 days after the incident. If nothing is reported, we say so, with the date.</li>
<li>Days are counted from the incident to {today.strftime("%d %b %Y")}.</li></ul></details>
<footer><span>Know of a case, an update or a correction? Write to <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a>.</span><span>{seo.FOLLOW}</span></footer>
</div>
<script>
document.querySelectorAll('.filters button').forEach(function(b){{b.addEventListener('click',function(){{
document.querySelectorAll('.filters button').forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});
document.querySelectorAll('.case').forEach(function(c){{c.hidden=!(b.dataset.k==='All'||c.dataset.k===b.dataset.k)}});}})}});
</script></body></html>
"""
os.makedirs(os.path.join(root, "accountability"), exist_ok=True)
open(os.path.join(root, "accountability", "index.html"), "w").write(page)
seo.write_sitemap(root)
# The home page shows the open-case count: rebuild it too.
subprocess.run([sys.executable, os.path.join(root, "tools", "home.py"), "index.html"], check=True)
print(f"built accountability/index.html: {len(open_cases)} open cases, {len(case_states)} states")
