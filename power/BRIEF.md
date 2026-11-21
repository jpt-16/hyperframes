---
workflow: faceless-explainer
flow: automation
storyboard: no
message: "Power is more than muscle: how well a hitter sequences the swing matters as much as how strong he is."
destination: instagram-reels-tiktok
aspect: "9:16"
resolution: 1080x1920
length: 45-55s
angle: concept
language: en
audience: players, coaches and fans
vo_mode: verbatim
---

# Baseball Decoded: "Why some hitters generate more power"

## Intent
A bigger hitter and a smaller one meet the same pitch; the smaller one's ball comes off the bat harder. Strength is real (both do the
same lift), but the difference is how the swing is sequenced: ground, legs, hips, torso, bat. Six scenes on the user's timings.

## Assets
- The Baseball Decoded series kit (field, geometric players, the gym built for this episode), copied from `catcher-hardest`.
- Voiceover: local Kokoro TTS, voice `am_michael`. No paid generators.

## Customizations
- Series geometric style; built in one go (the user's standing preferences).
- Two body builds (bigger and thicker, smaller and leaner) on the same rig; left/right split-screen as the brief asks.

## Notes: accuracy guardrails
- No numbers on screen: the two exit speeds in `tools/physics.py` are illustrative and never shown.
- The sequence visuals are labelled "Illustration of a typical sequence. Timing varies from hitter to hitter."
- The script's own line says energy transfers from the ground through the legs and hips into the bat; the visuals show a coordinated
  sequence lighting up in order, not force flowing into the bat, and the force arrows stay at the feet.
