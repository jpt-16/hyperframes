"""Panda Sports Collectibles: signed + framed Ja'Marr Chase jersey reel (1080x1920, 10 s).

    python3 tools/beat.py && python3 build.py
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/panda-chase-reel-v2.mp4 -q delivery
    # the same picture with sound effects only, for laying a trending sound in Instagram:
    ffmpeg -i renders/panda-chase-reel-v2.mp4 -i assets/mix-fx.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart renders/panda-chase-reel-v2-fx.mp4

Everything on screen is the owner's one photo (assets/photos/chase-framed.jpg): every shot is a crop of it
with camera moves (scale and position only). Nothing in the photo is retouched, redrawn or generated.
The backdrop behind the pulled-back shots is the same photo, blurred and dimmed.

0.0-2.0   the whole framed jersey from frame one under "WOULD YOU PUT THIS IN YOUR COLLECTION?", a fast push,
          then a cut to the autograph
2.0-5.0   beat-synced cuts (every 0.5 s), each showing something new: full jersey, nameplate, autograph end + sticker,
          sleeve stripes, frame corner, the whole autograph
5.0-6.5   pull back to the whole framed piece: SIGNED. FRAMED. READY TO DISPLAY.
6.5-10.0  Panda logo, OWN A PIECE OF FOOTBALL HISTORY, pandasportsmemorabilia.com (the site holds 3.25 s)
No prices, discounts, scarcity or authentication claims.
"""
import os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

D, FPS = 10.0, 30
G = "#00C820"                      # Panda green, sampled from the logo
PW, PH = 2377, 1956                # the photo
c = Comp(D, FPS)

def cam(cx, cy, w):
    """Camera framing: photo point (cx, cy) at the centre of the 1080x1920 frame, w photo-px across."""
    s = 1080 / w
    return dict(x=round(540 - s * cx, 2), y=round(960 - s * cy, 2), scale=round(s, 5))

FIT = cam(PW / 2, PH / 2 + (960 - 900) / (1080 / PW), PW)     # whole photo, full width, centred at y 900

def shot(t0, t1, a, b, ease="power2.inOut"):
    """A hard cut to framing a at t0, moving to framing b by t1."""
    c.set("#ph", o(**cam(*a)), t0)
    c.to("#ph", o(**cam(*b), duration=round(t1 - t0, 3), ease=ease), t0)

c.clip("bgl", 0, D, f'<img id="bg" src="assets/photos/bg.jpg" alt="">', cls="layer", style="z-index:1")
c.clip("caml", 0, D, f'<img id="ph" data-layout-allow-overflow src="assets/photos/chase-framed.jpg" alt="Signed and framed Ja\'Marr Chase #1 jersey">',
       cls="layer", style="z-index:2")

# ----------------------------------------------------------------- 0-2 hook: the whole framed jersey, a fast push, then the autograph
c.set("#ph", o(**FIT), 0.0)
c.to("#ph", o(**cam(1190, 1060, 1500), duration=1.0, ease="power2.in"), 0.0)        # subtle, fast push-in
shot(1.0, 2.0, (1205, 1215, 420), (1205, 1330, 370))                               # cut: the autograph (curiosity)
c.clip("hook", 0, 2.0, '<div class="hook"><div>WOULD YOU PUT THIS</div><div>IN YOUR <em>COLLECTION?</em></div></div>',
       cls="layer", style="z-index:20")
c.clip("hook-sh", 0, 2.0, '<i class="topshade"></i>', cls="layer", style="z-index:19")

# ----------------------------------------------------------------- 2-5.5 beat-synced cuts: every shot shows something new
CUTS = [
    ((1190, 990, 1000), (1190, 1005, 940)),     # 2.0 the full jersey
    ((1010, 690, 560), (1350, 690, 530)),       # 2.5 CHASE nameplate, tracking across
    ((1205, 1470, 360), (1205, 1430, 330)),     # 3.0 the end of the autograph and its sticker
    ((1950, 470, 440), (1995, 520, 390)),       # 3.5 sleeve stripes
    ((330, 570, 640), (305, 540, 590)),         # 4.0 frame corner: black frame, deep white mat
    ((1205, 1270, 600), (1205, 1270, 540)),     # 4.5 the whole autograph on the number
]
for k, (a_, b_) in enumerate(CUTS):
    shot(2.0 + 0.5 * k, 2.5 + 0.5 * k, a_, b_)

# ----------------------------------------------------------------- 5.0-6.5 pull back to the whole framed piece
c.to("#ph", o(**FIT, duration=0.5, ease="power3.inOut"), 5)
c.clip("rev", 5, 6.5, '<div class="rv"><div class="l1"><span id="w1">SIGNED.</span> <span id="w2">FRAMED.</span></div>'
       '<div class="l2" id="w3">READY TO DISPLAY.</div></div>', cls="layer", style="z-index:20")
for wid, t in [("#w1", 5.5), ("#w2", 5.75), ("#w3", 6)]:
    c.set(wid, o(opacity=0), 5)
    c.ft(wid, o(opacity=1, scale=1.12), o(scale=1, duration=0.2, ease="power3.out", immediateRender=False), t)
c.to("#ph", o(**cam(PW / 2, PH / 2 + (960 - 900) / (1080 / PW / 1.02), PW / 1.02), duration=0.95, ease="none"), 5.55)

# ----------------------------------------------------------------- 6.5-10 end: brand, one line, the site (on screen 3.25 s)
c.to("#ph", o(opacity=0, duration=0.3, ease="power1.inOut"), 6.4)                    # the photo melts into its blurred backdrop
c.clip("end", 6.4, D, '<img class="logo" id="logo" src="assets/photos/logo-badge.png" alt="Panda Sports Collectibles">'
       '<div class="tag" id="tag">OWN A PIECE OF<br>FOOTBALL HISTORY</div>'
       '<div class="url" id="url">pandasportsmemorabilia.com</div>', cls="layer", style="z-index:20")
c.ft("#logo", o(opacity=0, scale=0.94), o(opacity=1, scale=1, duration=0.35, ease="power3.out"), 6.45)
c.ft("#tag", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.3, ease="power3.out"), 6.5)
c.ft("#url", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.3, ease="power3.out"), 6.75)

# ----------------------------------------------------------------- sound: the beat + hits on the picture's moments
for name, t, gdb in [("impact", 0.0, -8), ("hit", 1.0, -7), ("impact", 2.0, -5),
                     *[("tick", 2.5 + 0.5 * k, -8) for k in range(5)],
                     ("whoosh", 5.25, -9), ("hit", 5.5, -9), ("hit", 5.75, -9), ("hit", 6, -7),
                     ("impact", 6.5, -5), ("tick", 6.75, -9)]:
    c.cue(name, t, gdb)

def mixdown():
    L = int(round(D * SR)); fx = np.zeros((L, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(L, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** (gdb / 20)
    beat = read(os.path.join(HERE, "assets", "beat.wav"))[:L]
    full = fx.copy(); full[: len(beat)] += beat
    def wr(p, x):
        w = wave.open(p, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, fxp = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wr(pre, full); wr(fxp, fx)
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    f = master(pre, os.path.join(HERE, "assets", "mix-fx.wav"), fx_path=fxp)       # same gain, sounds only
    os.remove(pre); os.remove(fxp)
    return m, f

CSS = f"""
@font-face {{ font-family:"Anton"; src:url("assets/fonts/Anton-400.woff2") format("woff2"); font-display:block; }}
@font-face {{ font-family:"Barlow Condensed"; font-weight:700; src:url("assets/fonts/BarlowCondensed-700.woff2") format("woff2"); font-display:block; }}
@font-face {{ font-family:"Barlow Condensed"; font-weight:800; src:url("assets/fonts/BarlowCondensed-800.woff2") format("woff2"); font-display:block; }}
@font-face {{ font-family:"Inter"; font-weight:800; src:url("assets/fonts/Inter-800-latin.woff2") format("woff2"); font-display:block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#050505; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#050505; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#bg {{ position:absolute; inset:0; width:1080px; height:1920px; }}
#ph {{ position:absolute; left:0; top:0; width:{PW}px; height:{PH}px; transform-origin:0 0; max-width:none; }}
#vignette {{ position:absolute; inset:0; pointer-events:none; z-index:10;
             background:radial-gradient(ellipse 95% 75% at 50% 50%, rgba(0,0,0,0) 60%, rgba(0,0,0,.38) 100%); }}

/* hook: big, bold, two lines above the framed piece */
.hook {{ position:absolute; left:30px; right:30px; top:176px; text-align:center; font-family:"Anton", sans-serif; font-size:104px; line-height:1.02;
         letter-spacing:.005em; color:#fff; text-shadow:0 4px 0 rgba(0,0,0,.35), 0 10px 40px rgba(0,0,0,.6); }}
.hook em {{ font-style:normal; color:{G}; }}
.topshade {{ position:absolute; left:0; right:0; top:0; height:620px; background:linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,.35) 55%, rgba(0,0,0,0) 100%); }}

.rv {{ position:absolute; left:40px; right:40px; top:150px; text-align:center; font-family:"Anton", sans-serif; color:#fff;
       text-shadow:0 6px 30px rgba(0,0,0,.55); }}
.rv .l1 {{ font-size:138px; line-height:1.0; letter-spacing:.01em; }}
.rv .l1 span {{ display:inline-block; }}
.rv .l2 {{ font-size:96px; line-height:1.05; color:{G}; margin-top:8px; letter-spacing:.02em; }}

.logo {{ position:absolute; left:{540 - 270}px; top:300px; width:540px; height:auto; mix-blend-mode:screen;
         -webkit-mask-image:linear-gradient(90deg, transparent 0%, #000 7%, #000 93%, transparent 100%), linear-gradient(180deg, transparent 0%, #000 8%, #000 92%, transparent 100%);
         -webkit-mask-composite:source-in; mask-composite:intersect; }}
.tag {{ position:absolute; left:40px; right:40px; top:790px; text-align:center; font-family:"Anton", sans-serif; font-size:118px; line-height:1.04;
        letter-spacing:.01em; color:#fff; text-shadow:0 8px 34px rgba(0,0,0,.55); }}
.url {{ position:absolute; left:0; right:0; top:1100px; margin:0 auto; width:max-content; padding:24px 44px 26px; border-radius:999px;
        background:{G}; color:#031003; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:68px; letter-spacing:.02em; line-height:1; }}
"""

if __name__ == "__main__":
    h = c.page(CSS, "Panda Sports Collectibles · Ja'Marr Chase jersey", script=True)
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m, f = mixdown()
    print(f"index.html: {D}s, {len(c.cues)} sound cues; with beat {m['lufs']} LUFS / {m['true_peak']} dBTP (dips {m['aac_dips']}); "
          f"fx only {f['lufs']} LUFS / {f['true_peak']} dBTP")
