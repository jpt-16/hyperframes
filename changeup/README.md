# "This pitch makes 95 mph look even faster": the changeup

A 36.0 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. A changeup comes out of the same delivery as a 95 mph fastball, arrives later, and the hitter's swing gets there first.

- **Framework:** the same three.js field, players, bat, gloved hands, split-screen renderer and HyperFrames workflow as `count`, `choke-up` and the other Baseball Decoded videos.
- **No voiceover:** the brief didn't include a script.
  - `assets/mix.wav` is music and effects only, at about −20 LUFS, so a narration can sit on top.
  - `CUES.md` lists each scene's start and end times.
- **One cast throughout:** the same right-handed pitcher (white home uniform) and right-handed hitter (gray road uniform, red helmet, black batting gloves), with the same catcher and umpire, on the same field.
- **Sound:** a `make_bed` bed (style "pulse"), whooshes on the cuts, the releases and the swings, glove pops, the bat crack on the barreled fastball, impacts on the titles, and stadium ambience.
- **New in this project:**
  - **One delivery for both pitches:** the pitcher's animation is literally the same function of time for the fastball and the changeup. Only the ball's flight differs.
  - **The arm path:** a trail of where his throwing hand has been over the last half second, cyan for the fastball and orange for the changeup. The two arcs match.
  - **An early swing:** the hitter's swing can be timed and placed for one pitch (the fastball) while the ball is another (the changeup). He can also lunge further out in front when he's completely fooled.
  - **The race camera:** a dolly beside the pitch path keeps pace with the fastball and stops at the plate. Both panes use the same camera move, so the changeup falls behind in its frame.
  - **Speed bars:** each pitch's bar fills as the ball travels, and its time to the plate (0.40 s vs. 0.44 s) appears when it gets there.
  - **The catcher's mitt:** the catcher's arm is solved once per pitch, so the mitt is exactly where each pitch ends (he sets up on the spot). The ball goes into the mitt without jumping.
  - **The radar reading** on the center-field board: "95 · FASTBALL", "85 · CHANGEUP", "84 · CHANGEUP".

```bash
python3 tools/physics.py   # the fastball, the changeups, the line drive -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/changeup.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## The pitches (`tools/physics.py`)

Every pitch is simulated with gravity, drag and spin lift. All three are released from the same point: 6.0 ft high, 1.9 ft to the arm side, 54 ft from the plate.

| | Speed | Spin | Crosses the front of the plate (ft) | Release to plate |
|---|---|---|---|---|
| Fastball | 95 mph | 2,400 rpm backspin | (+0.30, 2.35) | 0.397 s |
| Changeup | 85 mph | 1,750 rpm, tilted to the arm side | (+0.05, 2.00) | 0.443 s |
| Changeup (the payoff) | 84 mph | 1,750 rpm, tilted to the arm side | (+0.45, 1.80) | 0.449 s |

- **When the fastball reaches the plate,** the changeup is 0.046 s behind and still about 5.3 ft short of it.
- **Where the swing meets the fastball** (its contact point, about 1.2 ft in front of the plate), the changeup is still about 5.2 ft away. That's why the same swing barrels the fastball (a 101 mph line drive) and misses the changeup.

## Accuracy notes

- **A realistic speed gap:** 10 mph (95 vs. 85). Big-league changeups commonly run about 8 to 10 mph slower than the same pitcher's fastball. The time difference is under five hundredths of a second. The slow motion and the freeze make it visible.
- **No trick movement:**
  - The changeup has less spin and its spin is tilted to the arm side, so it fades slightly toward a right-handed hitter and drops a little more than the fastball.
  - It's a smooth path from the same physics as the fastball. It never stops, swerves or changes direction.
- **The same arm action:**
  - The delivery is identical for both pitches (same function, same timing, same release point). The hand-path trails overlap.
  - The note reads: "To the hitter, both start the same way. Only the grip, hidden in his hand, takes speed off the changeup."
- **The hitter's problem is timing:**
  - His swing is the swing he'd use against the fastball: same timing, same path.
  - Against the changeup it reaches the hitting zone first. The freeze labels "Bat: already in the zone" and "Ball: still coming", then the ball crosses the zone after the bat.
- **The payoff:** on the 84 mph changeup he starts even earlier and lunges, way out in front, and the ball goes into the mitt.

## Shots

| Time | Scene | Shot | On screen |
|---|---|---|---|
| 0–0.72 s | Hook | His gloved hands on the bat, close, against a blurred stadium | |
| 0.72–1.36 s | Hook | Over his shoulder: the pitcher, a 95 mph fastball | |
| 1.36–1.72 s | Hook | Low beside the plate: it pops into the mitt | "95 mph" |
| 1.72–2.72 s | Hook | From center field: the same pitcher, a changeup; he swings early and misses | "85 mph · changeup"; "Swings early" |
| 2.72–4.0 s | Hook | Top/bottom, frozen at the same moment of the same swing: on time for the fastball, the changeup still coming | **THIS PITCH MAKES 95 MPH LOOK EVEN FASTER.** |
| 4.0–7.3 s | Deception | Side by side, straight behind the pitcher, slowed at the release; arm-path trails | **SAME ARM ACTION.**; "Same arm path" |
| 7.3–11.0 s | Deception | Top/bottom, the throwing arm at the release (slowed, frozen); then each ball leaves at its speed | "Same release"; **DIFFERENT SPEED.**; "95 mph" / "85 mph"; the note |
| 11.0–17.2 s | Speed difference | Top/bottom, the race camera, slowed; frozen when the fastball reaches the plate | Speed bars (0.40 s / 0.44 s); "Already there" / "Still about 5 ft away"; **THE CHANGEUP ARRIVES LATER.** |
| 17.2–20.0 s | Speed difference | Top/bottom, close beside the plate: the same swing barrels the fastball and misses the changeup | "On time: barreled" / "Same swing: too early" |
| 20.0–22.15 s | Hitter's problem | Close on the hitter as he tracks the changeup in | "Tracking a fastball-looking pitch" |
| 22.15–27.2 s | Hitter's problem | Over the umpire, slowed; frozen as the bat reaches the zone; the ball crosses after it | **THE HITTER SWINGS TOO EARLY.**; "Bat: already in the zone"; "Ball: still coming"; "Crosses after the bat" |
| 27.2–29.0 s | Hitter's problem | Beside the plate, slowed, with the bat path | |
| 29.0–31.5 s | Payoff | Over his shoulder, then from center field: an 84 mph changeup; fooled, way out in front | "84 mph · changeup"; "Way out in front" |
| 31.5–33.3 s | Payoff | Close on the mitt, slowed: the ball arrives | **IT'S NOT ABOUT POWER. IT'S ABOUT TIMING.** |
| 33.3–36.0 s | Payoff | Wide over the stadium; Baseball Decoded | |
