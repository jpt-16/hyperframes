# "What should a catcher say?"

A 48.8 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: what a good mound visit looks like.

- **No voiceover**, per the brief. `CUES.md` lists each scene's start and end so you can record narration over it.
- **Sound:** a `make_bed` bed (style "glow"), a bat crack on the opening hit, glove pops, whooshes and stadium ambience.
- **Mix:** mastered to −20 LUFS so there is room for a voice on top. The same mix is in `assets/mix.wav`.
- **One pitcher and one catcher throughout**, on the same field, players and render workflow as the other Baseball Decoded videos.
- **The story runs on one clock** (`EV` in `build.py`):
  - the hit up the middle;
  - the pitcher's frustration: hands on hips, a tug of the cap, a look in;
  - the scoreboard;
  - the catcher's mask flipping up and his jog out;
  - he asks and listens;
  - the calm talk with mitt and glove over their mouths;
  - the breath;
  - the target;
  - the imagined pitch;
  - the nod and a tap of mitt to glove;
  - the real pitch, right on the mitt;
  - the throw back;
  - both ready for the next hitter.
- **New in this project:**
  - a center-field video board (top 6, one out, runners on first and second, three hits this inning);
  - the catcher's mask flipping up;
  - speech bubbles over the players' heads;
  - a glowing target ring at the mitt;
  - a cool "Picture it" look for the imagined pitch.

```bash
python3 tools/physics.py   # the pitches, including the low-and-away target pitch -> assets/play.json
python3 build.py           # index.html + assets/mix.wav + CUES.md
npx --yes hyperframes@0.8.154 render . -o renders/mound-visit.mp4 --video-bitrate 16M
```

## Accuracy notes

- **Listen first:** the catcher asks before he says anything else ("What are you feeling?"). The pitcher answers ("I'm rushing. Everything's up."), and the problem is named on screen before any advice.
- **Not every visit is the same:** on screen, "Every visit is different: sometimes it's mechanics, sometimes signs, sometimes just a breather."
- **Natural, teammate-to-teammate dialogue:**
  - "Take a breath." "Slow it down." "We've got this." "Low and away. Hit my glove." "Yeah. Let's go."
  - They finish with a tap of mitt to glove: teammates, not coach and student.
- **The imagined pitch** is shown as a visualization (a cool look and a "Picture it" tag). The real pitch afterward is a 93 mph fastball to the spot the catcher showed: low and away from a right-handed hitter.
