# "Why catcher might be the hardest position in baseball"

A 52.7 s vertical (1080×1920, 30 fps) 3D breakdown for Baseball Decoded. It covers what a catcher has to do: receive pitches, block balls in the dirt, throw out a runner, and run the game.

## The plays

There's one catcher (home whites, mask and pads) in every shot. The plays are in the "catcher" section of `assets/field.js`, and the pose tables come from the earlier `catcher` episode.

- **The pitches** come from `tools/physics.py`. Each is released from the pitcher rig's hand and flown with gravity, drag and spin lift:
  - **Fastball:** 95 mph, ending up in the zone.
  - **Breaking ball:** 84 mph, with a glove-side break. It starts near the middle and ends low and away from the right-handed hitter.
  - **Dirt ball:** a 79 mph curveball that bounces 4.6 ft in front of the plate.
  - **Steal pitch:** a 93 mph fastball, up in the zone.
- **Receiving:** the mitt is solved onto the ball with two-bone IK. It goes to where the ball will be, a hair early, and gives a little on the catch.
- **Blocking:**
  - he drops onto his knees with his chest over the ball;
  - the rebound is simulated off his body: mostly dead, a bit back toward the pitcher, then a bounce and a roll;
  - the ball stays in front of him.
- **The steal:**
  - the runner takes off from first;
  - the catcher catches, comes up, steps and throws to second;
  - the throw flies from his hand at release to the second baseman's glove under gravity;
  - the second baseman covers and puts the tag down;
  - the runner's go time is computed so his foot reaches the bag a hair after the tag is down.
- **The sign:** the jointed hand between his thighs shows the fingers, and the pitcher nods.
- **The talk:**
  - he stands and points, then sweeps his arm across;
  - the shortstop, second baseman and third baseman shift in response;
  - he looks at the runner on first.
- **The hook** opens on the shortstop's diving play from the last episode.

`tools/plan.json` holds the steal's and the block's timings, read back from the rig (`stealPlan()` and `blockPlan()` in `field.js`).

## On screen

On-screen text is kept minimal:

- **Titles:** **THE HARDEST POSITION?** in the hook, and **HARDEST POSITION IN BASEBALL?** at the end with the Baseball Decoded mark.
- **Captions:** a few words at a time at the top.

## Voiceover and sound

- **Voiceover:** your script, word for word, voiced with Kokoro TTS (voice `am_michael`, 1.28×) with pauses between lines.
- **Scene timing:** the scenes start at 0, 8.3, 16.9, 21.8, 29.1 and 46.2 s. The brief's blocks were 0, 5, 14, 23, 32 and 43 s. The hook runs about 3 s long because its three lines take 8 s to say. The throwing scene starts a second earlier than the brief and the mental-side scene about 3 s earlier.
- **Sound:**
  - the bat crack on the hook's shortstop play;
  - a tap for each bounce;
  - glove pops on each catch;
  - whooshes on each release and throw;
  - a thud off his chest on the block;
  - stadium ambience;
  - a music bed ducked under the voice;
  - mastered to about −14 LUFS.
- **Your own read:** `CUES.md` lists when each line starts, so you can record over `assets/mix-novo.wav`.

## Build

```bash
python3 tools/physics.py                                       # the pitches, the dirt ball and the grounders -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 52.68 90 <port>   # resumable render; mux with assets/mix.wav
```
