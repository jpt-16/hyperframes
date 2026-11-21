# "Why some hitters generate more power"

A 53.1 s vertical (1080×1920, 30 fps) 3D breakdown for Baseball Decoded. A bigger hitter and a smaller one meet the same pitch, and the difference between them is how well the swing is sequenced.

## The two hitters

Both are right-handed and meet the same 92 mph fastball at the same spot. They share one rig and are told apart by build and kit.

- **The bigger hitter:**
  - 1.07× the height, with limbs and torso 1.32× as thick;
  - charcoal kit, red helmet, orange graphics;
  - his shoulders turn almost with his hips, so there's little separation between them.
- **The smaller hitter:**
  - 0.93× the height, with limbs and torso 0.84× as thick;
  - white kit, navy helmet, cyan graphics;
  - his hips open first and his torso follows.
- **The exit speeds** in `tools/physics.py` are illustrative values chosen to make the point. They are never shown on screen. The smaller hitter's ball carries 378 ft to the wall; the bigger hitter's lands 319 ft out.

## What's new in `assets/field.js`

- **Builds:** `BUILD`, `applyBuild`, and the "power" section. The IK works in the rig's own units, so a scaled hitter still plants his feet and keeps both hands on the bat.
- **The gym:** a rubber floor, a rack, a dumbbell shelf, a mirror, and a barbell with plates (`GYM`, `BARBELL`). Both hitters do a back squat (`poseSquat`); the bigger one has three plates a side, the smaller one two.
- **The ball squashes against the bat** for a few thousandths of a second (about 1.6 ms either side of contact). That's the close-up in scene 4.
- **Cameras:** `bchase` trails the batted ball.
- **The pitcher** is the delivery rig from the 100 mph episode.

## On screen

- **Titles:** BIGGER ≠ MORE POWER (from the first frame), STRENGTH IS ONLY ONE PIECE, GROUND → LEGS → HIPS → TORSO → BAT (each word lights as that segment moves), TIMING + SEQUENCING = POWER, POWER IS MORE THAN MUSCLE., and STRENGTH OR MECHANICS?
- **The sequence note:** "Illustration of a typical sequence. Timing varies from hitter to hitter."
- **Captions:** a few words at a time at the top.

## Voiceover and sound

- **Voiceover:** your script, word for word, voiced with Kokoro TTS (voice `am_michael`, 1.2×).
- **Scene starts:** 0, 5.0, 13.0, 23.0, 35.0 and 49.0 s, which are your marks. The voice leaves silent stretches (about 3.6 s before the reveal and 5.7 s before the question) for the full-speed swing, the ball against the bat, and the flight to the wall.
- **Sound:** bat cracks at contact, swing whooshes, thuds at the bottom of each squat, ticks as each segment lights, impacts on titles, stadium ambience, and a music bed ducked under the voice, mastered to about −14 LUFS.
- **Your own read:** `CUES.md` lists when each line starts, so you can record over `assets/mix-novo.wav`.

## Build

```bash
python3 tools/physics.py                                       # the pitch and the two batted balls -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 53.11 90 <port>   # resumable render; mux with assets/mix.wav
```
