#!/usr/bin/env python3
"""Resistance Daily Instagram slides (1080x1350 JPEG).

  python3 tools/slides.py daily DATE OUTDIR      reads data/DATE.json and data/DATE.slides.json
  python3 tools/slides.py focus SLUG OUTDIR      reads data/focus/SLUG.json
  python3 tools/slides.py focus SLUG OUTDIR --update
                                                 an update post: slide 1 says "Update · DATE" and carries the Focus's
                                                 "whats_new" text instead of the summary (see ROUTINE.md, Instagram updates)

data/DATE.slides.json (the text-led daily carousel; a story slide shows its item's photo when the item has one):
{ "cover": [[place, headline <= 45 chars], x4],
  "stories": [{"n": item number, "label": "India · Life & safety", "fig", "figlab", "place", "head", "bullets": [2-3], "src": "A · B"}, x4] }
  Sunday case slides (not tied to an item) may carry their own "photo" (same fields as an item photo) and a "caption".
  "cover_style": "photo-sunday" = the photo cover on a light panel with red place names and "+ Still waiting".
  Sundays pick the current week's cover layout in white automatically (see cover_style()); set "cover_style" to override.

Focus carousels: cover photo + title, one slide per further photo (up to 6), key numbers, then "full story" with credits.
Writes OUTDIR/*.jpg, OUTDIR/contact.png (contact sheet), OUTDIR/facebook-post.txt, whatsapp.txt and x-post.txt (with direct links) and OUTDIR/slide-captions.txt (one caption per slide;
Instagram carousels take a caption per photo). For focus also caption.txt (slide 1's caption) and alt-text.txt.
Fonts come from @fontsource packages (npm pack) into build/fonts on first run.
"""
import sys, os, re, json, glob, html, subprocess, datetime

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(root, "build", "fonts")
# Threads redesign (Nov 2026): Caprasimo (headings) and Figtree (body). The old family names used across the slide
# templates are mapped onto them, so every slide type (covers, stories, focus, hope) takes the new type at once.
PKGS = ["@fontsource/caprasimo@5.2.7", "@fontsource/figtree@5.2.10"]
BG, INK, AC, RED, GR = "#f5ead8", "#201e1d", "#c67139", "#201e1d", "#7a8a5e"   # no red: RED is the text colour
AC_T = "#8c491a"            # accent text on the cream ground
SAGE, SAGE_T = "#e1eecc", "#272e1b"
WASH = "filter:saturate(.6) contrast(.85) brightness(1.1) opacity(.94)"


def fonts():
    have = lambda pkg: glob.glob(os.path.join(FONTS, f"fontsource-{pkg}-*", "package", "files"))
    if not all(have(p.split("/")[1].split("@")[0]) for p in PKGS):
        os.makedirs(FONTS, exist_ok=True)
        subprocess.run(["npm", "pack", "-q", *PKGS], cwd=FONTS, check=True, capture_output=True)
        for t in glob.glob(os.path.join(FONTS, "*.tgz")):
            d = t[:-4]; os.makedirs(d, exist_ok=True)
            subprocess.run(["tar", "xzf", t, "-C", d], check=True)

    def ff(fam, pkg, w, as_w=None):
        path = sorted(glob.glob(os.path.join(FONTS, f"fontsource-{pkg}-*", "package", "files", f"{pkg}-latin-{w}-normal.woff2")))[-1]
        return f"@font-face{{font-family:'{fam}';font-weight:{as_w or w};src:url('file://{path}') format('woff2')}}"
    return "".join([ff("Caprasimo", "caprasimo", 400), ff("Figtree", "figtree", 400), ff("Figtree", "figtree", 600),
                    ff("Figtree", "figtree", 700),
                    # old names -> new faces
                    ff("Barlow Condensed", "caprasimo", 400, 800), ff("IBM Plex Sans", "figtree", 400),
                    ff("IBM Plex Sans", "figtree", 600), ff("IBM Plex Mono", "figtree", 600, 500)])


CSS = f"""
*{{box-sizing:border-box;margin:0}}
body{{margin:0}}
.s{{width:1080px;height:1350px;padding:90px 84px;position:relative;overflow:hidden;font-family:'IBM Plex Sans';display:flex;flex-direction:column}}
.light{{background:{BG};color:{INK}}} .dark{{background:{INK};color:{BG}}}
.top{{display:flex;justify-content:space-between;font:500 24px 'IBM Plex Mono';text-transform:uppercase;letter-spacing:.08em;color:#7a808a}}
.D{{font-family:'Barlow Condensed';font-weight:800;text-transform:uppercase;line-height:.9}}
.big{{font-family:'Barlow Condensed';font-weight:800;font-size:260px;line-height:.85;color:{RED}}}
.lab{{font:500 30px 'IBM Plex Mono';color:#7a808a;text-transform:uppercase;letter-spacing:.05em;margin-top:14px}}
.place{{font:800 40px 'Barlow Condensed';text-transform:uppercase;color:{AC};margin-top:44px;letter-spacing:.02em}}
h2{{font-family:'Barlow Condensed';font-weight:800;font-size:76px;line-height:.95;text-transform:uppercase;margin-top:8px}}
ul{{padding:0;list-style:none;margin-top:34px;display:grid;gap:22px}}
li{{font-size:33px;line-height:1.3;padding-left:30px;position:relative}}
li:before{{content:'';position:absolute;left:0;top:16px;width:12px;height:12px;background:{AC};border-radius:2px}}
.srcs{{margin-top:auto;font:500 22px 'IBM Plex Mono';color:#7a808a;line-height:1.4}}
.act{{border-left:8px solid {GR};padding:14px 0 14px 26px;margin-top:26px}}
.act b{{font:800 50px 'Barlow Condensed';text-transform:uppercase;display:block}}
.act span{{font-size:28px;color:#b8bcc2}}
/* photo story slide */
.s.ph{{padding:0}}
.ph .img{{position:relative;height:560px;flex:none;background:#2b2f36}}
.ph .img img,.full img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.ph .img .top{{position:absolute;left:0;right:0;top:0;padding:60px 84px 80px;color:#fff;background:linear-gradient(rgba(0,0,0,.72),rgba(0,0,0,0))}}
.chip{{position:absolute;left:84px;bottom:24px;font:500 21px 'IBM Plex Mono';text-transform:uppercase;letter-spacing:.06em;background:rgba(21,24,29,.82);color:#f3f4f2;padding:8px 14px;border-radius:4px}}
.ph .body{{padding:40px 84px 70px;display:flex;flex-direction:column;flex:1}}
.ph .row{{display:flex;align-items:flex-end;gap:28px}}
.ph .big{{font-size:170px}}
.ph .lab{{margin:0 0 18px}}
.ph .place{{margin-top:26px}}
.ph h2{{font-size:64px}}
.ph ul{{margin-top:24px;gap:14px}}
.ph li{{font-size:30px}}
.ph .srcs{{font-size:19px}}
/* story without a photo: the key figure fills the photo area, so every story slide has the same shape */
.ph .img.figp{{background:#e2e5e0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
.ph .img.figp .top{{background:none;color:#7a808a}}
.figp .big{{font-size:240px;margin-top:40px}}
.figp .lab{{margin-top:18px;font-size:34px}}
.ph .body>.place:first-child{{margin-top:6px}}
/* focus */
.full{{padding:0;color:#fff}}
.full .shade{{position:absolute;inset:0;background:linear-gradient(rgba(0,0,0,.6) 0%,rgba(0,0,0,0) 20%,rgba(0,0,0,.25) 38%,rgba(0,0,0,.9) 62%,rgba(0,0,0,.94) 100%)}}
.full .in{{position:relative;height:100%;padding:90px 84px;display:flex;flex-direction:column}}
.full .top{{color:#e6e6e6}}
.kick{{font:500 26px 'IBM Plex Mono';text-transform:uppercase;letter-spacing:.08em;color:{AC}}}
.kick.on{{justify-self:start;background:{INK};padding:8px 14px;border-radius:4px}}
.pcap{{background:{INK};color:{BG};padding:34px 84px 64px;display:grid;gap:12px;flex:none}}
.pslide{{padding:0;display:flex;flex-direction:column;background:{INK};color:#fff}}
.pslide .pimg{{position:relative;flex:1}}
.pcap p{{font-size:32px;line-height:1.35}}
.pcap .cr{{font:500 19px 'IBM Plex Mono';color:#9ba1aa;line-height:1.4}}
.figs{{display:grid;grid-template-columns:1fr 1fr;gap:26px;margin-top:50px}}
.fig{{border-top:8px solid {RED};background:#fff;padding:26px 28px;display:grid;gap:10px;align-content:start}}
.fig b{{font:800 104px 'Barlow Condensed';line-height:.9;color:{RED}}}
.fig span{{font:500 24px 'IBM Plex Mono';text-transform:uppercase;letter-spacing:.04em;color:#5b616b}}
/* ── Threads redesign overrides ── */
.D,h2,.place,.act b,.fig b{{text-transform:none;letter-spacing:-.01em;line-height:1.02}}
.top{{color:#645c50}} .lab,.srcs{{color:#645c50}}
.big{{color:{INK}}}
li:before{{background:{AC};border-radius:50%}}
img{{{WASH}}}
.act{{border-left-color:{GR}}} .act span{{color:#dcd3c4}}
.fig{{border-top:0;background:#ebddc5;border-radius:32px}}
.chip,.kick.on{{border-radius:999px}}
/* story slide: kicker row, arch photo, tag pill, headline */
.st{{padding:70px 84px 70px}}
.st .k{{display:flex;justify-content:space-between;font:600 24px 'Figtree';text-transform:uppercase;letter-spacing:.08em;color:{AC_T}}}
.st .k span+span{{color:#645c50}}
.st .arch{{position:relative;height:500px;margin-top:30px;border-radius:250px 250px 40px 40px;overflow:hidden;background:#ebddc5;flex:none}}
.st .arch img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.st .arch .ptag{{position:absolute;left:28px;bottom:24px;font:600 20px 'Figtree';text-transform:uppercase;letter-spacing:.05em;background:rgba(46,43,37,.72);color:#f9f4ed;padding:8px 16px;border-radius:999px}}
.st .arch.fp{{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
.st .arch.fp b{{font:400 200px/1 'Caprasimo'}} .st .arch.fp span{{font:600 28px 'Figtree';color:#645c50;margin-top:10px}}
.st .tags{{display:flex;gap:12px;align-items:center;margin-top:34px;font-size:26px;color:#645c50}}
.st .tag{{font:600 24px 'Figtree';padding:8px 20px;border-radius:999px;background:#f9f4ed;color:#474238}}
.st .tag.acc{{background:#ffe1d0;color:#643312}} .st .tag.up{{background:#f0fae1;color:#3d472b}}
.st h2{{font:400 64px/1.08 'Caprasimo';margin-top:18px;text-transform:none}}
.st ul{{margin-top:22px;gap:12px}} .st li{{font-size:29px}}
.st .srcs{{font:400 21px 'Figtree';color:#645c50}}
.st.up{{background:{SAGE};color:{SAGE_T}}} .st.up .k{{color:#3d472b}} .st.up .arch{{background:#ccdbb2}}
"""


def top(label, n, N, light=False):
    return f'<div class="top"><span>{E(label)}</span><span>{n} / {N}</span></div>'


def credit(p):
    """Short on-slide credit (owner's rule): author and licence family; the full credit, licence version and changes
    are on the website. "faces blurred" stays, because it tells viewers the photo was altered."""
    who = p["credit"].replace(", via Wikimedia Commons", "").replace(" / Wikimedia Commons", "")
    lic = re.sub(r"\s+[0-9.]+(\s+igo)?$", "", p["licence"], flags=re.I)
    blur = " · faces blurred" if "blur" in p.get("changes", "") else ""
    return f"Photo: {who} · {lic}{blur}"


def label(p):
    return "Photo from the event" if p.get("kind") == "event" else f"File photo · {p['year']}"


def src_url(p):
    s = p["src"]
    return s if s.startswith(("http://", "https://")) else "file://" + os.path.join(root, s)


def pic(st, by):
    """A story slide's photo: its own "photo" (Sunday case slides, not tied to an item) or its item's photo."""
    return st.get("photo") or by.get(st.get("n"), {}).get("photo")


def big_enough(p, min_w=900):
    """Photos narrower than min_w px look soft at 1080px; remote photos are assumed to be large enough."""
    if p["src"].startswith(("http://", "https://")):
        return True
    from PIL import Image
    return Image.open(os.path.join(root, p["src"])).size[0] >= min_w


def write_captions(out, caps):
    for i, c in enumerate(caps, 1):
        if len(c) > 2200:
            print(f"WARNING: the caption for slide {i} is {len(c)} characters; Instagram allows 2,200. Shorten it.", file=sys.stderr)
    open(os.path.join(out, "slide-captions.txt"), "w").write(
        "\n\n".join(f"===== Slide {i} =====\n{c or '(no caption)'}" for i, c in enumerate(caps, 1)) + "\n")


SITE = "https://resistancedaily.github.io/"


def facebook_daily(d, out):
    """facebook-post.txt: Facebook posts carry clickable links, so link the permanent edition page (and the Focus)
    directly. Headlines and places come from data.json; the facts and their sources are on the linked page."""
    items = sorted(d["items"], key=lambda i: (not i.get("lead"), {"red": 0, "orange": 1, "grey": 2}[i["sev"]]))[:4]
    dt = datetime.date.fromisoformat(d["date"])
    lines = [f"Resistance Daily · {dt.strftime('%A %d %B %Y')}", "What happened to people's rights in the last 24 hours. Every fact sourced.", ""]
    lines += [f"{k}. {i.get('short', i['place'])}: {i['headline']}" for k, i in enumerate(items, 1)]
    if d.get("cases"):
        lines += ["", f"Still waiting: {len(d['cases'])} people and groups held for a long time after speaking out, protesting or reporting."]
    lines += ["", f"Full edition, with a source for every fact: {SITE}archive/{d['date']}.html"]
    for fc in d.get("focus", []):
        lines += [f"In focus · {fc['title']}: {SITE}focus/{fc['slug']}.html"]
    lines += ["", "Non-partisan. Rights, not parties.", "", "#HumanRights #CivilLiberties #ResistanceDaily"]
    open(os.path.join(out, "facebook-post.txt"), "w").write("\n".join(lines) + "\n")


# Verified X accounts of outlets we cite, to tag them ("via @..."). Add a handle only after opening the account and
# confirming it is the outlet's official one.
X_HANDLES = {}


def x_post(out, lines, url):
    """x-post.txt: one post, at most 280 characters (X counts any link as 23). Drops lines from the end to fit."""
    lines = list(lines)
    while lines and len("\n".join(lines)) + 1 + 23 > 280:
        lines.pop()
    open(os.path.join(out, "x-post.txt"), "w").write("\n".join(lines + [url]) + "\n")


def via(src):
    tags = [X_HANDLES[n] for n, u in src if n in X_HANDLES]
    return f" (via {' '.join(dict.fromkeys(tags))})" if tags else ""


def social_daily(d, out):
    """whatsapp.txt (the channel post) and x-post.txt for the daily edition."""
    items = sorted(d["items"], key=lambda i: (not i.get("lead"), {"red": 0, "orange": 1, "grey": 2}[i["sev"]]))
    dt = datetime.date.fromisoformat(d["date"])
    ed = f"{SITE}archive/{d['date']}.html"
    wa = [f"*Resistance Daily · {dt.strftime('%a %d %b')}*", ""] + [f"• *{i.get('short', i['place'])}:* {i['headline']}" for i in items[:5]]
    if d.get("cases"):
        wa += ["", f"Still waiting: {len(d['cases'])} people and groups held for a long time, with days counted."]
    wa += ["", f"Sources for every fact, in the full edition: {ed}"]
    for fc in d.get("focus", []):
        wa += [f"In focus · {fc['title']}: {SITE}focus/{fc['slug']}.html"]
    open(os.path.join(out, "whatsapp.txt"), "w").write("\n".join(wa) + "\n")
    x = [f"Resistance Daily · {dt.strftime('%d %b')}", ""] + [f"{i.get('short', i['place'])}: {i['headline']}{via(i['src'])}" for i in items[:4]]
    x_post(out, x + ["", "Every fact sourced:"], ed)


def facebook_focus(f, out, wn):
    url = f"{SITE}focus/{f['slug']}.html"
    when = datetime.date.fromisoformat(wn["date"]).strftime("%d %b") if wn else ""
    lines = [f"Focus update · {when} · {f['title']}" if wn else f"Focus · {f['title']}", "",
             (f"What's new: {wn['text']}" if wn else f["dek"]), "",
             f"The full story, with photos and a source for every fact: {url}", "",
             "Non-partisan. Rights, not parties.", "", " ".join(f.get("instagram", {}).get("hashtags", [])[:4])]
    open(os.path.join(out, "facebook-post.txt"), "w").write("\n".join(lines).rstrip() + "\n")
    lead = f"Update {when} · {f['title']}" if wn else f"Focus · {f['title']}"
    body = wn["text"] if wn else f["dek"]
    open(os.path.join(out, "whatsapp.txt"), "w").write(f"*{lead}*\n\n{body}\n\nFull story, every fact sourced: {url}\n")
    if len(lead) + len(body) + 2 + 1 + 23 > 280:
        # Never cut the what's-new text part-way: it may drop the official response. Point to the page instead.
        print('note: "whats_new" is too long for X; keep it under ~220 characters. x-post.txt links the page only.', file=sys.stderr)
        body = "What's new, with a source for every fact:"
    x_post(out, [lead, "", body], url)


def render(slides, out, prefix):
    from playwright.sync_api import sync_playwright
    face = fonts()
    os.makedirs(out, exist_ok=True)
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium") if os.path.exists("/opt/pw-browsers/chromium") else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(slides, 1):
            f = os.path.join(out, f"_s{i}.html")
            open(f, "w").write(f"<!doctype html><html><head><meta charset=utf-8><style>{face}{CSS}</style></head><body>{s}</body></html>")
            pg.goto("file://" + f); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            bad = pg.evaluate("[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src)")
            if bad:
                print("WARNING: image did not load:", bad, file=sys.stderr)
            path = os.path.join(out, f"{prefix}-slide{i}.jpg")
            pg.screenshot(path=path, type="jpeg", quality=82)
            paths.append(path); os.remove(f)
        b.close()
    from PIL import Image
    n = len(paths); cols = 3; rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (360 * cols, 450 * rows), "white")
    for i, pth in enumerate(paths):
        sheet.paste(Image.open(pth).resize((360, 450)), ((i % cols) * 360, (i // cols) * 450))
    sheet.save(os.path.join(out, "contact.png"))
    return paths


# Daily cover styles rotate by IST weekday so the profile grid doesn't repeat one look all week.
# data/DATE.slides.json may set "cover_style" to override. Every style keeps text inside x 110-970 (the 3:4 grid crop),
# the date as the largest element, the tagline, 4 place/headline rows and the "Swipe" footer.
COVER_ROTATION = ["photo", "paper", "signal", "night", "photo", "paper", "sunday"]  # Mon..Sun
# Owner's requests: the mosaic cover every day 23–29 Oct, then the photo cover every day 30 Oct–5 Nov,
# then back to the rotation.
COVER_PERIODS = [("2026-10-23", "2026-10-29", "mosaic"), ("2026-10-30", "2026-11-04", "photo"),
                 ("2026-11-05", "2099-12-31", "threads")]   # Threads redesign: one calm cover every day from 5 Nov
TAGLINE = "What happened to people's rights in the last 24 hours. Every fact sourced."


# Owner's rule (1 Nov 2026): Sunday keeps the layout of the current week's cover, but in white (light panel, red place
# names, "+ Still waiting"). Layouts with a dark panel map to their light Sunday version; others keep their layout.
SUNDAY_LIGHT = {"photo": "photo-sunday", "night": "sunday"}


def cover_style(dt, sp):
    if sp.get("cover_style"):
        return sp["cover_style"]
    period = next((s for a, b, s in COVER_PERIODS if a <= dt.isoformat() <= b), None)
    if period:
        return SUNDAY_LIGHT.get(period, period) if dt.weekday() == 6 else period
    return COVER_ROTATION[dt.weekday()]


def cover(dt, sp, by, N):
    style = cover_style(dt, sp)
    day, date = dt.strftime("%A"), dt.strftime("%d %b")
    foot = "Swipe → · Sources: link in bio"
    mono = "font:500 24px 'IBM Plex Mono';text-transform:uppercase;letter-spacing:.06em"
    brand = lambda c: f'<span style="color:{c};display:flex;align-items:center;gap:14px"><i style="display:inline-block;width:44px;height:8px;background:{AC}"></i>Resistance Daily</span>'
    # Cover row k goes with story k: its photo (when big enough) or its key figure fills the circle.
    pics = []
    for k in range(4):
        st = sp["stories"][k] if k < len(sp["stories"]) else {}
        ph = pic(st, by) if st else None
        pics.append((ph if ph and big_enough(ph, 600) else None, st.get("fig", "")))

    def disc(k, d, ring=AC):
        ph, fig = pics[k]
        inner = (f'<img src="{E(src_url(ph))}" alt="" style="width:100%;height:100%;object-fit:cover;object-position:{E(ph.get("pos", "center"))}">'
                 if ph else f'<span class="D" style="font-size:{int(d * .42)}px;color:#fff">{E(fig)}</span>')
        return (f'<div style="position:relative;width:{d}px;height:{d}px;flex:none"><div style="width:100%;height:100%;border-radius:50%;overflow:hidden;'
                f'border:8px solid {ring};background:{RED};display:grid;place-items:center">{inner}</div>'
                f'<span style="position:absolute;left:0;top:0;width:58px;height:58px;border-radius:50%;background:{INK};color:#fff;border:4px solid {ring};'
                f'display:grid;place-items:center;font:800 30px \'Barlow Condensed\'">{k + 1}</span></div>')

    def credits():
        cs = [f'{k + 1}: {ph["credit"].split(" / ")[0]}, {ph["licence"]}, {ph["year"]}' for k, (ph, _) in enumerate(pics) if ph]
        return f'File photos · {" · ".join(cs)}' if cs else ""

    if style == "threads":
        # "Where things stand today · Wed 4 Nov": cream ground, washed arch photo of the first story, 4 place rows.
        p = next((pic(st, by) for st in sp["stories"] if pic(st, by) and big_enough(pic(st, by), 600)), None)
        dd = dt.strftime("%a %d %b").replace(" 0", " ")
        rows = "".join(f'<div style="border-top:2px solid rgba(32,30,29,.16);padding:16px 0 14px"><div style="font:600 24px Figtree;text-transform:uppercase;'
                       f'letter-spacing:.06em;color:{AC_T}">{E(pl)}</div><div style="font:400 38px/1.15 Caprasimo;margin-top:6px">{E(h)}</div></div>'
                       for pl, h in sp["cover"])
        arch = (f'<div style="position:relative;height:330px;margin-top:26px;border-radius:165px 165px 36px 36px;overflow:hidden;flex:none">'
                f'<img src="{E(src_url(p))}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{E(p.get("pos", "center"))}"></div>') if p else ""
        cred = f' · {E(label(p))} · {E(p["credit"].split(" / ")[0])}' if p else ""
        return f'''<div class="s light" style="padding:80px 110px 70px">
<div class="top">{brand(INK)}<span>1 / {N}</span></div>
<div style="font:600 26px Figtree;text-transform:uppercase;letter-spacing:.08em;color:{AC_T};margin-top:40px">Where things stand today</div>
<div style="font:400 120px/1 Caprasimo;margin-top:8px">{E(dd)}</div>{arch}
<div style="margin-top:20px">{rows}</div>
<div style="margin-top:auto;padding-top:18px;font:600 21px Figtree;color:#645c50;text-transform:uppercase;letter-spacing:.05em">{foot}{cred}</div></div>'''
    if style == "circles":
        # Four round photo windows in a 2x2 grid under the date; place and headline beneath each circle.
        cells = "".join(f'<div style="display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px">{disc(k, 220)}'
                        f'<div class="D" style="font-size:46px;color:{RED};margin-top:6px">{E(pl)}</div>'
                        f'<div style="font:600 29px/1.25 \'IBM Plex Sans\';max-width:400px">{E(h)}</div></div>' for k, (pl, h) in enumerate(sp["cover"]))
        return f'''<div class="s light" style="padding:80px 110px 60px">
<div class="top">{brand(INK)}<span>1 / {N}</span></div>
<div style="display:flex;align-items:flex-end;gap:26px;margin-top:26px"><div class="D" style="font-size:170px">{date}</div><div class="D" style="font-size:60px;color:{AC};padding-bottom:14px">{day}</div></div>
<p style="font-size:27px;color:#5b616b;margin:10px 0 26px;line-height:1.35">{TAGLINE}</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:26px 40px">{cells}</div>
<div style="margin-top:auto;padding-top:16px;border-top:2px solid #d9dcd8;{mono};font-size:17px;color:#5b616b;line-height:1.5">{foot}<br>{E(credits())}</div></div>'''
    if style == "mosaic":
        # Four photo quarters edge to edge; the date sits in a circle where they meet.
        pos = [("left:0;top:0", "left"), ("right:0;top:0", "right"), ("left:0;bottom:0", "left"), ("right:0;bottom:0", "right")]
        tiles = ""
        for k, (pl, h) in enumerate(sp["cover"]):
            ph, fig = pics[k]
            bg = (f'<img src="{E(src_url(ph))}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{E(ph.get("pos", "center"))}">'
                  if ph else f'<div class="D" style="position:absolute;inset:0;display:grid;place-items:center;font-size:220px;color:rgba(255,255,255,.25)">{E(fig)}</div>')
            side, al = pos[k]
            top = k < 2
            txt = (f'<div style="position:absolute;{"top:150px" if top else "bottom:150px"};{"left:110px" if al == "left" else "right:110px"};width:360px;text-align:{al}">'
                   f'<div class="D" style="font-size:50px;color:{AC}">{k + 1} · {E(pl)}</div><div style="font:600 29px/1.25 \'IBM Plex Sans\';margin-top:6px">{E(h)}</div></div>')
            shade = "linear-gradient(rgba(0,0,0,.85),rgba(0,0,0,.35) 60%,rgba(0,0,0,.55))" if top else "linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,.35) 40%,rgba(0,0,0,.85))"
            tiles += (f'<div style="position:absolute;{side};width:539px;height:674px;overflow:hidden;background:{RED if not ph else INK}">{bg}'
                      f'<div style="position:absolute;inset:0;background:{shade}"></div></div>')
            tiles += txt
        return f'''<div class="s dark" style="padding:0;color:#fff">{tiles}
<div style="position:absolute;left:110px;right:110px;top:70px" class="top"><span style="color:#fff;display:flex;align-items:center;gap:14px"><i style="display:inline-block;width:44px;height:8px;background:{AC}"></i>Resistance Daily</span><span style="color:#e6e6e6">1 / {N}</span></div>
<div style="position:absolute;left:290px;top:425px;width:500px;height:500px;border-radius:50%;background:{AC};color:{INK};border:10px solid {INK};display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
<div class="D" style="font-size:58px;color:#fff">{day}</div><div class="D" style="font-size:150px">{date}</div>
<p style="font:600 23px/1.3 'IBM Plex Sans';max-width:330px;margin-top:10px">{TAGLINE}</p></div>
<div style="position:absolute;left:110px;right:110px;bottom:40px;{mono};font-size:17px;color:#d0d0d0;line-height:1.5">{foot}{" · " + E(credits()) if credits() else ""}</div></div>'''
    if style == "ring":
        # Type-only: the date in a big ring at the centre, the four stories in the corners around it.
        def corner(k, pl, h):
            al = "left" if k % 2 == 0 else "right"
            return (f'<div style="text-align:{al};width:380px;{"justify-self:end" if al == "right" else ""}">'
                    f'<div style="display:flex;{"flex-direction:row-reverse;" if al == "right" else ""}align-items:center;gap:14px">'
                    f'<span style="width:62px;height:62px;border-radius:50%;background:{RED};color:#fff;display:grid;place-items:center;font:800 36px \'Barlow Condensed\';flex:none">{k + 1}</span>'
                    f'<span class="D" style="font-size:52px;color:{AC}">{E(pl)}</span></div>'
                    f'<div style="font:600 30px/1.25 \'IBM Plex Sans\';margin-top:10px">{E(h)}</div></div>')
        c = [corner(k, pl, h) for k, (pl, h) in enumerate(sp["cover"])]
        return f'''<div class="s dark" style="padding:80px 110px 60px">
<div class="top">{brand(BG)}<span>1 / {N}</span></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:50px">{c[0]}{c[1]}</div>
<div style="align-self:center;margin:auto 0;width:600px;height:600px;border-radius:50%;border:14px solid {AC};display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
<div class="D" style="font-size:70px;color:{AC}">{day}</div><div class="D" style="font-size:185px">{date}</div>
<p style="font-size:26px;color:#9ba1aa;max-width:380px;line-height:1.35;margin-top:10px">{TAGLINE}</p></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:40px">{c[2]}{c[3]}</div>
<div style="border-top:2px solid #333840;padding-top:18px;{mono};color:#9ba1aa">{foot}</div></div>'''
    if style in ("photo", "photo-sunday"):
        # Lead story's photo fills the top; date sits on it, rows on a solid panel below. Falls back to "night".
        p = next((pic(st, by) for st in sp["stories"] if pic(st, by) and big_enough(pic(st, by))), None)
        if not p and style == "photo":
            style = "night"
        else:
            # "photo-sunday" without a photo keeps the same layout, with a plain dark block where the photo goes.
            # "photo-sunday": the same layout on a light panel with red place names and the "+ Still waiting" tag.
            sun = style == "photo-sunday"
            # Light panel: the photo keeps a dark lower edge (no fade to white) so the white date stays readable.
            rule, place, fade = ("#d9dcd8", RED, "rgba(0,0,0,.7)") if sun else ("#333840", AC, INK)
            tag = f' · <span style="color:{RED}">+ Still waiting</span>' if sun else ""
            img = (f'<img src="{E(src_url(p))}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{E(p.get("pos", "center"))}">' if p else "")
            cred = f' · {E(label(p))} · {E(p["credit"].split(" / ")[0])}, {E(p["licence"])}' if p else ""
            rows = "".join(f'<div style="border-top:2px solid {rule};padding:16px 0 14px"><div class="D" style="font-size:52px;color:{place}">{E(pl)}</div><div style="font:600 32px \'IBM Plex Sans\';margin-top:6px">{E(h)}</div></div>' for pl, h in sp["cover"])
            return f'''<div class="s {'light' if sun else 'dark'}" style="padding:0">
<div style="position:relative;height:590px;flex:none;background:{INK}">{img}
<div style="position:absolute;inset:0;background:linear-gradient(rgba(0,0,0,.7),rgba(0,0,0,.08) 28%,rgba(0,0,0,.6) 62%,{fade})"></div>
<div style="position:absolute;inset:0;padding:80px 110px 30px;display:flex;flex-direction:column">
<div class="top" style="color:#e6e6e6">{brand("#fff")}<span>1 / {N}</span></div>
<div style="margin-top:auto"><div class="D" style="font-size:64px;color:{AC}">{day}</div><div class="D" style="font-size:190px;color:#fff">{date}</div></div></div></div>
<div style="padding:10px 110px 70px;display:flex;flex-direction:column;flex:1">
<p style="font-size:28px;color:{'#5b616b' if sun else '#9ba1aa'};margin:0 0 16px;line-height:1.35">{TAGLINE}</p>{rows}
<div style="margin-top:auto;border-top:2px solid {rule};padding-top:18px;{mono};color:{'#5b616b' if sun else '#9ba1aa'}">{foot}{tag}{cred}</div></div></div>'''
    if style == "paper":
        # Newspaper front: light paper, heavy rules, numbered rows.
        rows = "".join(f'<div style="display:grid;grid-template-columns:86px 1fr;gap:8px;border-top:2px solid {INK};padding:18px 0 16px"><div class="D" style="font-size:64px;color:{RED}">{k:02d}</div><div><div class="D" style="font-size:52px">{E(pl)}</div><div style="font:400 33px \'IBM Plex Sans\';margin-top:6px;color:#3a3f47">{E(h)}</div></div></div>' for k, (pl, h) in enumerate(sp["cover"], 1))
        return f'''<div class="s light" style="padding:90px 110px;background:#fbfaf6">
<div class="top">{brand(INK)}<span>1 / {N}</span></div>
<div style="border-top:10px solid {INK};border-bottom:2px solid {INK};margin-top:36px;padding:14px 0 10px;display:flex;justify-content:space-between;align-items:baseline">
<span class="D" style="font-size:60px;color:{RED}">{day}</span><span style="{mono};color:#5b616b">The last 24 hours</span></div>
<div class="D" style="font-size:220px;margin-top:20px">{date}</div>
<p style="font-size:30px;color:#5b616b;margin:16px 0 30px;line-height:1.35">{TAGLINE}</p>{rows}
<div style="margin-top:auto;border-top:10px solid {INK};padding-top:18px;{mono};color:#5b616b">{foot}</div></div>'''
    if style == "signal":
        # Orange poster: ink type on the accent colour.
        rows = "".join(f'<div style="border-top:3px solid {INK};padding:18px 0 16px"><div class="D" style="font-size:60px;color:#fff">{E(pl)}</div><div style="font:600 34px \'IBM Plex Sans\';margin-top:6px;color:{INK}">{E(h)}</div></div>' for pl, h in sp["cover"])
        return f'''<div class="s" style="padding:90px 110px;background:{AC};color:{INK}">
<div class="top" style="color:{INK}"><span style="display:flex;align-items:center;gap:14px"><i style="display:inline-block;width:44px;height:8px;background:{INK}"></i>Resistance Daily</span><span>1 / {N}</span></div>
<div class="D" style="font-size:240px;margin-top:40px;line-height:.82">{date}</div>
<div class="D" style="font-size:76px;color:#fff;margin-top:8px">{day}</div>
<p style="font-size:30px;margin:20px 0 26px;line-height:1.35;font-weight:600">{TAGLINE}</p>{rows}
<div style="margin-top:auto;border-top:3px solid {INK};padding-top:18px;{mono}">{foot}</div></div>'''
    # "night" (the original dark cover) and "sunday" (light, red, with the Still waiting tag)
    sunday = style == "sunday"
    rows = "".join(f'<div style="border-top:2px solid {"#d9dcd8" if sunday else "#333840"};padding:20px 0 18px"><div class="D" style="font-size:64px;color:{RED if sunday else AC}">{E(pl)}</div><div style="font:600 36px \'IBM Plex Sans\';margin-top:8px">{E(h)}</div></div>' for pl, h in sp["cover"])
    tag = f' · <span style="color:{RED}">+ Still waiting</span>' if sunday else ""
    return f'''<div class="s {'light' if sunday else 'dark'}" style="padding:90px 110px">
<div class="top">{brand(INK if sunday else BG)}<span>1 / {N}</span></div>
<div class="D" style="font-size:76px;color:{AC};margin-top:46px">{day}</div>
<div class="D" style="font-size:200px">{date}</div>
<p style="font-size:30px;color:#9ba1aa;margin:22px 0 26px;line-height:1.35">{TAGLINE}</p>
{rows}
<div style="margin-top:auto;border-top:2px solid {"#d9dcd8" if sunday else "#333840"};padding-top:20px;{mono};color:#9ba1aa">{foot}{tag}</div></div>'''


# "Need hope?" (owner's request, 4 Nov 2026): a green sticker on every daily cover points to the last slide, which
# lists the latest items from data/hope.json (tools/hope.py). Sticker positions keep it beside the date and inside the
# middle 860px (x 110-970) that the profile grid shows.
STICKER_AT = {"threads": (800, 520, 190), "photo": (725, 330), "photo-sunday": (725, 330), "night": (735, 160), "sunday": (735, 160), "paper": (765, 262, 200),
              "signal": (765, 175, 200), "mosaic": (760, 330), "ring": (735, 120), "circles": (735, 60)}  # (left, top[, size])
GREEN_L = SAGE


def hope_items(dt, days=14, n=3):
    p = os.path.join(root, "data", "hope.json")
    if not os.path.exists(p):
        return []
    items = [i for i in json.load(open(p))["items"] if 0 <= (dt - datetime.date.fromisoformat(i["date"])).days < days]
    return sorted(items, key=lambda i: i["date"], reverse=True)[:n]


def focus_hope(slug, n=3):
    """Signs of hope for a Focus carousel: items linked to this Focus ("link" -> focus/SLUG.html) first, then the
    latest ones from the past 14 days, up to n."""
    p = os.path.join(root, "data", "hope.json")
    if not os.path.exists(p):
        return []
    items = json.load(open(p))["items"]
    mine = sorted([i for i in items if (i.get("link") or ["", ""])[1].endswith(f"focus/{slug}.html")], key=lambda i: i["date"], reverse=True)
    rest = [i for i in hope_items(ist_today(), n=n + len(mine)) if i not in mine]
    return (mine + rest)[:n]


def ist_today():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date()


def sticker(style):
    x, y, *z = STICKER_AT.get(style, (735, 160))
    z = z[0] if z else 230
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{z}px;height:{z}px;border-radius:50%;background:{GR};color:#fff;'
            f'display:grid;place-content:center;text-align:center;box-shadow:0 0 0 8px rgba(255,255,255,.92);transform:rotate(-8deg);z-index:5">'
            f'<b class="D" style="font-size:{round(z * .226)}px;line-height:.9">Need<br>hope?</b>'
            f'<span style="font:500 {round(z * .083)}px \'IBM Plex Mono\';text-transform:uppercase;letter-spacing:.05em;margin-top:8px">Last slide →</span></div>')


def hope_slide(items, N):
    rows = "".join(f'<div style="border-left:8px solid {GR};padding:6px 0 6px 26px"><b class="D" style="display:block;font-size:46px;line-height:1">{E(i.get("slide_head") or i["fig"])}</b>'
                   f'<span style="display:block;font-size:27px;color:#3d472b;margin-top:6px;line-height:1.3">{E(i["slide"])}</span></div>' for i in items)
    srcs = " · ".join(dict.fromkeys(n for i in items for n, _ in i["src"]))
    return f'''<div class="s" style="background:{GREEN_L};color:{SAGE_T}"><div class="top" style="color:{GR}"><span>Need hope?</span><span style="color:#5b616b">{N} / {N}</span></div>
<div class="D" style="font-size:150px;line-height:.86;margin-top:60px">Signs of<br><span style="color:{GR}">hope</span></div>
<p style="font-size:30px;color:#3d472b;margin-top:20px">Rights upheld lately. Every fact sourced.</p>
<div style="margin-top:50px;display:grid;gap:26px">{rows}</div>
<div style="margin-top:auto;border-top:2px solid #b7d6c2;padding-top:20px;font:500 22px 'IBM Plex Mono';color:#3d472b;text-transform:uppercase;letter-spacing:.05em">More signs of hope: link in bio · Sources: {E(srcs)}</div></div>'''


def daily(date, out):
    d = json.load(open(os.path.join(root, "data", f"{date}.json")))
    sp = json.load(open(os.path.join(root, "data", f"{date}.slides.json")))
    by = {i["n"]: i for i in d["items"]}
    dt = datetime.date.fromisoformat(date)
    hope = hope_items(dt)
    N = 7 if hope else 6
    c = cover(dt, sp, by, N)
    if hope:  # the sticker sits inside the cover's outer box (its last closing tag)
        c = c[:c.rstrip().rfind("</div>")] + sticker(cover_style(dt, sp)) + "</div>"
    slides = [c]
    for k, st in enumerate(sp["stories"], 2):
        b = "".join(f"<li>{E(x)}</li>" for x in st["bullets"])
        p = pic(st, by)
        if p and not big_enough(p):
            print(f"note: photo for item {st['n']} is too small for a slide; showing its key figure instead", file=sys.stderr)
            p = None
        it = by.get(st.get("n"), {})
        # Threads redesign: kicker = the item's thread name (else the slide label), a washed arch photo (or the key
        # figure), the calm word tag, the headline, bullets and sources. Upheld items sit on the sage ground.
        tname, tg, up = st["label"], None, False
        if it:
            sys.path.insert(0, os.path.join(root, "tools"))
            import threads as T
            regs = {t["slug"]: t for t in T.registry()}
            s_ = T.thread_of(it)
            tname = regs[s_]["name"] if s_ in regs else st["label"].split("·")[0].strip()
            tg = T.tag(it, date)
            up = T.upheld(it, date)
        cls = {"tag tag-accent-2": "tag up", "tag tag-accent": "tag acc"}.get(tg[1], "tag") if tg else "tag"
        tags = (f'<span class="{cls}">{E(tg[0])}</span>' if tg else "") + f'<span>{E(st["place"])}</span>'
        arch = (f'<div class="arch"><img src="{E(src_url(p))}" alt="" style="object-position:{E(p.get("pos", "center"))}"><span class="ptag">{E(label(p))}</span></div>'
                if p else f'<div class="arch fp"><b>{E(st["fig"])}</b><span>{E(st["figlab"])}</span></div>')
        slides.append(f'''<div class="s st{" up" if up else " light"}"><div class="k"><span>{E(tname)}</span><span>{k} / {N}</span></div>
{arch}<div class="tags">{tags}</div><h2>{E(st["head"])}</h2><ul>{b}</ul>
<div class="srcs">Sources: {E(st["src"])}{"<br>" + E(credit(p)) if p else ""}</div></div>''')
    acts = "".join(f'<div class="act"><b>{E(t)}</b><span>{E(s)}</span></div>' for t, s in d["acts"])
    slides.append(f'''<div class="s dark">{top("Act today", N - 1 if hope else N, N)}<div class="D" style="font-size:150px;margin-top:60px">Act today</div>
<div class="D" style="font-size:64px;color:{AC};margin-top:10px">Whatever your politics</div><div style="margin-top:30px">{acts}</div>
<div style="margin-top:auto;border-top:2px solid #333840;padding-top:20px;font:500 24px 'IBM Plex Mono';color:#9ba1aa;text-transform:uppercase;letter-spacing:.04em">Non-partisan · Every fact sourced · Full edition: link in bio</div></div>''')
    if hope:
        slides.append(hope_slide(hope, N))
    for p in render(slides, out, date):
        print(p)
    # Per-slide captions (owner's style: only what the slide doesn't show). Slide 1 uses the post caption
    # (OUTDIR/caption.txt, written by the routine); each story slide carries its item's full text (headline, bullets
    # and sources are on the slide); slide 6 shows everything already, so it has no caption.
    cp = os.path.join(out, "caption.txt")  # write caption.txt into OUTDIR first and it becomes slide 1's caption
    caps = [open(cp).read().strip() if os.path.exists(cp) else "(Use caption.txt as the caption for slide 1.)"]
    for st in sp["stories"]:
        it = by.get(st.get("n"), {})
        caps.append(st.get("caption") or it.get("text", ""))  # "caption" for slides not tied to an item (Sunday cases)
    caps.append("")
    if hope:  # the hope slide: "hope_caption" in DATE.slides.json, or a short pointer to the page
        caps.append(sp.get("hope_caption") or "Not every story this week was bad news: courts, communities and neighbours are holding the line. "
                    "Every card on our Signs of hope page has its source: link in bio.\nSource: " + " · ".join(dict.fromkeys(n for i in hope for n, _ in i["src"])))
    write_captions(out, caps)
    facebook_daily(d, out)
    social_daily(d, out)


def focus(slug, out, update=False):
    f = json.load(open(os.path.join(root, "data", "focus", f"{slug}.json")))
    wn = f.get("whats_new") if update else None
    if update and not wn:
        sys.exit("--update needs a \"whats_new\" entry in the Focus JSON")
    when = datetime.date.fromisoformat(wn["date"]).strftime("%d %b") if wn else ""
    ph = f["photos"][:7]
    hope = focus_hope(slug)  # "Need hope?" (owner's rule): Focus carousels end on Signs of hope too
    N = len(ph) + 2 + (1 if hope else 0)
    END = len(ph) + 2  # the "Read the full story" slide
    first = ph[0]
    slides = [f'''<div class="s full"><img src="{E(src_url(first))}" alt="" style="object-position:{E(first.get("pos", "center"))}"><div class="shade"></div>
<div class="in"><div class="top"><span style="display:flex;align-items:center;gap:14px;color:#fff"><i style="display:inline-block;width:44px;height:8px;background:{AC}"></i>Resistance Daily · Focus</span><span>1 / {N}</span></div>
<div style="margin-top:auto;display:grid;gap:20px">{f'<span class="kick on" style="background:{RED};color:#fff">Update · {E(when)}</span>' if wn else ''}<span class="kick on">{E(f["kicker"].replace("Focus · ", ""))}</span>
<div class="D" style="font-size:132px">{E(f.get("short", f["title"]))}</div><p style="font-size:34px;line-height:1.35;color:#e8e8e8">{E(wn["text"] if wn else f["dek"])}</p>
<div style="font:500 22px 'IBM Plex Mono';color:#cfcfcf;text-transform:uppercase;letter-spacing:.06em;border-top:2px solid rgba(255,255,255,.3);padding-top:18px">Swipe for photos → · {E(label(first))} · {E(credit(first))}</div></div></div></div>''']
    if hope:  # the sticker sits inside the cover's outer box, top right, clear of the title at the bottom
        slides[0] = slides[0][:slides[0].rstrip().rfind("</div>")] + sticker("night") + "</div>"
    for k, p in enumerate(ph[1:], 2):
        slides.append(f'''<div class="s pslide"><div class="pimg full"><img src="{E(src_url(p))}" alt="" style="object-position:{E(p.get("pos", "center"))}">
<div style="position:absolute;inset:0 0 auto 0;height:240px;background:linear-gradient(rgba(0,0,0,.7),rgba(0,0,0,0))"></div>
<div class="in" style="height:auto;padding-bottom:0">{top("Focus · " + f.get("short", f["title"]), k, N)}</div></div>
<div class="pcap"><span class="kick" style="font-size:22px">{E(label(p))}</span><p>{E(p["caption"])}</p><span class="cr">{E(credit(p))}</span></div></div>''')
    figs = "".join(f'<div class="fig"><b>{E(x["fig"])}</b><span>{E(x["figcap"])}</span></div>' for x in f.get("figs", [])[:4])
    srcs = sorted({x["src"][0] for x in f.get("figs", [])})
    # Every slide carries a photo (owner's rule): the key-numbers slide opens with a photo band and the last slide
    # sits on a shaded photo. "numbers_photo" / "end_photo" pick them by index in "photos" (default: the cover).
    kp = f["photos"][f.get("numbers_photo", 0)]
    ep = f["photos"][f.get("end_photo", 0)]
    slides.append(f'''<div class="s light" style="padding:0"><div class="full" style="position:relative;height:380px;flex:none"><img src="{E(src_url(kp))}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{E(kp.get("pos", "center"))}">
<div style="position:absolute;inset:0 0 auto 0;height:220px;background:linear-gradient(rgba(0,0,0,.8),rgba(0,0,0,0))"></div><div class="in" style="position:relative;height:auto;padding:90px 84px 0;color:#fff">{top("Focus · Key numbers", len(ph) + 1, N)}</div>
<span style="position:absolute;left:84px;bottom:18px;font:500 18px 'IBM Plex Mono';color:#fff;background:rgba(0,0,0,.55);padding:6px 12px;line-height:1.45">{E(label(kp))} · {E(credit(kp))}</span></div>
<div style="padding:40px 84px 64px;display:flex;flex-direction:column;flex:1"><div class="D" style="font-size:80px">{E(f.get("short", f["title"]))}</div>
<div class="figs" style="margin-top:34px">{figs}</div><div class="srcs">Sources: {E(" · ".join(srcs))}</div></div></div>''')
    ig = f.get("instagram", {})
    # Last slide (owner's rule): one short line on the official position ("instagram": {"official_short"}), not the
    # full paragraph, which stays on the website.
    off = ig.get("official_short") or f.get("official", {}).get("text", "").split(". ")[0].rstrip(".") + "."
    if not ig.get("official_short") and f.get("official"):
        print('note: add "instagram": {"official_short": "..."} (one sentence) for the last slide', file=sys.stderr)
    slides.append(f'''<div class="s full"><img src="{E(src_url(ep))}" alt="" style="object-position:{E(ep.get("pos", "center"))};filter:brightness(.55)"><div class="shade"></div><div class="in">{top("Focus · Full story", END, N)}<div class="D" style="font-size:120px;margin-top:60px">Read the full story</div>
<p style="font-size:34px;line-height:1.4;color:#d0d3d8;margin-top:34px">The full story, with a source for every fact, is on our website.</p>
<div style="margin-top:40px;border-left:8px solid {GR};padding:10px 0 10px 26px"><b style="font:800 46px 'Barlow Condensed';text-transform:uppercase;display:block">Link in bio</b>
<span style="font:500 26px 'IBM Plex Mono';color:#9ba1aa">resistancedaily.github.io/focus/{E(slug)}</span></div>
{f'<p style="font-size:32px;line-height:1.4;color:#b8bcc2;margin-top:44px"><b style="font:500 22px IBM Plex Mono;text-transform:uppercase;letter-spacing:.06em;color:#9ba1aa;display:block;margin-bottom:8px">Official position</b>{E(off)}</p>' if off else ''}
<div style="margin-top:auto;border-top:2px solid #333840;padding-top:20px;font:500 22px 'IBM Plex Mono';color:#9ba1aa;text-transform:uppercase;letter-spacing:.04em">Non-partisan · Every fact sourced<br><span style="text-transform:none">{E(label(ep))} · {E(credit(ep))}</span></div></div></div>''')
    if hope:
        slides.append(hope_slide(hope, N))
    for p in render(slides, out, f"focus-{slug}"):
        print(p)
    # One caption per slide: the cover carries the post caption; each later slide carries part of the story, so the
    # story reads in order as people swipe. Story paragraphs fill the photo slides, then the key-numbers slide.
    # Owner's style: a caption carries only what its slide doesn't already show. Slide 1: "Focus · title", the swipe
    # line, what the first photo shows, at most 5 hashtags. Photo slides: the story paragraph, then "Sources: …".
    # Key-numbers slide: the story paragraph only (numbers and sources are on the slide). Last slide: the sources
    # of the official position (the position and link are on the slide).
    def srcs_of(pairs):
        return "Sources: " + " · ".join(dict.fromkeys(n for n, u in pairs))  # each outlet named once
    story = list(f["story"])
    slots = len(ph) - 1 + 1  # photo slides 2..len(ph), then the key-numbers slide
    per = [story[i:i + 1] for i in range(min(slots - 1, len(story)))]
    per.append(story[slots - 1:] if len(story) >= slots else [])
    per += [[] for _ in range(slots - len(per))]
    caps = [(f"Focus update · {when} · {f['title']}\n\n" if wn else f"Focus · {f['title']}\n\n") + f"""Swipe: each slide's caption tells the next part of the story.

{first['caption']}

{' '.join(ig.get('hashtags', [])[:5])}"""]
    for k, p in enumerate(ph[1:]):
        body = "\n\n".join(f"{x['text']}\n{srcs_of(x['src'])}" for x in per[k])
        caps.append(body)
    shown = set(srcs)  # sources printed on the key-numbers slide
    caps.append("\n\n".join(x["text"] + ("" if {n for n, u in x["src"]} <= shown else "\n" + srcs_of(x["src"]))
                              for x in per[-1]))
    caps.append(srcs_of(f["official"]["src"]) if off else "")
    hope_cap = (ig.get("hope_caption") or "Not every story is bad news: courts, communities and neighbours are holding the line. "
                "Every card on our Signs of hope page has its source: link in bio.\nSource: "
                + " · ".join(dict.fromkeys(n for i in hope for n, _ in i["src"]))) if hope else None
    if hope:
        caps.append(hope_cap)
    if ig.get("slide_captions"):  # owner's rule: short hand-written captions, one per slide, win when given
        sc = list(ig["slide_captions"])
        if hope and len(sc) == END:  # captions written for the slides before Signs of hope: add its caption
            sc.append(hope_cap)
        if len(sc) != N:
            sys.exit(f'"slide_captions" has {len(ig["slide_captions"])} entries; this carousel has {N} slides')
        caps = sc
    else:
        print('note: no "instagram": {"slide_captions"}; using the long story paragraphs as captions', file=sys.stderr)
    open(os.path.join(out, "caption.txt"), "w").write(caps[0] + "\n")
    write_captions(out, caps)
    facebook_focus(f, out, wn)
    alts = [f"Slide 1: {first['alt']} " + (f"Update, {when}. Title: {f['title']}. {wn['text']}" if wn else f"Title: {f['title']}. {f['dek']}")]
    alts += [f"Slide {k}: {p['alt']} {p['caption']}" for k, p in enumerate(ph[1:], 2)]
    alts.append(f"Slide {len(ph) + 1}: Key numbers. " + "; ".join(f"{x['fig']} {x['figcap']}" for x in f.get("figs", [])[:4]) + ".")
    alts.append(f"Slide {END}: Read the full story at resistancedaily.github.io/focus/{slug}, link in bio." + (f" Official position: {off}" if off else ""))
    if hope:
        alts[0] += " A green sticker reads: Need hope? Last slide."
        alts.append(f"Slide {N}: Signs of hope. " + "; ".join(f"{i.get('slide_head') or i['fig']}: {i['slide']}" for i in hope) + ".")
    open(os.path.join(out, "alt-text.txt"), "w").write("\n\n".join(alts) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] not in ("daily", "focus"):
        sys.exit(__doc__)
    if sys.argv[1] == "daily":
        daily(sys.argv[2], sys.argv[3])
    else:
        focus(sys.argv[2], sys.argv[3], update="--update" in sys.argv[4:])
