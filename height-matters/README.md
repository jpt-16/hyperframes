# "Does height matter in baseball?"

A 40.4 s vertical (1080×1920, 30 fps) 3D video for Baseball Decoded. It opens with the 2026 World Series (Brewers vs. Rays) and asks whether height matters in baseball.

**Framework:** the same three.js field, player rig and HyperFrames workflow as `hit-and-run`, `infield-fly`, `tommy-john` and `intentional-walk`.

**New in this video:**
- Brewers- and Rays-inspired kits (team colors, a belt in the accent color, no names or logos) and World Series bunting on the dugouts.
- Players scaled to illustrative heights (and widths, for builds).
- A 6 ft reference line, seen with the camera at exactly 6 ft, so anyone taller pokes above it and anyone shorter sits below.
- Two simulated fastballs from different release heights.
- Strike zones measured on the posed hitters.
- A shortstop's low fielding stance.
- A builds-by-position lineup and a study card.

**Voiceover:** your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.65× to land at about 40 s); the text is in `transcript.txt`.
- Shots, word-by-word captions, pins and reveals are keyed to its words.
- Big titles replace captions for:
  - the hook (**DOES HEIGHT ACTUALLY MATTER IN BASEBALL?**)
  - "So does height actually matter"
  - "The takeaway?"
  - the last line (**TALENT DOESN'T COME IN ONE SIZE.**)

**Sound:**
- **Music:** a `make_bed` bed (style "drive"), ducked up to 7 dB under the voice.
- **Effects:** whooshes on cuts, glove pops, a bat crack, and hits on the titles.
- **Mixes:** mastered to about −14 LUFS. `assets/mix-novo.wav` is the music and effects without the voice.

```bash
python3 tools/physics.py                                       # the two fastballs, the ground ball, the line drive -> assets/play.json
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav)
npx --yes hyperframes@0.8.154 render . -o renders/height-matters.mp4 --video-bitrate 16M
```

## Accuracy notes

- **No invented heights or stats.**
  - The figures stand for no real player; no figure carries a height or a name.
  - The only numbers on screen come from the script or the cited sources, plus the simulation's own output:
    - one Rays starter over 6 ft, marked "per reports"
    - the 2023 study's 319 first-round picks and its 2005–2015 draft range
    - the 6 ft reference line
    - the simulated pitch's entry angles
- **Lineup heights are illustrative.** One Rays-inspired figure stands over the line and the other eight below it, to match the script's claim; the Brewers-inspired line is mixed. The exact heights are made up for the picture and labeled "heights illustrative".
- **Release point (simulated):**
  - The same 94 mph four-seam fastball (2300 rpm) is aimed at the same spot (middle of the plate, 2.5 ft up) from two releases: 6.6 ft up with 7 ft of extension, and 5.6 ft up with 6 ft.
  - Gravity, drag and spin lift are modeled.
  - It comes in at 5.8° from the higher release vs. 4.7° from the lower one. Those are the simulation's numbers, not a stat; the screen says "simulated".
  - The tall pitcher is sized so his hand is at the high release point when he lets go.
- **Strike zone:**
  - The rulebook definition is used: from the midpoint between the tops of the shoulders and the top of the uniform pants, down to the hollow beneath the kneecap, in the batting stance.
  - It is measured on the posed 5′7″-scale and 6′7″-scale figures (illustrative scales), so the shorter hitter's zone is shorter and its bottom sits lower.
- **The study:** "Anthropometric Evaluation of First Round Draft Selections in Major League Baseball", *Journal of Strength and Conditioning Research*, 2023 ([PubMed 36727719](https://pubmed.ncbi.nlm.nih.gov/36727719/)).
  - It covers 319 first-round picks from the 2005–2015 drafts.
  - It compares high-school height, weight and BMI against MLB WAR and found no relationship.
- **Even-handed portrayal:** the shorter players get the strike-zone and fielding advantages, and the montage alternates elite plays:
  - a taller pitcher's delivery
  - a shorter hitter's line drive
  - a shorter shortstop fielding low
  - a taller first baseman's stretch

## Shots (timed to the voiceover)

| Time | Line | Shot | On screen |
|---|---|---|---|
| 0–3.5 s | "The 2026 World Series is challenging…" | Eye level at 6 ft down a lineup on the third-base line; rings light up the shorter players at 1.0 s | **DOES HEIGHT ACTUALLY MATTER IN BASEBALL?**; "Yellow line: 6 ft" |
| 3.5–6.8 s | "The Brewers and Rays have some of the shortest lineups…" | From behind the mound: both teams on the foul lines | "2026 World Series · Brewers vs. Rays"; Brewers/Rays pins |
| 6.8–9.7 s | "…the Rays' starting lineup has just one player taller than six feet." | Eye level at 6 ft down the Rays-inspired line; one figure over the line, ringed on "one" | "1 of 9 over 6 ft"; "per reports" |
| 9.7–11.3 s | "So does height actually matter in baseball?" | High over both lines | **SO DOES HEIGHT ACTUALLY MATTER** |
| 11.3–13.2 s | "Being taller can give players longer levers…" | A taller and a shorter player reach up; bars mark each arm | "Longer arms: longer levers" |
| 13.2–15.0 s | "…pitchers may benefit from a higher release point." | Behind the plate: the tall pitcher delivers; two tubes from the two release points converge on the same spot | "Higher release" / "Lower release"; "Same pitch, same target: a steeper angle in" |
| 15.0–16.8 s | "But being shorter can come with advantages too." | Low, in front of a shorter hitter in his stance | captions |
| 16.8–18.7 s | "A shorter hitter may have a smaller strike zone…" | Behind the plate: his zone (yellow) and a taller hitter's (dashed) | zone labels; the rulebook definition |
| 18.7–21.2 s | "…shorter infielders can benefit from getting lower to the ground." | Low beside the shortstop as he gets down on a ground ball | "Gets low" |
| 21.2–31.8 s | "And the research is interesting." / the 2023 study | Different builds by position (C, 1B, SS, CF, P); the study card builds word by word | 319 count-up, "High-school height · weight · BMI", "MLB performance (WAR)", **NO RELATIONSHIP FOUND** |
| 31.8–32.5 s | "The takeaway?" | High over the field | **THE TAKEAWAY?** |
| 32.5–36.2 s | "Height can influence… how good they become." | Montage: taller pitcher, shorter hitter's line drive, shorter shortstop, taller first baseman's stretch | pins on each |
| 36.2–40.4 s | "The Brewers and Rays are proving that talent doesn't come in one size." | Both teams on the lines | **TALENT DOESN'T COME IN ONE SIZE.** |
