"""Prepare the source media for reveal.html.

    python3 tools/reveal/prep_media.py <uploads-dir>

Writes into assets/reveal/media/ (gitignored: personal footage, voice and
product recordings stay out of the repo) and assets/reveal/brand/.
Every crop below is in SOURCE pixels and was read off full-resolution frames.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

UP = sys.argv[1]
SRC = {
    "film": f"{UP}/c40a720f-recording_2.mov",                                   # game film in a film player, 1470x956@30
    "ui":   f"{UP}/a0c50f7a-Screen_Recording_2026-10-13_at_7.24.27PM",          # ScoutCard prototype, 2496x1414@60
    "logo": f"{UP}/0a89b3e6-image.png",                                         # ScoutCard AI logo, 600x600
    "vo1":  f"{UP}/b504cae7-IMG_1996.mov",  # "Introducing Scout Card AI."
    "vo2":  f"{UP}/7d1b0334-IMG_1998.mov",  # "We're working on a way to turn football film into scouting cards, ..."
    "vo3":  f"{UP}/d00069f8-IMG_2001.mov",  # "Still building. This is just the beginning."
}
M = "assets/reveal/media"; B = "assets/reveal/brand"
os.makedirs(M, exist_ok=True); os.makedirs(B, exist_ok=True)
run = lambda *a: subprocess.run(list(a), check=True)
X264 = ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-an"]

# Game film: drop the player chrome (stat bar above, scoreboard + transport below).
run("ffmpeg", "-v", "error", "-y", "-i", SRC["film"], "-vf", "crop=1470:744:0:92,fps=30,setsar=1", *X264, f"{M}/film.mp4")

# Prototype UI shots: exact regions, slowed from 60 fps so every output frame is a real frame.
CARD = "crop=1194:944:300:262"     # the play card
LIST = "crop=690:850:1790:272"     # the script list (highlight steps 01 -> 05)
def shot(name, crop, t0, t1, out_dur):
    k = out_dur / (t1 - t0)
    run("ffmpeg", "-v", "error", "-y", "-ss", f"{t0}", "-to", f"{t1}", "-i", SRC["ui"],
        "-vf", f"{crop},setpts={k:.5f}*(PTS-STARTPTS),fps=30,setsar=1", *X264, f"{M}/{name}.mp4")
shot("ui_card01", CARD, 0.00, 1.18, 1.60)   # card 01, before the first tap
shot("ui_list",   LIST, 0.95, 3.40, 2.60)   # highlight walks 01 -> 02 -> 03 -> 04 -> 05
shot("ui_flip",   CARD, 2.20, 3.45, 1.60)   # taps through card 03 -> 04 -> 05
# Card 05 (Pro Set - PA TE Leak) as a full-resolution still for the hero shot.
run("ffmpeg", "-v", "error", "-y", "-ss", "4.2", "-i", SRC["ui"], "-frames:v", "1", "-vf", CARD, f"{M}/card05.png")

# Logo: lift the orange mark itself from the real logo file (rows above the wordmark,
# whose orange "AI" would otherwise widen the box).
im = np.array(Image.open(SRC["logo"]).convert("RGBA")).astype(int)
orange = (np.arange(im.shape[0])[:, None] < 380) & (im[..., 0] > 200) & (im[..., 1] > 100) & (im[..., 1] < 180) & (im[..., 2] < 110)
ys, xs = np.where(orange)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
Image.open(SRC["logo"]).convert("RGBA").crop((x0, y0, x1, y1)).save(f"{B}/scoutcard-mark.png")
print("mark", (x0, y0, x1, y1), "orange", tuple(np.median(im[orange][:, :3], 0).astype(int)))

# Voiceover: his own takes. Clean, level and trim each; no loudnorm processing (measure only).
def lufs(path, af):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", af + ",loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float(json.loads(o[o.rindex("{"):o.rindex("}") + 1])["input_i"])
PRE = "pan=mono|c0=.5*c0+.5*c1,adeclip,highpass=f=80,afftdn=nr=10:nf=-50,equalizer=f=220:t=q:w=1.2:g=-2,equalizer=f=4200:t=q:w=1.0:g=2"
TRIM = {"vo1": (0.00, 2.20), "vo2": (0.00, 6.95), "vo3": (0.08, 2.25)}   # word bounds + air, from the transcript
for k, (a, b) in TRIM.items():
    g = -18 - lufs(SRC[k], f"atrim={a}:{b},{PRE}")
    run("ffmpeg", "-v", "error", "-y", "-i", SRC[k], "-map", "0:a:0", "-af",
        f"atrim={a}:{b},asetpts=PTS-STARTPTS,{PRE},volume={g:.2f}dB,"
        "acompressor=ratio=2.5:threshold=-24dB:attack=6:release=120,"
        "acompressor=ratio=4:threshold=-14dB:attack=1:release=50:knee=6,"
        "afade=t=in:d=0.012,areverse,afade=t=in:d=0.08,areverse",
        "-ar", "48000", "-c:a", "pcm_s16le", f"{M}/{k}.wav")
    print(k, f"gain {g:+.1f} dB")

# The logo sits on a dark square; clear only the background that touches the
# corners (flood fill), so the black strokes inside the orange tile stay.
from collections import deque
mk = np.array(Image.open(f"{B}/scoutcard-mark.png").convert("RGBA"))
bg = mk[0, 0, :3].astype(int); H, W = mk.shape[:2]
near = np.abs(mk[..., :3].astype(int) - bg).sum(-1) < 60
seen = np.zeros((H, W), bool); q = deque([(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)])
while q:
    y, x = q.popleft()
    if 0 <= y < H and 0 <= x < W and not seen[y, x] and near[y, x]:
        seen[y, x] = True; q.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
# soften the cut edge: partially-blended rim pixels get alpha by distance from the bg colour
d = np.abs(mk[..., :3].astype(int) - bg).sum(-1)
mk[..., 3] = np.where(seen, 0, 255)
rim = (~seen) & (np.roll(seen, 1, 0) | np.roll(seen, -1, 0) | np.roll(seen, 1, 1) | np.roll(seen, -1, 1))
mk[..., 3][rim] = np.clip(d[rim] * 255 // 320, 0, 255)
Image.fromarray(mk).save(f"{B}/scoutcard-mark.png")
print("mark corners cleared:", int(seen.sum()), "px")
