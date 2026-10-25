# "Dive or sprint through?"

A 33.9 s vertical (1080×1920, 30 fps) 3D baseball explainer comparing a head-first dive into first base with running through the bag.

- **Framework:** the same three.js field, players and render workflow as `sequencing`, `fastball`, `tag-up` and `catcher-clock`.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.35×. The script is in `transcript.txt`.
- **Sync:** word-timed captions, and the hook builds word by word on top of a frame-one statement.
- **Sound:** mastered to about −14 LUFS. Effects include footsteps on the runner's modeled foot strikes, the shortstop's glove, the throw, the first baseman's glove, the foot on the bag, and a dirt slide when the diver lands.

```bash
python3 tools/physics.py                                       # the model -> assets/play.json (+ a sensitivity printout)
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/dive-or-run.mp4 --video-bitrate 16M
```

## Measured vs. modeled

**Measured (quoted in the video):**
- *Source:* Ficklin, Dapena & Brunfeldt, "A comparison of base running and sliding techniques in collegiate baseball with implications for sliding into first base", *Journal of Sport and Health Science* 5(3), 2016 (9 college players).
- *Result:* running through the base was fastest overall, then head-first, feet-first and running to a stop.
- *The dive:* only a non-significant trend toward an advantage, which the video calls "not proven". The authors judged that the risks likely outweigh any small gain.
- *Same conclusion elsewhere:* a 2020 study of college baseball and softball players also found running through significantly faster than sliding.

**Modeled (`tools/physics.py`, labeled "3D model" on screen):** a transparent physics model that shows the trade-off. It isn't data.

| | Both runners (identical) |
|---|---|
| Start | first step out of the right-handed box, 90.6 ft from the near edge of the bag |
| Sprint | v(t) = 27 ft/s · (1 − e^(−t/0.8 s)); 27 ft/s is the MLB average Statcast sprint speed |
| Fielding play | the same ground ball in the hole, the same 84 mph throw |

| Running through | Head-first dive |
|---|---|
| Touches when the foot lands on the bag, 1.38 ft ahead of his hips | One setup stride lowers him and costs speed: **85% kept, an assumption**. Then he's in the air (gravity only) until his chest lands, then slides on the dirt (μ = 0.5) |
| Keeps 26.8 ft/s through the bag, then eases up in foul ground | "Well timed": his hand reaches the bag exactly as his chest lands, 3.51 ft ahead of his hips. That's **2.1 ft more reach** than a foot on the bag |

The foot and hand distances are measured on the 3D figure (`window.__measure()`), so the animation and the model touch the bag at the same moment.

**Result in the model:** both touch at ≈ 4.1 s, within a few thousandths of a second of each other. The outcome depends entirely on how much speed the setup stride really costs, which the model can't know:

| Speed kept after the setup stride | Dive minus run-through |
|---|---|
| 100% | −0.076 s (dive ahead) |
| 90% | −0.023 s |
| 85% (used) | +0.003 s |
| 80% | +0.031 s (run-through ahead) |

So the video shows times only to the tenth (4.1 s for both) and says "Too close to call · 3D model · not measured". Which method is faster in practice comes only from the measured study.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.3 s | "In a bang-bang play at first, is diving actually faster?" | Behind the shortstop: backhand in the hole and the throw. Then beyond first base: runner and ball arriving together, ½ speed, then a freeze just before the bag | **DIVE OR SPRINT THROUGH?** on frame one, the question word by word, and the title again on the freeze |
| 3.3–10.3 s | "Diving lets you reach farther…" | Split screen with the same camera, start, sprint and throw: dive on the left, run through on the right. Real time, then ½ speed; each side freezes on its own touch, then both carry on | Synchronized timers (to 0.1 s), HAND ON THE BAG / FOOT ON THE BAG, TOO CLOSE TO CALL |
| 10.3–20.6 s | "In a biomechanics study…" | From the side at ¼ speed, tracking: the diver solid and the run-through as a ghost on the same clock. Then wide at ½ speed | Model speed meters; "Extra step to get down: speed drops"; "Reach: hand ≈ 3.5 ft ahead of his hips"; "Full speed through the bag". Study card: **RUNNING THROUGH: FASTEST OVERALL IN THE STUDY**, **DIVE ADVANTAGE: NOT PROVEN** |
| 20.6–25.6 s | "A dive also adds injury risk…" | Low at the bag, ⅙ speed: hands and head go in first (non-graphic). Then wide, real time: the throw gets away while he is still on the ground | Two short tags |
| 25.6–33.9 s | "So if you're beating a throw to first…" | A bang-bang run-through from the side (safe), then he eases up in foul ground past the bag | **AT FIRST: SPRINT THROUGH WHEN YOU CAN.**, then **WOULD YOU DIVE OR RUN THROUGH?** |

A label in the top-left corner always shows the playback speed.
