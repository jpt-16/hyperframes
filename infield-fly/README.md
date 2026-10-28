# "The infield fly rule"

A 29.3 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why an infielder can't drop an easy pop-up to turn a cheap double play.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `intentional-walk` and `first-pitch`.
- **New 3D pieces:**
  - a physics pop-up with a short hop
  - the shortstop's decoy (calls for it, pulls the glove away, lets it drop)
  - the plate umpire's infield-fly signal
  - the 6-4-3 relay
  - a top/bottom split screen of the same play without and with the rule
  - rings marking the batter and runners
- **Voiceover:** your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×); the text is in `transcript.txt`. Shots, word-by-word captions, the checklist and the titles are keyed to its words. The hook line, "on purpose" (as **WAIT… HE DID THAT ON PURPOSE?**) and "That's the infield fly rule" land as big titles instead of captions.
- **Music:** a `make_bed` bed (style "drive"), ducked up to 7 dB under the voice. It lands its chord on the closing question.
- **Effects:**
  - the pop-up's bat sound
  - a riser and hit into the freeze
  - a hard hit on the umpire's signal
  - ball-on-dirt thuds (one at half speed)
  - glove pops on the double play
  - whooshes on the cuts and ticks on the conditions
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.

```bash
python3 tools/physics.py                                       # the pitch and the pop-up -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav)
npx --yes hyperframes@0.8.154 render . -o renders/infield-fly.mp4 --video-bitrate 16M
```

## The rule as shown

From MLB's Official Baseball Rules (the definition of an infield fly, and 5.09(a)(12)):
- **What it covers:** a fair fly ball, not a line drive or a bunt, that an infielder can catch with ordinary effort. It applies with runners on 1st and 2nd, or the bases loaded, with fewer than two out.
- **The call:** the umpire declares it while the ball is in the air, as soon as it's apparent. The signal is the right arm straight up.
- **The batter** is out whether or not the ball is caught.
- **The runners:**
  - The ball stays live, and runners may advance at their own risk.
  - The batter is already out, so there is no force: a runner off his base has to be tagged.
  - If the ball is caught, runners must retouch, as on any fly ball.
- **Line drives and bunts** are excluded, and the call is the umpire's judgment. The conditions card says so, so the video doesn't imply every pop-up qualifies.

**The split screen:**
The play is bases loaded with one out, as the script says.
- **Top, "without the rule":** a hypothetical, also shown full-screen on "the defense gets easy outs". The shortstop lets it drop. The batter, who was jogging, and all three runners are forced, so a throw to second and a relay to first make a double play.
- **Bottom, with the rule:** the batter is already out, so there is no force and no double play. Later, the runner on third breaks for home at his own risk and the shortstop looks him back.

**The pop-up physics** (gravity, drag, backspin): 54 mph off the bat at 65°.
- It peaks at 79 ft and comes down on the dirt in front of the shortstop, 104 ft out, after a 4.6 s hang time.
- It takes a short hop that keeps 35% of its vertical speed.
- The pitch is a 93 mph fastball in on a right-handed hitter's hands.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–2.0 s | "This is one of baseball's weirdest rules." | The swing; the pop-up climbing over the infield | The line builds word by word as the hook |
| 2.0–6.4 s | "Bases loaded, less than two outs…lets it drop on purpose." | The same pop-up, continuous: bases loaded from high behind the plate (runners ringed); the shortstop calling for it; he pulls the glove away; freeze with the ball just above the dirt, plus a fast zoom | "Bases loaded · 1 out"; "Shortstop: 'I got it'"; **WAIT… HE DID THAT ON PURPOSE?** |
| 6.4–8.6 s | "The runners take off, the defense gets easy outs…" | Without the rule: the drop, the force at second, the relay to first | WITHOUT THE RULE; "Force out at 2nd"; "And 1st: double play" |
| 8.6–10.5 s | "…except they don't." / "That's the infield fly rule." | The umpire's arm goes straight up (½ speed) | **THAT'S THE INFIELD FLY RULE.**; "called while the ball is still in the air" |
| 10.5–19.2 s | "When a fair fly ball…call the batter out immediately." | The shortstop camped under it, then a diamond board (runners on 1st and 2nd, then a runner on 3rd), then wide as the batter runs | Checklist on the words: FAIR FLY BALL · CATCHABLE WITH ORDINARY EFFORT · RUNNERS ON 1ST + 2ND · …OR BASES LOADED · LESS THAN 2 OUTS; "Not on a line drive or a bunt"; **BATTER: AUTOMATICALLY OUT** with an OUT pin |
| 19.2–23.3 s | "Why? To stop the defense…cheap double play." | Split screen, the same pop-up: without the rule (double play) vs. with it (batter out, no force) | **NO CHEAP DOUBLE PLAY.** on "cheap" |
| 23.3–26.1 s | "And here's the twist: the runners can still advance at their own risk." | ½ speed on the dirt as it falls in; the runner on third breaks for home and the shortstop looks him back | **THE CATCH DOESN'T MATTER.**; "he can try for home at his own risk" |
| 26.1–29.3 s | "Baseball has a rule for a play that looks too easy." | Wide: the batter walks off; freeze | **DID YOU KNOW THIS RULE?** |
