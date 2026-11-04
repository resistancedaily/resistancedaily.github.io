#!/usr/bin/env python3
"""Build one Resistance Daily edition into the site repository (github.com/resistancedaily/resistancedaily.github.io).

"Threads" redesign (Nov 2026): the web edition is no longer a weekday layout. DESIGN is still accepted (it is logged
in archive/editions.json, and the slides may use it) but every page is built by tools/home.py: the home page, today/
and archive/DATE.html share one layout. Thread pages (threads/SLUG.html) come from tools/threads.py.

Usage (from the repo root):
  python3 tools/publish.py DESIGN YYYY-MM-DD data/YYYY-MM-DD.json [data/YYYY-MM-DD.maps.json]

Writes:
  index.html                 the home page = today's edition (tools/home.py)
  today/index.html           the same edition at /today/ (canonical: its archive page)
  archive/YYYY-MM-DD.html    permanent copy, with every story in full under "All stories this day" (#iN anchors)
  archive/index.html         all editions by month, newest first
  threads/SLUG.html          every registry thread, newest update first (tools/threads.py)
  build/artifact.html        the edition with CSS and JS inlined (the Claude artifact backup)
Then: git add -A && git commit && git push.
Repo layout: tools/ (design.py, maps.js, thin.py, publish.py, package.json), data/ (YYYY-MM-DD.json, YYYY-MM-DD.maps.json, cases.json), archive/, .nojekyll, README.md. .gitignore: node_modules/ build/
"""
import sys, os, re, json, subprocess, html, datetime
import seo

design, date, data_path = sys.argv[1], sys.argv[2], sys.argv[3]
maps_path = sys.argv[4] if len(sys.argv) > 4 else None
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# "Today on the map" (every design): when no maps file is given and every item has "lon"/"lat", build
# data/DATE.items.json from the items (label = "short"; optional "map": {"left", "pos", "dx", "dy"} nudges) and run
# tools/maps.js + tools/thin.py to make data/DATE.maps.json.
_d = json.load(open(data_path))
if not maps_path and _d["items"] and all("lon" in i and "lat" in i for i in _d["items"]):
    pts = {"india": [], "world": []}
    for i in _d["items"]:
        pt = {"n": i["n"], "lon": i["lon"], "lat": i["lat"], "sev": i["sev"], "label": i.get("short", "")}
        pt.update(i.get("map", {}))
        pts["india" if i["region"] == "india" else "world"].append(pt)
    ip, mp = os.path.join(root, "data", f"{date}.items.json"), os.path.join(root, "data", f"{date}.maps.json")
    json.dump(pts, open(ip, "w"), ensure_ascii=False, indent=1)
    with open(mp, "w") as fh:
        subprocess.run(["node", os.path.join(root, "tools", "maps.js"), ip], check=True, stdout=fh, cwd=os.path.join(root, "tools"))
    subprocess.run([sys.executable, os.path.join(root, "tools", "thin.py"), mp], check=True)
    maps_path = mp
data = json.load(open(data_path))
import rdsite as S
import home as HOME
import threads as T
SITE = seo.SITE
top = sorted(data["items"], key=lambda i: (not i.get("lead"), S.SEV[i["sev"]]))[:3]
desc = "; ".join(f"{i.get('short', i['place'])}: {i['headline']}" for i in top)

# Link previews: a 1200x630 JPEG from the most serious item that has a photo, else a text card.
lead = next((i for i in sorted(data["items"], key=lambda i: (not i.get("lead"), S.SEV[i["sev"]])) if i.get("photo")), None)
share = seo.share_image(root, lead["photo"]["src"], f"images/{date}/share.jpg") if lead and not lead["photo"]["src"].startswith("http") else None
if not share:
    lines = [f"{i.get('short', i['place'])}: {i['headline']}" for i in top]
    share = seo.text_card(root, f"images/{date}/share.jpg", f"{data['date_long']} · Where things stand today", lines)

canon = f"{SITE}archive/{date}.html"
HOME.build(date, "today/index.html", "../", canon, "today", share)
HOME.build(date, f"archive/{date}.html", "../", canon, "archive", share)
body = HOME.build(date, "build/artifact.html", "", canon, "archive", share, inline=True)
# The backup page keeps images/ paths relative: publish those files with the artifact (see the list printed below).
imgs = sorted(set(re.findall(r'src="(images/[^"]+)"', body)))
if imgs:
    print("artifact files:", json.dumps({i: i for i in imgs}))

# archive index: grouped by month, one top line per day
log_path = os.path.join(root, "archive", "editions.json")
log = json.load(open(log_path)) if os.path.exists(log_path) else {}
log[date] = {"design": design, "summary": desc}
json.dump(log, open(log_path, "w"), ensure_ascii=False, indent=1)


def top_line(d, v):
    return S.top_line(d) or v["summary"]


months, rows = {}, []
for d, v in sorted(log.items(), reverse=True):
    m = datetime.date.fromisoformat(d).strftime("%B %Y")
    months.setdefault(m, []).append(f'<li><a href="{d}.html"><b>{html.escape(S.nice(d))}</b><span>{html.escape(top_line(d, v))}</span></a></li>')
lists = "".join(f'<section class="rd-sec"><h2 class="rd-h">{html.escape(m)}</h2><ul class="rd-past rd-arch-list">{"".join(r)}</ul></section>'
                for m, r in months.items())
ai = (S.head("Past editions · Resistance Daily", "Every Resistance Daily edition, newest first.", "../", f"{SITE}archive/")
      + S.nav("../") + f'<header><span class="rd-kicker">Archive</span><h1 style="font-size:44px;margin:6px 0 0">Past editions</h1></header>{lists}'
      + S.footer("../"))
open(os.path.join(root, "archive", "index.html"), "w").write(ai)

T.build_all()
seo.write_sitemap(root)
subprocess.run([sys.executable, os.path.join(root, "tools", "home.py"), "index.html"], check=True, cwd=root)
print("built", design, date)
missing = [i for i in data["items"] if not i.get("photo")]
if missing:
    print(f"PHOTOS: {len(missing)} of {len(data['items'])} items have no photo "
          f"({', '.join(str(i['n']) for i in missing)}). See ROUTINE.md, STEP 3.")
if imgs:
    print("BACKUP PAGE: pass the 'artifact files' map above as `files` when publishing build/artifact.html (ROUTINE.md, STEP 5).")
