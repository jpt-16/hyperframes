# "The count is more than a number"

A 40.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It shows how the count (balls and strikes) changes who has the advantage in an at-bat: 0-2, 3-0, 1-1 and 3-2.

- **No voiceover:** the brief didn't include a script.
  - `assets/mix.wav` is music and effects only, at about −20 LUFS, so a narration can sit on top.
  - `CUES.md` lists each scene's start and end times, so you can record your read to fit.
- **One cast throughout:** the same pitcher (white home uniform), batter (gray road uniform, red helmet, black batting gloves), catcher and umpire, on the same field as the other Baseball Decoded videos.
- **Sound:** a `make_bed` bed (style "pulse"), whooshes and impacts on the titles, a tick on each scoreboard change, glove pops, the bat crack on the foul, and stadium ambience.
- **New in this project:**
  - **The center-field scoreboard:** a 3D video board with a line score, B/S/O lights (balls green, strikes red, outs yellow) and the count in big numbers.
    - It shows the current count in every shot of each scene.
    - In the hook it shows the pitch speed (95 MPH).
    - At ball four it shows **WALK**, with "BALL FOUR" underneath.
  - **The count bug:** a broadcast-style count in the top-left corner, with dots and numbers. In the splits each half has its own bug.
  - **The strike zone:** drawn at the front of the plate, from the knees to the letters. The crossing mark is red for a strike and green for a ball.
  - **The advantage meter:** a Pitcher ↔ Hitter slider that moves with each count.
  - **The umpire's strike call** (right fist), **the catcher's glove** working to where each pitch goes, **a check swing** at 0-2, and **ball four:** he drops the bat and jogs to first.

```bash
python3 tools/physics.py   # the pitches and the foul ball -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/count.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## The pitches (`tools/physics.py`)

Each pitch is simulated with gravity, drag and spin lift. The "crosses" column is where the center of the ball crosses the front of the plate, in feet. x is measured from the middle of the plate (positive is away from this right-handed hitter); y is the height.

| Scene | Pitch | Crosses at (x, y) | Call |
|---|---|---|---|
| Hook | 95 mph fastball | (+0.05, 2.60) | (frozen before it arrives) |
| 0-2 | 85 mph slider, sweeping away | (+1.12, 1.45) | Ball: about 3.5 in off the outside edge. He starts the swing and holds up. |
| 3-0 | 93 mph fastball | (+1.02, 2.55) | Ball four: about 2.3 in off the outside edge, taken |
| 1-1, top | 94 mph fastball | (+0.35, 2.75) | Strike (called): 1-2 |
| 1-1, bottom | 94 mph fastball | (−1.10, 2.60) | Ball, inside: 2-1 |
| 3-2 | 96 mph fastball | (+0.62, 3.05) | In the zone. Fouled straight back: still 3-2. |

The zone's half-width is 8.5 in plus the ball's radius, because a pitch is a strike if any part of the ball passes over any part of the plate. Its height runs from the knees (1.55 ft) to the letters (3.45 ft) for this batter.

## Accuracy notes

- **Balls and strikes are never mixed up:**
  - The board, the bug and the dots always list balls first (B, then S).
  - Ball lights are green and strike lights red, matching the crossing marks (red is a strike, green is a ball).
  - Each count is shown as balls–strikes: 0-2 is no balls and two strikes; 3-0 is three balls and no strikes.
- **0-2: the pitcher's advantage.**
  - The pitch is a slider just off the plate, and the hitter starts the swing and checks it.
  - The note reads: "Hitter: anything close could be strike three, so he has to protect the zone. Pitcher: can work just off the plate and try to get a chase."
- **3-0: the hitter's advantage.**
  - "One more ball is a walk".
  - He takes a fastball just off the plate. The board changes to ball four and WALK, and he drops the bat and jogs to first.
  - The note reads: "At 3-0 the pitcher can't afford another ball, so the hitter can wait for a strike he likes."
- **1-1: the next pitch changes everything.**
  - The top and bottom halves show the same moment.
  - On top, a called strike (the umpire's punch) makes it 1-2: "Strike: pitcher ahead".
  - On the bottom, a ball inside makes it 2-1: "Ball: hitter ahead".
- **3-2: every pitch matters.**
  - The note reads: "Hitter: a strike he takes is strike three. Pitcher: a ball is ball four."
  - The pitch is in the zone, so the hitter protects and fouls it straight back.
  - The chip reads "Foul with two strikes: still 3-2". A foul can't be strike three unless it's a caught foul tip or a bunt.
- **The montage** stamps each count with its label: 0-2 "Pitcher's advantage", 3-0 "Hitter's advantage", 1-1 "Up for grabs", 3-2 "Every pitch matters".

## Shots

| Time | Scene | Shot | On screen |
|---|---|---|---|
| 0–1.9 s | Hook | Behind the pitcher; the fastball from beside the plate, with the board reading 95 MPH | **95 MPH** |
| 1.9–4.2 s | Hook | Top/bottom freeze: the same pitch just before the plate, with the zone | Bugs 0-2 "Pitcher's count" / 3-0 "Hitter's count"; **SAME PITCH. DIFFERENT ADVANTAGE.** |
| 4.2–5.4 s | 0-2 | The board: 0-2 | **0-2: PITCHER'S ADVANTAGE** |
| 5.4–7.85 s | 0-2 | From center field: the slider; he starts the swing and holds up | "He starts the swing… and holds up"; meter toward the pitcher |
| 7.85–10.2 s | 0-2 | Slow motion over the umpire: the slider misses the zone | "Just off the plate"; the note |
| 10.2–11.0 s | 3-0 | The board: 3-0 | **3-0: HITTER'S ADVANTAGE** |
| 11.0–13.4 s | 3-0 | Over the umpire: the fastball just off the plate, taken | "One more ball is a walk"; "Ball four: just off the plate" |
| 13.4–14.6 s | 3-0 | The board: BALL FOUR, WALK | Bug: WALK |
| 14.6–17.2 s | 3-0 | He drops the bat and jogs to first | The note |
| 17.2–18.2 s | 1-1 | The board: 1-1 | **1-1** |
| 18.2–25.2 s | 1-1 | Top/bottom over the umpire: a called strike (1-2) / a ball (2-1) | **1-1: THE NEXT PITCH CHANGES EVERYTHING**; bugs, labels, meters |
| 25.2–26.2 s | 3-2 | The board: 3-2 FULL COUNT | **3-2: EVERY PITCH MATTERS** |
| 26.2–28.4 s | 3-2 | Behind the pitcher as he comes set and holds | The note; meter in the middle |
| 28.4–30.0 s | 3-2 | The hitter's hands on the bat, close | |
| 30.0–31.6 s | 3-2 | Over the hitter's shoulder: the delivery and the pitch | |
| 31.6–33.0 s | 3-2 | Slow motion: he protects, with the bat path | "Fouled off: he stays alive" |
| 33.0–34.2 s | 3-2 | From in front, slow: the ball goes straight back over the screen | "Foul with two strikes: still 3-2" |
| 34.2–36.6 s | Montage | Freezes: 0-2, 3-0, 1-1, 3-2 | The count stamps |
| 36.6–40.5 s | Ending | Wide over the stadium, the board on 3-2; Baseball Decoded | **THE COUNT IS MORE THAN A NUMBER.** |
