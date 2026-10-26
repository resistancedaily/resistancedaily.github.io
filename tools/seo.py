#!/usr/bin/env python3
"""Search and sharing helpers for Resistance Daily, used by publish.py and focus.py.

  share_image(root, src, out)   1200x630 JPEG for link previews (og:image); WhatsApp, LinkedIn and others
                                 do not all show .webp. Returns the site path, or None if Pillow is missing.
  text_card(root, out, kicker, lines)  1200x630 text card used instead when an edition has no photo (e.g. Sundays)
  jsonld(obj)                   <script type="application/ld+json"> block (schema.org NewsArticle etc.)
  write_sitemap(root)           sitemap.xml (home, archive, every edition, every Focus) and robots.txt
"""
import os, json, glob, datetime

SITE = "https://resistancedaily.github.io/"
WHATSAPP = "https://whatsapp.com/channel/0029VbDijNkEVccEwHzXq62A"
FACEBOOK = "https://www.facebook.com/resistancedaily.in"
X = "https://x.com/ResistDaily_in"
INSTAGRAM = "https://www.instagram.com/resistance.daily/"
# Official accounts (search engines use sameAs to tie them to the site).
SAME_AS = [INSTAGRAM, WHATSAPP, FACEBOOK, X]
FOLLOW = (f'Follow: <a href="{INSTAGRAM}">Instagram</a> · <a href="{WHATSAPP}">WhatsApp</a> · '
          f'<a href="{FACEBOOK}">Facebook</a> · <a href="{X}">X</a>')
PUBLISHER = {"@type": "Organization", "name": "Resistance Daily", "url": SITE, "email": "resistancedaily.in@gmail.com", "sameAs": SAME_AS}


def share_image(root, src, out):
    """Crop the photo at site path `src` to 1200x630 and save it at site path `out` (JPEG)."""
    try:
        from PIL import Image
    except Exception:
        print("note: Pillow not available; link previews keep the .webp photo")
        return None
    dst = os.path.join(root, out)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(os.path.join(root, src)).convert("RGB")
    w, h = im.size
    tw, th = 1200, 630
    s = max(tw / w, th / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(dst, "JPEG", quality=85, optimize=True, progressive=True)
    return out


def text_card(root, out, kicker, lines):
    """1200x630 JPEG for link previews when no photo exists (e.g. Sunday "Still waiting"): masthead, kicker, up to 3 lines."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("note: Pillow not available; no link-preview image")
        return None

    def font(names, size):
        for n in names:
            for d in ("/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu"):
                p = os.path.join(d, n)
                if os.path.exists(p):
                    return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    bold, reg = ["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"], ["LiberationSans-Regular.ttf", "DejaVuSans.ttf"]
    im = Image.new("RGB", (1200, 630), "#15181d")
    dr = ImageDraw.Draw(im)
    dr.rectangle((80, 80, 200, 92), fill="#d9661a")
    dr.text((80, 116), "RESISTANCE DAILY", font=font(bold, 84), fill="#f3f4f2")
    dr.text((80, 230), kicker.upper(), font=font(bold, 30), fill="#f08a3c")
    f, y = font(reg, 34), 300
    for line in lines[:3]:
        while dr.textlength(line, font=f) > 1040 and len(line) > 4:
            line = line[:-2].rstrip() + "…"
        dr.text((80, y), line, font=f, fill="#eceae5")
        y += 56
    dr.text((80, 545), "Non-partisan · Every fact sourced · resistancedaily.github.io", font=font(reg, 26), fill="#9ba1aa")
    dst = os.path.join(root, out)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, "JPEG", quality=88, optimize=True, progressive=True)
    return out


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def write_sitemap(root):
    urls = []  # (loc, lastmod)
    eds = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(root, "archive", "????-??-??.html")))
    if eds:
        urls += [(SITE, eds[-1]), (SITE + "archive/", eds[-1])]
    foc = []
    for p in glob.glob(os.path.join(root, "data", "focus", "*.json")):
        f = json.load(open(p))
        if os.path.exists(os.path.join(root, "focus", f["slug"] + ".html")):
            foc.append((SITE + "focus/" + f["slug"] + ".html", f["updated"]))
    if foc:
        urls.append((SITE + "focus/", max(d for _, d in foc)))
    urls += sorted(foc, key=lambda x: x[1], reverse=True)
    urls += [(f"{SITE}archive/{d}.html", d) for d in reversed(eds)]
    rows = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    open(os.path.join(root, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")
    # Open to every crawler, search engines and AI search tools alike: the record is public and meant to be found.
    open(os.path.join(root, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n")


def iso(d):
    """Date string YYYY-MM-DD as an ISO time at 09:00 IST, when editions are published."""
    return datetime.date.fromisoformat(d).isoformat() + "T09:00:00+05:30"
