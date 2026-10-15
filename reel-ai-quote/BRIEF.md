---
workflow: general-video
flow: companion
message: "AI systems answer every quote request instantly, even when the owner is busy or closed"
destination: instagram-reels
aspect: 1080x1920
length: 39.6s
---

## Intent
Motion graphics over his talking head (with his own burned-in captions),
illustrating the AI quote system he describes, synced to the transcript.
Clean, not "AI-edited"; risers into every graphic that pops on screen.

## Build
- `tools/prep_base.sh <upload>` → `base.mp4` (gitignored). The upload had a keyframe
  every 4-8 s and full-range colour, which made every seek slow enough to time out
  `hyperframes check`; it is re-encoded once (lanczos 1080x1920, keyframe every 1 s,
  audio copied untouched).
- `python3 build.py` → `index.html`. Every beat is pinned to a word in
  `tools/words.json`; copy, timing and sound levels all live in build.py.
- `python3 tools/make_sfx.py` → risers (0.45/0.75/1.25 s), pops, bubbles, landing
  thump (original), keys.wav (from the Pixabay-licensed bundled typing sound).
- `python3 tools/sfx_levels.py` → offline check of each sound's lift over the voice.

## Layout
Graphics live in the band above his eyes (y 150-650) on a soft dark fade; his face
(y 360-1245) and captions (y 1390-1475) stay clear. Accent = his caption pink #FF0065.

## Story beats
hook "AI systems" → quote form fills + submits → request sits unanswered, timer races
to hours → AI takes over (long riser + land) and asks vehicle / service / availability
→ lead organized + sent to owner → inbox of auto-replies incl. one while closed →
JT Builds Co. → "Own a business?" + comment SYSTEM + DM.

## Notes
- Names, vehicles and the phone number (555) in the demo UI are illustrative.
- Delivery: no extra limiting. His source is already mastered hot (peaks -0.2 dBFS);
  pushing to -15 LUFS would limit his voice 7.5% of the time. Delivered at the
  render's own -15.8 LUFS, -1.7 dBTP.
