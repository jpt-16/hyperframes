# "Why every team wants a lefty"

A 40 s vertical (1080×1920, 30 fps) 3D baseball explainer for Baseball Decoded: the three edges a left-handed pitcher brings.

1. A different look.
2. The lefty-lefty matchup.
3. Control of the running game.

- **Framework:** the same three.js field, players, split-screen renderer and HyperFrames workflow as `catcher`, `ground-balls`, `fly-balls` and the earlier videos.
- **No narration:** this video has none. The voiceover is recorded separately and laid on top.
- **Voiceover cues:** the picture cuts on the planned voiceover cues. `vo-cues.txt` and `vo-cues.srt` give the window each line should land in.
- **Sound:** effects only (pitches, glove pops, swings, the pickoff throw and dive, cut whooshes, title hits, a crowd bed). They're mastered to −20 LUFS so a voiceover at normal level sits on top. The finished composition is `index.html`; its effects track is `assets/mix.wav`.

```bash
python3 tools/physics.py        # the pitches -> assets/play.json
python3 build.py                # index.html + assets/mix.wav (effects only) + vo-cues.txt / vo-cues.srt
npx --yes hyperframes@0.8.154 render . -o renders/lefty.mp4 --video-bitrate 16M
```

To lay the voiceover in afterwards (keeping the effects under it), either:
- drop `renders/lefty.mp4` and your VO into any editor, or
- `ffmpeg -i renders/lefty.mp4 -i vo.wav -filter_complex "[0:a][1:a]amix=inputs=2:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac lefty-vo.mp4`

## The model

**Pitches (`tools/physics.py`):**
- **Physics:** gravity, drag and spin lift, aimed by iteration.
- **The right-hander's pitches:** a 93 mph fastball and an 85 mph slider. His changeup and curve appear only as faint "what hitters see most" paths.
- **The left-hander's pitches:** the right-hander's pitches mirrored across the mound-to-plate line. Same speed, same spin, same break; only the release side changes. The video compares the angle and never claims a lefty throws harder or moves the ball more.
- **One slider path, two hitters:** the lefty's slider is the same path in both matchups. It crosses low and away from a left-handed hitter, and at a right-handed hitter's back foot.

**The left-hander (`assets/field.js`):**
- He's the right-handed figure drawn through a mirror, so his mechanics match the righty's exactly.
- **In the stretch:** he stands side-on, facing first base. A righty faces third.
- **The pickoff:** the same set, then a leg lift, then a step straight at first.
- **The throw:** about 76 mph from his hand at release to the first baseman's glove, gravity only.
- **The dive:** the runner leads 11 ft off the bag. He reads the step, takes a crossover step and dives head-first to the back corner of the bag as the tag comes down.
- **No call:** it's shown as a close play with no out or safe call. On screen: "A good move is a threat · not a guaranteed out."

## Shots

| Time | Scene | Shot | On screen |
|---|---|---|---|
| 0–2.9 s | Hook | Low, first-base side: the lefty explodes through his delivery. Flash cut: over the left-handed hitter's shoulder as the slider comes in at ½ speed, then from the front as he swings through it | **WHY DOES EVERY TEAM WANT A LEFTY?** from frame one |
| 2.9–11.8 s | A different look | **Familiar:** a righty to a righty hitter, with faint paths of the righty's four pitches. **Split screen:** the same pitch from a righty (left) and a lefty (right), ½ speed, with trajectory lines. **Hitter's view:** the lefty's pitch from a right-handed hitter's eyes, with the usual righty path as a faint ghost | Title; "Most hitters see far more right-handers"; RIGHTY / LEFTY; "Same pitch, mirrored: a different release angle"; "From the other side: a less familiar look" |
| 11.8–20.6 s | The lefty-lefty matchup | **Center field:** lefty vs. left-handed hitter, who chases the slider. **Replay:** high behind the plate with the strike zone and the slider's path running away from him. **Center field again:** the same pitch to a right-handed hitter, at his back foot; he takes it | Title; "Lefty pitcher vs. lefty hitter"; "Starts on his side, then breaks away"; "Righty hitter: the same pitch breaks toward him"; footnote "On average, a tougher matchup · not true of every hitter" |
| 20.6–30.4 s | Control the running game | **Wide from behind the mound:** the runner takes his lead. **Over the lefty's shoulder in the set:** a sight line to the runner. **Real time:** the pickoff. **Replay from beyond first base:** a freeze on the step with the lead marked, then ½ speed through the dive and tag | Title; "Righty in the set: faces third / Lefty in the set: faces first"; pinned labels HIS LEAD and STEP TO FIRST; footnote |
| 30.4–40 s | Payoff | Three connected shots: the lefty's delivery (1 · A different look), the left-handed hitter swinging through it (2 · Lefty vs. lefty), the runner giving ground when the lefty's head snaps over (3 · The pickoff threat). Then low in front of the mound as he walks back up to the rubber and turns to face home | **ONE ARM. THREE ADVANTAGES.** then **THAT'S THE VALUE OF A LEFTY.** |
