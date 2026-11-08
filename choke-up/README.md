# "Is choking up actually worth it?"

A 45.8 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: what choking up does, what it gives a hitter, what it costs, and when hitters use it.

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.45×). The text is in `transcript.txt`.
  - Shots, word-by-word captions, the grip slides and the titles are keyed to its words.
  - The opening question is covered by the big hook title instead of captions. The last two lines ("It's not about swinging harder." / "It's about controlling the barrel.") are the closing titles instead of captions.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Layout:** captions at the top; scene titles in a dark band just under them; pane labels, pins and notes around the batter.
- **Sound:** a `make_bed` bed (style "pulse") ducked up to 7 dB under the voice, bat cracks (lower and longer in slow motion), the hands sliding on the handle, whooshes and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
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
python3 tools/physics.py                                       # the pitches and batted balls -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
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
| "…easier to control…" | 99 mph down the middle | Liner to center |
| "…high velocity…" | 100 mph | Fouled straight back |
| "…consistent contact." | 91 mph | 92 mph grounder up the middle |
| "…better contact…" | 95 mph | 104 mph line drive at 16° into left-center |

## Accuracy notes

- **What choking up is:** moving the hands higher on the handle. Here both hands move 2 in, and the knob shows below the bottom hand.
- **Shorter effective length:** the bar from the bottom hand to the end of the bat gets about 2 in shorter, as labeled ("≈ 2 in shorter").
- **Control, not speed:**
  - The title says "More control".
  - An on-screen note says: "Choking up doesn't automatically add bat speed or guarantee contact. It can make the bat easier to control."
  - The swing is the same speed with either grip.
- **The tradeoff:**
  - The overhead freeze shows the end of the bat reaching less far when choked up.
  - On the pitch away the full grip's extra reach finds the barrel; on the pitch inside the choked-up grip does.
  - The note says: "Neither grip wins every pitch. It depends on the hitter, the pitch and the situation."
- **Who does it:** following the script, a split shows one hitter choking up with two strikes and another choked up on every pitch, then a full grip, unchanged.
- **"Better contact"** is labeled "The goal, not a guarantee."
- **The bottom line:** "Worth it if it helps him make better contact without giving up too much power."

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–2.1 s | "Is choking up on the bat actually worth it?" | He steps into the box | **IS CHOKING UP ACTUALLY WORTH IT?** |
| 2.1–4.4 s | "The answer depends on the hitter and the situation." | Extreme close on the hands: normal grip | "Normal grip: hands at the knob" |
| 4.4–7.1 s | "When a hitter chokes up, they move their hands higher on the handle…" | The hands slide up the handle on "hands higher"; the knob shows | "Hands up the handle" |
| 7.1–8.7 s | "…shortening the effective length of the bat." | The bat alone; the effective-length bar shrinks on "shortening" | **SHORTER EFFECTIVE BAT LENGTH**; "≈ 2 in shorter" |
| 8.7–13.4 s | "This can make the bat feel easier to control… the barrel through the zone…" | 99 mph; the swing in slow motion with its bat path, contact on "barrel" | **MORE CONTROL**; the note on bat speed |
| 13.4–18.7 s | "…facing high velocity, protecting with two strikes, or trying to make consistent contact." | 100 mph fouled back; he chokes up at 0–2; a hard grounder up the middle | **HIGH VELOCITY**, **TWO STRIKES**, **BETTER CONTACT** ("The goal, not a guarantee.") |
| 18.7–22.2 s | "But there's a tradeoff. Choking up reduces some of the leverage and reach…" | Top and bottom, overhead, frozen at contact on a pitch away: the reach of each grip | **MORE CONTROL VS. MORE REACH**; "Barrel on the ball" / "End of the bat" |
| 22.2–24.0 s | "…from holding the bat at the very bottom." | The pitch away, each grip: liner vs. soft grounder | Pitch away |
| 24.0–27.3 s | "So why don't all hitters do it? Because hitting isn't just about making contact." | A pitch inside, each grip: soft grounder vs. liner | Pitch inside; "Neither grip wins every pitch…" |
| 27.3–31.3 s | "It's about finding the right balance between bat speed, control, power, and timing." | The batter in his stance, pushing in | **FIND THE BALANCE**; Bat speed / Control / Power / Timing |
| 31.3–34.3 s | "Some hitters choke up with two strikes. Others do it on nearly every pitch." | Split: one chokes up on "two strikes"; the other is choked up already | Two strikes / Every pitch |
| 34.3–36.5 s | "And some never need to change their grip at all." | The hands, close: full grip | "Full grip, every pitch" |
| 36.5–41.0 s | "The bottom line? Choking up can be worth it if it helps you make better contact without sacrificing too much power." | Behind him: the line drive into left-center, contact on "contact" | **THE BOTTOM LINE**; the note |
| 41.0–43.8 s | "It's not about swinging harder. It's about controlling the barrel." | Low angle, slow motion: the bat finishes its swing | **IT'S NOT ABOUT SWINGING HARDER.** / **IT'S ABOUT CONTROLLING THE BARREL.** |
| 43.8–45.8 s | (end) | Baseball Decoded end card | |
