# "The complete catcher"

A 44.0 s vertical (1080×1920, 30 fps) 3D baseball explainer: the six skills that make a complete catcher. Those skills are pitch calling, framing, blocking, throwing, hitting and speed.

- **Framework:** the same three.js field, players and render workflow as `ground-balls`, `fly-balls`, `first-base` and the earlier Baseball Decoded videos. This project adds:
  - catcher's gear and finger signs;
  - a strike-zone graphic;
  - a pitcher's delivery;
  - a stolen-base play with a slide and a tag;
  - the catcher batting, then running.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.35×. The script is in `transcript.txt`.
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
| 0–2.0 s | "Being a catcher is more than you think." | The catcher behind the plate, with white-flash cuts to the slider, a block, the throw to second and a swing | **BEING A CATCHER IS MORE THAN YOU THINK.** from frame one |
| 2.0–10.1 s | "It starts with calling the game…" | The sign between his thighs (two fingers: slider). From center field, the hitter chases the slider. The pitcher nods from the mound. Then an overhead zone view: the chase area, the pitch's path, the target ring | **1 · Pitch calling**. The plan card: Count 1–2, Location low and away, Pitcher's strength his slider |
| 10.1–20.7 s | "Then he has to receive it…" | A borderline fastball at the bottom edge, called a strike. A ½-speed replay of the quiet glove held there. Then the zone graphic with the pitch's mark | **2 · Framing**. Cards: "Umpire's call: receiving can influence borderline pitches" / "ABS: the call can be challenged, or made by the system" |
| 20.7–26.1 s | "With runners on, a ball in the dirt…" | A curveball in the dirt. He drops to his knees and smothers it, real time, then a ½-speed replay. Then the runner holding at first | **3 · Blocking**. "Drop · square up · keep it in front", "The runner stays at first" |
| 26.1–30.8 s | "When the runner goes…" | The steal from behind the plate, real time, then at ½ speed. Then at second base: the shortstop's tag and the slide | **4 · Throwing**. Chips: Exchange → Footwork → Release → On the bag. "Tag down before he gets there" |
| 30.8–34.0 s | "A complete catcher can help at the plate…" | The catcher at bat. Contact, then following the ball into the gap | **5 · Hitting** |
| 34.0–38.2 s | "And if he can run…" | He sprints out of the box and rounds first | **6 · Speed**. "A bonus, not a requirement" |
| 38.2–44.0 s | "Six skills…" | 0.5 s callbacks to each skill, then back behind the plate | **6 SKILLS. ONE COMPLETE CATCHER.** |
