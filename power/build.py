"""'Why some hitters generate more power' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the pitch and the two batted balls -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

Two hitters of different build (the bigger one in charcoal with a red helmet, the smaller one in white with a navy helmet) meet the
same pitch. The bigger one's shoulders turn almost with his hips; the smaller one's hips open first and his torso follows. The exit
speeds are illustrative and are not shown on screen. A back squat in a gym shows that strength is real; the lab shows the sequence.
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
TCON = P["pitches"]["fb"]["t_contact"]
K = lambda k: round(TCON + k, 4)                                    # play time of k (seconds from contact); the pitch is released at t = 0
V2, V3, V4, V5, V6 = S["s1"], S["p1"], S["q1"], S["r1"], S["e1"]
LEFT, RIGHT, FULL = [0, 0, 540, 1920], [540, 0, 540, 1920], [0, 0, 1080, 1920]
TOPP, BOTP = [0, 0, 1080, 960], [0, 960, 1080, 960]
HB_, HS_ = dict(who="big", rel=0.0, hit="big"), dict(who="small", rel=0.0, hit="small")
# cameras (the hitters are right-handers in the left-side box, facing +x; the pitcher is toward -z)
FACEW = dict(c0=[11.5, 4.2, -0.3], c1=[10.8, 4.2, -0.3], l=[-2.6, 3.4, -0.4], f0=76)                               # square to his chest: a tall half-width pane                           # square to his chest, wide: a tall half-width pane
PUSH = dict(c0=[11.5, 4.2, -0.3], c1=[6.8, 4.5, -0.5], l=[-2.6, 3.4, -0.4], l1=[-2.5, 4.2, -0.4], f0=76, f1=46)     # the push toward the smaller hitter     # the push toward the smaller hitter
GYM1 = dict(c0=[5.4, 3.8, 9.6], c1=[4.6, 3.6, 8.8], l=[0.0, 2.9, 0.0], f0=62, close=1)                          # three-quarter, the whole lift in a tall pane
GYM2 = dict(c0=[3.2, 1.6, 6.8], c1=[2.8, 1.8, 6.2], l=[0.0, 2.2, -0.2], f0=58, close=1)                           # low: the legs and the bar
SIDEL = dict(c0=[5.8, 1.0, -4.6], c1=[7.4, 5.0, -4.2], l=[-2.6, 0.6, -0.3], l1=[-2.5, 4.5, -0.5], f0=40, close=1)   # the lab, from the side: starts at the feet, rises with the swing
TQ = dict(c0=[7.2, 4.6, -7.6], c1=[6.4, 4.5, -6.6], l=[-2.6, 3.6, -0.3], f0=48)                                 # three-quarter, the lab (top half)
TOP2 = dict(c0=[-2.8, 17.0, 1.2], c1=[-2.8, 16.0, 1.2], l=[-2.8, 2.0, 1.15], f0=38, up=[0, 0, -1])              # overhead (bottom half)
FACE = dict(c0=[11.5, 4.2, -0.3], c1=[10.9, 4.15, -0.3], l=[-2.4, 3.6, -0.4], f0=46)                            # chest view in the park, full frame
CONTC = dict(c0=[3.6, 2.9, -4.6], c1=[3.3, 2.9, -4.2], l=[0.15, 2.55, -2.62], f0=15, close=1)                           # the ball against the bat, from the side                       # the contact point, from in front of the plate
FOLC = dict(c0=[-1.6, 6.6, 11.5], c1=[-1.3, 7.6, 9.8], l=[-0.8, 2.6, -15.0], f0=34, f1=40, lag=0.3, fw=0.4, bglow=1)
FINC = dict(c0=[7.6, 5.0, -6.4], c1=[6.9, 4.8, -5.6], l=[-2.6, 4.6, 0.0], f0=40, close=1, bokeh=70)               # the finish, close, a dark stadium behind

# ----------------------------------------------------------------- 1 the hook: the comparison, the swings, a freeze at contact, the push on the smaller hitter, the ball
HA, HB2, HC = 1.5, 3.0, V2
shot(0.0, HA, "world", [0.0, HA], [K(-0.85), K(-0.01)], panes=[dict(rect=LEFT, hit=HB_, streak=1), dict(rect=RIGHT, hit=HS_, streak=1)], **FACEW)
shot(HA, HB2, "world", [HA, HB2], [K(-0.01), K(-0.01)], panes=[dict(rect=LEFT, r1=[0, 0, 0, 1920], rw=[HA + 0.2, HA + 1.2], hit=HB_), dict(rect=RIGHT, r1=FULL, rw=[HA + 0.2, HA + 1.2], hit=HS_)], **PUSH)
shot(HB2, HC, "hfollow", [HB2, HC], [K(-0.01), K(1.4)], hit=HS_, streak=1, **dict(FOLC, lag=0.2, fw=0.55))

# ----------------------------------------------------------------- 2 strength isn't the whole story: the same lift, then both in the box
G1 = V2 + 3.6; G2 = V2 + 5.0; G3 = V2 + 6.2
shot(V2, G1, "world", [V2, G1], [0.0, 3.6], panes=[dict(rect=LEFT, gym=dict(who="big", plates=3)), dict(rect=RIGHT, gym=dict(who="small", plates=2))], **GYM1)
shot(G1, G2, "world", [G1, G2], [3.6, 5.0], panes=[dict(rect=LEFT, gym=dict(who="big", plates=3)), dict(rect=RIGHT, gym=dict(who="small", plates=2))], **GYM2)
shot(G2, G3, "world", [G2, G3], [-2.2, -1.6], panes=[dict(rect=LEFT, hit=HB_), dict(rect=RIGHT, hit=HS_)], **FACEW)
shot(G3, V3, "world", [G3, V3], [K(-0.8), K(0.16)], panes=[dict(rect=LEFT, hit=HB_, ghost=0.012), dict(rect=RIGHT, hit=HS_, ghost=0.012)], **FACEW)

# ----------------------------------------------------------------- 3 where power starts: the lab, from the feet up; ground, legs, hips, torso, bat in order
X0, X1 = V3 + 0.5, V4 - 0.5
def at(k): return round(X0 + (k + 0.95) / 1.1 * (X1 - X0), 3)           # the swing runs k = -0.95 .. +0.15 over X0 .. X1
shot(V3, X0, "world", [V3, X0], [K(-0.95), K(-0.95)], hit=HS_, noball=1, lab=1, xray=[-1, NEVER], xin=0.01, seg=dict(legs=[at(-0.8), NEVER]), grf=[V3 + 0.1, NEVER], **SIDEL)
shot(X0, X1, "world", [X0, X1], [K(-0.95), K(0.15)], hit=HS_, lab=1, xray=[-1, NEVER], xin=0.01, grf=[V3 + 0.1, at(-0.1)],
     seg=dict(legs=[at(-0.7), NEVER], pelvis=[at(-0.2), NEVER], torso=[at(-0.12), NEVER], arms=[at(-0.07), NEVER], bat=[at(-0.03), NEVER]), **SIDEL)
shot(X1, V4, "world", [X1, V4], [K(0.15), K(0.15)], hit=HS_, lab=1, xray=[-1, NEVER], xin=0.01, seg=dict(legs=[-1, NEVER], pelvis=[-1, NEVER], torso=[-1, NEVER], arms=[-1, NEVER], bat=[-1, NEVER]), **SIDEL)

# ----------------------------------------------------------------- 4 the separation: hips, then torso, then the bat; full speed; the ball squashing against the bat
ACC = W("q2", "accelerates"); Y0 = ACC - 0.9; Y1 = ACC + 0.8; Y2 = Y1 + 2.0
PS = dict(hit=HS_, noball=1, lab=1, xray=[-1, NEVER], xin=0.01)
shot(V4, Y0, "world", [V4, V4 + 1.2, Y0], [K(-0.8), K(-0.12), K(0.12)], panes=[dict(rect=TOPP, seg=dict(pelvis=[V4 + 0.2, NEVER], torso=[W("q2", "torso") - 0.1, NEVER]), **PS, **TQ), dict(rect=BOTP, sep=[V4 + 0.2, NEVER], seg=dict(pelvis=[V4 + 0.2, NEVER], torso=[W("q2", "torso") - 0.1, NEVER]), **PS, **TOP2)])
shot(Y0, Y1, "world", [Y0, Y1], [K(-0.9), K(0.1)], hit=HS_, streak=1, ghost=0.012, **FACE)
shot(Y1, Y2, "world", [Y1, Y2], [K(-0.010), K(0.012)], hit=HS_, **CONTC)
shot(Y2, V5, "hfollow", [Y2, V5], [K(0.012), K(0.9)], hit=HS_, streak=1, **FOLC)

# ----------------------------------------------------------------- 5 the final reveal: the comparison again, the smaller hitter's swing, the ball deep to the wall
Z1 = V5 + 2.4; Z2 = V5 + 4.6
shot(V5, Z1, "world", [V5, Z1], [K(-0.85), K(0.35)], panes=[dict(rect=LEFT, hit=HB_, streak=1), dict(rect=RIGHT, hit=HS_, streak=1)], **FACEW)
shot(Z1, Z2, "world", [Z1, Z2], [K(-0.5), K(0.12)], hit=HS_, streak=1, ghost=0.012, **FACE)
shot(Z2, Z2 + 1.8, "hfollow", [Z2, Z2 + 1.8], [K(0.0), K(0.9)], hit=HS_, streak=1, **FOLC)
shot(Z2 + 1.8, V6, "bchase", [Z2 + 1.8, V6], [K(0.9), K(4.35)], hit=HS_, bglow=1, bgs=0.07, back=9, rise=3.2, lift=-2.4, f0=40, f1=32)

# ----------------------------------------------------------------- 6 the ending: freeze on the swing; the question
shot(V6, D, "world", [V6, V6 + 1.0, D], [K(-0.03), K(0.0), K(0.0)], hit=HS_, ghost=0.01, **FINC)

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
    c.set("#flash", '{"opacity":0.22}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)
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

for i_, (d0, d1) in enumerate([(0.0, HA + 0.2), (V2, V3), (V5, Z1)]):
    c.clip(f"vd{i_}", d0, d1, '<div class="vdiv"></div>', cls="layer", style="z-index:11")
# 1 the hook: the point is on screen from the first frame
title("t1", 0.0, V2 - 0.05, [("Bigger", "or"), ("≠ more power", "")], 250, "big")
chip("k1a", 0.0, HA + 1.2, "BIGGER HITTER", 1740, "sm or", 50); chip("k1b", 0.0, HA + 1.2, "SMALLER HITTER", 1740, "sm cy", 590)

# 2 strength isn't the whole story
title("t2", W("s2", "strength") - 0.1, V3 - 0.05, [("Strength is", ""), ("only one piece", "yl")], 1480, "band")

# 3 where power starts: the chain, lit in order
chain = [("Ground", V3 + 0.3, AMBER), ("Legs", at(-0.7), AMBER), ("Hips", at(-0.2), HOT), ("Torso", at(-0.12), CYAN), ("Bat", at(-0.03), Y)]
html = "".join(f'<span class="ck" id="ck{i}">{lab}</span>' + ('<i>→</i>' if i < len(chain) - 1 else "") for i, (lab, _, _) in enumerate(chain))
c.clip("chn", V3 + 0.1, V4 - 0.05, f'<div class="chain" id="chnx">{html}</div>', cls="layer", style="z-index:14"); pop("#chnx", V3 + 0.1, 10)
for i, (lab, tt, col) in enumerate(chain):
    c.ft(f"#ck{i}", o(opacity=0.32, color="#AEB8C6"), o(opacity=1, color=col, duration=0.2, ease="power2.out"), tt)
note("n3", V3 + 0.8, V4 - 0.05, "Illustration of a typical sequence. Timing varies from hitter to hitter.", 1600)

# 4 the separation
title("t4", V4 + 0.1, Y0 - 0.05, [("Timing + sequencing", ""), ("= power", "yl")], 960, "mid")
chip("c4a", V4 + 0.6, Y0 - 0.05, '<span class="or">Hips</span> first · <span class="cyt">torso</span> follows', 1500, "sm")

# 5 the final reveal
title("t5", W("r3", "strength") - 0.9, V6 - 0.05, [("Power is more", ""), ("than muscle.", "yl")], 1480, "band")

# 6 the ending
VBRAND = round(D - 1.55, 3)
title("t6", V6, D, [("Strength", ""), ("or mechanics?", "yl")], 330, "q")

# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"shortstop", "hardest", "catcher", "pitch", "speeds", "movement", "bounces", "dirt", "block", "steal", "transfer", "throw", "second", "communicating", "pitcher", "defense",
       "decisions", "heavy", "equipment", "focused", "title", "position"}
CAPS = []
for ln in TM["lines"]:
    wd = ln["words"]; chunk = []
    for n, w in enumerate(wd):
        chunk.append(n)
        brk = w["w"].endswith((",", ".")) or len(chunk) >= 4
        if brk or n == len(wd) - 1: CAPS.append((ln["id"], chunk[0], chunk[-1])); chunk = []
CAPS = [x for x in CAPS if x[0] != "e1"]
for k, (lid, i0, i1) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, D)
    if lid == "e2": end = min(end, VBRAND)
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
cue("riser-m", 0.0, -9); cue("impact", 0.05, -5); cue("impact", HA, -6)
for tt in [W("s2", "strength") - 0.1, V4 + 0.1, W("r3", "strength") - 0.9, V6]: cue("impact", tt, -7)
for _, tt, _ in chain: cue("tick", tt, -6)
def pv(sh, t):
    p0 = sh["panes"][0] if "panes" in sh else sh
    v = vat(p0.get("vs", sh["vs"]), p0.get("ts", sh["ts"]), t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
CRACKS = []
for sh in SHOTS:
    p0 = sh["panes"][0] if "panes" in sh else sh
    if p0.get("gym"):                                               # the bottom of each rep
        for tb in (1.8, 5.4):
            v = pv(sh, tb)
            if v is not None: cue("impact", v, -11)
        continue
    if not p0.get("hit") or p0.get("noball"): 
        if p0.get("hit"):
            v = pv(sh, K(-0.12)); cue("whoosh", v, -10)
        continue
    v = pv(sh, K(-0.12)); cue("whoosh", v, -10)                     # the swing
    v = pv(sh, K(0.0))
    if v is not None: CRACKS.append((v, (vat(sh["vs"], sh["ts"], K(0.02)) or v) - v > 0.1))
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
.vdiv {{ position:absolute; left:539px; width:3px; top:0; bottom:0; background:rgba(255,255,255,.8); box-shadow:0 0 14px rgba(0,0,0,.7); }}
.chip.or {{ color:{HOT}; border:3px solid {HOT}; }} .chip.cy {{ color:{CYAN}; border:3px solid {CYAN}; }}

.ttl .gr {{ color:{GREEN}; }}
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
SCENES = [(0.0, V2, "The hook", "A split screen: a big hitter and a smaller one meet the same pitch; a freeze at contact and a push on the smaller hitter; his ball rockets away", "BIGGER ≠ MORE POWER"),
          (V2, V3, "Strength isn't the whole story", "Both do the same back squat in a gym (the bigger one with more plates); then both step in and swing, side by side", "STRENGTH IS ONLY ONE PIECE"),
          (V3, V4, "Where power starts", "The lab, from the feet up: force arrows at the feet, then legs, hips, torso and bat light up in order, slow motion", "GROUND → LEGS → HIPS → TORSO → BAT"),
          (V4, V5, "The separation", "Three-quarter and overhead views: the hips open first, the torso follows; a full-speed swing; the ball squashing against the bat", "TIMING + SEQUENCING = POWER"),
          (V5, V6, "The final reveal", "The comparison again; the smaller hitter's swing; the ball flies deep toward the wall", "POWER IS MORE THAN MUSCLE."),
          (V6, D, "The ending", "Freeze on the swing; the question; the mark", "STRENGTH OR MECHANICS?")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Why Some Hitters Generate More Power", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
