# Why the best play isn't always the easy out (33.2 s, 1080x1920)
New in `field.js`: runners on the bases (`s.rn` with `R`, `R2`: stay / run to a bag / slide, `tArr` = arrival time), `thr.how: "hold"` (the shortstop keeps the ball), `s.flook` (his eyes to a base), overhead arrows (`s.arr`, `makeArrow(color, w)`). The base-state widget (runners and outs) is built in `build.py` (`state(...)`). Play timings in `tools/plan.json` (probed with `throwOf`/`dpPlan`).
| Time | Scene |
|---|---|
| 0.0 | Hook: runner on first, grounder to the shortstop, the easy out at first, frozen |
| 3.4 | 1. Get the lead runner: the same ball, the throw to second; the two outcomes from above |
| 9.5 | 2. Turn two: runners on first and second, the pivot, slow-motion replay |
| 15.8 | 3. Don't force it: the runner is already at second; the shortstop keeps the ball |
| 23.1 | 4. Think before you throw: the same ball in three situations from above |
| 29.1 | Three smart decisions and a clean overhead; BASEBALL IQ WINS PLAYS. |
