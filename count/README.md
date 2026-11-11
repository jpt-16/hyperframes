# "The count is more than a number"

A 40.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It shows how the count (balls and strikes) changes who has the advantage in an at-bat: 0-2, 3-0, 1-1 and 3-2.

- **Voiceover:**
  - Your script ("How counts create leverage"), voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.6×). The text is in `transcript.txt`.
  - The counts are read the way a broadcaster says them ("oh and two", "three and oh", "one and one"); the captions keep the numerals (0-2, 3-0, 1-1).
  - Shots, word-by-word captions, titles, labels and the pitches are keyed to its words.
  - Your scene times hold: each scene starts within about 0.7 s of the time in your script, and the whole video is 40.4 s.
  - The opening question is covered by the hook's split screen and title instead of captions.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Layout:** captions at the top; scene titles in a band under them (at the seam in the top/bottom splits); the scoreboard sits under the band.
- **One cast throughout:** the same pitcher (white home uniform), batter (gray road uniform, red helmet, black batting gloves), catcher and umpire, on the same field as the other Baseball Decoded videos.
- **Sound:** a `make_bed` bed (style "pulse") ducked up to 7 dB under the voice, whooshes and impacts on the titles, a tick on each scoreboard change, glove pops, the bat crack on the foul, and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **New in this project:**
  - **The center-field scoreboard:** a 3D video board with a line score, B/S/O lights (balls green, strikes red, outs yellow) and the count in big numbers.
    - It shows the current count in every shot of each scene.
    - In the hook it shows the pitch speed (95 MPH).
    - At ball four it shows **WALK**, with "BALL FOUR" underneath.
  - **The count bug:** a broadcast-style count in the top-left corner, with dots and numbers. In the splits each half has its own bug.
  - **The strike zone:** drawn at the front of the plate, from the knees to the letters. The crossing mark is red for a strike and green for a ball.
  - **The chase zone:** on "expand the zone" an orange outline grows out from the strike zone, about 5 in past each edge.
  - **The advantage meter:** a Pitcher ↔ Hitter slider that moves with each count.
  - **The umpire's strike call** (right fist), **the catcher's glove** working to where each pitch goes, **a check swing** at 0-2, and **ball four:** he drops the bat and jogs to first.

```bash
python3 tools/physics.py                                       # the pitches and the foul ball -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/count.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## The pitches (`tools/physics.py`)

Each pitch is simulated with gravity, drag and spin lift. The "crosses" column is where the center of the ball crosses the front of the plate, in feet. x is measured from the middle of the plate (positive is away from this right-handed hitter); y is the height.

| Scene | Pitch | Crosses at (x, y) | Call |
|---|---|---|---|
| Hook | 95 mph fastball | (+0.78, 2.45) | Frozen before it arrives: on the outside edge, a borderline strike (the ball just catches the plate) |
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
- **The hook:** "an easy take in one count, but a must-swing in another" is shown with one borderline pitch on the outside edge.
  - At 3-0 ("Easy take") a hitter can let it go, since even a strike only makes it 3-1.
  - At 0-2 ("Must swing") it's close enough to be called strike three, so he has to protect.
  - The label reads "On the edge: a strike".
- **0-2: the pitcher's advantage.**
  - "Expand the zone": the chase zone grows out from the strike zone.
  - "Breaking balls off the plate": a slider crosses just off the outside edge on "plate", inside the chase zone. The hitter starts the swing and checks it.
  - The note reads: "Hitter: anything close could be strike three, so he has to protect the zone. Pitcher: can work just off the plate and try to get a chase."
- **3-0: the hitter's advantage.**
  - "One more ball is a walk".
  - He takes a fastball just off the plate. The board changes to ball four and WALK, and he drops the bat and jogs to first.
  - The note reads: "At 3-0 the pitcher can't afford another ball, so the hitter can wait for a strike he likes."
- **1-1: the next pitch changes everything.**
  - The top and bottom halves show the same moment.
  - On top, a called strike (the umpire's punch) crosses the plate on "strike" and makes it 1-2: "Strike: pitcher ahead".
  - On the bottom, a ball inside crosses on "ball" and makes it 2-1: "Ball: hitter ahead".
  - Until then both meters sit in the middle: "neither side has a major advantage".
- **3-2: every pitch matters.**
  - The note reads: "Hitter: a strike he takes is strike three. Pitcher: a ball is ball four."
  - "Throw a strike without giving up a good opportunity to hit": the pitch is a strike on the upper outside corner, labeled "On the corner: a strike, but hard to hit".
  - The hitter protects and fouls it straight back.
  - The chip reads "Foul with two strikes: still 3-2". A foul can't be strike three unless it's a caught foul tip or a bunt.
- **The montage** stamps each count with its label: 0-2 "Pitcher's advantage", 3-0 "Hitter's advantage", 1-1 "Up for grabs", 3-2 "Every pitch matters".

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–1.55 s | "Why can the exact same pitch…" | Behind the pitcher, the board reading 95 MPH; the fastball from beside the plate | **95 MPH** |
| 1.55–3.96 s | "…be an easy take in one count… but a must-swing in another?" | Top/bottom freeze: the same pitch just before the plate, with the zone | 3-0 "Easy take" / 0-2 "Must swing" (on "must swing"); "On the edge: a strike"; **SAME PITCH. DIFFERENT ADVANTAGE.** |
| 3.96–5.71 s | "With two strikes, the pitcher has the advantage." | The board: 0-2 | **0-2: PITCHER'S ADVANTAGE**; meter to the pitcher |
| 5.71–7.05 s | "They can expand the zone…" | Over the umpire: the chase zone grows on "expand" | "Chase zone" |
| 7.05–8.5 s | "…throw breaking balls off the plate…" | From center field: the slider crosses on "plate"; he starts the swing and holds up | "He starts the swing… and holds up" |
| 8.5–10.73 s | "…and make the hitter protect against more possibilities." | Slow motion over the umpire: the slider misses the zone, inside the chase zone | "Just off the plate"; the note |
| 10.73–12.1 s | "But at 3-0, everything changes." | The board: 3-0 | **3-0: HITTER'S ADVANTAGE**; meter to the hitter on "changes" |
| 12.1–15.56 s | "The hitter can be much more selective because one ball means a walk." | Over the umpire: a fastball just off the plate, taken, crossing on "walk" | "One more ball is a walk"; "Ball four: just off the plate" |
| 15.56–16.21 s | "The pitcher has very little…" | The board: BALL FOUR, WALK | Bug: WALK |
| 16.21–17.2 s | "…room for error." | He drops the bat and jogs to first | The note |
| 17.2–17.94 s | "At 1-1…" | The board: 1-1 | **1-1** |
| 17.94–23.92 s | "…neither side has a major advantage. The next pitch can shift the entire at-bat. A strike creates 1-2, while a ball creates 2-1." | Top/bottom over the umpire: a called strike on "strike" / a ball on "ball" | **1-1: THE NEXT PITCH CHANGES EVERYTHING**; bugs, labels, meters |
| 23.92–25.52 s | "And at a full count, every pitch matters." | The board: 3-2 FULL COUNT | **3-2: EVERY PITCH MATTERS** |
| 25.52–26.78 s | (pause) | Behind the pitcher as he comes set and holds | Meter "Both under pressure"; the note |
| 26.78–28.3 s | "The hitter has to protect the strike zone…" | The hitter's hands on the bat, close | |
| 28.3–29.3 s | "…while the pitcher has to throw…" | Over the hitter's shoulder: the delivery | |
| 29.3–31.23 s | "…a strike without giving up a good opportunity to hit." | Slow motion over the umpire: the pitch on the corner; he fouls it off | "On the corner: a strike, but hard to hit"; "He protects: fouled off" |
| 31.23–32.55 s | (pause) | From in front, slow: the ball goes straight back over the screen | "Foul with two strikes: still 3-2" |
| 32.55–34.95 s | "That's what makes baseball so strategic." | Freezes: 0-2, 3-0, 1-1, 3-2 | The count stamps |
| 34.95–36.1 s | "The count doesn't just track balls and strikes." | The board: the B and S lights at 3-2 | |
| 36.1–40.37 s | "It changes the leverage of every pitch." | Wide over the stadium; Baseball Decoded | **THE COUNT IS MORE THAN A NUMBER.**, then the logo |
