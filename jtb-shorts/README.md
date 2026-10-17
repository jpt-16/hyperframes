# JT Builds Co — faceless shorts

Short vertical videos (1080×1920, 10–20 s, no face or voiceover) about website design, local SEO and website conversions for small businesses. You write one small JSON file per video, and `jtb.py` turns it into a HyperFrames project, checks it, renders it and masters the audio.

```bash
python3 jtb.py render videos/mistakes-hvac.json     # -> renders/mistakes-hvac.mp4
python3 jtb.py all                                  # every spec in videos/
python3 jtb.py fanout videos/mistakes-hvac.json     # the same video for every niche
python3 jtb.py new local-seo dental seo-dental-2    # new spec, copied from an example
python3 jtb.py snap videos/x.json 0.3 4 9           # PNG frames to eyeball before rendering
python3 jtb.py lint videos/*.json                   # copy check only
```

Options: `--niche <key>` and `--slug <name>` override the spec. `--draft` renders faster at lower quality.

Requirements: Python 3 with numpy and scipy, ffmpeg, and Node (for `npx hyperframes@0.8.154`).

## What every video has

- **Hook (0–2.3 s):** big kinetic type. The eyebrow is on screen from frame 0 and the full hook is readable by about 0.5 s. A device rises underneath it, then lands as the first scene starts.
- **Body:** cinematic device mockups showing example business sites, a simulated local search page, a business profile and a dashboard. Pop-up chips, highlight rings, light-sweep screen wipes and a JT Builds Co. brand bar.
- **CTA (last ~3.4 s):** the JT Builds Co. lockup (charcoal tile, JT mark, **BUILDS** white, **CO.** grey), the ask, an amber action pill and a sub line for disclaimers.
- **Sound:** an original music bed written per video at its exact length. Scene changes and the CTA land on the beat, with a drop before the CTA and a chord on it.
  - Risers into big entrances, pops on chips, whooshes on transitions and a low hit on the hook.
  - A synthesised key click for every typed character.
  - Mastered to −14 LUFS with a −1.5 dBTP ceiling. The build reports how hard the limiter worked.

## Templates

| template | scenes | spec fields |
|---|---|---|
| `redesign` | before (old site, pinch-zoom, problem chips) → after (light-sweep to new site, fix chips + rings) → optional dashboard | `before{head, problems[3]}`, `after{head, fixes[3]}`, `dashboard{head, values[3]}` (optional) |
| `local-seo` | search typed → map pack + results, Google's 3 local factors → business profile with 3 tips highlighted | `search{head, note, factors?}`, `profile{head, tips[3]{text, sub, section}}`, `query?` |
| `mistakes` | 3 × (mistake screen → fix screen with highlight) | `items[3]{type, mistake?, fix?}` |
| `before-after` | old desktop site → slider wipe to new → phone version + change chips | `before_head`, `after_head`, `changes[3]` |

All templates take:

- `hook{eyebrow, lines[], accent[]}`. Lines are explicit; keep each one to 18 characters or fewer.
- `cta{headline, action, sub}`.
- `style`: `drive` (118 bpm), `glow` (100 bpm) or `pulse` (124 bpm).
- `seed` (optional).

In any text, `*word*` turns that word amber and `\n` breaks the line. `{business} {short} {label} {city} {query} {category}` are filled in from the niche.

- **Mistake types** (`items[].type`): `hidden-phone`, `no-cta`, `slow`, `not-mobile`, `no-reviews`, `generic-heading`, `wall-of-text`. Each comes with default copy, a bad screen, a fixed screen and a highlight.
- **Profile sections** (`tips[].section`): `category`, `website`, `nap`, `hours`, `photos`, `reviews`, `posts`.
- **Fix rings** (`fixes[].ring` in redesign): `h1`, `btns`, `rev`, `bar`.

## Niches

`niches.json` holds the fictional example businesses shown inside the mockups. Each entry has a name, colours, services, search query and a 555 phone number. The current niches are:

- auto detailing
- landscaping
- plumbing
- dental
- HVAC

To add a niche, copy a block; every template then works for it. No real companies, people or search-engine logos appear anywhere. The search page and business profile are generic layouts.

## Honesty rules (enforced)

`lib/copylint.py` runs on every build and **blocks** guarantee language and promises about rankings, traffic or leads. Examples it blocks:

- "#1 on Google"
- "page one"
- "double your leads"
- "3x more calls"
- "will rank"

A sentence that negates the claim is fine, for example "No one can guarantee rankings". The SEO examples use Google's own stated factors (relevance, distance, prominence) and its Business Profile tips, with a source line on screen. Dashboards are labelled "illustrative data" both inside the mockup and on the canvas. Only override a rule (`"_allow": ["a #1 claim"]`) for a claim that is true and you can source.

## Layout

The canvas safe zone is x 70–1010 and y 220–1560, which keeps text clear of the Reels/TikTok UI.

- Headings sit at y 262 (70/62/56 px depending on length).
- The phone is 520×1040, either centred or beside a chip column.
- The desktop browser is 960 px wide.

Device screens are marked `data-layout-ignore` because they are set dressing. Everything a viewer must read (hook, headings, chips, CTA) is still checked by `hyperframes check` for layout and WCAG contrast.

## Files

```
jtb.py              CLI: spec -> out/<slug>/ (HyperFrames project) -> check -> renders/<slug>.mp4
videos/*.json       one spec per video (8 examples)
niches.json         example businesses
lib/templates.py    the four templates
lib/scenes.py       hook, headings, chips, rings, wipes, typing, brand bar, CTA
lib/mocks.py        device frames, example sites, search page, business profile, dashboard
lib/brand.py        colours, fonts, base CSS, icons
lib/comp.py         composition builder (clips, GSAP lines, sound cues -> index.html)
lib/audio.py        music bed + whoosh synthesis
lib/sfx.py          sound effects synthesis (python3 lib/sfx.py rebuilds brand/sfx)
lib/mix.py          mix, master, loudness/limiter report
lib/copylint.py     claim + length lint
brand/              fonts, JT mark, GSAP, sfx
```

`out/` and `renders/` are build output and are git-ignored.
