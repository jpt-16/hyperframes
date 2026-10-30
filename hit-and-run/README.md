# "The hit-and-run"

A 29.1 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why the runner is already running, and what happens when the batter makes contact versus when he misses.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `infield-fly`, `tommy-john` and `intentional-walk`.
- **New:**
  - a ground-ball model (hops, then a roll on the grass)
  - the right fielder's charge and throw in
  - the catcher's pop-up throw to second, and the runner's slide with the tag
  - a 2B umpire with the out call
  - flat arrows on the ground and a highlighted hole
- **Voiceover:** your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×); the text is in `transcript.txt`. Shots, word-by-word captions, pins and arrows are keyed to its words.
  - Big titles replace captions for the hook question (**WHY IS THE RUNNER ALREADY RUNNING?**), "Why?" and "That's the hit-and-run".
  - In the slowed overhead replay, the second baseman leaves on "baseman", contact lands on "hole" and the ball goes through the gap on "gap".
- **Music:** a `make_bed` bed (style "drive"), ducked up to 7 dB under the voice.
- **Effects:**
  - bat cracks and pitch whooshes
  - glove pops and a slide scrape
  - hits on the titles, the freeze and the out
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.

```bash
python3 tools/physics.py                                       # the pitch, the ground balls, the fielders -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav)
npx --yes hyperframes@0.8.154 render . -o renders/hit-and-run.mp4 --video-bitrate 16M
```

## The play as shown

**The setup:** a runner on first and a right-handed batter, the same pitch in both versions.
- **The break:** the runner goes with the pitch, breaking on the pitcher's first move.
- **The batter's job:** swing and make contact; he swings in both versions.
- **The coverage:** with a right-handed hitter, the second baseman covers second when the runner breaks. That opens a hole on the right side of the infield, highlighted from above with "2B covers second" and "The hole".
- **Contact:**
  - The ground ball is 92 mph at −4°, toward the right side, behind the runner.
  - It passes about 116 ft out through the spot the second baseman left, 30 ft vs. his original 26 ft over.
  - The right fielder charges it 221 ft out and throws it in to second.
  - The runner, who had a head start, goes first to third.
- **The double play line (a ground ball to short):**
  - 80 mph into the hole; the shortstop ranges 25 ft to his left and has it 1.39 s after contact.
  - By then the runner, who left on the pitch, is about 8 ft from second and into the bag before a throw could get there.
  - So there's no force at second: the throw goes to first for the only out.
- **A miss:**
  - The catcher receives the pitch, pops up and throws to second: the throw leaves at 0.72 s and arrives at 1.82 s.
  - The second baseman covering takes it and tags the sliding runner just before he reaches the bag (the out is by about 0.2 s, not exaggerated).
  - The 2B umpire signals out.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–2.9 s | "A hit-and-run is one of baseball's biggest calculated risks." | Behind the runner as he takes off; the batter swings at the incoming pitch, freeze just before contact | **WHY IS THE RUNNER ALREADY RUNNING?** |
| 2.9–6.2 s | "With a runner on first, the runner takes off…" | High behind the plate (runner, batter pins); beyond first: he breaks on "takes off", with an arrow on his path | "He runs with the pitch" |
| 6.2–9.1 s | "But here's the catch: the hitter is expected to swing and make contact." | Behind the pitcher; then the swing at ½ speed, contact on "contact" | "His job: swing and make contact" |
| 9.1–15.2 s | "Why?" / "…cover second base, opening up a hole…" / "…through that gap" | Slowed replay from above: 2B goes to cover (arrow), the hole lights up, the ball's track goes through it | **WHY?**; "2B covers second", "The hole" |
| 15.2–17.0 s | "…the runner can advance an extra base." | Beyond third: he rounds second and reaches third | **FIRST TO THIRD.** |
| 17.0–20.7 s | "It can also make a double play much harder…" | Above first base: a grounder to short; the runner is already at second; the throw goes to first | "He's already at second: no double play"; "Out at 1st only" |
| 20.7–24.3 s | "But if the hitter swings and misses…easy target for the catcher." | The miss; the catcher's throw; the tag at second | "Swing and miss"; **OUT** |
| 24.3–29.1 s | "One pitch can turn a smart strategy into a costly mistake." / "That's the hit-and-run." | Split, freezing on the outcomes: contact (top) vs. a miss (bottom) | CONTACT / SWING AND MISS; "1st to 3rd ✓" on "smart", "Out at 2nd" on "costly"; **THAT'S THE HIT-AND-RUN.** |
