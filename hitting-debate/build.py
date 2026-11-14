"""'A-Rod vs. Teacherman: two different hitting philosophies' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the fastball and the two line drives -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

Two right-handed hitters, told apart by their kits and their colour on screen: hitter A (white, navy helmet, cyan graphics)
swings with the knob cue: his hands and knob work down toward the ball and the barrel releases late. Hitter B (charcoal,
red helmet, black sleeves, orange graphics) loads into his rear hip and turns the barrel back into the plane early (a
rearward arc). Both stride, move their weight onto the front side, turn their hips and meet the same 95 mph fastball with
the barrel. Neither is shown as the right way: the video lays out the two cues and the debate.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
TCON = P["pitches"]["fb"]["t_contact"]
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
K = lambda k: round(TCON + k, 4)                                    # play time of k (seconds from contact); every pitch is released at t = 0
TOPP, BOTP, FULL = [0, 0, 1080, 960], [0, 960, 1080, 960], [0, 0, 1080, 1920]
def hit(who, ball=None): return dict(who=who, rel=0.0, hit=ball)
HA, HB = hit("A", "ld"), hit("B", "ld2")
GA, GB = CYAN, HOT
# cameras (the hitter is a right-hander in the box on the third-base side, facing +x; the pitcher is toward -z)
FACE2 = dict(c0=[6.6, 4.9, -0.6], c1=[6.2, 4.85, -0.5], l=[-2.4, 4.5, -0.3], f0=56)                  # square to his chest, from across the plate (half-height panes)
FACE = dict(c0=[11.5, 4.2, -0.3], c1=[10.9, 4.15, -0.3], l=[-2.4, 3.6, -0.4], f0=46)                 # the same, full frame
OTS = dict(c0=[-1.4, 7.8, 12.5], c1=[-1.3, 7.6, 11.6], l=[-0.9, 0.96, -15.0], f0=38)                      # over his rear shoulder, toward the pitcher
FRONT2 = dict(c0=[3.2, 6.2, -9.0], c1=[2.9, 6.0, -8.5], l=[-2.2, 3.9, 0.2], f0=46)                     # from in front of him, on the pitcher's side (half panes)
HIPCU = dict(o="broot", lo="broot", c0=[-6.8, 4.2, -6.5], c1=[-6.2, 4.0, -6.0], l=[-0.4, 3.0, 0.2], f0=40)      # low, behind his back hip
LEGCU = dict(o="broot", lo="broot", c0=[-3.4, 2.4, -9.5], c1=[-3.1, 2.4, -8.8], l=[-0.8, 2.3, 0.0], f0=38)        # low, from the open side, on the rear leg
CONT2 = dict(c0=[3.2, 2.3, -9.0], c1=[3.0, 2.3, -8.6], l=[-0.6, 2.9, -1.8], f0=34, close=1)                    # low, in front of the plate, on the contact point (half panes)

# ----------------------------------------------------------------- 1 the hook: both swings, frozen as they start
V1, V2, V3, V4 = S["a1"], S["t1"], S["i1"], S["e1"]
HF = 1.3; HU = W("h2", "actual") - 0.1                              # frozen from HF; both swings finish from HU
HOOKV, HOOKT = [0.0, HF, HU, V1], [K(-0.75), K(-0.17), K(-0.17), K(0.1)]
IA = W("h1", "knob") - 0.05; IB = W("h2", "teacherman")
shot(0.0, V1, "world", HOOKV, HOOKT, panes=[
    dict(rect=TOPP, hit=HA, intent=dict(v=[IA, HU + 0.05]), hl=dict(knob=[IA, HU + 0.05]), streak=1),
    dict(rect=BOTP, hit=HB, tip=dict(from_=-0.2, to=0.0, ahead=1, v=[IB + 0.2, HU + 0.05]), hl=dict(hip=[IB, HU + 0.05]), streak=1)], **FACE2)

# ----------------------------------------------------------------- 2 A-Rod's cue (hitter A): over the shoulder, then square to him
A2 = W("a1", "cue", end=True) + 0.04
AV = [V1, V1 + 0.75, W("a1", "downward"), W("a1", "punching-like") + 0.1, A2]; AT = [K(-0.95), K(-0.45), K(-0.2), K(-0.08), K(-0.07)]
shot(V1, A2, "world", AV, AT, hit=HA, knob=dict(from_=-0.2, v=[W("a1", "downward") - 0.1, A2 + 1]), intent=dict(v=[W("a1", "downward"), A2 + 1], k=-0.2, dur=0.6), **OTS)
AK, AH, AM, AB = W("a1", "knob"), W("a1", "hands"), W("a1", "moving"), W("a1", "baseball")
AVb = [A2, AK - 0.1, AM, AB + 0.05, V2]; ATb = [K(-0.6), K(-0.2), K(-0.08), K(0), K(0.22)]
shot(A2, V2, "world", AVb, ATb, hit=HA, ghost=0.012, knob=dict(from_=-0.2, v=[AM - 0.15, V2 + 1]), hl=dict(knob=[AK - 0.05, V2 + 1], hands=[AH - 0.05, V2 + 1]),
     rot=[AK + 0.15, V2 + 1], **FACE)

# ----------------------------------------------------------------- 3 Teacherman (hitter B): not a straight line; the rear hip; the rearward arc
T2 = S["t2"]
TS = W("t1", "straight")
TV = [V2, W("t1", "literally"), TS, W("t1", "ball") + 0.08, T2]; TT = [K(-1.0), K(-0.22), K(-0.12), K(0), K(0.05)]
shot(V2, T2, "world", TV, TT, hit=HB, straight=dict(v=[W("t1", "literally") - 0.1, T2 + 1], k=-0.22, dur=0.5), knob2=dict(from_=-0.22, c=HOT, v=[W("t1", "literally"), T2 + 1]), **FACE)
T3 = W("t2", "creating") - 0.08
HV = [T2, W("t2", "rear"), T3]; HT = [K(-1.0), K(-0.42), K(-0.32)]
shot(T2, T3, "obj", HV, HT, hit=HB, hl=dict(hip=[W("t2", "rear") - 0.05, T3 + 1]), **HIPCU)
T4 = W("t2", "and", nth=0) - 0.1
LV = [T3, W("t2", "rear", nth=1), T4]; LT = [K(-0.32), K(-0.22), K(-0.18)]
shot(T3, T4, "obj", LV, LT, hit=HB, hl=dict(hip=[T3 - 1, T4 + 1], leg=[W("t2", "stretch") - 0.05, T4 + 1]), **LEGCU)
BQ, BA = W("t2", "quickly"), W("t2", "rearward")
BV = [T4, BQ + 0.1, BA, BA + 0.55, V3]; BT = [K(-0.2), K(-0.16), K(-0.1), K(0), K(0.06)]
shot(T4, V3, "world", BV, BT, hit=HB, ghost=0.012, tip=dict(from_=-0.2, v=[BQ, V3 + 1]), hl=dict(barrel=[BQ, V3 + 1]), **FACE)

# ----------------------------------------------------------------- 4 different cues, different emphasis: both, the same camera; then the feel vs. the movement
C2 = W("i2", "what") - 0.06
CV = [V3, V3 + 0.5, C2 - 0.4, C2]; CT = [K(-0.6), K(-0.3), K(0.0), K(0.06)]
EMPH_A = dict(rect=TOPP, hit=HA, knob=dict(from_=-0.25), intent=dict(v=[V3 + 0.3, C2 + 1], k=-0.2, dur=0.5), hl=dict(hands=[V3 + 0.3, C2 + 1], knob=[V3 + 0.3, C2 + 1]))
EMPH_B = dict(rect=BOTP, hit=HB, tip=dict(from_=-0.2), hl=dict(hip=[V3 + 0.3, C2 + 1], barrel=[V3 + 1.2, C2 + 1]))
shot(V3, C2, "world", CV, CT, panes=[EMPH_A, EMPH_B], **FACE2)
C3 = S["i3"]
CV2 = [C2, C3 - 0.5, C3]; CT2 = [K(-0.5), K(0.0), K(0.05)]
shot(C2, C3, "world", CV2, CT2, panes=[dict(EMPH_A, intent=dict(v=[C2 + 0.2, C3 + 1], k=-0.2, dur=0.5), hl=dict(hands=[C2, C3 + 1], knob=[C2, C3 + 1])),
                                     dict(EMPH_B, hl=dict(hip=[C2, C3 + 1], barrel=[C2, C3 + 1]))], ghost=0.012, **FRONT2)
FL, FM = W("i3", "feel"), W("i3", "actual")
QL, QH, QN, QB = W("i3", "rear"), W("i3", "hip"), W("i3", "hands"), W("i3", "barrel")
QV = [C3, FM, QL, QH, QN, QB + 0.05, V4]; QT = [K(-1.1), K(-0.45), K(-0.24), K(-0.12), K(-0.06), K(0), K(0.05)]
shot(C3, V4, "world", QV, QT, hit=HA, intent=dict(v=[FL - 0.05, FM + 0.1], k=-0.3, dur=0.6),
     hl=dict(leg=[QL - 0.05, V4 + 1], hip=[QH - 0.05, V4 + 1], hands=[QN - 0.05, V4 + 1], barrel=[QB - 0.05, V4 + 1], c=Y), rot=[QH - 0.05, V4 + 1],
     tip=dict(from_=-0.12, v=[QB - 0.1, V4 + 1], c=Y), **FACE)

# ----------------------------------------------------------------- 5 the takeaway: two line drives; the split becomes one shot; the question
E2 = W("e1", "or") + 0.1
EV = [V4, V4 + 1.0, E2]; ET = [K(-0.25), K(0.0), K(0.06)]
shot(V4, E2, "world", EV, ET, panes=[dict(rect=TOPP, hit=HA, streak=1, ghost=0.01), dict(rect=BOTP, hit=HB, streak=1, ghost=0.01)], **CONT2)
EM0, EM1 = E2 + 0.15, E2 + 0.95                                     # the split merges into one frame
FOLV = [E2, D]; FOLT = [K(0.06), K(0.06) + (D - E2) * 0.75]
FOLC = dict(c0=[-1.6, 6.6, 11.5], c1=[-1.3, 7.4, 10.2], l=[-0.8, 2.6, -15.0], f0=34, f1=38, lag=0.3, fw=0.35, bglow=1)
shot(E2, D, "hfollow", FOLV, FOLT, panes=[dict(rect=TOPP, r1=FULL, rw=[EM0, EM1], hit=HA, streak=1), dict(rect=BOTP, r1=[0, 1920, 1080, 0], rw=[EM0, EM1], hit=HB, streak=1)], **FOLC)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
for sh in SHOTS:                                                    # field.js reads trail starts as "from"
    for p in [sh] + sh.get("panes", []):
        for key in ("knob", "tip", "knob2"):
            if key in p and "from_" in p[key]: p[key]["from"] = p[key].pop("from_")
CUTS = [x["a"] for x in SHOTS[1:]]

# ----------------------------------------------------------------- overlays
c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in CUTS:
    c.set("#flash", '{"opacity":0.35}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)

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
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style=f"z-index:{26 if cls == 'q' else 22}")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.05 * i)
def plab(pid, t0, t1, top, who, html):
    c.clip(pid, t0, t1, f'<div class="plb {who}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:16"); pop(f"#{pid}x", t0, 10)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def seam(sid, t0, t1):
    c.clip(sid, t0, t1, '<div class="hseam"></div>', cls="layer", style="z-index:11")
LAB_A = 'A-Rod <b>· knob to the ball</b>'
LAB_B = 'Teacherman <b>· rear-hip load</b>'
BAND = 1650

# 1 the hook
seam("sm1", 0, V1); plab("l1a", 0.2, V1 - 0.02, 24, "cy", LAB_A); plab("l1b", IB - 0.05, V1 - 0.02, 1838, "or", LAB_B)
title("t1a", 0.0, W("h2", "different") - 0.06, [("Two hitting", ""), ("philosophies.", "acc")], 815, "mid")
title("t1b", W("h2", "different") - 0.04, HU - 0.05, [("Which one", ""), ("is right?", "yl")], 815, "mid")
pinl("p1a", IA + 0.25, HU - 0.05, "Knob → ball", "knob", "cy sm", 0)
pinl("p1b", IB + 0.1, HU - 0.05, "Rear hip", "hipR", "sm", 1)

# 2 A-Rod
title("t2", W("a1", "described") - 0.05, V2 - 0.02, [("A-Rod:", "cy"), ("knob toward the ball", "")], BAND)
pinl("p2a", W("a1", "downward") + 0.2, A2 - 0.02, "The cue", "knob", "cy sm")
pinl("p2b", AK - 0.05, AM - 0.1, "Knob", "knob", "cy sm"); pinl("p2c", AH - 0.05, AB - 0.1, "Hands", "hands", "cy sm")
pinl("p2d", AK + 0.2, AB - 0.2, "Hips turn", "pelvis", "cy sm")
pinl("p2e", AB + 0.1, V2 - 0.02, "Barrel through the ball", "barrel", "cy sm")

# 3 Teacherman
pinl("p3a", W("t1", "straight") + 0.1, T2 - 0.02, "Straight to the ball?", "contact", "wh sm")
pinl("p3b", W("t1", "ball") - 0.3, T2 - 0.02, "The knob's actual path", "knob", "sm")
title("t3", W("t2", "philosophy") - 0.05, V3 - 0.02, [("Teacherman:", "or"), ("rear-hip load + quick barrel", "")], BAND)
pinl("p3c", W("t2", "rear") - 0.05, T3 - 0.02, "Rear hip", "hipR", "sm")
pinl("p3d", W("t2", "stretch") - 0.05, T4 - 0.02, "Stretch against the rear leg", "knee", "sm")
chip("c3", BQ - 0.05, V3 - 0.02, "Launch quickness", 560, "or big")
pinl("p3e", BA - 0.05, V3 - 0.02, "Rearward arc", "tip", "sm")

# 4 different cues
seam("sm4", V3, C3)
plab("l4a", V3 + 0.05, C3 - 0.02, 24, "cy", LAB_A); plab("l4b", V3 + 0.1, C3 - 0.02, 1838, "or", LAB_B)
title("t4", V3 + 0.1, C3 - 0.02, [("Different cues.", ""), ("Different emphasis.", "yl")], 790, "mid")
pinl("p4a", V3 + 0.6, C2 - 0.02, "Hands + knob", "hands", "cy sm", 0); pinl("p4b", V3 + 0.7, C2 - 0.02, "Rear hip + barrel", "hipR", "sm", 1)
chip("c4a", FL - 0.05, FM - 0.05, '<span class="cyt">The feel:</span> knob to the ball', 560)
chip("c4b", FM - 0.03, V4 - 0.02, '<span class="yt">The movement:</span> a sequence', 560)
for i, (wd, key, lab) in enumerate([(QL, "knee", "Rear leg"), (QH, "pelvis", "Hip"), (QN, "hands", "Hands"), (QB, "barrel", "Barrel")]):
    pinl(f"p4s{i}", wd - 0.05, V4 - 0.02, f"{i + 1} · {lab}", key, "yl sm")

# 5 the takeaway
seam("sm5", V4, EM1)
plab("l5a", V4 + 0.05, EM0, 24, "cy", LAB_A); plab("l5b", V4 + 0.1, EM0, 1838, "or", LAB_B)
title("t5", V4 + 0.25, W("e2", "that's") - 0.1, [("The goal:", ""), ("barrel control,", "yl"), ("power & timing.", "yl")], 790, "mid")
QQ = W("e2", "that's") - 0.05
title("t6", QQ, D, [("Which philosophy", ""), ("do you prefer?", "yl")], 420, "q")
VBRAND = round(LN("e2")["t1"] + 0.45, 3)

# ----------------------------------------------------------------- captions: the voiceover, word by word
A_ = "acc"
CAPS = [("h1", 0, 3, {0: A_}), ("h1", 4, 8, {5: A_, 8: A_}),
        ("h2", 0, 2, {1: A_}), ("h2", 3, 7, {6: A_}), ("h2", 8, 11, {10: A_}),
        ("a1", 0, 3, {0: A_}), ("a1", 4, 6, {5: A_}), ("a1", 7, 11, {9: A_, 10: A_}), ("a1", 12, 16, {14: A_, 16: A_}), ("a1", 17, 20, {20: A_}),
        ("t1", 0, 4, {1: A_}), ("t1", 5, 9, {9: A_}), ("t1", 10, 12, {12: A_}), ("t1", 13, 16, {13: A_}),
        ("t2", 0, 3, {1: A_}), ("t2", 4, 8, {7: A_, 8: A_}), ("t2", 9, 14, {10: A_, 13: A_, 14: A_}), ("t2", 15, 19, {16: A_, 17: A_}), ("t2", 20, 23, {22: A_, 23: A_}),
        ("i1", 0, 5, {5: A_}),
        ("i2", 0, 3, {0: A_}), ("i2", 4, 8, {7: A_}), ("i2", 9, 13, {11: A_}), ("i2", 14, 18, {15: A_}),
        ("i3", 0, 5, {3: A_}), ("i3", 6, 11, {8: A_}), ("i3", 12, 15, {14: A_, 15: A_}), ("i3", 16, 21, {20: A_, 21: A_}), ("i3", 22, 25, {24: A_, 25: A_}), ("i3", 26, 29, {26: A_, 27: A_, 29: A_}),
        ("e1", 0, 3, {2: A_}), ("e1", 4, 9, {5: A_, 8: A_}), ("e1", 10, 14, {13: A_}), ("e1", 15, 17, {16: A_, 17: A_}),
        ("e2", 0, 2, {2: A_})]
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
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8); cue("impact", 0.05, -5)
for tt in [W("h2", "different") - 0.04, W("a1", "described") - 0.05, W("t2", "philosophy") - 0.05, BQ - 0.05, V3 + 0.1, V4 + 0.25, QQ]: cue("impact", tt, -7)
for tt in [IA, IB, W("a1", "downward"), TS, W("t2", "rear"), W("t2", "stretch"), FL, QL, QH, QN, QB]: cue("tick", tt, -6)
CRACKS = []
def pv(sh, t):                                                      # video time of play time t in a shot (its first pane's clock)
    p = sh["panes"][0] if "panes" in sh else sh
    v = vat(p.get("vs", sh["vs"]), p.get("ts", sh["ts"]), t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
for sh in SHOTS:
    h_ = (sh["panes"][0] if "panes" in sh else sh).get("hit")
    if not h_: continue
    v = pv(sh, 0.0); cue("whoosh", v, -9)                           # the release
    v = pv(sh, K(-0.12)); cue("whoosh", v, -10)                     # the swing
    v = pv(sh, K(0.0))
    if v is not None and h_.get("hit"):
        r = (vat(sh["vs"], sh["ts"], K(0.02)) or v) - v
        CRACKS.append((v, r > 0.1))
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
.ttl.big {{ font-size:150px; }} .ttl.q {{ font-size:128px; z-index:30; }} .ttl.mid {{ font-size:112px; left:0; right:0; padding:18px 30px 24px; background:rgba(5,8,13,.86); }}
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
"""])

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [(0.0, V1, "The hook", "Split: hitter A (top) and hitter B (bottom) start their swings and freeze; A's knob-to-ball line; B's rear hip and the arc his barrel will take; both swings finish", "TWO HITTING PHILOSOPHIES. / WHICH ONE IS RIGHT?"),
          (V1, V2, "A-Rod's cue", "Hitter A over the shoulder: the knob path and the cue line to the ball; square to him in slow motion: knob, hands, hips turning, the barrel through the ball", "A-ROD: KNOB TOWARD THE BALL"),
          (V2, V3, "Teacherman's view", "Hitter B: a straight knob-to-ball line against the knob's actual path; his rear hip loading; stretch against the rear leg; the barrel's rearward arc into the zone", "TEACHERMAN: REAR-HIP LOAD + QUICK BARREL / LAUNCH QUICKNESS"),
          (V3, V4, "Different emphasis", "Both swings from the same camera, then from behind the plate: A's hands and knob, B's rear hip and barrel; then hitter A alone: the feel (knob to the ball) and the sequence (rear leg, hip, hands, barrel)", "DIFFERENT CUES. DIFFERENT EMPHASIS."),
          (V4, D, "The takeaway", "Both line drives off the barrel in slow motion; the split becomes one shot following the ball; the question; Baseball Decoded", "THE GOAL: BARREL CONTROL, POWER & TIMING. / WHICH PHILOSOPHY DO YOU PREFER?")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "A-Rod vs. Teacherman", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
