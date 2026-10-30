# "The hit-and-run"

A 32.8 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why the runner is already running, and what happens when the batter makes contact versus when he misses.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `infield-fly`, `tommy-john` and `intentional-walk`.
- **New:**
  - a ground-ball model (hops, then a roll on the grass)
  - the right fielder's charge and throw in
  - the catcher's pop-up throw to second, and the runner's slide with the tag
  - a 2B umpire with the out call
  - flat arrows on the ground and a highlighted hole
- **Audio:** no narration; the brief asked for the play to read without it. Short on-screen text carries it. A `make_bed` music bed (style "drive") lands its chord on the closing line. Effects:
  - bat crack and pitch whooshes
  - glove pops and a slide scrape
  - hits on the titles, the freeze and the out
  - a crowd lift as the ball goes through
- **Mix:** mastered to about −14 LUFS.

```bash
python3 tools/physics.py        # the pitch, the ground ball, the right fielder -> assets/play.json
python3 build.py                # index.html + assets/mix.wav
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
- **A miss:**
  - The catcher receives the pitch, pops up and throws to second: the throw leaves at 0.72 s and arrives at 1.82 s.
  - The second baseman covering takes it and tags the sliding runner just before he reaches the bag (the out is by about 0.2 s, not exaggerated).
  - The 2B umpire signals out.

## Shots

| Time | Shot | On screen |
|---|---|---|
| 0–2.3 s | Behind the runner as he takes off; in front of the batter as he swings at the incoming pitch, freeze just before contact, push-in | **WHY IS THE RUNNER ALREADY RUNNING?**; runner pin |
| 2.3–4.4 s | High behind the plate: pitcher, batter, runner on first | **THE HIT-AND-RUN**; runner and batter pins |
| 4.4–6.4 s | Beyond first: the runner breaks with the delivery; an arrow on his path | "He runs with the pitch" |
| 6.4–7.9 s | In front of the batter: contact, a ground ball | "The batter's job: swing and make contact" |
| 7.9–11.0 s | Replay from above: 2B goes to cover (arrow); the hole lights up; the ball's track goes right through it | "2B covers second", "The hole", "Ground ball right where he was" |
| 11.0–15.8 s | The ball rolls into right field; beyond third, the runner rounds second and reaches third | "Through the right side"; **FIRST TO THIRD.** |
| 15.8–23.6 s | The same setup: the runner goes, the batter swings and misses; the catcher's throw; the tag at ½ speed; the out | **SAME PLAY. HE MISSES.**; "Swing and miss"; "The catcher throws to second"; **OUT**; "No contact: the runner is exposed" |
| 23.6–32.8 s | Split screen, the same pitch: contact (top) vs. a miss (bottom), freezing on the outcomes | CONTACT / SWING AND MISS; "1st to 3rd ✓" / "Out at 2nd"; **ONE SWING DECIDES IT.** |
