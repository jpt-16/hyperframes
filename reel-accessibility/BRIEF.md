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

- base_round1.mp4 — the base layer. Five round-1 talking-head clips concatenated
  in chronological order (IMG_1369, 1371, 1375, 1394, 1397), 25.57s total.
  Native 1080x1920 portrait, tone-mapped from HLG HDR to Rec.709 SDR.
  Video and audio both play unmodified; graphics layer on top.

## Customizations

- Overlay beat sheet supplied verbatim by the user (hook stat, no-exemption
  line, 4-item animated checklist, WCAG badge stamp).
- Designed callouts live in the overlay layer rather than in caption lines.
- B-roll requested: user asked for generated material where it helps.

## Notes

- OPEN: user's beat-4 badge copy arrived truncated at "TESTED TO WCA". Built
  with the assumption "TESTED TO WCAG 2.1 AA" — single string in index.html,
  marked with a comment. Confirm or replace.
- OPEN: a beat 5 may exist; the supplied message ended mid-beat-4.
- OPEN: user's spec describes ONE continuous clip at [PATH_TO_MY_VIDEO.mp4],
  a placeholder. Built against the round-1 concatenation as the stand-in;
  swapping the source is a one-line change to the <video>/<audio> src.
- Beat 4 was specced 0:21-0:28 but the base runs 25.57s, so it is clamped to
  21.0-25.57 (4.57s). Extending needs round-2 footage.
- Round 2 footage is still pending.
- Transcription is impossible in this environment: huggingface.co,
  openaipublic.azureedge.net and alphacephei.com are all 403 by egress policy,
  which blocks whisper.cpp, Parakeet and the hyperframes CLI's transcribe alike.
  Word-timed captions need the script as text, or a transcript produced
  off-box.
- Source footage carries rotation=-90; encoded 1920x1080, displays 1080x1920.
  Anything that touches the raw .mov must respect the display matrix.
