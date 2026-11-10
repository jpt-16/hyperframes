"""'Pitch tipping' (1080x1920, music + effects; the narration is recorded separately).

    python3 tools/physics.py        # the fastball, the curveball, the batted ball -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (music + effects, mastered low for a voice on top) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/tipping.mp4 --video-bitrate 16M

One pitcher, batter and catcher throughout. The tells are hypothetical examples for this one pitcher: where his hands
come set, the glove flaring while he changes grip, how long he holds the set. The scouting room is its own 3D scene; its
video wall plays two live renders of the same pitcher.
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
D = 55.6
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
D_SWEET = round(2.30 - 0.283, 3)
TC = lambda pk: PI_[pk]["t_contact"]

SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def live(a, b, cam, **kw): shot(a, b, cam, [a, b], [a, b], **kw)
def vt(play):
    for s in SHOTS:
        for (v0, v1), (t0, t1) in zip(zip(s["vs"], s["vs"][1:]), zip(s["ts"], s["ts"][1:])):
            if t1 > t0 and t0 <= play <= t1: return v0 + (play - t0) / (t1 - t0) * (v1 - v0)
    return None
TOPP, BOTP = [0, 0, 1080, 960], [0, 960, 1080, 960]
def ab(pk, rel, tell, hit=None, swing=False): return dict(pk=pk, rel=rel, tell=tell, hit=hit, swing=swing, D=D_SWEET)
def pset(t_set, **tell): return dict(tell, rel=t_set + 1.05 + 30, hold=30)      # comes set at t_set and stays there
# 1 the hook: on the mound; the batter looks out; the delivery, frozen before release; into the glove
H_REL = 3.45
AH = ab("cb", H_REL, dict(glove="hi", hold=1.0))
live(0.0, 1.6, "world", ab=AH, c0=[-12.0, 5.2, -57.4], c1=[-11.2, 5.1, -57.8], l=[0.0, 4.6, -60.4], f0=30)
live(1.6, 2.5, "world", ab=AH, c0=[-3.3, 7.0, 3.2], c1=[-3.3, 6.95, 2.9], l=[0.0, 5.0, -60.4], f0=14)
FRZ = H_REL - 0.3
live(2.5, FRZ, "world", ab=AH, c0=[-1.6, 7.0, 9.5], c1=[-1.6, 7.0, 9.3], l=[0.0, 5.0, -58.0], f0=12)
shot(FRZ, 5.0, "aim", [FRZ, 5.0], [FRZ, FRZ], speed="freeze", ab=AH, ring=[[FRZ + 0.1, 0.0], [FRZ + 0.3, 1.0]], lo="glove", l=[0, 0, 0], c0=[-9.0, 5.4, -46.0], f0=16, f1=7.0)
# 2 three tells (hypothetical, this pitcher): split top/bottom, the same pitcher before a fastball and a curveball
SIDE = dict(c0=[-11.5, 5.4, -58.4], c1=[-11.0, 5.35, -58.6], l=[0.0, 4.6, -60.4], f0=22)
E1 = 5.6
shot(5.0, 9.0, "world", [5.0, 6.4, 9.0], [5.0, 6.4, 6.4], panes=[dict(rect=TOPP, pset=pset(E1, glove="lo")), dict(rect=BOTP, pset=pset(E1, glove="hi"))], ring=[[6.3, 0.0], [6.5, 1.0]], **SIDE)
E2 = 9.45
CLOSEG = dict(c0=[-9.6, 5.9, -58.2], c1=[-9.0, 5.85, -58.4], l=[0.0, 5.3, -60.4], f0=22)
shot(9.0, 13.0, "world", [9.0, 11.2, 13.0], [9.0, 10.0, 10.0], panes=[dict(rect=TOPP, pset=pset(E2, glove="hi")), dict(rect=BOTP, pset=pset(E2, glove="hi", flare=1))], ring=[[9.95, 0.0], [10.0, 1.0]], **CLOSEG)
E3 = 13.4
A3F, A3C = ab("fb", E3 + 1.05 + 0.9, dict(glove="hi", hold=0.9)), ab("cb", E3 + 1.05 + 1.8, dict(glove="hi", hold=1.8))
live(13.0, 17.0, "world", panes=[dict(rect=TOPP, ab=A3F), dict(rect=BOTP, ab=A3C)], c0=[-19.0, 5.0, -54.5], c1=[-18.4, 5.0, -55.0], l=[0.0, 4.2, -58.6], f0=28)
# 3 the scouting room: the video wall plays both pitches on a loop
live(17.0, 19.4, "world", room=1, c0=[6.5, 7.6, 17.5], c1=[5.6, 7.5, 16.0], l=[-1.0, 4.8, -4.0], f0=46)
live(19.4, 22.0, "world", room=1, ring="both", c0=[-1.6, 7.4, 3.8], c1=[-1.6, 7.4, 3.2], l=[-1.6, 7.4, -5.9], f0=44)
live(22.0, 24.4, "world", room=1, ring="both", loghl=[22.3, 23.9], c0=[3.55, 7.4, 2.6], c1=[3.55, 7.4, 2.2], l=[3.55, 7.4, -5.9], f0=50)
live(24.4, 27.0, "world", room=1, ring="both", loghl=[0, 0.01], recog=24.8, cpoint=24.6, c0=[10.0, 6.4, 4.2], c1=[9.2, 6.3, 4.6], l=[-1.5, 4.6, 5.6], f0=44)
# 4 relaying it: the runner at second reads the catcher's signs and signals the batter; another team's signal from the dugout
SG = [[27.4, 3], [27.9, 1], [28.4, 2], [28.9, 4], [29.6, 1], [30.2, 2], [30.8, 3]]
live(27.0, 29.4, "world", runner=1, signs=SG, c0=[-7.3, 7.4, -136.0], c1=[-7.25, 7.3, -135.0], l=[0.0, 2.6, 0.0], f0=22, f1=19)
live(29.4, 31.6, "aim", runner=1, signs=SG, lens=1, lo="chand", l=[0, 0.25, 0], c0=[-6.3, 5.5, -121.6], f0=2.4, f1=2.1)
RS = [32.1, 32.9]
live(31.6, 33.4, "world", runner=1, rsig=RS, c0=[-17.0, 4.6, -113.0], c1=[-16.4, 4.6, -113.6], l=[-6.5, 4.2, -122.5], f0=18)
live(33.4, 35.0, "world", runner=1, bnod=33.9, c0=[-3.3, 7.0, 3.2], c1=[-3.3, 6.95, 2.9], l=[-6.5, 4.0, -122.5], f0=11)
CS = 35.5
live(35.0, 37.3, "obj", o="croot", lo="croot", csig=[CS], c0=[1.4, 5.6, 10.5], c1=[1.2, 5.5, 9.8], l=[0.0, 5.0, 0.0], f0=22)
live(37.3, 39.0, "world", runner=1, c0=[1.6, 8.4, 12.0], c1=[1.5, 8.2, 11.5], l=[-1.8, 3.0, -3.0], f0=34)
# 5 the payoff: from the batter's eyes, the tell; the curveball, seen early, barreled; the ball to the outfield
P_REL = 42.2
A5 = ab("cb", P_REL, dict(glove="hi", hold=1.1), "ld_cb", True)
live(39.0, 42.25, "world", ab=A5, ring=[[40.1, 0.0], [40.4, 1.0], [41.1, 1.0], [41.35, 0.0]], streak=1, c0=[-3.9, 5.95, 1.9], c1=[-3.85, 5.95, 1.7], l=[0.0, 5.0, -58.0], f0=13, f1=12)
SL5 = 0.25
shot(42.25, 44.65, "world", [42.25, 44.65], [42.25, 42.25 + 2.4 * SL5], speed="slow", ab=A5, ghost=0.018, c0=[2.8, 3.4, -8.6], c1=[2.5, 3.3, -8.0], l=[-1.6, 3.0, -1.6], f0=34)
shot(44.65, 49.0, "follow", [44.65, 49.0], [42.75, 47.1], ab=A5, streak=1, c0=[-4.8, 4.5, 6.0], c1=[-4.9, 5.2, 6.8], l=[0.0, 3.6, -40.0], f0=32, f1=42, lag=0.5, fw=0.85)
# 6 the final shot: back up the mound, looking in; the ball in his hand
live(49.0, 51.8, "world", walkback=[49.0, 51.2], c0=[2.6, 4.4, -44.0], c1=[2.2, 4.5, -45.5], l=[0.4, 5.0, -61.0], f0=24)
HB = [24.0, 9.0, 28.0]
live(51.8, 53.8, "world", ballhand=1, bokeh=2.6, close=1, c0=[HB[0] + 0.35, HB[1] + 0.5, HB[2] + 1.55], c1=[HB[0] + 0.25, HB[1] + 0.48, HB[2] + 1.3], l=[HB[0], HB[1] + 0.42, HB[2]], f0=30, roll=2.4)
VBRAND = 53.8
live(VBRAND, D, "world", walkback=[0, 0.1], c0=[2.6, 4.4, -44.0], l=[0.4, 5.0, -61.0], f0=24)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [5.0, 9.0, 13.0, 17.0, 27.0, 39.0, 49.0, VBRAND]:
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


# 1 the hook
title("t1", 0.1, 4.95, [("What if the hitter", False), ("knew the pitch", False), ("before it was thrown?", True)], 200, "hk2 h3")
pinl("ph1", FRZ + 0.35, 4.98, "The glove", "glove", "yl sm")
# 2 three tells (hypothetical examples, one pitcher)
panesTB("pp", 5.0, 16.98, "Before the fastball", "Before the curveball")
title("e1", 5.1, 8.98, [("Glove position", True)], 852, "band")
pinl("pe1a", 6.45, 8.98, "Hands at the belt", "glove", "sm", 0)
pinl("pe1b", 6.55, 8.98, "Hands at the chest", "glove", "yl sm", 1)
frz("fz1", 6.4, 8.98)
title("e2", 9.1, 12.98, [("Hand movement", True)], 852, "band")
pinl("pe2a", 10.4, 12.98, "Glove stays still", "glove", "sm", 0)
pinl("pe2b", 10.5, 12.98, "Glove flares as he changes his grip", "glove", "yl sm", 1)
frz("fz2", 11.2, 12.98)
title("e3", 13.1, 16.98, [("Delivery timing", True)], 852, "band")
tbar("tb1", 13.1, 16.98, 760, E3, E3 + 0.9, "0.9 s")
tbar("tb2", 13.1, 16.98, 1720, E3, E3 + 1.8, "1.8 s", "yl")
note("n2", 5.3, 12.98, "Hypothetical examples for one pitcher. Real tells vary, and no single move always means one pitch.", 1760)
# 3 the scouting room
title("t3a", 17.1, 19.98, [("Study the video", True)], 110)
title("t3b", 20.05, 26.98, [("Find the pattern", True)], 110)
pinl("ps1", 19.6, 21.98, "Before the fastball: hands at the belt", "scrA", "sm")
pinl("ps2", 19.75, 21.98, "Before the curveball: hands at the chest", "scrB", "yl sm")
pinl("ps3", 22.45, 24.38, "Hands at the chest → curveball, every time in this log", "scrLog", "yl sm")
pinl("ps4", 24.95, 26.98, "There it is", "rp2", "cy sm")
note("n3", 24.6, 26.98, "Teams look for a move that <b>repeats</b>, not one clip.", 1700)
# 4 relaying it
title("t4a", 27.1, 31.55, [("Recognize it", True)], 230)
c.clip("lens", 29.4, 31.58, '<div class="lens"></div><div class="lenstag">Runner’s view</div>', cls="layer", style="z-index:4")
pinl("pr1", 30.25, 31.58, "Second sign is live: 2 = curveball (this example)", "chand", "yl sm")
title("t4b", 31.7, 34.98, [("Relay it", True)], 230)
pinl("pr2", 32.15, 33.38, "Prearranged signal: hand to the helmet", "runner", "yl sm")
pinl("pr3", 33.95, 34.98, "Got it", "bhead", "cy sm")
pinl("pr4", 35.4, 37.28, "Another team: a signal from the dugout", "coach", "sm")
note("n4", 35.6, 37.28, "Every team sets its own signals, and changes them.", 1700)
title("t4c", 37.4, 38.98, [("Use the advantage", True)], 230)
note("n4b", 37.45, 38.98, "Reading signs by sight is part of the game. Using electronics to steal them is against MLB rules.", 1700)
# 5 the payoff
pinl("p5", 40.45, 41.3, "Hands at the chest: curveball coming", "glove", "yl sm")
title("t5", 44.75, 48.95, [("Knowing the pitch", False), ("changes everything", True)], 230)
# 6 the final shot
title("t6", 49.1, VBRAND - 0.02, [("The best pitchers", False), ("don’t give", False), ("anything away.", True)], 230)
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
for tt in [0.1, FRZ, 5.1, 9.1, 13.1, 17.1, 20.05, 27.1, 31.7, 37.4, 44.75, 49.1]: cue("impact", tt, -6)
for t_, n in SG: cue("tick", t_, -16)
for a_ in [A3F, A3C, A5]: cue("whoosh", vt(a_["rel"]), -8)
for a_ in [A3F, A3C]: cue("glove", vt(a_["rel"] + PI_[a_["pk"]]["flight"]), -2)
CRACKS = [(vt(P_REL + TC("cb")), True)]
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
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=171)
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
.ttl.hk2 {{ font-size:112px; }} .ttl.big2 {{ font-size:124px; }} .ttl.h3 {{ font-size:104px; }}
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
.pin.cy span {{ background:{CYAN}; }}
"""

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [("0.0", "5.0", "On the mound, he looks in and comes set; the batter looks out; the delivery, frozen before release; the camera pushes into his glove", "WHAT IF THE HITTER KNEW THE PITCH BEFORE IT WAS THROWN?"),
          ("5.0", "9.0", "Example 1, split top/bottom: where his hands come set before a fastball (belt) and a curveball (chest); freeze", "GLOVE POSITION"),
          ("9.0", "13.0", "Example 2: close on the glove at the set; before the curveball it flares while he changes his grip; freeze", "HAND MOVEMENT"),
          ("13.0", "17.0", "Example 3: how long he holds the set: 0.9 s before the fastball, 1.8 s before the curveball (timer bars)", "DELIVERY TIMING"),
          ("17.0", "27.0", "The scouting room: a coach and two hitters; the video wall plays both pitches; the pitch log lights up the pattern; a hitter points it out", "STUDY THE VIDEO (17.1) · FIND THE PATTERN (20.1)"),
          ("27.0", "39.0", "Runner at second reads the catcher's signs (runner's view 29.4); hand to the helmet (32.1); the batter gets it (33.9); another team's coach signals from the dugout (35.5)", "RECOGNIZE IT (27.1) · RELAY IT (31.7) · USE THE ADVANTAGE (37.4)"),
          ("39.0", "49.0", "From the batter's eyes: the tell; the curveball, barreled in slow motion (contact 43.9); the line drive into left-center", "KNOWING THE PITCH CHANGES EVERYTHING (from 44.8)"),
          ("49.0", "53.8", "Back up the mound, looking in; the ball in his hand, close", "THE BEST PITCHERS DON'T GIVE ANYTHING AWAY."),
          ("53.8", f"{D:.1f}", "End card", "BASEBALL DECODED")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Pitch tipping", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Scene timing for the voiceover", "", f"The video is {D:.1f} s. Record each part of the narration inside its scene (times in seconds).", "",
             "| From | To | Scene | On screen |", "|---|---|---|---|"] + [f"| {a} | {b} | {d} | {t} |" for a, b, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
