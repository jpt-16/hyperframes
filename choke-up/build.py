"""'Is choking up actually worth it?' (1080x1920, music + effects; the narration is recorded separately).

    python3 tools/physics.py        # the pitches and batted balls -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (music + effects, mastered low for a voice on top) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/choke-up.mp4 --video-bitrate 16M

One batter (same model and uniform throughout), one bat, a two-hand grip that slides up the handle. Each at-bat is a
pitch from physics.py; the swing is placed so the bat meets the ball at a set distance from the hands, the same for both
grips, so what changes between them is only where the bat's sweet spot and end are.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PI_, HI_ = P["pitches"], P["hits"]
D = 50.0
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
HM_FULL, CHK = 0.158 + 0.125, 0.167                       # the middle of the hands above the knob; choking up moves them 2 in
D_SWEET_FULL, D_SWEET_CHOKE = round(2.30 - HM_FULL, 3), round(2.30 - HM_FULL - CHK, 3)   # hands -> sweet spot

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def live(a, b, cam, **kw): shot(a, b, cam, [a, b], [a, b], **kw)
def vt(play):
    """The video time at which a play time is shown (the first shot that shows it)."""
    for s in SHOTS:
        t0, t1 = s["ts"][0], s["ts"][-1]
        if t0 <= play <= t1 and t1 > t0: return s["a"] + (play - t0) / (t1 - t0) * (s["b"] - s["a"])
    return None
L, R = [0, 0, 540, 1920], [540, 0, 540, 1920]
TOPP, BOTP = [0, 0, 1080, 960], [0, 960, 1080, 960]
def ab(pk, rel, hit=None, D=D_SWEET_CHOKE, swing=True): return dict(pk=pk, rel=rel, hit=hit, D=D, swing=swing)
TC = lambda pk: PI_[pk]["t_contact"]
CLOSE = dict(cam="obj", o="bat", lo="bat", bokeh=2.4, close=1, fore=1)
# 1 the hook: he steps in, normal grip; extreme close on the hands; they slide up the handle
live(0.0, 1.5, "world", walk=[0.0, 1.05], c0=[3.4, 3.8, -6.0], c1=[2.9, 3.7, -5.4], l=[-3.6, 3.6, 1.6], f0=40)
live(1.5, 2.6, **CLOSE, c0=[1.65, 0.4, 0.3], c1=[1.45, 0.38, 0.24], l=[0.0, 0.3, 0.0], f0=30)
CH1 = [[2.85, 0.0], [3.45, 1.0]]
live(2.6, 4.0, **CLOSE, cht=CH1, c0=[1.6, 0.55, -0.4], c1=[1.5, 0.55, -0.36], l=[0.0, 0.36, 0.0], f0=30)
# 2 what choking up does: split screen, the same batter with each grip; the hands close; the effective length
PFULL, PCHOKE = dict(choke=0, rect=L), dict(choke=1, rect=R)
live(4.0, 7.2, "world", panes=[PFULL, PCHOKE], c0=[9.0, 4.6, 0.6], c1=[8.2, 4.6, 0.6], l=[-3.1, 4.3, 0.45], f0=40)
live(7.2, 9.4, **dict(CLOSE, bokeh=4.5), panes=[PFULL, PCHOKE], c0=[2.6, 0.45, -0.75], c1=[2.4, 0.45, -0.7], l=[0.0, 0.34, 0.0], f0=34)
CH2 = [[10.0, 0.0], [10.9, 1.0]]
live(9.4, 12.0, "obj", o="bat", lo="bat", bokeh=9, close=1, fore=1, nobody=1, len=1, cht=CH2, c0=[6.0, 1.45, -0.4], c1=[5.6, 1.45, -0.35], l=[0.2, 1.72, 0.0], f0=33)
# 3 the advantages: 99 mph; the controlled swing in slow motion; the hands; the contact point; a quick adjustment up and in
A3 = ab("mid", 13.2, "ld_mid")
live(12.0, 13.35, "world", ab=A3, choke=1, streak=1, c0=[-3.6, 8.0, -76.0], c1=[-3.4, 7.8, -75.0], l=[0.0, 3.8, -20.0], f0=22)
S3 = 0.18
shot(13.35, 16.8, "world", [13.35, 16.8], [13.35, 13.35 + 3.45 * S3], speed="slow", ab=A3, choke=1, ghost=0.016, c0=[2.8, 3.4, -8.6], c1=[2.5, 3.3, -8.0], l=[-1.6, 3.0, -1.6], f0=34)
shot(16.8, 18.4, "world", [16.8, 18.4], [13.45, 13.45 + 1.6 * 0.19], speed="slow", ab=A3, choke=1, ghost=0.016, close=1, c0=[2.2, 4.0, -6.8], c1=[2.0, 3.95, -6.4], l=[-2.0, 3.5, -0.8], f0=30)
CP3 = PI_["mid"]["contact"]
shot(18.4, 20.0, "world", [18.4, 20.0], [13.2 + TC("mid") - 0.03, 13.2 + TC("mid") + 0.05], speed="slow", ab=A3, choke=1, close=1,
     c0=[CP3[0] + 1.5, CP3[1] + 0.5, CP3[2] - 1.6], c1=[CP3[0] + 1.3, CP3[1] + 0.45, CP3[2] - 1.4], l=CP3, f0=30)
A3E = ab("hin", 20.55, "ld_hin")
shot(20.0, 22.0, "world", [20.0, 22.0], [20.25, 21.25], speed="slow", ab=A3E, choke=1, streak=1, c0=[1.6, 8.4, 12.0], c1=[1.5, 8.2, 11.5], l=[-1.8, 3.0, -3.0], f0=34)
# 4 the tradeoff: reach (overhead, frozen at contact) on a pitch away; then away and inside, each grip
A4 = ab("away", 23.0, None, D_SWEET_FULL)
FZ = 23.0 + TC("away")
shot(22.0, 24.6, "world", [22.0, 24.6], [FZ, FZ], speed="freeze", ab=A4, panes=[dict(PFULL, reach=0, rect=TOPP), dict(PCHOKE, reach=1, rect=BOTP)], up=[0, 0, -1], c0=[-1.3, 15.0, -1.4], c1=[-1.3, 13.6, -1.4], l=[-1.3, 0.0, -1.401], f0=30)
A4A = ab("away", 25.1, None, D_SWEET_FULL)
UMP = dict(c0=[2.4, 8.6, 12.5], c1=[2.3, 8.4, 12.0], l=[-0.8, 2.8, -6.0], f0=34, streak=1)
BEH = dict(c0=[-2.2, 7.4, 10.8], c1=[-2.1, 7.6, 11.2], l=[-0.6, 2.6, -16.0], f0=40, streak=1)
shot(24.6, 27.6, "world", [24.6, 27.6], [24.85, 24.85 + 3.0 * 0.6], speed="slow", ab=A4A, panes=[dict(PFULL, rect=TOPP, ab=dict(A4A, hit="away_full")), dict(PCHOKE, rect=BOTP, ab=dict(A4A, hit="away_choke"))], **BEH)
A4B = ab("in", 28.0, None, D_SWEET_CHOKE)
shot(27.6, 32.0, "world", [27.6, 32.0], [27.75, 27.75 + 4.4 * 0.6], speed="slow", ab=A4B, panes=[dict(PFULL, rect=TOPP, ab=dict(A4B, hit="in_full")), dict(PCHOKE, rect=BOTP, ab=dict(A4B, hit="in_choke"))], **BEH)
# 5 when hitters use it: two strikes; high velocity; a tough at-bat
CH5A = [[32.35, 0.0], [32.95, 1.0]]
live(32.0, 33.4, "world", cht=CH5A, c0=[6.5, 5.0, 1.2], c1=[6.0, 4.95, 1.1], l=[-3.0, 4.4, 0.5], f0=30)
A5A = ab("sl", 33.6, "foul_sl")
CF = dict(c0=[-3.0, 9.0, -112.0], c1=[-3.0, 9.0, -110.0], l=[-0.9, 3.2, 0.0], f0=7.5, f1=7.2)
live(33.4, 35.4, "world", ab=A5A, choke=1, **CF)
A5B = ab("fire", 36.45, "foul_back")
live(35.4, 36.6, "world", ab=A5B, choke=1, c0=[-4.4, 4.7, 4.2], c1=[-4.3, 4.65, 4.0], l=[0.0, 5.4, -60.0], f0=14)
live(36.6, 38.7, "world", ab=A5B, choke=1, **BEH)
CH5C = [[39.0, 0.0], [39.6, 1.0]]
live(38.7, 40.0, "world", cht=CH5C, c0=[7.5, 4.8, -5.0], c1=[7.0, 4.7, -4.6], l=[-3.0, 4.2, 0.5], f0=28)
A5C = ab("late", 40.3, "gb_late")
live(40.0, 42.0, "world", ab=A5C, choke=1, **CF)
# 6 the takeaway: the line drive; the bat finishing its swing in slow motion
A6 = ab("final", 42.6, "ld_final", D_SWEET_CHOKE)
live(42.0, 44.4, "follow", ab=A6, choke=1, streak=1, c0=[-4.8, 4.5, 6.0], c1=[-4.9, 5.0, 6.6], l=[0.0, 3.6, -40.0], f0=32, f1=40, lag=0.6, fw=0.8)
shot(44.4, 47.8, "world", [44.4, 47.8], [42.6 + TC("final") - 0.08, 42.6 + TC("final") + 0.72], speed="slow", ab=A6, choke=1, ghost=0.02,
     c0=[3.4, 1.8, -10.0], c1=[3.0, 1.7, -9.2], l=[-2.6, 4.4, -0.4], f0=36)
live(47.8, D, "world", ab=A6, choke=1, c0=[3.0, 1.7, -9.2], c1=[2.9, 1.7, -9.0], l=[-2.6, 4.4, -0.4], f0=36)
VBRAND = 47.8
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]
CONTACTS = []                                              # (video time, kind) of each contact the viewer sees
for s in SHOTS:
    abx = [pn.get("ab", s.get("ab")) for pn in s.get("panes", [{}])]
    for a_ in abx[:1]:
        if a_ and a_.get("swing"):
            pt = a_["rel"] + TC(a_["pk"]); t0, t1 = s["ts"][0], s["ts"][-1]
            if t0 <= pt <= t1 and t1 > t0: CONTACTS.append((s["a"] + (pt - t0) / (t1 - t0) * (s["b"] - s["a"]), s["speed"]))

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [1.5, 2.6, 4.0, 9.4, 12.0, 22.0, 32.0, 35.4, 38.7, 42.0, VBRAND]:
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
def tag(tid, t0, t1, text, cls=""):
    c.clip(tid, t0, t1, f'<div class="tagc {cls}" id="{tid}x">{text}</div>', cls="layer", style="z-index:16"); pop(f"#{tid}x", t0, 10)

# 1 the hook
title("t1", 0.15, 3.95, [("Is choking up", False), ("actually worth it?", True)], 230, "hk2 big2")
pinl("pn1", 1.65, 2.58, "Normal grip: hands at the knob", "bottom", "yl sm")
pinl("pn2", 3.5, 3.98, "Hands up the handle", "bottom", "cy sm")
# 2 what it does
panes2("pa", 4.0, 9.38, "Full grip", "Choked up", 140)
pinl("pk1", 7.45, 9.38, "Hands at the knob", "bottom", "yl sm", 0)
pinl("pk2", 7.6, 9.38, "Knob showing", "knob", "cy sm", 1)
title("t2", 9.5, 11.98, [("Shorter effective", False), ("bat length", True)])
pinl("pl1", 9.7, 11.98, "Effective length", "lenmid", "cy sm")
pinl("pl2", 11.0, 11.98, "≈ 2 in shorter", "bottom", "sm")
# 3 the advantages
chip("rad", 12.25, 13.33, '<span class="radar">99</span> MPH', 1500, "rd")
title("t3", 13.45, 17.98, [("More", False), ("control", True)])
pinl("ph3", 16.95, 18.38, "Hands stay compact", "hands", "sm")
pinl("pb3", 17.4, 18.38, "Bat path", "end", "yl sm")
pinl("pc3", 18.75, 19.98, "Contact point", "ball", "cy sm")
title("t3b", 20.05, 21.98, [("Quicker barrel", False), ("adjustments", True)])
note("n3", 18.5, 21.98, "Choking up doesn’t automatically add bat speed or guarantee contact. It can make the bat <b>easier to control</b>.", 1700)
# 4 the tradeoff
title("t4", 22.1, 24.58, [("More control", False), ("vs. more reach", True)], 852, "band")
chip("t4s", 24.6, 31.98, 'More control <span class="vsd">vs.</span> <b class="y">more reach</b>', 70, "hdr")
panesTB("pt", 22.0, 31.98, "Full grip", "Choked up")
pinl("pr1", 22.4, 24.58, "Barrel on the ball", "ball", "yl sm", 0)
pinl("pr2", 22.55, 24.58, "End of the bat", "ball", "cy sm", 1)
chip("tg1", 24.7, 27.58, "Pitch away", 918, "seamc")
pinl("po1", vt(25.1 + TC("away")) + 0.4, 27.58, "Barrel: line drive", "ball", "yl sm", 0)
pinl("po2", vt(25.1 + TC("away")) + 0.5, 27.58, "Off the end: soft grounder", "ball", "cy sm", 1)
chip("tg2", 27.7, 31.98, "Pitch inside", 918, "seamc")
pinl("po3", vt(28.0 + TC("in")) + 0.4, 29.9, "In on the hands: soft grounder", "ball", "yl sm", 0)
pinl("po4", vt(28.0 + TC("in")) + 0.5, 29.9, "Barrel: line drive", "ball", "cy sm", 1)
note("n4", 29.9, 31.98, "Neither grip wins every pitch. It depends on the <b>hitter</b>, the <b>pitch</b> and the <b>situation</b>.", 1760)
# 5 when hitters use it
title("t5a", 32.1, 35.38, [("Two strikes", True)])
chip("cnt1", 32.2, 35.38, 'Count <b class="y">0–2</b>', 1500)
pinl("pg5", 32.95, 33.38, "Chokes up", "hands", "cy sm")
note("n5", 33.5, 35.38, "Some hitters choke up with two strikes to protect the plate. Many don’t.", 1700)
title("t5b", 35.5, 38.68, [("High velocity", True)])
chip("rad2", vt(36.45) + 0.05, 38.68, '<span class="radar">100</span> MPH', 1500, "rd")
title("t5c", 38.8, 41.98, [("Better contact", True)])
chip("cnt3", 38.9, 41.98, 'Count <b class="y">3–2</b>', 1500)
pinl("pg6", 39.6, 39.98, "Chokes up", "hands", "cy sm")
note("n5c", 40.2, 41.98, "The goal, not a guarantee.", 1700)
# 6 the takeaway
title("t6", 42.1, 44.38, [("It’s not about", False), ("swinging harder.", True)])
title("t7", 44.5, VBRAND - 0.02, [("It’s about controlling", False), ("the barrel.", True)])
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
for tt in [0.15, 9.5, 13.45, 22.1, 32.1, 35.5, 38.8, 42.1, 44.5]: cue("impact", tt, -6)
for tt in [2.85, 10.0, 32.35, 39.0]: cue("tap", tt + 0.1, -10)            # the hands sliding on the handle
for a_, s_ in [(A3, None), (A3E, None), (A4A, None), (A4B, None), (A5A, None), (A5B, None), (A5C, None), (A6, None)]:
    cue("whoosh", vt(a_["rel"]), -8)
CRACKS = [(t_, sp) for t_, sp in CONTACTS]
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
        x = crack(rng, sp == "slow"); i = int(vt_ * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * 10 ** (-4 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-26 / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=151)
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
.ttl.hk2 {{ font-size:112px; }} .ttl.big2 {{ font-size:124px; }}
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
SCENES = [("0.0", "4.0", "The hook: he steps in, normal grip; extreme close on the hands; they slide up the handle (2.9–3.5)", "IS CHOKING UP ACTUALLY WORTH IT?"),
          ("4.0", "12.0", "Split screen: the same batter, full grip and choked up; the hands, close; the bat with the effective-length bar shrinking (10.0–10.9)", "SHORTER EFFECTIVE BAT LENGTH (from 9.5)"),
          ("12.0", "22.0", "99 mph; the controlled swing in slow motion with its bat path; the hands; the contact point; up and in, a quick adjustment (from 20.0)", "MORE CONTROL (13.5) · QUICKER BARREL ADJUSTMENTS (20.0)"),
          ("22.0", "32.0", "Overhead at contact: the reach of each grip; a pitch away, each grip (full: line drive; choked: off the end); a pitch inside (full: in on the hands; choked: line drive)", "MORE CONTROL VS. MORE REACH"),
          ("32.0", "42.0", "Two strikes: he chokes up, fights off a slider (foul); 100 mph: fouled straight back; full count: he chokes up, hard grounder up the middle", "TWO STRIKES (32.1) · HIGH VELOCITY (35.5) · BETTER CONTACT (38.8)"),
          ("42.0", "47.8", "The line drive into left-center; the bat finishing its swing in slow motion", "IT'S NOT ABOUT SWINGING HARDER. (42.1) · IT'S ABOUT CONTROLLING THE BARREL. (44.5)"),
          ("47.8", f"{D:.1f}", "End card", "BASEBALL DECODED")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Is choking up actually worth it?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Scene timing for the voiceover", "", f"The video is {D:.1f} s. Record each part of the narration inside its scene (times in seconds).", "",
             "| From | To | Scene | On screen |", "|---|---|---|---|"] + [f"| {a} | {b} | {d} | {t} |" for a, b, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; contacts {[round(x, 2) for x, _ in CONTACTS]}; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots; contacts {[round(x, 2) for x, _ in CONTACTS]}")
