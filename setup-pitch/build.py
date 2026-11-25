"""'The pitch that looks too good to be true' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the four pitches (fastball, changeup, high fastball, breaking ball) -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

One right-handed hitter, one pitcher and one catcher. The swing is always timed to the fastball (93 mph); the changeup (82 mph) leaves the same
release and arrives about a twentieth of a second later, so the same swing is early on it. The high fastball passes above the bat. The eyes
in the close-ups are two tiny meshes added for those shots only. The glowing path lines and the two-ball replay are illustrations.
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
FL = {k: v["flight"] for k, v in P["pitches"].items() if k != "cdirt"}
K = lambda k: round(TCON + k, 4)                                    # play time of k (seconds from fastball contact); the pitch is released at t = 0
TOPP, BOTP = [0, 0, 1080, 960], [0, 960, 1080, 960]
H = lambda pitch="fb", **kw: dict(who="quiet", rel=0.0, pitch=pitch, **kw)
QUIET = dict(who="quiet", rel=0.0, hit="quiet")                    # the fastball down the middle, swung at (the hook cuts before contact)
# cameras (the hitter is a right-hander in the left-side box facing +x; the pitcher is toward -z)
FACE = dict(c0=[11.5, 4.2, -0.3], c1=[10.9, 4.15, -0.3], l=[-2.4, 3.6, -0.4], f0=46)                           # chest view
FACE2 = dict(c0=[6.6, 4.9, -0.6], c1=[6.2, 4.85, -0.5], l=[-2.4, 4.5, -0.3], f0=56)                              # chest view, a half-height pane
SIDEN = dict(c0=[13.0, 4.0, -5.0], c1=[12.5, 3.9, -4.6], l=[-0.6, 3.2, -1.6], f0=40)                          # first-base side, close on the plate
CONTC = dict(c0=[3.6, 2.9, -4.6], c1=[3.3, 2.9, -4.2], l=[0.15, 2.55, -2.62], f0=15, close=1)                    # the ball against the bat
PCH = dict(c0=[-13.0, 5.0, -43.0], c1=[-11.5, 4.9, -44.5], l=[0.0, 3.6, -57.2], f0=36)                          # the pitcher, front three-quarter
PARM = dict(c0=[-8.4, 6.3, -50.8], c1=[-7.8, 6.2, -51.2], l=[-0.6, 5.2, -55.6], f0=40)                          # the arm from in front
MITTHI = dict(c0=[3.2, 3.5, -1.6], c1=[2.8, 3.4, -1.1], l=[0.3, 3.4, 1.7], f0=26)                               # the mitt, up high
HIGHF = dict(c0=[2.5, 4.8, -8.5], c1=[2.1, 4.6, -7.8], l=[-1.6, 3.4, -1.0], f0=30)                                # from the pitcher side: the ball coming in over the bat
FRZ = dict(c0=[3.5, 3.4, -9.0], c1=[3.1, 3.3, -8.2], l=[-0.7, 2.8, -3.0], f0=26)                                # from the pitcher side: the ball an instant before the bat
SIDEP = dict(c0=[-19.0, 4.4, -58.2], c1=[-18.0, 4.3, -58.0], l=[0.0, 3.4, -58.3], f0=40)                         # the pitcher, side on
MITTA = dict(c0=[2.6, 2.1, -5.2], c1=[2.2, 2.0, -4.6], l=[0.3, 2.3, 1.6], f0=26)                                  # the catcher receiving a changeup, from the pitcher side
MITTMD = dict(c0=[3.05, 2.34, -1.62], c1=[2.65, 2.24, -1.02], l=[0.35, 2.09, 1.68], f0=26)                         # the mitt, at the middle
BEHIND = dict(c0=[1.8, 8.5, 13.0], c1=[1.4, 8.0, 11.0], l=[0.2, 3.0, -46.0], f0=22)                             # over the hitter's shoulder, toward the mound
TOP = dict(c0=[0.15, 100.0, -13.2], l=[0.15, 0.0, -13.2], up=[0, 0, -1], f0=52)                                      # straight down on the pitch lane: the pitcher at the top
LATE = dict(c0=[4.0, 4.6, -12.0], c1=[3.6, 4.4, -11.2], l=[-1.0, 3.2, -0.5], f0=34)                          # from the pitcher side, wider: the swing is over before the ball arrives
SIDEN2 = dict(c0=[15.0, 4.4, -6.5], c1=[14.0, 4.3, -6.0], l=[-0.5, 3.4, -4.2], f0=46)                          # first-base side, a little wider: the swing and the ball coming in
SIDE2 = dict(c0=[24.0, 4.2, -6.0], c1=[23.0, 4.1, -6.0], l=[0.0, 3.0, -5.0], f0=50)                              # first-base side, the last stretch of the pitch
V2, V3, V4, V5, V6 = S["h2"], S["t1"], S["f1"], S["g1"], S["e1"]

# ----------------------------------------------------------------- 1 the hook: his eyes, the ball coming, the swing, cut just before contact
shot(0.0, 1.45, "eyes", [0.0, 1.45], [-0.2, 0.26], hit=QUIET, eyes=1, a0=18, a1=8, d0=2.1, d1=1.8, cy=0.16, f0=28)
shot(1.45, 2.55, "hpov", [1.45, 2.55], [0.12, K(-0.05)], hit=QUIET, f0=44, f1=38)
shot(2.55, 3.45, "world", [2.55, 3.45], [K(-0.55), K(-0.03)], hit=QUIET, ghost=0.012, **FACE)
shot(3.45, V2, "world", [3.45, V2], [K(-0.014), K(-0.014)], hit=QUIET, **FRZ)

# ----------------------------------------------------------------- 2 a high fastball, the swing and miss, the next pitch looks hittable
A1, A2, A3, A4 = V2 + 1.75, V2 + 3.35, V2 + 4.55, V2 + 5.95
shot(V2, A1, "world", [V2, A1], [-1.25, -0.02], hit=H("hi"), **PCH)
shot(A1, A2, "world", [A1, A2], [0.20, 0.56], hit=H("hi"), glow=1, bgs=0.03, noump=1, **HIGHF)
shot(A2, A3, "world", [A2, A3], [0.3, 0.56], hit=H("hi"), **MITTHI)
shot(A3, A4, "world", [A3, A4], [-1.1, 0.0], hit=H("fb", take=-0.3), **SIDEP)
shot(A4, V3, "hpov", [A4, V3], [0.02, 0.34], hit=H("fb", take=-0.3), f0=44, f1=36)

# ----------------------------------------------------------------- 3 a quick sequence, then the hitter starts to anticipate
B1, B2, B3, B4 = V3 + 1.6, V3 + 3.2, V3 + 4.8, V3 + 6.2
shot(V3, B1, "hride", [V3, B1], [0.0, FL["hi"]], hit=H("hi", take=-0.3), off=[-0.5, 0.3, -3.0], f0=34, f1=46)
shot(B1, B2, "hride", [B1, B2], [0.0, FL["br"]], hit=H("br", take=-0.3), off=[0.5, 0.3, -3.0], f0=34, f1=46)
shot(B2, B3, "hride", [B2, B3], [0.0, FL["fb"]], hit=H("fb", take=-0.3), off=[-0.5, 0.3, -3.0], f0=34, f1=46)
shot(B3, B4, "eyes", [B3, B4], [-1.3, -0.45], hit=H("fb", take=-0.3), eyes=1, a0=-16, a1=-6, d0=2.2, d1=1.9, cy=0.16, f0=28)
shot(B4, V4, "world", [B4, V4], [-1.25, 0.0], hit=H("fb", take=-0.3), expect=[dict(pitch="fb", v=[B4, NEVER], c="#56D1FF")], **BEHIND)

# ----------------------------------------------------------------- 4 the same look, a different speed: a split screen, the early swing, the replay, the timing off
C1, C2, C3, C4 = V4 + 2.25, V4 + 4.45, V4 + 7.1, V4 + 9.0
SPL = lambda pt, pb, vs, ts, **kw: [dict(rect=TOPP, hit=H("fb"), vs=vs, ts=ts, **pt, **kw), dict(rect=BOTP, hit=H("ch"), vs=vs, ts=ts, **pb, **kw)]
shot(V4, C1, "race", [V4, C1], [0, 0], panes=SPL(dict(gcol=0x56d1ff), dict(gcol=0xff6a3d), [V4, C1], [-0.06, 0.44], glow=1, gnorm=1, bgs=0.03), rel0=0.0, lead="fb", cx=8.0, cy=3.6, ly=3.2, lz=0.0, zstop=-3.5, f0=40)
shot(C1, C2, "world", [C1, C2], [0, 0], panes=[dict(rect=TOPP, hit=QUIET, vs=[C1, C2], ts=[K(-0.7), K(0.25)], ghost=0.014), dict(rect=BOTP, hit=H("ch"), vs=[C1, C2], ts=[K(-0.7), K(0.25)], ghost=0.014)], **FACE2)
shot(C2, C3, "world", [C2, C3 - 0.5, C3], [0.0, 0.5, 0.5], hit=H("fb", take=-0.3), ball2=dict(pitch="ch"), glow=1, gnorm=1, bgs=0.06, gcol=0x56d1ff, gcol2=0xff6a3d,
     expect=[dict(pitch="fb", v=[C2, NEVER], c="#56D1FF"), dict(pitch="ch", v=[C2, NEVER], c="#FF6A3D")], **TOP)
shot(C3, C4, "world", [C3, C4], [0.16, 0.52], hit=H("ch"), glow=1, bgs=0.03, noump=1, **LATE)
shot(C4, V5, "eyes", [C4, V5], [0.3, 0.5], hit=H("ch"), eyes=1, a0=10, a1=-10, d0=2.0, d1=1.7, cy=0.16, f0=28)

# ----------------------------------------------------------------- 5 setting him up: another pitch, swung through, the catcher, the expected path
D1, D2, D3, D4 = V5 + 1.7, V5 + 3.6, V5 + 5.5, V5 + 6.3
shot(V5, D1, "world", [V5, D1], [-1.2, 0.0], hit=H("ch"), **PCH)
shot(D1, D2, "world", [D1, D2], [K(-0.6), K(0.35)], hit=H("ch"), streak=1, **FACE)
shot(D2, D3, "world", [D2, D3], [0.40, 0.482], hit=H("ch"), **MITTA)
shot(D3, D4, "world", [D3, D4], [0.484, 0.484], hit=H("ch"), **dict(MITTA, c0=MITTA["c1"]))
shot(D4, V6, "world", [D4, V6], [-0.9, 0.45], hit=H("ch"), expect=[dict(pitch="fb", v=[D4 + 0.2, NEVER], c="#56D1FF")], **BEHIND)

# ----------------------------------------------------------------- 6 the ending question
E1 = V6 + 3.2
shot(V6, E1, "world", [V6, E1], [-1.3, 0.2], hit=H("fb", take=-0.3), **dict(BEHIND, c0=[-7.0, 5.6, 11.0], c1=[-5.5, 5.2, 8.0]))
shot(E1, D, "eyes", [E1, D], [-0.3, 0.2], hit=H("fb", take=-0.3), eyes=1, a0=14, a1=4, d0=2.2, d1=1.9, cy=0.16, f0=28)

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

# 1 the hook: the question is on screen from the first frame
title("t1", 0.0, V2, [("Too good", ""), ("to be true?", "yl")], 250, "big")
# 2 up and out, then the hittable one
title("t2", V2 + 0.1, V3, [("Not always", ""), ("a mistake", "yl")], 1450, "band")
chip("k2a", V2 + 0.25, A1, "HIGH FASTBALL", 1830, "sm yl"); chip("k2b", A1 + 0.5, A2, "SWING AND MISS", 1830, "sm rd")
chip("k2c", A4 + 0.2, V3, "LOOKS HITTABLE", 1830, "sm gr")
# 3 a sequence, then anticipation
title("t3", V3 + 0.1, V4, [("The hitter starts", ""), ("to anticipate", "yl")], 1450, "band")
chip("k3a", V3 + 0.1, B1, "HIGH FASTBALL", 1830, "sm yl"); chip("k3b", B1, B2, "BREAKING BALL", 1830, "sm or"); chip("k3c", B2, B3, "NEAR THE MIDDLE", 1830, "sm cy")
chip("k3d", B4 + 0.1, V4, "WHAT HE EXPECTS", 1830, "sm cy")
note("n3", B4 + 0.1, V4, "Illustration: the path he expects.", 1740)
# 4 the same look, a different speed
title("t4", V4 + 0.1, V5, [("Same look.", ""), ("Slower arrival.", "yl")], 1450, "band")
chip("k4a", V4 + 0.1, C2, "FASTBALL", 880, "sm cy", 40); chip("k4b", V4 + 0.1, C2, "CHANGEUP", 1840, "sm or", 40)
chip("k4c", C1 + 0.1, C2, "ON TIME", 880, "sm gr", 40); chip("k4d", C1 + 0.1, C2, "TOO EARLY", 1840, "sm rd", 40)
hdiv("h4", V4, C2, [958])
chip("k4e", C2 + 0.1, C3, '<span class="cyt">● FASTBALL</span> &nbsp; <span class="or">● CHANGEUP</span>', 1830, "sm")
chip("k4g", C2 + 0.1, C3, "REPLAY", 880, "sm yl", 40)
note("n4", C2 + 0.1, C3, "Illustration: both pitches replayed from the same release.", 1740)
chip("k4f", C3 + 0.1, V5, "TIMING OFF", 1830, "sm rd")
# 5 setting him up
title("t5", V5 + 0.1, V6, [("Strikes ≠", ""), ("a setup", "yl")], 1450, "band")
chip("k5a", V5 + 0.1, D1, "CHANGEUP", 1830, "sm or"); chip("k5b", D1 + 0.3, D2, "SWUNG THROUGH", 1830, "sm rd")
chip("k5c", D4 + 0.2, V6, "WHAT HE EXPECTS", 1830, "sm cy")
note("n5", D4 + 0.2, V6, "Illustration. Timing and pitch movement vary from pitch to pitch.", 1740)
# 6 the ending question
VBRAND = round(D - 1.55, 3)
title("t6", V6, D, [("Mistake or", ""), ("master plan?", "yl")], 290, "q")


# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"pitch", "perfect", "mistake", "setup", "set", "anticipating", "changeup", "fastball", "timing", "slower", "wrong", "expect", "strikes", "setting", "good", "true", "middle"}
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
cue("riser-m", 0.0, -8); cue("impact", 0.05, -4)
for tt in [V2 + 0.1, V3 + 0.1, V4 + 0.1, V5 + 0.1, V6]: cue("impact", tt, -7)
def pv(sh, t):
    p0 = sh["panes"][0] if "panes" in sh else sh
    v = vat(p0.get("vs", sh["vs"]), p0.get("ts", sh["ts"]), t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
for sh in SHOTS:
    h_ = (sh.get("panes") or [sh])[-1].get("hit") or sh.get("hit")
    if not h_: continue
    if "take" not in h_ and sh["cam"] != "hpov":
        v = pv(sh, K(-0.12))
        if v is not None: cue("whoosh", v, -10)                      # the swing
    if h_.get("pitch") != "fb" or "hit" not in h_:
        v = pv(sh, FL[h_.get("pitch", "fb")] + 0.01)
        if v is not None: cue("glove", v, -3)                       # into the mitt
CRACKS = []
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
SCENES = [(0.0, V2, "The hook", "Extreme close-up of his eyes tracking a fastball; the ball from his eyes; the swing; a cut and freeze just before contact", "TOO GOOD TO BE TRUE?"),
          (V2, V3, "Up and out", "The pitcher throws a high fastball; the swing and miss; the glove takes it high; the next pitch comes in and looks hittable", "NOT ALWAYS A MISTAKE"),
          (V3, V4, "A sequence, then anticipation", "A high fastball, a breaking ball, a pitch near the middle in quick cuts; his eyes; the path he expects glows", "THE HITTER STARTS TO ANTICIPATE"),
          (V4, V5, "Same look, slower arrival", "Split screen: a fastball and a changeup from the same release; the swing on time and too early; a replay of both balls; the timing off", "SAME LOOK. SLOWER ARRIVAL."),
          (V5, V6, "Setting him up", "Another pitch, swung through; a freeze on the catcher receiving it; the path he expected", "STRIKES ≠ A SETUP"),
          (V6, D, "The question", "Over his shoulder toward the mound, then his eyes; the mark", "MISTAKE OR MASTER PLAN?")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The Pitch That Looks Too Good to Be True", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
