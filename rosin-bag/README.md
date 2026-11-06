# "Why pitchers use the rosin bag"

A 38.6 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: what the rosin bag is, why pitchers use it, and where the line is between legal rosin and illegal foreign substances.

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.4×). The text is in `transcript.txt`.
  - Shots, word-by-word captions, pins and titles are keyed to its words. The opening question is covered by the big hook title instead of captions.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Sound:** a `make_bed` bed (style "pulse") ducked up to 7 dB under the voice, plus whooshes, the cloth squeeze of the bag, footsteps on the mound, glove pops and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **One pitcher throughout:** white home uniform and navy undershirt, the same as the other Baseball Decoded videos.
- **New close-up kit** (`assets/field.js`):
  - **The hand:** a palm with a jointed thumb and four fingers, three bones each. Fingers are solved at load to wrap the ball or the bag: each joint, from the knuckle out, bends until it touches the surface. The thumb is aimed at its contact point with the pad facing the object.
  - **The baseball:** leather texture, the figure-eight seam and 108 double red stitches. In flight it spins about the spin axis from the physics, at the pitch's rpm.
  - **The rosin bag:** a sewn cloth pillow with "ROSIN" printed on it. It squeezes and puffs, lies on the back slope of the mound behind the rubber, and sits on a powdery patch with pebbles.
  - **Rosin dust:** puffs from the bag, dust falling from rubbed fingertips, motes in the light, and a powder layer on the fingertips.
  - **Sweat beads:** glossy beads and a wet sheen on the fingertips that grow, then dry as the rosin goes on.
  - **The sunscreen bottle:** a plain, unbranded bottle for the illegal comparison, with a glossy paste on the fingertips.
  - **The background:** an out-of-focus stadium behind the close-ups, a key, rim and fill light for them, and a soft yellow outline on the fingers that matter for each grip.

```bash
python3 tools/physics.py                                       # fastball, curveball, changeup and the last pitch -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/rosin-bag.mp4 --video-bitrate 16M
```

## The pitches (`tools/physics.py`)

All four are right-handed, from the stretch, released 6.0 ft high and 1.9 ft to the arm side. Each flight uses gravity, drag (Cd 0.35) and spin lift.

| | Speed | Spin | Crosses the front of the plate |
|---|---|---|---|
| Four-seam fastball | 94 mph | 2,300 rpm backspin | (+0.25, 2.70) ft after 0.401 s |
| Curveball | 79 mph | 2,600 rpm topspin, a little glove side | (+0.15, 1.70) ft after 0.478 s |
| Changeup | 85 mph | 1,750 rpm, arm-side fade | (−0.35, 1.90) ft after 0.443 s |
| The last pitch | 95 mph | 2,350 rpm backspin | (+0.40, 2.60) ft after 0.397 s |

## Accuracy notes

- **What rosin does:**
  - Rosin is a powder made from pine-tree resin, in a cloth bag.
  - On the fingers it dries sweat and adds a little tack, so the grip feels more consistent.
  - The video says exactly that: "Rosin powder dries them and adds a little tack"; "Dry fingertips: the grip feels the same from pitch to pitch."
- **What it doesn't do:**
  - An on-screen note says "Rosin doesn't add speed or movement. It helps every grip feel the same."
  - Speed and movement come from the grip, finger pressure and release, shown with each pitch.
- **The rules:**
  - Rosin itself is legal. The bag sits on the ground behind the pitcher's rubber, as shown.
  - MLB prohibits applying foreign substances to the ball or hands, and that includes mixing rosin with something like sunscreen to make it stickier.
  - The split screen shows "Legal: the rosin bag" against "Illegal: rosin + sunscreen", with the note "MLB allows the rosin bag. Mixing rosin with a foreign substance like sunscreen to improve grip is not allowed."
- **Grips are simplified but standard:**
  - Four-seam fastball: index and middle across the seams, thumb under the ball.
  - Curveball: middle finger along a seam; the fingers pull down over the front for topspin.
  - Changeup: the ball deeper in the hand, thumb and index forming a circle.
- **Pitching mechanics:** a leg kick from the stretch. Each release is slowed and the ball leaves the fingers onto its simulated path.

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–3.5 s | "Have you ever noticed that little white bag…" | Low behind the bag on the mound, the rubber beyond; his cleats walk in | **WHAT IS THIS LITTLE WHITE BAG?** |
| 3.5–6.8 s | "That's a rosin bag, and it's actually more important than you might think." | He crouches and picks it up on "rosin bag"; a quick zoom; he squeezes it (a puff of dust) | "Rosin bag" |
| 6.8–10.9 s | "Pitchers use rosin to help manage moisture on their hands and improve their grip…" | He rubs the rosin into his fingertips; the grip on the seams, the key fingers outlined | "Rosin on the fingertips", "Grip" |
| 10.9–14.5 s | "When your hands get sweaty, gripping a baseball consistently becomes much harder." | On the rubber with the ball; close on his fingers: sweat beads, and on "consistently" the ball shifts | **MOISTURE MAKES GRIP HARDER**; "Sweat on the fingertips", "The ball shifts in his fingers" |
| 14.5–18.3 s | "Rosin helps absorb moisture, giving pitchers a more reliable feel for the ball." | Tossing the bag in his palm, the dust coats his fingertips and the sweat dries; he rubs it in; grips the ball again, dry | **BETTER MOISTURE CONTROL. MORE CONSISTENT GRIP.**; the two-step card |
| 18.3–23.9 s | "And that matters because even a small difference in grip can affect how a pitcher controls a pitch." | Fastball, curveball, changeup: the grip close, the release slowed, the ball to the catcher | **EVERY FINGER MATTERS**; the pitch cards; "Rosin doesn't add speed or movement…" |
| 23.9–30.6 s | "But here's something important: rosin isn't allowed to be mixed with foreign substances like sunscreen…" | The bag behind the rubber; split: rosin-dusted fingers (legal) vs. a rosin and sunscreen paste with the bottle (illegal) | **LEGAL ROSIN. ILLEGAL FOREIGN SUBSTANCES.**; ✓ / ✕; the rules note |
| 30.6–36.1 s | "So next time you see a pitcher reach for that little white bag, remember… It's part of controlling the baseball." | He reaches for the bag on "reach"; from behind the mound, a 95 mph fastball released on "controlling" | |
| 36.1–38.6 s | (end) | The bag on the mound, dust in the light; the end card | **NOW YOU KNOW.**, then Baseball Decoded |
