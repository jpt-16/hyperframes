# "Look at the clock": a stolen base is a race

A 71.4 s vertical (1080×1920) explainer built from the script. It has a 3D field, timers, word-timed captions, a voiceover (HyperFrames' built-in Kokoro TTS) and sound effects.

```bash
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover (hyperframes tts) + word timing, see below
python3 tools/sfx.py                                 # crowd bed, glove pop, stopwatch tick
python3 build.py                                     # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/look-at-the-clock.mp4 --video-bitrate 16M
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

These runner numbers are a model, not measured data. They match the script's "roughly 3.2 seconds" over 78–80 ft.

## Shots (timed to the voiceover)

| Time | Shot | On screen |
|---|---|---|
| 0–3.0 s | Behind the runner leading off first | – |
| 3.0–6.4 s | Behind the catcher | – |
| 6.4–11.9 s | Center-field camera: the delivery, at half speed | TIME TO PLATE counts to 1.40 |
| 11.9–19.4 s | Split screen: delivery (top) and the catcher's pop (bottom) | 1.40 and POP TIME 1.90 |
| 19.4–24.6 s | High wide view with the ball's path drawn | 1.40 + 1.90 = 3.30 s, + the runner's jump + the tag |
| 24.6–45.8 s | Down the basepath from behind first: the lead (blue), the distance to go (yellow), then the sprint | 90 FT − 10–12 FT = 78–80 FT; RUNNER TO SECOND counts to 3.27; SAFE (ball at 3.30) / OUT (ball at 3.10) |
| 45.8–54.9 s | The 1.2 s pitcher: the runner breaks, the throw travels | 1.20, the 3.30 vs 3.10 bars, −0.20 s |
| 54.9–64.3 s | Freeze as the shortstop receives the throw, with an orbit around second | ≈ 5 FT; the race: 1.20 / 1.90 / runner 3.27 |
| 64.3–71.4 s | Overhead at second base, the tag | STOLEN BASE 3.10 s, "Look at the clock." |

Captions are the script, word for word.

## Voiceover and captions

**The voice.** Every line is spoken by HyperFrames' built-in TTS (`hyperframes tts`), using the local Kokoro model. No external voice service is used.

- **Voice and speed:** `am_michael` at 1.05× speed, for a clear, confident tutorial read.
- **Setup:** `HYPERFRAMES_PYTHON` must point at a Python that has `kokoro-onnx`, `soundfile` and `onnx`.
- **Numbers:** the spoken text spells them out ("one point nine second pop time", "ten to twelve foot", "seventy-eight to eighty"), because Kokoro otherwise reads "1.9-second" as "one. nine second" and drops the "to" in ranges. "baserunner" is spoken as "base runner". The captions keep the script's wording.

**Word timing.** `tools/vo.py` works out when each word is spoken:

1. It makes a copy of HyperFrames' `kokoro-v1.0.onnx` with the model's own per-phoneme duration tensor exposed as an output. The weights are untouched, and the copy is cached in `.cache/`.
2. kokoro-onnx's `create_timed()` runs that copy without inserting pauses. Each line is checked to match the `hyperframes tts` audio sample for sample, so the timings are the times in the file.
3. Phonemes are aligned to words. This handles espeak merging short words such as "for the".

**What the timings drive:**

- **Captions:** the script word for word, in short phrases. The word being spoken turns yellow.
- **Animations:**
  - TIME TO PLATE reaches 1.40 as "seconds" ends.
  - POP TIME reaches 1.90 on "pop time".
  - The 1.2 s delivery reaches 1.20 on "seconds".
  - "3.30" lands on "three point three".
  - The basepath card builds on "ninety-foot", "ten" and "seventy-eight".
  - RUNNER TO SECOND reaches 3.27 as "3.2 seconds" ends; SAFE and OUT pop on those words.
  - "−0.20 s" lands on "two-tenths".
  - The race lanes fill on "delivery", "throw" and "jump".
  - "Look at the clock." appears word by word.
- **Line timing:** the pauses between lines are set in `tools/assemble.py`, and every shot moves with them.

## Sound

- A low ballpark crowd bed under everything.
- A whoosh on each cut.
- Stopwatch ticks while the timers run.
- A glove pop on every catch.
- An impact and riser on the freeze.
- Hits on the equation.
- Ticks into the final "Look at the clock."

All of it is synthesised or taken from the shared JT kit. No music. The effects sit 6 dB under the voice, and the mix is mastered to about −14 LUFS.
