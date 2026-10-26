# "Reading fly balls"

A 34.5 s vertical (1080×1920, 30 fps) 3D baseball explainer: how outfielders judge fly balls, charge or retreat, and play center field versus the corners.

- **Framework:** the same three.js field, players and render workflow as `first-base`, `sequencing`, `fastball`, `tag-up` and `catcher-clock`, including the split-screen renderer from `first-base`. This project adds:
  - a real outfield (330 ft lines, 375 ft alleys, 400 ft center), a warning track and foul poles;
  - outfield shadows.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.35×. The script is in `transcript.txt`.
- **Sync:** word-timed captions, and the hook builds word by word on top of a frame-one statement.
- **Sound:** mastered to about −14 LUFS. It includes a bat crack at contact (with the crowd lifting after it), glove pops on the catches, and whooshes on the cuts.

```bash
python3 tools/physics.py                                       # five fly balls + fielder routes -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/fly-balls.mp4 --video-bitrate 16M
```

## The model (`tools/physics.py`)

**Ball flight:**
- **Forces:** gravity, drag (Cd 0.40, which reproduces typical Statcast fly-ball carry) and Magnus lift from spin, in 1 ms steps.
- **Spin:** pure backspin only lifts the ball. Tilting the spin axis a few degrees adds a sideways push.
- **Slice and hook:** opposite-field fly balls tend to slice toward the foul line, and pulled ones tend to hook toward it.
- **Kept modest:** an 8° tilt gives **about 13 ft** of drift over a 340 ft fly. Most fly balls drift only a little, and the video says so.
- **Wind:** not modeled. It's mentioned only in the voiceover.

**Fielders:**
- **Movement:** they stand ready until a 0.30 s reaction, then accelerate toward 28 ft/s (time constant 0.75 s) and brake at up to 22 ft/s² to arrive.
- **The read:** each fielder's estimate of the landing point starts at where the ball *first looks* like it's going (the same launch with no sidespin) and settles on the real landing point by about 2 s.
- **Wrong first step:** this fielder commits the wrong way for 0.45 s, then has to stop and turn around.

| Ball | Launch | Lands | Hang time | Fielder's run | Result |
|---|---|---|---|---|---|
| Deep, over the CF's head | 102 mph, 22° | 394 ft (warning track) | 4.7 s | 68 ft back | right first step: there at 3.8 s for a 4.5 s catch · wrong first step: **8 ft short** |
| Shallow, in front of the CF | 71 mph, 35° | 259 ft | 4.4 s | 70 ft in | right: there at 3.8 s for a 4.3 s catch · wrong: **14 ft short** |
| Right-center gap | 90 mph, 27° | 349 ft | 4.7 s | CF 88 ft; the RF converges and backs up | CF there at 4.5 s for a 4.6 s catch |
| Left field, hooking | 88 mph, 28°, axis tilted 8° | 342 ft | 4.7 s | 57 ft | drifts 12.5 ft toward the line |
| Right field, slicing | 88 mph, 29°, axis tilted 8° | 344 ft | 4.9 s | 50 ft | drifts 13 ft toward the line · running straight to the first look leaves him **13 ft off** |

All of these are labeled "3D model" on screen where they appear; they're illustrations, not measurements.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.9 s | "The hardest part of catching a fly ball…" | Contact from behind the plate. Then behind the center fielder: he steps in on a ball going over his head, at ⅓ speed, then a freeze as he turns | **ONE WRONG STEP.** on frame one, the line word by word, then **ONE WRONG STEP CAN COST YOU THE PLAY.** |
| 3.9–10.2 s | "On a shallow ball, you need to charge…" | Split screen, real time: shallow (charge) on the left, deep (turn and run) on the right. A solid fielder takes the right first step and a ghost takes the wrong one; each side freezes at its catch | Flight path, landing marker, routes; "Right first step: caught" / "Wrong first step: 14 ft / 8 ft short" |
| 10.2–18.9 s | "And the read changes with your position…" | Aerial with LF/CF/RF tagged. Then center field into the right-center gap (with the right fielder backing up), left field hooking toward the line, and right field slicing toward the line | Start rings, routes, landing markers; one short tag per position |
| 18.9–24.8 s | "Spin, wind, and contact…" | With the ball at ¼ speed, a subtle spin-axis ring. Then from high over the infield: the same launch with no sidespin (dashed) vs. the real slicing flight, and a fielder who runs to the first look vs. one who adjusts | "Most fly balls drift only a little"; a legend with 13 ft drift, 13 ft off |
| 24.8–32.4 s | "Knowing the hitter's tendencies…" | A right-handed hitter, his opposite-field wedge shaded. Contact on "But once the ball's hit", then behind the right fielder tracking the slicing ball to a clean catch | "Right-handed hitter · fly balls to the opposite field tend to slice toward the line" |
| 32.4–34.5 s | (payoff) | ⅓-speed replay of the first read, then a wide shot | **READ IT. MOVE. ADJUST.**, then **WHAT'S THE HARDEST BALL TO JUDGE?** |
