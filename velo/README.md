# "Why do some pitchers throw 100 mph?"

A 54.9 s vertical (1080×1920, 30 fps) 3D biomechanics breakdown for Baseball Decoded. It covers what happens in an elite fastball delivery: the ground, pelvis and trunk rotation, and the arm through external rotation, internal rotation and elbow extension to release.

## The pitcher and the delivery

- **One pitcher throughout:** a right-hander in home whites, from the windup, in the series' geometric style.
- **New delivery rig.** The series' old pitcher was five poses that eased to a stop at each key. This one is built in the "100 mph" section of `assets/field.js`:
  - **Body:** pelvis and trunk rotation, drop, forward lean and the tilt toward the glove side run on smooth curves (`PBODY`).
    - The pelvis opens first, around foot contact, then the trunk.
    - At foot contact the pelvis is open and the trunk still closed.
    - The lead knee straightens between foot contact and release, which lifts him.
  - **Legs:** solved with two-bone IK, so the drive foot stays on the rubber and then drags, and the stride foot lands and holds (`PDRIVE`, `PLEAD`).
  - **Arms:** each one is keyed as the direction of the upper arm and of the forearm in the trunk's frame (`ARM_K`). That makes each motion separate and visible:
    - **external rotation:** the forearm is vertical at foot contact, then laid back at maximum external rotation;
    - **internal rotation:** the forearm sweeps forward over the top;
    - **elbow extension:** the forearm lines up with the upper arm at release.
- **The pitch:** the ball leaves the rig's own hand, at the release point in `tools/release.json`. `tools/physics.py` flies it as a 100 mph four-seamer (gravity, drag, backspin lift) into the catcher's mitt.

## Overlays

Kept sparse, per the brief:

- **The hook:** the ball spins toward the lens and stops in midair, the camera pulls back to the pitcher, and a speed gauge sweeps to 100 mph.
- **X-ray:** the uniform turns translucent over coloured segments. Legs are amber, the pelvis orange, the trunk cyan and the arms green.
- **Ground forces:** an arrow at each foot.
  - The drive leg pushes toward home.
  - The stride leg lands and braces, so its arrow points up and back.
  - Labelled "illustration, not measured data".
- **Rotation:** an orbit with the hip and shoulder lines, and a freeze at foot contact labelled "pelvis open · trunk still closed".
- **The arm:**
  - a cyan arc around the upper arm for external rotation, then a green one in the other direction for internal rotation;
  - a glowing elbow for elbow extension;
  - a camera that rides with the ball from the hand;
  - then the arm action in real time.
- **Release:** the fingertips, the ball to the plate, the catch, and the gauge at 100.

## Accuracy

- **No numbers beyond the scenario's 100 mph:** no force values, rotation speeds or percentage contributions.
- **No direct energy transfer:** the narration and the visuals present a coordinated sequence. The lower body doesn't hand its energy straight to the arm.
- **Three arm motions:** external rotation, internal rotation and elbow extension are shown and labelled separately.
- **On-screen caveat:** "A typical sequence. Timing and mechanics vary from pitcher to pitcher."
- **The animation is an illustration of a typical delivery,** not motion capture or a measurement of any real pitcher.
- **Sources:** the sequence follows published pitching biomechanics. Fleisig, Escamilla and colleagues describe foot contact, maximum external rotation, release, and the pelvis-then-trunk timing.
- **Hand speed:** the animated hand speed peaks a little before release rather than exactly at it. That isn't visible at normal speed.

## Voiceover and sound

- **Voiceover:**
  - your script, word for word;
  - voiced with Kokoro TTS (voice `am_michael`, 1.15×), slower than the other episodes so it isn't rushed;
  - with pauses after the key lines.
- **Scene timing:** scene starts follow your blocks (6, 15, 25, 38 and 47 s). The arm scene starts at 26.4 s because the rotation lines run long.
- **Captions:** a few words at a time at the top.
- **Sound:** stadium ambience, release whooshes, the mitt pop, impacts on the titles, and a music bed ducked under the voice, mastered to about −14 LUFS.
- **Your own read:** `CUES.md` lists when each line starts, so you can record over `assets/mix-novo.wav`.

## Build

```bash
python3 tools/physics.py                                       # the 100 mph fastball from tools/release.json -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 54.88 90 <port>   # resumable render; mux with assets/mix.wav
```
