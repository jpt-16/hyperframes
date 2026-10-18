"""Panda Sports Collectibles: signed + framed Ja'Marr Chase jersey reel (1080x1920, 11.5 s).

    python3 tools/beat.py && python3 build.py
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/panda-chase-reel.mp4 -q delivery
    # the same picture with sound effects only, for laying a trending sound in Instagram:
    ffmpeg -i renders/panda-chase-reel.mp4 -i assets/mix-fx.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/panda-chase-reel-fx.mp4

Everything on screen is the owner's one photo (assets/photos/chase-framed.jpg): every shot is a crop of it
with camera moves (scale and position only). Nothing in the photo is retouched, redrawn or generated.
The backdrop behind the pulled-back shots is the same photo, blurred and dimmed.

0.0-2.0   the jersey fills the frame, hook "JA'MARR CHASE FANS 👀" (native caption style: reads as a post, not an ad)
2.0-4.0   a smooth push-in onto the number and the autograph
4.0-7.0   close-ups cut on the beat: autograph, nameplate, sleeve stripes, frame corner, autograph + sticker
7.0-9.0   pull back to the whole framed piece: SIGNED. FRAMED. READY TO DISPLAY.
9.0-11.5  Panda Sports Collectibles logo, "Own a piece of football history", pandasportsmemorabilia.com
No prices, discounts, scarcity or authentication claims.
"""
import os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

D, FPS = 11.5, 30
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

# ----------------------------------------------------------------- 0-2 hook: the jersey fills the frame
shot(0.0, 2.0, (1190, 985, 1000), (1190, 1000, 930), ease="none")
c.clip("hook", 0, 2.0, '<div class="hook"><span>JA’MARR CHASE FANS 👀</span></div>', cls="layer", style="z-index:20")

# ----------------------------------------------------------------- 2-4 smooth push onto the number + autograph
c.to("#ph", o(**cam(1205, 1265, 520), duration=1.85, ease="power3.inOut"), 2.0)

# ----------------------------------------------------------------- 4-7 close-ups, one per beat
shot(4.0, 5.0, (1205, 1150, 360), (1205, 1400, 330))                 # the autograph, tilting down it
shot(5.0, 5.5, (1010, 690, 560), (1350, 690, 530))                   # CHASE nameplate, tracking across
shot(5.5, 6.0, (1950, 470, 440), (1995, 520, 390))                   # sleeve stripes
shot(6.0, 6.5, (330, 570, 640), (305, 540, 590))                     # frame corner: black frame, deep white mat
shot(6.5, 7.0, (1205, 1330, 470), (1205, 1300, 410))                 # back to the autograph and its sticker

# ----------------------------------------------------------------- 7-9 pull back to the whole framed piece
c.to("#ph", o(**FIT, duration=0.62, ease="power3.inOut"), 7.0)
c.clip("rev", 7.0, 9.0, '<div class="rv"><div class="l1"><span id="w1">SIGNED.</span> <span id="w2">FRAMED.</span></div>'
       '<div class="l2" id="w3">READY TO DISPLAY.</div></div>', cls="layer", style="z-index:20")
for wid, t in [("#w1", 7.6), ("#w2", 8.0), ("#w3", 8.4)]:
    c.set(wid, o(opacity=0), 7.0)
    c.ft(wid, o(opacity=1, scale=1.12), o(scale=1, duration=0.22, ease="power3.out", immediateRender=False), t)
c.clip("sw", 7.55, 8.4, '<i class="sweep" id="sweep"></i>', cls="layer", style="z-index:3")
c.ft("#sweep", o(xPercent=-120), o(xPercent=120, duration=0.8, ease="power2.inOut"), 7.58)
c.to("#ph", o(**cam(PW / 2, PH / 2 + (960 - 900) / (1080 / PW / 1.025), PW / 1.025), duration=2.3, ease="none"), 7.65)

# ----------------------------------------------------------------- 9-11.5 brand, line, site
c.clip("end", 9.0, D, '<img class="logo" id="logo" src="assets/photos/logo-badge.png" alt="Panda Sports Collectibles">'
       '<div class="tag" id="tag">OWN A PIECE OF FOOTBALL HISTORY</div>'
       '<div class="url" id="url">pandasportsmemorabilia.com</div>', cls="layer", style="z-index:20")
c.ft("#logo", o(opacity=0, scale=1.08), o(opacity=1, scale=1, duration=0.3, ease="power3.out"), 9.0)
c.set("#tag", o(opacity=0), 9.0); c.ft("#tag", o(opacity=1, y=16), o(y=0, duration=0.25, ease="power3.out", immediateRender=False), 9.5)
c.set("#url", o(opacity=0), 9.0); c.ft("#url", o(opacity=1, scale=1.08), o(scale=1, duration=0.25, ease="power3.out", immediateRender=False), 10.0)

# ----------------------------------------------------------------- sound: the beat + hits on the picture's moments
for name, t, gdb in [("impact", 0.0, -8), ("riser-l", 3.875, -6), ("whoosh", 2.25, -12),
                     ("impact", 4.0, -3), ("hit", 4.0, -6),
                     ("tick", 5.0, -6), ("tick", 5.5, -6), ("tick", 6.0, -6), ("tick", 6.5, -6),
                     ("whoosh", 7.25, -8), ("hit", 7.6, -8), ("hit", 8.0, -8), ("hit", 8.4, -6),
                     ("impact", 9.0, -4), ("tick", 10.0, -8)]:
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

/* native caption style: the hook reads like a post, not an ad */
.hook {{ position:absolute; left:0; right:0; top:300px; display:flex; justify-content:center; }}
.hook span {{ display:inline-block; padding:16px 28px 18px; border-radius:16px; background:#fff; color:#0A0A0A;
              font-family:"Inter", sans-serif; font-weight:800; font-size:70px; letter-spacing:-.01em; line-height:1.1; white-space:nowrap;
              box-shadow:0 8px 30px rgba(0,0,0,.25); }}

.rv {{ position:absolute; left:40px; right:40px; top:150px; text-align:center; font-family:"Anton", sans-serif; color:#fff;
       text-shadow:0 6px 30px rgba(0,0,0,.55); }}
.rv .l1 {{ font-size:138px; line-height:1.0; letter-spacing:.01em; }}
.rv .l1 span {{ display:inline-block; }}
.rv .l2 {{ font-size:96px; line-height:1.05; color:{G}; margin-top:8px; letter-spacing:.02em; }}
.sweep {{ position:absolute; left:0; top:{900 - 445}px; width:1080px; height:890px; mix-blend-mode:screen; opacity:.5;
          background:linear-gradient(105deg, rgba(255,255,255,0) 35%, rgba(255,255,255,.22) 50%, rgba(255,255,255,0) 65%); }}

.logo {{ position:absolute; left:{540 - 230}px; top:78px; width:460px; height:auto; mix-blend-mode:screen; }}
.tag {{ position:absolute; left:40px; right:40px; top:1374px; text-align:center; font-family:"Barlow Condensed", sans-serif; font-weight:800;
        font-size:70px; letter-spacing:.03em; color:#fff; line-height:1; }}
.url {{ position:absolute; left:0; right:0; top:1462px; margin:0 auto; width:max-content; padding:16px 34px 18px; border-radius:999px;
        background:{G}; color:#031003; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:54px; letter-spacing:.02em; line-height:1; }}
"""

if __name__ == "__main__":
    h = c.page(CSS, "Panda Sports Collectibles · Ja'Marr Chase jersey", script=True)
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m, f = mixdown()
    print(f"index.html: {D}s, {len(c.cues)} sound cues; with beat {m['lufs']} LUFS / {m['true_peak']} dBTP (dips {m['aac_dips']}); "
          f"fx only {f['lufs']} LUFS / {f['true_peak']} dBTP")
