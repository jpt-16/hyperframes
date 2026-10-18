# Panda Sports Collectibles: Ja'Marr Chase jersey reel

A 10 s vertical (1080×1920) reel built from one photo of the owner's signed, framed jersey.

```bash
python3 tools/beat.py && python3 build.py
npx --yes hyperframes@0.8.154 check .
npx --yes hyperframes@0.8.154 render . -o renders/panda-chase-reel-v2.mp4 -q delivery
ffmpeg -i renders/panda-chase-reel-v2.mp4 -i assets/mix-fx.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart renders/panda-chase-reel-v2-fx.mp4
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

## Timeline (v2: 120 BPM, so every cut sits on the beat)

| Time | Shot | Text |
|---|---|---|
| 0–1 s | The whole framed jersey from the first frame, with a fast, subtle push-in. | WOULD YOU PUT THIS IN YOUR COLLECTION? |
| 1–2 s | A cut to the autograph, tilting down it. | (hook stays on) |
| 2–5 s | Cuts every 0.5 s, each showing something new: the full jersey, the CHASE nameplate, the end of the autograph and its sticker, the sleeve stripes, the frame corner, the whole autograph. | – |
| 5–6.5 s | Pull back to the whole framed piece. | SIGNED. FRAMED. READY TO DISPLAY. |
| 6.5–10 s | The photo melts into its blurred backdrop: Panda logo and the line. The website appears at 6.75 s and holds for 3.25 s. | OWN A PIECE OF FOOTBALL HISTORY · pandasportsmemorabilia.com |

There are no prices, discounts, scarcity or authentication claims.

## Sound

- **`panda-chase-reel-v2.mp4`:** an original 120 BPM beat in F minor (`tools/beat.py`, synthesised, no samples) plus impacts, hits and ticks. It is energetic from the first frame, has no silent gaps, drops at 2 s and ends with a hit at 9.5 s. Mastered to −14 LUFS.
- **`panda-chase-reel-v2-fx.mp4`:** the same picture with the sound effects only, for adding a trending sound in Instagram. The effects sit at the same level.
