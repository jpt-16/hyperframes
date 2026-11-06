# "From finger signs to PitchCom"

A 49.9 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: how catchers called pitches with hidden finger signs, how teams protected them, and how PitchCom changed that in MLB.

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.65×). The text is in `transcript.txt`.
  - Shots, word-by-word captions, chips and titles are keyed to its words. The opening line is covered by the big hook title instead of captions.
  - `CUES.md` lists when each line starts, for a read of your own over `assets/mix-novo.wav`.
- **Sound:**
  - Music: a `make_bed` bed (style "pulse"), ducked up to 7 dB under the voice.
  - Effects: soft ticks as each sign flashes, a keypad chirp, whooshes, a glove pop and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **Look:**
  - The hand-signal era (3.3–33.8 s, and the left column of the then/now comparison) is graded warm, like old film, with a soft tint, grain, a vignette and a "The hand-signal era" tag.
  - The PitchCom era is clean and cool, with cyan graphics.
  - The same catcher, pitcher and runner throughout.
- **Built on `rosin-bag`'s close-up kit:**
  - **The hand:** the same jointed hand, now the catcher's right hand. It is placed at the end of his forearm between his thighs, back of the hand to the pitcher, fingers down; finger counts 1–4 flash out of a fist.
  - **The keypad:** a PitchCom-style wrist keypad on his glove-hand forearm (FB, CB, SL, CH and location buttons). The index finger presses a button, which lights up.
  - **The receiver:** in the pitcher's cap band, shown by an X-ray of the cap, with pulse rings.
  - **The signal:** pulses along an arc from the keypad to the cap.
  - **New views:** the runner's line of sight, a long lens from the pitcher's eye and one from the runner's, three-pane and two-column splits, and a ball to the catcher's glove.

```bash
python3 tools/physics.py                                       # the final 95 mph fastball (and others) -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/catcher-signs.mp4 --video-bitrate 16M
```

## Accuracy notes

- **Sign systems varied by team:**
  - "1 = Fastball, 2 = Curveball, 3 = Slider" appears with the note "Example only: every team set its own signs."
  - The three sequence systems (1st, 2nd or 3rd sign live), the indicator and the change-by-inning card are each labelled as examples.
- **PitchCom:**
  - On screen: "Introduced in MLB: 2022", and "Approved for MLB's 2022 regular season. The call plays as a voice in the pitcher's ear."
  - The keypad is a generic stand-in with no brand marks. It sits on the catcher's wrist, and the receiver sits in the cap band.
- **Hand signs haven't disappeared:**
  - The script's last lines ("No more complicated finger sequences… replaced by a few buttons") describe MLB.
  - During them the screen says "In MLB. Hand signs are still used across baseball, and as a backup."
- **Stealing signs:** the runner at second is shown seeing the signs, as the script says. The video doesn't claim every team stole signs.

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–3.3 s | "Before PitchCom, calling one pitch could involve an entire secret code." | From low between the catcher's legs, rising to his hand flashing signs; a long lens on the pitcher looking in, who nods | **ONE PITCH. A SECRET CODE.** |
| 3.3–7.5 s | "For over a century, catchers communicated with pitchers using hand signals hidden between their legs." | The film grade begins; the pitcher's-eye long lens on the catcher; close on the hand between his thighs | "The hand-signal era" |
| 7.5–11.3 s | "One finger might mean a fastball, two… three…" | Close on the hand: 1, 2 and 3 fingers on the words | 1 = FASTBALL, 2 = CURVEBALL, 3 = SLIDER; "Example only…" |
| 11.3–17.4 s | "But there was a problem. The opposing team could sometimes steal those signs…" | Behind the runner at second, the catcher far beyond; the runner in profile with his line of sight; the runner's long-lens view of the fingers | "Runner at second", "He can see the catcher's fingers", "Runner's view" |
| 17.4–19.5 s | "So teams developed different systems to hide their calls." | The hand flashing a fast sequence | **CHANGE THE SEQUENCE**; the sign chips |
| 19.5–24.4 s | "…where only the first, second, or third sign actually mattered." | Three panes, the same 2-1-3 sequence; each lights its live sign on "first", "second" and "third" | System A/B/C labels; → Curveball / Fastball / Slider; "Example systems…" |
| 24.4–28.9 s | "Other teams used an indicator sign, or even changed the system depending on the inning or number of outs." | The hand: 1-3-2-4, the 3 is the indicator, the 2 is live; the pitcher's-eye view | **USE AN INDICATOR**; the inning card |
| 28.9–33.3 s | "The goal was simple: make the signs look random…" | The runner, puzzled, with a "?"; the pitcher nods: "Got it" | **KEEP THE OPPONENT GUESSING** |
| 33.3–41.3 s | "Then came PitchCom. Introduced in MLB in 2022… a receiver in the pitcher's cap." | Into the fingers, a white flash, the keypad; the finger presses SL on "press"; from high behind home, the signal arcs to the mound; the cap X-ray, the receiver pulsing | **INTRODUCING PITCHCOM**; "2022"; "Wrist keypad", "Receiver in the cap", "In his ear: 'Slider… away'" |
| 41.3–45.5 s | "No more complicated finger sequences. No more worrying about a runner at second…" | Then (warm) and Now (cool) columns: the signs and the watching runner vs. one button, the signal and the pitcher set at once | THEN: SECRET HAND SIGNALS / NOW: ELECTRONIC COMMUNICATION; "In MLB. Hand signs are still used…" |
| 45.5–49.9 s | "A century of hand signals, replaced by a few buttons." | A 95 mph fastball from behind the mound; the catch in the glove; the end card | **A CENTURY OF SIGNALS. A NEW WAY TO COMMUNICATE.**, then Baseball Decoded |
