#!/usr/bin/env python3
"""Resistance Daily photo helper.

  python3 tools/photos.py commons api.json
      Turn a Wikimedia Commons API response (action=query&prop=imageinfo&iiprop=url|extmetadata|size
      &iiurlwidth=1280&iiextmetadatafilter=LicenseShortName|LicenseUrl|Artist|DateTimeOriginal|ImageDescription|Credit)
      into photo objects for data.json. Fill in "caption" and "alt" yourself, and check the licence page.

  python3 tools/photos.py prepare IN.jpg images/DATE/NAME [--no-blur | --box X,Y,W,H ...]
      Resize to at most 1400px, strip EXIF/GPS, blur detected faces, and write NAME.webp (used by the site and the slides).
      Prints how many faces were blurred so the credit can say "faces blurred". The detector can misfire on
      foliage or rocks: look at the result, and use --no-blur for photos with no identifiable faces, or
      --box X,Y,W,H (fractions of width/height, repeatable) to blur exactly the faces you mark instead.

  python3 tools/photos.py viewer SHOT.png OUT.jpg
      When this environment cannot reach upload.wikimedia.org, view the photo through Firecrawl instead: scrape
      https://commons.wikimedia.org/wiki/File:NAME#/media/File:NAME with formats ["screenshot"], viewport 1600x1150,
      waitFor 4000, download the screenshot, then run this to cut the photo out of the viewer (it drops the viewer's
      black frame, caption bar and corner buttons). Look at the result before using it, then run "prepare".

Rules: only free licences (CC BY, CC BY-SA, CC0, public domain, or agency terms that allow editorial reuse with credit);
no graphic images of the dead or injured; no identifiable children; protesters' faces blurred unless they chose to be shown.
Hotlinked photos cannot be blurred, so use them only when no protester's face is identifiable.
"""
import sys, json, re, html, os

OK_LICENCES = re.compile(r"^(CC BY(-SA)? [0-9.]+( igo)?|CC0|Public domain|PD)", re.I)


def strip(v):
    return html.unescape(re.sub(r"<[^>]+>", "", v or "")).strip()


def commons(path):
    q = json.load(open(path))["query"]["pages"]
    out = []
    for page in q.values():
        ii = page["imageinfo"][0]
        m = {k: strip(v["value"]) for k, v in ii.get("extmetadata", {}).items()}
        lic = m.get("LicenseShortName", "")
        year = re.search(r"(19|20)\d\d", m.get("DateTimeOriginal", ""))
        src = re.sub(r"\?.*$", "", ii.get("thumburl") or ii["url"]).replace("//thumb.wikimedia.org/", "//upload.wikimedia.org/")
        out.append({
            "src": src,
            "alt": "",
            "caption": "",
            "credit": m.get("Artist", "Unknown") + " / Wikimedia Commons",
            "licence": lic,
            "licence_url": m.get("LicenseUrl", "https://commons.wikimedia.org/wiki/Commons:Licensing"),
            "page": ii["descriptionurl"],
            "kind": "file",
            "year": year.group(0) if year else "",
            "_description": m.get("ImageDescription", ""),
            "_licence_ok": bool(OK_LICENCES.match(lic)),
            "_size": [ii.get("width"), ii.get("height")],
        })
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


def prepare(src, dest, blur=True, boxes=()):
    import cv2
    img = cv2.imread(src)
    if img is None:
        sys.exit(f"cannot read {src}")
    h, w = img.shape[:2]
    k = min(1.0, 1400 / max(h, w))
    if k < 1:
        img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    faces = []
    if boxes:
        H, W = img.shape[:2]
        faces = [(int(x * W), int(y * H), int(bw * W), int(bh * H)) for x, y, bw, bh in boxes]
    elif blur:
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
            det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, name))
            faces += [tuple(f) for f in det.detectMultiScale(grey, 1.1, 5, minSize=(18, 18))]
    for (x, y, fw, fh) in faces:
        pad = int(0.25 * max(fw, fh))
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(img.shape[1], x + fw + pad), min(img.shape[0], y + fh + pad)
        roi = img[y0:y1, x0:x1]
        k2 = max(31, (max(fw, fh) // 2) * 2 + 1)
        img[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (k2, k2), 0)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    # Re-encoding from pixels drops all EXIF/GPS metadata.
    cv2.imwrite(dest + ".webp", img, [cv2.IMWRITE_WEBP_QUALITY, 72])
    print(json.dumps({"webp": dest + ".webp", "faces_blurred": len(faces),
                      "size": [img.shape[1], img.shape[0]]}))


def viewer(shot, out):
    from PIL import Image
    import numpy as np
    im = Image.open(shot).convert("RGB")
    a = np.asarray(im).astype(int)
    white = (a.min(axis=2) > 235).mean(axis=1)
    bar = next((y for y in range(int(a.shape[0] * 0.6), a.shape[0]) if white[y] > 0.6), a.shape[0])
    m = a[:bar].max(axis=2) > 22
    ys = np.where(m.mean(axis=1) > 0.3)[0]
    xs = np.where(m.mean(axis=0) > 0.3)[0]
    x0, y0, x1, y1 = int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1
    if x1 > a.shape[1] - 120:  # photo runs under the viewer's corner buttons
        x1 = a.shape[1] - 120
    if y0 < 100 and x1 > a.shape[1] - 130:
        y0 = 100
    im.crop((x0, y0, x1, y1)).save(out, quality=92)
    print(json.dumps({"out": out, "size": [x1 - x0, y1 - y0]}))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "commons":
        commons(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "viewer":
        viewer(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "prepare":
        a = sys.argv
        boxes = [tuple(map(float, a[i + 1].split(","))) for i, v in enumerate(a) if v == "--box"]
        prepare(a[2], a[3], blur="--no-blur" not in a, boxes=boxes)
    else:
        sys.exit(__doc__)
