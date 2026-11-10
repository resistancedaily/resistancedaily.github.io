#!/usr/bin/env python3
"""Build the PREVIEW copy of the proposed inclusion and reach features (owner's request, 10 Nov 2026).

Usage (from the repo root):  python3 tools/preview.py [YYYY-MM-DD]     (default: the latest edition)
Writes everything under preview/ (every page is noindex and nothing on the live site links to it):
  preview/index.html             what is in the preview
  preview/en|hi|kn/index.html    the day's stories in English, Hindi and Kannada, with a "Listen" button
                                 (translations: data/i18n/DATE.LANG.json, {"items": {"N": [place, headline, text]}})
  preview/places/                one page per Indian state and per country, built from every edition
  preview/people/                one page per group of people (workers, women, students ...)
  preview/coverage/              the last 7 editions against the weekly coverage floor, and each outlet's share
  preview/report/                "Report something": safety guidance and a form that opens the reader's email app
  preview/corrections/           public corrections log (data/corrections.json)
  preview/about/                 who runs this, how it is made, how it is paid for
  preview/feed.xml               RSS feed, one entry per edition
  preview/ROUTINE-additions.md   is written by hand, not by this tool

Groups: an item belongs to a group when it carries it in "groups": [...]; older items have no such field, so until the
routine tags them the tool falls back to keywords in the headline and text (GROUPS below). That fallback is a guess.
"""
import sys, os, re, json, html, glob, datetime, collections, email.utils
import rdsite as S

E = html.escape
root = S.root
OUT = os.path.join(root, "preview")
DATE = sys.argv[1] if len(sys.argv) > 1 else S.editions()[-1]
LANGS = [("en", "English"), ("hi", "हिन्दी"), ("kn", "ಕನ್ನಡ")]
SPEECH = {"en": "en-IN", "hi": "hi-IN", "kn": "kn-IN"}
NOTO = {"hi": "Noto+Sans+Devanagari:wght@400;600;800", "kn": "Noto+Sans+Kannada:wght@400;600;800"}

GROUPS = [  # slug, name, keywords (fallback only)
    ("workers", "Workers", r"\bworkers?\b|labou?r|wages?\b|\bstrike\b|trade union|\bminers?\b|factory"),
    ("women", "Women and girls", r"\bwom[ae]n\b|\bgirls?\b|widow|gender"),
    ("dalit-adivasi", "Dalit and Adivasi communities", r"dalit|adivasi|tribal|\bcaste\b|indigenous|scheduled (caste|tribe)"),
    ("religious-minorities", "Religious minorities", r"muslim|christian|church|mosque|\bsikh|communal|conversion|cleric"),
    ("students", "Students and young people", r"students?\b|universit|campus|\byouths?\b"),
    ("migrants", "Migrants and displaced people", r"migrants?\b|refugees?\b|displaced|asylum"),
    ("journalists", "Journalists", r"journalists?\b|newspaper|\breporters?\b|\beditor\b|press freedom"),
    ("farmers-land", "Farmers and people losing land or homes", r"farmers?\b|\bland\b|evict|demoli|\bforest|\bdam\b|homeless"),
    ("children", "Children", r"\bchild(ren)?\b|\bminors?\b|\bboys?\b"),
    ("disability", "People with disabilities", r"disab"),
    ("prisoners", "People in detention", r"detain|detention|\bjail|prison|custod|undertrial|\bbail\b"),
]
# The weekly floor (see preview/ROUTINE-additions.md): each week must include at least one item on each of these.
FLOOR_GROUPS = ["workers", "women", "dalit-adivasi", "disability", "children"]
FLOOR_RIGHTS = [("Health", r"health|hospital|medic"), ("Education", r"educat|school")]
FLOOR_STATES = 5        # Indian states other than Delhi and the Northeast
NORTHEAST = {"Manipur", "Arunachal Pradesh", "Assam", "Nagaland", "Mizoram", "Tripura", "Meghalaya", "Sikkim"}
SHARE_CAP = 15          # % of a week's source links that one outlet may hold

STATE_FIX = {"New Delhi": "Delhi", "Old Delhi": "Delhi", "Bengaluru": "Karnataka", "Mumbai": "Maharashtra",
             "Arunachal": "Arunachal Pradesh", "north Bengal": "West Bengal", "Kashmir": "Jammu and Kashmir"}


def place_of(it):
    """State (India) or country (world) for an item, from the last part of "place"."""
    last = re.split(r"[,;]", it.get("place", ""))[-1].strip()
    if it.get("region") == "india":
        last = STATE_FIX.get(last, last)
        return last if last and " and across " not in last else STATE_FIX.get(last.split(" and ")[0], last)
    p = it.get("place", "")
    for key, name in (("Gaza", "Gaza and the West Bank"), ("West Bank", "Gaza and the West Bank"), ("DR Congo", "DR Congo"),
                      ("France", "France"), ("French", "France"), ("Abyei", "Sudan"), ("Sudan", "Sudan"),
                      ("Yemen", "Yemen"), ("Australia", "Australia"), ("Kenya", "Kenya")):
        if key in p:
            return name
    return re.sub(r"^(Across|Eastern|Off)\s+", "", last)


def groups_of(it):
    if it.get("groups"):
        return list(it["groups"])
    t = (it.get("headline", "") + " " + it.get("text", "")).lower()
    return [g for g, _, rx in GROUPS if re.search(rx, t)]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def all_items():
    out = []
    for d in S.editions():
        for it in S.load(f"data/{d}.json").get("items", []):
            out.append((d, it))
    return out


def outlet(name):
    return re.sub(r"\s*\(.*|^(AP|Reuters|AFP|PTI) via .*", "", name).strip() or name


# ── page frame ────────────────────────────────────────────────────────────────────────────────────────────────────
BANNER = ('<p class="pv-ban"><b>Preview.</b> A copy of proposed changes; nothing on the live site links here. '
          '<a href="{p}preview/">What is in this preview →</a></p>')
CSS = """
.pv-ban{background:var(--color-accent-100);color:var(--color-accent-800);border-radius:18px;padding:10px 16px;margin:0;font-size:14px}
.pv-ban a{color:inherit}
.pv-h1{font-size:44px;line-height:1.05;margin:6px 0 4px}
.pv-lead{font-size:16px;color:var(--color-neutral-800);margin:0;max-width:60ch}
.pv-pills{display:flex;flex-wrap:wrap;gap:8px}
.pv-pills a,.pv-pills button{font:600 14px var(--font-body);border:1px solid var(--color-divider);background:transparent;color:var(--color-text);
  border-radius:999px;padding:9px 16px;text-decoration:none;cursor:pointer;min-height:40px;display:inline-flex;align-items:center;gap:6px}
.pv-pills a[aria-current]{background:var(--color-text);color:var(--color-bg);border-color:transparent}
.pv-pills button{background:#b2622d;color:#fff;border-color:transparent}
.pv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
.pv-card{background:var(--color-neutral-100);border-radius:22px;padding:16px 18px;text-decoration:none;color:var(--color-text);display:flex;flex-direction:column;gap:4px}
a.pv-card:hover{background:var(--color-neutral-300)}
.pv-card b{font-family:var(--font-heading);font-weight:400;font-size:19px;line-height:1.2}
.pv-card span{font-size:13.5px;color:var(--color-neutral-700)}
.pv-card .n{font-family:var(--font-heading);font-size:30px;line-height:1;color:var(--color-accent-700)}
.pv-box{background:var(--color-surface);border-radius:28px;padding:20px 24px}
.pv-box h2{font-size:22px;margin:0 0 8px}
.pv-box p,.pv-box li{font-size:15px}
.pv-box ul{margin:0;padding-left:20px;display:grid;gap:6px}
.pv-todo{background:var(--color-accent-100);color:var(--color-accent-800);border-radius:8px;padding:1px 6px;font-weight:600}
.pv-row{display:grid;grid-template-columns:86px 1fr;gap:14px;padding:12px 0;border-top:1px solid var(--color-divider);font-size:15px}
.pv-row time{font-size:13px;color:var(--color-neutral-700);padding-top:2px}
.pv-row h3{font-family:var(--font-body);font-weight:600;font-size:15.5px;letter-spacing:0;margin:0 0 4px}
.pv-row p{margin:0 0 4px}
.pv-tbl{width:100%;border-collapse:collapse;font-size:15px}
.pv-tbl td,.pv-tbl th{padding:9px 8px;border-top:1px solid var(--color-divider);text-align:left;vertical-align:top}
.pv-tbl th{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--color-neutral-700);border-top:0}
.pv-ok{color:var(--color-accent-2-700);font-weight:700;white-space:nowrap}.pv-miss{color:var(--color-accent-700);font-weight:700;white-space:nowrap}
.pv-bar{display:inline-block;height:10px;border-radius:999px;background:var(--color-neutral-500);vertical-align:middle;margin-right:8px}
.pv-bar.over{background:var(--color-accent)}
.pv-form{display:grid;gap:14px;max-width:640px}
.pv-form label{display:grid;gap:5px;font-size:14px;font-weight:600}
.pv-form .hint{font-weight:400;color:var(--color-neutral-700);font-size:13px}
.pv-form .input{border-radius:16px}
.pv-form textarea.input{border-radius:16px}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .pv-ok{color:#ccdbb2}}
:root[data-theme="dark"] .pv-ok{color:#ccdbb2}
@media (max-width:720px){.pv-grid{grid-template-columns:1fr 1fr;gap:10px}.pv-card{padding:14px}.pv-card b{font-size:16px}.pv-h1{font-size:30px}.pv-row{grid-template-columns:1fr;gap:2px}.pv-box{padding:16px 18px}
  .pv-tbl{font-size:14px}.pv-tbl td,.pv-tbl th{padding:8px 4px}}
"""


def page(path, title, desc, body, lang="en", extra_css=""):
    depth = path.count("/") + 1
    p = "../" * depth
    h = S.head(f"{title} · Resistance Daily (preview)", desc, p, S.SITE + "preview/" + path.replace("index.html", ""),
               noindex=True, css=CSS + extra_css)
    if lang != "en":
        h = h.replace('<html lang="en">', f'<html lang="{lang}">').replace(
            '<link rel="stylesheet"', f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={NOTO[lang]}&display=swap"><link rel="stylesheet"', 1)
    out = h + S.nav(p) + BANNER.format(p=p) + body + S.footer(p)
    f = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w").write(out)
    return f


def row(date, it, p):
    link = f'{p}stories/{date}.html#i{it["n"]}' if os.path.exists(os.path.join(root, "stories", f"{date}.html")) else f'{p}archive/{date}.html'
    tag = '<span class="tag tag-accent-2">Right upheld</span> ' if it.get("upheld") else ""
    return (f'<div class="pv-row"><time datetime="{date}">{S.nice(date, "%d %b %Y")}</time><div><h3>{tag}<a href="{link}" style="color:inherit">{E(it["headline"])}</a></h3>'
            f'<p>{E(it["text"])}</p><span class="rd-src">{E(it["place"])} · {S.src_links(it.get("src", []))}</span></div></div>')


# ── 1. language editions + listen ────────────────────────────────────────────────────────────────────────────────
LISTEN_JS = """<script>
(function(){var b=document.querySelector('[data-listen]');if(!b)return;
if(!('speechSynthesis' in window)){b.hidden=true;return;}
var on=false,L=b.dataset.lang;
function stop(){speechSynthesis.cancel();on=false;b.textContent='▶ '+b.dataset.listen;}
b.addEventListener('click',function(){if(on)return stop();
 var parts=[].slice.call(document.querySelectorAll('[data-say]')).map(function(e){return e.textContent.trim();});
 on=true;b.textContent='■ '+b.dataset.stop;
 parts.forEach(function(t,i){var u=new SpeechSynthesisUtterance(t);u.lang=L;u.rate=.92;
  if(i===parts.length-1)u.onend=stop;speechSynthesis.speak(u);});});
window.addEventListener('pagehide',stop);})();
</script>"""


def edition(lang):
    d = S.load(f"data/{DATE}.json")
    tr = S.load(f"data/i18n/{DATE}.{lang}.json") if lang != "en" else None
    t = lambda k, en: tr[k] if tr else en
    p = "../../"
    pills = "".join(f'<a href="../{c}/" lang="{c}"{" aria-current=page" if c == lang else ""}>{n}</a>' for c, n in LANGS)
    arts = []
    for it in d["items"]:
        place, head, text = tr["items"][str(it["n"])] if tr else (it["place"], it["headline"], it["text"])
        ph = it.get("photo")
        fig = ""
        if ph:
            label = f'{t("file", "File photo")} · {ph.get("year", "")}' if ph.get("kind") != "event" else t("photo", "Photo from the event")
            fig = (f'<figure><img class="washed" src="{p}{ph["src"]}" alt="{E(ph["alt"]) if not tr else ""}" loading="lazy" decoding="async">'
                   f'<figcaption><b>{E(label)}</b> · <a href="{E(ph["page"])}">{E(ph["credit"])}</a>, <a href="{E(ph["licence_url"])}">{E(ph["licence"])}</a></figcaption></figure>')
        tag = f'<span class="tag tag-accent-2">{E(t("upheld", "Right upheld"))}</span>' if it.get("upheld") else ""
        arts.append(f'<article class="rd-story{"" if ph else " nophoto"}" id="i{it["n"]}">{fig}<div><div class="rd-meta">{tag}<span>{E(place)}</span></div>'
                    f'<h3 data-say>{E(head)}</h3><p data-say>{E(text)}</p><span class="rd-src">{E(t("source", "Source"))}: {S.src_links(it["src"])}</span></div></article>')
    note = f'<p class="pv-lead" style="font-size:14px">{E(tr["note"])}</p>' if tr else ""
    body = f"""<header><span class="rd-kicker">{E(t("date", d["date_long"]))}</span><h1 class="pv-h1">{E(t("title", "Where things stand today"))}</h1>
<p class="pv-lead">{E(t("tagline", "Human rights in India and the world. Non-partisan. Every fact sourced."))}</p></header>
<div class="pv-pills">{pills}<button type="button" data-listen="{E(t("listen", "Listen"))}" data-stop="{E(t("stop", "Stop"))}" data-lang="{SPEECH[lang]}">▶ {E(t("listen", "Listen"))}</button></div>{note}
<section class="rd-stories rd-stories-page">{"".join(arts)}</section>{LISTEN_JS}"""
    fam = {"hi": "'Noto Sans Devanagari'", "kn": "'Noto Sans Kannada'"}.get(lang)
    css = (f":root{{--font-heading:{fam},system-ui,sans-serif;--font-heading-weight:800;--font-body:{fam},system-ui,sans-serif}}"
           ".pv-h1,.rd-story h3{letter-spacing:0;line-height:1.3}.rd-brand{font-family:Caprasimo,system-ui,sans-serif;font-weight:400}") if fam else ""
    page(f"{lang}/index.html", t("title", "Where things stand today"), t("tagline", S.DESC), body, lang, css)


# ── 4. places and people ─────────────────────────────────────────────────────────────────────────────────────────
def listing(kind, key, name, rows, blurb):
    p = "../../"
    body = (f'<header><a class="rd-back" href="./">← All {kind}</a><h1 class="pv-h1">{E(name)}</h1><p class="pv-lead">{blurb}</p></header>'
            f'<section>{"".join(row(d, it, p) for d, it in sorted(rows, key=lambda r: r[0], reverse=True))}</section>')
    page(f"{kind}/{key}.html", name, f"Every Resistance Daily story about {name}.", body)


def index(kind, title, lead, groups):
    """groups: [(heading, [(key, name, n, latest date)])]"""
    secs = "".join(
        f'<section class="rd-sec"><h2 class="rd-h">{E(h)}</h2><div class="pv-grid">' + "".join(
            f'<a class="pv-card" href="{k}.html"><span class="n">{n}</span><b>{E(nm)}</b><span>latest {S.nice(last, "%d %b")}</span></a>'
            for k, nm, n, last in cards) + "</div></section>" for h, cards in groups if cards)
    page(f"{kind}/index.html", title, lead, f'<header><h1 class="pv-h1">{E(title)}</h1><p class="pv-lead">{lead}</p></header>{secs}')


def places(items):
    by = collections.defaultdict(list)
    for d, it in items:
        by[(it.get("region"), place_of(it))].append((d, it))
    cards = {"india": [], "world": []}
    for (reg, name), rows in by.items():
        if not name:
            continue
        listing("places", slug(name), name, rows, f'{len(rows)} stor{"y" if len(rows) == 1 else "ies"} since {S.nice(S.editions()[0], "%d %b %Y")}, newest first.')
        cards[reg].append((slug(name), name, len(rows), max(d for d, _ in rows)))
    for v in cards.values():
        v.sort(key=lambda c: (-c[2], c[1]))
    index("places", "Near you", "Every story, by Indian state and by country. Pick a place to see what has been recorded there.",
          [("India, by state", cards["india"]), ("World, by country", cards["world"])])
    return cards


def people(items):
    by = collections.defaultdict(list)
    for d, it in items:
        for g in groups_of(it):
            by[g].append((d, it))
    cards = []
    for g, name, _ in GROUPS:
        rows = by.get(g, [])
        if rows:
            listing("people", g, name, rows, f'{len(rows)} stor{"y" if len(rows) == 1 else "ies"}, newest first. '
                    'Older stories are matched by keywords until editions carry group tags, so a few may be misfiled.')
            cards.append((g, name, len(rows), max(d for d, _ in rows)))
    index("people", "About people like you", "The same record, by who is affected. Pick a group to see every story about it.", [("Groups", cards)])
    return cards


# ── 2 + 3. coverage floor and source spread ──────────────────────────────────────────────────────────────────────
def coverage(items):
    week = S.editions()[-7:]
    rows = [(d, it) for d, it in items if d in week]
    tick = lambda ok: '<span class="pv-ok">✓ met</span>' if ok else '<span class="pv-miss">✕ missing</span>'
    names = {g: n for g, n, _ in GROUPS}
    gcount = collections.Counter(g for _, it in rows for g in groups_of(it))
    trs = [f'<tr><td>{E(names[g])}</td><td>{gcount[g]}</td><td>{tick(gcount[g] > 0)}</td></tr>' for g in FLOOR_GROUPS]
    for nm, rx in FLOOR_RIGHTS:
        n = sum(1 for _, it in rows if re.search(rx, (" ".join(it.get("rights", [])) + " " + it["headline"] + " " + it["text"]).lower()))
        trs.append(f'<tr><td>{nm}</td><td>{n}</td><td>{tick(n > 0)}</td></tr>')
    states = collections.Counter(place_of(it) for _, it in rows if it.get("region") == "india")
    other = sorted(s for s in states if s != "Delhi" and s not in NORTHEAST)
    trs.append(f'<tr><td>Indian states outside Delhi and the Northeast (at least {FLOOR_STATES})</td><td>{len(other)}: {E(", ".join(other))}</td><td>{tick(len(other) >= FLOOR_STATES)}</td></tr>')
    world = collections.Counter(place_of(it) for _, it in rows if it.get("region") == "world")
    src = collections.Counter(outlet(s[0]) for _, it in rows for s in it.get("src", []))
    tot = sum(src.values()) or 1
    srows = "".join(f'<tr><td>{E(n)}</td><td><span class="pv-bar{" over" if 100 * c / tot > SHARE_CAP else ""}" style="width:{max(4, round(220 * c / tot))}px"></span>{round(100 * c / tot)}% ({c})</td></tr>'
                    for n, c in src.most_common(10))
    body = f"""<header><h1 class="pv-h1">How balanced are we?</h1>
<p class="pv-lead">The last 7 editions ({S.nice(week[0])} to {S.nice(week[-1])}, {len(rows)} stories) checked against our weekly coverage floor. We publish this so readers can hold us to it.</p></header>
<section class="pv-box"><h2>Weekly floor</h2><table class="pv-tbl"><tr><th>Must appear at least once</th><th>This week</th><th></th></tr>{"".join(trs)}</table></section>
<section class="pv-box"><h2>Where the week's stories came from</h2><table class="pv-tbl"><tr><th>India</th><th>World</th></tr>
<tr><td>{E(" · ".join(f"{s} {c}" for s, c in states.most_common()))}</td><td>{E(" · ".join(f"{s} {c}" for s, c in world.most_common()))}</td></tr></table></section>
<section class="pv-box"><h2>Whose reporting we relied on</h2><p>No outlet should supply more than {SHARE_CAP}% of a week's source links; bars over the cap are orange.</p>
<table class="pv-tbl"><tr><th>Outlet</th><th>Share of {tot} source links</th></tr>{srows}</table></section>
<p class="rd-sub">Group counts use keyword matching until editions carry group tags, so they are approximate.</p>"""
    page("coverage/index.html", "How balanced are we?", "The week's coverage against our floor.", body)


# ── 6. report + corrections, 8. about ────────────────────────────────────────────────────────────────────────────
def report():
    body = """<header><h1 class="pv-h1">Report something</h1>
<p class="pv-lead">Seen a right denied, or upheld, where you live? Tell us. We publish only what we can source, so we may not use every report, but every one is read.</p></header>
<section class="pv-box"><h2>Before you write</h2><ul>
<li><b>Your safety first.</b> Do not send from a work or shared device or account if the report could put you at risk.</li>
<li><b>No names of survivors of sexual violence, or of children.</b> We never publish them; please do not send them.</li>
<li><b>What we need to publish:</b> a published source (a news report, court order, FIR number or official statement) or a way to find one. A report without one becomes a lead we try to verify.</li>
<li><b>We never name you</b> unless you ask us to. Say if we may write back.</li></ul></section>
<form class="pv-form" data-report>
<label>What happened? <span class="hint">Two or three sentences: who was affected and what was done.</span><textarea class="input" name="what" required></textarea></label>
<label>Where? <span class="hint">Village or town, district, state or country.</span><input class="input" name="where" required></label>
<label>When? <input class="input" name="when" placeholder="Date, or about when"></label>
<label>A link or document that shows it <span class="hint">News report, court order, FIR number, official notice.</span><input class="input" name="source"></label>
<label>What do the authorities say, if you know? <input class="input" name="official"></label>
<label>May we write back to you? <select class="input" name="reply"><option>No</option><option>Yes, by email</option></select></label>
<div><button class="btn btn-primary" type="submit">Open my email app with this report</button>
<p class="rd-sub" style="margin:8px 0 0">Nothing is sent from this page: the button opens a draft in your own email app, addressed to resistancedaily.in@gmail.com, and you press send.</p></div></form>
<script>document.querySelector('[data-report]').addEventListener('submit',function(e){e.preventDefault();var f=new FormData(e.target),b='';
[['what','What happened'],['where','Where'],['when','When'],['source','Source'],['official','Official position'],['reply','May we write back']].forEach(function(k){b+=k[1]+': '+(f.get(k[0])||'')+'\\n\\n';});
location.href='mailto:resistancedaily.in@gmail.com?subject='+encodeURIComponent('Report: '+(f.get('where')||''))+'&body='+encodeURIComponent(b);});</script>"""
    page("report/index.html", "Report something", "Tell Resistance Daily about a right denied or upheld.", body)


def corrections():
    items = S.load("data/corrections.json").get("items", [])
    rows = "".join(f'<div class="pv-row"><time>{S.nice(c["date"], "%d %b %Y")}</time><div><h3>{E(c["page"])}</h3><p><b>We wrote:</b> {E(c["was"])}</p>'
                   f'<p><b>Correct:</b> {E(c["now"])}</p><span class="rd-src">{S.src_links(c.get("src", []))}</span></div></div>' for c in reversed(items))
    body = f"""<header><h1 class="pv-h1">Corrections</h1>
<p class="pv-lead">When we get a fact wrong we fix it and list it here: what we wrote, what is correct, and the source. Nothing is quietly changed.</p></header>
<section>{rows or '<div class="pv-box"><p style="margin:0">No corrections have been logged since this page was started. Spotted an error? <a href="../report/">Tell us</a>.</p></div>'}</section>"""
    page("corrections/index.html", "Corrections", "The public corrections log.", body)


def about():
    todo = lambda s: f'<span class="pv-todo">[Owner to fill in: {s}]</span>'
    body = f"""<header><h1 class="pv-h1">About Resistance Daily</h1>
<p class="pv-lead">A daily, non-partisan public record of human-rights and civil-liberties events in India and around the world.</p></header>
<section class="pv-box"><h2>Who runs it</h2><p>{todo("who you are, in one or two sentences; a name or a description such as 'an independent citizen in Bengaluru'")}</p>
<p>Contact: <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a></p></section>
<section class="pv-box"><h2>How it is paid for</h2><p>{todo("funding. For example: 'Self-funded. No advertising, no donations, no party or organisation behind it.'")}</p></section>
<section class="pv-box"><h2>How it is made</h2><ul>
<li>Each morning an AI assistant (Claude, made by Anthropic) researches the previous 24 hours, opens every source and drafts the edition, following written rules the owner sets.</li>
<li>The rules are public: <a href="https://github.com/resistancedaily/resistancedaily.github.io/blob/main/ROUTINE.md">read them here</a>.</li>
<li>{todo("how you review it, e.g. 'The owner reads every edition and corrects errors'")}</li>
<li>AI can make mistakes. Every fact links to its source so you can check it, and errors are listed on the <a href="../corrections/">corrections page</a>.</li>
<li>Photos are never AI-generated. They are freely licensed, credited, and labelled as file photos when they do not show the event.</li></ul></section>
<section class="pv-box"><h2>What "non-partisan" means here</h2><ul>{S.HOW}</ul>
<p style="margin-top:10px">We publish <a href="../coverage/">how balanced our coverage is</a> every week.</p></section>
<section class="pv-box"><h2>About the name</h2><p>{todo("one line on what 'Resistance' means to you, e.g. 'resisting indifference, not any party'. Worth saying, because the name can read as taking a side.")}</p></section>"""
    page("about/index.html", "About", "Who runs Resistance Daily and how it is made.", body)


# ── 7. feed ──────────────────────────────────────────────────────────────────────────────────────────────────────
def feed():
    ents = []
    for d in reversed(S.editions()[-20:]):
        ed = S.load(f"data/{d}.json")
        lis = "".join(f"<li><b>{E(it.get('short', it['place']))}:</b> {E(it['headline'])}. {E(it['text'])}</li>" for it in ed["items"])
        when = datetime.datetime.fromisoformat(d + "T09:00:00+05:30")
        url = f"{S.SITE}archive/{d}.html"
        ents.append(f"<item><title>{E('Resistance Daily · ' + ed.get('date_long', d))}</title><link>{url}</link><guid isPermaLink=\"true\">{url}</guid>"
                    f"<pubDate>{email.utils.format_datetime(when)}</pubDate><description>{E('<ul>' + lis + '</ul>')}</description></item>")
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Resistance Daily</title><link>{S.SITE}</link>'
           f"<description>{E(S.DESC)}</description><language>en-in</language>{''.join(ents)}</channel></rss>\n")
    open(os.path.join(OUT, "feed.xml"), "w").write(xml)


def hub(pc, gc):
    cards = [
        ("hi/", "हिन्दी · Hindi edition", "Today's stories in Hindi, with a Listen button"),
        ("kn/", "ಕನ್ನಡ · Kannada edition", "Today's stories in Kannada, with a Listen button"),
        ("en/", "English, with Listen", "The same page in English, to compare"),
        ("places/", "Near you", f'{len(pc["india"])} Indian states and {len(pc["world"])} countries, each with its own page'),
        ("people/", "About people like you", f"{len(gc)} groups: workers, women, students, migrants and more"),
        ("coverage/", "How balanced are we?", "The week against the coverage floor, and each outlet's share"),
        ("report/", "Report something", "Safety guidance and a form that opens the reader's own email"),
        ("corrections/", "Corrections", "A public log of fixed errors"),
        ("about/", "About", "Who runs it, how it is made (AI-assisted), how it is paid for"),
        ("feed.xml", "RSS feed", "One entry per edition, for feed readers"),
        ("ROUTINE-additions.md", "Proposed routine rules", "The text to add to ROUTINE.md when you approve"),
    ]
    body = (f'<header><h1 class="pv-h1">Reaching more people</h1><p class="pv-lead">A preview of the changes proposed on 10 Nov 2026, built from the {S.nice(DATE, "%d %b")} edition. '
            'Open each one; nothing here is live until you say so.</p></header><div class="pv-grid">'
            + "".join(f'<a class="pv-card" href="{h}"><b>{E(t)}</b><span>{E(s)}</span></a>' for h, t, s in cards) + "</div>")
    page("index.html", "Preview", "Preview of proposed changes.", body)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    items = all_items()
    for code, _ in LANGS:
        edition(code)
    pc, gc = places(items), people(items)
    coverage(items); report(); corrections(); about(); feed(); hub(pc, gc)
    print(f"built preview/ from {DATE}: {len(pc['india'])} states, {len(pc['world'])} countries, {len(gc)} groups")
