#!/usr/bin/env python3
"""links/index.html: one page for the Instagram bio link (owner's request, 10 Nov 2026), instead of a list of links in
the profile. Big tappable rows: today's edition (with its top headline), the newest Focus, the site's sections, then the
channels to follow and the tips address. publish.py rebuilds it with every edition, so it is always current.

Usage (from the repo root): python3 tools/links.py [YYYY-MM-DD]   (default: latest edition)
Bio link: https://resistancedaily.github.io/links/
"""
import os, sys, json, glob, html
import rdsite as S
import seo

E = html.escape
root = S.root

CSS = """
.rd-wrap{max-width:560px;gap:22px}
.lk-top{display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px;padding-top:6px}
.lk-logo{width:76px;height:76px;border-radius:50%;background:#201e1d;display:grid;place-items:center;font-family:var(--font-heading);font-size:30px;color:#f5ead8;position:relative}
.lk-logo::before{content:"";position:absolute;top:20px;left:22px;width:22px;height:5px;border-radius:3px;background:#c67139}
.lk-top h1{font-size:30px;margin:4px 0 0}
.lk-top p{margin:0;font-size:15px;color:var(--color-neutral-800)}
.lk-list{display:flex;flex-direction:column;gap:12px}
.lk{display:flex;align-items:center;gap:14px;background:var(--color-surface);border-radius:24px;padding:16px 18px 16px 20px;text-decoration:none;color:var(--color-text);transition:background .15s}
.lk:hover{background:var(--color-neutral-300)}
.lk b{display:block;font-family:var(--font-heading);font-weight:400;font-size:18px;line-height:1.2}
.lk span{display:block;font-size:13.5px;color:var(--color-neutral-700);margin-top:3px;line-height:1.35}
.lk i{margin-left:auto;flex:none;width:32px;height:32px;border-radius:50%;background:var(--color-neutral-100);display:flex;align-items:center;justify-content:center;color:var(--color-text)}
.lk i svg{display:block;width:16px;height:16px}
.lk-main{background:#b2622d;color:#fff}
.lk-main:hover{background:#8c491a}
.lk-main span{color:#ffe1d0}
.lk-main i{background:rgba(255,255,255,.18);color:#fff}
.lk-hope{background:var(--color-accent-2-200);color:var(--color-accent-2-900)}
.lk-hope span{color:var(--color-accent-2-800)}
.lk-h{font-size:12.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--color-neutral-700);margin:6px 0 -4px 6px}
.lk-soc{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.lk-soc a{display:flex;align-items:center;justify-content:center;min-height:52px;border-radius:999px;border:1px solid var(--color-divider);text-decoration:none;color:var(--color-text);font-family:var(--font-heading);font-size:16px}
.lk-soc a:hover{background:var(--color-neutral-200)}
.lk-soc a{border:0;color:#fff;font-weight:400}
.lk-soc a:hover{filter:brightness(.92);background-blend-mode:normal}
.lk-soc a.wa{grid-column:1/-1;background:#25D366;color:#073b1c}
.lk-soc a.ig{background:linear-gradient(45deg,#f58529,#dd2a7b 45%,#8134af 75%,#515bd4)}
.lk-soc a.x{background:#000}
.lk-soc a.fb{grid-column:1/-1;background:#1877F2}
.lk-foot{text-align:center;font-size:13.5px;color:var(--color-neutral-700);margin:4px 0 20px}
.lk-foot a{color:var(--color-accent-700)}
"""


ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'stroke-linejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')


def row(href, title, sub="", cls=""):
    return (f'<a class="lk{(" " + cls) if cls else ""}" href="{E(href)}"><div><b>{E(title)}</b>'
            f'{f"<span>{E(sub)}</span>" if sub else ""}</div><i aria-hidden="true">{ARROW}</i></a>')


def build(date=None):
    date = date or S.editions()[-1]
    p = "../"
    d = S.load(f"data/{date}.json")
    top = S.top_line(date)
    foc = sorted((json.load(open(f)) for f in glob.glob(os.path.join(root, "data", "focus", "*.json"))),
                 key=lambda f: f.get("updated", ""), reverse=True)
    foc = [f for f in foc if os.path.exists(os.path.join(root, "focus", f["slug"] + ".html"))]
    pick = [x["slug"] for x in d.get("focus", [])]           # the Focus today's edition features comes first
    foc.sort(key=lambda f: f["slug"] not in pick)
    rows = [row(p, f"Today's edition · {d['date_long']}", top, "lk-main")]
    if foc:
        f = foc[0]
        rows.append(row(f'{p}focus/{f["slug"]}.html', f'In focus: {f.get("short") or f["title"]}',
                        f'Updated {S.nice(f["updated"], "%d %b")}'))
    rows.append(row(f"{p}focus/", "All threads and Focus stories", "Long-running stories, every update"))
    rows.append(row(f"{p}hope/", "Rights upheld", "Courts, releases, people helping people", "lk-hope"))
    rows.append(row(f"{p}still-waiting/", "Still waiting", "People held for a long time, with days counted"))
    rows.append(row(f"{p}accountability/", "Accountability Watch", "Abuse of power, followed to the outcome"))
    rows.append(row(f"{p}archive/", "Past editions"))
    soc = (f'<a class="wa" href="{seo.WHATSAPP}">Follow on WhatsApp</a><a class="ig" href="{seo.INSTAGRAM}">Instagram</a>'
           f'<a class="x" href="{seo.X}">X (Twitter)</a><a class="fb" href="{seo.FACEBOOK}">Facebook</a>')
    body = (f'<header class="lk-top"><div class="lk-logo" aria-hidden="true">RD</div><h1>Resistance Daily</h1>'
            f'<p>What happened to people\'s rights in the last 24 hours. New edition 9am IST.</p></header>'
            f'<nav class="lk-list" aria-label="Read">{"".join(rows)}</nav>'
            f'<p class="lk-h">Follow</p><nav class="lk-soc" aria-label="Follow">{soc}</nav>'
            f'<p class="lk-foot">Non-partisan. Every fact sourced.<br>Tips, photos or corrections: '
            f'<a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a></p>')
    url = f"{S.SITE}links/"
    extra = f'<meta property="og:image" content="{S.SITE}images/{date}/share.jpg"><meta property="og:url" content="{url}">'
    html_ = (S.head("Resistance Daily · Links", "Today's edition, Focus stories and where to follow Resistance Daily.",
                    p, url, extra, css=CSS) + body + "</div></body></html>\n")
    os.makedirs(os.path.join(root, "links"), exist_ok=True)
    open(os.path.join(root, "links", "index.html"), "w").write(html_)
    print("built links/index.html", date)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
