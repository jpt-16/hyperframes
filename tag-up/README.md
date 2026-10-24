# "Can he throw him out from here?": tagging up from third

A 63.2 s vertical (1080×1920) 3D simulation of a sacrifice fly. A runner tags at third, the right fielder catches a deep fly ball and throws home, and the catcher applies the tag.

- **Voiceover:** HyperFrames' built-in Kokoro TTS, run locally (`am_michael`, 1.05×). The script is in `transcript.txt`.
- **Sync:** captions and every shot, timer and reveal are timed to the spoken words.
- **Sound:** effects sit under the voice, and the mix is mastered to about −14 LUFS.

The project uses the same framework and render workflow as `catcher-clock`: a three.js field driven by HyperFrames time, and the comp library in `jtb-shorts/lib`.

```bash
python3 tools/physics.py                                       # simulate the play -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 render . -o renders/tag-up.mp4 --video-bitrate 16M
```

**The hook** follows a short-form explainer style:
- **Opening frame:** "Arm strength isn't everything." is on screen from the first frame.
- **Question:** the spoken question then builds word by word as it's said, each word sliding up out of a blur, with the payoff words in orange.
- **Camera:** one continuous dive runs from straight above the runner on third to low behind the right fielder for the catch.

**Captions** use the same treatment for the rest of the script. Numbers and key terms are in orange.

## The play

Every number on screen and every movement in 3D is read from `assets/play.json`, so the labels, timers and animation always agree. The clock starts at the catch (t = 0).

| | Direct throw | Looping throw (comparison) |
|---|---|---|
| Release speed | 95 mph | 79.6 mph (shown as 80) |
| Launch angle | 12.41° (the flattest path at 95 mph that reaches the glove in the air) | 25° |
| Throw distance | 290 ft (release to glove) | 290 ft |
| Peak height | 26.3 ft | 49.2 ft |
| Flight time | 2.86 s | 3.79 s |
| Catch-to-release | 0.80 s | 0.80 s |
| Ball in the catcher's glove | 3.66 s | 4.59 s |
| Tag applied (+0.20 s) | **3.86 s** | **4.79 s** |
| Runner reaches the plate | 4.09 s | 4.09 s |
| Result | **Out** by 0.23 s, foot 5.1 ft short | **Safe** by 0.70 s |

**What would flip the out to safe** (changing one variable at a time, everything else held; computed in `tools/physics.py`):

| Variable | In the play | Safe at |
|---|---|---|
| Runner top speed | 27.0 ft/s | 29.0 ft/s |
| Catch-to-release | 0.80 s | 1.03 s |
| Catch depth | 300 ft | 316 ft |
| Arm speed (flattest throw each time) | 95 mph | 89.5 mph |

That's why the video doesn't claim any arm speed guarantees an out. A 95 mph throw gets this runner by 0.23 s, and the margin goes away if any one of these changes. Accuracy isn't simulated: every throw reaches the glove, and the end card says so.

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

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–7.9 s | "How hard is it…" / "Let's break it down." | One continuous dive from above third to behind the right fielder; the catch ring pulses on "outfielder" | "Arm strength isn't everything." on frame one, then the question word by word |
| 7.9–11.6 s | "…catches this ball about 300 feet from home plate." | Freeze on the catch; the camera rises over right field as the throw line and the runner's line draw in | 300 ft · throw ≈ 290 ft · runner 89 ft |
| 11.6–19.2 s | "He needs to get the ball out of his glove…" | The exchange in slow motion; the release lands on "throw" | Runner and Ball clocks start at the catch |
| 19.2–25.9 s | "At 95 miles per hour…" | Chasing the throw, then looking out from behind the plate as it comes in | 95 mph · 12° · flight timer |
| 25.9–29.0 s | "And the runner is already sprinting toward home." | Behind the runner's shoulder | Runner clock, feet to go |
| 29.0–41.4 s | "…the throw's trajectory." / "A high, looping throw…" | Replay, side view, to scale: both throws launched together | Each throw's flight timer; 3.79 s vs 2.86 s; 12° is the flattest a 95 mph throw can go and still reach the glove |
| 41.4–48.4 s | "Now it comes down to the race…" | Behind the runner, then the plate, slowing to the tag on "time?" | Both clocks |
| 48.4–53.4 s | "That's why arm strength alone…" | Freeze on the tag, orbiting | OUT · 0.80 + 2.86 + 0.20 = 3.86 vs 4.09 · 5.1 ft short · the loop would be safe |
| 53.4–58.6 s | "Distance, release time, trajectory, accuracy…" | Both throws to scale | Each factor lights up as it's named, with the value that would make him safe |
| 58.6–63.2 s | "So, would you send the runner…" | Back above the runner on third | The question word by word: SEND / HOLD |

## Sound

Under the voice, the effects come from the shared kit: a crowd bed that swells with the throw, whooshes on cuts, a glove pop on each catch, clock ticks while the timers run, and an impact and riser on the freeze. Effects sit 6 dB under the voice; the mix is mastered to about −14 LUFS.
