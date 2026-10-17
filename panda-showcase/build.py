"""Panda Sports Collectibles: helmet showcase (1080x1920, ~25 s, sound effects only).

    python3 build.py && npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/panda-helmets.mp4 -q delivery

Every product shot is the owner's own photo, used as-is: crops, scale, motion,
masks and light passes only. Nothing about a helmet, a signature or the letter
is redrawn or regenerated. Every name, number and description on screen comes
from the JSA letter or from what is legibly written on the item:
  - QB helmet: JSA LOA, cert ZZ16896, "NFL Quarterback Legends",
    "Multi-Signed Full-Size Helmet", Riddell, 7 signatures (names as listed).
  - Shula helmet: signature + "H.O.F. 97" inscription on the helmet; JSA sticker,
    number YY62600 as confirmed by the owner. No LOA shown until one is supplied
    (drop it in as assets/photos/loa-shula.jpg and rebuild).
No prices, discounts or scarcity claims anywhere.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, R, esc
from mix import read, codec_safe, measure, ANCHOR

FPS = 30
G = "#00C820"            # Panda green, sampled from the logo
G2 = "#3BFF5E"           # its glow
P = "assets/photos/"
IMG = {  # natural sizes of the owner's photos
    "qb-angle": (1932, 2576), "qb-dark": (2016, 1512), "shula": (2016, 1512), "loa": (1512, 2016), "logo": (852, 1846)}
SHULA_LOA = os.path.exists(os.path.join(HERE, P, "loa-shula.jpg"))

# ----------------------------------------------------------------- timing (seconds)
T = dict(hook=0.0, reveal=2.4, sig=5.3, loa=11.3, shula=14.5, both=18.3, cta=21.0)
D = 24.6
SIGS = [  # (id, name lines, crop centre x, y and width in qb-angle.jpg pixels)
    ("s1", ["JOHN ELWAY"], 780, 320, 560),
    ("s2", ["PEYTON MANNING"], 890, 710, 640),
    ("s3", ["BRETT FAVRE"], 665, 1300, 520),
    ("s4", ["ROGER STAUBACH"], 570, 1520, 640),
    ("s5", ["JOE MONTANA", "STEVE YOUNG", "DAN MARINO"], 1250, 1270, 1040),
]
SIG_LEN = (T["loa"] - T["sig"]) / len(SIGS)

c = Comp(D, FPS)

# ----------------------------------------------------------------- helpers
def photo(cid, src, size, scale, left, top, extra="", pool=None):
    """An owner's photo placed by scale + offset (no resampling beyond the browser's own scaling).
    pool=(cx, cy, rx, ry): an elliptical pool of light around the product, fading the photo's own backdrop into the stage."""
    w, h = size
    st = f' style="--mx:{pool[0]}px;--my:{pool[1]}px;--rx:{pool[2]}px;--ry:{pool[3]}px"' if pool else ' style="-webkit-mask-image:none;mask-image:none"'
    return (f'<div class="ph" id="{cid}" data-layout-ignore{st}>'
            f'<img src="{P}{src}" alt="" style="width:{w * scale:.1f}px;height:{h * scale:.1f}px;left:{left:.1f}px;top:{top:.1f}px">{extra}</div>')

def fit_center(size, cx, cy, sw, box_w, box_h, at=(540, 960)):
    """Scale + offset so source point (cx, cy) lands at `at` and sw source px span box_w."""
    s = box_w / sw
    return s, at[0] - cx * s, at[1] - cy * s

def clip(cid, t0, t1, inner=None, cls="scene on"):
    """Scene layers start visible; their contents carry their own entrances."""
    c.clip(cid, t0, t1, inner, cls)

def slam(sel, t, scale=1.5, blur=16, dur=0.32):
    c.ft(sel, o(opacity=0, scale=scale, filter=f"blur({blur}px)"),
         o(opacity=1, scale=1, filter="blur(0px)", duration=dur, ease="power4.out"), t)

def flash(t, strength=0.85):
    c.ft("#flash", o(opacity=0), o(opacity=strength, duration=0.06, ease="none", immediateRender=False), t)
    c.to("#flash", o(opacity=0, duration=0.32, ease="power2.out"), t + 0.06)

def sweep(sel, t, dur=1.1):
    c.ft(sel, o(xPercent=-120, opacity=1), o(xPercent=120, duration=dur, ease="power2.inOut", immediateRender=False), t)

# ----------------------------------------------------------------- stage: stadium dark, beams, haze, grain
rs = np.random.default_rng(11)
dots = "".join(f'<i style="left:{rs.uniform(0, 1080):.0f}px;top:{rs.uniform(0, 2100):.0f}px;width:{s:.1f}px;height:{s:.1f}px;opacity:{rs.uniform(.12, .4):.2f}"></i>'
               for s in rs.uniform(2, 5, 46))
c.raw(f'<div id="beams" data-layout-ignore><b class="bm b1"></b><b class="bm b2"></b><b class="bm b3"></b></div>')
c.raw(f'<div id="haze" data-layout-ignore>{dots}</div>')
c.ft(".bm", o(rotation=-6, opacity=0.5), o(rotation=6, opacity=1, duration=D, ease="sine.inOut", stagger=0.4), 0)
c.ft("#haze", o(y=0), o(y=-260, duration=D, ease="none"), 0)

# ================================================================= 1. HOOK  "SEVEN LEGENDS. ONE HELMET."
s, l, tp = fit_center(IMG["qb-angle"], 860, 560, 900, 1080, 1920)
clip("hook", 0, T["reveal"] + 0.2, photo("hk-ph", "qb-angle.jpg", IMG["qb-angle"], s, l, tp) + """
  <div class="hk-shade"></div>
  <div class="hk-t" id="hk-t">
    <div class="w1" id="hk1">SEVEN</div><div class="w2" id="hk2">LEGENDS.</div>
    <div class="rule" id="hk-rule"></div>
    <div class="w3" id="hk3">ONE HELMET.</div>
  </div>""", cls="scene on")
c.ft("#hk-ph", o(scale=1.12, transformOrigin="50% 40%"), o(scale=1.0, duration=T["reveal"] - 0.32, ease="power1.out"), 0)
c.ft("#hk1", o(opacity=0.85, scale=1.22, filter="blur(4px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.3, ease="power4.out"), 0)
slam("#hk2", 0.3)
c.ft("#hk-rule", o(scaleX=0, transformOrigin="0% 50%"), o(scaleX=1, duration=0.45, ease="power3.inOut"), 0.62)
slam("#hk3", 1.0, 1.7, 20, 0.36)
flash(1.0, 0.35)
c.to("#hk-t", o(scale=1.25, opacity=0, filter="blur(14px)", duration=0.3, ease="power3.in"), T["reveal"] - 0.3)
c.to("#hk-ph", o(scale=1.3, opacity=0, duration=0.3, ease="power3.in"), T["reveal"] - 0.3)
c.cue("impact", 0.0, -2.0); c.cue("hit", 0.3, -3.0); c.cue("riser-s", 1.0, -6.0); c.cue("impact", 1.0, 0.0)
c.cue("riser-m", T["reveal"], -4.0); c.cue("whoosh", T["reveal"] - 0.1, -3.0)

# ================================================================= 2. REVEAL  the legends helmet
t0 = T["reveal"]
s, l, tp = fit_center(IMG["qb-dark"], 910, 760, 1240, 1000, 0, at=(540, 1080))
clip("reveal", t0 - 0.05, T["sig"] + 0.3, cls="scene on", inner=photo("rv-ph", "qb-side-dark.jpg", IMG["qb-dark"], s, l, tp, '<i class="sheen" id="rv-sh"></i>', pool=(540, 1100, 640, 520)) + f"""
  <div class="tag" id="rv-tag"><span class="dot"></span>NFL QUARTERBACK LEGENDS</div>
  <div class="title" id="rv-title">7 SIGNATURES.<br><em>1 HELMET.</em></div>
  <div class="sub" id="rv-sub">Multi-signed full-size Riddell helmet</div>""")
flash(t0, 0.9)
c.ft("#rv-ph", o(scale=1.18, opacity=0, filter="brightness(0.2)"), o(scale=1.0, opacity=1, filter="brightness(1)", duration=1.1, ease="expo.out"), t0)
c.to("#rv-ph", o(scale=1.06, duration=T["sig"] - t0 - 1.1, ease="none"), t0 + 1.1)
sweep("#rv-sh", t0 + 0.6, 1.3)
c.ft("#rv-tag", o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.4, ease="power3.out"), t0 + 0.35)
slam("#rv-title", t0 + 0.5, 1.25, 10, 0.4)
c.ft("#rv-sub", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.45, ease="power2.out"), t0 + 0.9)
c.to("#reveal", o(opacity=0, duration=0.25), T["sig"] - 0.2)
c.cue("impact", t0, -1.0); c.cue("hit", t0 + 0.5, -5.0); c.cue("whoosh", t0 + 1.25, -10.0)

# ================================================================= 3. THE SIGNATURES  close-ups
c.raw('<div id="frame-ui" class="ui-l" data-layout-ignore></div>')
for i, (sid, names, cx, cy, sw) in enumerate(SIGS):
    a = T["sig"] + i * SIG_LEN; b = a + SIG_LEN
    s, l, tp = fit_center(IMG["qb-angle"], cx, cy, sw, 1080, 0, at=(540, 780))
    count = f"{i + 1:02d}" if len(names) == 1 else f"{i + 1:02d}–{i + len(names):02d}"
    nm = "".join(f"<div>{esc(n)}</div>" for n in names)
    eyebrow = "SIGNED BY" if len(names) == 1 else "ALSO SIGNED BY"
    clip(sid, a - 0.12, b + 0.12, photo(f"{sid}-ph", "qb-angle.jpg", IMG["qb-angle"], s, l, tp) + f"""
      <div class="mac-shade"></div>
      <div class="corners"><i></i><i></i><i></i><i></i></div>
      <div class="count" id="{sid}-n"><b>{count}</b> / 07</div>
      <div class="name{' multi' if len(names) > 1 else ''}" id="{sid}-name"><small>{eyebrow}</small>{nm}<i class="bar"></i></div>""")
    drift = 26 if i % 2 else -26
    c.ft(f"#{sid}-ph", o(scale=1.16, x=-drift, filter="blur(10px)", opacity=0),
         o(scale=1.0, x=0, filter="blur(0px)", opacity=1, duration=0.32, ease="power3.out"), a - 0.12)
    c.to(f"#{sid}-ph", o(scale=1.07, x=drift, duration=SIG_LEN - 0.34, ease="none"), a + 0.2)
    c.ft(f"#{sid}-name", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.3, ease="power3.out"), a + 0.1)
    c.ft(f"#{sid}-name .bar", o(scaleX=0, transformOrigin="0% 50%"), o(scaleX=1, duration=0.35, ease="power3.out"), a + 0.15)
    c.ft(f"#{sid}-n", o(opacity=0), o(opacity=1, duration=0.2), a + 0.05)
    if i < len(SIGS) - 1:
        c.to(f"#{sid}-ph", o(scale=1.22, filter="blur(12px)", opacity=0, duration=0.16, ease="power2.in"), b - 0.12)
        c.to(f"#{sid}-name", o(opacity=0, x=30, duration=0.14), b - 0.12)
    c.cue("whoosh", a - 0.05, -9.0 if i else -6.0); c.cue("hit", a + 0.1, -6.0 if len(names) == 1 else -3.0); c.cue("tick", a - 0.1, -8.0)
c.ft("#frame-ui", o(opacity=0), o(opacity=1, duration=0.3), T["sig"] - 0.1)
c.to("#frame-ui", o(opacity=0, duration=0.2), T["loa"] - 0.2)
c.to("#s5", o(opacity=0, duration=0.22), T["loa"] - 0.15)

# ================================================================= 4. AUTHENTICITY  the JSA letter
t0 = T["loa"]
LW = 860; ls = LW / IMG["loa"][0]; LX, LY = (1080 - LW) / 2, 520
def doc_pt(px, py): return LX + px * ls, LY + py * ls
clip("loa", t0 - 0.1, T["shula"] + 0.2, f"""
  <div class="tag top" id="lo-tag"><span class="dot"></span>AUTHENTICATED</div>
  <div class="title sm" id="lo-title">JSA LETTER OF<br><em>AUTHENTICITY</em></div>
  <div id="doccam"><div class="doc" id="doc" data-layout-ignore style="left:{LX}px;top:{LY}px;width:{LW}px">
    <img src="{P}loa-qb.jpg" alt="JSA letter of authenticity" style="width:{LW}px">
    <i class="hl" id="hl-cert" style="left:{780 * ls:.0f}px;top:{738 * ls:.0f}px;width:{680 * ls:.0f}px;height:{60 * ls:.0f}px"></i>
    <i class="hl" id="hl-sigs" style="left:{70 * ls:.0f}px;top:{928 * ls:.0f}px;width:{1360 * ls:.0f}px;height:{88 * ls:.0f}px"></i></div></div>
  <div class="chipline" id="lo-c1">CERT # <b>ZZ16896</b></div>
  <div class="chipline" id="lo-c2"><b>7</b> SIGNATURES · NFL QUARTERBACK LEGENDS</div>""")
c.ft("#doc", o(opacity=0, y=260, rotationX=28, rotationY=-14, transformPerspective=1600, scale=0.86),
     o(opacity=1, y=0, rotationX=0, rotationY=0, scale=1, duration=0.75, ease="expo.out"), t0)
c.ft("#lo-tag", o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.35, ease="power3.out"), t0 + 0.15)
slam("#lo-title", t0 + 0.25, 1.2, 8, 0.38)
# punch in on the certification number, then on the signature list (camera on the letter, origin 0 0)
def doccam(t, px, py, S, cy, dur=0.6):
    x, y = doc_pt(px, py)
    c.to("#doccam", o(x=540 - S * x, y=cy - S * y, scale=S, duration=dur, ease="power3.inOut"), t)
c.to(["#lo-tag", "#lo-title"], o(opacity=0, y=-20, duration=0.25, ease="power2.in"), t0 + 0.95)
doccam(t0 + 1.0, 1120, 768, 2.1, 1080)
c.ft("#hl-cert", o(opacity=0, scale=1.15), o(opacity=1, scale=1, duration=0.3, ease="power3.out", immediateRender=False), t0 + 1.4)
c.ft("#lo-c1", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.35, ease="back.out(1.6)"), t0 + 1.45)
doccam(t0 + 2.05, 745, 972, 1.55, 1080)
c.to("#hl-cert", o(opacity=0, duration=0.2), t0 + 2.05)
c.to("#lo-c1", o(opacity=0, duration=0.2), t0 + 2.05)
c.ft("#hl-sigs", o(opacity=0, scale=1.1), o(opacity=1, scale=1, duration=0.3, ease="power3.out", immediateRender=False), t0 + 2.45)
c.ft("#lo-c2", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.35, ease="back.out(1.6)"), t0 + 2.5)
c.to("#loa", o(opacity=0, duration=0.22), T["shula"] - 0.18)
c.cue("whoosh", t0 - 0.05, -4.0); c.cue("impact", t0 + 0.15, -4.0); c.cue("tick", t0 + 1.4, -3.0); c.cue("hit", t0 + 1.45, -7.0)
c.cue("tick", t0 + 2.45, -3.0); c.cue("hit", t0 + 2.5, -7.0)

# ================================================================= 5. DON SHULA
t0 = T["shula"]
s, l, tp = fit_center(IMG["shula"], 1015, 775, 1450, 1000, 0, at=(540, 1110))
sx, sy = l + 470 * s, tp + 1128 * s           # where the sticker sits on screen in the hero framing
clip("shula", t0 - 0.1, T["both"] + 0.2, f"""<div id="shcam">{photo("sh-ph", "shula-b.jpg", IMG["shula"], s, l, tp, '<i class="sheen" id="sh-sh"></i>', pool=(540, 1120, 640, 500))}</div>
  <div class="tag" id="sh-tag"><span class="dot"></span>HALL OF FAME HEAD COACH</div>
  <div class="title big" id="sh-title">DON <em>SHULA</em></div>
  <div class="sub" id="sh-sub">Signed Riddell helmet · inscribed “H.O.F. 97”</div>
  <div class="loupe" id="sh-loupe" data-layout-ignore><div class="lp-in">{photo("lp-ph", "shula-b.jpg", IMG["shula"], 3.2, 210 - 470 * 3.2, 210 - 1128 * 3.2)}</div></div>
  <div class="chipline low" id="sh-c">JSA STICKER · <b>YY62600</b></div>""")
flash(t0, 0.9)
c.ft("#sh-ph", o(scale=1.2, opacity=0, filter="brightness(0.2)"), o(scale=1.0, opacity=1, filter="brightness(1)", duration=1.0, ease="expo.out"), t0)
sweep("#sh-sh", t0 + 0.5, 1.2)
c.ft("#sh-tag", o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.4, ease="power3.out"), t0 + 0.3)
slam("#sh-title", t0 + 0.4, 1.35, 12, 0.4)
c.ft("#sh-sub", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.45, ease="power2.out"), t0 + 0.8)
# punch in on the signature + inscription
S = 1.9; px, py = l + 500 * s, tp + 560 * s
c.to("#shcam", o(x=540 - S * px, y=1100 - S * py, scale=S, duration=0.7, ease="power3.inOut"), t0 + 1.6)
c.to("#shcam", o(x=0, y=0, scale=1, duration=0.6, ease="power3.inOut"), t0 + 2.75)
# the authentication sticker, magnified in a loupe
c.ft("#sh-loupe", o(opacity=0, scale=0.4), o(opacity=1, scale=1, duration=0.45, ease="back.out(1.7)"), t0 + 2.9)
c.to("#sh-sub", o(opacity=0, duration=0.2), t0 + 2.8)
c.ft("#sh-c", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.35, ease="power3.out"), t0 + 3.05)
c.to(["#shula"], o(opacity=0, duration=0.22), T["both"] - 0.15)
c.cue("riser-m", t0, -4.0); c.cue("impact", t0, -1.0); c.cue("hit", t0 + 0.4, -5.0)
c.cue("whoosh", t0 + 1.95, -10.0); c.cue("tick", t0 + 2.9, -3.0); c.cue("hit", t0 + 2.95, -8.0)

# ================================================================= 6. BOTH TOGETHER
t0 = T["both"]
s1, l1, tp1 = fit_center(IMG["qb-dark"], 910, 760, 1240, 780, 0, at=(540, 880))
s2, l2, tp2 = fit_center(IMG["shula"], 1015, 775, 1450, 780, 0, at=(540, 1420))
clip("both", t0 - 0.1, T["cta"] + 0.25, f"""
  {photo("b1", "qb-side-dark.jpg", IMG["qb-dark"], s1, l1, tp1, pool=(540, 880, 500, 330))}{photo("b2", "shula-b.jpg", IMG["shula"], s2, l2, tp2, pool=(540, 1420, 500, 300))}
  <div class="both-t"><div id="bt1">AUTHENTIC</div><div id="bt2">MEMORABILIA.</div><div class="pf" id="bt3">PRICED FOR FANS.</div></div>""")
c.ft("#b1", o(x=-700, opacity=0), o(x=0, opacity=1, duration=0.6, ease="expo.out"), t0)
c.ft("#b2", o(x=700, opacity=0), o(x=0, opacity=1, duration=0.6, ease="expo.out"), t0 + 0.12)
slam("#bt1", t0 + 0.4, 1.4, 12, 0.32); slam("#bt2", t0 + 0.55, 1.4, 12, 0.32)
c.ft("#bt3", o(opacity=0, y=24, scale=0.9), o(opacity=1, y=0, scale=1, duration=0.45, ease="back.out(1.8)"), t0 + 1.2)
c.to(["#b1", "#b2"], o(scale=1.04, duration=2.0, ease="none"), t0 + 0.6)
c.to("#both", o(opacity=0, duration=0.25), T["cta"] - 0.2)
c.cue("whoosh", t0 - 0.05, -4.0); c.cue("whoosh", t0 + 0.1, -7.0); c.cue("impact", t0 + 0.45, -3.0); c.cue("hit", t0 + 1.2, -3.0)

# ================================================================= 7. CTA
t0 = T["cta"]
lsc = 1080 / IMG["logo"][0]
clip("cta", t0 - 0.12, D, f"""{photo("lg", "logo.png", IMG["logo"], lsc, 0, 900 - 950 * lsc)}
  <div class="cta-h" id="cta-h">OWN A PIECE OF<br><em>FOOTBALL HISTORY.</em></div>
  <div class="cta-row"><div class="pill" id="pill">SHOP PANDA SPORTS COLLECTIBLES</div></div>
  <div class="url" id="url">pandasportsmemorabilia.com</div>""")
c.ft("#cta", o(opacity=0), o(opacity=1, duration=0.25), t0 - 0.12)
c.ft("#lg", o(scale=1.25, filter="blur(14px)", opacity=0), o(scale=1, filter="blur(0px)", opacity=1, duration=0.8, ease="expo.out"), t0)
slam("#cta-h", t0 + 0.45, 1.3, 10, 0.4)
c.ft("#pill", o(opacity=0, y=30, scale=0.9), o(opacity=1, y=0, scale=1, duration=0.5, ease="back.out(1.7)"), t0 + 0.95)
c.ft("#url", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.4, ease="power2.out"), t0 + 1.2)
c.to("#pill", o(scale=1.05, duration=0.3, ease="sine.inOut", yoyo=True, repeat=1), t0 + 2.0)
flash(t0, 0.6)
c.cue("riser-l", t0, -3.0); c.cue("impact", t0, 0.0); c.cue("hit", t0 + 0.45, -4.0); c.cue("hit", t0 + 0.95, -8.0)

c.raw('<div id="flash"></div><div id="grain" data-layout-ignore></div>')

# ----------------------------------------------------------------- CSS
CSS = f"""
@font-face {{ font-family:"Anton"; font-weight:400; font-display:block; src:url("assets/fonts/Anton-400.woff2") format("woff2"); }}
@font-face {{ font-family:"Barlow Condensed"; font-weight:600; font-display:block; src:url("assets/fonts/BarlowCondensed-600.woff2") format("woff2"); }}
@font-face {{ font-family:"Barlow Condensed"; font-weight:700; font-display:block; src:url("assets/fonts/BarlowCondensed-700.woff2") format("woff2"); }}
@font-face {{ font-family:"Barlow Condensed"; font-weight:800; font-display:block; src:url("assets/fonts/BarlowCondensed-800.woff2") format("woff2"); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#030403; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; color:#fff; font-family:"Barlow Condensed", sans-serif;
         background:radial-gradient(ellipse 90% 55% at 50% 42%, #10160F 0%, #050605 60%, #020302 100%); }}
#grid {{ display:none; }}
#glow {{ position:absolute; left:50%; top:46%; width:1300px; height:1300px; margin:-650px 0 0 -650px; border-radius:50%; pointer-events:none;
         background:radial-gradient(circle, rgba(0,200,32,.10), rgba(0,200,32,0) 60%); }}
#vignette {{ position:absolute; inset:0; pointer-events:none; z-index:80; background:radial-gradient(ellipse 80% 70% at 50% 48%, rgba(0,0,0,0) 50%, rgba(0,0,0,.6) 100%); }}
#grain {{ position:absolute; inset:0; pointer-events:none; z-index:81; opacity:.07; mix-blend-mode:overlay;
          background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' seed='3'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>"); }}
#flash {{ position:absolute; inset:0; background:#fff; opacity:0; z-index:79; pointer-events:none; }}
#beams {{ position:absolute; inset:0; pointer-events:none; }}
.bm {{ position:absolute; top:-200px; width:520px; height:2000px; transform-origin:50% 0; opacity:.7;
       background:linear-gradient(180deg, rgba(220,255,225,.10), rgba(220,255,225,0) 70%); filter:blur(30px); }}
.b1 {{ left:-160px; }} .b2 {{ left:290px; }} .b3 {{ right:-160px; }}
#haze {{ position:absolute; inset:0; pointer-events:none; }}
#haze i {{ position:absolute; border-radius:50%; background:#DFFFE4; filter:blur(1px); }}
.scene {{ position:absolute; inset:0; opacity:0; }}
.scene.on {{ opacity:1; }}
.ph {{ position:absolute; inset:0; overflow:hidden;
       -webkit-mask-image:radial-gradient(var(--rx) var(--ry) at var(--mx) var(--my), #000 62%, transparent 100%);
       mask-image:radial-gradient(var(--rx) var(--ry) at var(--mx) var(--my), #000 62%, transparent 100%); }}
.ph img {{ position:absolute; display:block; max-width:none; }}
.sheen {{ position:absolute; inset:0; opacity:0; mix-blend-mode:screen;
          background:linear-gradient(105deg, rgba(255,255,255,0) 38%, rgba(255,255,255,.22) 50%, rgba(255,255,255,0) 62%); }}

/* hook */
#hook .ph {{ -webkit-mask-image:none; mask-image:none; }}
.hk-shade {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(3,4,3,.78), rgba(3,4,3,.62) 45%, rgba(3,4,3,.9)); }}
.hk-t {{ position:absolute; left:70px; right:70px; top:470px; text-align:center; font-family:"Anton", sans-serif; line-height:.92; }}
.hk-t .w1 {{ font-size:300px; letter-spacing:.01em; }}
.hk-t .w2 {{ font-size:212px; color:{G}; text-shadow:0 0 60px rgba(0,200,32,.45); }}
.hk-t .rule {{ width:520px; height:10px; margin:46px auto 40px; background:#fff; }}
.hk-t .w3 {{ font-size:176px; letter-spacing:.01em; }}

/* shared type */
.tag {{ position:absolute; left:70px; top:250px; display:flex; align-items:center; gap:14px; font-weight:700; font-size:40px; letter-spacing:.2em; color:{G}; }}
.tag .dot {{ width:14px; height:14px; border-radius:50%; background:{G}; box-shadow:0 0 16px {G2}; }}
.title {{ position:absolute; left:70px; right:70px; top:312px; font-family:"Anton", sans-serif; font-size:132px; line-height:.95; }}
.title em {{ font-style:normal; color:{G}; }}
.title.sm {{ font-size:112px; }}
.title.big {{ font-size:190px; }}
.sub {{ position:absolute; left:70px; right:70px; top:575px; font-weight:600; font-size:46px; letter-spacing:.04em; color:#D7DCD7; }}

/* signatures */
#frame-ui {{ position:absolute; inset:0; opacity:0; z-index:40; pointer-events:none; }}
.mac-shade {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(3,4,3,.9) 0%, rgba(3,4,3,0) 20%, rgba(3,4,3,0) 54%, rgba(3,4,3,.94) 70%); }}
.scene .ph {{ }}
#s1 .ph, #s2 .ph, #s3 .ph, #s4 .ph, #s5 .ph {{ -webkit-mask-image:none; mask-image:none; }}
.corners i {{ position:absolute; width:70px; height:70px; border-color:{G}; border-style:solid; border-width:0; }}
.corners i:nth-child(1) {{ left:60px; top:330px; border-top-width:6px; border-left-width:6px; }}
.corners i:nth-child(2) {{ right:60px; top:330px; border-top-width:6px; border-right-width:6px; }}
.corners i:nth-child(3) {{ left:60px; top:1160px; border-bottom-width:6px; border-left-width:6px; }}
.corners i:nth-child(4) {{ right:60px; top:1160px; border-bottom-width:6px; border-right-width:6px; }}
.count {{ position:absolute; right:70px; top:226px; font-weight:700; font-size:44px; letter-spacing:.12em; color:#E4E8E4; padding:8px 18px; border-radius:12px; background:rgba(3,4,3,.82); }}
.count b {{ color:{G}; font-weight:800; }}
.name {{ position:absolute; left:70px; right:70px; top:1290px; font-family:"Anton", sans-serif; font-size:118px; line-height:1; }}
.name small {{ display:block; font-family:"Barlow Condensed", sans-serif; font-weight:700; font-size:36px; letter-spacing:.24em; color:{G}; margin-bottom:12px; }}
.name.multi {{ top:1262px; font-size:76px; line-height:1.02; }}
.name .bar {{ display:block; width:140px; height:8px; background:{G}; margin-top:18px; }}

/* letter */
#doccam {{ position:absolute; inset:0; transform-origin:0 0; }}
.doc {{ position:absolute; box-shadow:0 40px 120px rgba(0,0,0,.7), 0 0 0 1px rgba(255,255,255,.08); }}
.doc img {{ display:block; }}
.hl {{ position:absolute; border:4px solid {G}; border-radius:8px; box-shadow:0 0 0 6px rgba(0,200,32,.25), 0 0 30px rgba(59,255,94,.45); opacity:0; }}
.tag.top {{ top:230px; z-index:5; }}
#lo-title {{ top:290px; z-index:5; text-shadow:0 6px 30px rgba(0,0,0,.8); }}
.chipline {{ position:absolute; left:70px; right:70px; top:1430px; text-align:center; z-index:6; font-weight:700; font-size:50px; letter-spacing:.08em; opacity:0;
             padding:22px 30px; border-radius:22px; background:rgba(6,9,6,.92); border:2px solid rgba(0,200,32,.6); }}
.chipline b {{ color:{G}; font-weight:800; }}
.chipline.low {{ top:1450px; }}

/* shula */
#shcam {{ position:absolute; inset:0; transform-origin:0 0; }}
#sh-title {{ top:300px; }}
#sh-sub {{ top:520px; }}
.loupe {{ position:absolute; right:80px; top:1010px; width:420px; height:420px; border-radius:50%; overflow:hidden; opacity:0; z-index:6;
          border:6px solid {G}; box-shadow:0 0 0 10px rgba(0,200,32,.18), 0 30px 80px rgba(0,0,0,.7); }}
.lp-in {{ position:absolute; inset:0; }}
.loupe .ph {{ -webkit-mask-image:none; mask-image:none; }}

/* both */
.both-t {{ position:absolute; left:60px; right:60px; top:230px; text-align:center; font-family:"Anton", sans-serif; line-height:.98; z-index:5; }}
.both-t #bt1, .both-t #bt2 {{ font-size:124px; }}
.both-t #bt2 {{ color:{G}; }}
.both-t .pf {{ display:inline-block; margin-top:22px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:64px; letter-spacing:.14em;
               padding:12px 34px; border:3px solid #fff; border-radius:14px; }}


/* cta */
#cta .ph {{ -webkit-mask-image:none; mask-image:none; }}
.cta-h {{ position:absolute; left:60px; right:60px; top:230px; text-align:center; font-family:"Anton", sans-serif; font-size:112px; line-height:1; text-shadow:0 8px 40px rgba(0,0,0,.9); }}
.cta-h em {{ font-style:normal; color:{G}; }}
.cta-row {{ position:absolute; left:0; right:0; top:1330px; display:flex; justify-content:center; }}
.pill {{ padding:26px 46px; border-radius:999px; background:{G}; color:#031003; font-weight:800; font-size:52px; letter-spacing:.06em; white-space:nowrap;
         box-shadow:0 0 50px rgba(0,200,32,.5); opacity:0; }}
.url {{ position:absolute; left:0; right:0; top:1468px; text-align:center; font-weight:700; font-size:54px; letter-spacing:.04em; color:#fff; opacity:0;
        text-shadow:0 4px 20px rgba(0,0,0,.9); }}
"""

# ----------------------------------------------------------------- sound: effects only (the owner adds the music)
LEVEL = {"impact": -4.0, "hit": -6.0, "tick": -10.0, "whoosh": -6.0, "riser-s": -8.0, "riser-m": -7.0, "riser-l": -7.0}
def mixdown(path):
    SR = 48000; L = int(round(D * SR)); buf = np.zeros((L, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(L, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: buf[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    buf *= 10 ** (-2.5 / 20) / (np.max(np.abs(buf)) + 1e-12)          # loudest hit at -2.5 dBFS
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    dips = codec_safe(path)
    return measure(path), dips

if __name__ == "__main__":
    open(os.path.join(HERE, "index.html"), "w").write(c.page(CSS, "Panda Sports Collectibles · helmet showcase"))
    (I, tp), dips = mixdown(os.path.join(HERE, "assets", "mix.wav"))
    print(f"index.html: {D}s, {len(c.cues)} sound cues; effects track {I} LUFS, true peak {tp} dBTP, AAC dips {dips}")
    if not SHULA_LOA: print("note: no assets/photos/loa-shula.jpg yet; the Shula beat shows its JSA sticker only")
