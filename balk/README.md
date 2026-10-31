# "Five ways to balk"

A 35.9 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: five different ways a balk can be called, including the catcher balk, and the penalty.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `hit-and-run`, `infield-fly` and `lefty`. The pickoff motion is adapted from `lefty`.
- **New in this project:**
  - the umpire's balk call, standing and pointing at the pitcher
  - a delivery that starts and stops
  - a set position with no stop
  - a pickoff whose stride goes toward home, with flat arrows for his step and the line to first
  - a ball that drops off the pitcher's hand on the rubber (falls, bounces, rolls down the mound)
  - a pitched intentional walk: the catcher stands with the glove out wide and steps out of the catcher's box before the release, in slow motion with a freeze
  - the catcher's box lit up, yellow then red
- **Voiceover:** your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×); the text is in `transcript.txt`. Shots, word-by-word captions, number cards, pins and "BALK" stamps are keyed to its words.
- **Titles:** "Here are five different ways a balk can be called" is a big title instead of captions.
- **Music:** a `make_bed` bed (style "drive"), ducked up to 7 dB under the voice.
- **Effects:** whooshes, glove pops, the dropped ball's thud, and a hit on each call.
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.

```bash
python3 tools/physics.py                                       # the fastball and the intentional-ball pitch -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav)
npx --yes hyperframes@0.8.154 render . -o renders/balk.mp4 --video-bitrate 16M
```

## The rules as shown (Official Baseball Rules)

**The setup:** a right-hander in the set position (left shoulder to home, facing the third-base side) with a runner on first.

1. **Starts, then stops** (6.02(a)(1)): the leg starts up and comes back down without a pitch.
2. **No complete stop** (6.02(a)(13)): his hands come together and he goes straight into the delivery with no pause.
3. **No step toward first** (6.02(a)(3)): he throws to first while his stride goes toward home. A white dashed arrow shows the direct line to first that the step has to take.
4. **Drops the ball on the rubber** (6.02(a)(11)): the ball slips out of his hand while his foot is on the rubber.
5. **The catcher balk** (5.02(a)): on an intentional walk that's pitched, the catcher has to keep both feet in the catcher's box until the ball leaves the pitcher's hand; leaving early is a balk.
   - The script states this generally; the screen adds the "pitched intentional walk" condition and cites the rule.
   - Today most intentional walks are signaled from the dugout without pitches, so this comes up only when a team throws them.

**The penalty:** runners advance one base; shown with the runner on first awarded second.
- A note says that with the bases empty, an illegal pitch is called a ball instead (6.02(b)).

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–2.6 s | "A balk isn't always caused by the pitcher making a mistake." | Behind the umpire as he stands and points at the pitcher | **BALK!** |
| 2.6–4.8 s | "Here are five different ways a balk can be called." | High over the infield, runner on first | **5 WAYS A BALK CAN BE CALLED** |
| 4.8–8.1 s | #1 | Third-base side: the leg starts up on "starts", stops on "stops" | card 1, "Stops", BALK |
| 8.1–12.0 s | #2 | Hands together on "set", no pause, the pitch | card 2, "Hands together", "No pause", BALK |
| 12.0–15.6 s | #3 | Behind the mound: the throw to first; his step and the line to first | card 3, "His step", "Toward first", BALK |
| 15.6–18.6 s | #4 | Low at the mound: the ball drops on "drops"; the rubber lights up on "touching" | card 4, "Foot on the rubber", BALK |
| 18.6–21.9 s | #5 / "Yes, the catcher can actually cause a balk." | High behind home: the catcher standing for an intentional walk; the box lights up | card 5, "Catcher", "Catcher's box", "Pitched intentional walk: both feet in the box" |
| 21.9–26.1 s | "If the catcher steps outside the catcher's box…" | Behind home, slow motion: he steps out on "steps"; freeze on the release ("releases"); the box turns red | "Out before the release", rule note, BALK |
| 26.1–32.0 s | "…requires runners on base… runners advance one base." | Beyond first: the runner lights up on "runners", is awarded second on "advance" | "Runners on base", **+1 BASE**, bases-empty note |
| 32.0–35.9 s | "Baseball has some rules that even experienced fans don't know." | High over the infield | the five, as a list |
