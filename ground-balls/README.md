# "Work through the ball"

A 34.3 s vertical (1080×1920, 30 fps) 3D baseball explainer: why infielders read the hop and work through ground balls instead of letting the ball play them.

- **Framework:** the same three.js field, players, split-screen renderer and workflow as `fly-balls`, `first-base` and the earlier Baseball Decoded videos.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.3×. The script is in `transcript.txt`.
- **Sync:** word-timed captions, and the hook builds word by word on top of a frame-one statement.
- **Sound:** mastered to about −14 LUFS. Effects are placed on the bat crack, each bounce off the dirt, the glove, the footwork steps after the field, the throw and the first baseman's glove.

```bash
python3 tools/physics.py                                       # four ground balls (bounces) + the shortstop's plays -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/ground-balls.mp4 --video-bitrate 16M
```

## The balls (`tools/physics.py`)

Each ball is an ordinary ground ball hit down into the dirt in front of the plate, toward the shortstop (17° to the third-base side of center). He starts 146 ft from the plate.

**Physics:**
- **In the air:** gravity and air drag.
- **Each bounce:** the vertical speed reverses and keeps 50–55% of its size (a firm infield). The speed along the ground keeps 88%.
- **Rolling:** low skips turn into a roll.

The hop pattern near the shortstop comes out of those bounces. Nothing is hand-drawn.

| Ball | Launch | Hops near the shortstop | How he plays it |
|---|---|---|---|
| Awkward | 93 mph, −16° | A long hop lands 7 ft in front of his spot | **Waiting flat-footed:** an in-between hop, rising at about knee height as it reaches him, fielded at his body. **Working through it:** about 10 ft of angled approach takes the end of the big hop, out in front at a comfortable 1.2 ft |
| Routine | 66 mph, −28° | A readable 2 ft hop | Attacks it and fields it in stride, 12 ft in, at 1.2 ft |
| Short hop | 69 mph, −24° | Bounces right where he meets it (138 ft) | Comes in under control and fields the short hop 0.27 ft off the ground: lower, wider, glove out front |
| High hop | 63 mph, −36° | A chopper whose hop would be about 2.9 ft high at his spot | Backs up about 5 ft and takes it at 1.45 ft as it comes down |

**The shortstop:**
- **Approach:** a 0.25 s first move, then a choreographed route to a spot where the ball is at a playable height and he can get there under control.
- **Glove on the ball:** his body is nudged so his glove meets the ball exactly at the field.
- **Footwork after the field:** waiting and gathering takes a gather plus three reset steps before the throw. Working through it takes a step through and a plant.
- **Times:** glove-to-release times are illustrative values for each technique. **The video never shows times or claims a time saving.** The payoff only shows where each release happens and how many steps it took (labeled "3D model · same ball, same shortstop").

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.8 s | "Great infielders don't just field the ball…" | Contact from behind the plate, then low behind the flat-footed shortstop as the long hop comes in, ½ speed, then a freeze as it kicks up at his feet | **DON'T LET THE BALL PLAY YOU.** (frame one and the freeze), the line word by word |
| 3.8–9.7 s | "If you wait for the ball…" | On from the freeze: the late field at his body, the gather, the throw (wide). Then a ½-speed replay from the side | "Fields it at his body", "Extra steps to reset: 1 · 2 · 3" counting as each foot lands, "Then the throw, from a standstill" |
| 9.7–17.8 s | "You have to read the hop…" | Split: routine hop (attack it) and short hop (stay down). Then the high hop square to the line: he backs up and lets it come down | Hop rings, the ball's path, glove markers; "High hop: back up a step, let it come down" |
| 17.8–24.4 s | "Either way, don't stop your feet…" | Real time in front of him, then a ½-speed replay from behind and above: an angled approach, the glove out front, momentum carrying toward first | A movement arrow on the dirt; "Eyes on the ball, angled approach" → "Glove out front" → "Momentum carries toward first" |
| 24.4–32.3 s | "Now you're moving toward first…" | Split on the same ball: waits on it (gather, reset) vs. works through it (field, throw), real time, then a ½-speed replay | Footprints after the field, a RELEASE tag at each side's release |
| 32.3–34.3 s | (end screen) | Wide: the throw to first | **READ THE HOP. WORK THROUGH IT.** |
