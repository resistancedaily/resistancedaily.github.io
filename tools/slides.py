#!/usr/bin/env python3
"""Resistance Daily Instagram slides (1080x1350 JPEG).

  python3 tools/slides.py daily DATE OUTDIR      reads data/DATE.json and data/DATE.slides.json
  python3 tools/slides.py focus SLUG OUTDIR      reads data/focus/SLUG.json

data/DATE.slides.json (the text-led daily carousel; a story slide shows its item's photo when the item has one):
{ "cover": [[place, headline <= 45 chars], x4],
  "stories": [{"n": item number, "label": "India · Life & safety", "fig", "figlab", "place", "head", "bullets": [2-3], "src": "A · B"}, x4] }

Focus carousels: cover photo + title, one slide per further photo (up to 6), key numbers, then "full story" with credits.
Writes OUTDIR/*.jpg, OUTDIR/contact.png (contact sheet) and OUTDIR/slide-captions.txt (one caption per slide;
Instagram carousels take a caption per photo). For focus also caption.txt (slide 1's caption) and alt-text.txt.
Fonts come from @fontsource packages (npm pack) into build/fonts on first run.
"""
import sys, os, json, glob, html, subprocess, datetime

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(root, "build", "fonts")
PKGS = ["@fontsource/barlow-condensed@5.0.13", "@fontsource/ibm-plex-sans@5.0.20", "@fontsource/ibm-plex-mono@5.0.13"]
BG, INK, AC, RED, GR = "#f3f4f2", "#15181d", "#d9661a", "#b3261e", "#1d7a4c"


def fonts():
    if not glob.glob(os.path.join(FONTS, "*", "package", "files")):
        os.makedirs(FONTS, exist_ok=True)
        subprocess.run(["npm", "pack", "-q", *PKGS], cwd=FONTS, check=True, capture_output=True)
        for t in glob.glob(os.path.join(FONTS, "*.tgz")):
            d = t[:-4]; os.makedirs(d, exist_ok=True)
            subprocess.run(["tar", "xzf", t, "-C", d], check=True)

    def ff(fam, pkg, w):
        path = glob.glob(os.path.join(FONTS, f"fontsource-{pkg}-*", "package", "files", f"{pkg}-latin-{w}-normal.woff2"))[0]
        return f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('file://{path}') format('woff2')}}"
    return "".join([ff("Barlow Condensed", "barlow-condensed", 800), ff("IBM Plex Sans", "ibm-plex-sans", 400),
                    ff("IBM Plex Sans", "ibm-plex-sans", 600), ff("IBM Plex Mono", "ibm-plex-mono", 500)])


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
"""


def top(label, n, N, light=False):
    return f'<div class="top"><span>{E(label)}</span><span>{n} / {N}</span></div>'


def credit(p):
    ch = f" ({p['changes']})" if p.get("changes") else ""
    return f"Photo: {p['credit']}, {p['licence']}{ch}"


def label(p):
    return "Photo from the event" if p.get("kind") == "event" else f"File photo · {p['year']}"


def src_url(p):
    s = p["src"]
    return s if s.startswith(("http://", "https://")) else "file://" + os.path.join(root, s)


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
TAGLINE = "What happened to people's rights in the last 24 hours. Every fact sourced."


def cover(dt, sp, by, N):
    style = sp.get("cover_style") or COVER_ROTATION[dt.weekday()]
    day, date = dt.strftime("%A"), dt.strftime("%d %b")
    foot = "Swipe → · Sources: link in bio"
    mono = "font:500 24px 'IBM Plex Mono';text-transform:uppercase;letter-spacing:.06em"
    brand = lambda c: f'<span style="color:{c};display:flex;align-items:center;gap:14px"><i style="display:inline-block;width:44px;height:8px;background:{AC}"></i>Resistance Daily</span>'
    # Cover row k goes with story k: its photo (when big enough) or its key figure fills the circle.
    pics = []
    for k in range(4):
        st = sp["stories"][k] if k < len(sp["stories"]) else {}
        ph = by.get(st.get("n"), {}).get("photo")
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
<div style="position:absolute;left:110px;right:110px;bottom:40px;{mono};font-size:17px;color:#d0d0d0;line-height:1.5">{foot} · {E(credits())}</div></div>'''
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
    if style == "photo":
        # Lead story's photo fills the top; date sits on it, rows on a solid panel below. Falls back to "night".
        p = next((by.get(st.get("n"), {}).get("photo") for st in sp["stories"]
                  if by.get(st.get("n"), {}).get("photo") and big_enough(by[st["n"]]["photo"])), None)
        if not p:
            style = "night"
        else:
            rows = "".join(f'<div style="border-top:2px solid #333840;padding:16px 0 14px"><div class="D" style="font-size:52px;color:{AC}">{E(pl)}</div><div style="font:600 32px \'IBM Plex Sans\';margin-top:6px">{E(h)}</div></div>' for pl, h in sp["cover"])
            return f'''<div class="s dark" style="padding:0">
<div style="position:relative;height:590px;flex:none"><img src="{E(src_url(p))}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{E(p.get("pos", "center"))}">
<div style="position:absolute;inset:0;background:linear-gradient(rgba(0,0,0,.7),rgba(0,0,0,.08) 28%,rgba(0,0,0,.6) 62%,{INK})"></div>
<div style="position:absolute;inset:0;padding:80px 110px 30px;display:flex;flex-direction:column">
<div class="top" style="color:#e6e6e6">{brand("#fff")}<span>1 / {N}</span></div>
<div style="margin-top:auto"><div class="D" style="font-size:64px;color:{AC}">{day}</div><div class="D" style="font-size:190px;color:#fff">{date}</div></div></div></div>
<div style="padding:10px 110px 70px;display:flex;flex-direction:column;flex:1">
<p style="font-size:28px;color:#9ba1aa;margin:0 0 16px;line-height:1.35">{TAGLINE}</p>{rows}
<div style="margin-top:auto;border-top:2px solid #333840;padding-top:18px;{mono};color:#9ba1aa">{foot} · {E(label(p))} · {E(p["credit"].split(" / ")[0])}, {E(p["licence"])}</div></div></div>'''
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


def daily(date, out):
    d = json.load(open(os.path.join(root, "data", f"{date}.json")))
    sp = json.load(open(os.path.join(root, "data", f"{date}.slides.json")))
    by = {i["n"]: i for i in d["items"]}
    dt = datetime.date.fromisoformat(date)
    N = 6
    slides = [cover(dt, sp, by, N)]
    for k, st in enumerate(sp["stories"], 2):
        b = "".join(f"<li>{E(x)}</li>" for x in st["bullets"])
        p = by.get(st.get("n"), {}).get("photo")
        if p and not big_enough(p):
            print(f"note: photo for item {st['n']} is too small for a slide; showing its key figure instead", file=sys.stderr)
            p = None
        if p:
            slides.append(f'''<div class="s light ph"><div class="img"><img src="{E(src_url(p))}" alt="" style="object-position:{E(p.get("pos", "center"))}">
<div class="top"><span>{E(st["label"])}</span><span>{k} / {N}</span></div><span class="chip">{E(label(p))}</span></div>
<div class="body"><div class="row"><div class="big">{E(st["fig"])}</div><div class="lab">{E(st["figlab"])}</div></div>
<div class="place">{E(st["place"])}</div><h2>{E(st["head"])}</h2><ul>{b}</ul>
<div class="srcs">Sources: {E(st["src"])}<br>{E(credit(p))}</div></div></div>''')
        else:
            slides.append(f'''<div class="s light ph"><div class="img figp">
<div class="top"><span>{E(st["label"])}</span><span>{k} / {N}</span></div><div class="big">{E(st["fig"])}</div><div class="lab">{E(st["figlab"])}</div></div>
<div class="body"><div class="place">{E(st["place"])}</div><h2>{E(st["head"])}</h2><ul>{b}</ul>
<div class="srcs">Sources: {E(st["src"])}</div></div></div>''')
    acts = "".join(f'<div class="act"><b>{E(t)}</b><span>{E(s)}</span></div>' for t, s in d["acts"])
    slides.append(f'''<div class="s dark">{top("Act today", N, N)}<div class="D" style="font-size:150px;margin-top:60px">Act today</div>
<div class="D" style="font-size:64px;color:{AC};margin-top:10px">Whatever your politics</div><div style="margin-top:30px">{acts}</div>
<div style="margin-top:auto;border-top:2px solid #333840;padding-top:20px;font:500 24px 'IBM Plex Mono';color:#9ba1aa;text-transform:uppercase;letter-spacing:.04em">Non-partisan · Every fact sourced · Full edition: link in bio</div></div>''')
    for p in render(slides, out, date):
        print(p)
    # Per-slide captions (owner's style: only what the slide doesn't show). Slide 1 uses the post caption
    # (OUTDIR/caption.txt, written by the routine); each story slide carries its item's full text (headline, bullets
    # and sources are on the slide); slide 6 shows everything already, so it has no caption.
    cp = os.path.join(out, "caption.txt")  # write caption.txt into OUTDIR first and it becomes slide 1's caption
    caps = [open(cp).read().strip() if os.path.exists(cp) else "(Use caption.txt as the caption for slide 1.)"]
    for st in sp["stories"]:
        it = by.get(st.get("n"), {})
        caps.append(it.get("text", ""))
    caps.append("")
    write_captions(out, caps)


def focus(slug, out):
    f = json.load(open(os.path.join(root, "data", "focus", f"{slug}.json")))
    ph = f["photos"][:7]
    N = len(ph) + 2
    first = ph[0]
    slides = [f'''<div class="s full"><img src="{E(src_url(first))}" alt="" style="object-position:{E(first.get("pos", "center"))}"><div class="shade"></div>
<div class="in"><div class="top"><span style="display:flex;align-items:center;gap:14px;color:#fff"><i style="display:inline-block;width:44px;height:8px;background:{AC}"></i>Resistance Daily · Focus</span><span>1 / {N}</span></div>
<div style="margin-top:auto;display:grid;gap:20px"><span class="kick on">{E(f["kicker"].replace("Focus · ", ""))}</span>
<div class="D" style="font-size:132px">{E(f["title"])}</div><p style="font-size:34px;line-height:1.35;color:#e8e8e8">{E(f["dek"])}</p>
<div style="font:500 22px 'IBM Plex Mono';color:#cfcfcf;text-transform:uppercase;letter-spacing:.06em;border-top:2px solid rgba(255,255,255,.3);padding-top:18px">Swipe for photos → · {E(label(first))} · {E(credit(first))}</div></div></div></div>''']
    for k, p in enumerate(ph[1:], 2):
        slides.append(f'''<div class="s pslide"><div class="pimg full"><img src="{E(src_url(p))}" alt="" style="object-position:{E(p.get("pos", "center"))}">
<div style="position:absolute;inset:0 0 auto 0;height:240px;background:linear-gradient(rgba(0,0,0,.7),rgba(0,0,0,0))"></div>
<div class="in" style="height:auto;padding-bottom:0">{top("Focus · " + f["title"], k, N)}</div></div>
<div class="pcap"><span class="kick" style="font-size:22px">{E(label(p))}</span><p>{E(p["caption"])}</p><span class="cr">{E(credit(p))}</span></div></div>''')
    figs = "".join(f'<div class="fig"><b>{E(x["fig"])}</b><span>{E(x["figcap"])}</span></div>' for x in f.get("figs", [])[:4])
    srcs = sorted({x["src"][0] for x in f.get("figs", [])})
    # Every slide carries a photo (owner's rule): the key-numbers slide opens with a photo band and the last slide
    # sits on a shaded photo. "numbers_photo" / "end_photo" pick them by index in "photos" (default: the cover).
    kp = f["photos"][f.get("numbers_photo", 0)]
    ep = f["photos"][f.get("end_photo", 0)]
    slides.append(f'''<div class="s light" style="padding:0"><div class="full" style="position:relative;height:380px;flex:none"><img src="{E(src_url(kp))}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:{E(kp.get("pos", "center"))}">
<div style="position:absolute;inset:0 0 auto 0;height:220px;background:linear-gradient(rgba(0,0,0,.8),rgba(0,0,0,0))"></div><div class="in" style="position:relative;height:auto;padding:90px 84px 0;color:#fff">{top("Focus · Key numbers", len(ph) + 1, N)}</div>
<span style="position:absolute;left:84px;bottom:18px;font:500 18px 'IBM Plex Mono';color:#fff;background:rgba(0,0,0,.55);padding:6px 12px;line-height:1.45">{E(label(kp))} · {E(kp["caption"].split(". ")[0].rstrip("."))}<br>{E(credit(kp))}</span></div>
<div style="padding:40px 84px 64px;display:flex;flex-direction:column;flex:1"><div class="D" style="font-size:80px">{E(f["title"])}</div>
<div class="figs" style="margin-top:34px">{figs}</div><div class="srcs">Sources: {E(" · ".join(srcs))}</div></div></div>''')
    off = f.get("official", {}).get("text", "")
    slides.append(f'''<div class="s full"><img src="{E(src_url(ep))}" alt="" style="object-position:{E(ep.get("pos", "center"))};filter:brightness(.55)"><div class="shade"></div><div class="in">{top("Focus · Full story", N, N)}<div class="D" style="font-size:120px;margin-top:60px">Read the full story</div>
<p style="font-size:34px;line-height:1.4;color:#d0d3d8;margin-top:34px">Every photo with its caption, and what is happening, with a source for every fact.</p>
<div style="margin-top:40px;border-left:8px solid {GR};padding:10px 0 10px 26px"><b style="font:800 46px 'Barlow Condensed';text-transform:uppercase;display:block">Link in bio</b>
<span style="font:500 26px 'IBM Plex Mono';color:#9ba1aa">resistancedaily.github.io/focus/{E(slug)}</span></div>
{f'<p style="font-size:27px;line-height:1.4;color:#b8bcc2;margin-top:40px"><b style="font:500 22px IBM Plex Mono;text-transform:uppercase;letter-spacing:.06em;color:#9ba1aa;display:block;margin-bottom:8px">Official position</b>{E(off)}</p>' if off else ''}
<div style="margin-top:auto;border-top:2px solid #333840;padding-top:20px;font:500 22px 'IBM Plex Mono';color:#9ba1aa;text-transform:uppercase;letter-spacing:.04em">Non-partisan · Every fact sourced · Photos freely licensed<br><span style="text-transform:none">{E(label(ep))} · {E(ep["caption"].split(". ")[0].rstrip("."))} · {E(credit(ep))}</span></div></div></div>''')
    for p in render(slides, out, f"focus-{slug}"):
        print(p)
    ig = f.get("instagram", {})
    # One caption per slide: the cover carries the post caption; each later slide carries part of the story, so the
    # story reads in order as people swipe. Story paragraphs fill the photo slides, then the key-numbers slide.
    # Owner's style: a caption carries only what its slide doesn't already show. Slide 1: "Focus · title", the swipe
    # line, what the first photo shows, at most 5 hashtags. Photo slides: the story paragraph, then "Sources: …".
    # Key-numbers slide: the story paragraph only (numbers and sources are on the slide). Last slide: the sources
    # of the official position (the position and link are on the slide).
    def srcs_of(pairs):
        return "Sources: " + " · ".join(n for n, u in pairs)
    story = list(f["story"])
    slots = len(ph) - 1 + 1  # photo slides 2..len(ph), then the key-numbers slide
    per = [story[i:i + 1] for i in range(min(slots - 1, len(story)))]
    per.append(story[slots - 1:] if len(story) >= slots else [])
    per += [[] for _ in range(slots - len(per))]
    caps = [f"""Focus · {f['title']}

Swipe: each slide's caption tells the next part of the story.

{first['caption']}

{' '.join(ig.get('hashtags', [])[:5])}"""]
    for k, p in enumerate(ph[1:]):
        body = "\n\n".join(f"{x['text']}\n{srcs_of(x['src'])}" for x in per[k])
        caps.append(body)
    shown = set(srcs)  # sources printed on the key-numbers slide
    caps.append("\n\n".join(x["text"] + ("" if {n for n, u in x["src"]} <= shown else "\n" + srcs_of(x["src"]))
                              for x in per[-1]))
    caps.append(srcs_of(f["official"]["src"]) if off else "")
    open(os.path.join(out, "caption.txt"), "w").write(caps[0] + "\n")
    write_captions(out, caps)
    alts = [f"Slide 1: {first['alt']} Title: {f['title']}. {f['dek']}"]
    alts += [f"Slide {k}: {p['alt']} {p['caption']}" for k, p in enumerate(ph[1:], 2)]
    alts.append(f"Slide {len(ph) + 1}: Key numbers. " + "; ".join(f"{x['fig']} {x['figcap']}" for x in f.get("figs", [])[:4]) + ".")
    alts.append(f"Slide {N}: Read the full story at resistancedaily.github.io/focus/{slug}, link in bio." + (f" Official position: {off}" if off else ""))
    open(os.path.join(out, "alt-text.txt"), "w").write("\n\n".join(alts) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] not in ("daily", "focus"):
        sys.exit(__doc__)
    (daily if sys.argv[1] == "daily" else focus)(sys.argv[2], sys.argv[3])
