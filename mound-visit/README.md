# "What should a catcher say?"

A 46.8 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: what a good mound visit sounds like.

- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.55×). The text is in `transcript.txt`.
  - Shots, word-by-word captions, speech bubbles and scene titles are keyed to its words.
  - The opening question is covered by the big hook title instead of captions. The quoted line ("Take a breath. Slow everything down. We've got this.") is the catcher's speech bubbles instead of captions.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Layout:** captions at the top; scene titles in a dark band just under them; the players and their speech bubbles in the middle.
- **Sound:** a `make_bed` bed (style "glow") ducked up to 7 dB under the voice, a bat crack on the opening hit, glove pops, whooshes and stadium ambience.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.
- **One pitcher and one catcher throughout**, on the same field, players and workflow as the other Baseball Decoded videos.
- **The story runs on one clock** (`EV` in `build.py`, keyed to the narration):
  - the hit up the middle, the pitcher's frustration, the scoreboard;
  - the catcher's mask flipping up and his jog out;
  - he asks, then listens;
  - the calm talk with mitt and glove over their mouths, and the breath;
  - the target and the imagined pitch;
  - the nod and a tap of mitt to glove;
  - back to work: the real pitch, right on the mitt, and the throw back;
  - both ready for the next hitter.
- **New in this project:**
  - a center-field video board (top 6, one out, runners on first and second, three hits this inning);
  - the catcher's mask flipping up;
  - speech bubbles over the players' heads, including a struck-out "Not this" bubble;
  - a glowing target ring at the mitt;
  - a cool "Picture it" look for the imagined pitch.

```bash
python3 tools/physics.py                                       # the pitches, including the low-and-away target pitch -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/mound-visit.mp4 --video-bitrate 16M
```

## Accuracy notes

- **Don't make it worse:** while the script says a catcher shouldn't list everything that's wrong, a struck-out bubble labeled "✕ Not this" shows that kind of list.
- **Listen first:**
  - The catcher asks ("What's going on?") before he gives any advice.
  - A checklist builds with the script's questions: rushing, losing confidence, missing spots, falling behind in counts.
  - The pitcher answers ("I'm rushing. Everything's up."), and "Rushing" is marked as his answer.
- **Not every visit is the same:** on screen, "Every visit is different: command, frustration, tipping pitches, mechanics, signs, or just a breather."
- **Teammates, not coach and student:**
  - The dialogue is short and natural: "Take a breath." "Slow everything down." "We've got this." "Low and away. Hit my glove." "Yeah. Next one."
  - They finish with a tap of mitt to glove.
- **A specific adjustment:** for "tipping his pitches or changing his mechanics", the example on screen is a common fix for tipping: "Example: same glove set, every pitch." It is labeled as an example.
- **The imagined pitch** is shown as a visualization, with a cool look and a "Picture it" tag. The real pitch afterward is a 93 mph fastball to the spot the catcher showed: low and away from a right-handed hitter.

## Shots

| Time | Script | Shot | On screen |
|---|---|---|---|
| 0–3.6 s | "When a pitcher starts struggling, what should a catcher say during a mound visit?" | A single up the middle; the pitcher, hands on hips, the cap; the scoreboard | **WHAT SHOULD A CATCHER SAY?**; "Another hit", "Frustrated" |
| 3.6–8.4 s | "The first thing? Don't make it worse. A catcher shouldn't walk to the mound and start listing everything…" | The mask flips up, the jog out, he arrives | "✕ Not this" bubble |
| 8.4–14.2 s | "Instead, they need to figure out what's happening. Is the pitcher rushing? …" | He asks; then from the third-base side, he listens | **FIRST: FIGURE OUT THE PROBLEM**; the checklist; "I'm rushing. Everything's up." |
| 14.2–19.7 s | "Sometimes, the best thing to say is simple: 'Take a breath. Slow everything down. We've got this.'" | Close, mitts over mouths; in profile, the breath | **KEEP IT SIMPLE**; the quote as bubbles; Inhale / Exhale |
| 19.7–25.4 s | "If the pitcher is struggling with command… focus on one target…" | He shows the spot; the imagined pitch from the pitcher's eyes, slowed, into the mitt | "Low and away. Hit my glove."; **ONE TARGET. ONE PITCH AT A TIME.** |
| 25.4–29.7 s | "If he's getting frustrated, bring his attention back to the next pitch. Not the last one." | The nod and the tap; back to work, from high behind home | **FOCUS ON THE NEXT PITCH**; the "every visit is different" note |
| 29.7–33.0 s | "…tipping his pitches or changing his mechanics… a specific adjustment. But here's the biggest thing:" | Set on the rubber; the delivery | **ONE SPECIFIC ADJUSTMENT**; "Example: same glove set, every pitch" |
| 33.0–37.3 s | "A good catcher doesn't try to fix everything in one conversation." | Right on the mitt; the throw back | **NOT EVERYTHING IN ONE TALK**; "Right where he set up" |
| 37.3–45.0 s | "They give their pitcher confidence, a clear plan… believe in himself again." | Over the pitcher's shoulder to the plate; a new hitter steps in; high behind home | Confidence / A clear plan / Trust in the next pitch; **GOOD CATCHERS DON'T JUST CALL PITCHES. THEY BUILD CONFIDENCE.** |
| 45.0–46.8 s | (end) | Baseball Decoded end card | |
