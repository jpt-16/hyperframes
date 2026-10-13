---
workflow: general-video
flow: companion
message: "What if film could build your scout cards? Meet Scout Card — still building."
destination: instagram-reels
aspect: 1080x1920
fps: 30
length: 20s
entry: reveal.html          # index.html is the separate 94.5 s founder reel; untouched
---

# ScoutCard reveal reel

A 20 s cinematic product reveal: football-documentary opening, startup launch
payoff. Lives beside the founder reel in this project; it does not replace it.

## Files

| Path | What |
| --- | --- |
| `reveal.html` | Root composition (generated). Scenes, subtitles, voiceover, music, SFX. |
| `compositions/reveal/s1-hook.html` | 0–3 s. Black, two type beats, rumble + riser + impact. |
| `compositions/reveal/s2-meet.html` | 3–6 s. Film opens out of a line of light; "MEET SCOUT CARD." |
| `compositions/reveal/s3-product.html` | 6–14 s. Film → prototype card → script list → card taps; three labels. |
| `compositions/reveal/s4-close.html` | 14–20 s. Card 05 hero, zoom-through to the brand end card. |
| `tools/reveal/build_reveal.py` | **CONFIG block = every timing, text, colour, panel position and audio level.** Edit and re-run. |
| `tools/reveal/prep_media.py` | Rebuilds `assets/reveal/media/` and the logo mark from the original uploads. |
| `tools/reveal/make_audio.py` | Rebuilds the original music bed, rumble and text thumps. |
| `assets/reveal/` | Fonts, SFX (+ CREDITS.md), music bed, brand mark. `media/` is gitignored. |

## Preview and render

```bash
cd reel-scoutcard
python3 tools/reveal/build_reveal.py        # after any CONFIG change
tools/reveal/workspace.sh preview           # Studio preview of reveal.html
tools/reveal/workspace.sh check             # full check of reveal.html
npx hyperframes@0.8.154 render -c reveal.html --quality high --video-frame-format png -o renders/scoutcard-reveal.mp4
```

HyperFrames' `preview`, `check` and `lint` always read a project's `index.html`
(here, the founder reel), so `workspace.sh` builds a throwaway workspace whose
index is `reveal.html`. `render -c reveal.html` renders it directly.

## Honesty rules this reel follows

- Every product shot is the real prototype recording, tagged
  **PROTOTYPE · DEMO DATA** (the file on screen is `demo-script.csv`).
- No shot implies film is processed automatically: film and cards are shown as
  separate things, never morphed one into the other.
- The website recording was left out on purpose: it states capabilities
  ("90%+ of routes right", routes "read from the film") that are not shipped.
- The end card says **IN DEVELOPMENT**.

## Voiceover

The founder's own takes (IMG_1996 / 1998 / 2001), not TTS. They differ slightly
from the written script, and the subtitles follow what is actually said:

| Scene | Script | Recorded |
| --- | --- | --- |
| 2 | "That's why we're building Scout Card." | "Introducing Scout Card AI." |
| 3 | "…streamline **how** they prepare…" | "…streamline **the way** they prepare…" |
| 4 | "**We're** still building. This is just the beginning." | "Still building. This is just the beginning." |

To use exact-script lines, record them and replace `assets/reveal/media/vo1-3.wav`
(or the source clips, then re-run `prep_media.py`); update `vo_words.json` timings.

## Audio

- Opening: original sub rumble, the bundled Pixabay riser timed to peak on the
  3.0 s impact, Pixabay bass impact; two low thumps on the type beats.
- Bed: original 120 BPM instrumental (`assets/reveal/music/bed.wav`); bar lines
  fall on the scene changes, drums drop out 16–17 s, the reveal lands on the
  downbeat at 17.0 and the chord rings out to silence by 19.9 s.
- The bed ducks ~9 dB under the voice via a `data-automation` volume lane.
- Quiet whooshes on the three UI handoffs only.

## Missing / yours to provide

- **Licensed music (optional):** no music catalog was reachable here (HeyGen CLI
  not signed in), so the bed is original. Swap any track in by replacing
  `bed.wav` (start it on the impact, ~17 s long) — no code change needed.
- **Exact-script voiceover (optional):** see the table above.
- **Brand colour:** the logo is orange (#FF8A3D); the brief asked for electric
  blue accents, so blue is taken from the prototype's own line of scrimmage
  (#1E57E6) and orange appears only in the real logo and UI.
