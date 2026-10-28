# "Intentional walk: smart strategy or big mistake?"

A 29.7 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: when intentionally walking a star makes sense, and when it backfires.

- **Framework:** the same three.js field, players and HyperFrames workflow as `first-pitch`, `first-baseman`, `lefty` and `catcher`.
- **New 3D pieces:**
  - dugouts with teammates on the rail
  - the defense's manager, who signals with four fingers up
  - on-deck circles and outfield seats with a crowd
  - the walk itself: the batter drops the bat and jogs to first, and the next hitter walks up from the on-deck circle
  - a mirrored rig for a left-handed hitter
  - rings marking players and runners
  - the 6-4-3 double-play path
- **Voiceover:** HyperFrames' local Kokoro TTS, voice `am_michael` at 1.5×, which fits the script into 25–30 s. The script is in `transcript.txt`.
- **Sync:** shots, word-by-word captions, titles and base diagrams are keyed to the voice. The hook question and the "2024 NLCS" title build word by word in place of captions.
- **Music:** a `make_bed` bed (style "pulse"). It ducks up to 7 dB under the voice and lands its chord on the freeze.
- **Sound:**
  - a tense riser and hit into the hook's zoom
  - whooshes on the cuts
  - the bat crack and a crowd roar on the grand slam
  - pops and ticks on the diagrams and checklist
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.

```bash
python3 tools/physics.py                                       # walk timeline, the pitch, the home run -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav)
npx --yes hyperframes@0.8.154 render . -o renders/intentional-walk.mp4 --video-bitrate 16M
```

## Accuracy

**Rules:**
- Since 2017, MLB's intentional walk is called from the dugout. The batter is awarded first base without any pitches, so the video shows a signal, not four pitches.
- Runners move up on a walk only when forced:
  - With runners on 2nd and 3rd, the walk loads the bases and nobody else moves.
  - With runners on 1st and 2nd (Situation B), everyone is forced up one base.
- A double play needs fewer than two outs. The verdict scene's situation is 1 out, runners on 2nd and 3rd: walking the star loads the bases, which creates a force at every base and makes a 6-4-3 possible.

**The 2024 NLCS scene is an illustrative 3D reenactment:** generic uniforms, not broadcast footage. As reported:
- NLCS Game 2, October 14, 2024, at Dodger Stadium.
- 2nd inning, 2 outs, Mets leading 2–0, runners on 2nd and 3rd.
- The Dodgers intentionally walked Francisco Lindor, a switch-hitter shown batting left against a right-hander, to load the bases.
- Mark Vientos then hit a grand slam off Landon Knack, a 95 mph fastball, to right-center, 391 ft per Statcast's projection.
- Sources: [MLB.com](https://www.mlb.com/mets/news/mark-vientos-hits-grand-slam-for-mets-in-nlcs-game-2), [SI](https://www.si.com/mlb/mets-mark-vientos-felt-slighted-by-dodgers-intentional-walk-before-grand-slam), [AMNY](https://www.amny.com/sports/mets-dodgers-nlcs-game-2-10-14-24), [CBS](https://www.cbssports.com/mlb/news/mets-vs-dodgers-score-nlcs-game-2-takeaways-as-mark-vientos-grand-slam-helps-new-york-tie-series/live), [ESPN](https://africa.espn.com/mlb/story/_/id/41798337/new-york-mets-win-game-2-even-nlcs-los-angeles-dodgers).

**The home run physics** (gravity, drag, backspin) goes out to right-center, 22° toward right field:
- The exit speed is solved so the ball would carry 391 ft to field level. It clears the 376 ft wall about 14 ft up and lands in the first rows.
- The real exit speed and launch angle weren't found, so the model's pair is a plausible one, not the real one, and neither appears on screen.
- The pitch location is illustrative.

**No probabilities are shown.** The two situations are framed as "can make sense" vs. "adds risk", not as rules, so the video doesn't imply every intentional walk is a mistake.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.3 s | "Why would a manager intentionally put…" | The star in the box, runners on 2nd and 3rd, the catcher turning to the dugout. The manager's four fingers on "intentionally". The star drops the bat and walks; quick zoom on "base?", then a hard cut | **WHY GIVE HIM FIRST BASE?** builds with the voice; star pin; signal and "no pitches thrown" tags |
| 3.3–7.4 s | "Because sometimes, the real target…" | He reaches first (bases loaded). A dimmed wide shot behind the choice card. The next hitter swinging on deck | Base diagram with **+1 FREE BASERUNNER**; choice card (pitch to the star, struck out on "isn't" / walk him, face the next hitter); **AVOID ONE HITTER. / FACE ANOTHER.** |
| 7.4–8.2 s | "But there's a risk." | Behind the walked star on first as the next hitter walks up | Caption |
| 8.2–16.4 s | "In the 2024 NLCS…grand slam." / "That's the gamble:" | A high establishing orbit; the manager's signal; Lindor to first; bases loaded with Vientos in; the pitch and swing; a tracking shot into the right-center seats; a low ½-speed replay | **2024 NLCS** title; Game 2 situation; reenactment label; **INTENTIONAL WALK → GRAND SLAM**; 95 mph / 391 ft tags |
| 16.4–21.5 s | "…avoid one dangerous hitter…the extra baserunner matters." | Tactical board over the field from above | Situation A (first base open: the walk sets up a force at every base) and B (bases crowded: the walk forces runners up); **THE MATCHUP MATTERS. / SO DO THE RUNNERS AND OUTS.** |
| 21.5–25.9 s | "So managers have to weigh…" | Manager weighing it; the star; the next hitter on deck; the outs; overhead with the 6-4-3 path and a ghost runner on first | Checklist: HITTER · NEXT MATCHUP · OUTS · DOUBLE PLAY? |
| 25.9–29.7 s | "So when is walking a superstar actually smart baseball?" | Four fingers again; the star walks; the next hitter in, pitcher in his stride; freeze before he lets it go | **SMART STRATEGY… OR BIG MISTAKE?** then **WOULD YOU WALK HIM?** |
