# "Pitch tipping": what if the hitter knew the pitch before it was thrown?

A 55.6 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: how pitchers tip pitches, how teams find the pattern, how the information gets to the hitter, and what it's worth.

- **No voiceover**, per the brief. `CUES.md` lists each scene's start and end so you can record narration over it.
- **Sound:** a `make_bed` bed (style "pulse"), whooshes, impacts on the titles, soft ticks as the catcher's signs flash, glove pops, the bat crack (low and long, in slow motion) and stadium ambience.
- **Mix:** mastered to −20 LUFS so there is room for a voice on top, in `assets/mix.wav`.
- **One cast throughout:** the same pitcher (white home uniform), batter (gray road uniform, red helmet, black batting gloves), catcher and umpire, on the same field as the other Baseball Decoded videos.
- **New in this project:**
  - **The tells:** built into the pitcher's set and delivery.
    - Where his hands come together: at the belt or at the chest.
    - The glove flaring while his hand works the grip inside it.
    - How long he holds the set.
    - A yellow ring finds the glove in any camera.
  - **The scouting room:** a second 3D scene with a hitting coach, two hitters at a table, a laptop and a video wall.
    - The wall plays two live renders of the same pitcher on a loop: the clip before the fastball above the one before the curveball.
    - Beside them is a pitch log whose matching rows light up one by one.
  - **The signs:**
    - The catcher's jointed hand flashes finger signs between his thighs, seen through a runner's-view lens.
    - The runner at second touches his helmet.
    - Another team's coach touches his cap and swipes his arm from the dugout rail.
  - **The close-up of the ball in the pitcher's hand:** his fingers are solved at load to wrap a stitched baseball in a four-seam grip.

```bash
python3 tools/physics.py   # the fastball, the curveball, the batted ball -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/tipping.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## The pitches (`tools/physics.py`)

| | Speed | Spin | Crosses the front of the plate |
|---|---|---|---|
| Fastball | 94 mph | 2,300 rpm backspin | (+0.20, 2.80) ft after 0.401 s |
| Curveball | 79 mph | 2,600 rpm topspin | (−0.10, 2.00) ft after 0.478 s |

The payoff: the curveball is barreled for a 101 mph line drive at 15° into left-center, landing about 300 ft out.

## Accuracy notes

- **The tells are hypothetical:**
  - All three are made-up examples for this one pitcher, labeled "Before the fastball" and "Before the curveball".
  - An on-screen note says: "Hypothetical examples for one pitcher. Real tells vary, and no single move always means one pitch."
  - Nothing says a glove position always means a particular pitch.
- **The examples cover what the brief lists:**
  - **Glove position:** hands at the belt vs. at the chest.
  - **Hand movement:** the glove flares while he changes his grip.
  - **Delivery timing:** 0.9 s vs. 1.8 s in the set, with timer bars.
- **Patterns, not single clips:**
  - The scouting room compares two clips, then a pitch log of eight pitches. The pin reads "Hands at the chest → curveball, every time in this log".
  - The note reads: "Teams look for a move that repeats, not one clip."
- **Reading signs:**
  - The runner at second reads the catcher's sequence. The pin reads "Second sign is live: 2 = curveball (this example)".
  - He relays it with a prearranged signal (a hand to the helmet), and the batter sees it.
- **Systems vary:**
  - A different team's coach uses a different signal from the dugout.
  - The note reads: "Every team sets its own signals, and changes them."
- **No electronics:** the note says "Reading signs by sight is part of the game. Using electronics to steal them is against MLB rules." No device appears in the relay.
- **The payoff** shows the batter spotting the tell (the ring and "Hands at the chest: curveball coming"), then waiting on the curveball and barreling it.

## Shots

| Time | Shot | On screen |
|---|---|---|
| 0–1.6 s | On the mound, side on: he looks in and comes set, hands at the chest | **WHAT IF THE HITTER KNEW THE PITCH BEFORE IT WAS THROWN?** |
| 1.6–2.5 s | Over the batter's shoulder, looking out at him | |
| 2.5–3.15 s | The delivery | |
| 3.15–5.0 s | Frozen at the stride, just before release; the camera pushes into his glove | "The glove"; Freeze |
| 5.0–9.0 s | Top and bottom: coming set before a fastball (belt) and a curveball (chest), then a freeze | **GLOVE POSITION**; "Hands at the belt" / "Hands at the chest"; the hypothetical note |
| 9.0–13.0 s | Close on the glove: before the curveball it flares as he changes his grip (slowed, then frozen) | **HAND MOVEMENT**; "Glove stays still" / "Glove flares as he changes his grip" |
| 13.0–17.0 s | Full delivery, each: 0.9 s in the set before the fastball, 1.8 s before the curveball | **DELIVERY TIMING**; timer bars |
| 17.0–19.4 s | The scouting room: the wall, the table, the hitters | **STUDY THE VIDEO** |
| 19.4–22.0 s | The wall: both clips, rings on the glove | **FIND THE PATTERN**; "Before the fastball: hands at the belt" / "Before the curveball: hands at the chest" |
| 22.0–24.4 s | The pitch log: the curveball rows light up one by one | "Hands at the chest → curveball, every time in this log" |
| 24.4–27.0 s | The hitters: one leans in and points, the other nods; the coach turns to the wall | "There it is"; "Teams look for a move that repeats, not one clip." |
| 27.0–29.4 s | Behind the runner at second, looking in | **RECOGNIZE IT** |
| 29.4–31.6 s | The runner's view: the catcher's signs, 1-2-3 | "Second sign is live: 2 = curveball (this example)" |
| 31.6–33.4 s | The runner: hand to the helmet | **RELAY IT**; "Prearranged signal: hand to the helmet" |
| 33.4–35.0 s | Over the batter's shoulder to second; he gets it | "Got it" |
| 35.0–37.3 s | Another team's coach on the dugout rail: a touch of the cap, a swipe of the arm | "Another team: a signal from the dugout"; "Every team sets its own signals, and changes them." |
| 37.3–39.0 s | High behind home: the batter digs in | **USE THE ADVANTAGE**; the note on electronics |
| 39.0–42.25 s | The batter's eyes: the hands come set at the chest; the delivery | Ring; "Hands at the chest: curveball coming" |
| 42.25–44.65 s | Slow motion: he waits on the curveball and barrels it | |
| 44.65–49.0 s | The line drive into left-center | **KNOWING THE PITCH CHANGES EVERYTHING** |
| 49.0–51.8 s | He walks back up the mound, looking in at the catcher | **THE BEST PITCHERS DON'T GIVE ANYTHING AWAY.** |
| 51.8–53.8 s | The ball in his hand, close | |
| 53.8–55.6 s | Baseball Decoded end card | |
