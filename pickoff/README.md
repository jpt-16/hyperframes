# "One step = one extra base?" A pickoff throw out of play

A 38.0 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. The same wild pickoff throw goes into the first-base dugout twice. With the pitcher's pivot foot on the rubber, the runner gets one base. After the pivot foot steps backward off the rubber, he gets two.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `balk`, `lefty` and the other Baseball Decoded videos.
- **No voiceover:** the brief didn't include a script.
  - `assets/mix.wav` is music and effects only, at about −20 LUFS, so a narration can sit on top.
  - `CUES.md` lists each scene's start and end times.
- **One cast throughout:** the same right-handed pitcher (white home uniform), runner (gray road uniform, red helmet), first baseman, first-base umpire, catcher, batter and plate umpire, on the same field.
- **Sound:** a `make_bed` bed (style "pulse"), whooshes on the cuts and the throws, impacts on the titles, ticks on the labels, the ball hitting the dugout wall, a riser into the freeze, and crowd ambience.
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
python3 tools/physics.py   # the field model -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
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

| Time | Scene | Shot | On screen |
|---|---|---|---|
| 0–1.15 s | Hook | Low on his feet in the set, pushing in: the pivot foot on the rubber | "His pivot foot, on the rubber" |
| 1.15–1.95 s | Hook | The runner shuffles out to his lead, the first baseman holding him | "The runner takes his lead" |
| 1.95–2.9 s | Hook | Behind the mound: the sudden pickoff move | |
| 2.9–4.0 s | Hook | Frozen just before the throw; the camera zooms down to his feet | **ONE STEP = ONE EXTRA BASE?** |
| 4.0–5.0 s | One base | Behind the runner: the pitcher in the set | **1 · STAYS ON THE RUBBER** |
| 5.0–7.25 s | One base | Low on the feet, slow motion, then frozen at the release: the pivot foot on the rubber, the free foot stepping toward first | "Pivot foot: on the rubber"; "Steps directly toward first" |
| 7.25–8.45 s | One base | The throw sails over the leaping first baseman as the runner dives back | "Over the first baseman…" |
| 8.45–9.15 s | One base | At the dugout: the ball goes in | "…into the dugout" |
| 9.15–10.75 s | One base | The umpire: arms up, then points to second | **DEAD BALL** |
| 10.75–12.0 s | One base | The runner trots to second | **1 BASE AWARDED** |
| 12.0–13.1 s | Two bases | High behind the mound: the same setup | "Same pitcher · same runner · same throw"; **2 · DISENGAGES THE RUBBER** |
| 13.1–16.0 s | Two bases | Above the rubber, slow motion, then frozen: the pivot foot steps back off it | "Pivot foot steps back off the rubber"; "Off the rubber, behind it" |
| 16.0–17.1 s | Two bases | Behind the mound: off the rubber, he throws | "Now he throws" |
| 17.1–18.9 s | Two bases | The same throw into the dugout | "…into the dugout" |
| 18.9–20.5 s | Two bases | The umpire: arms up, then points to third | **DEAD BALL** |
| 20.5–22.0 s | Two bases | The runner trots to second, rounds it and goes to third | **2 BASES AWARDED** |
| 22.0–32.0 s | Why | Side by side at the release, both pivot feet lit | **WHY THE RULE CHANGES**; PITCHER / NOW TREATED AS AN INFIELDER FOR THE THROW; the base awards |
| 32.0–38.0 s | Ending | Side by side: one runner on second, the other on third; Baseball Decoded | **SAME THROW. DIFFERENT RULE.** |
