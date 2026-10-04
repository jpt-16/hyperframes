---
workflow: general-video
flow: automation
storyboard: no
message: "Control the controllables — and I'm holding myself to it"
destination: instagram-reels
aspect: 1080x1920
language: en
length: 71s
angle: reflective, personal
---

## Intent

User brief: remove the clinical, AI-generated feel. Human, organic,
intentional pacing and sound. Understated visuals; raw energy over polish.

## Decisions

- Pacing: natural pauses and breaths kept. Only dead air over 0.9s was
  shortened (one instance, 0.57s total removed across 71.7s). Longer pauses
  keep proportionally more. No per-sentence zooms; one slow push-in across
  the confession clip, reset by the next cut.
- Sound: three accents for three structural shifts, none from a stock
  library — all synthesised for this piece (sfx.py in the session scratchpad):
  sub-boom on the open; a vinyl-crackle swell under "this applies directly in
  business too" resolving into an analog thud on the cut into "If I'm being
  honest"; a quieter boom reprise on the cut into the sign-off, faded with it.
- Voice: declip, 75 Hz highpass, 2:1 compression, plain gain, one 4x-
  oversampled limiter. Mastered to -16 LUFS rather than -14: at -14 the
  limiter would work on 3.5% of the speech (up to 3.6 dB); at -16 it is
  idle 99.9% of the time (max 1.6 dB), which keeps the dynamics organic.
- Captions: sentence case, warm off-white, soft plate, phrase-sized chunks
  that follow his rhythm (0.84-2.60s), not a fixed word count.
- Video and audio cut on identical frame boundaries: 71.1333s each, 0 ms apart.

- Motion graphics (user asked for some, explicitly "not AI generic slop"):
  a hand-drawn layer built from the registry's hw family (hw-callout-circle,
  hw-underline, hw-boil, lifted into hw-helpers.js/.css) with Caveat.
  Content-driven, not decorative: a circle of control drawn as he describes
  it; the four things he admits he could do more as an UNCHECKED list; the
  list returns on "content creation" and only "more content" gets a check on
  "videos" — the video's single colour accent. It sits in the clear band
  above his eyes (the face is low in these clips) on a feathered shade.
- SFX files are normalised to -3 dBFS AFTER their processing: band-limiting
  and the room echo had cost ~17 dB, which is why the first cut's crackle
  swell was silent. Levels verified by offline mix: swell +2.6 dB in its band
  at the crest (+0.6 overall), thud +0.9 / +1.3, booms unchanged from v1.

## Notes

- IMG_1820 was uploaded twice (byte-identical); used once.
- Lint keeps one false-positive warning on #sx-close's volume fade: it
  fromTo's 0.32 -> 0, matching its data-volume exactly.
