# "Look at the clock": a stolen base is a race

A 51.7 s vertical (1080×1920) explainer built from the script. It has a 3D field, timers, captions, a scratch voiceover and sound effects.

```bash
python3 tools/vo.py && python3 tools/assemble.py     # scratch voiceover + line timing (needs kokoro-onnx, see below)
python3 tools/sfx.py                                 # crowd bed, glove pop, stopwatch tick
python3 build.py                                     # index.html + assets/mix.wav + assets/mix-novo.wav
npx --yes hyperframes@0.8.154 render . -o renders/look-at-the-clock.mp4 --video-bitrate 16M
ffmpeg -i renders/look-at-the-clock.mp4 -i assets/mix-novo.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/look-at-the-clock-novo.mp4
```

## The 3D

`assets/field.js` (three.js) builds a regulation field to scale:

- 90 ft bases
- the rubber 60.5 ft from home
- the infield skin 95 ft from the rubber
- chalk lines, batter's boxes and bases
- a night-game stadium, lit by banks of lights

The players are articulated figures, posed and animated in code: the pitcher, catcher, runner, shortstop, first and second basemen, and the batter. It's a broadcast-analysis look, not photoreal footage.

### The play, computed from the script's numbers

**The ball**

| Delivery | Pitch release | In the catcher's glove | Catcher's release | At second (pop time 1.9 s) |
|---|---|---|---|---|
| 1.4 s | 0.98 s | 1.40 s | 2.12 s | 3.30 s |
| 1.2 s | 0.78 s | 1.20 s | 1.92 s | 3.10 s |

The pitch takes about 0.42 s to reach the plate (about 90 mph).

**The runner**

- **Model:** a 12 ft lead, 0.05 s reaction, accelerating toward 30 ft/s, and a slide for the last 9 ft.
- **Result:** he reaches the bag at 3.27 s.
  - With the 1.4 s pitcher he's in just ahead of the ball.
  - With the 1.2 s pitcher he's 4.96 ft short when the ball arrives, which is the "≈ 5 FT" in the freeze frame.

These runner numbers are an illustrative model, not measured data. The video says "Illustrative timings" on screen.

## Shots (timed to the voiceover)

| Time | Shot | On screen |
|---|---|---|
| 0–3.0 s | Behind the runner leading off first | – |
| 3.0–6.6 s | Behind the catcher | – |
| 6.6–12.2 s | Center-field camera: the delivery, at half speed | TIME TO PLATE counts to 1.40 |
| 12.2–20.0 s | Split screen: delivery (top) and the catcher's pop (bottom) | 1.40 and POP TIME 1.90 |
| 20.0–25.4 s | High wide view with the ball's path drawn | 1.40 + 1.90 = 3.30 s, + the runner's jump + the tag |
| 25.4–33.5 s | The 1.2 s pitcher: the runner breaks, the throw travels | 1.20, the 3.30 vs 3.10 bars, −0.20 s |
| 33.5–44.4 s | Freeze as the shortstop receives the throw, with an orbit around second | ≈ 5 FT; the race: 1.20 / 1.90 / runner 3.27 |
| 44.4–51.7 s | Overhead at second base, the tag | STOLEN BASE 3.10 s, "Look at the clock." |

Captions are the script, word for word.

## Voiceover

`assets/vo/` holds a scratch voiceover from a local text-to-speech model (Kokoro, voice `am_michael`). It needs the `kokoro-onnx` and `soundfile` Python packages, pointed to with `HYPERFRAMES_PYTHON`.

- **Spoken text:** the numbers are spelled out ("one point nine second pop time"), because the model otherwise misreads "1.9-second".
- **Captions:** they keep the script's numerals.

**To use your own voice:**

- **Easiest:** record over `renders/look-at-the-clock-novo.mp4`, which has the same picture with sound effects only. The line start times are listed in `assets/vo/timing.json`.
- **Or:** replace `assets/vo/vo.wav` with your recording, edit the start times in `tools/assemble.py`, and rebuild. The shots move with the lines.

## Sound

- A low ballpark crowd bed under everything.
- A whoosh on each cut.
- Stopwatch ticks while the timers run.
- A glove pop on every catch.
- An impact and riser on the freeze.
- Hits on the equation.
- Ticks into the final "Look at the clock."

All of it is synthesised or taken from the shared JT kit. No music. The voice version is mastered to about −14 LUFS.
