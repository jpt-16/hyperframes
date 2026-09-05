---
workflow: general-video
flow: automation
storyboard: no
message: "Anyone guaranteeing you #1 on Google is lying — Google says so itself"
destination: instagram-reels
aspect: 1080x1920
language: en
audience: small business owners buying SEO
length: 39s
angle: myth-bust
---

## Intent

Vertical Reel debunking SEO "guaranteed #1 ranking" promises, using Google's
own published position as the proof. Bold, high-contrast, fast overlay cuts,
with one deliberately quiet sincere beat before the CTA.

## Assets

- transcript.json — 137 words with onsets, re-derived AFTER the pause cut.
  Source of truth for every cue.
- cues.json / anchors.json — the 32 caption cues and the anchor times every
  beat is pinned to.
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
- REVISED: the five bold text overlays were replaced by 32 word-timed auto
  captions, and 4.07s of pauses were cut from the base (43.04s -> 38.90s).
  The spec's original "no auto-generated captions" line is superseded.
- Captions are suppressed under the quote card and the checklist, where the
  card already carries the same words.
- Captions DO run through the sincere beat. The brief's "no text overlays"
  there meant no punchy cues; captions are a continuous accessibility layer,
  and dropping them would leave the most important 6.5s uncaptioned. The beat
  still carries no SFX and no cards.
- The pause before the sincere beat is trimmed to 0.35s rather than the 0.12s
  used elsewhere: that silence is doing real work.
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
- RESOLVED: the "QUESTIONS? LINK IN BIO" overlay is gone with the other bold
  text beats, so the on-screen/spoken conflict with "DM me if you have any
  questions" no longer exists. Captions now show what he actually says.
- ASR CORRECTION: Parakeet heard the opening "Someone" as "No one", which
  inverts the argument. Cue 1 is hand-corrected in cues.json. Any re-run of
  the caption generator must re-apply it.
- Quiet beat 33.4-41.0 carries no overlay and no SFX, as specified.
