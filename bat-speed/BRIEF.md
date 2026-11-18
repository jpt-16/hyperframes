---
workflow: faceless-explainer
flow: automation
storyboard: yes
message: "Bat speed comes from the whole body working together, not the arms or hips alone."
destination: instagram-reels-tiktok
aspect: "9:16"
resolution: 1080x1920
length: 40-45s
angle: concept
language: en
audience: serious players, coaches and fans
vo_mode: verbatim
---

# Baseball Decoded: "What actually creates bat speed?"

## Intent
A sports-science documentary breakdown of where bat speed comes from: how the hitter interacts with the ground, pelvis and
torso rotation, and the arms and hands, all coordinated. Six scenes with the user's timings (0–5, 5–13, 13–22, 22–33, 33–42, 42–45 s).

## Assets
- The Baseball Decoded series kit in this repo: the three.js ballpark, the geometric hitter (`makePlayer`), the gloved
  hand rig, the bat, fonts (Barlow Condensed, Inter, Plex Mono) and sound effects. Copied from `hitting-debate`.
- Logo: the series' typographic "Baseball Decoded" mark, the same as the other episodes.
- Voiceover: local Kokoro TTS, voice `am_michael`, like the rest of the series. No paid generators (no Higgsfield).

## Customizations
- The hitter keeps the series' geometric style (user's choice). The anatomy overlay is an x-ray mode: a translucent
  uniform with the colored segments underneath.
- Captions: short, word by word at the top, like the rest of the series.

## Notes: accuracy guardrails (from the user)
- Ground reaction forces are not shown flowing up the body into the bat. Force arrows stay at the feet, and the meaning is "support and help generate the movement".
- No claim that every hitter uses the same sequence. A small on-screen note says sequence and timing vary between hitters.
- Hip rotation alone is never credited. The arms and hands get their own scene.
- Observed movement (rotation, paths) is kept separate from explanations (forces). Nothing measured is invented: no numbers, percentages or mph.
