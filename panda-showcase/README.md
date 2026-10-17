# Panda Sports Collectibles: helmet showcase

A 24.6 s vertical (1080×1920) product showcase built only from the owner's own photos. Every shot uses crops, scale, motion, light pools and light passes, and nothing more. No helmet, signature or document is redrawn or regenerated.

```bash
python3 tools/sfx.py        # (re)make the sound effects
python3 build.py            # write index.html + assets/mix.wav
npx --yes hyperframes@0.8.154 check .
npx --yes hyperframes@0.8.154 render . -o renders/panda-helmets-showcase.mp4 -q delivery
```

The photos go in `assets/photos/` and are not committed:

- `logo.png`
- `qb-angle.jpg`
- `qb-side-dark.jpg`
- `qb-side-grey.jpg`
- `shula-a.jpg`
- `shula-b.jpg`
- `loa-qb.jpg`

To add the Shula letter of authenticity, save it as `assets/photos/loa-shula.jpg` and rebuild.

## What is on screen, and where it comes from

| Claim | Source |
|---|---|
| NFL Quarterback Legends, multi-signed full-size Riddell helmet, 7 signatures | JSA LOA |
| The seven names | JSA LOA. Elway, Manning, Favre and Staubach are labelled on their own signatures. Montana, Young and Marino are shown together in one close-up, so no signature is matched to a name the photo can't confirm. |
| Cert # ZZ16896 | JSA LOA |
| Don Shula, "H.O.F. 97" | written on the helmet |
| JSA sticker YY62600 | sticker on the helmet, number confirmed by the owner |

There are no prices, discounts or scarcity claims anywhere in the video.

## Sound

The track carries sound effects only: impacts, hits, risers, whooshes and close-up ticks. All of them are original and synthesised in `tools/sfx.py`. The loudest hit peaks at about −2.5 dBFS. Add your music track in CapCut and line up its big moments with these hits:

| Time | Moment |
|---|---|
| 0.0 / 0.3 / 1.0 s | SEVEN / LEGENDS. / ONE HELMET. |
| 2.4 s | helmet reveal |
| 5.3, 6.5, 7.7, 8.9, 10.1 s | signature close-ups |
| 11.3 s | JSA letter lands |
| 14.5 s | Don Shula reveal |
| 18.3 s / 18.75 s | both helmets in / AUTHENTIC MEMORABILIA |
| 21.0 s | logo and call to action (holds to the end) |
