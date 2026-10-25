# Resistance Daily

A daily, non-partisan public record of human-rights and civil-liberties events in India and around the world.
Live site: https://resistancedaily.github.io/ · Past editions: `archive/` · Contact: resistancedaily.in@gmail.com

## Routine
The daily routine's instructions live in [ROUTINE.md](ROUTINE.md); its scheduled prompt only loads that file. Change the routine by changing ROUTINE.md.

## How we report
- Rights, not parties: life and safety, assembly, expression, press freedom, due process, land and livelihood.
- Every number and claim links to its source; independent and ground-level outlets first.
- Official positions sit next to allegations; claims are labelled as claims; ranges shown when figures disagree.

## Rotation (IST weekday)
Mon map · Tue numbers · Wed ledger · Thu front · Fri clock · Sat map · Sun tracker ("Still waiting").

## Build
`cd tools && npm install`, then `node tools/maps.js items.json > data/DATE.maps.json && python3 tools/thin.py data/DATE.maps.json`
and `python3 tools/publish.py DESIGN DATE data/DATE.json [data/DATE.maps.json]`.

## Photos
- Every item with a summary gets a photo; one-line briefs do not. First choice: a photo of the event itself. Otherwise a
  file photo of the place for context (e.g. Jantar Mantar for a Delhi protest story). No photo rather than a misleading one.
  Sources, in order: Wikimedia Commons (CC BY, CC BY-SA, CC0,
  public domain), UN and humanitarian agencies whose terms allow reuse with credit, government press photos, Creative
  Commons Flickr, and reader photos sent with permission. Never agency/newspaper photos we have no licence for, and never AI images.
- Every photo is looked at before use: no graphic images of the dead or injured, protesters' and
  children's faces blurred (other adults unblurred unless the photo puts them at particular risk), and the caption must match what the photo shows (Commons titles can be wrong).
- Labels: "File photo · YEAR" for an older picture of the place; "Photo from the event" only when it shows the event.
  Credit line: photographer / source, licence (with link), and changes such as "cropped" or "faces blurred".
- Tools: `python3 tools/photos.py commons api.json` (metadata), `viewer` (cut a photo out of a Commons viewer
  screenshot when the environment cannot reach upload.wikimedia.org), `prepare` (resize, strip EXIF, blur faces → images/DATE/NAME.webp).
  In data.json an item takes an optional `"photo"` object; see the header of tools/design.py.

## Focus
One place or issue told through 3–8 photos with a short, fully sourced write-up. Made whenever enough good photos exist.
`data/focus/SLUG.json` → `python3 tools/focus.py SLUG` builds `focus/SLUG.html` and `focus/index.html`;
add `"focus": [...]` to data.json to show an "In focus" card on the daily page.
Optional `"seo_title"` (the search-friendly page title) and `"whats_new"` (the latest development, shown at the top).

## Search and sharing
`tools/seo.py` (run by publish.py and focus.py) writes `sitemap.xml`, `robots.txt`, schema.org NewsArticle data and
1200x630 link-preview images (`share.jpg`).

## Instagram
`python3 tools/slides.py daily DATE OUTDIR` (needs data/DATE.slides.json) and `python3 tools/slides.py focus SLUG OUTDIR` (add `--update` for an update post; see ROUTINE.md, Instagram updates).
Python packages: playwright, pillow, "opencv-python-headless<5".
