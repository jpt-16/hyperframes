# "Why catchers struggle with pop-ups"

A 40.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It covers why a pop-up behind the plate is hard for a catcher:

- finding the ball;
- its drift;
- his gear and the obstacles around the plate;
- why the play is so hard to practice.

## The catcher and the play

- **One catcher model throughout:** cream jersey with green gear. The gear is built piece by piece:
  - a skull cap worn backward;
  - a removable mask (a steel cage of frame and bars over leather pads, with a throat guard and harness);
  - a chest protector with raised ribs, shoulder caps and a collar;
  - shin guards with knee cups, foot plates and knee savers;
  - a round, deep-pocketed catcher's mitt.
- **Every pop-up uses the same technique:**
  1. He comes up out of the crouch with his eyes on the ball.
  2. He pulls the mask off with his throwing hand and turns.
  3. Once he has the ball, he tosses the mask away from his path.
  4. He gets under the ball and catches it with the mitt up in front of his face.
- **Movement:** legs and arms are solved with IK, so his feet step and plant as he runs and both hands reach where they should. The tossed mask flies, bounces and lies on the grass.
- **Around him:**
  - the umpire stands and gets out of the way;
  - the batter drops his bat by the plate and runs;
  - the stadium has a padded backstop with netting, seats behind the plate and light towers.

## The physics

`tools/physics.py` uses gravity, drag and a true Magnus force from a fixed spin axis.

- **Game pop-ups** come off a 95 mph fastball with heavy backspin (3,600–4,200 rpm here). Their paths bend as they rise and fall. Hang times are about 6 s, with apexes of 147–171 ft. Each launch is solved so the ball comes down at a chosen spot:
  - toward the third-base dugout;
  - back to the backstop;
  - curling toward the mound;
  - near the wall for the finale.
- **The practice fungoes** are hit off a toss with far less spin (800 rpm here), so their paths are close to plain parabolas.
- **The side-by-side** in the practice scene draws a game pop-up and a fungo to the same spot, so you can see the difference in shape.

## Voiceover and text

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.45×). The text is in `transcript.txt`.
  - Scene starts follow your time blocks: the three directions at 6.2 s, the gear at 14.0 s, practice at 20.5 s and the takeaway at 32.3 s.
- **Captions:** short, word by word at the top.
- **On-screen text:**
  - "Why is this so hard?"
  - "Toward the dugout / backstop / mound"
  - pins for the mask, chest protector, shin guards, umpire, bat and plate
  - "Hard to practice" and "6 pop-ups · 6 different spots"
  - Find it / Get under it / Make the play
  - "It's harder than it looks."
  - a small Baseball Decoded mark
- `CUES.md` lists when each line starts, for recording your own read over `assets/mix-novo.wav`.

## Shot list (times in `CUES.md`)

1. **Hook:**
   - From behind the plate: the ball goes straight up and his head snaps up, under "Why is this so hard?".
   - In slow motion, from his side: the mask comes off.
   - Straight up past him at the ball (traced) against the light towers, as he tosses the mask.
   - Tracking him as he settles under it.
2. **Three directions:**
   - The pop-ups drifting toward the dugout, the backstop and the mound.
   - Then from above, the mound pop-up: his first read is back, the ball comes down in front, and his path shows the turn.
3. **Gear and obstacles:**
   - The mask coming off, with the gear named.
   - From above the plate: the umpire, the bat and the plate.
   - Low behind him as he gets under the ball (into the lights) and catches it.
4. **Practice (day, empty stadium):**
   - A coach hits fungoes, with quick cuts of the catcher chasing them in different directions.
   - Six fungoes from above, each landing somewhere new.
   - A game pop-up against a fungo, side by side.
5. **Payoff:**
   - Through the backstop net, as he comes back to the wall.
   - The ball going into the mitt in slow motion, with Find it / Get under it / Make the play.
   - "It's harder than it looks." and the Baseball Decoded mark.

## Accuracy notes

- The spin rates are illustrative values in a realistic range. Pop-ups off a pitched ball carry much more backspin than a fungo, which is why practice fungoes don't fly like game pop-ups. The exact numbers vary from play to play.
- The catcher's technique (mask off with the throwing hand, toss it away from the ball, back to the infield on balls behind the plate, mitt up with fingers up) is standard instruction. The timings are this animation's own.
- The players are stylized figures, not real people, in generic uniforms.

## Build

```bash
python3 tools/physics.py                                       # the pitch, the pop-ups and the fungoes -> assets/play.json (about 40 s)
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 40.47 90 <port>   # resumable render; mux with assets/mix.wav
```

The new code is the "pop-ups" section of `assets/field.js`:

- the backstop, light towers and day lighting;
- the catcher's gear, mask and mitt;
- `gaitFeet` (running steps);
- `poseCatcher` (the routine);
- the umpire and batter;
- the practice coach;
- the ground tracks and trails.
