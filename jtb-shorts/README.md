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
- **Body:** a phone mockup inside a camera. The camera punches in on whatever the beat is about (the map, the call button, the booking sheet), so the screen content reads at phone size. Positions come from the real page layout, measured in Chromium at build time.
  - One large callout card at a time, highlight rings, taps, light-sweep screen wipes and a big step numeral (1/2/3) behind the phone.
  - A JT Builds Co. brand bar sits at the top.
  - The example sites have photo-style hero scenes per business type (`lib/art.py`), ratings, hours and real-world microcopy.
- **CTA (last ~3.4 s):** the JT Builds Co. lockup (charcoal tile, JT mark, **BUILDS** white, **CO.** grey), the ask, an amber action pill and a sub line for disclaimers.
- **Sound:** **no music by default**, so you can add one consistent track to the whole series in CapCut. Exports carry sound effects only:
  - Risers into big entrances, pops on callouts, whooshes on transitions, taps and a low hit on the hook and end card.
  - A synthesised key click for every typed character.
  - The effects keep the level they were designed at under a −14 LUFS song (about −22 LUFS on their own), so a normally loud track drops in balanced.
  - Set `"music": true` in a spec to bring back the built-in original bed. Scene changes then snap to its beat and the mix is mastered to −14 LUFS.

## Templates

| template | scenes | spec fields |
|---|---|---|
| `redesign` | before (old site, pinch-zoom, problems) → after (light-sweep to the new site, fixes with punch-ins) → optional booking (tap, pick a time, confirmed) | `before{head, problems[2]}`, `after{head, fixes[2-3]{text, sub}}`, `booking?{head, callout, sub}` |
| `local-seo` | search typed → results → one beat per Google local factor: relevance (your listing, matching words marked), distance (rings from the searcher, "you can't control this"), prominence (ratings + review counts) | `search{head}`, `factors?[3]{head, callout, sub}`, `query?` |
| `gbp-tips` | three Business Profile improvements, each shown happening: real job photos land, the owner's reply types out, hours get corrected and marked updated | `tips?[3]{eyebrow, head, callout, sub, reply}` |
| `mistakes` | 3 × (numbered mistake → fix, punched in on what changed) | `items[3]{type, mistake?, fix?, why?}` |
| `before-after` | old desktop site → slider wipe to new → phone version + change chips | `before_head`, `after_head`, `changes[3]` |

All templates take:

- `hook{eyebrow, lines[], accent[]}`. Lines are explicit; keep each one to 18 characters or fewer.
- `cta{headline, action, sub}`.
- `music` (default `false`). With music on, `style` picks the bed: `drive` (118 bpm), `glow` (100 bpm) or `pulse` (124 bpm).
- `seed` (optional).

In any text, `*word*` turns that word amber and `\n` breaks the line. `{business} {short} {label} {city} {query} {category}` are filled in from the niche.

- **Mistake types** (`items[].type`): `hidden-phone`, `no-cta`, `slow`, `not-mobile`, `no-reviews`, `generic-heading`, `wall-of-text`. Each comes with default copy, a bad screen, a fixed screen and a highlight.
- **Using your own work:** to show real sites instead of the examples, put screenshots in `brand/photos/` and swap the `scene()` art in `lib/sites.py` for an `<img>`. The layouts don't care which they get.

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
lib/templates.py    the templates
lib/scenes.py       hook, headings, callouts, rings, wipes, typing, taps, camera, brand bar, CTA
lib/sites.py        the example mobile site, booking sheet, local results page, Business Profile
lib/art.py          photo-style hero scenes per business type (inline SVG)
lib/mocks.py        device frames, old-site / desktop / slow-page mockups, dashboard
lib/measure.js      build-time layout measurement the camera aims with
lib/brand.py        colours, fonts, base CSS, icons
lib/comp.py         composition builder (clips, GSAP lines, sound cues -> index.html)
lib/audio.py        music bed + whoosh synthesis
lib/sfx.py          sound effects synthesis (python3 lib/sfx.py rebuilds brand/sfx)
lib/mix.py          mix, master, loudness/limiter report
lib/copylint.py     claim + length lint
brand/              fonts, JT mark, GSAP, sfx
```

`out/` and `renders/` are build output and are git-ignored.
