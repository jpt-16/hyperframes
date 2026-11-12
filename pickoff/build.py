"""'Pickoff throw out of play: one base or two?' (1080x1920, music + effects; no narration).

    python3 tools/physics.py        # the field model -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (music + effects, mastered low for a voice on top) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/pickoff.mp4 --video-bitrate 16M

A right-handed pitcher in the set, a runner on first. The same wild pickoff throw goes into the first-base dugout twice:
  "on":  his pivot (right) foot stays in contact with the rubber, his free foot steps directly toward first, he throws.
         A throw by the pitcher from the rubber that goes out of play: 1 base (OBR 5.06(b)(4)(H)). Runner: first -> second.
  "off": his pivot foot steps backward off the rubber first. He's now an infielder (OBR 5.07(e)); then he steps toward
         first and throws. A wild throw by an infielder that goes out of play: 2 bases (5.06(b)(4)(G)). First -> third.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
D = 38.0
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
T_TURN0, T_OFF0, T_OFF1, T_TH, T_DEAD, T_AWARD = -0.62, -1.32, -0.98, 0.9, 1.35, 2.45   # mirror assets/field.js

SHOTS = []
def shot(a, b, cam, vs, ts, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], **kw))
def rt(a, b, cam, t0, r=1.0, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], **kw)
def vat(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
LR = [[0, 0, 540, 1920], [540, 0, 540, 1920]]
# cameras (world: c0 -> c1, looking at l -> l1, field of view f0 -> f1)
FEET_ON = dict(c0=[1.4, 2.7, -53.4], c1=[1.2, 2.4, -54.2], l=[0.6, 1.25, -60.5], f0=42)            # low, from the home side: the rubber and both feet
FEET_OFF = dict(c0=[-4.4, 4.4, -64.2], c1=[-3.9, 4.0, -63.8], l=[0.0, 0.85, -61.0], f0=40)   # above and behind, third-base side: the rubber, the gap, the foot           # low, from the third-base side: the step back
BEHIND = dict(c0=[-14.0, 9.0, -66.0], c1=[-13.4, 8.8, -65.6], l=[6.0, 3.0, -61.0], f0=40)           # behind the mound, third-base side, toward first
THROW = dict(c0=[-8.0, 7.5, -70.0], c1=[-6.5, 7.4, -69.0], l=[70.0, 4.0, -55.0], f0=30)         # the throw, the leap, the dugout
def DUGCAM(): return dict(c0=[74.9, 6.5, -70.7], c1=[76.5, 6.2, -69.5], l=[100.4, 3.5, -52.4], f0=50) # in foul territory, looking into the dugout's first-base end
UMP = dict(c0=[90.5, 5.2, -61.0], c1=[89.6, 5.1, -61.8], l=[78.4, 4.6, -70.0], f0=40)
AWARD = dict(c0=[86.0, 13.0, -47.0], c1=[84.0, 12.5, -49.0], l=[28.0, 1.0, -100.0], f0=44)
AT2 = dict(c0=[-16.0, 6.0, -110.0], c1=[-15.0, 5.8, -111.0], l=[2.0, 3.0, -127.0], f0=36)
AT3 = dict(c0=[-45.0, 6.0, -45.0], c1=[-46.0, 5.8, -46.5], l=[-62.0, 3.0, -67.0], f0=40)

# ----------------------------------------------------------------- 1 the hook (0-4): his feet on the rubber; the runner's lead; the move; freeze before the throw
rt(0.0, 1.15, "world", -3.6, play="on", leadAt=-2.75, c0=[-7.0, 2.6, -57.0], c1=[-4.6, 1.8, -58.2], l=[0.1, 0.9, -59.5], f0=44, f1=36)
rt(1.15, 1.95, "world", -2.45, play="on", leadAt=-2.75, c0=[61.0, 3.4, -47.0], c1=[60.0, 3.2, -48.5], l=[58.0, 2.8, -70.0], f0=36)
VFZ = 2.9; TFZ = -0.06
rt(1.95, VFZ, "world", TFZ - (VFZ - 1.95), play="on", leadAt=-2.75, **BEHIND)
V1 = 4.0
shot(VFZ, V1, "world", [VFZ, V1], [TFZ, TFZ], play="on", leadAt=-2.75, rub=-9, pivr=-9, c0=BEHIND["c1"], c1=[-5.0, 2.6, -62.4], l=BEHIND["l"], l1=[0.6, 1.0, -60.6], f0=40, f1=32)

# ----------------------------------------------------------------- 2 one base (4-12): he stays on the rubber
V2 = 12.0
rt(V1, 5.0, "world", -1.72, play="on", c0=[73.0, 5.0, -74.0], c1=[71.5, 4.9, -73.6], l=[20.0, 3.6, -63.0], f0=30)
S2F = 6.75
shot(5.0, 7.25, "world", [5.0, S2F, 7.25], [-0.74, 0.0, 0.0], play="on", rub=-0.6, pivr=-0.6, arStep=-0.5, **FEET_ON)
rt(7.25, 8.45, "follow", 0.0, play="on", fo="ball", fw=0.25, **THROW)
rt(8.45, 9.15, "world", 0.52, play="on", **DUGCAM())
rt(9.15, 10.75, "world", 1.0, play="on", **UMP)
rt(10.75, 11.35, "world", 2.6, play="on", arAdv=2.35, **AWARD)
rt(11.35, V2, "world", 7.55, play="on", arAdv=-9, **AT2)

# ----------------------------------------------------------------- 3 two bases (12-22): he steps backward off the rubber first
V3 = 22.0
rt(V2, 13.1, "world", -3.1, play="off", c0=[-30.0, 24.0, -42.0], c1=[-28.0, 23.0, -43.5], l=[36.0, 0.0, -66.0], f0=40)
S3F = 14.9
shot(13.1, 16.0, "world", [13.1, S3F, 16.0], [-1.46, -0.9, -0.9], play="off", rub=-9, pivr=-9, arBack=-1.3, gap=-0.95, **FEET_OFF)
rt(16.0, 17.1, "world", -0.92, play="off", pivr=-9, **BEHIND)
rt(17.1, 18.2, "follow", 0.1, play="off", fo="ball", fw=0.25, **THROW)
rt(18.2, 18.9, "world", 0.52, play="off", **DUGCAM())
rt(18.9, 20.5, "world", 1.0, play="off", **UMP)
rt(20.5, 21.1, "world", 2.6, play="off", arAdv=2.35, **AWARD)
rt(21.1, V3, "world", 12.0, play="off", arAdv=-9, **AT3)

# ----------------------------------------------------------------- 4 why the rule changes (22-32): side by side, the pivot foot lit
V4 = 32.0
SPL = dict(c0=[0.8, 5.6, -48.6], c1=[0.8, 5.0, -50.4], l=[0.8, 1.9, -61.0], f0=62, f1=58)
S4F = 25.2
shot(V3, V4, "world", [V3, V4], [0, 0], panes=[dict(rect=LR[0], play="on", vs=[V3, S4F, V4], ts=[-0.78, 0.0, 0.0], rub=-9, pivr=-9),
                                              dict(rect=LR[1], play="off", vs=[V3, S4F, V4], ts=[-1.42, 0.0, 0.0], rub=-9, pivr=-9, gap=-0.95)], **SPL)

# ----------------------------------------------------------------- 5 the ending (32-38): where each runner ends up
VBRAND = 36.3
shot(V4, D, "world", [V4, D], [0, 0], panes=[dict(rect=LR[0], play="on", vs=[V4, D], ts=[9.0, 15.0], arAdv=-9, c0=[26.0, 12.0, -96.0], c1=[22.0, 10.5, -100.0], l=[2.0, 3.0, -126.0], f0=56),
                                            dict(rect=LR[1], play="off", vs=[V4, D], ts=[13.4, 19.4], arAdv=-9, c0=[-36.0, 12.0, -38.0], c1=[-40.0, 10.5, -42.0], l=[-62.0, 3.0, -66.0], f0=56)], c0=[0, 0, 0], l=[0, 0, -1])
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [VFZ, V1, V2, V3, V4]:
    c.set("#flash", '{"opacity":0.45}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls="", pane=0):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, pane])
def title(tid, t0, t1, lines, top=250, cls="hk2"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.06 * i)
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:13"); pop(f"#{nid}x", t0, 8)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def panes2(pid, t0, t1, a, b, top=150):
    c.clip(pid, t0, t1, f'<div class="vseam"></div><div class="plab" style="left:270px;top:{top}px" id="{pid}a">{a}</div><div class="plab cy" style="left:810px;top:{top}px" id="{pid}b">{b}</div>', cls="layer", style="z-index:15")
    pop(f"#{pid}a", t0 + 0.05, 10); pop(f"#{pid}b", t0 + 0.15, 10)
def panesTB(pid, t0, t1, a, b):
    c.clip(pid, t0, t1, f'<div class="hseam2"></div><div class="plab" style="left:200px;top:560px" id="{pid}a">{a}</div><div class="plab cy" style="left:200px;top:1520px" id="{pid}b">{b}</div>', cls="layer", style="z-index:15")
    pop(f"#{pid}a", t0 + 0.05, 10); pop(f"#{pid}b", t0 + 0.15, 10)
def panesTB(pid, t0, t1, a, b):
    c.clip(pid, t0, t1, f'<div class="hseam2"></div><div class="plab" style="left:230px;top:60px" id="{pid}a">{a}</div><div class="plab cy" style="left:230px;top:1020px" id="{pid}b">{b}</div>', cls="layer", style="z-index:15")
    pop(f"#{pid}a", t0 + 0.05, 10); pop(f"#{pid}b", t0 + 0.15, 10)
def frz(fid, t0, t1):
    c.clip(fid, t0, t1, f'<div class="frz" id="{fid}x">Freeze</div>', cls="layer", style="z-index:31"); pop(f"#{fid}x", t0, 6)
def tbar(bid, t0, t1, top, fill0, fill1, label, cls=""):
    c.clip(bid, t0, t1, f'<div class="tbar {cls}" style="top:{top}px"><i>Time in the set</i><div class="tb"><span id="{bid}f"></span></div><b id="{bid}l">{label}</b></div>', cls="layer", style="z-index:16")
    c.ft(f"#{bid}f", o(width="0%"), o(width="100%", duration=fill1 - fill0, ease="none"), fill0)
    c.ft(f"#{bid}l", o(opacity=0, scale=0.6), o(opacity=1, scale=1, duration=0.2, ease="back.out(2)"), fill1)
def tag(tid, t0, t1, text, cls=""):
    c.clip(tid, t0, t1, f'<div class="tagc {cls}" id="{tid}x">{text}</div>', cls="layer", style="z-index:16"); pop(f"#{tid}x", t0, 10)


def dots(n, mx, cls): return "".join(f'<i class="{cls if k < n else "off"}"></i>' for k in range(mx))
def bug(bid, t0, t1, b, s_, o_, top=60, label=None):
    """A broadcast-style count bug: balls and strikes as lights, and the count in big numbers."""
    big = "WALK" if b >= 4 else f"{b}-{s_}"
    lab = f'<em>{label}</em>' if label else ""
    c.clip(bid, t0, t1, f'<div class="bug" id="{bid}x" style="top:{top}px"><div class="bl"><span>B</span>{dots(min(b, 3), 3, "b")}<span>S</span>{dots(s_, 2, "s")}<span>O</span>{dots(o_, 2, "o")}</div><b class="{"w" if b >= 4 else ""}">{big}</b>{lab}</div>', cls="layer", style="z-index:18")
    pop(f"#{bid}x", t0, 8)
def meter(mid, t0, t1, p0, p1=None, tch=None, top=1560, label=""):
    """Who the count favors: a marker between PITCHER and HITTER."""
    c.clip(mid, t0, t1, f'<div class="meter" style="top:{top}px"><span class="pl">Pitcher</span><div class="tr"><div class="mk" id="{mid}m" style="left:{p0 * 100:.0f}%"></div></div><span class="hl">Hitter</span>{f"<em>{label}</em>" if label else ""}</div>', cls="layer", style="z-index:17")
    pop(f"#{mid}m", t0 + 0.05, 6)
    if p1 is not None: c.to(f"#{mid}m", o(left=f"{p1 * 100:.0f}%", duration=0.45, ease="power3.inOut"), tch)
BAND = 1640
def band(tid, t0, t1, lines, top=None): title(tid, t0, t1, lines, BAND if top is None else top, "band")
def stamp(sid, t0, t1, big, small):
    c.clip(sid, t0, t1, f'<div class="stampc" id="{sid}x"><b>{big}</b><span>{small}</span></div>', cls="layer", style="z-index:21")
    c.ft(f"#{sid}x", o(opacity=0, scale=1.25), o(opacity=1, scale=1, duration=0.18, ease="power3.out"), t0)

def big(bid, t0, t1, html, top=760, cls=""):
    """A full-width statement that slams in."""
    c.clip(bid, t0, t1, f'<div class="bigt {cls}" id="{bid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:23")
    c.ft(f"#{bid}x", o(opacity=0, scale=1.6, filter="blur(14px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def plabel(pid, t0, t1, x, top, html, cls=""):
    c.clip(pid, t0, t1, f'<div class="plb {cls}" id="{pid}x" style="left:{x}px;top:{top}px">{html}</div>', cls="layer", style="z-index:16"); pop(f"#{pid}x", t0, 10)
def award(aid, t0, t1, n, frm, to, top=1500, pane=None):
    """The base award: a mini diamond with the runner's path, and the number of bases."""
    pts = {1: (150, 80), 2: (80, 10), 3: (10, 80), 0: (80, 150)}
    path = " ".join(f"{pts[k][0]},{pts[k][1]}" for k in range(frm, to + 1))
    svg = f'''<svg viewBox="-10 -10 180 180" width="150" height="150"><polygon points="80,150 150,80 80,10 10,80" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="4"/>
      {"".join(f'<rect x="{pts[k][0] - 9}" y="{pts[k][1] - 9}" width="18" height="18" transform="rotate(45 {pts[k][0]} {pts[k][1]})" fill="#f4f6f8"/>' for k in (1, 2, 3))}
      <polyline points="{path}" fill="none" stroke="{Y}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" class="awp" pathLength="100"/>
      <circle cx="{pts[to][0]}" cy="{pts[to][1]}" r="15" fill="{Y}"/></svg>'''
    left = "50%" if pane is None else ("270px" if pane == 0 else "810px")
    c.clip(aid, t0, t1, f'<div class="award" id="{aid}x" style="top:{top}px;left:{left}">{svg}<div><b>{n} base{"s" if n > 1 else ""}</b><span>awarded</span></div></div>', cls="layer", style="z-index:17")
    pop(f"#{aid}x", t0, 14)

# 1 the hook
big("hq", VFZ + 0.02, V1 - 0.02, '<span>One step</span><span>= <em>one extra base?</em></span>', 470)
pinl("ph1", 0.25, 1.13, "His pivot foot, on the rubber", "pivot", "cy sm")
pinl("ph2", 1.25, 1.93, "The runner takes his lead", "runner", "yl sm")

# 2 one base
band("t2", V1 + 0.05, 9.13, [("1 · Stays on the rubber", True)])
pinl("p2a", 5.1, 7.23, "Pivot foot: on the rubber", "pivot", "cy sm")
pinl("p2b", 5.75, 7.23, "Steps directly toward first", "rubber", "sm")
note("n2", S2F - 0.15, 7.23, "He throws <b>while his pivot foot is touching the rubber</b>: it's the pitcher's throw.", 1430)
pinl("p2c", 7.75, 8.43, "Over the first baseman…", "b1", "sm")
pinl("p2d", 8.5, 9.13, "…into the dugout", "dugout", "rd sm")
stamp("s2", 9.35, 10.2, "Dead ball", "Out of play")
big("a2", 10.5, V2 - 0.02, '<span>1 base</span><span><em>awarded</em></span>', 330, "sm")
award("w2", 10.55, V2 - 0.02, 1, 1, 2, 1480)

# 3 two bases
band("t3", V2 + 0.05, 18.88, [("2 · Disengages the rubber", True)])
chip("c3", V2 + 0.15, 13.08, "Same pitcher · same runner · same throw", 1500)
pinl("p3a", 13.2, S3F - 0.02, "Pivot foot steps <b>back</b> off the rubber", "pivot", "sm")
pinl("p3b", S3F, 16.0 - 0.02, "Off the rubber, behind it", "gap", "rd sm")
note("n3", S3F, 16.0 - 0.02, "The <b>pivot foot</b> steps backward first. Only then does he step toward first and throw.", 1430)
pinl("p3c", 16.05, 17.08, "Now he throws", "pitcher", "sm")
pinl("p3d", 18.25, 18.88, "…into the dugout", "dugout", "rd sm")
stamp("s3", 19.15, 20.0, "Dead ball", "Out of play")
big("a3", 20.3, V3 - 0.02, '<span>2 bases</span><span><em>awarded</em></span>', 330, "sm")
award("w3", 20.35, V3 - 0.02, 2, 1, 3, 1480)

# 4 why the rule changes
c.clip("vs4", V3, V4, '<div class="vseam"></div>', cls="layer", style="z-index:11")
band("t4", V3 + 0.05, V4 - 0.02, [("Why the rule changes", True)], 70)
plabel("l4a", V3 + 0.15, V4 - 0.02, 270, 250, "Pitcher", "cy")
plabel("l4b", V3 + 0.25, V4 - 0.02, 810, 250, "Now treated as<br>an infielder<br>for the throw", "or")
pinl("p4a", 22.6, V4 - 0.02, "On the rubber", "pivot", "cy sm", 0)
pinl("p4b", 22.7, V4 - 0.02, "Off the rubber", "pivot", "rd sm", 1)
RULE4 = 26.0
plabel("r4a", RULE4, V4 - 0.02, 270, 1290, "Throw out of play<br><b>1 base</b>", "rule")
plabel("r4b", RULE4 + 0.15, V4 - 0.02, 810, 1290, "Wild throw out of play<br><b>2 bases</b>", "rule or")
award("w4a", RULE4 + 0.5, V4 - 0.02, 1, 1, 2, 1530, 0); award("w4b", RULE4 + 0.65, V4 - 0.02, 2, 1, 3, 1530, 1)
note("n4", 27.2, V4 - 0.02, "Pivot foot touching the rubber: a <b>pitcher's</b> throw. Stepped backward off it: an <b>infielder's</b> throw.<br><i>MLB Official Baseball Rules 5.06(b)(4)(H), 5.07(e), 5.06(b)(4)(G)</i>", 1770)

# 5 the ending
c.clip("vs5", V4, D, '<div class="vseam"></div>', cls="layer", style="z-index:11")
pinl("p5a", V4 + 0.3, VBRAND - 0.02, "Ends at second", "base2", "yl sm", 0)
pinl("p5b", V4 + 0.4, VBRAND - 0.02, "Ends at third", "base3", "yl sm", 1)
plabel("l5a", V4 + 0.1, VBRAND - 0.02, 270, 1540, "On the rubber<br><b>1 base</b>", "rule")
plabel("l5b", V4 + 0.2, VBRAND - 0.02, 810, 1540, "Off the rubber<br><b>2 bases</b>", "rule or")
title("t5", V4 + 0.6, VBRAND - 0.02, [("Same throw.", False), ("Different rule.", True)], 250)

c.clip("brand", VBRAND, D, """<div class="brand ov" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.3), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- sound (no voice: room left for a narrator)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8); cue("riser-m", VFZ - 0.9, -9)
for tt in [VFZ, V1 + 0.05, 9.35, 10.5, V2 + 0.05, 19.15, 20.3, V3 + 0.05, RULE4, V4 + 0.6]: cue("impact", tt, -6)
for tt in [0.3, 1.25, 5.1, 5.75, 13.2, S3F, 22.6, 22.7]: cue("tick", tt, -10)
# the throws (release whoosh), the ball hitting the dugout wall, the runner's dive
for sh in SHOTS:
    if "panes" in sh: continue
    v = vat(sh, 0.0)
    if v is not None and sh["vs"][0] < v < sh["b"]: cue("whoosh", v, -4)
    v = vat(sh, T_TH + 0.07)
    if v is not None and sh["vs"][0] < v < sh["b"]: cue("tap", v, 2); cue("impact", v, -14)
CRACKS = []
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)

LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}
def crack(rng, slow=False):
    """Ash bat on a ball: a hard broadband click and a short wooden ring (lower and longer in slow motion)."""
    k = 0.55 if slow else 1.0
    t = np.arange(int((1.2 if slow else 0.6) * SR)) / SR
    click = rng.standard_normal(len(t)) * np.exp(-t / (0.0025 / k))
    ring = sum(a * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) * np.exp(-t / (d / k)) for f, a, d in [(1150, .55, .05), (1720, .4, .035), (2380, .3, .025), (640, .3, .07)])
    x = click * 0.9 + ring + np.sin(2 * np.pi * 180 * k * t) * np.exp(-t / (0.03 / k)) * 0.5
    x /= np.max(np.abs(x)); return np.stack([x, x], 1)

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    rng = np.random.default_rng(9)
    for vt_, sp in CRACKS:
        x = crack(rng, sp); i = int(vt_ * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * 10 ** (-4 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-26 / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=181)
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

CSS += f"""
.ttl.t3l {{ font-size:100px; }}
.bub {{ position:absolute; left:-260px; width:520px; bottom:30px; display:flex; flex-direction:column; align-items:center; }}
.bub i {{ font-style:normal; {MONO} font-size:20px; letter-spacing:.14em; color:{MUTED}; margin-bottom:6px; padding:3px 10px; border-radius:6px; background:rgba(6,10,18,.75); }}
.bub span {{ position:relative; padding:14px 24px; border-radius:22px; background:#f4f6f8; color:#0b1018; font-family:"Inter", sans-serif; font-weight:800; font-size:40px; line-height:1.15; text-align:center; box-shadow:0 8px 26px rgba(0,0,0,.45); }}
.bub span::after {{ content:""; position:absolute; left:50%; bottom:-16px; margin-left:-14px; border:14px solid transparent; border-top-color:#f4f6f8; border-bottom:0; }}
.bub.P span {{ background:{Y}; }} .bub.P span::after {{ border-top-color:{Y}; }}
.chip.cy {{ color:{CYAN}; }} .chip b.y {{ color:{Y}; }}
.chip .ear::before {{ content:"●"; color:{CYAN}; margin-right:12px; font-size:40px; vertical-align:middle; }}
.visg {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 50%, rgba(10,40,70,0) 34%, rgba(4,14,28,.78) 78%); mix-blend-mode:normal; }}
.vistag {{ position:absolute; right:40px; top:200px; padding:6px 14px; border-radius:8px; background:rgba(6,18,30,.8); {MONO} font-size:22px; letter-spacing:.16em; color:{CYAN}; text-transform:uppercase; }}
"""

CSS += f"""
.ttl.hk2 {{ font-size:112px; }} .ttl.band {{ font-size:88px; padding:18px 30px 22px; }} .ttl.big1 {{ font-size:220px; }}
.bug {{ position:absolute; left:40px; display:flex; align-items:center; gap:22px; padding:12px 22px 12px 18px; border-radius:16px; background:rgba(6,10,18,.9); border:2px solid rgba(255,255,255,.16); box-shadow:0 8px 26px rgba(0,0,0,.5); }}
.bug .bl {{ display:grid; grid-template-columns:auto repeat(3, 26px); gap:6px 8px; align-items:center; }}
.bug .bl span {{ {MONO} font-size:22px; color:{MUTED}; }} .bug .bl span:nth-of-type(n) {{ grid-column:1; }}
.bug .bl i {{ width:24px; height:24px; border-radius:50%; background:#1b2230; border:2px solid #2c3646; }}
.bug .bl i.b {{ background:{GREEN}; border-color:{GREEN}; }} .bug .bl i.s {{ background:{RED}; border-color:{RED}; }} .bug .bl i.o {{ background:{Y}; border-color:{Y}; }}
.bug b {{ {BC} font-size:118px; line-height:.9; color:#fff; letter-spacing:.02em; }} .bug b.w {{ color:{Y}; font-size:96px; }}
.bug em {{ font-style:normal; {BC} font-size:46px; color:{Y}; max-width:330px; line-height:1; }}
.meter {{ position:absolute; left:60px; right:60px; display:grid; grid-template-columns:auto 1fr auto; gap:18px; align-items:center; padding:14px 22px; border-radius:16px; background:rgba(6,10,18,.85); }}
.meter span {{ {BC} font-size:44px; }} .meter .pl {{ color:{HOT}; }} .meter .hl {{ color:{CYAN}; }}
.meter .tr {{ position:relative; height:18px; border-radius:9px; background:linear-gradient(90deg, {HOT}, #3a4250 50%, {CYAN}); }}
.meter .mk {{ position:absolute; top:50%; width:44px; height:44px; margin:-22px 0 0 -22px; border-radius:50%; background:#fff; border:5px solid #05080d; box-shadow:0 0 0 3px #fff; }}
.meter em {{ grid-column:1 / -1; justify-self:center; font-style:normal; {MONO} font-size:22px; letter-spacing:.12em; color:{MUTED}; text-transform:uppercase; }}
.stampc {{ position:absolute; left:0; right:0; top:620px; display:grid; justify-items:center; gap:10px; }}
.stampc b {{ {BC} font-size:300px; line-height:.9; color:#fff; text-shadow:0 10px 40px rgba(0,0,0,.85); }}
.stampc span {{ padding:8px 22px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:64px; color:{Y}; }}
.brand.ov {{ background:radial-gradient(ellipse at 50% 45%, rgba(10,16,28,.72), rgba(3,6,11,.55)); }}
.pin.gr span {{ background:{GREEN}; }} .ttl.big2 {{ font-size:124px; }} .ttl.h3 {{ font-size:104px; }}
.frz {{ position:absolute; right:44px; top:150px; padding:8px 16px; border-radius:8px; background:rgba(6,10,18,.8); {MONO} font-size:22px; letter-spacing:.14em; color:{CYAN}; }}
.frz::before {{ content:"❚❚ "; }}
.tbar {{ position:absolute; left:48px; width:520px; display:grid; grid-template-columns:1fr auto; gap:6px 14px; align-items:center; padding:12px 18px; border-radius:14px; background:rgba(6,10,18,.88); }}
.tbar i {{ grid-column:1 / -1; font-style:normal; {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; }}
.tbar .tb {{ height:18px; border-radius:9px; background:#26303f; overflow:hidden; }} .tbar .tb span {{ display:block; height:100%; width:0; background:{WHITE}; }}
.tbar.yl .tb span {{ background:{Y}; }} .tbar b {{ {BC} font-size:52px; color:#fff; }} .tbar.yl b {{ color:{Y}; }}
.lens {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 38%, rgba(0,0,0,.9) 62%); }}
.lenstag {{ position:absolute; left:50%; top:1480px; transform:translateX(-50%); padding:6px 16px; border-radius:8px; background:rgba(6,10,18,.85); {MONO} font-size:24px; letter-spacing:.14em; color:{CYAN}; text-transform:uppercase; }}
.vseam {{ position:absolute; top:0; bottom:0; left:538px; width:4px; background:rgba(255,255,255,.8); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.plab {{ position:absolute; transform:translateX(-50%); padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:54px; white-space:nowrap; color:{Y}; }}
.plab.cy {{ color:{CYAN}; }}
.hseam2 {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.8); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.tagc {{ position:absolute; left:0; right:0; margin:0 auto; width:max-content; top:1400px; padding:8px 24px; border-radius:12px; background:#05080d; border:3px solid {WHITE}; color:#fff; {BC} font-size:50px; white-space:nowrap; }}
.chip.seamc {{ background:{WHITE}; color:#05080d; font-size:50px; padding:6px 24px; z-index:20; }}
.chip.hdr {{ font-size:52px; padding:8px 22px; }} .chip .vsd {{ color:{MUTED}; }}
.chip.rd {{ color:#fff; }} .chip .radar {{ color:{Y}; font-size:84px; vertical-align:-4px; }}
.pin.cy span {{ background:{CYAN}; }} .pin.rd span {{ background:{RED}; color:#fff; }} .pin span b {{ color:#fff; }}
.pin.cy span b, .pin.yl span b {{ color:#05080d; text-decoration:underline; }}
.bigt {{ position:absolute; left:30px; right:30px; display:grid; justify-items:center; text-align:center; {BC} font-size:150px; line-height:.92; color:#fff; text-shadow:0 8px 34px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.7); }}
.bigt em {{ font-style:normal; color:{HOT}; }} .bigt.sm {{ font-size:132px; }} .bigt.sm em {{ color:{Y}; }}
.plb {{ position:absolute; transform:translateX(-50%); width:500px; text-align:center; padding:12px 14px; border-radius:14px; background:rgba(6,10,18,.88); border:3px solid {CYAN}; {BC} font-size:50px; line-height:1.0; color:{CYAN}; }}
.plb.or {{ border-color:{HOT}; color:{HOT}; }}
.plb.rule {{ border-color:rgba(255,255,255,.25); color:#dfe5ec; font-size:40px; }} .plb.rule b {{ display:block; font-size:78px; color:{Y}; margin-top:4px; }}
.award {{ position:absolute; transform:translateX(-50%); display:flex; align-items:center; gap:18px; padding:12px 26px 12px 14px; border-radius:18px; background:rgba(6,10,18,.88); }}
.award div {{ display:grid; {BC} line-height:.95; }} .award b {{ font-size:70px; color:{Y}; white-space:nowrap; }} .award span {{ font-size:36px; color:#dfe5ec; }}
.stampc {{ top:760px; }} .stampc b {{ font-size:220px; color:#fff; }} .stampc span {{ color:{RED}; }}
.note i {{ display:block; margin-top:6px; font-style:normal; font-size:22px; color:{MUTED}; font-weight:700; }}
"""


HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [(0.0, V1, "The hook", "His feet on the rubber; the runner's lead; the pickoff move, frozen before the throw; the camera pushes in on his feet", "ONE STEP = ONE EXTRA BASE?"),
          (V1, V2, "One base", "He keeps his pivot foot on the rubber and steps directly toward first; the throw sails over the first baseman into the dugout; dead ball; the runner goes to second", "STAYS ON THE RUBBER · 1 BASE AWARDED"),
          (V2, V3, "Two bases", "Reset; his pivot foot steps backward off the rubber; then he throws; into the dugout; dead ball; the runner goes to third", "DISENGAGES THE RUBBER · 2 BASES AWARDED"),
          (V3, V4, "Why", "Side by side at the release: pivot foot on the rubber (pitcher) vs. off it (infielder); the base award for each", "PITCHER · NOW TREATED AS AN INFIELDER FOR THE THROW"),
          (V4, D, "The ending", "Side by side: one runner on second, the other on third; Baseball Decoded", "SAME THROW. DIFFERENT RULE.")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Pickoff throw out of play", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Scene timing", "", f"The video is {D:.1f} s, music and effects only. Record a narration inside each scene (times in seconds).", "",
             "| From | To | Scene | Shots | On screen |", "|---|---|---|---|---|"] + [f"| {a:.1f} | {b:.1f} | {n} | {d} | {t} |" for a, b, n, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
