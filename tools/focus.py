#!/usr/bin/env python3
"""Build Resistance Daily "Focus" pages: one place or issue told through photos, with a sourced write-up.

Usage (from the repo root):  python3 tools/focus.py SLUG
Reads data/focus/SLUG.json, writes focus/SLUG.html and focus/index.html (all focus pages, newest first).

data/focus/SLUG.json:
{ "slug", "title", "kicker", "dek", "updated": "YYYY-MM-DD", "rights": [...],
  "photos": [photo, ...]            # same photo objects as data.json items (tools/photos.py); 3-8 of them
  "figs": [{"fig", "figcap", "src": [name, url]}],   # 2-4 key numbers
  "story": [{"text", "src": [[name, url], ...], "fig"?, "figcap"?}],  # 3-5 short paragraphs, every fact sourced;
                                                      # with "chapters", a paragraph past the last photo shows fig/figcap
  "official": {"text", "src": [[name, url], ...]},    # the authorities' position, or that they have not responded
  "editions": ["YYYY-MM-DD", ...],                    # daily editions that covered it
  "instagram": {"caption", "hashtags": [...]},       # used by tools/slides.py focus SLUG
  "seo_title": "...",                                 # optional: the words people search for, used for <title> and
                                                      #   link previews (≤ 65 chars, neutral); the page heading stays "title"
  "whats_new": {"date": "YYYY-MM-DD", "text": "..."}, # optional: 1-2 sentences on the latest development, shown at the top
  "published": "YYYY-MM-DD",                          # optional: first published (default: earliest edition)
  "layout": "chapters",                               # optional: pair story[i] with photos[i+1] instead of a gallery
  "numbers_photo": 0, "end_photo": 0 }                # optional: photo indexes for the slides' key-numbers and last slide
"""
import sys, os, json, html, datetime, glob
import seo

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://resistancedaily.github.io/"

CSS = """
:root{--bg:#f3f4f2;--paper:#fff;--ink:#15181d;--muted:#5b616b;--rule:#d9dcd8;--accent:#d9661a;--red:#b3261e;--chip:#eceee9;
--display:"Barlow Condensed","Arial Narrow",Arial,sans-serif;--body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;--red:#ef6b62;--chip:#22262c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111317;--paper:#181b20;--ink:#eceae5;--muted:#9ba1aa;--rule:#2b2f36;--accent:#f08a3c;--red:#ef6b62;--chip:#22262c;color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--body)}
.wrap{max-width:900px;margin:0 auto;padding:20px max(16px,env(safe-area-inset-left,0px)) 48px;display:grid;gap:26px}
a{color:inherit;text-decoration-color:var(--accent);text-underline-offset:2px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2{font-family:var(--display);text-transform:uppercase;margin:0;line-height:.95}
p{margin:0}
.top{display:flex;justify-content:space-between;gap:12px;font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border-bottom:3px solid var(--ink);padding-bottom:10px}
.top b{color:var(--ink);font-weight:500}
.top a{white-space:nowrap}
.top>span{text-align:right}
.top .sep{font-style:normal}
@media (max-width:520px){.top>span{display:flex;flex-direction:column;align-items:flex-end;gap:6px}.top .sep{display:none}}
.kicker{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
h1{font-size:clamp(40px,8vw,72px);font-weight:800;text-wrap:balance}
.dek{font-size:18px;color:var(--muted);max-width:62ch}
.meta{font:500 12px var(--mono);color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 16px}
.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.gallery figure:first-child{grid-column:1/-1}
.gallery figure:first-child img{aspect-ratio:16/9}
.gallery figure:last-child:nth-child(even){grid-column:1/-1}
.gallery figure:last-child:nth-child(even) img{aspect-ratio:16/9}
@media (max-width:620px){.gallery{grid-template-columns:1fr}}
figure{margin:0;display:grid;gap:6px;min-width:0}
figure img{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:4px;background:var(--chip)}
figcaption{font-size:13px;color:var(--muted)}
figcaption b{font:500 10.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin-right:6px}
figcaption .cr{display:block;font-size:11.5px}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.fig{background:var(--paper);border:1px solid var(--rule);border-top:5px solid var(--red);border-radius:6px;padding:14px;display:grid;gap:4px}
.fig b{font:800 52px var(--display);line-height:.9;color:var(--red)}
.fig span{font:500 11.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.fig a{font-size:12px;color:var(--muted)}
.sec-h{border-bottom:1px solid var(--rule);padding-bottom:6px}
.sec-h h2{font-size:30px;font-weight:800}
.story{display:grid;gap:14px;max-width:66ch;font-size:16.5px}
.src{font-size:12.5px;color:var(--muted)}
.official{background:var(--paper);border:1px solid var(--rule);border-left:4px solid var(--ink);border-radius:6px;padding:14px 16px;display:grid;gap:6px;max-width:66ch}
.official b{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
ul.list{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:6px;display:grid;grid-template-columns:160px 1fr;overflow:hidden;text-decoration:none}
.card img{width:100%;height:100%;min-height:110px;object-fit:cover;background:var(--chip)}
.card div{padding:12px 14px;display:grid;gap:4px;align-content:start}
.card h2{font-size:26px;font-weight:800}
.card p{font-size:14px;color:var(--muted)}
@media (max-width:520px){.card{grid-template-columns:1fr}.card img{aspect-ratio:16/9}}
footer{font-size:12.5px;color:var(--muted);border-top:1px solid var(--rule);padding-top:12px;display:grid;gap:4px}
.cover img{aspect-ratio:16/9}
.allf{justify-self:start;font-weight:600;font-size:14px;color:var(--ink);text-decoration:none;border:1px solid var(--rule);border-left:4px solid var(--accent);background:var(--paper);border-radius:6px;padding:8px 12px}
.allf.big{display:grid;gap:2px;padding:14px 16px}
.allf.big span{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.allf.big b{font:800 26px var(--display);text-transform:uppercase}
.chaps{display:grid;gap:26px}
.chap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:start;border-top:1px solid var(--rule);padding-top:20px}
.chap p{font-size:16.5px}
@media (max-width:680px){.chap{grid-template-columns:1fr}}
.figp{aspect-ratio:4/3;background:var(--chip);border-radius:4px;display:grid;place-content:center;justify-items:center;gap:8px;padding:16px;text-align:center}
.figp b{font:800 clamp(64px,11vw,96px)/.9 var(--display);color:var(--red)}
.new{background:var(--paper);border:1px solid var(--rule);border-left:5px solid var(--red);border-radius:6px;padding:12px 16px;display:grid;gap:4px;max-width:66ch}
.new b{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:var(--red)}
.more-f{display:grid;gap:6px;max-width:66ch}
.more-f h2{font-size:24px;font-weight:800}
.more-f ul{margin:0;padding-left:18px;display:grid;gap:4px}
.figp span{font:500 12px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);max-width:28ch}
"""

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title><meta name="description" content="{desc}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
{og_image}<meta property="og:type" content="article"><link rel="canonical" href="{canonical}">{extra}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{css}</style></head><body><div class="wrap">"""

FOOT = """<footer><span>Resistance Daily is a non-partisan public record of human-rights events. Every fact links to its source.</span>
<span>Photos are freely licensed and credited. "File photo" marks an older picture of the place, not of the event. We blur protesters' and children's faces.</span>
<span>{follow} for each new edition.</span>
<span>Seen something? Send photos with the date, the place and your permission to publish to <a href="mailto:resistancedaily.in@gmail.com?subject=Photo%20for%20Resistance%20Daily">resistancedaily.in@gmail.com</a>.</span></footer>
</div></body></html>
"""


def links(pairs):
    return " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in pairs)


def rel(src, prefix):
    return src if src.startswith(("http://", "https://")) else prefix + src


def figure(p, prefix="../"):
    label = "Photo from the event" if p.get("kind") == "event" else f"File photo · {p['year']}"
    ch = f" ({E(p['changes'])})" if p.get("changes") else ""
    pos = f' style="object-position:{E(p["pos"])}"' if p.get("pos") else ""
    return (f'<figure><img src="{E(rel(p["src"], prefix))}" alt="{E(p["alt"])}" loading="lazy" decoding="async"{pos}>'
            f'<figcaption><b>{label}</b>{E(p["caption"])}<span class="cr">Photo: <a href="{E(p["page"])}">{E(p["credit"])}</a>, '
            f'<a href="{E(p["licence_url"])}">{E(p["licence"])}</a>{ch}</span></figcaption></figure>')


def body(f, figs, story, official):
    figs_html = f'<section class="figs" aria-label="Key numbers">{figs}</section>' if figs else ''
    if f.get("layout") != "chapters":
        return (f'<section class="gallery" aria-label="Photos">{"".join(figure(p) for p in f["photos"])}</section>\n{figs_html}\n'
                f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>What is happening</h2></div><div class="story">{story}</div>{official}</section>')
    # "chapters": every paragraph sits next to its own photo (photos[0] is the cover, photos[i+1] goes with story[i]).
    # A paragraph without a photo shows its key figure ("fig", "figcap") in the photo's place, as the slides do.
    ph = f["photos"]

    def side(i, x):
        if i + 1 < len(ph):
            return figure(ph[i + 1])
        if x.get("fig"):
            return f'<div class="figp"><b>{E(x["fig"])}</b><span>{E(x.get("figcap", ""))}</span></div>'
        return ""
    chaps = "".join(f'<div class="chap">{side(i, x)}<p>{E(x["text"])} <span class="src">{links(x["src"])}</span></p></div>'
                    for i, x in enumerate(f["story"]))
    return (f'<section class="cover">{figure(ph[0])}</section>\n{figs_html}\n'
            f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>What is happening</h2></div><div class="chaps">{chaps}</div>{official}</section>')


def page(f, all_f=()):
    upd = datetime.date.fromisoformat(f["updated"]).strftime("%d %b %Y")
    figs = "".join(f'<div class="fig"><b>{E(x["fig"])}</b><span>{E(x["figcap"])}</span><a href="{E(x["src"][1])}">{E(x["src"][0])}</a></div>' for x in f.get("figs", []))
    story = "".join(f'<p>{E(s["text"])} <span class="src">{links(s["src"])}</span></p>' for s in f["story"])
    off = f.get("official")
    official = f'<div class="official"><b>Official position</b><p>{E(off["text"])} <span class="src">{links(off["src"])}</span></p></div>' if off else ""
    eds = " · ".join(f'<a href="../archive/{d}.html">{datetime.date.fromisoformat(d).strftime("%a %d %b")}</a>' for d in sorted(f.get("editions", []), reverse=True))
    first = f["photos"][0]["src"] if f["photos"] else ""
    # Link previews: a 1200x630 JPEG cut from the cover photo (falls back to the .webp if Pillow is missing).
    share = seo.share_image(root, first, f"images/focus/{f['slug']}/share.jpg") if first else None
    img = share or first
    og = (f'<meta property="og:image" content="{E(rel(img, SITE))}">' + ('<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if share else "")
          + f'<meta property="og:image:alt" content="{E(f["photos"][0]["alt"])}">') if first else ""
    url = f"{SITE}focus/{f['slug']}.html"
    head = f.get("seo_title") or f["title"]
    pub = f.get("published") or min(f.get("editions") or [f["updated"]])
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": head[:110], "alternativeHeadline": f["title"],
          "description": f["dek"], "url": url, "mainEntityOfPage": url, "datePublished": seo.iso(pub), "dateModified": seo.iso(f["updated"]),
          "author": seo.PUBLISHER, "publisher": seo.PUBLISHER, "isAccessibleForFree": True, "inLanguage": "en",
          "about": f.get("rights", []), "image": [rel(img, SITE)] if first else []}
    extra = (f'<meta property="og:url" content="{url}"><meta property="og:site_name" content="Resistance Daily">'
             f'<meta property="article:published_time" content="{seo.iso(pub)}"><meta property="article:modified_time" content="{seo.iso(f["updated"])}">'
             f'<meta name="twitter:card" content="summary_large_image">{seo.jsonld(ld)}')
    wn = f.get("whats_new")
    new = (f'<div class="new"><b>What\'s new · {datetime.date.fromisoformat(wn["date"]).strftime("%d %b %Y")}</b><p>{E(wn["text"])}</p></div>' if wn else "")
    others = [o for o in all_f if o["slug"] != f["slug"]]
    more = ('<section class="more-f"><h2>Other Focus stories</h2><ul>' + "".join(
        f'<li><a href="{E(o["slug"])}.html">{E(o.get("seo_title") or o["title"])}</a></li>' for o in others) + '</ul></section>') if others else ""
    return HEAD.format(title=E(f"{head} · Resistance Daily"), desc=E(f["dek"]), og_image=og, extra=extra,
                       canonical=url, css=CSS) + f"""
<div class="top"><a href="../"><b>Resistance Daily</b></a><span><a href="./">All Focus stories</a><i class="sep"> · </i><a href="../archive/">Past editions</a></span></div>
<header style="display:grid;gap:10px"><span class="kicker">{E(f['kicker'])}</span><h1>{E(f['title'])}</h1><p class="dek">{E(f['dek'])}</p>
{new}<div class="meta"><span>Updated {upd}</span><span>{E(" · ".join(f.get("rights", [])))}</span><span>{len(f["photos"])} photos</span></div>
<a class="allf" href="./">Looking for another story? See all Focus stories →</a></header>
{body(f, figs, story, official)}
{f'<p class="src">In the daily edition: {eds}</p>' if eds else ''}
{more}
<a class="allf big" href="./"><span>More in-depth stories, every fact sourced</span><b>See all Focus stories →</b></a>
""" + FOOT.format(follow=seo.FOLLOW)


def index(all_f):
    cards = "".join(f'''<li><a class="card" href="{E(f["slug"])}.html"><img src="{E(rel(f["photos"][0]["src"], "../"))}" alt="{E(f["photos"][0]["alt"])}" loading="lazy">
<div><span class="kicker">{E(f["kicker"])}</span><h2>{E(f["title"])}</h2><p>{E(f["dek"])}</p><span class="src">Updated {datetime.date.fromisoformat(f["updated"]).strftime("%d %b %Y")} · {len(f["photos"])} photos</span></div></a></li>''' for f in all_f)
    return HEAD.format(title="Focus · Resistance Daily", desc="In-depth stories on places and issues, with a source for every fact.",
                       og_image="", extra=f'<meta property="og:url" content="{SITE}focus/"><meta property="og:site_name" content="Resistance Daily">',
                       canonical=f"{SITE}focus/", css=CSS) + f"""
<div class="top"><a href="../"><b>Resistance Daily</b></a><span><a href="../archive/">Past editions</a></span></div>
<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Focus stories</h1>
<ul class="list">{cards}</ul>
""" + FOOT.format(follow=seo.FOLLOW)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    f = json.load(open(os.path.join(root, "data", "focus", f"{slug}.json")))
    os.makedirs(os.path.join(root, "focus"), exist_ok=True)
    all_f = [json.load(open(p)) for p in glob.glob(os.path.join(root, "data", "focus", "*.json"))]
    all_f.sort(key=lambda x: x["updated"], reverse=True)
    open(os.path.join(root, "focus", f"{slug}.html"), "w").write(page(f, all_f))
    open(os.path.join(root, "focus", "index.html"), "w").write(index(all_f))
    seo.write_sitemap(root)
    # The home page shows the latest Focus cards: rebuild it too.
    import subprocess
    subprocess.run([sys.executable, os.path.join(root, "tools", "home.py"), "index.html"], check=True)
    print("built focus", slug)
