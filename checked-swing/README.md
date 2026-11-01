# "What counts as a swing?"

A 43.9 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: how umpires judge a checked swing.

- **No voice in the video:** you record the voiceover separately.
  - The shots are timed to your script read at a brisk, natural pace. `CUES.md` lists when each line should start.
  - The script was read by the local TTS only to measure the timing; that audio isn't in the video or the repo.
- **Audio:** music and effects only, mastered low (about −20 LUFS) so a voice can sit on top.
  - A subtle bed that builds over the opening.
  - Whooshes, impacts, glove pops, a bat tick on the checked-swing contact, and stadium ambience.
- **Framework:** the same three.js field, players, umpires and HyperFrames workflow as `hit-and-run` and `balk`.
- **New in this project:**
  - a check-swing pose and a bat-tip trail
  - a translucent plane at the front edge of home plate
  - base umpires with "yes, he went" and "no swing" signals
  - a mirrored left-handed batter
  - a checked-swing dribbler down the third-base line
  - split screens with a camera per half
  - a Baseball Decoded end card

```bash
python3 tools/physics.py                                       # the pitch and the dribbler -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # timing guide only (assets/vo/timing.json)
python3 build.py                                               # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/checked-swing.mp4 --video-bitrate 16M
```

## Accuracy notes

- **No definition of a swing in MLB's rules:** there's no line the bat has to cross; it's the umpire's judgment of whether the batter attempted to strike at the ball.
  - In 2026, the minors are testing a 45° bat-angle definition with checked-swing challenges (Triple-A, Florida State League).
  - That isn't an MLB rule, so the video doesn't show it.
- **Appeals (OBR 8.02(c)):**
  - The defense can appeal only when the plate umpire has called the pitch a ball; the catcher or manager asks.
  - The plate umpire then asks a base umpire: by convention, the first-base umpire for a right-handed batter and the third-base umpire for a left-handed batter. That umpire's call stands.
  - Signals as shown: a strike fist for "yes, he went", the safe sign for "no".
- **Contact on a check swing:** the ball is a batted ball like any other.
  - Fair: in play and live, as shown: the runner advances and the defense makes a play.
  - Foul: an ordinary foul ball, which is dead unless caught.
  - The script says a foul ball is also live; the screen adds "Contact makes it a batted ball: fair is in play; foul is a foul ball".

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–2.6 s | "What actually counts as a swing in baseball?" | The pitch; he starts and checks; freeze where the bat stops; push in on the bat | **WHAT ACTUALLY COUNTS AS A SWING?** |
| 2.6–6.6 s | "You might think it's as simple as whether the bat crosses home plate, but it's not." | Split, first-base side, slow motion: a check (top) vs a full swing (bottom). The front of the plate is a blue plane; the bat tip's path is traced | CHECKED / FULL SWING; **IT'S NOT JUST ABOUT CROSSING THE PLATE** |
| 6.6–11.7 s | "There is no universal rule…" | A borderline check, frozen, seen from above the plate | "MLB's rulebook doesn't define a swing: it's the umpire's call"; "Where's the line?" |
| 11.7–16.8 s | "Instead, umpires use their judgment…" | Center-field camera: batter, catcher, plate umpire; then close on the hands and bat, slowed | **THE UMPIRE USES JUDGMENT**; "An attempt to hit it?" |
| 16.8–22.3 s | "If the home plate umpire initially calls a pitch a ball, the defensive team can appeal…" | Over the plate umpire's shoulder (Ball), then the catcher appeals and the plate umpire points to first | "Plate umpire: Ball"; "Catcher appeals"; "Did he go?" |
| 22.3–26.8 s | "…to the first or third base umpire. That umpire then makes the final decision." | A whip pan to the first-base umpire; then split: the 1B umpire (right-handed batter) signals a swing, the 3B umpire (left-handed batter) signals no swing | **FIRST OR THIRD BASE UMPIRE**; "He went": strike / "No swing": ball; **FINAL CALL** |
| 26.8–34.1 s | "And here's something interesting… it's a live ball." | Runner on first; contact on a check swing (slowed); the dribbler fair down the third-base line, the runner goes, the throw to first | "Fair", "Runner goes"; **THE BALL IS STILL LIVE!**; the fair/foul note |
| 34.1–41.4 s | "So next time you see a checked swing call…" | Replay from the side, slowed: batter, catcher and umpire; the bat's path and where it ended up | "Where the bat ended up", "Did he try to hit it?" |
| 41.4–43.9 s | (end) | | **NOW YOU KNOW.**, then the Baseball Decoded end card |
