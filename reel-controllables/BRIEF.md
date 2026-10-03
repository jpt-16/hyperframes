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

## Notes

- IMG_1820 was uploaded twice (byte-identical); used once.
- Lint keeps one false-positive warning on #sx-close's volume fade: it
  fromTo's 0.32 -> 0, matching its data-volume exactly.
