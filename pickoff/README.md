# "One step = one extra base?" A pickoff throw out of play

A 38.4 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. The same wild pickoff throw goes into the first-base dugout twice. With the pitcher's pivot foot on the rubber, the runner gets one base. After the pivot foot steps backward off the rubber, he gets two.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `balk`, `lefty` and the other Baseball Decoded videos.
- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×). The text is in `transcript.txt`.
  - Word-by-word captions at the top. The words you capitalized (ENTIRE, ONE, TWO) are highlighted.
  - Each scene starts at or within 0.7 s of its time in your script.
  - Shots, freezes, labels and the base awards are keyed to the words:
    - The release freezes on "throw".
    - The pivot foot lifts on "steps" and lands behind the rubber on "off".
    - The ball reaches the dugout on "dugout" and on "out of play".
    - "1 base" / "2 bases" land on "one" / "two".
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Layout:** captions at the top, the scenario title in a band at the bottom, labels and award cards between them.
- **One cast throughout:** the same right-handed pitcher (white home uniform), runner (gray road uniform, red helmet), first baseman, first-base umpire, catcher, batter and plate umpire, on the same field.
- **Sound:** a `make_bed` bed (style "pulse") ducked up to 7 dB under the voice, whooshes on the cuts and the throws, impacts on the titles, ticks on the labels, the ball hitting the dugout wall, a riser into the freeze, and crowd ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **New in this project:**
  - **Leg IK for the pitcher:** each foot is placed exactly (the ball of the foot, the way the toes point, how far the heel is up), and a two-bone solve bends the hip, knee and ankle to reach it.
    - The pivot foot can turn on the rubber without leaving it, or step back off it to a set spot behind it.
  - **Rubber graphics:**
    - the rubber lights up;
    - a ring follows the pivot foot (cyan while it touches the rubber, orange once it's off);
    - a red bar marks the gap behind the rubber;
    - arrows on the mound show each step.
  - **The runner:** he takes his lead, dives back head-first on the move, gets up on the bag, and trots to the base he's awarded. On the way to third he rounds second.
  - **The first baseman** leaps toward the line for the high, wide throw and misses.
  - **The first-base umpire:** both arms up for dead ball, then he points to the base awarded.
  - **The first-base dugout:** the throw clears the rail and hits the back wall inside it, then drops to the floor.

```bash
python3 tools/physics.py                                       # the field model -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/pickoff.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## The footwork

The pitcher is right-handed and starts in the set, with his right (pivot) foot on the rubber and his left (free) foot toward home.

| | Scenario 1: stays on the rubber | Scenario 2: disengages |
|---|---|---|
| Pivot foot | Turns on the ball of the foot and **stays touching the rubber** through the release and the follow-through (the heel comes up). | **Steps backward off the rubber first** (1.32 to 0.98 s before the release). It lands about a foot behind the rubber's back edge and stays there. |
| Free foot | Steps **directly toward first base**, then he throws. | Stays put while the pivot foot steps back. Only after a pause does it step toward first, and then he throws. |
| What he is for the throw | The pitcher | An infielder |

The free foot never moves first in Scenario 2, and he never throws before he's off the rubber. The step back is straight backward, not sideways.

## The throw

The throw is the same in both plays: about 75 mph (0.9 s), high and about 6 ft wide of the bag toward the home-plate side. The first baseman leaps toward the line, and it goes over his glove into the first-base dugout.

To make that path possible, this ballpark's first-base dugout runs from about 51 to 115 ft down the line, 28 to 39 ft into foul territory. In many real parks the dugout ends closer to home, where a throw this close to the bag couldn't reach it.

## Accuracy notes

- **The rule depends on the pivot foot:**
  - **On the rubber:** a throw by the pitcher from his position on the pitcher's plate that goes into a bench or stands is **one base** (MLB Official Baseball Rules 5.06(b)(4)(H)). The runner goes from first to second.
  - **Stepped backward off it:** "If the pitcher removes his pivot foot from contact with the pitcher's plate by stepping backward with that foot, he thereby becomes an infielder." A wild throw from there is treated like any other infielder's (5.07(e)).
    - A wild throw by an infielder that goes out of play is generally **two bases** from where the runners were when the ball was thrown (5.06(b)(4)(G)). The runner goes from first to third.
  - The rule numbers appear in small type in the side-by-side scene.
- **Dead ball:** the ball is shown going into the dugout. The first-base umpire raises both arms (dead ball), then points the runner to second (Scenario 1) or third (Scenario 2).
- **Same everything else:** the pitcher, runner, first baseman, throw and dugout are identical. A chip says "Same pitcher · same runner · same throw".
- **Labels:**
  - Left: "PITCHER".
  - Right: "NOW TREATED AS AN INFIELDER FOR THE THROW".
  - The rule cards: "Throw out of play: 1 base" / "Wild throw out of play: 2 bases".

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–1.0 s | "One tiny step…" | Low on his feet in the set, pushing in: the pivot foot on the rubber | "His pivot foot, on the rubber" |
| 1.0–1.75 s | "…can cost a team…" | The runner shuffles out to his lead | "The runner takes his lead" |
| 1.75–2.68 s | "…an ENTIRE extra base." | Behind the mound: the sudden pickoff move | |
| 2.68–3.92 s | (pause) | Frozen just before the throw; the camera zooms down to his feet | **ONE STEP = ONE EXTRA BASE?** |
| 3.92–5.04 s | "Watch what happens here." | Behind the runner: the pitcher in the set | **1 · STAYS ON THE RUBBER** |
| 5.04–8.75 s | "The pitcher keeps his pivot foot on the rubber, steps toward first, and makes a pickoff throw." | Low on the feet, slow motion: the free foot steps toward first; frozen at the release on "throw", the pivot foot still on the rubber | "Pivot foot: on the rubber"; "Steps directly toward first" |
| 8.75–9.75 s | "But the ball sails into the dugout." | The throw sails over the leaping first baseman as the runner dives back | "Over the first baseman…" |
| 9.75–10.36 s | (the same) | At the dugout: the ball goes in | |
| 10.36–11.24 s | "The runner is awarded…" | The umpire: arms up | **DEAD BALL** |
| 11.24–12.62 s | "…just ONE base." | The runner trots to second, arriving on the bag | **1 BASE AWARDED** |
| 12.62–13.73 s | "Now watch the difference." | High behind the mound: the same setup | "Same pitcher · same runner · same throw"; **2 · DISENGAGES THE RUBBER** |
| 13.73–17.15 s | "Before throwing, the pitcher legally steps backward off the rubber with his pivot foot." | Above the rubber, slow motion: the pivot foot lifts on "steps" and lands behind the rubber on "off"; frozen | "Pivot foot steps back off the rubber"; "Off the rubber, behind it" |
| 17.15–18.34 s | "He then throws the ball away…" | Behind the mound: off the rubber, he throws (release on "away") | "Now he throws" |
| 18.34–19.88 s | "…and it goes out of play." | The same throw, over the first baseman and into the dugout; then at the dugout | |
| 19.88–20.86 s | "This time, the runner gets…" | The umpire: arms up | **DEAD BALL** |
| 20.86–22.32 s | "…TWO bases." | The runner trots to second, rounds it and goes to third | **2 BASES AWARDED** |
| 22.32–31.52 s | "It's because once the pitcher legally disengages the rubber… treated like a wild throw by another infielder." | Side by side at the release, both pivot feet lit | **WHY THE RULE CHANGES**; PITCHER / NOW TREATED AS AN INFIELDER FOR THE THROW (on "treats"); the base awards; the rule numbers |
| 31.52–36.01 s | "Same pitcher. Same target. Different foot position. And that one detail changes the entire base award." | Side by side: one runner on second, the other on third | "On the rubber: 1 base" / "Off the rubber: 2 bases" |
| 36.01–38.41 s | (end) | (the same) | **SAME THROW. DIFFERENT RULE.**, then Baseball Decoded at 37.26 s |
