"""'Why pitchers use the rosin bag' (1080x1920, music + effects; the narration is recorded separately).

    python3 tools/physics.py        # the pitches -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (music + effects, mastered low for a voice on top) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/rosin-bag.mp4 --video-bitrate 16M

One pitcher throughout (white home uniform, navy undershirt). Close-ups use a jointed hand whose fingers are solved to
wrap the ball or the bag (assets/field.js), the seamed ball, the cloth rosin bag, rosin dust and sweat beads.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PI_ = P["pitches"]
D = 44.5
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
CLOSE = dict(close=1)
# 1 the hook (0-5): the bag on the mound, close; his cleats come into view; he picks it up; quick zoom; squeeze; he rubs his fingertips
rate(0.0, 1.6, "bag", 0.0, act="pick", k="s1", c0=[0.45, 0.22, -1.8], c1=[0.35, 0.2, -1.5], l=[-0.15, 0.3, 1.0], f0=34, f1=30, bokeh=0, **CLOSE)
rate(1.6, 2.6, "bag", 1.6, act="pick", k="s1", c0=[9.0, 3.0, 5.5], c1=[11.0, 4.2, 7.0], l=[-0.6, 1.8, 0.4], l1=[-0.9, 3.2, 0.9], f0=30, f1=32)
rate(2.6, 3.2, "zoomHand", 2.6, act="pick", k="s1", dFar=9, c1=[1.1, 1.2, 2.2], l=[0.0, 0.22, 0.09], f0=34, f1=26, bokeh=0)
rate(3.2, 5.0, "rig", 3.2, act="pick", k="s1", c0=[1.1, 1.2, 2.2], c1=[0.95, 1.1, 1.9], l=[0.0, 0.22, 0.09], f0=26, bokeh=8, **CLOSE)
VSQ = 3.35
# 2 the problem (5-13): the ball in his hand; in on his fingers on the seams; sweat beads; the ball shifts; he regrips
rate(5.0, 6.6, "world", 0.0, act="hold", c0=[-8.0, 6.3, -52.5], c1=[-6.8, 6.0, -54.0], l=[-0.4, 4.5, -60.0], f0=28, f1=25)
rate(6.6, 10.2, "rig", 1.6, act="hold", c0=[-1.5, 0.8, 0.7], c1=[-1.3, 0.75, 0.6], l=[0.03, 0.43, 0.15], f0=26, bokeh=8, **CLOSE)
rate(10.2, 13.0, "rig", 5.2, act="hold", c0=[1.4, 0.9, -0.6], c1=[1.25, 0.85, -0.5], l=[0.03, 0.43, 0.15], f0=26, bokeh=8, **CLOSE)
V_WET, V_SLIP, V_REGRIP = 6.6 + 0.4, 6.6 + (3.7 - 1.6), 10.2 + (5.6 - 5.2)
# 3 how rosin works (13-23): back to the bag; dust onto the fingertips, the sweat goes; he rubs them; grips the seams again
S3 = dict(act="pick", k="s3", wet0=1, bounce=1, dryAt=2.8, dustAt=2.6)
rate(13.0, 14.5, "bag", 0.6, c0=[9.5, 3.4, 6.0], c1=[9.0, 3.2, 5.6], l=[-0.9, 2.2, 1.2], f0=38, **S3)
rate(14.5, 17.4, "rig", 2.1, c0=[1.1, 1.2, 2.2], c1=[0.95, 1.1, 1.9], l=[0.0, 0.22, 0.09], f0=26, bokeh=8, **CLOSE, **S3)
rate(17.4, 18.8, "rig", 4.25, c0=[0.7, 1.9, 1.2], c1=[0.62, 1.8, 1.05], l=[0.05, 0.5, 0.06], f0=26, bokeh=8, **CLOSE, **S3)
rate(18.8, 23.0, "rig", 0.0, act="hold", dry=1, c0=[-1.5, 0.8, 0.7], c1=[-1.3, 0.75, 0.6], l=[0.03, 0.43, 0.15], f0=26, bokeh=8, **CLOSE)
# 4 why grip matters (23-33): fastball, curveball, changeup: the grip, close; the release, slowed; the ball on its way
V4 = [23.0, 26.33, 29.67]
for i, k in enumerate(["fb", "cb", "ch"]):
    a = V4[i]
    rate(a, a + 1.0, "rig", 0.0, act="hold", dry=1, kind=k, hl=["IM", "MT", "IT"][i], c0=[-1.5, 0.8, 0.7], c1=[-1.35, 0.76, 0.62], l=[0.03, 0.42, 0.14], f0=26, bokeh=8, **CLOSE)
    shot(a + 1.0, a + 2.6, "track", [a + 1.0, a + 2.6], [-0.42, 0.07], speed="slow", act="pitch", kind=k, hl=["IM", "MT", "IT"][i], off=[-4.5, 0.8, 2.2], f0=28, bokeh=0, **CLOSE)
    rate(a + 2.6, V4[i + 1] if i < 2 else 33.0, "ball", 0.07, r=0.7, act="pitch", kind=k, c0=[-1.4, 6.6, -63.5], c1=[-1.3, 6.5, -63.0], l=[0, 2.6, 0], f0=22)
# 5 the rules (33-39): the bag behind the rubber; legal rosin vs. rosin mixed with sunscreen
rate(33.0, 34.6, "bag", 0.0, act="rules", noHand=1, c0=[0.8, 1.1, -3.0], c1=[0.65, 1.0, -2.6], l=[-0.35, 0.3, 1.5], f0=34, bokeh=0, **CLOSE)
RULE = dict(act="rules", cam="bag", c0=[0.0, 1.35, 1.45], c1=[0.0, 1.28, 1.3], l=[0.0, 0.3, 0.0], f0=30, bokeh=6, close=1)
shot(34.6, 39.0, "bag", [34.6, 39.0], [0, 4.4], mode="split", top=dict(RULE), bot=dict(RULE, illegal=1))
# 6 the ending (39-44.5): he delivers; the bag behind the mound; now you know; the end card
rate(39.0, 41.5, "world", -2.1, act="pitch", kind="end", streak=1, c0=[1.4, 9.6, -85.0], c1=[1.2, 9.3, -83.0], l=[0.0, 3.2, -28.0], f0=19)
rate(41.5, D, "bag", 1.0, act="rest", kind="end", c0=[0.95, 0.38, -1.25], c1=[0.8, 0.34, -1.05], l=[-0.05, 0.12, 0.3], f0=36, bokeh=16, **CLOSE)
VBRAND = 43.0
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [5.0, 13.0, 23.0, 33.0, 39.0, VBRAND]:
    c.set("#flash", '{"opacity":0.45}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls="", half=""):
    hv = f' data-half="{half}"' if half else ""
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"{hv}><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, half])
def title(tid, t0, t1, lines, top=260, cls="hk2"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.06 * i)
def note(nid, t0, t1, text, top=1640):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:13"); pop(f"#{nid}x", t0, 8)
def card(cid, t0, t1, n, text, top=1380):
    c.clip(cid, t0, t1, f'<div class="nc" id="{cid}x" style="top:{top}px"><i>{n}</i><b>{text}</b></div>', cls="layer", style="z-index:13")
    c.ft(f"#{cid}x", o(opacity=0, x=-60), o(opacity=1, x=0, duration=0.24, ease="power3.out"), t0)

# ----------------------------------------------------------------- 1 the hook
title("hook", 0.1, 4.98, [("What is this", False), ("little white bag?", True)])
pinl("pbag", 0.5, 1.58, "Rosin bag", "bag", "")
# 2 the problem
title("t2", 5.1, 12.98, [("Moisture makes", False), ("grip harder", True)])
pinl("pwet", V_WET, V_SLIP - 0.05, "Sweat on the fingertips", "tipM", "cy sm")
pinl("pslip", V_SLIP + 0.1, 10.18, "The ball shifts in his fingers", "ball", "sm")
pinl("preg", V_REGRIP, 12.98, "He has to reset his grip", "tipI", "yl sm")
# 3 how rosin works
title("t3", 13.1, 22.98, [("Better moisture control.", False), ("More consistent grip.", True)])
c.clip("steps", 14.9, 18.78, """<div class="howto" id="howx"><div class="hrow" id="h1"><i>1</i><span>Sweat leaves the fingertips <b>slick</b></span></div>
  <div class="hrow" id="h2"><i>2</i><span>Rosin powder <b>dries</b> them and adds a little <b>tack</b></span></div></div>""", cls="layer", style="z-index:13")
pop("#h1", 14.9, 12); pop("#h2", 16.1, 12)
pinl("pdust", 15.9, 17.38, "Rosin on the fingertips", "tipI", "sm")
pinl("prub", 17.5, 18.78, "Worked in", "tipT", "sm")
note("n3", 19.3, 22.98, "Dry fingertips: the grip feels the <b>same</b> from pitch to pitch.")
# 4 why grip matters
title("t4", 23.1, 32.98, [("Every finger", False), ("matters", True)])
NAMES = [("1", "Four-seam fastball"), ("2", "Curveball"), ("3", "Changeup")]
GRIPN = [("Index and middle across the seams", "tipI"), ("Middle finger along a seam", "tipM"), ("Thumb and index circle: ball deeper in the hand", "ball")]
RELN = ["Backspin off the fingertips", "Fingers pull down over the front: topspin", "Less speed off a deeper grip"]
for i, a in enumerate(V4):
    card(f"k{i}", a + 0.05, a + 3.3 if i < 2 else 32.98, *NAMES[i])
    pinl(f"pg{i}", a + 0.2, a + 0.98, GRIPN[i][0], GRIPN[i][1], "yl sm")
    pinl(f"pr{i}", a + 1.5, a + 2.58, RELN[i], "tipM", "sm")
note("n4", 23.4, 32.98, "Rosin doesn’t add speed or movement. It helps every grip <b>feel the same</b>.", 1660)
# 5 the rules
pinl("pbag2", 33.2, 34.58, "Rosin bag", "bag", "")
pinl("prub2", 33.5, 34.58, "Behind the rubber", "rubber", "cy sm")
c.clip("splt", 34.6, 39.0, """<div class="seam"></div>
  <div class="half t"><span class="vd ok" id="vd1"><i>✓</i>Legal: the rosin bag</span></div>
  <div class="half b"><span class="vd no" id="vd2"><i>✕</i>Illegal: rosin + sunscreen</span></div>""", cls="layer", style="z-index:11")
pop("#vd1", 34.7, 10); pop("#vd2", 35.4, 10)
title("t5", 34.65, 38.98, [("Legal rosin.", False), ("Illegal foreign substances.", True)], 860, "hk2 band")
pinl("pt1", 35.0, 38.98, "Rosin dust", "tipI", "sm", "t")
pinl("pt2", 35.6, 38.98, "Sunscreen", "bottle", "sm", "b")
pinl("pt3", 36.0, 38.98, "Sticky mix on the fingers", "tipM", "sm", "b")
note("n5", 36.4, 38.98, "MLB allows the rosin bag. Mixing rosin with a <b>foreign substance</b> like sunscreen to improve grip is <b>not allowed</b>.", 1700)
# 6 the ending
title("t6", 41.6, VBRAND - 0.02, [("Now you know.", True)], 820, "hk2 big")
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.2), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- sound (no voice: room left for the narrator)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8)
for tt in [0.1, 5.1, 13.1, 23.1, 34.65, 41.6]: cue("impact", tt, -6)
STEPS = [0.15 + 0.42 * i for i in range(3)] + [13.1, 13.5]                    # footsteps on the dirt
PUFFS = [VSQ + 0.1] + [14.5 + 0.25 + 0.42 * i for i in range(4)]
THUDS = [4.05 + 0.36]
for a in V4: cue("whoosh", a + 1.0 + 0.42 / 0.49 * 1.6, -8)
for a, k in zip(V4, ["fb", "cb", "ch"]): cue("glove", a + 2.6 + (PI_[k]["flight"] - 0.07) / 0.7, -2)
REL_END = 39.0 + 2.1
cue("whoosh", REL_END, -6); cue("glove", REL_END + PI_["end"]["flight"], 0)
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}

def cloth(rng):
    """A squeeze of a powder-filled cloth bag: a soft, muffled crunch with a breathy puff."""
    t = np.arange(int(0.35 * SR)) / SR
    n = np.convolve(rng.standard_normal(len(t)), np.ones(9) / 9, "same")
    env = np.exp(-((t - 0.05) / 0.05) ** 2) + 0.5 * np.exp(-t / 0.12) * (t > 0.03)
    x = n * env; x /= np.max(np.abs(x)); return np.stack([x, x], 1)

def step(rng):
    """A cleat on mound clay: a dull low thump with grit."""
    t = np.arange(int(0.25 * SR)) / SR
    body = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.03)
    grit = np.convolve(rng.standard_normal(len(t)), np.ones(6) / 6, "same") * np.exp(-t / 0.025) * 0.6
    x = body + grit; x /= np.max(np.abs(x)); return np.stack([x, x], 1)

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    rng = np.random.default_rng(7)
    for vt, fn, g in [(v, cloth, -16) for v in PUFFS] + [(v, step, -18) for v in STEPS] + [(v, step, -14) for v in THUDS]:
        x = fn(rng); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * 10 ** (g / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-27 / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=121)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 3.0, 0.5, 1.0)[:, None]
    full = (fx + bed * ramp * 10 ** (-16 / 20)) * 10 ** (-6 / 20)
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre = os.path.join(HERE, ".pre.wav"); wav(pre, full)
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-20.0)
    os.remove(pre)
    return m

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
MONO = 'font-family:"Plex Mono", monospace; font-weight:500; text-transform:uppercase;'
BC = 'font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase;'
CARD = "background:rgba(6,10,18,.86); border-radius:14px;"
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:700px; background:linear-gradient(180deg, rgba(3,6,12,.66), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:820px; background:linear-gradient(0deg, rgba(3,6,12,.75) 0%, rgba(3,6,12,.38) 55%, rgba(3,6,12,0) 100%); }}
.flash {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.dim {{ position:absolute; inset:0; background:rgba(4,7,12,.62); }}
.spd {{ position:absolute; right:44px; top:150px; display:inline-flex; align-items:center; gap:10px; padding:8px 16px; border-radius:8px; background:rgba(6,10,18,.72); {MONO} font-size:21px; letter-spacing:.14em; color:{Y}; opacity:0; }}
.spd::before {{ content:""; width:10px; height:10px; border-radius:50%; background:currentColor; }}

.hk {{ position:absolute; left:52px; right:40px; top:300px; display:grid; gap:2px; {BC} font-size:150px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.75), 0 2px 4px rgba(0,0,0,.6); }}
.hk .hl {{ display:block; }} .hk .acc, .hk .hl.acc {{ color:{HOT}; }} .hk .hw {{ display:inline-block; transform-origin:0 80%; }}
.hk.big {{ font-size:210px; }} .hk.qq2 {{ font-size:140px; }}
.cap {{ position:absolute; left:52px; right:40px; }}
.cap .cl {{ display:block; {BC} font-size:88px; line-height:.96; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{HOT}; }}
.yl {{ color:{Y}; }} .hot {{ color:{HOT}; }} .wh {{ color:#eef2f7; }}
.pt {{ position:absolute; left:52px; right:60px; {BC} font-size:104px; line-height:.95; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.7); }}
.pt.sm {{ font-size:84px; }} .pt em {{ font-style:normal; color:{HOT}; }}
.tg {{ position:absolute; left:52px; max-width:980px; padding:10px 20px; border-radius:12px; background:rgba(6,10,18,.86); white-space:nowrap; font-family:"Inter", sans-serif; font-weight:800; font-size:33px; }}
.tg b {{ font-weight:800; }}
.rs {{ position:absolute; left:52px; padding:10px 22px; border-radius:12px; {CARD} {BC} font-size:60px; }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:24px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; {BC} font-size:46px; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.pin.yl span {{ background:{Y}; }}

.mini {{ position:absolute; right:52px; top:560px; display:grid; justify-items:center; gap:10px; padding:20px 22px 16px; {CARD} }}
.mini .ml {{ {MONO} font-size:20px; letter-spacing:.08em; color:{MUTED}; }}
.dia {{ position:relative; }}
.dia svg {{ position:absolute; left:0; top:0; overflow:visible; }}
.dia polygon {{ fill:rgba(63,110,47,.28); stroke:rgba(244,246,248,.7); stroke-width:4; }}
.dia .bs {{ position:absolute; width:30px; height:30px; margin:-15px 0 0 -15px; background:#f4f6f8; transform:rotate(45deg); border-radius:3px; }}
.dia .bs.hp {{ width:26px; height:26px; margin:-13px 0 0 -13px; border-radius:2px 2px 50% 2px; }}
.dia .rn {{ position:absolute; width:52px; height:52px; margin:-26px 0 0 -26px; border-radius:50%; background:{HOT}; border:4px solid #05080d; box-shadow:0 0 0 3px {HOT}; display:grid; place-items:center; color:#05080d; font-size:30px; }}
.dia .rn.bt {{ background:{Y}; box-shadow:0 0 0 3px {Y}; }}
.fork {{ position:absolute; left:52px; right:52px; top:620px; display:grid; gap:16px; }}
.fork .fh {{ {MONO} font-size:24px; letter-spacing:.16em; color:{MUTED}; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.fr {{ display:flex; align-items:center; gap:20px; padding:20px 24px; {CARD} border:3px solid rgba(255,255,255,.16); transform-origin:0 50%; }}
.fr i {{ display:grid; place-items:center; width:62px; height:62px; flex:none; border-radius:12px; background:#26303f; {BC} font-style:normal; font-size:44px; }}
.fr b {{ {BC} font-size:58px; line-height:1; color:#fff; }} .fr em {{ font-style:normal; color:{HOT}; }}
#fr2 i {{ background:{HOT}; color:#05080d; }}
.gm {{ position:absolute; left:52px; right:52px; top:520px; display:grid; gap:8px; }}
.gm b {{ {BC} font-size:82px; line-height:1; color:{Y}; text-shadow:0 4px 22px rgba(0,0,0,.85); }}
.gm span {{ justify-self:start; padding:10px 18px; {CARD} font-family:"Inter", sans-serif; font-weight:800; font-size:31px; line-height:1.25; }}
.rec {{ position:absolute; left:52px; top:1820px; {MONO} font-size:21px; letter-spacing:.1em; color:#cfd6e0; padding:6px 12px; border-radius:8px; background:rgba(6,10,18,.72); }}
.bnr {{ position:absolute; left:52px; top:205px; display:flex; align-items:center; gap:12px; padding:6px 16px 6px 8px; border-radius:12px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.14); }}
.bnr b {{ padding:4px 12px; border-radius:8px; background:{HOT}; color:#05080d; {BC} font-size:36px; }} .bnr span {{ {BC} font-size:36px; }}
.tac {{ position:absolute; inset:0; background:radial-gradient(ellipse at 50% 45%, rgba(8,14,24,.82), rgba(3,6,11,.94)); }}
.sit {{ position:absolute; left:36px; top:560px; width:492px; display:grid; justify-items:center; gap:10px; padding:20px 18px 22px; {CARD} border:2px solid rgba(255,255,255,.12); }}
.sit.r {{ left:552px; }}
.sit .sk {{ justify-self:start; display:flex; align-items:center; gap:12px; {BC} font-size:44px; }}
.sit .sk i {{ display:grid; place-items:center; width:50px; height:50px; border-radius:10px; background:{Y}; color:#05080d; font-style:normal; }}
.sit.r .sk i {{ background:{HOT}; }}
.sit .so {{ {MONO} font-size:22px; letter-spacing:.12em; padding:4px 12px; border-radius:8px; background:#26303f; }}
.sit .sl2 {{ justify-self:stretch; font-family:"Inter", sans-serif; font-weight:700; font-size:25px; color:#dfe5ec; }}
.sit .sl2 b {{ font-weight:800; }}
.sit .sv {{ justify-self:stretch; margin-top:4px; padding:12px 14px; border-radius:10px; background:#141b27; {BC} font-size:38px; line-height:1; }}
.steps {{ position:absolute; left:36px; right:36px; top:1660px; display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }}
.steps span {{ display:grid; place-items:center; padding:14px 6px; border-radius:12px; background:rgba(6,10,18,.88); border-bottom:5px solid {HOT}; {BC} font-size:37px; white-space:nowrap; opacity:0; }}
"""])

CSS += f"""
.hk.mid {{ font-size:124px; }}
.pt.ctr {{ left:0; right:0; text-align:center; font-size:112px; }}
.seam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; left:0; right:0; height:960px; }} .half.t {{ top:0; }} .half.b {{ top:960px; }}
.hlab {{ position:absolute; left:40px; top:180px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:56px; }}
.half.b .hlab {{ top:28px; }}
.ch {{ position:absolute; left:52px; top:250px; display:grid; gap:4px; }}
.ch span {{ {MONO} font-size:26px; letter-spacing:.16em; color:{MUTED}; }} .ch b {{ {BC} font-size:110px; line-height:.95; color:#fff; }}
.cdia {{ position:absolute; left:0; right:0; top:620px; display:flex; justify-content:center; }}
.clst {{ position:absolute; left:52px; right:52px; top:960px; display:grid; gap:14px; }}
.ci {{ display:flex; align-items:center; gap:22px; padding:16px 22px; {CARD} border-left:6px solid {Y}; }}
.ci i {{ display:grid; place-items:center; width:58px; height:58px; flex:none; border-radius:50%; background:{Y}; color:#05080d; font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:36px; }}
.ci b {{ {BC} font-size:64px; line-height:1; color:#fff; }}
.cbl {{ position:absolute; left:52px; right:52px; top:1530px; padding:16px 22px; border-radius:14px; background:{HOT}; color:#05080d; {BC} font-size:62px; text-align:center; }}
.cbl em {{ font-style:normal; color:#fff; }}
.cfn {{ position:absolute; left:52px; right:52px; top:1680px; {MONO} font-size:24px; letter-spacing:.08em; color:#cfd6e0; text-align:center; }}
"""

CSS += f"""
.seam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; left:0; right:0; height:960px; }} .half.t {{ top:0; }} .half.b {{ top:960px; }}
.hlab {{ position:absolute; left:40px; top:120px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:60px; }}
.half.b .hlab {{ top:28px; }}
.rs2 {{ position:absolute; right:40px; padding:10px 22px; border-radius:12px; background:rgba(6,10,18,.9); {BC} font-size:62px; }}
.stamp {{ position:absolute; left:0; right:0; top:620px; text-align:center; {BC} font-size:260px; line-height:1; color:{HOT}; text-shadow:0 10px 40px rgba(0,0,0,.85); }}
.endq {{ position:absolute; left:0; right:0; top:830px; padding:26px 0 30px; background:rgba(5,8,13,.9); text-align:center; {BC} font-size:128px; line-height:.95; color:#fff; text-shadow:0 8px 34px rgba(0,0,0,.9); }}
.endq em {{ font-style:normal; color:{Y}; }}
"""

CSS += f"""
.hk.big {{ font-size:220px; }}
"""



CSS += f"""
.ttl {{ position:absolute; left:40px; right:40px; display:grid; justify-items:center; text-align:center; {BC} font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.6); }}
.ttl.big {{ font-size:158px; }} .ttl .tl {{ display:block; }} .ttl .acc {{ color:{HOT}; }} .ttl .tw {{ display:inline-block; }}
.ttl.band {{ left:0; right:0; padding:22px 30px 26px; background:rgba(5,8,13,.84); font-size:104px; }}
.ttl.nyk {{ top:820px; font-size:150px; }} .ttl.nyk .acc {{ color:{Y}; }}
.seam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; left:0; right:0; height:960px; }} .half.t {{ top:0; }} .half.b {{ top:960px; }}
.hlab {{ position:absolute; left:50%; transform:translateX(-50%); top:40px; padding:8px 20px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:54px; white-space:nowrap; }}
.half.b .hlab {{ top:175px; }}
.yl {{ color:{Y}; }} .hot {{ color:{HOT}; }} .cy {{ color:{CYAN}; }}
.fpl {{ position:absolute; left:0; right:0; top:1770px; text-align:center; {MONO} font-size:24px; letter-spacing:.1em; color:{CYAN}; }}
.note {{ position:absolute; left:60px; right:60px; text-align:center; font-family:"Inter", sans-serif; font-weight:700; font-size:31px; line-height:1.3; color:#dfe5ec; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.84); }}
.note b {{ color:#fff; font-weight:800; }}
.chip {{ position:absolute; left:50%; transform:translateX(-50%); padding:12px 26px; border-radius:14px; background:rgba(6,10,18,.88); {BC} font-size:64px; white-space:nowrap; }}
.pin.cy span {{ background:{CYAN}; }} .pin.gr span {{ background:#3dd68c; }}
.rs2 {{ position:absolute; left:50%; transform:translateX(-50%); padding:10px 22px; border-radius:12px; background:rgba(6,10,18,.9); {BC} font-size:60px; white-space:nowrap; }}
.stamp {{ position:absolute; left:0; right:0; top:1180px; text-align:center; {BC} font-size:190px; line-height:1; color:{Y}; text-shadow:0 10px 40px rgba(0,0,0,.9); }}
.brand {{ position:absolute; inset:0; display:grid; place-content:center; justify-items:center; gap:28px; background:radial-gradient(ellipse at 50% 45%, rgba(10,16,28,.94), rgba(3,6,11,.98)); }}
.bname {{ display:grid; justify-items:center; {BC} line-height:.9; }} .bname span {{ font-size:120px; color:#fff; }} .bname em {{ font-style:normal; font-size:150px; color:{HOT}; letter-spacing:.02em; }}
"""


CSS += f"""
.ttl.hk2 {{ font-size:112px; }}
.nc {{ position:absolute; left:40px; top:1380px; display:flex; align-items:center; gap:18px; padding:12px 24px 12px 12px; border-radius:16px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.14); }}
.nc i {{ display:grid; place-items:center; width:84px; height:84px; border-radius:12px; background:{Y}; color:#05080d; font-style:normal; {BC} font-size:72px; }}
.nc b {{ {BC} font-size:60px; line-height:1; color:#fff; }}
.chip.lb {{ color:{CYAN}; }}
.pin.sm span {{ font-size:34px; padding:6px 12px; }}
"""


CSS += f"""
.ttl.band {{ left:0; right:0; padding:20px 30px 24px; background:rgba(5,8,13,.86); font-size:92px; }}
.ttl.big {{ font-size:150px; }}
.howto {{ position:absolute; left:48px; right:48px; top:1430px; display:grid; gap:14px; }}
.hrow {{ display:flex; align-items:center; gap:18px; padding:14px 22px 14px 14px; border-radius:16px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.12); }}
.hrow i {{ display:grid; place-items:center; width:64px; height:64px; flex:none; border-radius:12px; background:{CYAN}; color:#05080d; font-style:normal; {BC} font-size:52px; }}
.hrow + .hrow i {{ background:#f4f2ec; }}
.hrow span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:36px; line-height:1.2; color:#dfe5ec; }} .hrow b {{ color:#fff; font-weight:800; }}
.vd {{ position:absolute; left:50%; transform:translateX(-50%); top:40px; display:inline-flex; align-items:center; gap:14px; padding:10px 22px 10px 12px; border-radius:14px; background:rgba(6,10,18,.9); {BC} font-size:56px; white-space:nowrap; }}
.half.b .vd {{ top:auto; bottom:40px; }}
.vd i {{ display:grid; place-items:center; width:62px; height:62px; border-radius:50%; font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:40px; color:#05080d; }}
.vd.ok {{ color:{GREEN}; }} .vd.ok i {{ background:{GREEN}; }} .vd.no {{ color:{RED}; }} .vd.no i {{ background:{RED}; }}
"""

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [("0.0", "5.0", "The hook: the bag on the mound, close; he walks over and picks it up; zoom in; he squeezes it and rubs his fingertips", "WHAT IS THIS LITTLE WHITE BAG?"),
          ("5.0", "13.0", "The problem: the ball in his hand; in on his fingers on the seams; sweat beads up; the ball shifts; he resets his grip", "MOISTURE MAKES GRIP HARDER"),
          ("13.0", "23.0", "How rosin works: back to the bag; rosin dust onto his fingertips as the sweat dries; he rubs it in; grips the seams again", "BETTER MOISTURE CONTROL. MORE CONSISTENT GRIP."),
          ("23.0", "33.0", "Why grip matters: fastball (23.0), curveball (26.3), changeup (29.7): the grip close, the release slowed, the ball on its way", "EVERY FINGER MATTERS"),
          ("33.0", "39.0", "The rules: the bag behind the rubber; split: legal rosin (top) vs rosin mixed with sunscreen (bottom)", "LEGAL ROSIN. ILLEGAL FOREIGN SUBSTANCES."),
          ("39.0", "43.0", "The ending: he delivers (release 41.1); the bag behind the mound", "NOW YOU KNOW. (from 41.6)"),
          ("43.0", f"{D:.1f}", "End card", "BASEBALL DECODED")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Why pitchers use the rosin bag", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Scene timing for the voiceover", "", f"The video is {D:.1f} s. Record each part of the narration inside its scene (times in seconds).", "",
             "| From | To | Scene | On screen |", "|---|---|---|---|"] + [f"| {a} | {b} | {d} | {t} |" for a, b, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
