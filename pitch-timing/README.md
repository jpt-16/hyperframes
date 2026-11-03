# "Why pitchers vary their timing"

A 43.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why pitchers change how long they hold the set, and what a runner does when they don't.

- **No voice:** you record the narration separately. `CUES.md` gives each scene's start and end.
- **Audio:** music and effects only, mastered low (about −20 LUFS) so a voice can sit on top.
  - A tension bed (`make_bed`, style "pulse").
  - Glove pops, pitch whooshes, ticks when the pitcher comes set and when he moves, a slide scrape, a dive thud, hits on the titles, and stadium ambience.
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
python3 tools/physics.py     # the pitch -> assets/play.json
python3 build.py             # index.html + assets/mix.wav + CUES.md
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
  - **A long hold:** 2.6 s. The runner leans at 1.2 s, when he expects the pitch, and has to stop.
  - **A pickoff:** the pitcher jump-turns, steps directly toward first and throws (legal, unlike a throw without the step); the runner dives back in time.
- **Not shown:** since 2023, MLB limits pitchers to two disengagements (a step-off or pickoff attempt) per plate appearance; a third that doesn't get the runner is a balk. That is part of why pitchers lean on holds and slide steps.

## Scenes

| Time | Scene | On screen |
|---|---|---|
| 0–4 s | The hook: a pitch from behind the runner, another with the same timing, a push in on the runner studying him | **WHY DON'T PITCHERS ALWAYS USE THE SAME TIMING?**; the meter, 1.2 s twice |
| 4–12 s | The runner is watching: two pitches side by side with the same hold; his line of sight to the pitcher; his feet rocking in rhythm | **RUNNERS LOOK FOR PATTERNS**; "Same timing" |
| 12–21 s | The consequence: the same hold, he goes as the pitcher moves (slowed), the catcher's throw, the slide, safe | **PREDICTABLE TIMING = BETTER JUMPS**; "First move", "He's already going"; SAFE; the numbers |
| 21–32 s | The counters: 1 a slide step, 2 a long hold, 3 a pickoff and a dive back | **KEEP RUNNERS GUESSING**; "Too late to go", "Go? Wait?", "Steps toward first" |
| 32–41.3 s | The takeaway: a varied hold with two looks at the runner, the pitch; then the runner and the pitcher, slowed | **THE BATTLE ISN'T JUST AGAINST THE HITTER.** |
| 41.3–43.5 s | End card | **BASEBALL DECODED** |
