"""'What if an MLB hitter stopped swinging for 3 months?' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the pitches and batted balls -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

A hypothetical. One hitter throughout (white uniform, navy helmet and batting gloves). His swing is the same swing every
time: what changes is when it starts against the ball. A swing is aimed at a pitch's contact point with a timing offset,
so "late" means the barrel gets to the hitting zone after the ball, "early" means before it, and "fooled" means he swung
for a fastball and got a breaking ball. Nothing here puts a number on how much a hitter would lose.
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
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
SHOTS = []
def shot(a, b, cam, vs, ts, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], **kw))
def vat(vs, ts, t):
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
PI = P["pitches"]; HT = P["hits"]
R = 2.0                                                              # every pitch: released at play time 2.0
TCP = lambda pk: PI[pk]["t_contact"]
def live(a, b, cam, t0, rate=1.0, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * rate], **kw)
def P_(pk): return dict(pk=pk, rel=R)
def SW(aim, **kw): return dict(aim=aim, rel=R, **kw)
CAGE = dict(cage=1)
# cameras (the hitter is a right-hander on the third-base side of the plate, facing +x; the pitcher is toward -z)
OTS = dict(c0=[-3.2, 7.8, 12.0], c1=[-3.0, 7.6, 11.2], l=[-1.0, 1.0, -15.0], f0=38)                     # over his shoulder, at the pitcher
OTSC = dict(c0=[-1.2, 7.2, 8.4], c1=[-1.1, 7.0, 7.8], l=[-0.9, 1.4, -15.0], f0=40)                       # the same, inside the cage
FACE = dict(c0=[6.8, 4.1, -0.6], c1=[6.4, 4.0, -0.5], l=[-2.4, 3.5, -0.4], f0=58)                        # square to him, from across the plate (inside the cage)
FACEG = dict(c0=[11.5, 4.2, -0.3], c1=[10.9, 4.15, -0.3], l=[-2.4, 3.6, -0.4], f0=46)                   # the same in the ballpark
BEHIND = dict(c0=[-1.9, 5.3, 8.2], c1=[-1.8, 5.2, 7.6], l=[-1.1, 3.4, -30.0], f0=42)                     # behind the plate, inside the back net
HANDSC = dict(o="broot", lo="broot", c0=[3.4, 5.4, 5.4], c1=[3.0, 5.3, 4.9], l=[-0.6, 4.4, 0.6], f0=40, close=1)

# ----------------------------------------------------------------- 0 the hook: a 96 mph fastball, taken; then 90 days
V1, V2, V3, V4 = S["w1"] - 0.1, S["m1"] - 0.1, S["s1"] - 0.1, S["g1"] - 0.1
A1 = 0.95; A2 = 2.15
live(0.0, A1, "world", R - 0.32, p=P_("g96"), sw=SW("g96", take=1), streak=1, **OTS)
shot(A1, A2, "world", [A1, A2], [R + 0.29, R + 0.43], p=P_("g96"), sw=SW("g96", take=1), streak=1, close=1, c0=[8.4, 3.6, 2.0], c1=[8.0, 3.5, 1.8], l=[-1.6, 3.2, -0.6], f0=44)
shot(A2, V1, "world", [A2, V1], [R + 1.4, R + 1.4], p=P_("g96"), sw=SW("g96", take=1), c0=[7.0, 15.0, 33.0], c1=[4.5, 10.5, 21.0], l=[-2.0, 3.6, -6.0], f0=44, f1=38)

# ----------------------------------------------------------------- 1 one week: he racks the bat and walks out; seven days; back in the cage, the same swing
B1 = W("w2", "years") - 0.2; B2 = B1 + 0.75
WALK = dict(t0=R, keys=[[0.0, -2.6, -0.1], [0.9, -6.0, 1.9], [1.45, -9.3, 3.25], [1.95, -9.4, 3.3], [2.6, -9.6, 5.3], [3.2, -13.0, 7.2]], rack=1.55)
shot(V1, B1, "world", [V1, B1], [R + 0.2, R + 0.2 + (B1 - V1) * 1.35], walk=WALK, **CAGE, c0=[0.8, 5.4, -7.5], c1=[0.2, 5.6, -6.5], l=[-8.0, 3.4, 3.5], f0=48)
shot(B1, B2, "world", [B1, B2], [R, R], hide=1, **CAGE, c0=[1.0, 6.5, -9.0], c1=[0.6, 6.4, -7.5], l=[-2.0, 3.0, 2.0], f0=48)
B3 = W("w3", "his") - 0.1
shot(B2, B3, "obj", [B2, B3], [R - 1.6, R - 1.6 + (B3 - B2)], p=None, sw=SW("bfb"), **CAGE, **HANDSC)
B4 = W("w3", "memory") + 0.25
shot(B3, B4, "world", [B3, B4], [R - 0.62, R - 0.62 + (B4 - B3)], p=P_("bfb"), sw=SW("bfb"), coach=1, hit="k1", **CAGE, **FACE)
shot(B4, V2, "world", [B4, B4 + 0.9, V2], [R + 0.1, R + TCP("bfb") + 0.02, R + 0.9], p=P_("bfb"), sw=SW("bfb"), coach=1, hit="k2", ghost=0.012, **CAGE, **OTSC)

# ----------------------------------------------------------------- 2 one month: knowing how to swing vs. timing a moving ball
C1 = W("m2", "timing") - 0.35
shot(V2, C1, "world", [V2, V2 + 0.6, C1], [R - 1.2, R - 1.2 + 0.6, R + 0.9], sw=SW("bfb", reset=1), coach=1, **CAGE, c0=[-9.0, 5.0, -5.5], c1=[-8.6, 4.8, -4.6], l=[-2.4, 3.8, 0.0], f0=40)
C2 = W("m2", "recognizing") - 0.15
live(C1, C2, "world", R - 0.55, p=P_("bfb"), sw=SW("bfb@0.012"), coach=1, hit="kf", **CAGE, **BEHIND)
C3 = W("m2", "and") - 0.05
shot(C2, C3, "world", [C2, C2 + 0.45, C3], [R - 0.12, R + 0.45, R + 0.75], p=P_("bcb"), sw=SW("bfb"), coach=1, ghost=0.012, **CAGE, **FACE)
C4 = W("m2", "contact", end=True) + 0.1
live(C3, C4, "world", R - 0.75, p=P_("bch"), sw=SW("bch@-0.035"), coach=1, hit="kp", **CAGE, **OTSC)
shot(C4, V3, "world", [C4, V3], [R - 1.0, R - 1.0 + (V3 - C4)], sw=SW("bfb", reset=1), **CAGE, c0=[3.5, 7.0, -8.0], c1=[2.8, 6.4, -6.8], l=[-2.4, 3.6, 0.0], f0=44)

# ----------------------------------------------------------------- 3 sixty days: live pitching in the cage: a fastball he watches, a slider he chases
D0 = V3 + 0.75
shot(V3, D0, "world", [V3, D0], [R, R], hide=1, **CAGE, c0=[-0.4, 6.0, 7.0], c1=[-0.6, 5.6, 4.0], l=[-1.0, 3.6, -40.0], f0=40)
D1 = W("s2", "even") - 0.1
live(D0, D1, "world", R - 1.05, p=P_("cfb"), sw=SW("cfb", take=1), live=1, streak=1, **CAGE, **OTSC)
D2 = W("s2", "struggle") - 0.05
shot(D1, D2, "world", [D1, D2], [R + 0.12, R + 0.36], p=P_("csl"), sw=SW("cfb", off=-0.03), live=1, **CAGE, c0=[1.0, 2.6, -6.5], c1=[0.8, 2.5, -6.0], l=[-1.4, 4.4, -40.0], f0=24)
D3 = W("s2", "pitches", end=True) + 0.15
shot(D2, D3, "world", [D2, D2 + 0.25, D3], [R + 0.33, R + 0.39, R + 0.62], p=P_("csl"), sw=SW("cfb", off=-0.03), live=1, ghost=0.012, **CAGE, **FACE)
D4 = S["g1"] - 1.0
shot(D3, D4, "world", [D3, D4], [R - 1.2, R - 1.2 + (D4 - D3) * 0.9], sw=SW("cfb", reset=1), live=1, **CAGE, c0=[-6.5, 4.6, 6.0], c1=[-5.8, 4.4, 5.2], l=[-2.3, 3.8, -1.0], f0=40)
shot(D4, V4, "world", [D4, V4], [R, R], hide=1, **CAGE, c0=[-0.4, 6.0, 7.0], c1=[-0.6, 5.8, 6.0], l=[-1.0, 3.6, -40.0], f0=40)

# ----------------------------------------------------------------- 4 ninety days: a full ballpark, the first at-bat back, 98 mph, late
E1 = W("g1", "hit") + 0.3
WALK2 = dict(t0=R, keys=[[0.0, -9.5, 6.5], [1.6, -2.8, 0.6], [2.0, -2.6, -0.1]])
shot(V4, E1, "world", [V4, E1], [R + 0.2, R + 0.2 + (E1 - V4) * 1.15], walk=WALK2, c0=[9.0, 22.0, 42.0], c1=[5.0, 13.0, 26.0], l=[-3.0, 3.0, -4.0], f0=50, f1=40)
E2 = E1 + 1.1
live(E1, E2, "world", R - 0.82, p=P_("g98"), sw=SW("g98", off=0.022), streak=1, board=[0, 0, 0, "98|FASTBALL"], **OTS)
E3 = W("g2", "against") + 0.1
shot(E2, E3, "world", [E2, E2 + 0.35, E3], [R + 0.28, R + 0.34, R + 0.42], p=P_("g98"), sw=SW("g98", off=0.022), ghost=0.01, close=1, c0=[3.6, 3.5, -6.0], c1=[3.3, 3.4, -5.6], l=[-1.0, 3.0, -0.6], f0=42)
E4 = S["e1"] - 0.05
shot(E3, E4, "world", [E3, E4], [R, R + (E4 - E3)], sw=dict(aim="g98", rel=R + 30.0), dugout=R + 0.45, close=1, c0=[5.4, 6.0, -4.6], c1=[4.8, 5.9, -4.0], l=[-2.6, 4.3, -0.2], f0=36)

# ----------------------------------------------------------------- 5 back to work: the timing comes back; then on time, in a game: gone
F1 = W("e1", "even") - 0.1
live(E4, F1, "world", R - 0.75, p=P_("bfb"), sw=SW("bfb@0.012"), coach=1, hit="kf", **CAGE, **FACE)
F2 = W("e1", "can") - 0.05
live(F1, F2, "world", R - 0.4, p=P_("bfb"), sw=SW("bfb"), coach=1, hit="k4", **CAGE, **OTSC)
F3 = W("e1", "home") + 0.1
live(F2, F3, "world", R - 0.55, p=P_("ghr"), sw=SW("ghr", hold=0.62), hit="hr", streak=1, **OTS)
TF = R + TCP("ghr")
shot(F3, D, "follow2", [F3, D], [TF + 0.08, TF + 0.08 + (D - F3) * 1.0], p=P_("ghr"), sw=SW("ghr", hold=0.62), hit="hr", bglow=1, tf=TF + 0.1, lag=0.4, fw=0.9,
     c0=[-3.0, 9.0, 16.0], c1=[-6.0, 22.0, 4.0], l=[-6.0, 12.0, -60.0], f0=44, f1=50)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]
for sh in SHOTS:
    if sh.get("p") is None: sh.pop("p", None)

# ----------------------------------------------------------------- overlays
c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in CUTS:
    c.set("#flash", '{"opacity":0.28}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)
def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls="", pane=0):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, pane])
def title(tid, t0, t1, lines, top, cls="band"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{(" " + acc) if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style=f"z-index:{28 if cls == 'big' else 22}")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.05 * i)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)

# --- the calendar: a tear-off day calendar; its pages flip from d0 to d1, then the label lands under it
def calendar(cid, t0, t1, d0, d1, label=None, dim=True):
    steps = sorted(set([d0] + [round(d0 + (d1 - d0) * (i / 24) ** 1.6) for i in range(1, 25)] + [d1]))
    flip0, flip1 = t0 + 0.12, t1 - (0.45 if label else 0.2)
    nums = "".join(f'<b class="cn" id="{cid}n{d}">{d}</b>' for d in steps)
    c.clip(cid, t0, t1, f'''{'<div class="caldim"></div>' if dim else ''}<div class="cal" id="{cid}x"><div class="calring"><i></i><i></i></div><div class="calhd">DAY</div>
      <div class="calnum">{nums}</div><div class="calleaf" id="{cid}l"></div></div>''' + (f'<div class="callab" id="{cid}t">{label}</div>' if label else ""), cls="layer", style="z-index:26")
    c.ft(f"#{cid}x", o(opacity=0, scale=0.82, y=40), o(opacity=1, scale=1, y=0, duration=0.18, ease="power3.out"), t0)
    for i, d in enumerate(steps):
        ti = flip0 + (flip1 - flip0) * (i / max(1, len(steps) - 1)) ** 0.85
        c.set(f"#{cid}n{d}", '{"opacity":1}', ti)
        if i + 1 < len(steps):
            tn = flip0 + (flip1 - flip0) * ((i + 1) / max(1, len(steps) - 1)) ** 0.85
            c.set(f"#{cid}n{d}", '{"opacity":0}', tn - 0.001)
            c.ft(f"#{cid}l", o(rotationX=0, opacity=0.55), o(rotationX=-92, opacity=0.0, duration=max(0.03, (tn - ti) * 0.8), ease="power1.in"), ti)
    if label: c.ft(f"#{cid}t", o(opacity=0, scale=1.6), o(opacity=1, scale=1, duration=0.2, ease="back.out(2)"), flip1 + 0.02)
    return flip1
def badge(bid, t0, t1, text):
    c.clip(bid, t0, t1, f'<div class="dayb" id="{bid}x"><i></i>{text}</div>', cls="layer", style="z-index:18"); pop(f"#{bid}x", t0, 8)
# --- the timing meter: early | on time | late; the marker lands where that swing met (or missed) the ball
def meter(mid, t0, t1, tc, val, word):
    pct = 50 + 40 * val
    c.clip(mid, t0, t1, f'''<div class="tm" id="{mid}x"><div class="tmt"><span class="e">Early</span><span class="o">On time</span><span class="l">Late</span></div>
      <div class="tmb"><div class="tmz"></div><div class="tmk" id="{mid}k" style="left:50%"></div></div><div class="tmw" id="{mid}w">{word}</div></div>''', cls="layer", style="z-index:17")
    pop(f"#{mid}x", t0, 8)
    c.ft(f"#{mid}k", o(left="50%", opacity=0.0), o(left=f"{pct:.0f}%", opacity=1, duration=0.22, ease="power3.out"), tc - 0.02)
    c.ft(f"#{mid}w", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.18), tc + 0.05)
def pv(sh, t):
    v = vat(sh["vs"], sh["ts"], t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
def shot_at(a): return next(s_ for s_ in SHOTS if abs(s_["a"] - a) < 1e-3)

# 0 the hook
title("t0", 1.7, V1 - 0.05, [("90 days", "yl"), ("without swinging?", "")], 290, "big")
calendar("cal0", A2, V1, 1, 90)
# 1 one week
calendar("cal1", B1, B2 + 0.25, 0, 7, "1 week", dim=False)
badge("b1", B2 + 0.25, V2, "Day 7")
# 2 one month
f2 = calendar("cal2", V2, V2 + 1.0, 7, 30, "1 month")
badge("b2", V2 + 1.0, V3, "Day 30")
title("t2", W("m2", "timing") - 0.05, V3 - 0.05, [("Timing", ""), ("matters", "yl")], 1660, "band")
# 3 sixty days
calendar("cal3", V3, D0 + 0.2, 30, 60, "60 days", dim=False)
badge("b3", D0 + 0.2, D4, "Day 60")
chip("c3", D1 + 0.05, D2 - 0.02, '<span class="yt">85 mph</span> slider', 1460)
# 4 ninety days
calendar("cal4", D4, V4 + 0.25, 60, 90, "90 days", dim=False)
badge("b4", V4 + 0.25, E4, "Day 90 · first game back")
chip("c4", E1 + 0.55, E3 - 0.02, '<span class="yt">98 mph</span>', 1460, "big")
pinl("p4", E2 + 0.4, E3 - 0.02, "Just behind it", "ball", "yl sm")
# 5 back to work
badge("b5", E4 + 0.05, F3, "Back in the cage")
title("t5", F3 + 1.2, D, [("Timing is", ""), ("everything", "yl")], 700, "big")
# the timing meter on every swing at a ball
for a, b, tc_k, val, word in [(B3, B4, None, 0.0, "On time"), (B4, V2, None, 0.0, "On time"), (C1, C2, None, 0.45, "A little late"), (C2, C3, "bcb", -0.8, "Early: fooled by the break"),
                                (C3, C4, None, -0.6, "Out in front"), (D2, D3, "csl", -0.7, "Early: fooled by the break"), (E2, E3, None, 0.75, "Late"), (E4, F1, None, 0.35, "Closer"), (F1, F2, None, 0.0, "On time"), (F2, F3, None, 0.0, "On time")]:
    sh = shot_at(a); sw = sh.get("sw", {})
    aim = sw.get("aim", "bfb"); pk, _, off = aim.partition("@")
    tc = pv(sh, R + PI[pk]["t_contact"] + float(off or 0) + sw.get("off", 0.0))
    if tc is None: tc = a + 0.4
    meter(f"m{int(a * 100)}", max(a, tc - 0.6), b - 0.02, tc, val, word)

# ----------------------------------------------------------------- captions: the voiceover, word by word
A_ = "acc"
CAPS = [("h1", 0, 3, {2: A_}), ("h1", 4, 8, {5: A_, 8: A_}), ("h1", 9, 14, {12: A_, 14: A_}),
        ("w1", 0, 4, {3: A_, 4: A_}),
        ("w2", 0, 5, {2: A_, 5: A_}),
        ("w3", 0, 2, {2: A_}), ("w3", 3, 8, {4: A_, 5: A_}),
        ("m1", 0, 3, {2: A_}), ("m1", 4, 8, {5: A_}),
        ("m2", 0, 4, {2: A_}), ("m2", 5, 7, {5: A_, 7: A_}), ("m2", 8, 12, {9: A_, 12: A_}), ("m2", 13, 15, {15: A_}),
        ("s1", 0, 2, {2: A_}), ("s1", 3, 6, {4: A_, 6: A_}), ("s1", 7, 10, {9: A_, 10: A_}),
        ("s2", 0, 4, {2: A_}), ("s2", 5, 7, {5: A_}), ("s2", 8, 10, {10: A_}), ("s2", 11, 13, {12: A_}), ("s2", 14, 17, {17: A_}),
        ("g1", 0, 6, {3: A_}),
        ("g2", 0, 4, {4: A_}), ("g2", 5, 8, {7: A_, 8: A_}), ("g2", 9, 12, {11: A_, 12: A_}), ("g2", 13, 17, {16: A_}),
        ("e1", 0, 4, {3: A_}), ("e1", 5, 10, {7: A_, 10: A_}), ("e1", 11, 14, {14: A_}), ("e1", 15, 18, {17: A_, 18: A_}), ("e1", 19, 21, {21: A_})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]; i1 = min(i1, len(wd) - 1)
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, D)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"]; w = w.rstrip(",:") if n == i1 and i1 > i0 else w
        w = w.replace("'", "’")
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" id="{cid}c"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:27")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

VBRAND = round(LN("e1")["t1"] + 0.6, 3)
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="96" height="96"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.4, ease="power3.out"), VBRAND)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -14)
for cal in [(A2, V1), (B1, B2 + 0.25), (V2, V2 + 1.0), (V3, D0 + 0.2), (D4, V4 + 0.25)]:
    a, b = cal
    for i in range(10): cue("tick", a + 0.12 + (b - a - 0.5) * i / 9, -12 + i * 0.4)
    cue("impact", b - 0.42, -8)
cue("impact", 1.7, -6); cue("impact", W("m2", "timing") - 0.05, -8); cue("impact", F3 + 1.2, -6)
CRACKS = []
GAMEPOP = []
for sh in SHOTS:
    p_ = sh.get("p")
    if not p_: continue
    v = pv(sh, p_["rel"]); cue("whoosh", v, -10)
    sw = sh.get("sw", {})
    if sw and not sw.get("take"):
        aim = sw["aim"]; pk, _, off = aim.partition("@")
        v = pv(sh, R + PI[pk]["t_contact"] + float(off or 0) + sw.get("off", 0.0) - 0.08); cue("whoosh", v, -9)
    h_ = sh.get("hit")
    if h_:
        v = pv(sh, R + PI[HT[h_]["pitch"]]["t_contact"] + HT[h_].get("off", 0.0))
        if v is not None: CRACKS.append((v, (vat(sh["vs"], sh["ts"], R + 1.0) or v + 1) - v > 1.5))
    elif not sh.get("cage"):
        v = pv(sh, R + PI[p_["pk"]]["flight"]); cue("glove", v, 0)
cue("riser-m", F3 - 0.8, -12); cue("impact", VBRAND, -9)

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
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=90)
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
.ttl.big {{ font-size:150px; }} .ttl.mid {{ font-size:112px; left:0; right:0; padding:18px 30px 24px; background:rgba(5,8,13,.86); }}
.ttl.band {{ left:0; right:0; padding:18px 30px 22px; background:rgba(5,8,13,.86); font-size:86px; line-height:.98; }}

.plb {{ position:absolute; left:50%; transform:translateX(-50%); padding:4px 18px; border-radius:12px; background:rgba(6,10,18,.88); border:3px solid {CYAN}; {BC} font-size:44px; line-height:1.0; color:{CYAN}; white-space:nowrap; }}
.plb.or {{ border-color:{HOT}; color:{HOT}; }} .plb b {{ color:#fff; font-weight:700; }}
.chip {{ position:absolute; left:50%; transform:translateX(-50%); padding:12px 26px; border-radius:14px; background:rgba(6,10,18,.88); {BC} font-size:60px; white-space:nowrap; }}
.chip.big {{ font-size:78px; padding:8px 30px; color:{Y}; }} .chip.yl {{ color:{Y}; }} .chip.cy {{ color:{CYAN}; }}
.chip.step {{ left:60px; transform:none; display:flex; align-items:center; gap:18px; font-size:64px; padding:8px 26px 8px 10px; }}
.chip.step i {{ display:grid; place-items:center; width:66px; height:66px; border-radius:10px; background:{Y}; color:#05080d; font-style:normal; }}
.chip .cyt {{ color:{CYAN}; }} .chip .yt {{ color:{Y}; }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:24px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; {BC} font-size:46px; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.pin.sm span {{ font-size:38px; padding:6px 14px; }}
.pin.cy span {{ background:{CYAN}; }} .pin.yl span {{ background:{Y}; }} .pin.wh span {{ background:{WHITE}; }}

.brand {{ position:absolute; left:0; right:0; top:1640px; display:flex; justify-content:center; align-items:center; gap:22px; }}
.bname {{ display:grid; justify-items:center; {BC} line-height:.9; }} .bname span {{ font-size:54px; color:#fff; }} .bname em {{ font-style:normal; font-size:66px; color:{HOT}; letter-spacing:.02em; }}
.caldim {{ position:absolute; inset:0; background:radial-gradient(ellipse at 50% 50%, rgba(5,8,13,.55), rgba(5,8,13,.85)); }}
.cal {{ position:absolute; left:50%; top:760px; width:400px; height:430px; margin-left:-200px; border-radius:22px; background:#f4f1ea; box-shadow:0 30px 80px rgba(0,0,0,.65), 0 0 0 6px rgba(255,255,255,.08); perspective:900px; overflow:visible; }}
.calhd {{ height:104px; border-radius:22px 22px 0 0; background:{RED}; display:grid; place-items:center; {BC} font-size:62px; letter-spacing:.2em; color:#fff; }}
.calring {{ position:absolute; left:0; right:0; top:-18px; display:flex; justify-content:space-around; padding:0 80px; z-index:3; }}
.calring i {{ width:22px; height:46px; border-radius:11px; background:linear-gradient(#cfd4da, #7d848c); box-shadow:0 2px 6px rgba(0,0,0,.4); }}
.calnum {{ position:relative; height:326px; }}
.cn {{ position:absolute; inset:0; display:grid; place-items:center; {BC} font-size:230px; line-height:1; color:#11151b; opacity:0; }}
.calleaf {{ position:absolute; left:0; right:0; top:104px; height:326px; border-radius:0 0 22px 22px; background:linear-gradient(#ffffff, #e2ddd2); transform-origin:50% 0; opacity:0; box-shadow:0 10px 30px rgba(0,0,0,.25); }}
.callab {{ position:absolute; left:0; right:0; top:1225px; text-align:center; {BC} font-size:118px; line-height:1; color:{Y}; text-shadow:0 8px 30px rgba(0,0,0,.85); }}
.dayb {{ position:absolute; left:44px; top:270px; display:inline-flex; align-items:center; gap:12px; padding:8px 18px 8px 12px; border-radius:12px; background:rgba(6,10,18,.86); border:2px solid rgba(255,255,255,.14); {BC} font-size:44px; color:#fff; }}
.dayb i {{ width:30px; height:30px; border-radius:7px; background:{RED}; box-shadow:inset 0 9px 0 rgba(255,255,255,.35); }}
.tm {{ position:absolute; left:110px; right:110px; top:1500px; display:grid; gap:8px; padding:14px 22px 16px; border-radius:16px; background:rgba(6,10,18,.84); }}
.tmt {{ display:flex; justify-content:space-between; {MONO} font-size:21px; letter-spacing:.12em; color:{MUTED}; }} .tmt .o {{ color:{GREEN}; }}
.tmb {{ position:relative; height:18px; border-radius:9px; background:linear-gradient(90deg, {CYAN}, #26303f 38%, #26303f 62%, {HOT}); }}
.tmz {{ position:absolute; left:44%; width:12%; top:-4px; bottom:-4px; border-radius:6px; background:{GREEN}; opacity:.8; }}
.tmk {{ position:absolute; top:50%; width:40px; height:40px; margin:-20px 0 0 -20px; border-radius:50%; background:#fff; border:5px solid #05080d; box-shadow:0 0 0 3px #fff; }}
.tmw {{ justify-self:center; {BC} font-size:44px; color:#fff; }}
.chip .yt {{ color:{Y}; }}
"""])

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [(0.0, V1, "The hook", "Night game: he watches a 96 mph fastball into the mitt (over his shoulder, then low beside the plate in slow motion); the ballpark from high behind the plate as a day calendar flips to 90", "90 DAYS WITHOUT SWINGING?"),
          (V1, V2, "One week", "In the batting cage he racks his bat and walks out; the empty cage, the calendar flips to 7; back in: his hands on the bat, then two clean swings off batting practice into the net", "1 WEEK / timing meter: on time"),
          (V2, V3, "One month", "The calendar flips to 30; a dry swing; batting practice: a fastball fouled back (a little late), a curve swung over (early: fooled), a change pulled foul (out in front); another dry swing", "1 MONTH / TIMING MATTERS"),
          (V3, V4, "Sixty days", "The calendar flips to 60; live pitching in the cage: a 93 mph fastball he watches; an 85 mph slider coming in, close; he swings early and over it; he works on it; the calendar flips to 90", "60 DAYS / 90 DAYS"),
          (V4, D, "Ninety days, and back", "A full ballpark: he walks up to the plate; 98 mph, late, the bat just behind the ball in slow motion; he looks to the dugout; back in the cage, the timing comes back; then on time in a game, and the ball is gone", "98 MPH / TIMING IS EVERYTHING")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "What if an MLB hitter stopped swinging for 3 months?", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
