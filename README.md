# Resistance Daily

A daily, non-partisan public record of human-rights and civil-liberties events in India and around the world.
Live site: https://resistancedaily.github.io/ · Past editions: `archive/` · Contact: resistancedaily.in@gmail.com

## How we report
- Rights, not parties: life and safety, assembly, expression, press freedom, due process, land and livelihood.
- Every number and claim links to its source; independent and ground-level outlets first.
- Official positions sit next to allegations; claims are labelled as claims; ranges shown when figures disagree.

## Rotation (IST weekday)
Mon map · Tue numbers · Wed ledger · Thu front · Fri clock · Sat map · Sun tracker ("Still waiting").

## Build
`cd tools && npm install`, then `node tools/maps.js items.json > data/DATE.maps.json && python3 tools/thin.py data/DATE.maps.json`
and `python3 tools/publish.py DESIGN DATE data/DATE.json [data/DATE.maps.json]`.
