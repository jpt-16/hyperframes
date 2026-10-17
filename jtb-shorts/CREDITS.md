# Credits and licences

## Audio — all original

Every sound in these videos is synthesised by code in this folder with fixed seeds. There are no samples, stock music or third-party audio, so it is free to publish on Instagram, TikTok and YouTube without a licence or Content ID claims.

- **Music bed:** `lib/audio.py` (`make_bed`). A new one is written for every video at its exact length.
- **Sound effects:** `lib/sfx.py`. This covers the risers, popup, bubble, land, whoosh, tap and the per-character key clicks.
- **Default exports have no music.** The bed is only used offline as a level reference.

To use a licensed track instead, replace `assets/mix.wav` in a built project. Keep the length the same, and the CTA should land on a strong beat at the time shown in `build.json`.

## Fonts

All are SIL Open Font License 1.1, from Google Fonts:

- Montserrat (the JT Builds Co. wordmark face)
- Inter
- Fraunces (used only in the deliberately dated "old website" mockup)

## Code

- GSAP (`brand/gsap.min.js`): standard "no charge" GSAP licence.

## Brand

- The JT mark (`brand/jt-mark.png`) belongs to JT Builds Co.

## Mockup content

The photo-style scenes in the example sites are original illustrations drawn in code (`lib/art.py`).


All businesses, phone numbers (555), addresses, reviews and dashboard numbers are fictional examples. The search page and business profile are generic layouts with no third-party logos.
