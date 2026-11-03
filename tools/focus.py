#!/usr/bin/env python3
"""Build Resistance Daily "Focus" pages: one place or issue told through photos, with a sourced write-up.

Usage (from the repo root):  python3 tools/focus.py SLUG
Reads data/focus/SLUG.json, writes focus/SLUG.html and focus/index.html (all focus pages, newest first).

data/focus/SLUG.json:
{ "slug", "title", "kicker", "dek", "updated": "YYYY-MM-DD", "rights": [...],
  "photos": [photo, ...]            # same photo objects as data.json items (tools/photos.py); 3-8 of them
  "figs": [{"fig", "figcap", "src": [name, url]}],   # 2-4 key numbers
  "story": [{"text", "src": [[name, url], ...], "fig"?, "figcap"?, "date"?}],  # short paragraphs, every fact sourced;
                                                      # with "chapters", a paragraph past the last photo shows fig/figcap.
                                                      # "date" (YYYY-MM-DD) marks a dated update: with 3+ dated paragraphs
                                                      # the page shows "The background" (undated paragraphs) and then a
                                                      # "Timeline" of the dated ones, newest first, older ones folded.
  "official": {"text", "src": [[name, url], ...],     # the authorities' position, or that they have not responded
               "points"?: [str | {"text", "src"}]},   # optional: the same position as 3-6 short bullets (strings share "src"), shown on
                                                      #   the page instead of "text" (the slides keep using "text")
  "editions": ["YYYY-MM-DD", ...],                    # daily editions that covered it
  "instagram": {"caption", "hashtags": [...]},       # used by tools/slides.py focus SLUG
  "short": "...",                                     # 2-4 words for cards on the home page and the Focus list
  "seo_title": "...",                                 # optional: the words people search for, used for <title> and
                                                      #   link previews (≤ 65 chars, neutral); the page heading stays "title"
  "whats_new": {"date": "YYYY-MM-DD", "text": "..."}, # optional: 1-2 sentences on the latest development, shown at the top
  "published": "YYYY-MM-DD",                          # optional: first published (default: earliest edition)
  "layout": "chapters",                               # optional: pair story[i] with photos[i+1] instead of a gallery
  "numbers_photo": 0, "end_photo": 0,                 # optional: photo indexes for the slides' key-numbers and last slide
  # Visual layout (optional): "summary" puts three answer-first cards under the header, and a paragraph with a
  # "takeaway" becomes a block: its visual, the one-sentence takeaway, and the full text under "More detail".
  "summary": [{"label": "What's happening"|"Why it matters"|"What's next", "text" (<= 20 words), "src"}, x3],
  # story[i]["takeaway"]: one sentence; story[i]["visual"]: {"type": "photo", "i": photo index} |
  #   {"type": "chart", "title", "bars": [[label, value], ...], "unit"?, "src"} | {"type": "dots", "n", "of", "cap", "src"} |
  #   {"type": "map", "cap", "src"} (inlines data/focus/maps/SLUG.svg, made by tools/maps.js from data/focus/maps/SLUG.json "custom") | {"type": "fig"}
  # Photos not used by a block appear in an "In pictures" strip.
}                # optional: photo indexes for the slides' key-numbers and last slide
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
.opts{margin:0;padding-left:18px;display:grid;gap:8px}
.opts li{padding-left:2px}
.opts li::marker{color:var(--muted)}
ul.list{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:6px;display:grid;grid-template-columns:76px 1fr;overflow:hidden;text-decoration:none;color:inherit}
.card img{width:76px;height:100%;min-height:68px;object-fit:cover;background:var(--chip)}
.card div{padding:8px 12px;display:grid;gap:2px;align-content:center;min-width:0}
.card h2{font:600 17px/1.25 var(--body);text-transform:none;letter-spacing:0}
.card .kicker{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kf{font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.kf b{font:800 17px var(--display);color:var(--red)}
.card p{font-size:14px;color:var(--muted)}

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
.sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.sum div{background:var(--paper);border:1px solid var(--rule);border-top:5px solid var(--accent);border-radius:6px;padding:14px 16px;display:grid;gap:6px;align-content:start}
.sum b{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:var(--accent)}
.sum p{font-size:16px;line-height:1.4}
.blocks{display:grid;gap:30px}
.blk{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px;align-items:center;border-top:1px solid var(--rule);padding-top:22px}
.blk h3{font:600 21px/1.3 var(--body);margin:0}
.blk .tx{display:grid;gap:10px}
.blk details summary{cursor:pointer;font-size:13.5px;font-weight:600;color:var(--muted)}
.blk details p{font-size:15.5px;margin-top:8px}
.blk.wide{grid-template-columns:1fr}
@media (max-width:680px){.blk{grid-template-columns:1fr}}
.viz{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:14px;display:grid;gap:10px}
.viz .t{font:500 11.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.bars{display:grid;gap:10px}
.bar{display:grid;grid-template-columns:70px minmax(0,1fr);gap:10px;align-items:center;font-size:13px;color:var(--muted)}
.bar i{display:block;height:34px;background:var(--red);border-radius:3px;position:relative;min-width:4px}
.bar i span{position:absolute;left:8px;top:50%;transform:translateY(-50%);font:800 22px var(--display);color:#fff;white-space:nowrap}
.dots{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;max-width:300px}
.dots i{aspect-ratio:1;border-radius:50%;background:var(--chip);border:2px solid var(--rule)}
.dots i.on{background:var(--red);border-color:var(--red)}
.viz .big{font:800 56px/0.9 var(--display);color:var(--red)}
.map{width:100%;height:auto;display:block}
.land{fill:var(--chip)}
.pin circle{stroke:var(--paper);stroke-width:2}
.pin text{font:700 13px var(--body);fill:#fff}
.pin text.pl{font:600 17px var(--body);fill:var(--ink);paint-order:stroke;stroke:var(--chip);stroke-width:4px}
.pin.red circle{fill:var(--red)} .pin.grey circle{fill:#7a808a}
@media (max-width:520px){.pin text.pl{font-size:25px}.pin circle{r:13px}}
.pics{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.tl{list-style:none;margin:0;padding:0;display:grid;gap:0;max-width:760px}
.tl li{display:grid;grid-template-columns:76px minmax(0,1fr);gap:16px;position:relative;padding:0 0 22px}
.tl li:before{content:"";position:absolute;left:90px;top:6px;bottom:0;width:2px;background:var(--rule)}
.tl li:last-child:before{display:none}
.tl time{font:800 22px/1 var(--display);text-transform:uppercase;text-align:right;color:var(--muted);padding-top:2px}
.tl time small{display:block;font:500 11px var(--mono);letter-spacing:.05em;margin-top:3px}
.tl .ev{display:grid;gap:8px;padding-left:18px;position:relative;min-width:0}
.tl .ev:before{content:"";position:absolute;left:-8px;top:5px;width:14px;height:14px;border-radius:50%;background:var(--bg);border:3px solid var(--muted);box-sizing:border-box}
.tl .ev p{font-size:16.5px}
.tl li.latest time{color:var(--red)}
.tl li.latest .ev:before{border-color:var(--red);background:var(--red)}
.tl .badge{justify-self:start;font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.07em;color:#fff;background:var(--red);border-radius:3px;padding:2px 7px}
.tl .tfig{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.tl .tfig b{font:800 34px/1 var(--display);color:var(--red)}
.tl .tfig span{font:500 11.5px var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.tl figure{max-width:440px}
.older{max-width:760px}
.older summary{cursor:pointer;font-weight:600;font-size:14px;list-style:none;border:1px solid var(--rule);background:var(--paper);border-radius:6px;padding:8px 12px;display:inline-block;margin:0 0 18px 92px}
.older summary::-webkit-details-marker{display:none}
.older[open] summary{margin-bottom:22px}
@media (max-width:520px){.tl li{grid-template-columns:52px minmax(0,1fr);gap:18px}.tl li:before{left:68px}.tl time{font-size:18px}.older summary{margin-left:70px}}
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


def viz(f, x, used):
    """The visual for a block (see the docstring); records which photos it uses."""
    v = x.get("visual") or {"type": "fig"}
    vs = f'<span class="src">{links(v["src"])}</span>' if v.get("src") else ""
    t = v["type"]
    if t == "photo" and v.get("i") is not None and v["i"] < len(f["photos"]):
        used.add(v["i"])
        return figure(f["photos"][v["i"]])
    if t == "chart":
        mx = max(b[1] for b in v["bars"]) or 1
        bars = "".join(f'<div class="bar"><span>{E(str(lbl))}</span><i style="width:{max(val / mx * 100, 2):.1f}%"><span>{val:,}{E(v.get("unit", ""))}</span></i></div>' for lbl, val in v["bars"])
        return f'<div class="viz"><span class="t">{E(v.get("title", ""))}</span><div class="bars">{bars}</div>{vs}</div>'
    if t == "dots":
        dots = "".join(f'<i class="{"on" if k < v["n"] else ""}"></i>' for k in range(v["of"]))
        return (f'<div class="viz"><div class="big">{v["n"]} in {v["of"]}</div><div class="dots" role="img" aria-label="{v["n"]} of {v["of"]}">{dots}</div>'
                f'<span class="t">{E(v.get("cap", ""))}</span>{vs}</div>')
    if t == "map":
        try:
            svg = open(os.path.join(root, "data", "focus", "maps", f"{f['slug']}.svg")).read()
        except OSError:
            svg = ""
        return f'<div class="viz">{svg}<span class="t">{E(v.get("cap", ""))}</span>{vs}</div>'
    if x.get("fig"):
        return f'<div class="figp"><b>{E(x["fig"])}</b><span>{E(x.get("figcap", ""))}</span></div>'
    return ""


def blocks(f, idx, used):
    """Visual layout: per paragraph, its visual, the one-sentence takeaway, and the full text folded."""
    out = []
    for i in idx:
        x = f["story"][i]
        tx = (f'<div class="tx"><h3>{E(x["takeaway"])}</h3>'
              f'<details><summary>More detail and sources</summary><p>{E(x["text"])} <span class="src">{links(x["src"])}</span></p></details></div>')
        if (x.get("visual") or {}).get("type") == "map":  # maps need the full width: takeaway first, then the map
            out.append(f'<div class="blk wide">{tx}{viz(f, x, used)}</div>')
        else:
            out.append(f'<div class="blk">{viz(f, x, used)}{tx}</div>')
    return f'<div class="blocks">{"".join(out)}</div>'


def visual_body(f, figs_html, official):
    used = {0}
    ph = f["photos"]
    dated = [(i, x) for i, x in enumerate(f["story"]) if x.get("date")]
    tl = len(dated) >= 3
    idx = [i for i, x in enumerate(f["story"]) if not (tl and x.get("date"))]
    main = blocks(f, idx, used)
    tl_html = timeline(f, dated, lambda i: "") if tl else ""
    rest = [p for k, p in enumerate(ph) if k not in used]
    pics = (f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>In pictures</h2></div><div class="pics">{"".join(figure(p) for p in rest)}</div></section>') if rest else ""
    return (f'<section class="cover">{figure(ph[0])}</section>\n{figs_html}\n'
            f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>{"The background" if tl else "The story"}</h2></div>{main}</section>\n'
            f'{tl_html}\n{pics}\n<section style="display:grid;gap:14px">{official}</section>')


SHOW_LATEST = 5  # timeline entries shown before "Show earlier updates"


def timeline(f, dated, side_photo):
    """Dated updates, newest first; the newest is marked "Latest" and entries past SHOW_LATEST fold away."""
    order = sorted(dated, key=lambda ix: (ix[1]["date"], ix[0]), reverse=True)

    def item(k, i, x):
        d = datetime.date.fromisoformat(x["date"])
        ph = side_photo(i)
        fig = (f'<div class="tfig"><b>{E(x["fig"])}</b><span>{E(x.get("figcap", ""))}</span></div>'
               if x.get("fig") and not ph else "")
        badge = '<span class="badge">Latest</span>' if k == 0 else ""
        return (f'<li class="{"latest" if k == 0 else ""}"><time datetime="{x["date"]}">{d.strftime("%d %b")}<small>{d.year}</small></time>'
                f'<div class="ev">{badge}<p>{E(x["text"])} <span class="src">{links(x["src"])}</span></p>{fig}{ph}</div></li>')
    items = [item(k, i, x) for k, (i, x) in enumerate(order)]
    shown, rest = items[:SHOW_LATEST], items[SHOW_LATEST:]
    older = (f'<details class="older"><summary>Show {len(rest)} earlier update{"s" if len(rest) != 1 else ""} ↓</summary>'
             f'<ol class="tl">{"".join(rest)}</ol></details>') if rest else ""
    return (f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>Timeline</h2></div>'
            f'<p class="src">Newest first. Every update links to its sources.</p><ol class="tl">{"".join(shown)}</ol>{older}</section>')


def body(f, figs, story, official):
    figs_html = f'<section class="figs" aria-label="Key numbers">{figs}</section>' if figs else ''
    if any(x.get("takeaway") for x in f["story"]):
        return visual_body(f, figs_html, official)
    dated = [(i, x) for i, x in enumerate(f["story"]) if x.get("date")]
    if len(dated) >= 3:
        # Live story: undated paragraphs are the background, dated ones form the timeline (newest first).
        ph = f["photos"]
        chapters = f.get("layout") == "chapters"
        side_photo = (lambda i: figure(ph[i + 1]) if chapters and i + 1 < len(ph) else "")
        bg = [(i, x) for i, x in enumerate(f["story"]) if not x.get("date")]
        if chapters:
            def side(i, x):
                if i + 1 < len(ph):
                    return figure(ph[i + 1])
                if x.get("fig"):
                    return f'<div class="figp"><b>{E(x["fig"])}</b><span>{E(x.get("figcap", ""))}</span></div>'
                return ""
            bg_html = "".join(f'<div class="chap">{side(i, x)}<p>{E(x["text"])} <span class="src">{links(x["src"])}</span></p></div>' for i, x in bg)
            top = f'<section class="cover">{figure(ph[0])}</section>\n{figs_html}'
            bg_sec = f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>The background</h2></div><div class="chaps">{bg_html}</div></section>' if bg else ""
        else:
            bg_html = "".join(f'<p>{E(x["text"])} <span class="src">{links(x["src"])}</span></p>' for i, x in bg)
            top = f'<section class="gallery" aria-label="Photos">{"".join(figure(p) for p in ph)}</section>\n{figs_html}'
            bg_sec = f'<section style="display:grid;gap:14px"><div class="sec-h"><h2>The background</h2></div><div class="story">{bg_html}</div></section>' if bg else ""
        return f'{top}\n{bg_sec}\n{timeline(f, dated, side_photo)}\n<section style="display:grid;gap:14px">{official}</section>'
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
    if off and off.get("points"):
        # A point is a string (sources shared, listed once under the bullets) or {"text", "src"} with its own sources.
        lis = "".join(f'<li>{E(pt)}</li>' if isinstance(pt, str) else f'<li>{E(pt["text"])} <span class="src">{links(pt["src"])}</span></li>'
                      for pt in off["points"])
        shared = f'<span class="src">Sources: {links(off["src"])}</span>' if any(isinstance(pt, str) for pt in off["points"]) else ""
        official = f'<div class="official"><b>Official position</b><ul class="opts">{lis}</ul>{shared}</div>'
    elif off:
        official = f'<div class="official"><b>Official position</b><p>{E(off["text"])} <span class="src">{links(off["src"])}</span></p></div>'
    else:
        official = ""
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
    summary = ('<section class="sum" aria-label="The story in brief">' + "".join(
        f'<div><b>{E(c["label"])}</b><p>{E(c["text"])}</p><span class="src">{links(c["src"])}</span></div>' for c in f["summary"]) + '</section>') if f.get("summary") else ""
    others = [o for o in all_f if o["slug"] != f["slug"]]
    more = ('<section class="more-f"><h2>Other Focus stories</h2><ul>' + "".join(
        f'<li><a href="{E(o["slug"])}.html">{E(o.get("seo_title") or o["title"])}</a></li>' for o in others) + '</ul></section>') if others else ""
    return HEAD.format(title=E(f"{head} · Resistance Daily"), desc=E(f["dek"]), og_image=og, extra=extra,
                       canonical=url, css=CSS) + f"""
<div class="top"><a href="../"><b>Resistance Daily</b></a><span><a href="./">All Focus stories</a><i class="sep"> · </i><a href="../archive/">Past editions</a></span></div>
<header style="display:grid;gap:10px"><span class="kicker">{E(f['kicker'])}</span><h1>{E(f['title'])}</h1><p class="dek">{E(f['dek'])}</p>
{new}<div class="meta"><span>Updated {upd}</span><span>{E(" · ".join(f.get("rights", [])))}</span><span>{len(f["photos"])} photos</span></div>
<a class="allf" href="./">Looking for another story? See all Focus stories →</a></header>
{summary}
{body(f, figs, story, official)}
{f'<p class="src">In the daily edition: {eds}</p>' if eds else ''}
{more}
<a class="allf big" href="./"><span>More in-depth stories, every fact sourced</span><b>See all Focus stories →</b></a>
""" + FOOT.format(follow=seo.FOLLOW)


def index(all_f):
    def kf(f):
        x = (f.get("figs") or [{}])[0]
        return f'<span class="kf"><b>{E(x["fig"])}</b> {E(x["figcap"])}</span>' if x.get("fig") else ""
    cards = "".join(f'''<li><a class="card" href="{E(f["slug"])}.html"><img src="{E(rel(f["photos"][0]["src"], "../"))}" alt="" loading="lazy">
<div><span class="kicker">{E(f["kicker"].replace("Focus · ", "").split(", ")[0])} · {datetime.date.fromisoformat(f["updated"]).strftime("%d %b")}</span><h2>{E(f.get("short", f["title"]))}</h2>{kf(f)}</div></a></li>''' for f in all_f)
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
