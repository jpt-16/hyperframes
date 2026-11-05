# "Why does catcher positioning change with the hitter?"

A 40.3 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded. It shows how the catcher and the plate umpire set up differently for right- and left-handed hitters, and how the catcher sets up for the pitch that's called.

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.3×). The text is in `transcript.txt`.
  - Shots, word-by-word captions, pins and titles are keyed to its words. The opening line is covered by the big hook title instead of captions.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Music:** a `make_bed` bed (style "glow"), ducked up to 7 dB under the voice.
- **Effects:** whooshes, glove pops, a freeze hit, and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the same music and effects without the voice.
- **Framework:** the same three.js field, players, umpires and HyperFrames workflow as `checked-swing` and `pitch-timing`. The catcher and the umpire are the same models in every shot.
- **New in this project:**
  - the catcher setting up inside on every pitch, then bringing outside pitches back toward the plate after the catch
  - the umpire switching slots for a left-handed hitter
  - the umpire's sightlines to the corners of the zone
  - two marks for every pitch: where it crossed the zone (yellow) and where it was caught (cyan), joined by a line so the two are never confused
  - the throw back to the pitcher

```bash
python3 tools/physics.py                                       # the pitches (93 mph) to each target -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/catcher-setup.mp4 --video-bitrate 16M
```

## Accuracy notes

- **The inside setup:**
  - At your direction, this catcher sets up on the inside part of the plate (the hitter's side) for every pitch.
  - On a pitch away from him, he catches it and brings the glove back about 3½ inches toward the plate.
  - The video presents this as one approach: "This catcher sets up inside on every pitch… It's one approach: setups vary by catcher and situation." It doesn't claim all catchers always set up inside.
  - Common catching instruction often differs: catchers set up toward the called location, and a glove that travels a long way or visibly drags the ball can make a borderline pitch look like a ball.
- **The umpire's slot:**
  - The plate umpire normally works the slot between the catcher and the batter, on the batter's side.
  - With a left-handed hitter he moves to the other slot, as shown.
  - The sightlines only show what he looks at. Nothing suggests he calls a pitch because his view is blocked.
- **Framing:**
  - The script says that on borderline pitches "good framing can also help the umpire recognize the pitch as a strike".
  - On screen, alongside it: "The call is made where the pitch crosses the zone. Bringing the glove back toward the plate can make an edge pitch look more like a strike."
  - The yellow mark always shows where the ball really crossed, so it stays distinct from where the glove ends up.
- **Where the call is made:**
  - The yellow mark is where the ball crossed the zone; the cyan ring is where the glove ends up.
  - For clarity the yellow mark sits at the front of the plate. By rule, the strike zone is the whole area over home plate.
- **Not covered:** the automated ball-strike challenge system isn't mentioned.

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–5.2 s | "Did you know a catcher's positioning can change…" | High behind home: a right-handed hitter steps in, the catcher and umpire set; on "depending", a left-handed hitter in the other box; freeze on "hitter" | **WHY DOES CATCHER POSITIONING CHANGE WITH THE HITTER?** |
| 5.2–10.6 s | "When a right-handed hitter steps into the box, the umpire and catcher have a particular viewing angle." | From above: he arrives on "box"; the umpire and catcher are labelled as they're named; then up behind the umpire, the sightlines draw and an inside pitch is caught on "angle" | **THE HITTER CHANGES THE VIEW**; "Crossed the zone" / "Caught here" |
| 10.6–14.0 s | "But when a left-handed hitter steps up, that angle changes." | From above: a left-handed hitter steps in; the umpire moves to the other slot on "that angle changes" | **OPPOSITE SIDE. DIFFERENT ANGLE.** |
| 14.0–19.4 s | "The catcher has to adjust to the hitter's position, the pitch location, and the umpire's line of sight." | Split: the same outside pitch to each hitter; then the umpire's view: the catcher sets up inside on "location", catches the outside pitch and brings it back, and the sightlines draw on "umpire's" | "Sets up inside"; "Brought back"; "This catcher sets up inside on every pitch…" |
| 19.4–25.9 s | "Why does this matter? Because catchers want to give the umpire the clearest possible look…" | High behind home; then 1 Inside (umpire's view, caught on "look"), 2 Outside (from in front, caught on "smoothly" and brought back) | **POSITIONING + PRESENTATION** |
| 25.9–31.3 s | "On borderline pitches, good framing can also help…" | 3 On the edge, umpire's view, in slow motion, caught on "recognize" | "Crossed the edge" / "Glove ends over the plate"; the note on where the call is made |
| 31.3–34.8 s | "At the highest level, catching isn't just about stopping the baseball." | From the side: an edge pitch to a right-handed hitter, then to a left-handed hitter | "Brought back" |
| 34.8–38.0 s | "It's about understanding everything happening around home plate." | Side close-up: the catcher stands and throws the ball back | **ELITE CATCHERS READ THE ENTIRE FIELD.** |
| 38.0–40.3 s | (end) | Baseball Decoded end card | |
