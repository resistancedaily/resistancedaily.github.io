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
     "id", "region": "india" (default) | "world" (then "state" is the country), "kind": "Custody"|"Police force"|"Caste"|"Political power"|"RTI & whistleblowers"|"Workers"|"Land",
     "state", "place", "date": "YYYY-MM-DD" (the incident), "power": who held power, by ROLE (e.g. "Police"),
     "head" (<= 9 words, neutral), "text" (2 sentences: what is alleged, by whom), "official" (police/official version,
     or that none was reported), "steps": [{"step", "status": "done"|"unknown"|"open", "date"?, "note"?}],
     "src": [[name, url], ...], "checked": "YYYY-MM-DD" (last source check), "closed"?: "outcome text" }] }

Rules (see ROUTINE.md, ACCOUNTABILITY WATCH): a clear power gap; a named source AND an official step; the accused by role
unless police or a court have named them; never identify sexual-assault survivors or child victims; no photos of bodies.
"""
import sys, os, json, html, datetime, subprocess
import seo
import rdsite as S

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


def no_arrest(c):
    return (any(x["step"].lower().startswith("arrest") for x in c["steps"])
            and not any(x["step"].lower().startswith("arrest") and x["status"] == "done" for x in c["steps"]))


def card(c):
    """Threads redesign (Nov 2026): place and state, headline, a step track of pills, days since the incident; the story,
    the official version and the sources sit under "Details"."""
    days = (today - datetime.date.fromisoformat(c["date"])).days
    dl = f'{days:,} day{"s" if days != 1 else ""}'
    st = states.get(c["state"])
    pill = {"done": ("tag tag-accent-2", "✓ "), "unknown": ("tag tag-outline", "? "), "open": ("tag tag-neutral", "")}
    track = "".join(f'<li><span class="{pill.get(x["status"], pill["open"])[0]}">{pill.get(x["status"], pill["open"])[1]}{E(x["step"])}</span></li>' for x in c["steps"])
    if c.get("closed"):
        line = "Closed: outcome reached"
    elif no_arrest(c):
        line = f"{dl} since the incident · no arrest reported"
    else:
        line = f"{dl} since the incident"
    notes = "".join(
        f'<li><b>{E(x["step"])}:</b> ' + {"done": "done", "unknown": "not reported", "open": "not yet"}.get(x["status"], x["status"])
        + (f', {fmt(x["date"])}' if x.get("date") else "") + (f' ({E(x["note"])})' if x.get("note") else "") + "</li>"
        for x in c["steps"])
    src = " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in c["src"])
    gov = f' Governed by {E(st["party"])}.' if st else ""
    outcome = f'<p class="outcome">Outcome: {E(c["closed"])}</p>' if c.get("closed") else ""
    nxt = "" if c.get("closed") else f' · Next check {next_check(c).strftime("%d %b")}'
    return (f'<article class="acase" id="{E(c["id"])}" data-k="{E(c["kind"])}" data-r="{E(c.get("region", "india"))}">'
            f'<div class="rd-row" style="gap:8px"><span class="aw">{E(c["place"].split(",")[-2].strip() if c["place"].count(",") >= 2 else c["place"].split(",")[0])} · {E(c["state"])}</span>'
            f'<span class="tag tag-neutral">{E(c["kind"])}</span></div>'
            f'<h3>{E(c["head"])}</h3><ol class="track" aria-label="Case progress">{track}</ol>'
            f'<p class="days">{line}</p>{outcome}'
            f'<details><summary>Details</summary><p>{E(c["text"])}</p>'
            f'<p class="off"><b>Official version:</b> {E(c["official"])}</p><ul class="notes">{notes}</ul>'
            f'<p class="src">{E(c["place"])}. Power: {E(c["power"])}.{gov}<br>Sources: {src} · Last checked {fmt(c["checked"])}{nxt}</p></details></article>')


kinds = ["All"] + sorted({c["kind"] for c in cases})
region = lambda c: c.get("region", "india")
case_states = sorted({c["state"] for c in open_cases if region(c) == "india"})
world_open = [c for c in open_cases if region(c) == "world"]
countries = sorted({c["state"] for c in world_open})
parties = {}
for s in case_states:
    if s in states:
        parties.setdefault(states[s]["party"], []).append(s)
bal = "; ".join(f'{E(p)}: {", ".join(E(x) for x in v)}' for p, v in sorted(parties.items(), key=lambda kv: -len(kv[1])))
gov_src = " · ".join(f'<a href="{E(states[s]["src"][1])}">{E(s)}</a>' for s in case_states if s in states)
figs = "".join(f'<div class="fig"><b>{E(f["fig"])}</b><span>{E(f["cap"])}</span><a href="{E(f["src"][1])}">{E(f["src"][0])}</a></div>'
               for f in data.get("figures", []))
noarrest = sum(1 for c in open_cases if any(x["step"].lower().startswith("arrest") for x in c["steps"])
               and not any(x["step"].lower().startswith("arrest") and x["status"] == "done" for x in c["steps"]))
# Open cases first, those longest without an arrest at the top; then other open cases by age; closed last.
ordered = (sorted([c for c in open_cases if no_arrest(c)], key=lambda c: c["date"])
           + sorted([c for c in open_cases if not no_arrest(c)], key=lambda c: c["date"])
           + [c for c in cases if c.get("closed")])
title = "Accountability Watch: abuse of power in India and worldwide, tracked to the outcome"
desc = (f"{len(open_cases)} open cases from {len(case_states)} Indian states and {len(countries)} other countries: custodial deaths, caste violence, attacks on RTI activists "
        "and abuse by the powerful, each followed from complaint to arrest, chargesheet and verdict. Non-partisan, every fact sourced.")
url = SITE + "accountability/"
ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url,
      "dateModified": data["updated"], "publisher": {"@type": "NewsMediaOrganization", "name": "Resistance Daily", "url": SITE}}

CSS = """
.ahero{display:flex;flex-direction:column;gap:8px}
.ahero h1{font-size:44px;margin:6px 0 2px}
.ahero .rd-stat{margin:0 0 10px}
.filters{display:flex;gap:8px;flex-wrap:wrap}
.filters button{font:600 13px var(--font-body);padding:8px 14px;border-radius:999px;background:var(--color-neutral-100);color:var(--color-text);border:0;cursor:pointer}
.filters button[aria-pressed="true"]{background:var(--color-text);color:var(--color-bg)}
.acases{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,460px),1fr));gap:16px}
.acase{background:var(--color-surface);border-radius:28px;padding:20px 22px;display:flex;flex-direction:column;gap:10px;scroll-margin-top:16px}
.acase[hidden]{display:none}
.acase h3{font-size:20px;line-height:1.2;margin:0}
.aw{font-size:13px;color:var(--color-neutral-700)}
.track{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.days{margin:0;font-size:14px;font-weight:600}
.outcome{margin:0;font-weight:600}
.acase details summary{font-weight:600;font-size:14px;color:var(--color-accent-700)}
.acase details p,.acase details ul{font-size:14px;margin:8px 0 0}
.acase .src{font-size:12.5px;color:var(--color-neutral-700)}
.afigs{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-top:12px}
.afigs .fig{background:var(--color-neutral-100);border-radius:22px;padding:14px 16px;display:flex;flex-direction:column;gap:4px}
.afigs .fig b{font:400 30px/1 var(--font-heading)}.afigs .fig span{font-size:13px}.afigs .fig a{font-size:12px}
@media (max-width:720px){.ahero h1{font-size:30px}}
"""
extra = (f'<meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary">'
         + seo.jsonld(ld))
page = (S.head(f"{title} · Resistance Daily", desc, "../", url, extra, css=CSS) + S.nav("../") + f"""
<header class="ahero"><span class="rd-kicker">Thread</span><h1>Accountability Watch</h1>
<p class="rd-stat">{len(open_cases)} cases followed · {noarrest} with no arrest. Abuse by police, officials and the powerful, followed until there is an outcome.</p>
<div class="rd-row"><button class="btn btn-primary" data-rd-follow="accountability">Follow this thread</button><a class="rd-more" href="../threads/accountability.html">Daily updates →</a></div></header>
<div class="filters" role="group" aria-label="Filter cases by region">{"".join(f'<button type="button" class="fr" aria-pressed="{str(k == "All").lower()}" data-r="{E(k.lower())}">{E(k)}</button>' for k in ["All", "India", "World"])}</div>
<div class="filters ks" role="group" aria-label="Filter cases by type">{"".join(f'<button type="button" class="fk" aria-pressed="{str(k == "All").lower()}" data-k="{E(k)}">{E(k)}</button>' for k in kinds)}</div>
<section class="acases" aria-label="Cases">{"".join(card(c) for c in ordered)}</section>
<details class="rd-how"><summary>The bigger picture</summary><div class="afigs">{figs}</div></details>
<details class="rd-how"><summary>Balance: where our cases are</summary><p style="font-size:14px;margin-top:10px">India: {len(open_cases) - len(world_open)} open cases in {len(case_states)} states. {bal}.{f" World: {len(world_open)} in {', '.join(E(x) for x in countries)}." if world_open else ""}</p>
<p style="font-size:13px;color:var(--color-neutral-700)">We log which party governs each state with a case and say openly when coverage is uneven. Who governs: {gov_src}. Updated {fmt(data["updated"])}.</p></details>
<details class="rd-how"><summary>How cases are chosen</summary><ul>
<li>A clear power gap: police or officials, elected leaders and their supporters, employers, landlords, or a dominant group over a weaker one.</li>
<li>A named source and an official step (an FIR, a suspension or a court notice). No bare accusations.</li>
<li>Outside India, only cases where an accountability process (a charge, a prosecution, an inquiry) is reported and can be followed; at most about a third of open cases.</li>
<li>The accused are described by role, and named only once police or a court have named them. The police or official version sits beside every allegation.</li>
<li>Sexual-assault survivors and child victims are never identifiable. No photos of bodies.</li>
<li>Every case is re-checked 30, 90 and 180 days after the incident. If nothing is reported, we say so, with the date.</li>
<li>Days are counted from the incident to {today.strftime("%d %b %Y")}. Step track: ✓ done · ? not reported · plain: not reached yet.</li></ul></details>
<p class="rd-src">Know of a case, an update or a correction? Write to <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a>.</p>
<script>
(function(){{var r='all',k='All';
function apply(){{document.querySelectorAll('.acase').forEach(function(c){{c.hidden=!((r==='all'||c.dataset.r===r)&&(k==='All'||c.dataset.k===k))}})}}
function wire(sel,set){{document.querySelectorAll(sel).forEach(function(b){{b.addEventListener('click',function(){{
document.querySelectorAll(sel).forEach(function(x){{x.setAttribute('aria-pressed',x===b)}});set(b);apply();}})}})}}
wire('.fr',function(b){{r=b.dataset.r}});wire('.fk',function(b){{k=b.dataset.k}});}})();
</script>""" + S.footer("../"))
os.makedirs(os.path.join(root, "accountability"), exist_ok=True)
open(os.path.join(root, "accountability", "index.html"), "w").write(page)
seo.write_sitemap(root)
# The home page shows the open-case count: rebuild it too.
subprocess.run([sys.executable, os.path.join(root, "tools", "home.py"), "index.html"], check=True)
print(f"built accountability/index.html: {len(open_cases)} open cases, {len(case_states)} states, {len(countries)} countries")
