# "Tommy John: back, but not the same?"

A 27.3 s vertical (1080×1920, 30 fps) 3D baseball breakdown for Baseball Decoded: why returning to the mound after Tommy John surgery isn't the same as returning to peak performance.

- **Framework:** the same three.js field, players, dugouts, seats and HyperFrames workflow as `infield-fly`, `intentional-walk` and `first-pitch`.
- **New:**
  - an anatomical elbow scene (a separate three.js scene in the same canvas)
  - left/right split-screen rendering
  - a catcher's target with miss marks
  - the pitcher's frustrated reaction
- **Voiceover:** your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.5×); the text is in `transcript.txt`. Shots, word-by-word captions and every graphic are keyed to its words. The hook title **BACK FROM TOMMY JOHN… BUT NOT THE SAME?** builds on "Tommy John" and "pitchers" in place of captions for the first line.
- **Music:** a quiet `make_bed` bed (style "glow"), ducked up to 7 dB under the voice. It lands its chord on the closing question.
- **Sound:**
  - pitch whooshes and glove pops
  - a riser and hit into each freeze
  - soft pops on the elbow labels and a tap on the tear
  - a hit on the 28.1% and on "≠"
  - ticks on the timeline
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.

```bash
python3 tools/physics.py                                       # the pitches -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav)
npx --yes hyperframes@0.8.154 render . -o renders/tommy-john.mp4 --video-bitrate 16M
```

## Accuracy

**The elbow** is an illustrative anatomical model of a right elbow, seen from the inner (medial) side:
- **Bones:** the humerus with its medial epicondyle, the ulna (olecranon, coronoid, sublime tubercle) and the radius.
- **The UCL:** its anterior bundle runs from the underside of the medial epicondyle to the sublime tubercle, the band that resists the valgus pull on the inner elbow in a throw (shown by the arrows).
- **The reconstruction:** a tendon graft in a figure-of-eight through bone tunnels in the ulna and the medial epicondyle. This is the classic Jobe-style configuration; surgeons use several variants.
- **Non-graphic:** no incision, tissue or blood.
- **Not an instant fix:** an on-screen note says "the graft then needs months to heal", so the surgery isn't shown as a simple swap that restores the arm.

**The 28.1%:**
- **The claim:** within three seasons, only 28.1% of the MLB pitchers analyzed returned to full performance by the study's criteria (reported as 3.9% after one season).
- **The study:** reported for a 2025 study of 129 MLB pitchers after UCL reconstruction. "Full performance" was recovery across expected FIP, WAR, overall velocity, fastball velocity and spin rate.
- **On screen:**
  - The bar fills to 28.1% and hatches the other 71.9% ("not by year 3").
  - The source label reads "MLB pitchers · UCL surgery study (2025)".
  - A note says full performance means the study's performance benchmarks, not just pitching again. It is **not** a return-to-play rate.
- **Verification caveat:** this session couldn't open the primary paper (PubMed and SAGE are outside its network). Other abstracts on the same question report similar but not identical numbers: an AAOS 2025 abstract on 119 pitchers reports 3%, 21% and 32% at 1, 2 and 3 seasons. Check the original paper before publishing.

**Timeline:** recovery is shown as "often 12–18 months", with performance rebuilding continuing after the return, and the note "Every pitcher's timeline is different".

**Illustrative elements:**
- The analytics screen is labelled "Pitch tracking · illustrative" and has no numbers.
- The pitches are simulated (gravity, drag, spin lift) with illustrative locations: an on-target fastball before surgery, a miss sailing up and arm-side after, and a five-pitch command scatter. No speeds appear on screen.

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.1 s | "Tommy John surgery doesn't magically make pitchers throw harder." | Behind his throwing shoulder: a hard fastball, frozen just out of his hand, plus a zoom. Then high behind the plate: after surgery, the pitch sails well off the catcher's target. His reaction, head down | **BACK FROM TOMMY JOHN… BUT NOT THE SAME?**; "Before surgery" / "After surgery: way off the target" |
| 3.1–6.7 s | "It rebuilds the ligament that stabilizes your elbow during a throw." | A push into his cocked elbow, then the elbow from the inside: the UCL lights up; arrows show the pull it resists in a throw; torn; the graft woven in a figure-of-eight; it settles | Pins: Elbow · UCL · Torn UCL · Tendon graft; **REBUILD THE LIGAMENT.**; "Illustrative · the graft then needs months to heal" |
| 6.7–12.6 s | "And here's the surprising part…within three seasons of surgery." | Center field: he walks back onto the mound. Then the statistic over him, dimmed | **ONLY 28.1%** (counting up on "twenty-eight") · RETURNED TO FULL PERFORMANCE WITHIN 3 SEASONS · bar 28.1% vs 71.9% · source and definition notes |
| 12.6–16.4 s | "Getting back on the mound…two completely different things." | Split. Left: behind him, the delivery completed (return to play). Right: above the plate, his pitches scattering around the same target | RETURN TO PLAY ✓ / FULL PERFORMANCE? · Command · consistency; **RETURN TO PLAY ≠ FULL PERFORMANCE** |
| 16.4–19.1 s | "Recovery can take 12 to 18 months, and even after that…" | Orbiting him throwing, dimmed under the timeline | Surgery → Recovery: often 12–18 months → Return to the mound → Rebuilding command & performance →; "Every pitcher's timeline is different" |
| 19.1–21.7 s | "…pitchers still need time to regain their command and performance." | High behind the plate: the fifth pitch lands closer to the target than the first four | "Same target, five pitches: command comes back slowly" |
| 21.7–25.1 s | "The surgery can save a career. But it doesn't guarantee you'll get your old arm back." | A composed delivery from the third-base side; then the analytics screen | **THE COMEBACK IS ONLY HALF THE STORY.**; velocity / command / consistency, before vs. after (illustrative) |
| 25.1–27.3 s | — | The bookend: released, frozen | **WOULD YOU RISK LOSING YOUR BEST STUFF?** |
