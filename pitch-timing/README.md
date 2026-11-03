# "Why pitchers vary their timing"

A 36.7 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why pitchers change how long they hold the set, and what a runner does when they don't.

- **Voiceover:** your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×); the text is in `transcript.txt`.
  - Shots, word-by-word captions, labels and titles are keyed to its words.
  - The opening question is the big title instead of captions; the other titles from the brief sit mid-frame under the captions.
  - `CUES.md` lists when each line starts, for recording your own read over `assets/mix-novo.wav`.
- **Music:** a tension bed (`make_bed`, style "pulse"), ducked up to 7 dB under the voice.
- **Effects:** glove pops, pitch whooshes, ticks when the pitcher comes set and when he moves, a slide scrape, a dive thud, hits on the titles, and stadium ambience.
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.
- **The hold meter:** an on-screen bar counts how long the pitcher holds the set before his first move, so the pattern (and the break from it) is visible: 1.2 s, 1.2 s, 1.2 s, then 0.4, 2.6 and a pickoff.
- **Framework:** the same three.js field, players and HyperFrames workflow as `hit-and-run`, `balk` and `checked-swing`.
- **Reused:**
  - the catcher's pop and throw, the second baseman covering, and the slide, from `hit-and-run`
  - the pickoff arm action, from `lefty`, here for a right-hander
- **New in this project:**
  - set holds and a slide step
  - looks over at the runner
  - a runner who rocks in rhythm with the pitcher, leans and has to stop, and dives back head first
  - the runner's line of sight
  - a jump turn to first
  - a second-base umpire's safe call

```bash
python3 tools/physics.py                                       # the pitch -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/pitch-timing.mp4 --video-bitrate 16M
```

## The numbers as shown

**Setup:** a right-handed pitcher in the stretch (facing the third-base side), a runner on first with a 12.5 ft lead, and a right-handed batter.

- **Time to the plate:** 1.48 s from the first move to the catcher's glove with a leg kick; 1.23 s with a slide step (a short, low lift).
- **The steal:**
  - The runner breaks as the pitcher moves, having timed the same 1.2 s hold.
  - He reaches the bag 3.3 s after the first move: a 29 ft/s top speed and a slide over the last 8 ft.
  - The catcher's pop time is 1.95 s (receives, pops up and throws to second).
  - The second baseman covers with a right-handed batter at the plate.
  - Safe by about 0.2 s.
- **The counters:**
  - **The slide step:** less time to the plate, too late for the runner to go.
  - **A long hold:** 2.6 s. The runner leans when he expects the pitch and has to stop.
  - **A pickoff:** the pitcher jump-turns, steps directly toward first and throws (legal, unlike a throw without the step); the runner dives back in time.
- **Not shown:** since 2023, MLB limits pitchers to two disengagements (a step-off or pickoff attempt) per plate appearance; a third that doesn't get the runner is a balk. That is part of why pitchers lean on holds and slide steps.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.3 s | "Why do pitchers constantly change how long they take to deliver the ball?" | A pitch from behind the runner, another with the same timing | **WHY DON'T PITCHERS ALWAYS USE THE SAME TIMING?**; the meter, 1.2 s twice |
| 3.3–5.2 s | "Because runners are watching their every move." | The runner's profile and his line of sight to the pitcher | |
| 5.2–10.9 s | "When a pitcher repeatedly uses the same timing, baserunners can recognize patterns…" | Two pitches side by side, first move on "same"; then his feet, rocking in rhythm, the first move on "anticipate" | "Same timing"; **RUNNERS LOOK FOR PATTERNS** |
| 10.9–13.2 s | "This gives them a better opportunity to steal a base." | Up behind the runner: he goes on the first move | "Gone on first move" |
| 13.2–19.7 s | "That's why pitchers mix things up. Sometimes they'll use a quick delivery, other times they'll take longer, and they'll vary their pickoff moves…" | A look over; a slide step on "quick"; a long hold on "take longer" (he leans and stops); a pickoff on "moves" and the dive back | **KEEP RUNNERS GUESSING**; cards 1–3; "Go? Wait?", "Steps toward first", "Back in time" |
| 19.7–21.9 s | "But what happens if a pitcher doesn't change their timing?" | The same 1.2 s hold again | "Same 1.2 s, every pitch" |
| 21.9–26.2 s | "Runners can start getting bigger jumps, stealing bases more easily, and putting pressure on the defense." | He goes on the first move (slowed); the catcher's throw; the slide | **PREDICTABLE TIMING = BETTER JUMPS**; SAFE |
| 26.2–30.4 s | "At higher levels, even a tiny timing advantage can make the difference between safe and out." | The play at second again, very slow; safe on "safe" | runner 3.33 s vs the ball 3.55 s; SAFE |
| 30.4–34.6 s | "In baseball, pitchers aren't just competing against hitters. They're competing against the runners, too." | Behind and above the runner: him, and the pitcher beyond, slowed | **THE BATTLE ISN'T JUST AGAINST THE HITTER.** |
| 34.6–36.7 s | (end) | | **BASEBALL DECODED** |
