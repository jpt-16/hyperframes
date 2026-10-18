# JT Builds Co: "the egg" reel

A 9-second faceless pattern-interrupt reel, 1080×1920, with sound effects only (add your music in CapCut).

```bash
python3 tools/sfx.py          # synthesise the sounds (roll, edge, crack, shards)
python3 build.py              # write index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 check .
npx --yes hyperframes@0.8.154 render . -o renders/jtb-egg-reel.mp4 -q delivery
```

## Timeline

| Time | What happens |
|---|---|
| 0–1.5 s | A real-time 3D egg rolls across a dark stone counter toward the edge (`assets/egg.js`, three.js, rendered from HyperFrames time). |
| 1.5–2.0 s | It tips and drops. The camera follows, then whips down. The old website falls in on the same motion and lands with an egg-crack impact. |
| 2.0–7.0 s | The old site cracks like a shell and breaks away: REBUILT → BUILT FOR PHONES → ONE TAP TO BOOK → EASY TO FIND → MODERN. MOBILE. BOOKABLE. |
| 7.0–9.0 s | "Your next customer is looking online." then JT Builds Co \| DM ‘SITE’. |

The search beat shows the example listing among the results, not first. There are no ranking claims anywhere. The example business is fictional (`jtb-shorts/niches.json`).

`egg-preview.html` previews the 3D shot on its own. Serve the folder over HTTP, since ES modules don't load from `file://`.

## Sound cues (for lining up music)

| Time | Cue |
|---|---|
| 0–1.5 s | egg roll |
| 1.5 s | edge knock |
| 2.02 s | crack and impact (the match cut) |
| 2.3 s | shell breaks |
| 2.95, 3.95, 4.92 s | beat hits |
| 6.0 / 6.28 / 6.56 s | word stamps |
| 7.0 s | end impact |
| 7.9 s | logo |

## Credits

- **three.js** (MIT): `assets/vendor/`
- **GSAP:** standard licence
- **Fonts:** OFL
- **Sounds:** original, synthesised in code
