"""JT Builds Co: "the egg" pattern-interrupt reel (1080x1920, 9 s, sound effects only).

    python3 tools/sfx.py && python3 build.py
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/jtb-egg.mp4 -q delivery

0.0-1.5  a real-time 3D egg (assets/egg.js) rolls across a dark stone counter toward the edge
1.5-2.0  it tips and drops; the old website drops in on the same downward motion and lands
         with an egg-crack impact; the old site cracks like a shell
2.0-7.0  the shell falls away to the rebuilt site, then: built for phones, one tap to book,
         easy to find in a local search, modern / mobile / bookable
7.0-9.0  "Your next customer is looking online." / JT Builds Co | DM 'SITE'
The example business is fictional (niches.json). No ranking claims: the search beat shows
the listing in the results (not first) under "Easy to find."
"""
import json, math, os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "jtb-shorts", "lib")
sys.path.insert(0, LIB)
from comp import Comp, o, R, esc
from brand import C, icon, BASE_CSS
from mocks import phone, PHONE, MOCK_CSS, site_old, MOBILE_SCALE
from sites import site_mobile, serp, SITES_CSS
from scenes import SCENE_CSS, TYPING_CSS, typing, type_into, cam_to, cam_home, tap, ring, scroll_to
from mix import read, codec_safe, measure, ANCHOR
from sfx import key_click

D = 9.0
A = C["accent"]
NICHES = {k: dict(v, _key=k) for k, v in json.load(open(os.path.join(HERE, "..", "jtb-shorts", "niches.json"))).items() if not k.startswith("_")}
n = NICHES["landscaping"]
QUERY = n["query"]

c = Comp(D, 30)

# ----------------------------------------------------------------- 0-2 s: the egg (three.js canvas) over a dark kitchen
bokeh = "".join(f'<i style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;background:rgba(255,{g},{b},{a})"></i>'
                for x, y, s, g, b, a in [(90, 250, 170, 170, 80, .30), (640, 160, 240, 185, 110, .22), (420, 470, 120, 150, 60, .28), (860, 520, 140, 175, 90, .20)])
c.clip("eggshot", 0, 2.12, f'<div id="egg-bg" data-layout-ignore>{bokeh}</div><canvas id="egg-gl" width="1080" height="1920" data-layout-ignore></canvas>',
       cls="layer", style="z-index:4")
c.ft("#eggshot", o(y=0, filter="blur(0px)"), o(y=760, filter="blur(16px)", duration=0.22, ease="power2.in"), 1.86)   # whip down with the fall
c.to("#eggshot", o(opacity=0, duration=0.05), 2.05)

# ----------------------------------------------------------------- the old site, as shell pieces + crack lines
SH = 1012 / MOBILE_SCALE                       # screen height in page px (390 wide)
CX, CY = 195, SH * 0.42                         # impact point
rs = np.random.default_rng(31)
NS = 9
angles = np.sort((np.arange(NS) / NS * 2 * np.pi + rs.uniform(-0.25, 0.25, NS)) % (2 * np.pi))
def boundary(a):
    dx, dy = math.cos(a), math.sin(a)
    ts = [t for t in [(-CX / dx) if dx < 0 else ((390 - CX) / dx) if dx > 0 else 1e9,
                      (-CY / dy) if dy < 0 else ((SH - CY) / dy) if dy > 0 else 1e9] if t > 0]
    t = min(ts); return CX + dx * t, CY + dy * t
def perim(p):
    x, y = p
    if abs(y) < 1e-6: return x
    if abs(x - 390) < 1e-6: return 390 + y
    if abs(y - SH) < 1e-6: return 390 + SH + (390 - x)
    return 780 + SH + (SH - y)
corners = [(390, 0), (390, SH), (0, SH), (0, 0)]
pts = [boundary(a) for a in angles]
shards, cracks = [], []
for i in range(NS):
    p0, p1 = pts[i], pts[(i + 1) % NS]
    q0, q1 = perim(p0), perim(p1)
    if q1 < q0: q1 += 2 * (390 + SH)
    mid = sorted([(perim(cn) + (2 * (390 + SH) if perim(cn) < q0 else 0), cn) for cn in corners])
    poly = [(CX, CY), p0] + [cn for q, cn in mid if q0 < q < q1] + [p1]
    cx_ = sum(p[0] for p in poly) / len(poly); cy_ = sum(p[1] for p in poly) / len(poly)
    clip = ", ".join(f"{x / 390 * 100:.2f}% {y / SH * 100:.2f}%" for x, y in poly)
    shards.append((clip, cx_ / 390 * 100, cy_ / SH * 100))
for a in angles:                               # jagged crack along each seam, plus a ring at the impact
    bx, by = boundary(a); pts_ = []
    for k in range(9):
        f = k / 8; j = 0 if k in (0, 8) else rs.uniform(-7, 7)
        pts_.append((CX + (bx - CX) * f - math.sin(a) * j, CY + (by - CY) * f + math.cos(a) * j))
    cracks.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts_))
ringp = "M" + " L".join(f"{CX + math.cos(t) * (34 + rs.uniform(-6, 6)):.1f} {CY + math.sin(t) * (30 + rs.uniform(-6, 6)):.1f}" for t in np.linspace(0, 2 * np.pi, 15)) + " Z"
old_html = site_old(n, "mobile")
shell = "".join(f'<div class="shard" id="sh{i}" style="clip-path:polygon({cl})">{old_html}</div>' for i, (cl, _, _) in enumerate(shards))
crack_svg = (f'<svg class="cracks" viewBox="0 0 390 {SH:.0f}" width="390" height="{SH:.0f}">'
             + "".join(f'<path class="ck" d="{d}" pathLength="1"/>' for d in cracks + [ringp]) + "</svg>")

screens = [("s-new", site_mobile(n, px="n-", booking=True), ""),
           ("s-old", f'<div class="shell">{shell}{crack_svg}</div>', ""),
           ("s-serp", serp(n, typing(QUERY, 0)[0]), "wipe"),
           ("s-new2", site_mobile(n, px="r-"), "wipe")]
c.clip("dev", 1.8, 7.1, f'<div id="cam"><div id="drop">{phone("ph", screens)}</div></div>', cls="layer", style="z-index:10")
c.clip("scrim-l", 1.8, 7.1, '<div class="scrim"></div>', cls="layer", style="z-index:25")

# 1.86-2.02: the phone falls in on the egg's motion and lands
c.ft("#drop", o(y=-1750, filter="blur(14px)"), o(y=0, filter="blur(0px)", duration=0.16, ease="power2.in"), 1.86)
for k, (dx, dy) in enumerate([(16, 10), (-12, -8), (8, 6), (-4, -3), (0, 0)]):     # landing jolt
    c.to("#drop", o(x=dx, y=dy, duration=0.035, ease="none"), 2.02 + 0.035 * k)
c.ft("#s-old .ck", o(strokeDashoffset=1), o(strokeDashoffset=0, duration=0.16, ease="power2.out", stagger=0.012), 2.03)
c.ft("#flash", o(opacity=0), o(opacity=0.4, duration=0.04, immediateRender=False), 2.02)
c.to("#flash", o(opacity=0, duration=0.25), 2.06)
# 2.38: the shell falls away, the rebuilt site is underneath
order = rs.permutation(NS)
for k, i in enumerate(order):
    _, ox, oy = shards[i]
    c.to(f"#sh{i}", o(y=float(700 + rs.uniform(0, 500)), x=float((ox - 50) * rs.uniform(4, 8)), rotation=float(rs.uniform(-55, 55)),
                      transformOrigin=f"{ox:.1f}% {oy:.1f}%", opacity=0, duration=0.36, ease="power2.in"), 2.3 + 0.016 * k)
c.to("#s-old .cracks", o(opacity=0, duration=0.12), 2.3)
c.ft("#s-new-sweep", o(xPercent=-110, opacity=1), o(xPercent=110, duration=0.6, ease="power2.inOut", immediateRender=False), 2.42)

# ----------------------------------------------------------------- headlines (one idea per beat)
HEADS = [("h1", 2.03, 2.38, "OUTDATED<br>SITE<em>?</em>"), ("h2", 2.40, 2.92, "<em>REBUILT.</em>"),
         ("h3", 2.95, 3.92, "BUILT FOR<br><em>PHONES.</em>"), ("h4", 3.95, 4.90, "ONE TAP<br>TO <em>BOOK.</em>"),
         ("h5", 4.92, 5.92, "EASY TO<br><em>FIND.</em>")]
for hid, t0, t1, txt in HEADS:
    c.clip(hid, t0 - 0.02, t1 + 0.06, f'<div class="hd" id="{hid}-t">{txt}</div>', cls="layer", style="z-index:40")
    c.ft(f"#{hid}-t", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power4.out"), t0)
    c.to(f"#{hid}-t", o(opacity=0, y=-30, duration=0.08, ease="power2.in"), t1 - 0.04)
WORDS = [("w1", 6.0, "MODERN."), ("w2", 6.28, "MOBILE."), ("w3", 6.56, "<em>BOOKABLE.</em>")]
c.clip("words", 5.96, 7.0, '<div class="hd stack">' + "".join(f'<div id="{wid}">{t}</div>' for wid, _, t in WORDS) + "</div>", cls="layer", style="z-index:40")
for wid, t0, _ in WORDS:
    c.ft(f"#{wid}", o(opacity=0, scale=1.4, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.18, ease="power4.out"), t0)
    c.cue("hit", t0, -7.0)

# ----------------------------------------------------------------- 2.95 built for phones: a fast flick through the site
c.to("#s-new-scr", o(y=-620, duration=0.45, ease="power3.inOut"), 2.98)
c.to("#s-new-scr", o(y=-180, duration=0.32, ease="power3.inOut"), 3.47)
c.to("#cam", o(x=540 - 1.1 * 540, y=1010 - 1.1 * 1020, scale=1.1, duration=0.9, ease="power2.out"), 2.95)
c.to("#s-new-scr", o(y=0, duration=0.22, ease="power3.inOut"), 3.84)
# 3.95 one tap to book
cam_home(c, 3.86, 0.2)
tap(c, "n-", 4.06, "n-sm-cta")
c.ft("#n-bk", o(yPercent=104), o(yPercent=0, duration=0.32, ease="power3.out"), 4.12)
cam_to(c, 4.2, 0.32, "n-bk-slots", 1.38, cy=930)
tap(c, "n-", 4.48, "n-bk-s2")
c.to("#n-bk-s2", o(backgroundColor=n["colors"]["primary"], color="#ffffff", borderColor=n["colors"]["primary"], duration=0.08), 4.48)
tap(c, "n-", 4.66, "n-bk-go")
c.ft("#n-bk-done", o(opacity=0), o(opacity=1, duration=0.16), 4.74)
c.ft("#n-bk-done .ok", o(scale=0.4), o(scale=1, duration=0.3, ease="back.out(2.2)"), 4.74)
# 4.92 easy to find: a local search, the listing among the results
cam_home(c, 4.84, 0.18)
c.ft("#s-serp", o(clipPath="inset(0% 0% 100% 0%)"), o(clipPath="inset(0% 0% 0% 0%)", duration=0.22, ease="power3.inOut"), 4.86)
te = type_into(c, QUERY, 5.0, cps=34)
c.ft("#sp-map", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.25, ease="power2.out"), te + 0.03)
c.ft("#s-serp .pinw", o(opacity=0, y=-26), o(opacity=1, y=0, duration=0.3, ease="back.out(2)", stagger=0.06), te + 0.1)
c.ft("#s-serp .sp-row", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.25, ease="power2.out", stagger=0.05), te + 0.08)
c.ft("#sp-places", o(opacity=0), o(opacity=1, duration=0.2), te + 0.05)
c.ft("#sp-you", o(opacity=0), o(opacity=1, duration=0.2), te + 0.15)
c.to("#sp-caret", o(opacity=0, duration=0.1), te + 0.05)
cam_to(c, te + 0.05, 0.25, "sp-r1", 1.42, cy=980)
ring(c, "ring-sp-mine", te + 0.3, 6.35)
# 5.95 modern / mobile / bookable: back on the rebuilt site, then dive into the end card
cam_home(c, 5.88, 0.2)
c.ft("#s-new2", o(clipPath="inset(0% 0% 100% 0%)"), o(clipPath="inset(0% 0% 0% 0%)", duration=0.22, ease="power3.inOut"), 5.9)
c.ft("#s-new2-sweep", o(xPercent=-110, opacity=1), o(xPercent=110, duration=0.5, ease="power2.inOut", immediateRender=False), 5.95)
c.to("#s-new2-scr", o(y=-300, duration=0.8, ease="power1.inOut"), 6.05)
c.to("#cam", o(x=540 - 1.7 * 540, y=960 - 1.7 * 1020, scale=1.7, opacity=0, duration=0.18, ease="power3.in"), 6.84)
c.to("#words", o(opacity=0, scale=1.2, duration=0.16, ease="power3.in"), 6.86)

# ----------------------------------------------------------------- 7-9 s: the line, then the brand
c.clip("end", 6.96, D, f"""<div class="end-bg"></div>
  <div class="end-t"><div class="m"><span id="e1">Your next customer</span></div><div class="m"><span id="e2">is <em>looking online.</em></span></div><i id="e-u"></i></div>
  <div class="lockup" id="lock"><span class="tile"><img src="assets/jt-mark.png" alt="JT Builds Co"></span><b>JT BUILDS CO</b><i class="sep"></i><span class="dm">DM ‘SITE’</span></div>""",
       cls="layer", style="z-index:50")
c.ft(".end-bg", o(opacity=0), o(opacity=1, duration=0.12), 6.96)
c.ft("#e1", o(yPercent=110), o(yPercent=0, duration=0.32, ease="power4.out"), 7.0)
c.ft("#e2", o(yPercent=110), o(yPercent=0, duration=0.32, ease="power4.out"), 7.1)
c.ft("#e-u", o(scaleX=0, transformOrigin="0% 50%"), o(scaleX=1, duration=0.35, ease="power3.inOut"), 7.35)
c.ft("#lock", o(opacity=0, y=40, scale=0.92), o(opacity=1, y=0, scale=1, duration=0.42, ease="back.out(1.6)"), 7.9)
c.to("#lock .dm", o(scale=1.06, duration=0.22, yoyo=True, repeat=1, ease="sine.inOut"), 8.45)

c.raw('<div id="flash"></div><div id="grain" data-layout-ignore></div>')

# ----------------------------------------------------------------- sound (effects only; the owner adds music)
for t, db in [(0.0, 0.0)]: c.cue("roll", t, db)
c.cue("edge", 1.5, -6.0); c.cue("whoosh", 1.93, -5.0)
c.cue("crack", 2.02, 0.0); c.cue("impact", 2.02, -7.0)
c.cue("shards", 2.31, -4.0); c.cue("whoosh", 2.5, -12.0); c.cue("hit", 2.4, -6.0)
c.cue("whoosh", 3.1, -10.0); c.cue("hit", 2.95, -9.0)
c.cue("hit", 3.95, -9.0); c.cue("tap", 4.04); c.cue("whoosh", 4.25, -13.0); c.cue("tap", 4.46); c.cue("tap", 4.64); c.cue("bubble", 4.74, -3.0)
c.cue("hit", 4.92, -9.0); c.cue("whoosh", 4.95, -12.0)
c.cue("bubble", te + 0.1, -7.0); c.cue("popup", te + 0.3, -8.0)
c.cue("whoosh", 5.95, -9.0); c.cue("riser-m", 7.0, -6.0); c.cue("whoosh", 6.9, -6.0)
c.cue("impact", 7.0, -2.0); c.cue("hit", 7.9, -6.0); c.cue("popup", 7.92, -8.0)

LEVEL = {"roll": 0.0, "edge": -2.0, "crack": 0.0, "shards": -4.0, "impact": -3.0, "hit": -5.0, "whoosh": -6.0,
         "tap": -6.0, "bubble": -8.0, "popup": -8.0, "riser-s": -8.0, "riser-m": -7.0}

def mixdown(path):
    SR = 48000; L = int(round(D * SR)); buf = np.zeros((L, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(L, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: buf[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    for t, gdb in c.keys:
        x = key_click(int(t * 1000)); i = int(t * SR); j = min(L, i + len(x))
        if j > i: buf[i:j] += x[: j - i] * 10 ** ((-10 + gdb) / 20)
    buf *= 10 ** (-2.5 / 20) / (np.max(np.abs(buf)) + 1e-12)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    return measure(path), codec_safe(path)

# ----------------------------------------------------------------- CSS
CSS = "\n".join([BASE_CSS, MOCK_CSS, SITES_CSS, SCENE_CSS, TYPING_CSS, f"""
#grid, #glow {{ display:none; }}
#root {{ background:#070605; }}
#eggshot {{ background:#050404; }}
#egg-bg {{ position:absolute; inset:0; background:radial-gradient(ellipse 80% 40% at 50% 28%, #2a1d12 0%, #0c0907 60%, #050404 100%); }}
#egg-bg i {{ position:absolute; border-radius:50%; filter:blur(28px); }}
#egg-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
#flash {{ position:absolute; inset:0; background:#fff; opacity:0; z-index:70; pointer-events:none; }}
#grain {{ position:absolute; inset:0; pointer-events:none; z-index:71; opacity:.06; mix-blend-mode:overlay;
          background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' seed='5'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>"); }}
#vignette {{ z-index:69; }}
#s-old {{ background:transparent; }}
.shell {{ position:relative; width:390px; height:{SH:.0f}px; }}
.shard {{ position:absolute; left:0; top:0; width:390px; height:{SH:.0f}px; }}
.cracks {{ position:absolute; left:0; top:0; }}
.ck {{ fill:none; stroke:#1d1a17; stroke-width:2.2; stroke-linejoin:round; stroke-dasharray:1; stroke-dashoffset:1;
       filter:drop-shadow(0.6px 0.8px 0 rgba(255,255,255,.75)); }}
.hd {{ position:absolute; left:50px; right:50px; top:228px; text-align:center; font-family:"Montserrat", sans-serif; font-weight:800;
       font-size:118px; line-height:.96; letter-spacing:-.025em; color:{C['white']}; text-shadow:0 10px 40px rgba(0,0,0,.65); }}
.hd em {{ font-style:normal; color:{A}; }}
.hd.stack {{ top:200px; font-size:104px; line-height:1.0; }}
.end-bg {{ position:absolute; inset:0; background:radial-gradient(ellipse 90% 50% at 50% 46%, #1f1710 0%, #0a0806 62%, #050404 100%); }}
.end-t {{ position:absolute; left:60px; right:60px; top:640px; text-align:center; font-family:"Montserrat", sans-serif; font-weight:800;
          font-size:90px; line-height:1.06; letter-spacing:-.025em; color:{C['white']}; }}
.end-t .m {{ overflow:hidden; padding-bottom:.08em; white-space:nowrap; }}
.end-t span {{ display:inline-block; }}
.end-t em {{ font-style:normal; color:{A}; }}
#e-u {{ display:block; width:300px; height:10px; margin:34px auto 0; border-radius:5px; background:{A}; }}
.lockup {{ position:absolute; left:0; right:0; top:1130px; display:flex; align-items:center; justify-content:center; gap:22px; opacity:0;
           font-family:"Montserrat", sans-serif; }}
.lockup .tile {{ width:92px; height:92px; border-radius:22px; background:{C['tile']}; display:flex; align-items:center; justify-content:center;
                 box-shadow:0 0 0 1px rgba(255,255,255,.08), 0 14px 40px rgba(0,0,0,.5); }}
.lockup .tile img {{ width:58px; height:49px; }}
.lockup b {{ font-weight:800; font-size:46px; letter-spacing:.06em; color:{C['white']}; }}
.lockup .sep {{ width:3px; height:56px; background:rgba(255,255,255,.35); }}
.lockup .dm {{ display:inline-block; padding:18px 30px; border-radius:999px; background:{A}; color:{C['accent_ink']}; font-weight:800; font-size:44px; }}
"""])

EGG_HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
EGG_BODY = '''<script type="module" src="./assets/egg.js"></script>'''

def page(script=True):
    h = c.page(CSS, "JT Builds Co · the egg", script=script)
    h = h.replace('<script src="assets/gsap.min.js"></script>', '<script src="assets/vendor/gsap.min.js"></script>\n    ' + EGG_HEAD)
    return h.replace("</body>", "  " + EGG_BODY + "\n  </body>")

if __name__ == "__main__":
    if c.needs:     # measure the page once (timeline off, fonts loaded) so taps and punch-ins land exactly
        mp = os.path.join(HERE, ".measure.html"); open(mp, "w").write(page(script=False))
        npm_root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        r = subprocess.run(["node", os.path.join(LIB, "measure.js"), mp, json.dumps(sorted(c.needs))], capture_output=True, text=True,
                           env=dict(os.environ, NODE_PATH=npm_root))
        if r.returncode: sys.exit(r.stderr[-1500:])
        c.resolve(json.loads(r.stdout)); os.remove(mp)
    open(os.path.join(HERE, "index.html"), "w").write(page())
    (I, tp), dips = mixdown(os.path.join(HERE, "assets", "mix.wav"))
    print(f"index.html: {D}s, {len(c.cues)} sounds + {len(c.keys)} key clicks; effects track {I} LUFS, {tp} dBTP, AAC dips {dips}")
