# Panda Sports Collectibles: Ja'Marr Chase jersey reel

An 11.5 s vertical (1080×1920) reel built from one photo of the owner's signed, framed jersey.

```bash
python3 tools/beat.py && python3 build.py
npx --yes hyperframes@0.8.154 check .
npx --yes hyperframes@0.8.154 render . -o renders/panda-chase-reel.mp4 -q delivery
ffmpeg -i renders/panda-chase-reel.mp4 -i assets/mix-fx.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/panda-chase-reel-fx.mp4
```

## Photos (not committed)

The images live in `assets/photos/`.

| File | What it is |
|---|---|
| `chase-framed.jpg` | The owner's photo. |
| `logo.png` | The Panda logo. |
| `logo-badge.png` | A crop of the logo. |
| `bg.jpg` | The photo, blurred and dimmed, used as the backdrop behind the pulled-back shots. |

Every shot is a crop of the one photo, moved with scale and position only. Nothing is retouched, redrawn or generated.

## Timeline (120 BPM, so every cut sits on the beat)

| Time | Shot | Text |
|---|---|---|
| 0–2 s | The jersey fills the frame. | JA’MARR CHASE FANS 👀 (in a native caption style) |
| 2–4 s | A smooth push onto the number and the autograph. | – |
| 4–7 s | Close-ups: the autograph (tilt), CHASE nameplate (track), sleeve stripes, frame corner, the autograph and its sticker. | – |
| 7–9 s | Pull back to the whole framed piece, with a light pass. | SIGNED. FRAMED. READY TO DISPLAY. |
| 9–11.5 s | Panda logo. | OWN A PIECE OF FOOTBALL HISTORY · pandasportsmemorabilia.com |

There are no prices, discounts, scarcity or authentication claims.

## Sound

- **`panda-chase-reel.mp4`:** an original 120 BPM beat in F minor (`tools/beat.py`, synthesised, no samples) plus impacts, hits, ticks and a riser. Mastered to −14 LUFS.
- **`panda-chase-reel-fx.mp4`:** the same picture with the sound effects only, for adding a trending sound in Instagram. The effects sit at the same level.
