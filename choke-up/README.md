# "Is choking up actually worth it?"

A 50 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: what choking up does, what it gives a hitter, what it costs, and when hitters use it.

- **No voiceover**, per the brief. `CUES.md` lists each scene's start and end so you can record narration over it.
- **Sound:** a `make_bed` bed (style "pulse"), bat cracks (lower and longer in slow motion), the hands sliding on the handle, whooshes and stadium ambience.
- **Mix:** mastered to −20 LUFS so there is room for a voice on top, in `assets/mix.wav`.
- **One batter throughout:** the same model, uniform (gray road jersey, red helmet) and bat in every shot, on the same field, players and workflow as the other Baseball Decoded videos.
- **New in this project:**
  - **The bat:** a 34 in maple bat with a resampled lathe profile (knob, handle, taper, barrel, cupped end). It has a wood-grain texture, a natural handle with pine tar, and a dark barrel.
  - **The hands:** two of the rosin-bag video's jointed hands in black batting gloves with red wrist straps, the left one mirrored.
    - Their fingers are solved at load to wrap the handle: each joint bends until the finger touches it. The thumbs wrap over the top.
    - The hands ride on the bat. Choking up slides both of them 2 in up the handle, so the knob shows below the bottom hand.
  - **Split screens:** each side renders the same batter with a different grip, either side by side or top and bottom.
  - **Graphics on the bat:**
    - the effective-length bars (the whole bat, and from the bottom hand to the end);
    - translucent copies of the bat a few hundredths of a second apart, for the bat path;
    - the arc the end of the bat sweeps at contact, for each grip;
    - a flash at contact.

```bash
python3 tools/physics.py   # the pitches and batted balls -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/choke-up.mp4 --video-bitrate 16M
```

This video was rendered with `tools/render_chunks.js` instead. It renders 3-second chunks that survive a container restart. Join the chunks and add `assets/mix.wav` with ffmpeg's concat demuxer.

## How the swings are placed

Each at-bat is a pitch from `tools/physics.py` (gravity, drag and spin lift), with a contact point: where the ball is at the hitter's contact depth. It is out in front for a pitch inside and deeper for one away.

At load, each swing is placed so the bat's line at contact passes the ball at a set distance from the middle of the hands, with the ball touching the face of the barrel. For each comparison that distance is **the same for both grips**, and the batter stands in the same place. So the only difference between the two sides is where the sweet spot and the end of the bat are:

| | Middle of the hands → sweet spot | Middle of the hands → end of the bat |
|---|---|---|
| Full grip | 2.02 ft | 2.55 ft |
| Choked up (2 in) | 1.85 ft | 2.38 ft |

- **Pitch away:** placed for the full grip's sweet spot. The choked-up bat meets the same ball 2 in toward its end.
- **Pitch inside:** placed for the choked-up sweet spot. The full grip meets the same ball 2 in in toward the hands.

The outcomes are then chosen to match:

| Pitch | Full grip | Choked up |
|---|---|---|
| Away, 94 mph on the outer edge | 98 mph liner to right-center | 74 mph grounder |
| Inside, 95 mph | 76 mph grounder | 99 mph liner to left-center |

The other pitches:

| Scene | Pitch | Result |
|---|---|---|
| Scene 3 | 99 mph down the middle; 99 mph up and in | Liners to center and left-center |
| Scene 5, two strikes | 86 mph slider low and away | 68 mph foul down the right-field line |
| Scene 5, high velocity | 100 mph | Fouled straight back |
| Scene 5, full count | 91 mph | 92 mph grounder up the middle |
| Scene 6 | 95 mph | 104 mph line drive at 16° into left-center |

## Accuracy notes

- **What choking up is:** moving the hands higher on the handle. Here both hands move 2 in, and the knob shows below the bottom hand.
- **Shorter effective length:** the bar from the bottom hand to the end of the bat gets about 2 in shorter, as labeled ("≈ 2 in shorter").
- **Control, not speed:**
  - The titles say "More control" and "Quicker barrel adjustments".
  - An on-screen note says: "Choking up doesn't automatically add bat speed or guarantee contact. It can make the bat easier to control."
  - The swing is the same speed with either grip.
- **The tradeoff:**
  - The overhead freeze shows the end of the bat reaching less far when choked up.
  - On the pitch away the full grip's extra reach finds the barrel; on the pitch inside the choked-up grip does.
  - The note says: "Neither grip wins every pitch. It depends on the hitter, the pitch and the situation."
- **Two strikes:** "Some hitters choke up with two strikes to protect the plate. Many don't."
- **"Better contact"** is labeled "The goal, not a guarantee."

## Shots

| Time | Shot | On screen |
|---|---|---|
| 0–1.5 s | He steps into the box | **IS CHOKING UP ACTUALLY WORTH IT?** |
| 1.5–2.6 s | Extreme close on the hands: normal grip, the bottom hand against the knob | "Normal grip: hands at the knob" |
| 2.6–4.0 s | The hands slide up the handle; the knob shows | "Hands up the handle" |
| 4.0–7.2 s | Split: the same batter, full grip and choked up | Full grip / Choked up |
| 7.2–9.4 s | Split: the hands, close | "Hands at the knob" / "Knob showing" |
| 9.4–12.0 s | The bat alone; the hands slide up and the effective-length bar shrinks | **SHORTER EFFECTIVE BAT LENGTH**; "≈ 2 in shorter" |
| 12.0–13.35 s | Behind the pitcher: 99 mph | 99 MPH |
| 13.35–16.8 s | Slow motion: the controlled swing with its bat path, contact | **MORE CONTROL** |
| 16.8–18.4 s | Replay on the hands and the bat path | "Hands stay compact", "Bat path" |
| 18.4–20.0 s | The contact point, very slow | "Contact point" |
| 20.0–22.0 s | Up and in at 99 mph: the barrel still gets there | **QUICKER BARREL ADJUSTMENTS**; the note on bat speed |
| 22.0–24.6 s | Overhead, frozen at contact on a pitch away: the reach of each grip | **MORE CONTROL VS. MORE REACH**; "Barrel on the ball" / "End of the bat" |
| 24.6–27.6 s | Top and bottom: pitch away (full grip: liner; choked up: soft grounder) | Pitch away |
| 27.6–32.0 s | Top and bottom: pitch inside (full grip: soft grounder; choked up: liner) | Pitch inside; "Neither grip wins every pitch…" |
| 32.0–35.4 s | Two strikes: he chokes up; a slider low and away, fouled off | **TWO STRIKES**; Count 0–2 |
| 35.4–38.7 s | 100 mph; fouled straight back | **HIGH VELOCITY**; 100 MPH |
| 38.7–42.0 s | Full count: he chokes up; a hard grounder up the middle | **BETTER CONTACT**; Count 3–2; "The goal, not a guarantee." |
| 42.0–44.4 s | Behind him: the line drive into left-center | **IT'S NOT ABOUT SWINGING HARDER.** |
| 44.4–47.8 s | Low angle, slow motion: the bat finishes its swing | **IT'S ABOUT CONTROLLING THE BARREL.** |
| 47.8–50.0 s | Baseball Decoded end card | |
