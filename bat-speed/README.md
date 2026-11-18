# "What actually creates bat speed?"

A 42.5 s vertical (1080×1920, 30 fps) 3D biomechanics breakdown for Baseball Decoded. It shows where bat speed comes from: the hitter's interaction with the ground, the pelvis and torso turning in sequence, and the arms and hands delivering the barrel, all working together.

## The hitter and the swing

- **One hitter throughout:** white uniform, navy helmet, the series' geometric figure. He uses one swing in every shot. Legs and arms are solved with two-bone IK, so his feet stay planted and both hands stay on the bat.
- **The swing:**
  - he loads into the rear leg;
  - he strides (the lead foot lands 0.22 s before contact);
  - his weight moves onto the lead leg;
  - the pelvis turns, then the torso;
  - the arms and hands deliver the barrel into a 95 mph fastball, driven to left-center for a home run (107 mph, 27°, by `tools/physics.py`).
- **Smoother rotation:** from the end of the load on, his body moves on a smooth curve through its keyframes. It no longer eases to a stop at each one. The pelvis reaches its fastest turn just before the torso does, which is the typical proximal-to-distal sequence.

## Where it happens

- **The ballpark** (the series' night game): the hook, the full-speed swing, the contact and the home run, and the finish.
- **A biomechanics lab** for the teaching shots:
  - a dark capture stage with a grid floor;
  - a ring of motion-capture cameras;
  - a force plate under each foot.

## Overlays

- **X-ray:** the uniform turns translucent and the segments glow. Legs and ground are amber, the pelvis orange, the torso cyan, the arms and hands green, and the bat gold.
- **Ground reaction forces:**
  - an arrow rises from the ground under each foot. Its size shows relative support; its lean shows the rear leg pushing toward the pitcher and the lead leg bracing;
  - the plates glow with the load;
  - a support bar moves from the rear leg to the lead leg.
  - The arrows stay at the feet. Nothing shows force "travelling" into the bat.
- **Pelvis → torso:**
  - a side view over an overhead view;
  - the hip and shoulder lines, and the wedge between them;
  - a freeze with the pelvis open and the torso still closed;
  - two turning-speed traces drawn from the same swing.
- **Barrel acceleration:**
  - translucent bat positions at equal time steps (the wider the gap, the faster the barrel);
  - a trail on the end of the bat;
  - a close-up on the hands and wrists.
- **All together:** an x-ray replay that lights legs → pelvis → torso → arms → bat as each one moves.

## Accuracy

These follow the brief's guardrails:

- No measured numbers appear on screen: no mph, percentages or force values. The arrows and the traces are labelled as an illustration.
- Ground reaction forces "help support and generate" movement. They are never shown flowing up the body into the bat.
- The hips are never credited alone. The arms and hands get their own scene.
- On-screen note: "Sequence and timing vary from hitter to hitter."
- The script matches the hitting biomechanics literature: Welch et al. (1995) on the kinematic sequence and ground reaction forces in hitting, and later joint-torque studies of how much the trunk and the arms contribute to bat-head speed.

## Voiceover and text

- **Voiceover:** your script, word for word, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.38×). The text is in `transcript.txt`.
- **Scene starts follow the read:** 4.8 s, 12.1 s, 21.3 s, 28.9 s and 37.5 s, against the brief's 5/13/22/33/42. The home run carries in silence before the outro.
- **Captions:** a few words at a time at the top, with key words in yellow.
- **On-screen titles:**
  - WHAT ACTUALLY CREATES BAT SPEED?
  - GROUND REACTION FORCES
  - PELVIS → TORSO
  - BARREL ACCELERATION
  - THE ENTIRE BODY WORKS TOGETHER.
  - FOLLOW ALONG FOR OUR BIOMECHANICS SERIES, with the Baseball Decoded mark.
- **Your own read:** `CUES.md` lists when each line starts, so you can record over `assets/mix-novo.wav`.

## Build

```bash
python3 tools/physics.py                                       # the fastball and the home run -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 42.51 90 <port>   # resumable render; mux with assets/mix.wav
```

The new code is the "bat speed" section of `assets/field.js`:

- the lab and its force plates (`setLab`, `PLATES`);
- the ground-force model (`grfAt`, `setGRF`);
- the x-ray skeleton and the hip-shoulder wedge (`setXray`);
- the turning-speed traces (`TRACE`, `drawTrace`).
