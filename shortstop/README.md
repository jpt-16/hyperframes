# "Why shortstop is one of the hardest positions in baseball"

A 49.9 s vertical (1080×1920, 30 fps) 3D breakdown for Baseball Decoded. It covers the shortstop's range, the hops, the throws, and the thinking.

## The plays

There's one shortstop (home whites, the defense) in every play. The plays are driven by the new fielder rig in the "shortstop" section of `assets/field.js`.

- **Ground balls** come from `tools/physics.py`:
  - each ball is hit off the same contact point;
  - gravity and drag act in the air;
  - each bounce off a firm infield keeps 52% of the vertical speed and 88% along the ground;
  - low skips turn into a roll;
  - one ball takes a bad hop off the lip: it kicks up and 9° to the side just before he fields it.
- **The fielder**, for each play (`PLAYS`):
  - **First step:** about 0.14 s after contact, then a run cycle along his route.
  - **Fielding:** he takes the ball forehand, backhand, diving or charging.
  - **The glove** is solved onto the ball with two-bone IK, so glove and ball meet exactly, including when the bad hop changes direction.
  - **Throws:** a plant and throw, from his knees after the dive, a jump throw, or a sidearm feed to second. The throwing arm is keyed as the direction of the upper arm and the forearm (the same method as `velo`).
- **Throws** fly from his hand at release to the receiver's glove under gravity, at 42–86 mph depending on the throw. The first baseman stretches off the bag; at second, the coverer runs in and takes it on the bag.
- **The rest of the play:**
  - the batter swings for every ball;
  - the pitcher delivers;
  - on the force plays, a runner breaks from first.

| Play | Ball | How he plays it |
|---|---|---|
| Hook, payoff | 98 mph up the middle | Dives to his glove side, up to his knees, up, throws |
| Range | up the middle / deep in the hole / slow chopper | Routes drawn on the dirt over his range |
| Hops | 90 mph with a bad hop | Glove follows the kick |
| Hops, throw | 92 mph deep in the hole | Backhand, plant, throw across the diamond |
| Throw, payoff | 90 mph deeper in the hole | Backhand, jump throw |
| Mental side | toward the bag / to the second baseman | Second baseman covers, then the shortstop covers |
| Payoff | routine, right at him | Forehand, plant, throw |

## On screen

On-screen text is kept minimal:

- **Titles:** **THE HARDEST POSITION?** on the hook freeze, and **MORE THAN JUST GOOD HANDS** at the end with the Baseball Decoded mark.
- **Labels:**
  - his range on the dirt;
  - "Up the middle", "Deep in the hole" and "In between";
  - "Bad hop", "Backhand" and "Off balance";
  - "Who covers second?", with a ring on the bag and "Second baseman covers" / "Shortstop covers".

## Voiceover and sound

- **Voiceover:** your script, word for word, voiced with Kokoro TTS (voice `am_michael`, 1.28×) with pauses between lines.
- **Scene timing:** the scenes start at 0, 6.9, 15.2, 23.4, 33.5 and 41.6 s, close to your 0/4/12/20/29/39 blocks. The hook runs longer because its two lines take 6.5 s to say.
- **Captions:** a few words at a time at the top.
- **Sound:**
  - the bat crack;
  - a tap for each bounce;
  - glove pops on the field and the catch;
  - throw whooshes;
  - stadium ambience;
  - a music bed ducked under the voice;
  - mastered to about −14 LUFS.

## Build

```bash
python3 tools/physics.py                                       # the pitch and eight ground balls -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 49.93 90 <port>   # resumable render; mux with assets/mix.wav
```
