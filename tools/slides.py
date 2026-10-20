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


def daily(date, out):
    d = json.load(open(os.path.join(root, "data", f"{date}.json")))
    sp = json.load(open(os.path.join(root, "data", f"{date}.slides.json")))
    by = {i["n"]: i for i in d["items"]}
    dt = datetime.date.fromisoformat(date)
    sunday = dt.weekday() == 6
    N = 6
    rows = "".join(f'<div style="border-top:2px solid {"#d9dcd8" if sunday else "#333840"};padding:20px 0 18px"><div class="D" style="font-size:64px;color:{RED if sunday else AC}">{E(p)}</div><div style="font:600 36px \'IBM Plex Sans\';margin-top:8px">{E(h)}</div></div>' for p, h in sp["cover"])
    tag = f' · <span style="color:{RED}">+ Still waiting</span>' if sunday else ""
    slides = [f'''<div class="s {'light' if sunday else 'dark'}" style="padding:90px 110px">
<div class="top"><span style="color:{INK if sunday else BG};display:flex;align-items:center;gap:14px"><i style="display:inline-block;width:44px;height:8px;background:{AC}"></i>Resistance Daily</span><span>1 / {N}</span></div>
<div class="D" style="font-size:76px;color:{AC};margin-top:46px">{dt.strftime("%A")}</div>
<div class="D" style="font-size:200px">{dt.strftime("%d %b")}</div>
<p style="font-size:30px;color:#9ba1aa;margin:22px 0 26px;line-height:1.35">What happened to people's rights in the last 24 hours. Every fact sourced.</p>
{rows}
<div style="margin-top:auto;border-top:2px solid {"#d9dcd8" if sunday else "#333840"};padding-top:20px;font:500 24px 'IBM Plex Mono';color:#9ba1aa;text-transform:uppercase;letter-spacing:.06em">Swipe → · Sources: link in bio{tag}</div></div>''']
    for k, st in enumerate(sp["stories"], 2):
        b = "".join(f"<li>{E(x)}</li>" for x in st["bullets"])
        p = by.get(st.get("n"), {}).get("photo")
        if p and not big_enough(p):
            print(f"note: photo for item {st['n']} is too small for a slide; using the text layout", file=sys.stderr)
            p = None
        if p:
            slides.append(f'''<div class="s light ph"><div class="img"><img src="{E(src_url(p))}" alt="" style="object-position:{E(p.get("pos", "center"))}">
<div class="top"><span>{E(st["label"])}</span><span>{k} / {N}</span></div><span class="chip">{E(label(p))}</span></div>
<div class="body"><div class="row"><div class="big">{E(st["fig"])}</div><div class="lab">{E(st["figlab"])}</div></div>
<div class="place">{E(st["place"])}</div><h2>{E(st["head"])}</h2><ul>{b}</ul>
<div class="srcs">Sources: {E(st["src"])}<br>{E(credit(p))}</div></div></div>''')
        else:
            slides.append(f'''<div class="s light">{top(st["label"], k, N)}<div class="big" style="margin-top:50px">{E(st["fig"])}</div><div class="lab">{E(st["figlab"])}</div>
<div class="place">{E(st["place"])}</div><h2>{E(st["head"])}</h2><ul>{b}</ul><div class="srcs">Sources: {E(st["src"])}</div></div>''')
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
