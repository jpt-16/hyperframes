# "Every pitch is designed to mess with your timing"

A 34.7 s vertical (1080×1920, 30 fps) 3D baseball explainer about pitch sequencing: why hitting is a decision made with incomplete information.

- **Framework:** the same three.js field, players and render workflow as `fastball`, `tag-up` and `catcher-clock`.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.3×. The script is in `transcript.txt`.
- **Sync:** word-timed captions and shots keyed to the narration.
- **Sound:** effects under the voice, mastered to about −14 LUFS. Sounds include the release, glove pops, swing swishes and cut whooshes. Nobody makes contact in this video, so there's no bat crack.

```bash
python3 tools/physics.py                                       # three pitches + swing timing -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/pitch-sequencing.mp4 --video-bitrate 16M
```

## The physics (`tools/physics.py`)

Every pitch is right-handed and comes from the same release point: 6.5 ft extension, 6.0 ft high, 1.9 ft to the arm side. Each flight uses gravity, drag (Cd 0.35) and spin lift (Magnus).

| | High fastball | Curveball | Fastball |
|---|---|---|---|
| Out of the hand | 95 mph, 2,300 rpm backspin | 79 mph, 2,600 rpm topspin (slightly glove side) | 95 mph, same spin as the first |
| Crosses the plate | top of the zone | at the knees | belt-high, inner third |
| Flight to the front of the plate | 0.40 s | 0.48 s | 0.40 s |

**How alike they look.** These gaps are measured at the same distance from the plate, not at the same moment:

| Point in the flight | Gap between fastball and curveball |
|---|---|
| First 10 ft out of the hand | ≈ 3 in |
| 16 ft from the plate (where a hitter has to commit to the curveball) | ≈ 5 in |
| At the plate | ≈ 22 in |

**What that means for the hitter:**
- The curveball gets there **0.08 s later** and **≈ 20 in lower**.
- Commit point: a swing takes ≈ 0.15 s (reported 0.10–0.20 s), so the commit point is 0.15 s before the ball reaches the contact point.
- A swing timed for the curveball is **≈ 0.09 s late** on the fastball.
- The video says they *can* look similar early. It doesn't claim they always look identical out of the hand.

**How the 3D matches the numbers:**
- **Pitcher:** his hand is placed exactly at the simulated release point.
- **Batter:** he's placed so an on-time swing at the final fastball would meet it on the sweet spot.
- **Every other swing** uses that same body and bat. Only the timing changes, so being early or late is real timing in the scene:
  - a fastball-timed swing on the curveball is out in front;
  - a swing that waits to see the curveball is late;
  - a curveball-timed swing on the fastball is late.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.5 s | "Every pitch is designed to mess with the hitter's timing." | From behind the pitcher (fastball released), then the hitter's eyes: the fastball, then a curveball on a different path with both paths drawn. Then a ⅓-speed replay from behind the batter | **FASTBALL? CURVEBALL?** on frame one, then **EVERY PITCH IS DESIGNED TO MESS WITH YOUR TIMING.** word by word |
| 3.5–7.8 s | "…a high fastball, then come back with a curveball." | Center-field camera in real time (high fastball), then the hitter's eyes in real time (curveball) | Pitch chips with name and speed |
| 7.8–12.0 s | "Early on, the pitches can look similar, but the curveball breaks…" | Hitter's eyes at ⅙ speed. A faint yellow fastball rides alongside the curveball at the same distance from the plate, and the two paths separate late | Gap card: 5 in at 16 ft, 22 in at the plate |
| 12.0–15.2 s | "…adjust your timing and where you expect the ball to arrive." | Behind the batter at ⅛ speed, both pitches on the same clock | +0.08 s later · ≈20 in lower |
| 15.2–20.5 s | "And you can't wait to see exactly what the pitch does…" | Hitter's eyes, slowed (then a freeze at the commit point), then real time: he waits, and his swing is late. A ¼-speed replay from behind | RECOGNIZE / PREDICT / COMMIT · ball still 16 ft away · LATE |
| 20.5–27.7 s | "And here's the mind game…" | Close in on the pitcher. Then a fastball-timed swing on a curveball, ¼ speed ("out in front"). Then the hitter's eyes: a dashed expected-curveball path, and a real-time fastball he's late on | **EXPECTING THE BREAKER? THINK AGAIN.** · expected vs actual legend · "depends on the count, the hitter's tendencies, and where the pitcher puts it" |
| 27.7–34.7 s | "That's pitch sequencing…" | Behind the batter: high fastball → curveball → fastball in real time, the paths stacking up, then a freeze as he commits to the last one (curveball timing, fastball already at the plate) | 1 · 2 · 3 sequence chips, **NOW IMAGINE DOING THIS AGAINST 100 MPH.** |

A label in the top-left corner always shows the playback speed.
