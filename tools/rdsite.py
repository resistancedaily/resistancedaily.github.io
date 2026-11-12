#!/usr/bin/env python3
"""Shared page frame for the "Threads" redesign (Nov 2026): <head>, nav bar, footer and small helpers.

Every page links assets/organic.css (the Organic design system, vendored from the design handoff) and assets/rd.css
(page components + dark mode), and loads assets/rd.js (thread player + reader state kept only in localStorage).
Paths are relative ("" on the home page, "../" one folder down) so pages also work as local files and on the backup
artifact.
"""
import os, json, html, datetime
import seo

E = html.escape
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = seo.SITE
SEV = {"red": 0, "orange": 1, "grey": 2}
FONTS = "https://fonts.googleapis.com/css2?family=Caprasimo&family=Figtree:wght@400;600;700&display=swap"
# Favicon recoloured to the Organic palette.
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23201e1d'/%3E"
        "%3Crect x='14' y='18' width='22' height='6' rx='3' fill='%23c67139'/%3E%3Ctext x='14' y='50' font-family='Georgia' font-weight='900' "
        "font-size='26' fill='%23f5ead8'%3ERD%3C/text%3E%3C/svg%3E")
DESC = ("A non-partisan daily record of human-rights and civil-liberties events in India and around the world. "
        "Every fact links to its source.")
HOW = """<li>Rights, not parties: life and safety, assembly, expression, press freedom, due process, land and livelihood.</li>
<li>Every number links to its source, with ground-level reporting first.</li>
<li>The official position sits next to every allegation; when sources disagree we show the range.</li>
<li>Photos are freely licensed and credited; protesters' and children's faces are blurred.</li>
<li>Follows and the stories you have seen are stored only on your device. No accounts, no tracking.</li>"""



def ver(name):
    """Short content hash for asset URLs, so phones fetch new CSS/JS as soon as it changes (no stale cached styles)."""
    import hashlib
    return hashlib.md5(open(os.path.join(root, "assets", name), "rb").read()).hexdigest()[:8]

def load(p):
    return json.load(open(os.path.join(root, p)))


def head(title, desc, prefix, canonical, extra="", noindex=False, css=""):
    """Document start up to <body>. `extra`: og:image, JSON-LD and other tags."""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">{'<meta name="robots" content="noindex">' if noindex else ''}
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:site_name" content="Resistance Daily">
<link rel="canonical" href="{canonical}"><link rel="icon" href="{ICON}">{extra}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{prefix}assets/organic.css?v={ver("organic.css")}"><link rel="stylesheet" href="{prefix}assets/rd.css?v={ver("rd.css")}">{f"<style>{css}</style>" if css else ""}
</head><body><div class="rd-wrap">"""


def nav(prefix):
    return f"""<nav class="rd-nav" aria-label="Site"><a class="rd-brand" href="{prefix or './'}">Resistance Daily</a>
<span class="rd-links"><a href="{prefix}focus/">Threads</a><a href="{prefix}hope/">Rights upheld</a><a href="{prefix}archive/">Archive</a><a href="{prefix}#how">How we report</a></span>
<a class="tag tag-neutral rd-fol" href="{prefix}following/">Following · <span data-rd-follow-count>0</span></a></nav>"""


def footer(prefix):
    socials = "".join(f'<a class="btn btn-secondary" href="{u}">{n}</a>' for n, u in
                      (("WhatsApp", seo.WHATSAPP), ("Instagram", seo.INSTAGRAM), ("X", seo.X), ("Facebook", seo.FACEBOOK)))
    return f"""</div><footer class="rd-foot"><div class="rd-foot-in"><div><b class="rd-brand">Resistance Daily</b>
<p>Tips, photos or corrections: <a href="mailto:resistancedaily.in@gmail.com">resistancedaily.in@gmail.com</a></p>
<p class="rd-foot-small">Non-partisan. Every fact sourced. <a href="{prefix}archive/">Past editions</a></p></div>
<div class="rd-socials">{socials}</div></div></footer>
<div id="rd-player" class="rd-player" hidden role="dialog" aria-modal="true" aria-labelledby="rd-p-name"></div>
<script src="{prefix}assets/rd.js?v={ver("rd.js")}" defer></script>
</body></html>
"""


def editions():
    """Every edition date that has data, oldest first."""
    import glob
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(root, "data", "????-??-??.json")))


def top_item(d):
    return sorted(d["items"], key=lambda i: (not i.get("lead"), SEV[i["sev"]]))[0]


def top_line(date):
    """One line per day: the edition's most serious headline."""
    try:
        h = top_item(load(f"data/{date}.json"))
        return f'{h.get("short", h["place"])}: {h["headline"]}'
    except Exception:
        return ""


def src_links(pairs):
    return " · ".join(f'<a href="{E(u)}">{E(n)}</a>' for n, u in pairs)


# Local-language coverage (owner's request, 12 Nov 2026): an item may carry "local": [[lang, outlet, url], ...], reports
# of the same event in the language of the place it happened. Shown after the sources as "ಕನ್ನಡ: Vartha Bharati".
LANG = {"hi": "हिन्दी", "kn": "ಕನ್ನಡ", "ta": "தமிழ்", "te": "తెలుగు", "ml": "മലയാളം", "bn": "বাংলা", "mr": "मराठी", "gu": "ગુજરાતી",
        "pa": "ਪੰਜਾਬੀ", "or": "ଓଡ଼ିଆ", "as": "অসমীয়া", "ur": "اردو", "ne": "नेपाली", "mni": "ꯃꯤꯇꯩꯂꯣꯟ", "ks": "کٲشُر",
        "ar": "العربية", "fa": "فارسی", "he": "עברית", "tr": "Türkçe", "fr": "Français", "es": "Español", "pt": "Português",
        "de": "Deutsch", "nl": "Nederlands", "no": "Norsk", "sv": "Svenska", "ru": "Русский", "uk": "Українська",
        "zh": "中文", "ja": "日本語", "ko": "한국어", "my": "မြန်မာ", "th": "ไทย", "id": "Bahasa Indonesia", "sw": "Kiswahili",
        "am": "አማርኛ", "si": "සිංහල", "ps": "پښتو"}


def local_links(item):
    """' · ಕನ್ನಡ: <a>Outlet</a>' for each entry of item["local"]; empty when there is none."""
    return "".join(f' · <span lang="{E(l)}">{E(LANG.get(l, l))}</span>: <a href="{E(u)}" hreflang="{E(l)}">{E(n)}</a>'
                   for l, n, u in item.get("local", []))


def photo_label(p):
    return "Photo from the event" if p.get("kind") == "event" else f"File photo · {p.get('year', '')}"


def photo_credit(p):
    ch = f" ({E(p['changes'])})" if p.get("changes") else ""
    return (f'Photo: <a href="{E(p["page"])}">{E(p["credit"])}</a>, '
            f'<a href="{E(p["licence_url"])}">{E(p["licence"])}</a>{ch}')


def rel(src, prefix):
    """Site path -> path relative to the page (remote URLs unchanged)."""
    return src if src.startswith(("http://", "https://")) else prefix + src


def nice(date, fmt="%a %d %b"):
    return datetime.date.fromisoformat(date).strftime(fmt).replace(" 0", " ").lstrip("0")
