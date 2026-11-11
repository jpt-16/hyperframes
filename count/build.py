"""'The count' (1080x1920), cut to the voiceover ("How counts create leverage").

    python3 tools/physics.py        # the pitches and the foul ball -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/count.mp4 --video-bitrate 16M

One pitcher, batter, catcher and umpire throughout. Every count is on the center-field board (B / S / O lights and the
numbers) and in a broadcast-style count bug on screen. The strike zone and where each pitch crossed it are drawn at the
front of the plate; a pitch is a strike if any part of the ball touches the zone.
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
TMJ = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TMJ["lines"])}
LN = lambda lid: TMJ["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TMJ["duration"]
S = {x["id"]: x["t0"] - 0.08 for x in TMJ["lines"]}
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
D_SWEET = round(2.30 - 0.283, 3)
TC = lambda pk: PI_[pk]["t_contact"]
FRONT = lambda pk: PI_[pk]["front"]

SHOTS = []
BD = None
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    if "board" not in kw and BD: kw["board"] = BD
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def live(a, b, cam, **kw): shot(a, b, cam, [a, b], [a, b], **kw)
def vt(play, after=0.0):
    for s in SHOTS:
        if s["a"] < after: continue
        for (v0, v1), (t0, t1) in zip(zip(s["vs"], s["vs"][1:]), zip(s["ts"], s["ts"][1:])):
            if t1 > t0 and t0 <= play <= t1: return v0 + (play - t0) / (t1 - t0) * (v1 - v0)
    return None
TOPP, BOTP = [0, 0, 1080, 960], [0, 960, 1080, 960]
def ab(pk, rel, hold=1.0, hit=None, swing=False, check=None): return dict(pk=pk, rel=rel, tell=dict(glove="hi", hold=hold), hit=hit, swing=swing, check=check, D=D_SWEET)
BOARDCAM = dict(c0=[-30.0, 20.0, -170.0], c1=[-36.0, 24.0, -196.0], l=[-70.0, 74.0, -432.0], f0=27, f1=22)   # the board sits low, under the scene title
UMPV = dict(c0=[-0.4, 8.6, 12.5], c1=[-0.4, 8.5, 12.0], l=[-0.7, 2.3, -3.0], f0=24)
UMPVF = dict(c0=[-0.4, 7.8, 12.5], c1=[-0.4, 7.7, 11.8], l=[-0.6, 3.7, -3.0], f0=46)
CF = dict(c0=[-3.0, 9.0, -112.0], c1=[-3.0, 9.0, -110.0], l=[-0.9, 3.2, 0.0], f0=7.5, f1=7.2)
# 1 the hook: "Why can the exact same pitch be an easy take in one count… but a must-swing in another?"
#   a 95 mph fastball on the outside edge, frozen just before it reaches the hitter; the same pitch at 3-0 (top) and 0-2 (bottom)
V1, V2, V3, V4, V5, V6 = 0.0, S["a02"], S["a30"], S["a11"], S["a32"], S["e1"]
BD = [[0, -1, 0, 1, "95"]]
HR = 1.25; AH = ab("hook", HR, hold=0.7)
live(0.0, 1.38, "world", ab=AH, streak=1, c0=[-2.4, 6.6, -70.0], c1=[-2.2, 6.4, -69.0], l=[0.0, 4.0, -20.0], f0=26)
FZ = HR + 0.3
live(1.38, FZ, "world", ab=AH, streak=1, c0=[5.2, 3.3, -4.0], c1=[5.0, 3.3, -3.2], l=[0.0, 4.2, -40.0], f0=30)
HKL = [-0.2, 2.6, -8.0]                                             # the panes are framed low so the bugs and the band sit above the zone
shot(FZ, V2, "world", [FZ, V2], [FZ, FZ], speed="freeze", ab=AH, zone=1, panes=[dict(rect=TOPP), dict(rect=BOTP)], c0=[1.6, 6.4, 10.5], c1=[1.4, 6.2, 9.8], l=HKL, f0=30)
# 2 0-2: "With two strikes, the pitcher has the advantage. They can expand the zone, throw breaking balls off the plate,
#   and make the hitter protect against more possibilities."
BD = [[0, 0, 2, 1, ""]]
B2 = S["b02"] - 0.05
live(V2, B2, "world", **BOARDCAM)
C2 = W("b02", "throw") - 0.08
R2 = W("b02", "plate") - FRONT("sl02"); A2 = ab("sl02", R2, swing=True, check=0.1)
CHASE2 = W("b02", "expand")
live(B2, C2, "world", ab=A2, zone=1, chase=CHASE2, **UMPVF)
D2 = W("b02", "and") - 0.1
live(C2, D2, "world", ab=A2, zone=1, chase=0, **CF)
S2 = 0.3
shot(D2, V3, "world", [D2, V3], [R2 + 0.2, R2 + 0.2 + (V3 - D2) * S2], speed="slow", ab=A2, zone=1, mark=1, chase=0, c0=[2.4, 7.0, 12.5], c1=[2.2, 6.9, 11.8], l=[0.0, 2.6, -3.0], f0=40)
# 3 3-0: "But at 3-0, everything changes. The hitter can be much more selective because one ball means a walk.
#   The pitcher has very little room for error."
BD = [[0, 3, 0, 1, ""]]
B3 = S["b30"] - 0.3
live(V3, B3, "world", **BOARDCAM)
R3 = W("b30", "walk", end=True) + 0.05 - FRONT("fb30"); A3 = ab("fb30", R3, hold=1.6)
C3 = R3 + FRONT("fb30") + 0.4
live(B3, C3, "world", ab=A3, zone=1, mark=1, **UMPVF)
D3 = C3 + 0.65
live(C3, D3, "world", board=[[C3, 3, 0, 1], [C3 + 0.25, 4, 0, 1, "BALL FOUR"]], **BOARDCAM)
BD = [[0, 4, 0, 1, "BALL FOUR"]]
live(D3, V4, "world", ab=A3, bwalk=[D3 - 0.05, D3 + 2.4], c0=[-14.0, 6.0, 8.0], c1=[-13.0, 6.0, 6.0], l=[1.0, 3.0, -3.0], l1=[9.0, 3.0, -11.0], f0=36)
# 4 1-1: "At 1-1, neither side has a major advantage. The next pitch can shift the entire at-bat.
#   A strike creates 1-2, while a ball creates 2-1."   Top: a called strike on "strike"; bottom: a ball on "ball".
BD = [[0, 1, 1, 1, ""]]
B4 = W("a11", "neither") - 0.1
live(V4, B4, "world", **BOARDCAM)
CR4S, CR4B = W("c11", "strike") + 0.02, W("c11", "ball") + 0.02
A4S, A4B = ab("st11", CR4S - FRONT("st11")), ab("bl11", CR4B - FRONT("bl11"))
P4L = [-0.3, 2.7, -3.0]                                             # framed low: the bug and the meter above, the zone in the middle
shot(B4, V5, "world", [B4, V5], [B4, V5], zone=1, mark=1,
     panes=[dict(rect=TOPP, ab=A4S, ucall=CR4S + 0.15), dict(rect=BOTP, ab=A4B)], **dict(UMPV, l=P4L))
# 5 3-2: "And at a full count, every pitch matters. The hitter has to protect the strike zone, while the pitcher has to
#   throw a strike without giving up a good opportunity to hit."   The pitch is on the corner; he protects and fouls it back.
BD = [[0, 3, 2, 1, "FULL COUNT"]]
B5 = S["a32"] + 1.6
live(V5, B5, "world", **BOARDCAM)
C5 = W("b32", "hitter") - 0.05
R5 = W("b32", "pitcher") + 0.45; A5 = ab("fb32", R5, hold=2.0, hit="foul32", swing=True)
live(B5, C5, "world", ab=A5, c0=[-9.0, 3.2, -48.0], c1=[-8.4, 3.4, -50.0], l=[0.0, 5.4, -60.4], f0=26, f1=22)
D5 = W("b32", "while") - 0.08
live(C5, D5, "obj", ab=A5, o="bat", lo="bat", bokeh=2.4, close=1, fore=1, c0=[1.65, 0.4, 0.3], c1=[1.45, 0.38, 0.24], l=[0.0, 0.3, 0.0], f0=30)
E5 = R5 + 0.22
live(D5, E5, "world", ab=A5, streak=1, c0=[-3.3, 7.0, 3.2], c1=[-3.3, 6.95, 2.9], l=[0.0, 5.0, -60.4], f0=14, f1=16)
S5 = 0.3; F5 = W("b32", "hit") + 0.35
shot(E5, F5, "world", [E5, F5], [R5 + 0.22, R5 + 0.22 + (F5 - E5) * S5], speed="slow", ab=A5, ghost=0.016, zone=1, mark=1, c0=[1.4, 7.0, 12.0], c1=[1.2, 6.9, 11.2], l=[-0.4, 3.9, -3.0], f0=40)
T5 = R5 + 0.22 + (F5 - E5) * S5
shot(F5, V6, "world", [F5, V6], [R5 + TC("fb32") - 0.08, R5 + TC("fb32") - 0.08 + (V6 - F5) * 0.33], speed="slow", ab=A5, streak=1, c0=[5.0, 3.0, -22.0], c1=[5.0, 3.6, -23.5], l=[-1.0, 9.5, 8.0], f0=56)
# 6 "That's what makes baseball so strategic." the four counts, quickly; "The count doesn't just track balls and strikes."
#   the board; "It changes the leverage of every pitch." wide over the stadium; the closing title and the logo
MT = [V6 + 0.6 * k for k in range(5)]
BD = [[0, 0, 2, 1, ""]]
shot(MT[0], MT[1], "world", [MT[0], MT[1]], [R2 + TC("sl02") - 0.1] * 2, speed="freeze", ab=A2, zone=1, chase=0, **dict(CF, f0=7.0))
BD = [[0, 3, 0, 1, ""]]
shot(MT[1], MT[2], "world", [MT[1], MT[2]], [R3 + 0.5] * 2, speed="freeze", ab=A3, zone=1, mark=1, **UMPVF)
BD = [[0, 1, 1, 1, ""]]
shot(MT[2], MT[3], "world", [MT[2], MT[3]], [CR4S + 0.45] * 2, speed="freeze", ab=A4S, zone=1, mark=1, ucall=CR4S + 0.15, **UMPVF)
BD = [[0, 3, 2, 1, "FULL COUNT"]]
shot(MT[3], MT[4], "world", [MT[3], MT[4]], [R5 + TC("fb32") + 0.01] * 2, speed="freeze", ab=A5, ghost=0.016, c0=[2.8, 3.4, -8.6], l=[-1.6, 3.0, -1.6], f0=34)
G6 = S["e3"] - 0.05
live(MT[4], G6, "world", **BOARDCAM)
VEND = LN("e3")["t1"] + 0.15; VBRAND = round(VEND + 1.2, 3)
live(G6, D, "world", c0=[14.0, 58.0, 92.0], c1=[10.0, 78.0, 128.0], l=[0.0, 0.0, -150.0], f0=42, f1=46)

for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [V2, V3, V4, V5] + MT + [G6]:
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
BAND = 560                                                        # scene titles sit in a band under the captions
def band(tid, t0, t1, lines): title(tid, t0, t1, lines, BAND, "band")
def stamp(sid, t0, t1, big, small):
    c.clip(sid, t0, t1, f'<div class="stampc" id="{sid}x"><b>{big}</b><span>{small}</span></div>', cls="layer", style="z-index:21")
    c.ft(f"#{sid}x", o(opacity=0, scale=1.25), o(opacity=1, scale=1, duration=0.18, ease="power3.out"), t0)

# 1 the hook (the hook title stands in for the question's captions)
title("t1", 0.1, FZ - 0.02, [("95 mph", True)], 240, "hk2")
panesTB("pp", FZ, V2 - 0.02, "", "")
bug("g1a", FZ + 0.05, V2 - 0.02, 3, 0, 1, 60, "Easy take"); bug("g1b", W("q", "must") - 0.1, V2 - 0.02, 0, 2, 1, 1020, "Must swing")
title("t1b", FZ + 0.15, V2 - 0.02, [("Same pitch.", False), ("Different advantage.", True)], 852, "band")
pinl("p1", FZ + 0.4, V2 - 0.02, "On the edge: a strike", "zone", "sm", 0)
# 2 0-2
band("t2", V2 + 0.05, V3 - 0.02, [("0-2: Pitcher’s", False), ("advantage", True)])
bug("g2", B2, V3 - 0.02, 0, 2, 1)
meter("m2", W("a02", "advantage") - 0.05, V3 - 0.02, 0.5, 0.18, W("a02", "advantage") + 0.1)
pinl("p2c", CHASE2 + 0.1, C2 - 0.02, "Chase zone", "chase", "rd sm")
pinl("p2a", vt(R2 + TC("sl02") - 0.05, C2), D2 - 0.02, "He starts the swing… and holds up", "batter", "sm")
pinl("p2b", vt(R2 + FRONT("sl02"), D2) + 0.1, V3 - 0.02, "Just off the plate", "mark", "gr sm")
note("n2", W("b02", "protect") - 0.1, V3 - 0.02, "<b>Hitter:</b> anything close could be strike three, so he has to protect.<br><b>Pitcher:</b> can work off the plate and try to get a chase.", 1680)
# 3 3-0
band("t3", V3 + 0.05, V4 - 0.02, [("3-0: Hitter’s", False), ("advantage", True)])
bug("g3", V3 + 0.05, C3 + 0.23, 3, 0, 1)
meter("m3", W("a30", "everything") - 0.05, V4 - 0.02, 0.5, 0.85, W("a30", "changes"))
chip("c3", W("b30", "one") - 0.05, C3 - 0.02, "One more ball is a walk", 1450, "rd")
pinl("p3", vt(R3 + FRONT("fb30"), B3) + 0.1, C3 - 0.02, "Ball four: just off the plate", "mark", "gr sm")
bug("g3b", C3 + 0.25, V4 - 0.02, 4, 0, 1)
note("n3", W("c30", "very") - 0.1, V4 - 0.02, "At 3-0 the pitcher can’t afford another ball, so the hitter can wait for a strike he likes.", 1700)
# 4 1-1
title("t4", V4 + 0.05, B4 - 0.02, [("1-1", True)], 560, "hk2 big1")
bug("g4", V4 + 0.05, B4 - 0.02, 1, 1, 1)
bug("g4a", B4 + 0.05, CR4S + 0.3, 1, 1, 1, 60); bug("g4b", B4 + 0.1, CR4B + 0.3, 1, 1, 1, 1020)
bug("g4c", CR4S + 0.32, V5 - 0.02, 1, 2, 1, 60, "Strike: pitcher ahead"); bug("g4d", CR4B + 0.32, V5 - 0.02, 2, 1, 1, 1020, "Ball: hitter ahead")
panesTB("pq", B4, V5 - 0.02, "", "")
title("t4b", B4 + 0.1, V5 - 0.02, [("1-1: The next pitch", False), ("changes everything", True)], 852, "band")
meter("m4a", B4 + 0.2, V5 - 0.02, 0.5, 0.3, CR4S + 0.35, 780); meter("m4b", B4 + 0.25, V5 - 0.02, 0.5, 0.68, CR4B + 0.35, 1740)
pinl("p4a", CR4S + 0.1, V5 - 0.02, "Strike", "mark", "sm", 0); pinl("p4b", CR4B + 0.1, V5 - 0.02, "Ball", "mark", "gr sm", 1)
# 5 3-2
band("t5", V5 + 0.05, V6 - 0.02, [("3-2: Every pitch", False), ("matters", True)])
bug("g5", B5, V6 - 0.02, 3, 2, 1)
meter("m5", B5 + 0.1, D5 - 0.02, 0.5, label="Both under pressure")
note("n5", B5 + 0.2, D5 - 0.02, "<b>Hitter:</b> a strike he takes is strike three.<br><b>Pitcher:</b> a ball is ball four.", 1700)
pinl("p5a", vt(R5 + FRONT("fb32"), E5) + 0.1, F5 - 0.02, "On the corner: a strike, but hard to hit", "mark", "sm")
chip("p5", vt(R5 + TC("fb32"), E5) + 0.2, F5 - 0.02, "He protects: <b class=\"y\">fouled off</b>", 1500)
chip("c5", F5 + 0.1, V6 - 0.02, "Foul with two strikes: still <b class=\"y\">3-2</b>", 1500)
# 6 the four counts; the board; the stadium
stamp("s1", MT[0], MT[1] - 0.02, "0-2", "Pitcher’s advantage"); stamp("s2", MT[1], MT[2] - 0.02, "3-0", "Hitter’s advantage")
stamp("s3", MT[2], MT[3] - 0.02, "1-1", "Up for grabs"); stamp("s4", MT[3], MT[4] - 0.02, "3-2", "Every pitch matters")
title("t6", VEND, VBRAND - 0.02, [("The count is more", False), ("than a number.", True)], 300)

c.clip("brand", VBRAND, D, """<div class="brand ov" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.3), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)


# ----------------------------------------------------------------- captions: the voiceover, word by word (the question in the hook is covered by the hook title)
DISP = {("a30", 2): "3-0,", ("a30", 3): "", ("a30", 4): "", ("a11", 1): "1-1,", ("a11", 2): "", ("a11", 3): "", ("b11", 7): "at-bat.", ("b11", 8): "",
        ("c11", 3): "1-2,", ("c11", 4): "", ("c11", 5): "", ("c11", 10): "2-1.", ("c11", 11): "", ("c11", 12): ""}
A_ = "acc"
CAPS = [("a02", 0, 2, {1: A_, 2: A_}), ("a02", 3, 7, {7: A_}),
        ("b02", 0, 4, {2: A_, 4: A_}), ("b02", 5, 7, {6: A_, 7: A_}), ("b02", 8, 10, {10: A_}), ("b02", 11, 15, {15: A_}), ("b02", 16, 18, {}),
        ("a30", 0, 4, {2: A_}), ("a30", 5, 6, {6: A_}),
        ("b30", 0, 6, {6: A_}), ("b30", 7, 12, {9: A_, 12: A_}),
        ("c30", 0, 2, {}), ("c30", 3, 7, {4: A_, 5: A_}),
        ("a11", 0, 3, {1: A_}), ("a11", 4, 9, {8: A_, 9: A_}),
        ("b11", 0, 4, {4: A_}), ("b11", 5, 8, {7: A_}),
        ("c11", 0, 5, {1: A_, 3: A_}), ("c11", 6, 12, {8: A_, 10: A_}),
        ("a32", 0, 4, {3: A_, 4: A_}), ("a32", 5, 7, {7: A_}),
        ("b32", 0, 4, {4: A_}), ("b32", 5, 7, {6: A_, 7: A_}), ("b32", 8, 12, {}), ("b32", 13, 15, {15: A_}), ("b32", 16, 19, {}), ("b32", 20, 23, {20: A_, 21: A_}),
        ("e1", 0, 3, {}), ("e1", 4, 5, {5: A_}),
        ("e2", 0, 3, {1: A_}), ("e2", 4, 7, {5: A_, 7: A_}),
        ("e3", 0, 3, {3: A_}), ("e3", 4, 6, {5: A_, 6: A_})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]; i1 = min(i1, len(wd) - 1)
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TMJ["lines"]): end = min(ln["t1"] + 0.35, TMJ["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, VEND - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = DISP.get((lid, n), wd[n]["w"])
        if not w: continue
        w = w.rstrip(",:") if n == i1 and i1 > i0 else w
        w = w.replace("'", "’")
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        if DISP.get((lid, n), wd[n]["w"]): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8)
for tt in [0.1, FZ, V2 + 0.05, V3 + 0.05, V4 + 0.05, B4 + 0.1, V5 + 0.05] + MT[:4] + [VEND]: cue("impact", tt, -6)
for tt in [V2 + 0.05, V3 + 0.05, C3 + 0.25, V4 + 0.05, V5 + 0.05, CR4S + 0.32, CR4B + 0.32, G6 + 0.05]: cue("tick", tt, -8)
cue("popup", CHASE2, -4)
for a_, after in [(AH, 0), (A2, C2), (A3, B3), (A4S, B4), (A4B, B4), (A5, D5)]: cue("whoosh", vt(a_["rel"], after), -8)
for a_, after in [(A2, D2), (A3, B3), (A4S, B4), (A4B, B4)]: cue("glove", vt(a_["rel"] + PI_[a_["pk"]]["flight"], after), -1)
CRACKS = [(vt(R5 + TC("fb32"), E5), True)]
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
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]; vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
    env = np.convolve(np.abs(vo).mean(1), np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
    duck = 10 ** (-7 * np.clip(env / 0.05, 0, 1) / 20)
    duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), "same")
    music = bed * ramp * duck[:, None] * 10 ** (-17 / 20)
    full = (fx + music) * 10 ** (-6 / 20) + vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, (fx + bed * ramp * 10 ** (-17 / 20)) * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=pfx)
    os.remove(pre); os.remove(pfx)
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
.pin.cy span {{ background:{CYAN}; }} .pin.rd span {{ background:{HOT}; color:#fff; }}
.cap {{ position:absolute; left:52px; right:40px; }}
.cap .cl {{ display:block; {BC} font-size:88px; line-height:.96; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{HOT}; }}
"""

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [(0.0, V2, "the hook", "A 95 mph fastball on the outside edge, frozen just before it reaches the hitter; split: the same pitch at 3-0 (easy take) and 0-2 (must swing)"),
          (V2, V3, "0-2", "The board; the chase zone; a slider just off the plate, he starts the swing and holds up; slowed, with the zone"),
          (V3, V4, "3-0", "The board; a fastball just off the plate, taken; the board: ball four, walk; he drops the bat and jogs to first"),
          (V4, V5, "1-1", "The board; split: a called strike (1-2) on top, a ball (2-1) below"),
          (V5, V6, "3-2", "The board; he comes set; the hitter's hands; the pitch on the corner; he fouls it back"),
          (V6, D, "the takeaway", "The four counts; the board; wide over the stadium; Baseball Decoded")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The count", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Voiceover cues", "", f"The video is {D:.1f} s. To record your own read over `assets/mix-novo.wav`, start each line at its time (seconds).", "",
             "| Start | End | Scene | Line |", "|---|---|---|---|"]
    for a, b, name, desc in SCENES:
        for ln in TMJ["lines"]:
            if a - 0.01 <= ln["t0"] < b: lines.append(f"| {ln['t0']:.2f} | {ln['t1']:.2f} | {name} | {ln['text']} |")
    lines += ["", "## Scenes", "", "| From | To | Scene | Shots |", "|---|---|---|---|"] + [f"| {a:.2f} | {b:.2f} | {n} | {d} |" for a, b, n, d in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
