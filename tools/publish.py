#!/usr/bin/env python3
"""Build one Resistance Daily edition into the site repository (github.com/resistancedaily/resistancedaily.github.io).

Usage (from the repo root):
  python3 tools/publish.py DESIGN YYYY-MM-DD data/YYYY-MM-DD.json [data/YYYY-MM-DD.maps.json]

Writes:
  index.html                 today's edition (full HTML document)
  archive/YYYY-MM-DD.html    permanent copy
  archive/index.html         list of all editions, newest first
  build/artifact.html        page content without the document wrapper (for the Claude artifact backup)
Then: git add -A && git commit && git push.
Repo layout: tools/ (design.py, maps.js, thin.py, publish.py, package.json), data/ (YYYY-MM-DD.json, YYYY-MM-DD.maps.json, cases.json), archive/, .nojekyll, README.md. .gitignore: node_modules/ build/
"""
import sys, os, re, json, subprocess, html, datetime

design, date, data_path = sys.argv[1], sys.argv[2], sys.argv[3]
maps_path = sys.argv[4] if len(sys.argv) > 4 else None
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cmd = [sys.executable, os.path.join(root, "tools", "design.py"), design, data_path] + ([maps_path] if maps_path else [])
body = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
data = json.load(open(data_path))
# Ensure the footer carries the archive link and contact line (design.py does not add it)
if 'href="archive/"' not in body:
    body = body.replace("</span></footer>", '</span><span><a href="archive/">Past editions</a> · Contact or send a tip: <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a></span></footer>', 1)

top = sorted(data["items"], key=lambda i: {"red": 0, "orange": 1, "grey": 2}[i["sev"]])[:3]
desc = "; ".join(f"{i.get('short', i['place'])}: {i['headline']}" for i in top) if design != "tracker" else \
    "Still waiting: people held for long periods after speaking out, protesting or reporting, in India and around the world."
title = f"Resistance Daily · {data['date_long']}"
SITE = "https://resistancedaily.github.io/"
ICON = "data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%2315181d'/%3E%3Crect x='14' y='18' width='22' height='6' rx='2' fill='%23d9661a'/%3E%3Ctext x='14' y='50' font-family='Arial' font-weight='900' font-size='26' fill='%23f3f4f2'%3ERD%3C/text%3E%3C/svg%3E"

def wrap(content, canonical):
    content = re.sub(r"<title>.*?</title>", "", content, count=1, flags=re.S)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{ICON}">
<link rel="canonical" href="{canonical}">
<style>body{{margin:0}}</style>
</head><body>
{content}
</body></html>
"""

os.makedirs(os.path.join(root, "archive"), exist_ok=True)
os.makedirs(os.path.join(root, "build"), exist_ok=True)
open(os.path.join(root, "index.html"), "w").write(wrap(body, SITE))
arch = body.replace('href="archive/"', 'href="./"').replace('src="images/', 'src="../images/').replace('href="focus/', 'href="../focus/')
open(os.path.join(root, "archive", f"{date}.html"), "w").write(wrap(arch, f"{SITE}archive/{date}.html"))
# The backup page keeps images/ paths relative: publish those files with the artifact (see the list printed below).
open(os.path.join(root, "build", "artifact.html"), "w").write(body.replace('href="archive/"', f'href="{SITE}archive/"')
    .replace('href="focus/', f'href="{SITE}focus/'))
imgs = sorted(set(re.findall(r'src="(images/[^"]+)"', body)))
if imgs:
    print("artifact files:", json.dumps({i: i for i in imgs}))

# archive index
names = {"map": "Map", "numbers": "Day in numbers", "ledger": "Rights ledger", "front": "Front page", "clock": "24-hour clock", "tracker": "Still waiting"}
log_path = os.path.join(root, "archive", "editions.json")
log = json.load(open(log_path)) if os.path.exists(log_path) else {}
log[date] = {"design": design, "summary": desc}
json.dump(log, open(log_path, "w"), ensure_ascii=False, indent=1)
rows = "".join(
    f'<li><a href="{d}.html"><b>{datetime.date.fromisoformat(d).strftime("%a %d %b %Y")}</b></a> <span class="t">{names.get(v["design"], v["design"])}</span><p>{html.escape(v["summary"])}</p></li>'
    for d, v in sorted(log.items(), reverse=True))
open(os.path.join(root, "archive", "index.html"), "w").write(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Resistance Daily · Past editions</title><link rel="icon" href="{ICON}">
<style>
:root{{--bg:#f3f4f2;--paper:#fff;--ink:#15181d;--muted:#5b616b;--rule:#d9dcd8;--accent:#d9661a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:760px;margin:0 auto;padding:24px max(16px,env(safe-area-inset-left))}}
h1{{font:800 44px "Arial Narrow",Arial,sans-serif;text-transform:uppercase;margin:0 0 4px}}
a{{color:inherit;text-decoration-color:var(--accent)}}
ul{{list-style:none;padding:0;display:grid;gap:8px}}
li{{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px 14px}}
.t{{font:500 11px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin-left:8px}}
li p{{margin:4px 0 0;color:var(--muted);font-size:14px}}
</style></head><body><div class="wrap">
<h1>Past editions</h1><p><a href="../">← Today's edition</a> · Every edition is kept here permanently.</p>
<ul>{rows}</ul>
<p style="color:var(--muted);font-size:13px">Contact or send a tip: resistancedaily.in@gmail.com</p>
</div></body></html>
""")
print("built", design, date)
# Standing routine instructions live in ROUTINE.md (photos, Focus, slides). Remind the run of the photo step.
if design != "tracker":
    missing = [i for i in data["items"] if not i.get("photo")]
    if missing:
        print(f"PHOTOS: {len(missing)} of {len(data['items'])} items have no photo "
              f"({', '.join(str(i['n']) for i in missing)}). See ROUTINE.md, STEP 2b.")
if imgs:
    print("BACKUP PAGE: pass the 'artifact files' map above as `files` when publishing build/artifact.html (ROUTINE.md, STEP 3).")
