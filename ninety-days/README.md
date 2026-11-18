# "What if an MLB hitter stopped swinging for 3 months?"

A 42.8 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It's a hypothetical: one hitter, 90 days without swinging, and what that might do to his timing.

It does not put a number on how much he'd lose. There are no batting averages and no percentages. The visuals show timing (early, on time, late) and a hitter working to get it back.

## The hitter and his swings

- **One hitter throughout:** white uniform, navy helmet and navy batting gloves. He uses the same swing mechanics every time. Legs and arms are solved with IK, so his feet stay planted and both hands stay on the bat.
- **What changes is when the swing meets the ball.** A swing is aimed at a pitch's contact point with a timing offset:
  - **late:** the barrel reaches the hitting zone after the ball (the 98 mph fastball in his first game back, or a batting-practice fastball fouled back into the net);
  - **early / out in front:** a changeup pulled foul;
  - **fooled:** he swings for a fastball and gets a breaking ball. The curve or slider arrives later and lower, and the bat goes over it;
  - **on time:** clean contact.
- **Other movement:**
  - a take (he loads and strides, then holds);
  - dry practice swings;
  - walking with the bat and putting it in the rack.

## Where it happens

- **The ballpark:**
  - a night game with a full crowd;
  - seats and netting behind the plate, plus light towers;
  - a catcher in full gear whose mitt goes to each pitch, and an umpire.
- **A professional indoor batting cage:**
  - turf with a taped plate and batter's box;
  - nets on steel arches, padded ends and LED panels;
  - a bat rack and a cart of balls;
  - a coach throwing batting practice from behind an L-screen;
  - a pitcher throwing live from 60 ft 6 in.

## Pitch physics

`tools/physics.py` uses gravity, drag and spin lift.

- **Game:** 96 and 98 mph fastballs, plus a 94 mph fastball hit 110 mph at 29° for a home run.
- **Live in the cage:** a 93 mph fastball and an 85 mph slider.
- **Batting practice:** a 60 mph fastball, a 50 mph curve and a 52 mph change.

In the cage, balls hit the nets, drop and roll.

## On screen

- **The calendar:** a tear-off day calendar flips 1→90 in the hook, then 0→7, 7→30, 30→60 and 60→90. It's labelled "1 week", "1 month", "60 days" and "90 days", and a small day badge stays in the corner.
- **The timing meter:** on every swing at a ball, a meter (early | on time | late) marks where it met or missed the ball:
  - on time in week one;
  - a little late, fooled and out in front at a month;
  - fooled at 60 days;
  - late at 90;
  - then back to on time.
- **Other text:**
  - "90 days without swinging?"
  - "Timing matters"
  - "85 mph slider" and "98 mph"
  - "Just behind it"
  - "Timing is everything"
  - a small Baseball Decoded mark at the end
- **Captions:** short, word by word at the top.

## Voiceover

- Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.45×). The text is in `transcript.txt`.
- Scene starts follow your time blocks: one week at 4.4 s, a month at 11.2 s, 60 days at 19.2 s, 90 days at 28.2 s and the takeaway at 35.2 s.
- `CUES.md` lists when each line starts, for recording your own read over `assets/mix-novo.wav`.

## Shot list (times in `CUES.md`)

1. **Hook:**
   - Night game: he takes a 96 mph fastball (over his shoulder, then low beside the plate in slow motion).
   - The ballpark from high behind the plate as the calendar flips to 90, under "90 days without swinging?".
2. **One week:**
   - He racks his bat and walks out of the cage. The empty cage as the calendar flips to 7.
   - His hands on the bat, then two clean swings off batting practice into the net (meter: on time).
3. **One month:**
   - The calendar flips to 30.
   - A dry swing ("knowing how to swing").
   - A fastball fouled back ("timing a pitch").
   - A curve he swings over ("recognizing its movement").
   - A change pulled foul ("coordinating your entire body").
   - Another dry swing. "Timing matters" throughout.
4. **Sixty days:**
   - The calendar flips to 60.
   - Live pitching in the cage: a 93 mph fastball he watches; the slider coming in, close; he swings early and over it.
   - He works on it. The calendar flips to 90.
5. **Ninety days:**
   - A full ballpark as he walks up to the plate.
   - 98 mph from over his shoulder, then the late swing in slow motion beside the plate, the ball just behind the bat.
   - In the box, he looks over to the dugout.
6. **Takeaway:**
   - Back in the cage, the timing comes back: a little late, then on time.
   - On time in a game, a home run with a tracking shot of the ball.
   - "Timing is everything" and Baseball Decoded.

## Notes

- It's a hypothetical. The voiceover hedges ("probably", "could", "likely") and so do the visuals: the swing never falls apart, only its timing moves, and the hitter adjusts.
- The players are stylized figures, not real people, in generic uniforms.

## Build

```bash
python3 tools/physics.py
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py
python3 build.py
node tools/render_chunks.js . <chunk dir> 30 42.82 90 <port>   # resumable render; mux with assets/mix.wav
```

The new code is the "90 days" section of `assets/field.js`:

- the batting cage and the game/cage switch;
- `poseSwing` (offsets, takes, dry swings);
- `poseWalker` (walking with the bat, racking it);
- `setSceneND`.

The swing set-ups are now made per target pitch (`SU`).
