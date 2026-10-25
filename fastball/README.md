# "100 MPH. Could you hit it?"

A 27.3 s vertical (1080×1920, 30 fps) 3D baseball explainer: what it takes to hit a 100 mph fastball.

- **Framework:** built on the same three.js field, players and render workflow as `catcher-clock` and `tag-up`.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_adam` at 1.25× for an energetic sports-documentary read.
- **Sync:** word-timed captions and shots keyed to the narration.
- **Sound:** effects under the voice, mastered to about −14 LUFS.

```bash
python3 tools/physics.py                                       # the pitch, swing timing, batted ball -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/fastball-100.mp4 --video-bitrate 16M
```

## The physics (`tools/physics.py`)

| | Value |
|---|---|
| 100 mph | **146.7 ft/s** |
| Rubber to the back of the plate | 60 ft 6 in |
| At a constant 100 mph | 60.5 / 146.7 = **0.41 s** |
| Release point | 6.5 ft in front of the rubber, 6.0 ft high, 1.9 ft to the arm side, so **52.6 ft** from the front of the plate |
| Ball flight | Drag (Cd 0.35, ρ 1.19 kg/m³) plus four-seam backspin lift (2,300 rpm), aimed belt-high over the middle |
| Speed at the plate | **91 mph** |
| Flight to the front of the plate | **0.38 s** |
| Contact point | 1.3 ft in front of the plate, at 0.37 s |
| Swing, start to contact | ≈ 0.15 s (pro swings are reported at roughly 0.10 to 0.20 s), so it starts by **≈ 0.22 s** after release |
| Recognition | Shown as the first ≈ 0.10 s of flight; the decision fills the gap up to the swing |
| Ball speed at contact | 91 mph = **1.6 in per millisecond**, so a swing 10 ms early or late meets the ball ≈ 16 in from the bat's path |
| Batted ball | 104 mph, 17° line drive, with the same drag and lift model (Cd 0.40) |

**How the 3D matches the numbers:**
- **Pitcher:** his hand is measured at release and placed exactly at the simulated release point.
- **Batter:** he's placed so the bat's sweet spot (about 6 in from the end of a 34 in bat) meets the ball at the simulated contact point, at the simulated contact time.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–0.75 s | (frame one) | Pitcher on the mound, ball in his hand | **100 MPH. 0.38 SECONDS.** |
| 0.75–1.35 s | "You think you could hit…" | Low angle on the batter | The question, word by word |
| 1.35–3.2 s | "…a 100-mile-per-hour fastball?" | The delivery from behind the mound; the camera chases the ball to the glove | **100 MPH** in orange |
| 3.2–4.9 s | "At that speed…" | Center-field camera, real time | Real time |
| 4.9–7.3 s | "…nearly 147 feet every second." | Alongside the ball at ⅛ speed, passing white marks every 14.7 ft (0.1 s at a constant 100 mph) | 100 MPH = 146.7 feet per second |
| 7.3–11.4 s | "…around four-tenths of a second." | From above home, replayed at ¼ speed, with labels for the rubber and the release point | 60 FT 6 IN → 0.41 S; 52.6 FT → 0.38 S; a flight timer |
| 11.4–15.2 s | "…you can't wait until the ball reaches you…" | The batter's eyes, real time | Timeline: recognize / decide / swing ≈ 0.15 s; the swing must start by ≈ 0.22 s |
| 15.2–19.8 s | "…recognize, decide, swing…" | The batter's eyes at 1/12 speed; the playhead crosses each phase on its word | RECOGNIZE. DECIDE. SWING. |
| 19.8–24.5 s | "That's what makes…" | Slow-motion replay from the side, then a freeze at contact | 1.6 in per millisecond; 10 ms ≈ 16 in |
| 24.5–27.3 s | "Be honest. Could you make contact?" | Real time: contact on "honest", a bat crack, the follow-through | THAT'S WHY 100 MPH IS ELITE. COULD YOU MAKE CONTACT? |

A label in the top-left corner always shows the playback speed: real time, ¼, ⅛ or 1/12 speed, slow-motion replay, or freeze.
