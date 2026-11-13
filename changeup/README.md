# "This pitch makes 95 mph look even faster": the changeup

A 36.0 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. A changeup comes out of the same delivery as a 95 mph fastball, arrives later, and the hitter's swing gets there first.

- **Framework:** the same three.js field, players, bat, gloved hands, split-screen renderer and HyperFrames workflow as `count`, `choke-up` and the other Baseball Decoded videos.
- **Voiceover:**
  - Your script ("Why changeups are so hard to hit"), voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×). The text is in `transcript.txt`.
  - Word-by-word captions at the top. "95 mph" is spoken as words, and the captions keep the numerals.
  - The deception starts at 3.1 s, about a second before 0:04, because the hook line takes under 3 s to say. The other scenes start within 0.1 s of their times in your script. The video is 36.0 s.
  - Shots and graphics are keyed to the words:
    - The release, side by side, on "hand".
    - The close release on "release"; "Different speed." on "difference".
    - The fastball reaches the plate on "sooner", with the changeup still coming; it arrives on "actually does".
    - The freeze, with the bat in the zone and the ball still coming, on "difference" in "recognize the difference".
    - The ball reaches the mitt on "time" in "the wrong time".
  - The hook line builds as captions, then lands as the title on the split screen.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Layout:** captions at the top; titles in a band at the seam of the splits (or at the bottom); pane labels at the top of each pane.
- **One cast throughout:** the same right-handed pitcher (white home uniform) and right-handed hitter (gray road uniform, red helmet, black batting gloves), with the same catcher and umpire, on the same field.
- **Sound:** a `make_bed` bed (style "pulse") ducked up to 7 dB under the voice, whooshes on the cuts, the releases and the swings, glove pops, the bat crack on the barreled fastball, impacts on the titles, and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **New in this project:**
  - **One delivery for both pitches:** the pitcher's animation is literally the same function of time for the fastball and the changeup. Only the ball's flight differs.
  - **The arm path:** a trail of where his throwing hand has been over the last half second, cyan for the fastball and orange for the changeup. The two arcs match.
  - **An early swing:** the hitter's swing can be timed and placed for one pitch (the fastball) while the ball is another (the changeup). He can also lunge further out in front when he's completely fooled.
  - **The race camera:** a dolly beside the pitch path keeps pace with the fastball and stops at the plate. Both panes use the same camera move, so the changeup falls behind in its frame.
  - **Speed bars:** each pitch's bar fills as the ball travels, and its time to the plate (0.40 s vs. 0.44 s) appears when it gets there.
  - **The catcher's mitt:** the catcher's arm is solved once per pitch, so the mitt is exactly where each pitch ends (he sets up on the spot). The ball goes into the mitt without jumping.
  - **The radar reading** on the center-field board: "95 · FASTBALL", "85 · CHANGEUP", "84 · CHANGEUP".

```bash
python3 tools/physics.py                                       # the fastball, the changeups, the line drive -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
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

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–0.46 s | "This pitch…" | His gloved hands on the bat, close, against a blurred stadium | |
| 0.46–1.17 s | "…makes a 95 mph…" | Over his shoulder: the pitcher, a 95 mph fastball | |
| 1.17–1.51 s | "…fastball…" | Low beside the plate: it pops into the mitt | "95 mph" |
| 1.51–2.35 s | "…look even…" | From center field: the same pitcher, a changeup; he swings early and misses | "85 mph · changeup"; "Swings early" |
| 2.35–3.12 s | "…faster." | Top/bottom, frozen at the same moment of the same swing: on time for the fastball, the changeup still coming | **THIS PITCH MAKES 95 MPH LOOK EVEN FASTER.** |
| 3.12–7.13 s | "A changeup is designed to look almost identical to a fastball coming out of the pitcher's hand." | Side by side, straight behind the pitcher, slowed; the release on "hand"; arm-path trails | "Same arm path" |
| 7.13–10.92 s | "Same arm action. Similar release. But there's one major difference: the speed." | Top/bottom, the throwing arm, slowed; the release on "release"; each ball leaves at its own speed | **SAME ARM ACTION.**, then **DIFFERENT SPEED.** on "difference"; "Same release"; the speeds on "speed" |
| 10.92–15.31 s | "Because the changeup travels slower, the hitter's brain expects the ball to arrive sooner than it actually does." | Top/bottom, the race camera, slowed: the fastball reaches the plate on "sooner" (frozen); the changeup arrives on "actually does" | Speed bars (0.40 s / 0.44 s); "Already there" / "Still about 5 ft away"; **THE CHANGEUP ARRIVES LATER.** |
| 15.31–19.92 s | "The hitter commits to the swing too early, and the ball is still traveling toward the plate." | Top/bottom, close beside the plate, slowed: the same swing barrels the fastball and misses the changeup | "On time: barreled" / "Same swing: too early" |
| 19.92–23.0 s | "The best changeups disguise themselves until the last possible moment." | Close on the hitter as a changeup comes in; he swings through it | "It looks like a fastball…" |
| 23.0–26.75 s | "If a hitter can't recognize the difference early enough, their timing is completely disrupted." | Over the umpire: frozen on "difference" as the bat reaches the zone; the ball crosses after it | **THE HITTER SWINGS TOO EARLY.**; "Bat: already in the zone"; "Ball: still coming"; "Crosses after the bat" |
| 26.75–28.92 s | (pause) | Beside the plate, slowed, with the bat path | |
| 28.92–31.58 s | "That's the secret of the changeup. It doesn't have to overpower a hitter." | Over his shoulder, then from center field, slowed: an 84 mph changeup; fooled, way out in front | "84 mph · changeup"; "Way out in front" |
| 31.58–33.65 s | "It just has to make them swing at the wrong time." | Close on the mitt, slowed: the ball arrives on "time" | |
| 33.47–35.97 s | (end) | Wide over the stadium | **IT'S NOT ABOUT POWER. IT'S ABOUT TIMING.**, then Baseball Decoded at 34.72 s |
