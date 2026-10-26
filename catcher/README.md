# "The complete catcher"

A 44.7 s vertical (1080×1920, 30 fps) 3D baseball explainer: the six skills that make a complete catcher. Those skills are pitch calling, framing, blocking, throwing, hitting and speed.

- **Framework:** the same three.js field, players and render workflow as `ground-balls`, `fly-balls`, `first-base` and the earlier Baseball Decoded videos. This project adds:
  - catcher's gear and finger signs;
  - a strike-zone graphic;
  - a pitcher's delivery;
  - a stolen-base play with a slide and a tag;
  - the catcher batting, then running.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.2×. The script is in `transcript.txt`. Each skill in the closing list is voiced as its own clip with a short beat after it, so every callback gets a clean cut.
- **Sync:** word-timed captions, and the hook builds word by word on top of a frame-one statement.
- **Sound:** mastered to about −14 LUFS. Effects include pitch whooshes, glove pops, the ball in the dirt, the throw, the tag, the slide, the bat crack and footsteps.

```bash
python3 tools/physics.py                                       # pitches, the steal, the double, the runner -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/complete-catcher.mp4 --video-bitrate 16M
```

## The model (`tools/physics.py`)

**Pitches:** each pitch is thrown by a right-handed pitcher and simulated with gravity, drag and Magnus lift. Each one is aimed iteratively until it crosses the plate at its target.

| Pitch | Speed | Where it goes |
|---|---|---|
| Slider (the chase) | 85 mph | Low and away, off the plate |
| Fastball (framing) | 94 mph | The bottom edge of the zone: borderline |
| Fastball (the steal) | 93 mph | Up, so it's a clean catch to throw from |
| Curveball in the dirt | 79 mph | Bounces about 6.5 ft in front of the plate and comes up into the catcher's chest |

**Stolen base:**
- **The runner:** leads 13 ft off first and accelerates toward 28.5 ft/s.
- **The catcher:** exchange, footwork and release, then a throw to the bag. The tag goes down just before the runner's slide reaches it.
- **Times are illustrative.** No pop time or runner time is shown on screen.

**The double:** 99 mph at 16°, into the left-center gap. It lands at about 336 ft and rolls to the wall.

**No statistics are claimed.** The video doesn't quote framing runs, pop times, ABS challenge numbers or sprint speeds.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.4 s | "Being a catcher is about way more than catching the ball." | The catcher behind the plate, with white-flash cuts to the slider, a block, the throw to second and a swing. Then back on him as a pitch pops his glove on "ball" | **BEING A CATCHER IS MORE THAN YOU THINK.** from frame one |
| 3.4–10.9 s | "First, you have to call the game…" | The sign between his thighs (two fingers: slider). From center field, the hitter chases the slider on "tendencies". The pitcher nods from the mound. Then an overhead zone view: the chase area, the pitch's path, the target ring | **1 · Pitch calling**. The plan card: Count 1–2 (on "situation"), Pitcher's strength his slider (on "pitcher"), Location low and away (on "weaknesses") |
| 10.9–18.5 s | "Then there's framing…" | A borderline fastball at the bottom edge, called a strike. A ½-speed replay of the quiet glove held there. Then the zone graphic with the pitch's mark | **2 · Framing**. Cards: "Umpire's call: receiving can influence borderline pitches" / "ABS: the call can be challenged, or made by the system" |
| 18.5–22.7 s | "You have to block balls in the dirt…" | A curveball in the dirt. He drops and smothers it on "block", real time, then a ½-speed replay. Then the runner holding at first | **3 · Blocking**. "Drop · square up · keep it in front", "The runner stays at first" |
| 22.7–28.4 s | "And when someone steals…" | The steal from behind the plate, real time, then ½ speed through the catch; the release lands on "arm". Then at second base: the throw arrives, the shortstop's tag, the slide | **4 · Throwing**. Chips: Exchange → Footwork → Arm → Accuracy, each on its word. "Tag down before he gets there" |
| 28.4–31.8 s | "But the best all-around catchers…" | The catcher at bat. Contact, then following the ball into the gap | **5 · Hitting** |
| 31.8–34.5 s | "And if you can run? That's another weapon." | He sprints down the line and rounds first | **6 · Speed**. "An added weapon, not a requirement" |
| 34.5–39.8 s | "Pitch calling. Framing. Blocking. Throwing. Hitting. Speed." | A callback to each skill as it's named | **6 SKILLS.**, with a label for each skill |
| 39.8–44.7 s | "A complete catcher can change the game…" | Back behind the plate: one more pitch received, at ½ speed | **6 SKILLS. ONE COMPLETE CATCHER.** |
