"""'Why catcher might be the hardest position in baseball' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the pitches, a dirt ball and the shortstop's grounders -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

One catcher (home whites, mask and pads) through every play: a fastball and a breaking ball received, a curveball in the dirt blocked,
a stolen base (the catch, the exchange, the throw, the second baseman's tag), the signs and the talk with the infield, the gear.
The hook opens on the shortstop's dive from the last episode. tools/plan.json holds the steal's and the block's timings, read back from the rig.
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
HT = {k: P["hits"][k]["tf"] for k in P["hits"]}
PL = json.load(open(os.path.join(HERE, "tools", "plan.json")))      # the steal and the block, read back from the rig (see the README)
GOT, TTAG, SREL, TCB = PL["GOT"], PL["tTag"], 0.75, PL["tcBlock"]
FL = {k: P["pitches"][k]["flight"] for k in ("cfb", "cslide", "cdirt", "csteal")}
BNC = P["pitches"]["cdirt"]["bounce_t"] - FL["cdirt"]               # the dirt ball's bounce, in play time (t = 0 at the mitt)
tfm = HT["mid"]
V2, V3, V4, V5, V6 = S["r1"], S["b1"], S["t1"], S["m1"], S["d1"]
# cameras (home at the origin, center field toward -z, first base toward +x; the catcher crouches at z = 3 facing -z)
RUNIN = dict(who="ss", off=[-6, 6, -22], lo=[4, -1, 12], f0=40)
DIVECU = dict(c0=[-15.5, 1.8, -130.5], c1=[-15.0, 1.7, -131.0], l=[-20, 0.6, -139.5], f0=34, close=1)
FRONTC = dict(c0=[-1.2, 2.4, -8.0], c1=[-0.9, 2.5, -6.0], look="ball", lo=[0.3, 0, 1.6], f0=30, close=1)                      # low in front of the plate: the pitch comes at the lens           # low in front of the plate: the pitch comes at the lens
BEHINDC = dict(c0=[1.8, 5.0, 7.0], c1=[1.2, 4.4, 5.4], l=[0.3, 2.4, -8.0], f0=30, noump=1)                                  # over the catcher's shoulder, the pitch coming in
CATCHF = dict(c0=[-1.4, 2.4, -6.6], c1=[-0.7, 2.6, -5.2], l=[0.4, 2.9, 3.0], f0=28, close=1)                            # the catcher crouched, from low in front                              # over the umpire's shoulder, the pitch coming in
MITTCU = dict(c0=[2.5, 2.5, -4.6], c1=[1.7, 2.4, -3.0], l=[0.5, 2.4, 2.0], f0=26, close=1)                                 # low in front, on the mitt                              # over his shoulder, on the mitt             # low, beside the mitt
SLIDEC = dict(c0=[3.6, 4.2, 6.0], c1=[2.4, 3.8, 4.6], l=[0.8, 2.2, -6.0], f0=30, noump=1)                                    # behind and to his right: the break across the zone
GLOVEC = dict(c0=[-0.6, 2.0, -3.4], c1=[-0.1, 2.2, -2.0], l=[0.9, 2.0, 1.9], f0=26, close=1)                              # low in front: the mitt adjusting                              # low in front: the mitt adjusting                                # from the third-base side: the break across the zone
LOWBLK = dict(c0=[-6.2, 1.1, -6.6], c1=[-4.5, 1.2, -4.0], l=[0.5, 1.0, 1.7], f0=36, close=1)                      # low in front, the dirt ball and the block
LOWBLK2 = dict(c0=[8.6, 1.6, 5.6], c1=[7.2, 1.5, 4.6], l=[0.6, 0.9, 1.6], f0=34, close=1)                         # low from the first-base side                         # low from the first-base side
FIRSTCU = dict(c0=[67, 2.4, -58], c1=[65, 2.8, -60], l=[55, 3.2, -73], f0=34)                                    # the runner in his lead
STEALHI = dict(c0=[-6.5, 5.6, 9.4], c1=[-5.0, 5.2, 7.4], l=[0.3, 3.3, 0.8], f0=32, noump=1)                                # behind and to the left: up, transfer, throw                                # behind and to the left: up, transfer, throw
XFER = dict(c0=[4.8, 4.3, -4.6], c1=[4.0, 4.4, -4.0], l=[0.3, 3.8, 1.2], f0=28, close=1)                              # close on the exchange, from the front                         # close on the exchange, from the front
SECCU = dict(c0=[-8.0, 3.4, -116.0], c1=[-6.6, 3.2, -117.5], l=[0.3, 1.9, -126.3], f0=34)                            # at second: the throw comes in, the tag                         # at second: the throw comes in, the tag
SIGNCU = dict(c0=[0.5, 0.9, -0.9], c1=[0.35, 0.95, -0.2], l=[0.25, 1.05, 2.5], f0=20, close=1)                           # the sign between his thighs, low in front                    # the sign between his thighs
MOUNDV = dict(c0=[-3.2, 4.6, 5.0], c1=[-3.0, 4.6, 5.0], l=[-0.3, 4.4, -59.0], f0=14, noump=1)                            # down the line to the mound: the nod                              # down the line to the mound: the nod
TALKB = dict(c0=[3.4, 5.4, 9.2], c1=[1.6, 5.2, 7.8], l=[-6, 3.2, -88], f0=38, noump=1)                                  # behind him, the infield in front                                   # behind him, the infield in front
FIRSTLOOK = dict(c0=[-1.8, 4.7, 6.0], c1=[-1.2, 4.6, 5.6], l=[52, 3.0, -66], f0=22, noump=1)                         # his view of the runner on first                              # his view of the runner on first
GEAR = dict(ctr=[0.2, 2.2, 3.0], a0=150, a1=232, r0=6.4, r1=5.0, h0=2.4, h1=2.6, ly=0.2, f0=36, close=1)         # around the crouch: the gear
PULLC = dict(noump=1, c0=[-1.4, 5.2, 9.8], c1=[-20, 96, 74], l=[0.3, 2.3, 0.0], l1=[0.0, 0.0, -52], f0=36, f1=46)         # the pull back to the whole field

# ----------------------------------------------------------------- 1 the hook: a shortstop's dive, then the catcher: a pitch at the lens, the catch
H1 = 1.3; H2 = H1 + 0.85; HC = S["h2"] - 0.02
shot(0.0, H1, "follow2", [0.0, H1], [-0.45, tfm - 0.32], play="mid", streak=1, **RUNIN)
shot(H1, HC, "world", [H1, H2, HC], [tfm - 0.32, tfm, tfm], play="mid", streak=1, **DIVECU)
HK1 = HC + 1.95
shot(HC, HC + 0.9, "world", [HC, HC + 0.9], [-1.95, -1.7], c=dict(kind="recv", id="cfb", base="set"), **CATCHF)
shot(HC + 0.9, HK1, "track", [HC + 0.9, HK1], [-FL["cfb"] - 0.12, -0.03], c=dict(kind="recv", id="cfb", base="set"), streak=1, **FRONTC)
shot(HK1, V2, "world", [HK1, V2], [-0.08, 0.25], c=dict(kind="recv", id="cfb", base="set"), streak=1, **BEHINDC)

# ----------------------------------------------------------------- 2 receiving: the fastball into the mitt; the breaking ball across the zone, the mitt adjusting
SPD = W("r1", "speeds"); MOV = W("r1", "movement")
R1b = V2 + 1.5; R2b = SPD + 0.35
shot(V2, R1b, "track", [V2, R1b], [-FL["cfb"] - 0.45, -0.05], c=dict(kind="recv", id="cfb", base="mid"), streak=1, **FRONTC)
shot(R1b, R2b, "world", [R1b, R2b], [-0.3, 0.3], c=dict(kind="recv", id="cfb", base="mid"), **MITTCU)
shot(R2b, MOV + 0.5, "world", [R2b, MOV + 0.5], [-FL["cslide"] - 0.35, 0.1], c=dict(kind="recv", id="cslide", base="lowaway"), streak=1, **SLIDEC)
shot(MOV + 0.5, V3, "world", [MOV + 0.5, V3], [-0.5, 0.35], c=dict(kind="recv", id="cslide", base="lowaway", lead=0.1), **GLOVEC)

# ----------------------------------------------------------------- 3 blocking: a curveball in the dirt; down onto his knees; it drops in front of him
B1e = V3 + 2.4
shot(V3, B1e, "world", [V3, V3 + 0.9, V3 + 1.5, B1e], [BNC - 0.55, BNC - 0.06, TCB + 0.1, TCB + 0.7], c=dict(kind="block", id="cdirt", runner=1), **LOWBLK)
shot(B1e, V4, "world", [B1e, B1e + 1.0, V4], [BNC - 0.3, TCB + 0.2, TCB + 1.5], c=dict(kind="block", id="cdirt", runner=1), **LOWBLK2)

# ----------------------------------------------------------------- 4 throwing out a runner: the runner goes; the catch, up, transfer, throw; the slow replay of the exchange; the tag
STT = W("t1", "steal"); XFR = W("t1", "transfer")
T1e = STT + 0.9
shot(V4, T1e, "world", [V4, T1e], [GOT - 0.7, GOT + 0.55], c=dict(kind="steal", id="csteal"), **FIRSTCU)
T2e = T1e + 1.9
shot(T1e, T2e, "world", [T1e, T2e], [-0.5, 0.95], c=dict(kind="steal", id="csteal"), streak=1, **STEALHI)
T3e = T2e + 1.55
shot(T2e, T3e, "world", [T2e, T3e], [0.06, 0.84], c=dict(kind="steal", id="csteal"), **XFER)
T4e = T3e + 0.95
shot(T3e, T4e, "schase", [T3e, T4e], [SREL, TTAG - 0.25], c=dict(kind="steal", id="csteal"), streak=1, back=9, rise=2.2, side=3.5, f0=44)
shot(T4e, V5, "world", [T4e, V5], [TTAG - 0.45, TTAG + 0.75], c=dict(kind="steal", id="csteal"), **SECCU)

# ----------------------------------------------------------------- 5 the mental side: the sign and the nod; the defense adjusts; the runner; the gear; the focus
M2 = S["m2"]; HLP = W("m2", "helping") - 0.12; DEC = W("m2", "decisions") - 0.1
SEQ = [[-4.3, 2], [-3.45, 1], [-2.75, 3]]
shot(V5, M2, "world", [V5, M2], [-3.4, -3.0], c=dict(kind="rest", id="cfb"), c0=[2.6, 3.3, -3.6], c1=[1.7, 3.0, -1.8], l=[0.15, 2.9, 3.0], f0=34, close=1)
SGN = M2 + 1.45
shot(M2, SGN, "world", [M2, SGN], [-4.35, -2.7], c=dict(kind="sign", id="cfb", seq=SEQ, nod=-2.45), **SIGNCU)
shot(SGN, HLP, "world", [SGN, HLP], [-2.55, -1.55], c=dict(kind="sign", id="cfb", seq=SEQ, nod=-2.45), **MOUNDV)
shot(HLP, DEC, "world", [HLP, DEC], [0.0, 3.0], c=dict(kind="talk", id="cfb", at=[0.55, 1.7, 2.3]), **TALKB)
shot(DEC, S["m3"], "world", [DEC, S["m3"]], [-0.5, -0.5], c=dict(kind="talk", id="cfb", at=[-9, -9, -9]), **FIRSTLOOK)
GEARE = W("m3", "focused") - 0.15
shot(S["m3"], GEARE, "orbit", [S["m3"], GEARE], [-3.0, -3.0], c=dict(kind="rest", id="cfb"), **GEAR)
shot(GEARE, V6, "world", [GEARE, V6], [-FL["cfb"] - 0.6, 0.35], c=dict(kind="recv", id="cfb", base="mid"), streak=1, **MITTCU)

# ----------------------------------------------------------------- 6 the debate: a fast montage; the pull back to the whole field
Q = (S["d2"] - 0.05 - V6) / 4
shot(V6, V6 + Q, "world", [V6, V6 + Q], [-FL["cfb"] - 0.3, 0.2], c=dict(kind="recv", id="cfb", base="mid"), streak=1, **MITTCU)
shot(V6 + Q, V6 + 2 * Q, "world", [V6 + Q, V6 + 2 * Q], [BNC - 0.1, TCB + 0.5], c=dict(kind="block", id="cdirt"), **LOWBLK)
shot(V6 + 2 * Q, V6 + 3 * Q, "world", [V6 + 2 * Q, V6 + 3 * Q], [0.4, 1.3], c=dict(kind="steal", id="csteal"), **STEALHI)
shot(V6 + 3 * Q, S["d2"] - 0.05, "world", [V6 + 3 * Q, S["d2"] - 0.05], [0.0, 1.4], c=dict(kind="talk", id="cfb", at=[0.3, 1.0, 1.6]), **TALKB)
shot(S["d2"] - 0.05, D, "world", [S["d2"] - 0.05, D], [-3.0, -3.0], c=dict(kind="rest", id="cfb"), **PULLC)

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

title("t1", HC + 0.1, V2 - 0.02, [("The hardest", ""), ("position?", "yl")], 1440, "big")
VBRAND = round(D - 1.55, 3)
title("t6", S["d2"], D, [("Hardest position", ""), ("in baseball?", "yl")], 360, "q")

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
cue("riser-s", HC - 0.6, -10); cue("impact", HC, -4)
for tt in [V2, V5]: cue("impact", tt, -8)
def pv(sh, t):
    v = vat(sh["vs"], sh["ts"], t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
CRACKS = []
for sh in SHOTS:
    pid = sh.get("play")
    if pid:                                                         # the shortstop's dive (hook)
        v = pv(sh, 0.0)
        if v is not None: CRACKS.append((v, (vat(sh["vs"], sh["ts"], 0.02) or v) - v > 0.1))
        for bt in P["hits"][pid]["bounces"][:4]:
            v = pv(sh, bt)
            if v is not None: cue("tap", v, -10)
        v = pv(sh, HT[pid]); cue("glove", v, -2)
        continue
    cc = sh.get("c")
    if not cc: continue
    kind, pid = cc["kind"], cc.get("id", "cfb")
    if kind in ("recv", "steal"):
        v = pv(sh, -FL[pid]); cue("whoosh", v, -9)                  # the release
        v = pv(sh, 0.0); cue("glove", v, 0 if kind == "recv" else -1)   # the pop
    if kind == "block":
        v = pv(sh, BNC); cue("tap", v, -6)                          # the dirt
        v = pv(sh, TCB); cue("impact", v, -6)                       # off his chest
        v = pv(sh, -FL["cdirt"]); cue("whoosh", v, -10)
    if kind == "steal":
        v = pv(sh, SREL); cue("whoosh", v, -7)                      # the throw
        v = pv(sh, TTAG); cue("glove", v, -3)                       # the glove at second
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
.ttl.big {{ font-size:128px; line-height:.9; }}

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
SCENES = [(0.0, V2, "The hook", "The shortstop's diving play; a cut to the catcher crouched behind the plate: a fast pitch at the lens, the catch", "THE HARDEST POSITION?"),
          (V2, V3, "Receiving pitches", "A fastball into the mitt (the lens low in front, then beside the mitt); a breaking ball across the zone, the mitt adjusting", ""),
          (V3, V4, "Blocking", "A curveball in the dirt: he drops onto his knees and the ball drops in front of him, from low in front and from the side", ""),
          (V4, V5, "Throwing out runners", "A runner takes off from first; the catch, up, transfer, throw; a slow replay of the exchange; the second baseman's tag", ""),
          (V5, V6, "The mental side", "The sign between his thighs and the pitcher's nod; the defense adjusts to his signals; the runner on first; the gear; focus", ""),
          (V6, D, "The debate", "A fast montage of receiving, blocking, throwing and communicating; the pull back to the whole field; the mark", "HARDEST POSITION IN BASEBALL?")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Catcher: The Hardest Position?", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
