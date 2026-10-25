# "100 MPH. Could you hit it?"

A 37.8 s vertical (1080×1920, 30 fps) 3D baseball explainer: what it takes to hit a 100 mph fastball.

- **Framework:** built on the same three.js field, players and render workflow as `catcher-clock` and `tag-up`.
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.15×. The script is in `transcript.txt`.
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
| Seeing the pitch | Shown as the first ≈ 0.10 s of flight; the decision fills the gap up to the swing |
| When the swing starts | The ball is still ≈ 20 ft from the contact point |
| A blink | ≈ 0.25–0.45 s for a full blink (Frontiers in Systems Neuroscience review, 2023), so the pitch arrives in about the time it takes to blink |
| Typical reaction to something you see | ≈ 0.20–0.25 s, about when the swing has to start, so a hitter has to anticipate rather than react |
| Ball speed at contact | 91 mph = **1.6 in per millisecond**, so a swing 10 ms early or late meets the ball ≈ 16 in from the bat's path |
| Batted ball | 104 mph, 17° line drive, with the same drag and lift model (Cd 0.40) |

**How the 3D matches the numbers:**
- **Pitcher:** his hand is measured at release and placed exactly at the simulated release point.
- **Batter:** he's placed so the bat's sweet spot (about 6 in from the end of a 34 in bat) meets the ball at the simulated contact point, at the simulated contact time.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.6 s | "You think you could hit a 100-mile-per-hour fastball?" | The pitcher with the ball, the batter, then the delivery chased to the glove | **100 MPH. 0.38 SECONDS.** on frame one, then the question word by word |
| 3.6–8.6 s | "…nearly 147 feet every second." | Center-field camera in real time, then alongside the ball at ⅛ speed past the 0.1 s marks | 100 MPH = 146.7 feet per second |
| 8.6–13.2 s | "…about four-tenths of a second, about as long as a blink." | From above home, replayed at ¼ speed | 60 FT 6 IN → 0.41 S; 52.6 FT → 0.38 S; flight timer; a blinking eye: A BLINK ≈ 0.25–0.45 S |
| 13.2–18.0 s | "Just reacting to something you see takes…" | The batter's eyes, real time | Timeline (see / decide / swing) with the 0.20–0.25 s reaction band on top of the swing start |
| 18.0–23.3 s | "…read the pitch and commit to a swing with the ball still 20 feet away." | The batter's eyes at 1/12 speed | READ. COMMIT. SWING STARTS · BALL STILL 20 FT AWAY |
| 23.3–29.9 s | "Then his hands have to put a round bat on a ball less than three inches wide…" | Slow-motion replay from the side as the swing begins, then a freeze at contact | 2.9 IN; 1.6 in per millisecond; 10 ms ≈ 16 in |
| 29.9–31.8 s | "That's why hitting a baseball…" | Real time: contact on "hitting", a bat crack, the follow-through | ARGUABLY THE HARDEST THING IN SPORTS. |
| 31.8–37.8 s | "…in sports." / "Be honest. Could you make contact?" | High behind the plate, the line drive into the gap | COULD YOU MAKE CONTACT? |

A label in the top-left corner always shows the playback speed: real time, ¼, ⅛ or 1/12 speed, slow-motion replay, or freeze.
