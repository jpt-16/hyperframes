# "Why copying an MLB swing can hurt your hitting"

A 50.8 s vertical (1080×1920, 30 fps) 3D breakdown for Baseball Decoded. A young hitter copies a pro's big leg kick and struggles; three pros hit with three different movements; the point is to learn why a swing works and build one that fits you.

## The hitters

All five are right-handed, on one rig, and meet the same 92 mph fastball. The swing styles are in the "copying a swing" section of `assets/field.js`.

| Hitter | Look | What he does differently |
|---|---|---|
| **Big leg kick** (pro) | charcoal, red helmet, orange graphics | the front foot lifts high early, then a long stride |
| **Short stride** (pro) | white, navy helmet, cyan graphics | barely lifts the front foot, a short stride, a still setup and bat |
| **Active hands** (pro) | green, gold helmet, green graphics | hands set high and busy before the swing starts |
| **Young hitter, copying** | bright blue, white helmet, yellow graphics | the same big kick, overdone: a longer stride, a lunge, off balance, on the end of the bat, a stumbling step through |
| **Young hitter, his own swing** | the same hitter | a modest lift, balanced, meets the sweet spot |

The swing styles differ in actual movement, not just stance: the foot's lift and timing, the stride, the body's weight shift, and the hands' and bat's path (`STY`, `BODY`, `HANDS_K`, `BAT_K`). The exit speeds are illustrative and never shown.

## What's new

- **Balance marker:** a shaded patch on the ground shows his base of support (the planted feet), with a dot and a line for where his weight is. It's green when his weight is over his base, amber near the edge, and red outside. It's labelled "an illustration" on screen.
- **The film room:** three screens in a column play three pro swings on a loop (render targets), with the young hitter's back in front of them. His head turns from screen to screen.
- **The ball squashes against the bat** at contact, as in the last episode.

## On screen

- **Titles:** STOP COPYING MLB SWINGS? (from the first frame), 3 HITTERS. 3 DIFFERENT SWINGS., IMITATION ≠ IMPROVEMENT, DIFFERENT MOVEMENTS. SAME GOAL., LEARN THE WHY. BUILD YOUR SWING., and WHO HAS THE BEST SWING?
- **Labels:** kept to a few short ones (YOUNG HITTER / THE PRO, OFF BALANCE, BIG LEG KICK, SHORT STRIDE, ACTIVE HANDS).
- **Captions:** a few words at a time at the top; none on the last line, where the title carries it.

## Voiceover and sound

- **Voiceover:** your script, word for word, voiced with Kokoro TTS (voice `am_michael`, 1.2×). It is continuous: no scene anchors and no empty gaps between lines.
- **Scene starts:** 0, 5.8, 12.2, 19.0, 31.8 and 47.4 s, against your 0, 5, 14, 24, 37 and 49. The read is continuous, so the scenes shift with it.
- **Sound:** a whoosh on each swing and cut, a crack on solid contact, a dull thud on the young hitter's mis-hit, ticks and impacts on the titles, stadium ambience, and a music bed that builds at the start and ducks under the voice, mastered to about −14 LUFS.
- **Your own read:** `CUES.md` lists when each line starts, so you can record over `assets/mix-novo.wav`.

## Build

```bash
python3 tools/physics.py                                       # the pitch and the five batted balls -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 50.82 90 <port>   # resumable render; mux with assets/mix.wav
```
