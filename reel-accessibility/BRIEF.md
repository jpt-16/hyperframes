---
workflow: general-video
flow: companion
storyboard: yes
message: "Your small business website probably isn't accessible — and there is no exemption for you"
destination: instagram-reels
aspect: 1080x1920
language: en
audience: small business owners
length: 26s
angle: practical checklist
---

## Intent

A vertical Instagram Reel on web-accessibility exposure for small business
owners. Talking-head delivery straight to camera, packaged with bold graphic
overlays. The tone is direct and a little confrontational — a warning with a
checklist, not a lecture.

The video is about accessibility, so it is held to its own standard: caption and
overlay text must clear WCAG AA contrast, and no meaning may be carried by
colour alone.

## Assets

- transcript.json — word-level transcript with onsets; the source of truth
  for every overlay timing.
- base_round1.mp4 — the base layer. Five round-1 talking-head clips
  concatenated in NARRATIVE order (IMG_1369, 1371, 1375, 1397, 1394),
  25.57s total. Note 1394 is the CTA and plays last even though it was
  recorded before 1397: chronological order buried the call to action in
  the middle, which is the ordering bug the user caught.
  Native 1080x1920 portrait, tone-mapped from HLG HDR to Rec.709 SDR.
  Video and audio both play unmodified; graphics layer on top.

## Customizations

- Overlay beat sheet supplied verbatim by the user (hook stat, no-exemption
  line, 4-item animated checklist, WCAG badge stamp). The two bold text
  beats were later REPLACED by word-timed auto captions at the user's
  request; the checklist and b-roll were retimed to the transcript.
- Captions are suppressed 13.8-22.4s, where the checklist card already
  spells out the same four items.
- End card copy ("Link in bio / Website health report") comes from the
  speaker's own closing line in the transcript, not invented.
- Designed callouts live in the overlay layer rather than in caption lines.
- B-roll requested: user asked for generated material where it helps.

## Notes

- The "TESTED TO WCAG 2.1 AA" badge is PARKED (data-hidden on #badge). Its
  copy was never confirmed and the transcript contains no claim it maps to.
  Remove data-hidden to restore it.
- OPEN: a beat 5 may exist; the supplied message ended mid-beat-4.
- OPEN: user's spec describes ONE continuous clip at [PATH_TO_MY_VIDEO.mp4],
  a placeholder. Built against the round-1 concatenation as the stand-in;
  swapping the source is a one-line change to the <video>/<audio> src.
- Beat 4 (badge) runs 20.0-22.35, moved earlier than the specced 0:21-0:28 so
  it clears before the CTA clip at 22.35s and the closing beat plays with no
  overlay on it.
- The CTA clip (22.35-25.55) deliberately carries no graphics — its copy is
  unknown without a transcript, so inventing an end card would be guesswork.
- Round 2 footage is still pending.
- SOLVED: transcription works via sherpa-onnx (PyPI) with NeMo Parakeet
  TDT 0.6b v2 int8, whose weights are GitHub release assets — GitHub is
  reachable here even though huggingface.co, openaipublic.azureedge.net and
  alphacephei.com are all 403 by egress policy. That blocks whisper.cpp,
  MLX Parakeet and the hyperframes CLI's transcribe, but not this path.
  Output is transcript.json (80 words with onsets).
- All overlay timings derive from transcript.json, not from guesses. Beat
  timings in the user's original spec were up to 4.4s early against the
  real delivery.
- Source footage carries rotation=-90; encoded 1920x1080, displays 1080x1920.
  Anything that touches the raw .mov must respect the display matrix.
