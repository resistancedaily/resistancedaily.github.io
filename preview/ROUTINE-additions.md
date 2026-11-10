# Proposed additions to ROUTINE.md (preview, not yet in force)

Nothing below is active. When the owner approves, these paragraphs move into ROUTINE.md and `tools/preview.py`'s pages
move out of `preview/` into the live site.

## COVERAGE FLOOR (add under EDITORIAL STANDARDS)
- Every week (the last 7 editions) must include at least one item about each of: workers, women and girls, Dalit and
  Adivasi communities, people with disabilities, children; and at least one item each on health and on education.
- Every week must include items from at least 5 Indian states other than Delhi and the Northeast, and at least one
  item each from Latin America, Southeast or East Asia, and sub-Saharan Africa outside Sudan.
- The floor is a prompt to look harder, never a licence to lower the bar: an item still needs a real event in the
  window, a named source and the official position. If nothing qualifies, say so in the notification
  ("Coverage floor: no disability item found this week") instead of padding.
- Before STEP 5, run `python3 tools/preview.py` and read coverage/: search specifically for whatever the floor
  shows as missing (e.g. "disability rights", "ASHA workers", "manual scavenging", "anganwadi", the missing states).
- Tag every item with "groups": [...] from: workers, women, dalit-adivasi, religious-minorities, students, migrants,
  journalists, farmers-land, children, disability, prisoners. Tag by who is affected, as the source describes them.

## SOURCE SPREAD (add to the sourcing bullet)
- No single outlet may supply more than 15% of a week's source links. When one is over, find the same fact in another
  credible outlet or a primary document (court order, UN statement, official release) and cite that instead or as well.
- Each week cite at least three Indian-language outlets (read through translation; quote the fact, link the original),
  e.g. Prajavani, Vartha Bharati, Dainik Bhaskar, Anandabazar Patrika, Mathrubhumi, Dinamani, Siasat (Urdu).

## LANGUAGES (new step after STEP 5)
- Write data/i18n/DATE.hi.json and DATE.kn.json: {"items": {"N": [place, headline, text]}} for every item, plus the
  fixed interface strings. Translate plainly, sentence for sentence; keep every number, name, qualifier ("alleged",
  "said", "no response was reported") and the official position. Never add or drop a fact in translation.
- Keep proper nouns and legal terms readers know in Latin letters (UAPA, ICC, FIR as एफ़आईआर / ಎಫ್‌ಐಆರ್).
- Every translated page carries the note that it is machine-assisted and that the English edition prevails.
- Next languages, in order, once a native reader has reviewed a week of Hindi and Kannada: Tamil, Bengali, Urdu.

## ACT TODAY (amend STEP 5)
- At least one of the 4 actions must be usable by a reader outside India (e.g. "Support aid", "Verify, then share").

## CORRECTIONS (new)
- When a published fact is corrected, fix it at the source data and add {date, page, was, now, src} to
  data/corrections.json the same day. Say "Correction" in the notification.
