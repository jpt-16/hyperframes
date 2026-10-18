# JT Builds Co: "the egg" reel

A 9-second faceless pattern-interrupt reel, 1080×1920, sound effects only (add music in CapCut if wanted).

**v2 (`build.py`)** uses real footage and hard cuts, with one noise hit per cut, modelled on the reference reel. **v1 (`build_3d.py`)** is the earlier three.js 3D-egg version, kept as an alternative.

```bash
python3 build.py              # write index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 check .
npx --yes hyperframes@0.8.154 render . -o renders/jtb-egg-reel-v3.mp4 -q delivery
```

## Media (not committed)

`assets/media/` holds footage and captures and is git-ignored.

| File | What it is |
|---|---|
| `egg.mp4` | The egg clip, 1080×1314, played at 0.72× speed. |
| `egg-bg.mp4` | A blurred fill made from the egg clip. |
| `egg-audio.wav` | The clip's own sound, at the same speed, with the crack lined up to the visible impact. |
| `clover-hero.jpg` | cloverdownsdetailing.com, desktop, at 1200×732 (2× density). |
| `clover-mobile.mp4` | The home page on a 390-px phone, scrolling, captured frame by frame. |
| `clover-form.mp4` | The quote form being typed into, captured frame by frame. **It is never submitted.** |
| `clover-beverly.png`, `clover-salem.png`, `clover-danvers.png` | The tops of the town pages. |

`tools/capture-site.js` recaptures the site captures above. Encode them as described in `build.py`.

```bash
NODE_EXTRA_CA_CERTS=/root/.ccr/ca-bundle.crt NODE_PATH=$(npm root -g) node tools/capture-site.js
```

The egg clip is by TikTok creator **@nikso2893** and is credited on screen. Get their permission before posting, or film your own 2-second egg drop and drop it in as `egg.mp4`.

## Timeline

| Time | Shot | Word |
|---|---|---|
| 0–1.87 s | The real egg rolls off the table and breaks on the tile. | – |
| 1.87 s | Card | need a website? |
| 2.33 s | A generic 2011-style site for a made-up shop, in a browser ("Not secure") | outdated. |
| 2.97 s | cloverdownsdetailing.com in the same browser, with a slow push | modern. |
| 3.60 s | The same site on a phone, really scrolling to the sticky BOOK NOW bar | mobile. |
| 4.40 s | Its quote form being filled in | bookable. |
| 5.30 s | Its Beverly, Salem and Danvers town pages, as hard cuts. No search-ranking claim. | findable. |
| 6.40 / 6.70 s | Cream card / amber card | clean. / fast. |
| 7.00–9.00 s | "Your next customer is looking online." then JT Builds Co \| DM ‘SITE’ at 7.9 s. | – |

## Sound

- **0–1.87 s:** the egg clip's own room tone and crack, which peaks at 1.74 s.
- **From 1.87 s:** a noise hit on every cut, at 1.87, 2.33, 2.97, 3.60, 4.40, 5.30, 5.70, 6.10, 6.40, 6.70, 7.00, 7.30 and 7.90 s. The town-page and second-line hits are softer.
  - Each hit is a burst of bright air with a click on the attack. It fades in a straight line (in dB) and stops hard just before the next cut.
  - It is synthesised in `tools/sfx.py` (`noise_hit`).
- **Form beat:** faint key clicks under the typing.
- No music.

## Credits

- **Egg footage:** @nikso2893 (TikTok)
- **GSAP:** standard licence
- **Fonts:** OFL
- **three.js** (v1 only): MIT
