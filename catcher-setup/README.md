# "Why does catcher positioning change with the hitter?"

A 43.5 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It shows how the catcher and the plate umpire set up differently for right- and left-handed hitters, and how the catcher sets up for the pitch that's called.

- **No voiceover**, per the brief. `CUES.md` lists each scene's start and end so you can record your own narration over it.
- **Music:** a `make_bed` bed (style "glow").
- **Effects:** whooshes, glove pops, a freeze hit, and stadium ambience.
- **Mix:** mastered to −20 LUFS so there is room for a voice on top. The same mix is in `assets/mix.wav`.
- **Framework:** the same three.js field, players, umpires and HyperFrames workflow as `checked-swing` and `pitch-timing`. The catcher and the umpire are the same models in every shot.
- **New in this project:**
  - the catcher's setup shift to each target, solved to match the glove height
  - the umpire switching slots for a left-handed hitter
  - the umpire's sightlines to the zone corners
  - two marks per pitch: where it crossed the zone (yellow) and where it was caught (cyan), joined by a line, so the two are never confused
  - the throw back to the pitcher

```bash
python3 tools/physics.py   # the pitches (93 mph) to each target -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/catcher-setup.mp4 --video-bitrate 16M
```

## Accuracy notes

- **Catchers don't always set up inside.** Every setup in the video follows the pitch that's called: inside, outside or on the edge. The on-screen note says the setup depends on "the hitter and the situation" (count, runners, the pitch).
- **The umpire's slot:**
  - The plate umpire normally works the slot between the catcher and the batter, on the batter's side.
  - With a left-handed hitter he moves to the other slot, as shown.
  - The sightlines only show what he looks at. The video never suggests he calls a pitch because his view is blocked.
- **The call is made where the pitch crosses the zone, not where it's caught.**
  - The yellow mark is where the ball crossed the zone; the cyan ring is the glove.
  - For clarity the yellow mark sits at the front of the plate. By rule, the strike zone is the whole area over home plate.
- **Receiving:**
  - The video shows a quiet glove that catches the ball cleanly and holds it ("Good receivers catch it cleanly and hold it").
  - There's no claim that framing changes calls.
- **Not covered:** the automated ball-strike challenge system isn't mentioned.

## Shots

| Time | Shot | On screen |
|---|---|---|
| 0–5 s | High behind home: a right-handed hitter steps in, the catcher and umpire set; then a left-handed hitter in the other box; freeze | **WHY DOES CATCHER POSITIONING CHANGE WITH THE HITTER?** |
| 5–7.6 s | From above: batter, catcher, umpire in the slot (rings) | **THE HITTER CHANGES THE VIEW** |
| 7.6–14 s | Up behind the umpire, with his sightlines: an inside pitch, then an outside pitch | "Crossed the zone" / "Caught here"; INSIDE / OUTSIDE PITCH |
| 14–17.2 s | From above: a left-handed hitter steps in, and the umpire moves to the other slot | **OPPOSITE SIDE. DIFFERENT ANGLE.** |
| 17.2–23 s | Split screen: the same outside pitch to a right-handed hitter (top) and a left-handed hitter (bottom) | |
| 23–33 s | 1 Inside (umpire's view), 2 Outside (from in front), 3 On the edge (umpire's view, slow motion) | **POSITIONING + PRESENTATION**; "He sets up for the pitch that's called…"; "The call is where it crosses the zone, not where it's caught…" |
| 33–38.6 s | From the side: an edge pitch to a right-handed hitter, then to a left-handed hitter | "Quiet glove" |
| 38.6–41.3 s | Side close-up: the catcher stands and throws the ball back | **ELITE CATCHERS READ THE ENTIRE FIELD.** |
| 41.3–43.5 s | Baseball Decoded end card | |
