"""'Why do some pitchers throw 100 mph?' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the 100 mph fastball from the rig's release point -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

One right-handed pitcher (home whites) and one delivery from the windup: the leg lift, the stride and landing, the pelvis
then the trunk turning, the arm through external rotation, internal rotation and elbow extension to release, and a 100 mph
fastball into the catcher's mitt. Segment colours: legs/ground amber, pelvis orange, trunk cyan, arms green. The force arrows
are qualitative and the delivery is an illustration of a typical one, not a measurement of any pitcher.
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
PB = P["pitches"]["fb"]; FLIGHT = PB["flight"]
def ball_at(k):
    pts = PB["path"]["p"]; hz = PB["path"]["hz"]; i = min(len(pts) - 1, int(k * hz)); return pts[i]
def k_at_z(z):
    pts = PB["path"]["p"]; hz = PB["path"]["hz"]
    for i, p in enumerate(pts):
        if p[2] >= z: return i / hz
    return FLIGHT
ALLP = dict(legs=[-1, NEVER], pelvis=[-1, NEVER], torso=[-1, NEVER], arms=[-1, NEVER])
V2, V3, V4, V5, V6 = S["d1"], S["r1"], S["a1"], S["l1"], S["e1"]
# cameras (home plate's back point at the origin, the mound toward -z; the pitcher is a right-hander, so his arm side is -x)
PCTR = [0.15, 0.62, -57.9]                                                                      # the pitcher at foot contact (for orbits)
SIDE = dict(c0=[-19.0, 4.4, -58.2], c1=[-18.0, 4.3, -58.0], l=[0.0, 3.4, -58.3], f0=40)           # side on, from the third-base side
FEET = dict(c0=[-14.5, 2.0, -56.0], c1=[-13.5, 1.9, -56.4], l=[0.0, 1.7, -57.6], f0=38)             # low, the feet and the mound
ARMCU = dict(c0=[-9.0, 6.0, -53.0], c1=[-8.4, 6.0, -53.4], l=[-0.4, 5.0, -57.0], f0=40)    # behind his throwing side, close on the shoulder and elbow
ARMFR = dict(c0=[-8.4, 6.3, -50.8], c1=[-7.8, 6.2, -51.2], l=[-0.6, 5.2, -55.6], f0=40)    # the arm from in front, on his throwing side
FULL3Q = dict(c0=[-13.0, 5.0, -43.0], c1=[-11.5, 4.9, -44.5], l=[0.0, 3.6, -57.2], f0=36)            # front three-quarter, full body
HANDCU = dict(c0=[-3.4, 6.1, -51.2], c1=[-3.1, 6.0, -51.5], l=[-0.45, 5.4, -53.9], f0=26, close=1, bokeh=60)   # the fingertips at release
PLATE = dict(c0=[-13.0, 3.8, 9.0], c1=[-12.0, 3.6, 8.2], l=[0.2, 2.3, 0.5], f0=28)                 # the catcher receiving it, from the third-base side
FINW = dict(c0=[-13.0, 4.4, -46.0], c1=[-12.0, 4.2, -47.0], l=[0.0, 3.4, -56.2], f0=34)          # the finish, wide

# ----------------------------------------------------------------- 1 the hook: the ball spinning at the lens, stopped; pull back to the pitcher; the gauge; into his body
KZ = k_at_z(-30.5); BZ = ball_at(KZ)
H1 = 2.7; H2 = V2 - 1.35
BALLCAM = dict(c0=[BZ[0] + 0.04, BZ[1] + 0.03, BZ[2] + 1.25], l=[BZ[0] - 0.4, BZ[1] - 0.25, BZ[2] - 12.0], f0=24)
shot(0.0, H1, "world", [0.0, H1], [-0.32, KZ], spinx=0.22, **BALLCAM)
shot(H1, H2, "world", [H1, H2], [KZ, KZ], spinx=0.22, c0=BALLCAM["c0"], c1=[2.2, 6.4, -14.0], l=BALLCAM["l"], l1=[0.0, 4.2, -57.5], f0=24, f1=30)
shot(H2, V2, "orbit", [H2, V2], [0.0, 0.0], ctr=PCTR, a0=-58, a1=-40, r0=17, h0=4.4, ly=3.4, f0=34, xray=[H2 + 0.15, NEVER], xin=0.6, seg=ALLP)

# ----------------------------------------------------------------- 2 the lower body: the windup side on, then low on the feet as he strides, lands and braces
D2 = S["d2"]
shot(V2, D2, "world", [V2, D2], [-1.45, -0.5], **SIDE)
shot(D2, V3, "world", [D2, V3 - 1.1, V3], [-0.5, -0.1, -0.06], grf=[D2 + 0.3, NEVER], **FEET)

# ----------------------------------------------------------------- 3 the rotation: an orbit with the x-ray, pelvis then trunk; a freeze at foot contact; slow motion on
RF0 = W("r1", "coordinated") - 0.1; RF1 = W("r2", "role") - 0.05
RSEG = dict(pelvis=[-1, NEVER], torso=[W("r1", "torso") - 0.1, NEVER], legs=[-1, -0.5], arms=[-1, -0.5])
shot(V3, V4, "orbit", [V3, RF0, RF1, V4], [-0.42, -0.12, -0.12, 0.04], ctr=PCTR, a0=-112, a1=-8, r0=12.5, r1=11.0, h0=4.2, h1=8.5, ly=3.2, f0=40,
     xray=[-1, NEVER], xin=0.01, seg=RSEG, sep=[RF0 - 0.2, RF1 + 1.2])

# ----------------------------------------------------------------- 4 the arm: late cocking into external rotation, then internal rotation, elbow extension, the hand to release
A2 = S["a2"]; AI = W("a2", "internally") - 0.1; AE = W("a2", "elbow") - 0.1; AH = W("a2", "hand") - 0.1; A3 = S["a3"]
ASEG = dict(arms=[-1, NEVER], torso=[-1, V4 + 0.6], pelvis=[-1, V4 + 0.6])
shot(V4, A2, "world", [V4, A2], [-0.26, -0.06], xray=[-1, NEVER], xin=0.01, seg=ASEG, **ARMCU)
shot(A2, AE, "world", [A2, A2 + 0.25, AI, AE], [-0.06, -0.035, -0.035, -0.013], xray=[-1, NEVER], xin=0.01, seg=dict(arms=[-1, NEVER]), er=[A2 + 0.15, AI - 0.05], ir=[AI, AE + 0.3], **ARMFR)
shot(AE, AH, "world", [AE, AH], [-0.013, -0.002], xray=[-1, NEVER], xin=0.01, seg=dict(arms=[-1, NEVER]), elbow=[AE + 0.05, AH + 0.3], **ARMFR)
shot(AH, A3, "ride", [AH, AH + 0.7, A3], [-0.004, 0.006, 0.16], off=[-0.55, 0.35, -2.4], streak=1, f0=34, f1=46)
AQ = A3 + (V5 - A3) / 2
shot(A3, AQ, "world", [A3, AQ], [-1.0, 0.5], **SIDE)
shot(AQ, V5, "world", [AQ, V5], [-1.1, 0.45], **FULL3Q)

# ----------------------------------------------------------------- 5 the release: the full delivery slowed; the fingertips; with the ball to the plate; the catch
L1 = W("l1", "producing") - 0.1; L2 = S["l2"] + 0.2; L3 = W("l2", "fraction") - 0.1
shot(V5, L1, "world", [V5, L1], [-0.75, -0.012], **FULL3Q)
shot(L1, L2, "world", [L1, L2], [-0.012, 0.014], noball=0, **HANDCU)
shot(L2, L3, "ride", [L2, L3], [0.014, FLIGHT - 0.06], off=[-0.55, 0.35, -2.4], streak=1, f0=40, f1=48)
shot(L3, V6, "world", [L3, L3 + 1.1, V6], [FLIGHT - 0.06, FLIGHT + 0.01, FLIGHT + 0.25], streak=1, **PLATE)

# ----------------------------------------------------------------- 6 the end: the finish, a freeze, dark, the mark
EZ = V6 + 1.5
shot(V6, D, "world", [V6, EZ, D], [0.15, 0.6, 0.6], noball=1, **FINW)

for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]
GAUGE = [[0, 0], [H1 + 0.15, 0], [H1 + 1.5, 100], [D, 100]]

# ----------------------------------------------------------------- overlays
c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in CUTS:
    c.set("#flash", '{"opacity":0.3}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)

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
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def note(nid, t0, t1, text, top):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{esc(text)}</div>', cls="layer", style="z-index:14"); pop(f"#{nid}x", t0, 8)
def gauge(gid, t0, t1, top):
    ticks = "".join(f'<line x1="0" y1="-208" x2="0" y2="{-186 if i % 2 else -176}" transform="rotate({-120 + i * 240 / 11:.2f})" />' for i in range(12))
    nums = "".join(f'<text transform="rotate({-120 + m / 110 * 240:.2f}) translate(0 -146) rotate({120 - m / 110 * 240:.2f})">{m}</text>' for m in range(0, 101, 20))
    c.clip(gid, t0, t1, f"""<div class="gauge" id="{gid}x" style="top:{top}px"><svg viewBox="-240 -240 480 330" width="560" height="385">
      <path d="M -180.1 104 A 208 208 0 1 1 180.1 104" class="garc"/><path d="M -180.1 104 A 208 208 0 1 1 180.1 104" class="ghot" pathLength="240" />
      <g class="gtk">{ticks}</g><g class="gnum">{nums}</g><g class="gneedle"><polygon points="-9,0 9,0 0,-196" class="gnd"/></g><circle r="20" class="ghub"/></svg>
      <div class="gread"><b class="gdig">0</b><span>MPH</span></div></div>""", cls="layer", style="z-index:24"); pop(f"#{gid}x", t0, 12)
BAND = 1660

# 1 the hook
gauge("g1", H1 + 0.05, V2 - 1.4, 1160)
title("t1", H1 + 1.55, V2 - 0.02, [("100 MPH.", "yl"), ("How is it possible?", "")], 300, "big")

# 2 the lower body
title("t2", D2 + 0.05, V3 - 0.02, [("The lower body", "am")], BAND)
pinl("p2a", D2 + 0.4, V3 - 0.02, "Drive leg", "pfootR", "am sm"); pinl("p2b", W("d2", "starting") - 0.05, V3 - 0.02, "Stride leg", "pfootL", "am sm")
note("n2", D2 + 0.8, V3 - 0.02, "Arrows show direction and relative size. Illustration, not measured data.", 1585)

# 3 the rotation
title("t3", V3 + 0.1, V4 - 0.02, [("Pelvis + trunk rotation", "")], BAND)
pinl("p3a", V3 + 0.3, V4 - 0.02, "Pelvis", "ppelvis", "sm"); pinl("p3b", W("r1", "torso") - 0.05, V4 - 0.02, "Trunk", "pchest", "cy sm")
chip("c3", RF0 + 0.05, RF1 + 0.2, '<span class="or">Pelvis open</span> · <span class="cyt">trunk still closed</span>', 1500, "sm")
note("n3", RF1 + 0.3, V4 - 0.02, "A typical sequence. Timing and mechanics vary from pitcher to pitcher.", 1585)

# 4 the arm
title("t4", V4 + 0.1, A3 - 0.02, [("Arm acceleration", "gr")], BAND)
pinl("p4a", A2 + 0.2, AI - 0.05, "External rotation", "pelbow", "cy sm"); pinl("p4b", AI, AE - 0.02, "Internal rotation", "pelbow", "gr sm")
pinl("p4c", AE + 0.05, AH - 0.02, "Elbow extension", "pelbow", "gr sm")
chip("c4", A3 + 0.1, V5 - 0.02, '<span class="yt">Real time</span>', 1500, "sm")

# 5 the release
gauge("g5", L3 + 0.4, V6 + 0.9, 1160)
title("t5", L3 + 1.1, V6 + 0.9, [("100 MPH", "yl")], 560, "big")

# 6 the end
c.clip("dark", EZ + 0.3, D, '<div class="dark" id="dkx"></div>', cls="layer", style="z-index:23")
c.ft("#dkx", o(opacity=0), o(opacity=1, duration=0.9, ease="power2.inOut"), EZ + 0.3)
VBRAND = round(S["e2"] - 0.05, 3)
title("t6", VBRAND, D, [("Follow along for our", ""), ("biomechanics series", "yl")], 360, "q")

# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"100", "miles", "hour", "arm", "entire", "body", "ground", "pelvis", "torso", "sequence", "timing", "energy", "explosive", "shoulder", "internally", "elbow",
       "extends", "hand", "accelerates", "release", "quickly", "fast-moving", "fraction", "second", "biomechanics", "fastball"}
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
for t_ in CUTS: cue("whoosh", t_, -14)
cue("riser-m", 0.0, -12); cue("impact", H1, -3); cue("riser-s", H1 + 0.1, -10); cue("impact", H1 + 1.55, -5)
for tt in [D2 + 0.05, V3 + 0.1, V4 + 0.1, L3 + 1.15]: cue("impact", tt, -7)
for tt in [W("r1", "torso") - 0.05, RF0, A2 + 0.2, AI, AE + 0.05]: cue("tick", tt, -6)
def pv(sh, t):
    v = vat(sh["vs"], sh["ts"], t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
CRACKS = []
for sh in SHOTS:
    v = pv(sh, 0.0)
    if v is not None: cue("whoosh", v, -8)                          # the release
    v = pv(sh, FLIGHT)
    if v is not None: cue("glove", v, 0)                            # the mitt
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
SCENES = [(0.0, V2, "The hook", "The ball spinning at the lens, stopped in midair; the camera pulls back to the pitcher; the gauge sweeps to 100; into the x-ray of his body", "100 MPH. HOW IS IT POSSIBLE?"),
          (V2, V3, "The lower body", "Side on: the windup and leg lift; low on the feet: the drive leg pushing off the rubber, the stride foot landing and bracing, force arrows at each foot", "THE LOWER BODY"),
          (V3, V4, "The rotation", "An orbit with the x-ray: pelvis (orange) then trunk (cyan); a freeze at foot contact with the pelvis open and the trunk closed; slow motion on", "PELVIS + TRUNK ROTATION"),
          (V4, V5, "The arm", "Close on the shoulder and elbow: late cocking into external rotation, internal rotation, elbow extension, the hand to release; riding with the ball; the arm action in real time", "ARM ACCELERATION"),
          (V5, V6, "The release", "The full delivery in slow motion, the ball leaving the fingertips, riding with it to the plate, the catch, the gauge at 100", "100 MPH"),
          (V6, D, "The end", "The finish, a freeze, the frame goes dark, the Baseball Decoded mark", "FOLLOW ALONG FOR OUR BIOMECHANICS SERIES")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS, "gauge": GAUGE}
    h = c.page(CSS, "Why Pitchers Throw 100 MPH", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
