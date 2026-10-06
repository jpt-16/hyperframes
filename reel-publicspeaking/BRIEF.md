---
workflow: general-video
flow: companion
message: "Public speaking is the class that teaches confidence, and confidence is the whole point"
destination: instagram-reels
aspect: 1080x1920
length: 64s
---

## Intent

Talking-head Reel on why public speaking matters. The user asked for a good
edit with captions that look nice, and for it not to look AI-made. The same
organic-edit standards as reel-controllables apply: natural pauses kept, no
metronome cutting, no default zooms, no stock whooshes, sparse SFX.

## Edit

- Order: IMG_1842 (hook) -> 1863 (why people fear it) -> 1853 (it teaches
  confidence) -> 1866 (the stakes in business) -> 1861 (still nervous,
  recommendation, "get in the spotlight").
- IMG_1856 is a rougher take of the 1866 point and is left out.
- Only two pauses shortened (1863: 1.10s -> 0.45s; 1866: 0.95s -> 0.5s).
- HLG HDR tone-mapped to Rec.709 (npl 203). Audio chain in tools/base.py.

## Captions

- Bricolage Grotesque, sentence case, phrase-optimised breaks (tools in build.py),
  dark outline for legibility on the light shirt, warm marker block on the
  word being spoken.
- "confidence." is promoted once, at the thesis line, and is the only big word.

## Motion + sound

- Stage spotlight on "under the spotlight ... pressure on them", off on the
  cut; called back on "get in the spotlight" to the end.
- SFX: stage-light throw on each spotlight (synthesised, assets/sfx/gen.py),
  one soft pop on "confidence." Nothing else.
