"""'Why the best play isn\'t always the easy out' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the grounders (a hard one at him, a slow roller) -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav + CUES.md
    node render_par.js . <chunk dir> 30 <duration> 90 <port>

The series' fielding rig with runners on the bases (R, R2), a base-state widget (runners and outs), overhead views with arrows, a double play, and a deep ball the shortstop keeps.
No claim is made that any one decision is always right; the situation decides.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
S = {x["id"]: round(x["t0"] - 0.08, 3) for x in TM["lines"]}
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED, AMBER = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D", "#FFB547"

SHOTS = []
def shot(a, b, cam, vs, ts, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], **kw))
def vat(vs, ts, t):
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
NEVER = 1e9


PLN = json.load(open(os.path.join(HERE, "tools", "plan.json"))) if os.path.exists(os.path.join(HERE, "tools", "plan.json")) else {k: dict(tf=1.6, tr=2.2, ta=2.7) for k in ("easy", "lead", "hold")}
E, LD, HO = PLN["easy"], PLN["lead"], PLN["hold"]
DP = PLN.get("dp", dict(tf=2.1, tr1=2.46, ta=2.74, tr2=2.94, ta2=3.63))
# cameras: follow2 rides with a fielder; home is the origin, center field toward -z, first base toward +x, second base at (0, -127)
CLOSE = dict(who="ss", off=[-9, 3.2, -9], lo=[2, -0.5, 6], f0=34)                               # the shortstop and his feed
FACE = dict(who="ss", off=[3, 3.0, 8], lo=[0, 0.2, 0], f0=30, close=1)                          # his face, from the front
FIELDV = dict(c0=[15, 165, -98], l=[15, 0, -98], up=[1, 0, 0], f0=42)                         # the shortstop's throw and first base
BAGW = dict(c0=[16, 9, -108], c1=[13, 8, -110], l=[0, 1.8, -127], f0=36)                         # the bag from the first base side, high
BAGLOW = dict(c0=[14, 2.6, -118], c1=[11, 2.4, -120], l=[0, 2.0, -127], f0=34)
FOOT = dict(who="b2", off=[-5, 1.4, 8], lo=[0, -1.2, 0], f0=34, close=1)                         # the pivot, low on the feet
WIDEDP = dict(c0=[-16, 12, -150], c1=[-12, 11, -148], l=[0, 2.5, -124], f0=40)
HOLECU = dict(who="ss", off=[-6, 2.6, 15], lo=[0, -1.4, -1], f0=36, close=1)                      # deep in the hole, low
OHPANE = dict(c0=[20, 110, -95], l=[20, 0, -95], up=[0, 0, -1], f0=46)                           # overhead on the right side (half-height panes)
TOPSS = dict(c0=[-30, 130, -132], l=[-30, 0, -132], up=[1, 0, 0], f0=42)                          # overhead on the shortstop and second base
TOPALL = dict(c0=[15, 165, -98], l=[15, 0, -98], up=[1, 0, 0], f0=42)                            # overhead on the right side of the infield
TB = [[0, 0, 1080, 960], [0, 960, 1080, 960]]
V2, V3, V4, V5, V6 = S["p1"], S["p2"], S["p3"], S["p4"], S["e1"]
tfe, tfl, tfh = E["tf"], LD["tf"], HO["tf"]

# ----------------------------------------------------------------- 1 the hook: runner on first, a grounder to the shortstop, the easy out, frozen
RUN_E = [dict(who=1, from_="b1", to="b2", t0=-0.1, lead=12, slide=1)]
def rn(sp): return [{("from" if k == "from_" else k): v for k, v in d.items()} for d in sp]
shot(0.0, 1.2, "follow2", [0.0, 1.2], [tfe - 0.6, tfe + 0.3], play="easy", rn=rn(RUN_E), streak=1, **CLOSE)
shot(1.2, 2.3, "world", [1.2, 2.3], [E["tr"] - 0.05, E["ta"] - 0.02], play="easy", rn=rn(RUN_E), streak=1, **FIELDV)
shot(2.3, V2, "world", [2.3, V2], [E["ta"], E["ta"]], play="easy", rn=rn(RUN_E), **FIELDV)

# ----------------------------------------------------------------- 2 point 1: the lead runner
RUN_L = [dict(who=1, from_="b1", to="b2", tArr=LD["ta"] + 0.14, lead=12, slide=1)]
shot(V2, V2 + 1.3, "follow2", [V2, V2 + 1.3], [tfl - 0.55, tfl + 0.4], play="lead", rn=rn(RUN_L), flook=dict(at="b2", t=[tfl - 0.12, tfl + 0.5]), streak=1, **CLOSE)
shot(V2 + 1.3, V2 + 2.8, "world", [V2 + 1.3, V2 + 2.8], [LD["tr"] - 0.1, LD["ta"] + 0.4], play="lead", rn=rn(RUN_L), streak=1, **BAGW)
OUT1 = dict(rect=TB[0], play="easy", vs=[V2 + 2.8, V3], ts=[E["ta"] + 0.9, E["ta"] + 1.2], rn=[dict(who=1, stay="b2", lead=0)])
OUT2 = dict(rect=TB[1], play="lead", vs=[V2 + 2.8, V3], ts=[LD["ta"] + 0.9, LD["ta"] + 1.2], rn=[dict(who=1, hide=1), dict(who=2, stay="b1", lead=0)])
shot(V2 + 2.8, V3, "world", [V2 + 2.8, V3], [0, 0], panes=[OUT1, OUT2], **OHPANE)

# ----------------------------------------------------------------- 3 point 2: runners on first and second, one out: turn two
RUN_D = [dict(who=1, from_="b1", to="b2", tArr=DP["ta"] + 0.42, lead=12, slide=1), dict(who=2, from_="b2", to="b3", t0=-0.1, lead=10)]
shot(V3, V3 + 1.3, "follow2", [V3, V3 + 1.3], [DP["tf"] - 0.6, DP["tf"] + 0.3], play="dp", dp=1, rn=rn(RUN_D), streak=1, **CLOSE)
shot(V3 + 1.3, V3 + 3.0, "world", [V3 + 1.3, V3 + 3.0], [DP["tr1"] - 0.05, DP["ta2"] + 0.15], play="dp", dp=1, rn=rn(RUN_D), streak=1, **BAGW)
shot(V3 + 3.0, V3 + 5.0, "follow2", [V3 + 3.0, V3 + 5.0], [DP["ta"] - 0.15, DP["tr2"] + 0.4], play="dp", dp=1, rn=rn(RUN_D), **FOOT)
shot(V3 + 5.0, V4, "world", [V3 + 5.0, V4], [DP["ta2"] - 0.15, DP["ta2"] + 0.35], play="dp", dp=1, rn=rn(RUN_D), streak=1, **WIDEDP)

# ----------------------------------------------------------------- 4 point 3: don't force it: the runner is already there, the shortstop keeps the ball
RUN_H = [dict(who=1, from_="b1", to="b2", t0=-1.55, lead=12, slide=1)]
shot(V4, V4 + 1.5, "follow2", [V4, V4 + 1.5], [tfh - 0.55, tfh + 0.25], play="hold", rn=rn(RUN_H), streak=1, **HOLECU)
shot(V4 + 1.5, V4 + 3.3, "world", [V4 + 1.5, V4 + 3.3], [tfh - 0.5, tfh + 0.7], play="hold", rn=rn(RUN_H), flook=dict(at="b2", t=[tfh + 0.05, tfh + 1.2]), **TOPSS)
shot(V4 + 3.3, V4 + 5.4, "follow2", [V4 + 3.3, V4 + 5.4], [tfh + 0.2, tfh + 1.1], play="hold", rn=rn(RUN_H), flook=dict(at="b2", t=[tfh + 0.05, tfh + 1.6]), **FACE)
shot(V4 + 5.4, V5, "world", [V4 + 5.4, V5], [tfh + 1.1, tfh + 1.4], play="hold", rn=rn(RUN_H), **TOPSS)

# ----------------------------------------------------------------- 5 point 4: the same ground ball, three situations, from above
Q1, Q2 = V5 + 2.0, V5 + 4.0
def sit(a, b, rn_, arr, **kw):
    shot(a, b, "world", [a, b], [-0.9, -0.9], play="easy", rn=rn_, arr=arr, **kw, **TOPALL)
SS0, B2_, B1_ = (-36, -140), (0, -127.3), (63.6, -63.6)
sit(V5, Q1, [dict(who=1, stay="b1", lead=0)], [dict(a=SS0, b=B2_, v=[V5 + 0.3, Q1], c=0xffd84d)])
sit(Q1, Q2, [dict(who=1, stay="b1", lead=0), dict(who=2, stay="b2", lead=0)], [dict(a=SS0, b=B2_, v=[Q1 + 0.2, Q2], c=0xffd84d), dict(a=B2_, b=B1_, v=[Q1 + 0.7, Q2], c=0x56d1ff)])
sit(Q2, V6, [dict(who=1, stay="b1", lead=0)], [dict(a=SS0, b=B2_, v=[Q2 + 0.2, V6], c=0xffd84d), dict(a=SS0, b=B1_, v=[Q2 + 0.5, V6], c=0x56d1ff)])

# ----------------------------------------------------------------- 6 the ending: three smart decisions, then a clean overhead
M1 = V6 + 1.0
shot(V6, M1, "world", [V6, M1], [LD["tr"] - 0.1, LD["ta"] + 0.3], play="lead", rn=rn(RUN_L), streak=1, **BAGW)
shot(M1, M1 + 1.0, "follow2", [M1, M1 + 1.0], [DP["ta"] - 0.1, DP["tr2"] + 0.3], play="dp", dp=1, rn=rn(RUN_D), **FOOT)
shot(M1 + 1.0, M1 + 1.9, "follow2", [M1 + 1.0, M1 + 1.9], [tfh + 0.2, tfh + 1.0], play="hold", rn=rn(RUN_H), flook=dict(at="b2", t=[tfh + 0.05, tfh + 1.6]), **FACE)
shot(M1 + 1.9, D, "world", [M1 + 1.9, D], [DP["ta2"] + 0.2, DP["ta2"] + 0.8], play="dp", dp=1, rn=[dict(who=1, hide=1)], **TOPALL)

for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

# ----------------------------------------------------------------- overlays
c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in CUTS:
    c.set("#flash", '{"opacity":0.2}', f); c.to("#flash", o(opacity=0, duration=0.1, ease="power2.out"), f + 0.001)
def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def title(tid, t0, t1, lines, top, cls="band"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{(" " + acc) if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style=f"z-index:{26 if cls == 'q' else 22}")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.05 * i)
def chip(cid, t0, t1, html, top, cls="", left=None):
    st = f"top:{top}px" + (f";left:{left}px;transform:none" if left is not None else "")
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="{st}">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def note(nid, t0, t1, text, top):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{esc(text)}</div>', cls="layer", style="z-index:14"); pop(f"#{nid}x", t0, 8)
def hdiv(did, t0, t1, tops):
    for i, tp in enumerate(tops): c.clip(f"{did}{i}", t0, t1, f'<div class="hdiv" style="top:{tp}px"></div>', cls="layer", style="z-index:11")





# the base-state widget: the diamond with the runners, and the outs
def state(sid, t0, t1, bases, outs):
    pos = {"b2": (50, 8), "b1": (88, 46), "b3": (12, 46), "home": (50, 84)}
    sq = "".join(f'<rect x="{x - 9}" y="{y - 9}" width="18" height="18" transform="rotate(45 {x} {y})" fill="{"#FFD84D" if k in bases else "#1b2330"}" stroke="#F4F6F8" stroke-width="2.5"/>' for k, (x, y) in pos.items())
    dots = "".join(f'<circle cx="{34 + 16 * i}" cy="112" r="6" fill="{"#FF4D4D" if i < outs else "none"}" stroke="#F4F6F8" stroke-width="2"/>' for i in range(3))
    html = f'<div class="bs"><svg viewBox="0 0 100 124" width="190" height="236"><polygon points="50,8 88,46 50,84 12,46" fill="none" stroke="rgba(244,246,248,.35)" stroke-width="2"/>{sq}{dots}</svg><b>{outs} OUT{"S" if outs != 1 else ""}</b></div>'
    c.clip(sid, t0, t1, html, cls="layer", style="z-index:15")
# 1 the hook: the question is on screen from the first frame; the situation is on the widget
title("t1", 0.0, V2, [("The easy out can be", ""), ("the wrong play.", "yl")], 250, "mid")
state("s1a", 0.0, 2.3, ["b1"], 0); state("s1b", 2.3, V2, ["b2"], 1)
def point(pid, t0, t1, num, name):
    title(pid, t0, t1, [(f"{num}.", "yl"), (name, "")], 250, "big")
point("p1", V2 + 0.02, V3, "1", "Get the lead runner")
state("s2a", V2, V2 + 2.8, ["b1"], 0); state("s2b", V2 + 2.8, V3, [], 1)
chip("k2a", V2 + 2.8, V3, "OUT AT 1ST: RUNNER ON 2ND", 880, "sm or", 40) if False else None
c.clip("lab2a", V2 + 2.85, V3, '<div class="plb or" style="top:860px;left:50%">OUT AT 1ST: RUNNER ON 2ND</div>', cls="layer", style="z-index:13")
c.clip("lab2b", V2 + 2.85, V3, '<div class="plb" style="top:1820px;left:50%">OUT AT 2ND: RUNNER ON 1ST</div>', cls="layer", style="z-index:13")
c.clip("hd2", V2 + 2.8, V3, '<div class="hdiv" style="top:958px"></div>', cls="layer", style="z-index:11")
point("p2", V3 + 0.02, V4, "2", "Turn two")
state("s3a", V3, V3 + 3.5, ["b1", "b2"], 1); state("s3b", V3 + 3.5, V4, [], 3)
chip("k3a", V3 + 3.0, V3 + 5.0, "SLOW MOTION", 1500, "sm yl")
point("p3", V4 + 0.02, V5, "3", "Don't force it")
state("s4a", V4, V4 + 1.8, ["b1"], 0); state("s4b", V4 + 1.8, V5, ["b1", "b2"], 0)
chip("k4a", V4 + 3.3, V5, "KEEP THE BALL", 1500, "sm gr")
point("p4", V5 + 0.02, V6, "4", "Think before you throw")
state("s5a", V5, Q1, ["b1"], 0); state("s5b", Q1, Q2, ["b1", "b2"], 1); state("s5c", Q2, V6, ["b1"], 2)
chip("k5a", V5 + 0.2, Q1, "LEAD RUNNER?", 1500, "sm yl"); chip("k5b", Q1, Q2, "TURN TWO?", 1500, "sm cy"); chip("k5c", Q2, V6, "EITHER OUT ENDS IT", 1500, "sm or")
note("n5", V5 + 0.2, V6, "Illustration. The right play depends on the situation.", 1620)
# 6 the ending
VBRAND = round(D - 1.55, 3)
title("t6", V6 + 0.1, D, [("Baseball IQ", ""), ("wins plays.", "yl")], 290, "q")

# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"worst", "out", "lead", "runner", "double", "play", "outs", "force", "throw", "ball", "runners", "right", "easy", "keeping", "mistake"}
CAPS = []
for ln in TM["lines"]:
    wd = ln["words"]; chunk = []
    for n, w in enumerate(wd):
        chunk.append(n)
        brk = w["w"].endswith((",", ".")) or len(chunk) >= 4
        if brk or n == len(wd) - 1: CAPS.append((ln["id"], chunk[0], chunk[-1])); chunk = []
for k, (lid, i0, i1) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, D)
    if lid == "e1": end = min(end, VBRAND)
    if start >= end: continue
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"].rstrip(",.").replace("'", "’")
        acc = w.lower().strip("’s").rstrip("’") in KEY or w.lower() in KEY
        sp.append(f'<span class="cw{" acc" if acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" id="{cid}c"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0, y=40), o(opacity=1, y=0, duration=0.35, ease="power3.out"), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)


# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -15)
cue("riser-m", 0.0, -8); cue("glove", 0.7, -3)
for tt in [V2 + 0.02, V3 + 0.02, V4 + 0.02, V5 + 0.02, V6 + 0.1]: cue("impact", tt, -7)
def pv(sh, t):
    v = vat(sh["vs"], sh["ts"], t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
CRACKS = []
for sh in SHOTS:
    pl = sh.get("play")
    if not pl or "panes" in sh: continue
    pts = {"easy": [(E["tf"], "glove", -3), (E["tr"], "whoosh", -10), (E["ta"], "glove", -4)], "lead": [(LD["tf"], "glove", -3), (LD["tr"], "whoosh", -10), (LD["ta"], "glove", -4)],
           "hold": [(HO["tf"], "glove", -3)], "dp": [(DP["tf"], "glove", -3), (DP["ta"], "glove", -4), (DP["tr2"], "whoosh", -10), (DP["ta2"], "glove", -5)]}[pl]
    for tt, nme, db in pts:
        v = pv(sh, tt)
        if v is not None: cue(nme, v, db)
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)

LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}
def crack(rng, slow=False):
    """Maple bat on a ball: a hard broadband click and a short wooden ring (lower and longer in slow motion)."""
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
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=311)
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
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:560px; background:linear-gradient(180deg, rgba(3,6,12,.6), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:620px; background:linear-gradient(0deg, rgba(3,6,12,.7) 0%, rgba(3,6,12,.3) 55%, rgba(3,6,12,0) 100%); }}
.flash {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.spd {{ position:absolute; right:40px; top:1856px; display:inline-flex; align-items:center; gap:10px; padding:6px 14px; border-radius:8px; background:rgba(6,10,18,.72); {MONO} font-size:20px; letter-spacing:.14em; color:{Y}; opacity:0; }}
.spd::before {{ content:""; width:10px; height:10px; border-radius:50%; background:currentColor; }}
.hseam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.85); box-shadow:0 0 18px rgba(0,0,0,.6); }}

.cap {{ position:absolute; left:52px; right:52px; top:118px; text-align:center; }}
.cap .cl {{ display:block; {BC} font-size:74px; line-height:.98; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.75); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{Y}; }}

.ttl {{ position:absolute; left:40px; right:40px; display:grid; justify-items:center; text-align:center; {BC} font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.6); }}
.ttl .tl {{ display:block; }} .ttl .tw {{ display:inline-block; }}
.ttl .acc {{ color:{HOT}; }} .ttl .yl {{ color:{Y}; }} .ttl .cy {{ color:{CYAN}; }} .ttl .or {{ color:{HOT}; }}
.ttl.big {{ font-size:150px; }} .ttl.q {{ font-size:96px; z-index:30; }} .ttl.mid {{ font-size:112px; left:0; right:0; padding:18px 30px 24px; background:rgba(5,8,13,.86); }}
.ttl.band {{ left:0; right:0; padding:18px 30px 22px; background:rgba(5,8,13,.86); font-size:86px; line-height:.98; }}

.plb {{ position:absolute; left:50%; transform:translateX(-50%); padding:4px 18px; border-radius:12px; background:rgba(6,10,18,.88); border:3px solid {CYAN}; {BC} font-size:44px; line-height:1.0; color:{CYAN}; white-space:nowrap; }}
.plb.or {{ border-color:{HOT}; color:{HOT}; }} .plb b {{ color:#fff; font-weight:700; }}
.chip {{ position:absolute; left:50%; transform:translateX(-50%); padding:12px 26px; border-radius:14px; background:rgba(6,10,18,.88); {BC} font-size:60px; white-space:nowrap; }}
.chip.big {{ font-size:96px; padding:10px 30px; }} .chip.or {{ color:{HOT}; border:3px solid {HOT}; }}
.chip .cyt {{ color:{CYAN}; }} .chip .yt {{ color:{Y}; }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:24px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; {BC} font-size:46px; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.pin.sm span {{ font-size:38px; padding:6px 14px; }}
.pin.cy span {{ background:{CYAN}; }} .pin.yl span {{ background:{Y}; }} .pin.wh span {{ background:{WHITE}; }}

.brand {{ position:absolute; inset:0; display:grid; place-content:center; justify-items:center; gap:28px; padding-top:640px; background:linear-gradient(180deg, rgba(3,6,11,0) 42%, rgba(3,6,11,.8) 66%, rgba(3,6,11,.95)); }}
.bname {{ display:grid; justify-items:center; {BC} line-height:.9; }} .bname span {{ font-size:110px; color:#fff; }} .bname em {{ font-style:normal; font-size:140px; color:{HOT}; letter-spacing:.02em; }}

.ttl.am {{ color:{AMBER}; }} .ttl .am {{ color:{AMBER}; }}
.pin.am span {{ background:{AMBER}; }} .pin.gr span {{ background:{GREEN}; }}
.chip.sm {{ font-size:46px; padding:8px 20px; }} .chip .or {{ color:{HOT}; }}
.note {{ position:absolute; left:50%; transform:translateX(-50%); width:960px; text-align:center; {MONO} font-size:22px; letter-spacing:.06em; line-height:1.35; color:{MUTED}; text-transform:none; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.legend {{ position:absolute; left:0; right:0; display:flex; justify-content:center; gap:22px; {MONO} font-size:22px; letter-spacing:.08em; color:#e8edf4; text-shadow:0 2px 8px rgba(0,0,0,.9); }}
.legend .lg {{ display:inline-flex; align-items:center; gap:8px; }} .legend i {{ width:16px; height:16px; border-radius:50%; display:inline-block; box-shadow:0 0 10px currentColor; }}
.sup {{ position:absolute; left:110px; right:110px; top:1440px; }}
.sup .sl {{ display:flex; justify-content:space-between; align-items:baseline; {BC} font-size:40px; color:{AMBER}; margin-bottom:10px; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.sup .sl b {{ {MONO} font-size:22px; letter-spacing:.14em; color:{MUTED}; }}
.sup .st {{ position:relative; height:18px; border-radius:9px; background:linear-gradient(90deg, rgba(255,181,71,.85), rgba(255,181,71,.15) 50%, rgba(255,181,71,.85)); box-shadow:0 0 0 2px rgba(5,8,13,.8); }}
.sup .sk {{ position:absolute; top:50%; width:44px; height:44px; margin:-22px 0 0 -22px; border-radius:50%; background:#fff; border:6px solid {AMBER}; box-shadow:0 0 22px {AMBER}; left:50%; }}
.trw {{ position:absolute; left:80px; width:920px; top:1580px; padding:14px 20px 10px; border-radius:16px; background:rgba(5,8,13,.78); }}
.trw canvas {{ display:block; width:880px; height:250px; }}
.trl {{ display:flex; gap:28px; align-items:baseline; {BC} font-size:40px; }} .trl .or {{ color:{HOT}; }} .trl .cyt {{ color:{CYAN}; }}
.trl em {{ margin-left:auto; font-style:normal; {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; }}
.trx {{ text-align:right; {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; margin-top:-4px; }}
.ttl.big {{ font-size:150px; line-height:.88; }}
.chain {{ position:absolute; left:0; right:0; top:1450px; display:flex; justify-content:center; align-items:baseline; gap:10px; flex-wrap:nowrap; padding:0 16px; white-space:nowrap; {BC} font-size:58px; color:#fff; text-shadow:0 4px 24px rgba(0,0,0,.9); }}
.chain i {{ font-style:normal; color:{MUTED}; font-size:40px; }}
.hdiv {{ position:absolute; left:0; right:0; height:3px; background:rgba(255,255,255,.8); box-shadow:0 0 14px rgba(0,0,0,.7); }}
.chip.rd {{ color:{RED}; border:3px solid {RED}; }} .chip.gr {{ color:{GREEN}; border:3px solid {GREEN}; }} .chip.yl {{ color:{Y}; border:3px solid {Y}; }}
.vdiv {{ position:absolute; left:539px; width:3px; top:0; bottom:0; background:rgba(255,255,255,.8); box-shadow:0 0 14px rgba(0,0,0,.7); }}
.chip.or {{ color:{HOT}; border:3px solid {HOT}; }} .chip.cy {{ color:{CYAN}; border:3px solid {CYAN}; }}

.ttl .gr {{ color:{GREEN}; }}
.bs {{ position:absolute; left:34px; top:1480px; display:grid; justify-items:center; gap:0; }}
.bs b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:44px; color:#fff; letter-spacing:.04em; margin-top:-6px; text-shadow:0 3px 12px rgba(0,0,0,.9); }}
.bs svg {{ filter:drop-shadow(0 4px 14px rgba(0,0,0,.7)); }}

.dark {{ position:absolute; inset:0; background:radial-gradient(ellipse at 50% 55%, rgba(4,7,12,.55), rgba(4,7,12,.96) 70%); opacity:0; }}
.gauge {{ position:absolute; left:50%; transform:translateX(-50%); width:560px; display:grid; justify-items:center; }}
.gauge svg {{ overflow:visible; filter:drop-shadow(0 8px 30px rgba(0,0,0,.7)); }}
.gauge .garc {{ fill:none; stroke:rgba(10,14,22,.82); stroke-width:46; stroke-linecap:round; }}
.gauge .ghot {{ fill:none; stroke:url(#none); stroke:{HOT}; stroke-width:8; stroke-dasharray:44 240; stroke-dashoffset:-196; opacity:.95; }}
.gauge .gtk line {{ stroke:#e9eef5; stroke-width:5; stroke-linecap:round; }}
.gauge .gnum text {{ fill:{MUTED}; font-family:"Plex Mono", monospace; font-size:26px; text-anchor:middle; dominant-baseline:middle; }}
.gauge .gnd {{ fill:{Y}; filter:drop-shadow(0 0 10px {Y}); }} .gauge .ghub {{ fill:#05080d; stroke:{Y}; stroke-width:6; }}
.gauge .gread {{ margin-top:-96px; display:flex; align-items:baseline; gap:12px; {BC} }}
.gauge .gread b {{ font-size:150px; line-height:1; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.85); font-variant-numeric:tabular-nums; }}
.gauge .gread span {{ font-size:54px; color:{Y}; }}
"""])

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'

SCENES = [(0.0, V2, "The hook", "Runner on first, a grounder to the shortstop, the easy throw to first, frozen; the widget shows runners and outs", "THE EASY OUT CAN BE THE WRONG PLAY."),
          (V2, V3, "1. Get the lead runner", "The same ground ball: he looks to second and throws; the runner is out; the two outcomes side by side from above", "1. GET THE LEAD RUNNER"),
          (V3, V4, "2. Turn two", "Runners on first and second, one out: the feed, the pivot, the throw; a slow-motion replay of the pivot", "2. TURN TWO"),
          (V4, V5, "3. Don't force it", "A deep ground ball; the runner is already at second; the shortstop checks him and keeps the ball", "3. DON'T FORCE IT"),
          (V5, V6, "4. Think before you throw", "The same ground ball from above in three situations, arrows showing the options", "4. THINK BEFORE YOU THROW"),
          (V6, D, "The ending", "Three smart decisions in quick cuts; a clean overhead; the mark", "BASEBALL IQ WINS PLAYS.")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Why the Best Play Is Not Always the Easy Out", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Voiceover cues", "", f"The video is {D:.1f} s. To record your own read over `assets/mix-novo.wav`, start each line at its time (seconds).", "",
             "| Start | End | Scene | Line |", "|---|---|---|---|"]
    for a, b, name, desc, _ in SCENES:
        for ln in TM["lines"]:
            if a - 0.01 <= ln["t0"] + 0.08 < b: lines.append(f"| {ln['t0']:.2f} | {ln['t1']:.2f} | {name} | {ln['text']} |")
    lines += ["", "## Scenes", "", "| From | To | Scene | Shots | On screen |", "|---|---|---|---|---|"] + [f"| {a:.2f} | {b:.2f} | {n} | {d} | {t} |" for a, b, n, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
