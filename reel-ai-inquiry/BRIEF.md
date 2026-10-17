---
workflow: general-video
flow: companion
message: "Your next customer could be lost before you read their message - an AI system replies, collects, organizes"
destination: instagram-reels
aspect: 1080x1920
length: 40.3s
---

## Intent
Engaging captions, motion graphics and B-roll so the reel isn't a talking head
throughout; risers/impacts on every graphic that lands.

## Build
- `tools/prep_media.sh <talking-head> <demo>` -> media/ (gitignored): three retimed
  demo segments at 2160 px, one website still, un-cut reference copy.
- `python3 tools/cut_base.py <talking-head>` -> media/base.mp4 with the pauses and
  the filler "Basically," removed (tools/cuts.json: 10 ranges, 2.73 s, all inside
  measured silence, picture and sound cut on the same frames). build.py maps every
  original-clock time onto the cut clock, so the cut list can be edited freely.
- `python3 build.py` -> index.html. Beats pinned to words in tools/words.json.
- `python3 tools/sfx_levels.py` -> offline check of each sound's lift over the voice.

## Structure
0-3.6 hook (unread notification) / 3.6-9.4 cutaway: inbox nobody answers /
9.6-14.6 owner busy + request arrives + the real website / 14.6-21.9 cutaway:
the AI system (respond, collect, organize, automatic) / 22.4 "HERE'S HOW IT
WORKS" / 23.87-37.23 his split-screen: sharp demo crops replace his low-res strip,
synced (form -> AI reply -> saved + dashboard), step chips / 38.6 comment SYSTEM /
40 JT Builds Co. lockup (logo style).

## Notes
- Captions: Montserrat (his logo's face), spoken word turns the demo's green.
- Demo honesty: the demo's own DEMO MODE badge stays visible in the crops.
- Stock B-roll: vidIQ found free Pexels detailing clips (credit required), but this
  environment's network policy blocks pexels.com / videos.pexels.com, and the
  Higgsfield account has 0 credits. Drop a clip at media/broll-detailing.mp4 and
  rebuild: it becomes a full-screen cutaway on "working on a car".
- Voice untouched (-14 LUFS source); delivered at -15.2 LUFS, -1.5 dBTP, no limiting.
