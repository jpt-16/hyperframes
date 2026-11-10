# "Pitch tipping": what if the hitter knew the pitch before it was thrown?

A 52.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: how pitchers tip pitches, how teams find the pattern, how the information gets to the hitter, and what it's worth.

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.6×). The text is in `transcript.txt`.
  - Shots, freezes, rings, signs, word-by-word captions and titles are keyed to its words.
  - The opening question is covered by the hook title, and the last line ("It's knowing which pitch is coming.") is the closing title instead of captions.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Slider, as in the script:** the breaking pitch in every example, in the pitch log and in the payoff is a slider (86 mph, sweeping away from a right-handed hitter), compared with a fastball.
- **Layout:** captions at the top; scene titles in a band under them (at the seam in the top/bottom splits); in the splits the top pane is framed low so the captions don't cover the glove.
- **Sound:** a `make_bed` bed (style "pulse") ducked up to 7 dB under the voice, whooshes, impacts on the titles, soft ticks as the catcher's signs flash, glove pops, the bat crack (low and long, in slow motion) and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **One cast throughout:** the same pitcher (white home uniform), batter (gray road uniform, red helmet, black batting gloves), catcher and umpire, on the same field as the other Baseball Decoded videos.
- **New in this project:**
  - **The tells:** built into the pitcher's set and delivery.
    - Where his hands come together: at the belt or at the chest.
    - The glove flaring while his hand works the grip inside it.
    - How long he holds the set.
    - A yellow ring finds the glove in any camera.
  - **The scouting room:** a second 3D scene with a hitting coach, two hitters at a table, a laptop and a video wall.
    - The wall plays two live renders of the same pitcher on a loop: the clip before the fastball above the one before the slider.
    - Beside them is a pitch log whose matching rows light up one by one.
  - **The signs:**
    - The catcher's jointed hand flashes finger signs between his thighs, seen through a runner's-view lens.
    - The runner at second touches his helmet.
    - Another team's coach touches his cap and swipes his arm from the dugout rail.
  - **The close-up of the ball in the pitcher's hand:** his fingers are solved at load to wrap a stitched baseball in a four-seam grip.

```bash
python3 tools/physics.py                                       # the fastball, the slider, the batted ball -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/tipping.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## The pitches (`tools/physics.py`)

| | Speed | Spin | Crosses the front of the plate |
|---|---|---|---|
| Fastball | 94 mph | 2,300 rpm backspin | (+0.20, 2.80) ft after 0.401 s |
| Slider | 86 mph | 2,500 rpm, glove-side sweep | (+0.35, 2.20) ft after 0.438 s |

The payoff: the slider is barreled for a 101 mph line drive at 15° into right-center, landing about 300 ft out.

## Accuracy notes

- **The tells are hypothetical:**
  - All three are made-up examples for this one pitcher, labeled "Before the fastball" and "Before the slider".
  - An on-screen note says: "Hypothetical examples for one pitcher. Real tells vary, and no single move always means one pitch."
  - Nothing says a glove position always means a particular pitch.
- **The examples cover what the brief lists:**
  - **Glove position:** hands at the belt vs. at the chest.
  - **Hand movement:** the glove flares while he changes his grip.
  - **Delivery timing:** 0.9 s vs. 1.8 s in the set, with timer bars.
- **Patterns, not single clips:**
  - The scouting room compares two clips, then a pitch log of eight pitches. The pin reads "Hands at the chest → slider, every time in this log".
  - The note reads: "Teams look for a move that repeats, not one clip."
- **Reading signs:**
  - The runner at second reads the catcher's sequence. The pin reads "Second sign is live: 2 = slider (this example)".
  - He relays it with a prearranged signal (a hand to the helmet), and the batter sees it.
- **Systems vary:**
  - A different team's coach uses a different signal from the dugout.
  - The note reads: "Every team sets its own signals, and changes them."
- **No electronics:** the note says "Reading signs by sight is part of the game. Using electronics to steal them is against MLB rules." No device appears in the relay.
- **The payoff** shows the batter spotting the tell (the ring and "Hands at the chest: slider coming"), then waiting on the slider and barreling it.

## Shots

| Script | Shot | On screen |
|---|---|---|
| "Have you ever wondered how a hitter can know what pitch is coming…" | On the mound he looks in and comes set; over the batter's shoulder; the delivery, frozen before release; the camera pushes into the glove | **WHAT IF THE HITTER KNEW THE PITCH BEFORE IT WAS THROWN?**; "The glove" |
| "It's called tipping pitches… without even realizing it." | The pitch goes on, the pitcher none the wiser | **TIPPING PITCHES** |
| "…a slightly different glove position, hand movement, or setup…" | Top/bottom: hands at the belt before the fastball, at the chest before the slider (freeze on "glove"); then close: the glove flares as he changes his grip (freeze) | **GLOVE POSITION**, **HAND MOVEMENT**; the hypothetical note |
| "…like a change in delivery timing…" | Full delivery, each: 0.9 s in the set before the fastball, 1.8 s before the slider | **DELIVERY TIMING**; timer bars |
| "…or how they handle the ball." | The ball in his hand, close | "The grip, hidden until the last moment" |
| "But here's where it gets interesting. Teams study video and look for patterns." | The scouting room | **STUDY THE VIDEO** |
| "If they notice the pitcher consistently doing something different before throwing a slider compared to a fastball…" | The video wall: both clips, rings on the glove | **FIND THE PATTERN**; "Before the fastball…" / "Before the slider…" |
| "…they can start recognizing the tell." | The pitch log lights up the slider rows | "Hands at the chest → slider, every time in this log" |
| "And once they figure it out, that information can spread throughout the team." | The hitters: one leans in and points, the other nods | "There it is"; "Teams look for a move that repeats, not one clip." |
| "A runner at second base might recognize the catcher's signs and relay information to the hitter." | Behind the runner; the runner's view of the signs; hand to the helmet; over the batter's shoulder, he gets it | **RECOGNIZE IT**, **RELAY IT**; the pins |
| "Coaches and teammates can also communicate through prearranged signals." | Another team's coach on the dugout rail: cap, then arm | "Another team: a signal from the dugout"; the note on signals and electronics |
| "The challenge is making sure the pitcher doesn't realize they've been figured out." | The batter's eyes: the pitcher comes set, hands at the chest | **USE THE ADVANTAGE**; "Hands at the chest: slider coming" |
| "Because if a hitter knows what's coming, even a fraction of a second earlier, it can completely change the at-bat." | Slow motion: contact on "earlier"; the line drive | **KNOWING THE PITCH CHANGES EVERYTHING** |
| "And that's why pitchers work so hard to make every pitch look exactly the same." | He walks back up the mound, looking in | **THE BEST PITCHERS DON'T GIVE ANYTHING AWAY.** |
| "In baseball, sometimes the biggest advantage isn't having a better pitch." | The ball in his hand, close | |
| "It's knowing which pitch is coming." | (the same) | **IT'S KNOWING WHICH PITCH IS COMING.**, then the Baseball Decoded end card |
