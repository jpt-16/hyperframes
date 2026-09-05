---
workflow: general-video
flow: automation
storyboard: no
message: "Anyone guaranteeing you #1 on Google is lying — Google says so itself"
destination: instagram-reels
aspect: 1080x1920
language: en
audience: small business owners buying SEO
length: 43s
angle: myth-bust
---

## Intent

Vertical Reel debunking SEO "guaranteed #1 ranking" promises, using Google's
own published position as the proof. Bold, high-contrast, fast overlay cuts,
with one deliberately quiet sincere beat before the CTA.

## Assets

- transcript.json — 137 words with onsets. Source of truth for EVERY cue;
  the spec asked for delivery-synced timing, not timecode guesses.
- base_seo.mp4 — three clips normalised to -14 LUFS (two-pass loudnorm,
  linear) and tone-mapped HLG->Rec.709, concatenated in narrative order:
  d45aeb06 (0-19.6) -> 3b8682e9 (19.6-29.7) -> f0e9b4fc (29.7-43.0).
  Sentences run across both cuts, which is what fixes the order.
- .media/audio/sfx/riser-short.mp3, riser-long.mp3 — time-scaled copies of
  the bundled riser. Source peaks at 3.2s, which fits neither the 0.5s pause
  at 2.64 nor the 7.8s build into the cut. Peaks now at 1.20s / 7.20s.
- .media/audio/sfx/tick-1..3.mp3 — sparkle pitched up in three steps for the
  rising checklist pattern.

## Customizations

- Cue sheet supplied verbatim by the user; every cue anchored to a word onset.
- Checklist reuses the ADA reel's card component (dark semi-transparent card,
  white text, tick rows that open one at a time).

## Notes

- BLOCKER: the screen recording of Google Search Central was never uploaded —
  all three files are talking-head clips. developers.google.com is also 403 by
  this environment's egress policy, so it could not be captured either.
  #quote is a STAND-IN: a designed quote card in the reel's own language,
  deliberately NOT a mock of Google's page, because faking a screenshot of
  their documentation would be manufacturing a record. Swap it for the real
  recording when it arrives; the 17.36-21.4 slot and its whoosh/zoom are built.
- UNVERIFIED: the quote wording "No one can guarantee a #1 ranking on Google."
  could not be checked against the live page (blocked). Confirm before publishing.
- Three specced cue anchors are not in the delivered audio:
  "Themselves."      -> not said; stinger moved to "so." (4.72)
  "Red flags"        -> not said; final impact + card clear at 33.2, after
                        "in a week" and before the quiet beat
  "is selling you a lie" -> not said; quiet beat runs to "happen in a week"
- COPY MISMATCH: the CTA overlay says "QUESTIONS? LINK IN BIO" as specified,
  but he actually says "DM me if you have any questions." On-screen and spoken
  instructions disagree. User's call.
- Quiet beat 33.4-41.0 carries no overlay and no SFX, as specified.
