# "Why pitchers use the rosin bag"

A 44.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: what the rosin bag is, why pitchers use it, and where the line is between legal rosin and illegal foreign substances.

- **No voiceover**, per the brief. `CUES.md` lists each scene's start and end so you can record narration over it.
- **Sound:** a `make_bed` bed (style "pulse"), whooshes, the cloth squeeze of the bag, footsteps on the mound, glove pops and stadium ambience.
- **Mix:** mastered to −20 LUFS so there is room for a voice on top. The same mix is in `assets/mix.wav`.
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
python3 tools/physics.py   # fastball, curveball, changeup and the last pitch -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
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

| Time | Shot | On screen |
|---|---|---|
| 0–5 s | Low behind the bag: his cleats step in; he crouches and picks it up; a quick zoom on his hand; he squeezes it (a puff of dust), drops it and rubs his fingertips | **WHAT IS THIS LITTLE WHITE BAG?**; "Rosin bag" |
| 5–13 s | On the rubber, the ball out in front; close on his fingers on the seams; sweat beads up; the ball shifts in his fingers; he resets his grip | **MOISTURE MAKES GRIP HARDER**; "Sweat on the fingertips", "The ball shifts in his fingers", "He has to reset his grip" |
| 13–23 s | Back to the bag; tossing it in his palm, the dust coats his fingertips and the sweat dries; he rubs it in; grips the seams again, dry | **BETTER MOISTURE CONTROL. MORE CONSISTENT GRIP.**; the two-step card; "Dry fingertips: the grip feels the same from pitch to pitch." |
| 23–33 s | For each of fastball, curveball and changeup: the grip close, with the key fingers outlined; the release, slowed and tracked; the ball to the catcher | **EVERY FINGER MATTERS**; the grip and release labels; "Rosin doesn't add speed or movement…" |
| 33–39 s | The bag behind the rubber; split screen: rosin-dusted fingers by the bag (legal) vs. fingers with a rosin and sunscreen paste and the bottle (illegal) | **LEGAL ROSIN. ILLEGAL FOREIGN SUBSTANCES.**; ✓ / ✕ labels; the rules note |
| 39–43 s | Behind the pitcher: a 95 mph fastball to the catcher; then the bag on the mound, dust in the light | **NOW YOU KNOW.** |
| 43–44.5 s | Baseball Decoded end card | |
