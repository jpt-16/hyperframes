# "Can he throw him out from here?": tagging up from third

A 23.8 s vertical (1080×1920) 3D simulation of a sacrifice fly. A runner tags at third, the right fielder catches a deep fly ball and throws home, and the catcher applies the tag. The video shows the numbers that decide the play and then freezes it at the plate. There's no narration, only on-screen statistics and sound effects.

**The hook** follows a short-form explainer style:
- **Opening frame:** a bold statement is on screen from the first frame.
- **Eyebrow:** a small "— Tagging up from third" label sits above the headline.
- **Caption build:** the question builds word by word, each word sliding up out of a blur.
- **Accent and sync:** the payoff words are in orange, and the catch-spot ring pulses on "here?".

The project uses the same framework and render workflow as `catcher-clock`: a three.js field driven by HyperFrames time, and the comp library in `jtb-shorts/lib`.

```bash
python3 tools/physics.py      # simulate the play -> assets/play.json
python3 build.py              # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/tag-up.mp4 --video-bitrate 16M
```

## The play

Every number on screen and every movement in 3D is read from `assets/play.json`, so the labels, timers and animation always agree. The clock starts at the catch (t = 0).

| | Direct throw | Looping throw (comparison) |
|---|---|---|
| Release speed | 92 mph | 79.6 mph (shown as 80) |
| Launch angle | 13.95° (the flattest path at 92 mph that reaches the glove in the air) | 25° |
| Throw distance | 290 ft (release to glove) | 290 ft |
| Peak height | 28.9 ft | 49.2 ft |
| Flight time | 2.98 s | 3.79 s |
| Catch-to-release | 0.80 s | 0.80 s |
| Ball in the catcher's glove | 3.78 s | 4.59 s |
| Tag applied (+0.20 s) | **3.98 s** | **4.79 s** |
| Runner reaches the plate | 4.09 s | 4.09 s |
| Result | **Out** by 0.11 s, foot 2.3 ft short | **Safe** by 0.70 s |

**What would flip the out to safe** (changing one variable at a time, everything else held; computed in `tools/physics.py`):

| Variable | In the play | Safe at |
|---|---|---|
| Runner top speed | 27.0 ft/s | 27.9 ft/s |
| Catch-to-release | 0.80 s | 0.91 s |
| Catch depth | 300 ft | 307 ft |
| Arm speed (flattest throw each time) | 92 mph | 89.5 mph |

That's why the video doesn't claim any arm speed guarantees an out. A 92 mph throw gets this runner by 0.11 s, and the margin goes away if any of these changes slightly.

## Assumptions (simulation, not MLB tracking data)

**The ball.** It is integrated in 1 ms steps under gravity, air drag and backspin lift.

- **Drag:** ρ = 1.19 kg/m³ (about 75 °F at sea level).
  - Throws use Cd = 0.35, within the range measured in pitch tracking.
  - The batted fly ball uses Cd = 0.40. That value reproduces typical Statcast carry (about 370 ft at 95 mph and 30°).
- **Lift:** CL = 1.5·S for S < 0.1, otherwise 0.09 + 0.6·S, where S = rω/v (Sawicki et al.). Throws carry 1,500 rpm of backspin.
- **Aim:** each throw's launch angle (or speed, for the loop) is solved so the ball arrives in the catcher's glove at 2.4 ft, in front of the plate on the third-base side.

**The fielder.** He catches 300 ft from home, 20° toward right field from the center-field line, with the glove at 6.4 ft. He crow-hops 7 ft toward home and releases at 6.3 ft, 0.80 s after the catch.

**The runner.**
- **Start:** he holds the bag until the catch and reacts 0.10 s after it.
- **Sprint:** v(t) = 27·(1 − e^(−t/0.65)) ft/s.
- **Slide:** feet first for the last 9 ft, slowing at 16 ft/s² (sliding friction μ ≈ 0.5).
- **Finish:** he scores when his foot reaches the plate's near corner, 89 ft from the bag.

**The catcher.** He needs 0.20 s from ball in the glove to tag applied.

**Sourced figure.** 27 ft/s is the MLB average Statcast sprint speed on competitive runs. Baseball Savant describes 23 ft/s as poor and 30 ft/s as elite. This is the only real MLB statistic the video uses.

## Shots

| Time | Shot | On screen |
|---|---|---|
| 0–0.55 s | Straight down on the runner at third (the opening frame) | "Arm strength isn't everything." |
| 0.55–2.8 s | One continuous dive: up and out over the infield, swinging wide of right field, down behind the fielder for the catch; an orange ring marks the spot | "Can an outfielder throw him out from here?", word by word |
| 2.8–5.0 s | Freeze on the catch. The camera rises over right field; the throw line and the runner's line draw on the field | Caught 300 ft · throw ≈ 290 ft · runner 89 ft |
| 5.0–6.45 s | The crow hop and release, from the side (0.75× speed) | Runner and Ball clocks start at the catch; 92 mph, 14° |
| 6.45–8.3 s | Both throws, chased from behind; the loop is released at the same moment | Flight timers for both |
| 8.3–9.5 s | The runner, from behind his shoulder (0.5×) | Runner clock with feet to go |
| 9.5–10.9 s | The plate, from the first-base side: the catch and the tag (0.42×) | – |
| 10.9–14.8 s | Freeze on the tag, orbiting from foul ground | OUT · 0.80 + 2.98 + 0.20 = 3.98 vs 4.09 · 2.3 ft short |
| 14.8–17.6 s | The same play with the looping throw | SAFE · 0.80 + 3.79 + 0.20 = 4.79 |
| 17.6–23.8 s | Both throws side by side, to scale | What would flip it; no arm speed guarantees an out |

## Sound

The effects come from the shared kit: a crowd bed that swells with the throw, whooshes on cuts, a glove pop on each catch, clock ticks while the timers run, and an impact and riser on the freeze. The mix is mastered to about −17 LUFS.
