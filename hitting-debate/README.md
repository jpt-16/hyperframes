# "A-Rod vs. Teacherman": two different hitting philosophies

A 42.7 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It compares two ways of teaching the swing: A-Rod's cue (the knob and hands toward the ball) and Teacherman's view (a rear-hip load and a quick barrel into a rearward arc). It doesn't pick a winner: it ends on the debate.

## The two hitters

Both are right-handed. You can tell them apart by their kit and by their colour on screen.

- **Hitter A, the knob cue** (white jersey, navy helmet, cyan graphics):
  - His hands and knob work down toward the ball, then the barrel releases late and meets it.
  - He never pushes the knob into the ball: the barrel makes the contact.
- **Hitter B, the rear-hip load** (charcoal jersey, red helmet, black sleeves, orange graphics):
  - He sinks and coils into his rear hip, and his stride lands while the hips stay closed (stretch against the rear leg).
  - Then the barrel turns back into the plane early, a rearward arc, and he rotates through.
  - He does not spin on a stationary back foot: he strides, his weight moves onto the front side, and his rear heel comes up and pivots.

Both swings go from stance to load, stride, launch, contact and finish, and both hit the same 95 mph fastball. The legs and arms are solved with two-bone IK, so the feet stay planted and both hands stay on the bat through the whole swing.

## Voiceover and text

- **Voiceover:**
  - Your revised script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.6×). The text is in `transcript.txt`.
  - The video is 42.7 s, against the brief's ~40 s. The speech alone runs 37.8 s, and the end card adds about 2.7 s.
  - Scene starts follow the script's time blocks: Teacherman's section starts at 12.0 s and "here's where it gets interesting" at 22.0 s.
- **Captions:** word by word at the top.
- **On-screen text** (from the brief):
  - "Two hitting philosophies." / "Which one is right?"
  - "A-Rod: knob toward the ball"
  - "Teacherman: rear-hip load + quick barrel" / "Launch quickness"
  - "Different cues. Different emphasis."
  - "The goal: barrel control, power & timing." / "Which philosophy do you prefer?"
  - The Baseball Decoded mark.
- `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.

## Shot list (times in `CUES.md`)

1. **Hook:** split screen, A on top and B below.
   - Both swings start in slow motion and freeze as the movement begins.
   - A's knob-to-ball line draws, and B's rear hip and the arc his barrel will take light up.
   - On "his actual swing", both swings finish into line drives.
2. **A-Rod's cue:**
   - Over hitter A's shoulder as the pitch comes in: the cue line and his knob path ("downward, punching-like cue").
   - Then square to him in slow motion, keyed to the voiceover:
     - the knob, on "knob";
     - the hands, on "hands";
     - the hips turning;
     - the barrel through the ball, on "baseball".
3. **Teacherman's view:**
   - Hitter B with a straight knob-to-ball line against his knob's actual path ("literally move the knob straight").
   - His rear hip loading, from behind ("rear hip").
   - Stretch against the rear leg ("rear leg").
   - The barrel's rearward arc into the zone ("quickly launching... rearward arc"), with "Launch quickness".
4. **Different emphasis:**
   - Both swings from the same camera, then from in front of them:
     - A: hands and knob, with the cue line;
     - B: rear hip and barrel path.
   - Then hitter A alone, keyed to the voiceover:
     - the feel (knob to the ball, on "feel like they're driving the knob");
     - the movement as a numbered sequence, each lit on its word: 1 rear leg, 2 hip, 3 hands, 4 barrel.
5. **Takeaway:**
   - Both line drives leave the barrel in slow motion, low in front of the plate.
   - The split merges into one frame behind hitter A as his line drive carries to the outfield.
   - "Which philosophy do you prefer?", then Baseball Decoded.

## Accuracy notes

- The hitters are generic models in generic kits, not likenesses of Alex Rodriguez or anyone else. The labels name the cue or approach, not the player.
- The quotes and characterisations ("A-Rod has publicly described… a downward, punching-like cue", Teacherman's rear-hip load and rearward-arc argument) are your script's. I haven't checked them against the original interviews or videos.
- The two swings are illustrations of each teaching emphasis, not motion capture of any real swing. Both are kept physically plausible:
  - A's knob never stabs at the ball.
  - B never spins on a planted back foot.
- Neither approach is presented as correct. The closing text asks the viewer.

## Layout

The comparisons use top and bottom halves rather than left and right. Each swing sweeps about 6 ft across the frame, so a 540 px-wide half would shrink each hitter to a few hundred pixels.

## Build

```bash
python3 tools/physics.py                                       # the fastball and both line drives -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 42.72 90 <port>   # resumable render; mux with assets/mix.wav
```

The swing code is the "two hitters, two swings" section of `assets/field.js`:

- `BODY`, `HANDS_K` and `BAT_K` key each swing on time from contact.
- `legIK` and `armIK` keep the feet planted and the hands on the bat.
