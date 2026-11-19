"""'Why shortstop is one of the hardest positions in baseball' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the pitch and eight ground balls (bounces, one bad hop) -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

One shortstop (home whites, the defense) through every play: the dive up the middle, his range from straight above, a bad
hop, the backhand in the hole, the plant and throw across the diamond, a jump throw, talking it over with the second baseman,
the second baseman covering, the shortstop covering, and a routine play to finish.
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
TR = {"mid": HT["mid"] + 1.3, "hole": HT["hole"] + 0.58, "chop": HT["chop"] + 0.34, "routine": HT["routine"] + 0.62, "bad": HT["bad"] + 0.7, "hole2": HT["hole2"] + 0.66, "ss2": HT["ss2"] + 0.36, "b2": HT["b2"] + 0.55}
V2, V3, V4, V5, V6 = S["g1"], S["o1"], S["t1"], S["m1"], S["p1"]
# cameras (home at the origin, center field toward -z, first base toward +x; the shortstop starts at (-36, -140))
BEHIND = dict(c0=[-46, 8.5, -170], c1=[-44, 8.0, -165], l=[-28, 2.2, -128], f0=40)              # behind the shortstop, toward home
OVER = dict(c0=[-22, 118, -36], c1=[-24, 108, -44], l=[-31, 0, -128], f0=40)     # straight down on the left side of the infield, center field up
HOPCU = dict(who="ss", off=[-8, 1.7, 13], lo=[1, -1.3, -2], f0=34, close=1)    # low on the dirt beside the hop
HOLECU = dict(who="ss", off=[-6, 2.6, 15], lo=[0, -1.4, -1], f0=36, close=1)     # in front of the hole, low
HOLEBK = dict(c0=[-55, 8, -165], c1=[-53, 7.5, -162], l=[-57, 2.5, -132], f0=40)                 # behind him in the hole
JUMPCU = dict(who="ss", off=[-7.8, 5, 13.9], lo=[2, -0.5, 0], f0=40)              # from the third-base side, the jump throw
CATCH1 = dict(c0=[42, 6.0, -48], c1=[44, 5.8, -50], l=[62, 4.0, -64], f0=32)                     # first base, the catch
TALK = dict(c0=[0, 6.6, -97], c1=[0, 6.3, -100], l=[0, 4.0, -131], f0=30)                       # the middle infielders before the pitch
FORCE = dict(c0=[0, 105, -58], c1=[0, 100, -62], l=[0, 0, -132], f0=50)
FORCE2 = dict(c0=[0, 105, -58], c1=[0, 100, -62], l=[0, 0, -132], f0=50)
DIVECU = dict(c0=[-15.5, 1.8, -130.5], c1=[-15.0, 1.7, -131.0], l=[-20, 0.6, -139.5], f0=34, close=1)
UPTHROW = dict(who="ss", off=[-15, 7, -13.2], lo=[11, -1.5, 10], f0=42)
RUNIN = dict(who="ss", off=[-6, 6, -22], lo=[4, -1, 12], f0=40)                           # high behind the mound, toward second
PULL = dict(c0=[-42, 7.5, -160], c1=[-6, 190, 70], l=[-33, 2.0, -136], l1=[0, 0, -80], f0=40, f1=48)   # the pull back to the whole field

# ----------------------------------------------------------------- 1 the hook: up the middle, the dive, a freeze, up and the throw
tf = HT["mid"]; ta = TR["mid"] + 1.0
H1 = 1.7; H2 = H1 + 0.55; H3 = H2 + 1.35
shot(0.0, H1, "follow2", [0.0, H1], [-0.45, tf - 0.32], play="mid", streak=1, **RUNIN)
shot(H1, H3, "world", [H1, H2, H3], [tf - 0.32, tf, tf], play="mid", streak=1, **DIVECU)
shot(H3, V2, "follow2", [H3, V2], [tf, TR["mid"] + 0.95], play="mid", streak=1, **UPTHROW)

# ----------------------------------------------------------------- 2 covering ground: straight down; his range; up the middle, deep in the hole, in between
G2 = S["g2"]; GM = W("g2", "middle") - 0.6; GH = W("g2", "hole") - 0.5; GB = W("g2", "everything") - 0.3
RT = dict(mid=dict(done=1), hole=dict(done=1), chop=dict(done=1))
shot(V2, GM, "world", [V2, GM], [-0.6, -0.6], play="mid", range=[V2 + 0.3, V3], **OVER)
shot(GM, GH, "world", [GM, GH], [0.0, HT["mid"] + 0.05], play="mid", range=[-1, V3], routes=dict(mid={}), streak=1, **OVER)
shot(GH, GB, "world", [GH, GB], [0.0, HT["hole"] + 0.05], play="hole", range=[-1, V3], routes=dict(mid=dict(done=1), hole={}), streak=1, **OVER)
shot(GB, V3, "world", [GB, V3 - 0.6, V3], [0.0, HT["chop"] + 0.05, HT["chop"] + 0.2], play="chop", range=[-1, V3 + 1], routes=RT, streak=1, **OVER)

# ----------------------------------------------------------------- 3 the hops: a bad hop up close; the backhand deep in the hole
tb = HT["bad"]; O2 = W("o2", "sharply") - 0.2
shot(V3, O2, "follow2", [V3, V3 + 0.8, O2 - 0.8, O2], [tb - 0.9, tb - 0.6, tb + 0.02, tb + 0.35], play="bad", streak=1, **HOPCU)
th = HT["hole"]
shot(O2, V4, "follow2", [O2, V4 - 0.7, V4], [th - 0.75, th + 0.03, th + 0.3], play="hole", streak=1, **HOLECU)

# ----------------------------------------------------------------- 4 the throw: plant and throw across the diamond, the ball all the way to first; the jump throw
T2 = S["t2"]
shot(V4, T2 + 0.6, "world", [V4, T2 + 0.6], [th - 0.2, TR["hole"] + 0.05], play="hole", streak=1, **HOLEBK)
T3 = W("t2", "off-balance") - 0.15
shot(T2 + 0.6, T3 - 0.55, "chase", [T2 + 0.6, T3 - 0.55], [TR["hole"] + 0.05, TR["hole"] + 0.85], play="hole", streak=1, back=8, up=2.4, side=3.0, f0=44)
shot(T3 - 0.55, T3, "world", [T3 - 0.55, T3], [TR["hole"] + 0.85, TR["hole"] + 1.2], play="hole", streak=1, **CATCH1)
t2 = HT["hole2"]; tr2 = TR["hole2"]
shot(T3, V5, "follow2", [T3, T3 + 1.2, V5 - 1.0, V5], [t2 - 0.5, t2 + 0.05, tr2 + 0.05, tr2 + 0.6], play="hole2", streak=1, **JUMPCU)

# ----------------------------------------------------------------- 5 the mental side: they talk it over; the second baseman covers; then the shortstop covers
M2 = W("m1", "cover") - 0.2; M3 = W("m1", "decisions") - 0.3
shot(V5, M2, "world", [V5, M2], [-1.0, -1.0], play="ss2", talk=[V5 + 0.2, M2 + 1], **TALK)
shot(M2, M3, "world", [M2, M3], [-0.2, TR["ss2"] + 0.6], play="ss2", cover=[M2 + 0.2, M3 + 1], cover_who="b2", streak=1, **FORCE)
shot(M3, V6, "world", [M3, V6], [-0.2, TR["b2"] + 0.7], play="b2", cover=[M3 + 0.15, V6 + 1], cover_who="ss", streak=1, **FORCE2)

# ----------------------------------------------------------------- 6 the payoff: the dive, the backhand, the jump throw; then a routine one; pull back to the whole field
P1 = V6 + 0.9; P2 = P1 + 0.9; P3 = P2 + 1.0; P4 = S["p2"] + 0.1
shot(V6, P1, "world", [V6, P1], [tf - 0.25, tf + 0.05], play="mid", streak=1, **DIVECU)
shot(P1, P2, "follow2", [P1, P2], [th - 0.2, th + 0.06], play="hole", streak=1, **HOLECU)
shot(P2, P3, "follow2", [P2, P3], [tr2 - 0.25, tr2 + 0.15], play="hole2", streak=1, **JUMPCU)
tr_ = HT["routine"]
shot(P3, P4, "world", [P3, P4], [tr_ - 1.0, TR["routine"] + 0.4], play="routine", streak=1, **BEHIND)
shot(P4, D, "world", [P4, D], [TR["routine"] + 0.4, TR["routine"] + 1.2], play="routine", streak=1, **PULL)

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
    c.set("#flash", '{"opacity":0.25}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)
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

title("t1", H2 - 0.05, H3 + 0.6, [("The hardest", ""), ("position?", "yl")], 1440, "big")
chip("c2", V2 + 0.4, GM - 0.05, '<span class="cyt">The shortstop’s ground</span>', 1560, "sm")
pinl("p2a", GM + 0.6, GH - 0.02, "Up the middle", "sball", "gr sm"); pinl("p2b", GH + 0.6, GB - 0.02, "Deep in the hole", "sball", "sm"); pinl("p2c", GB + 0.8, V3 - 0.05, "In between", "sball", "yl sm")
pinl("p3a", V3 + 1.4, O2 - 0.1, "Bad hop", "sball", "sm")
pinl("p3b", O2 + 0.2, V4 - 0.05, "Backhand", "ss", "sm")
pinl("p4a", T3 + 1.0, V5 - 0.05, "Off balance", "ss", "sm")
chip("c5", V5 + 0.5, M2 - 0.05, 'Who covers second?', 1560, "sm")
pinl("p5a", M2 + 0.3, M3 - 0.05, "Second baseman covers", "b2", "yl sm"); pinl("p5b", M3 + 0.25, V6 - 0.05, "Shortstop covers", "ss", "yl sm")
VBRAND = round(D - 1.55, 3)
title("t6", P4 + 0.1, D, [("More than just", ""), ("good hands", "yl")], 360, "q")

# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"shortstop", "hardest", "hands", "ground", "middle", "hole", "hops", "bad", "adjust", "half", "throw", "across", "off-balance", "communicate", "cover",
       "bases", "split-second", "decisions", "routine-looking", "lot", "more", "shortstops"}
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
cue("riser-s", H1 - 0.6, -10); cue("impact", H2, -4)
for tt in [P4 + 0.1]: cue("impact", tt, -5)
def pv(sh, t):
    v = vat(sh["vs"], sh["ts"], t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
CRACKS = []
for sh in SHOTS:
    pid = sh.get("play")
    if not pid or sh.get("talk"): continue
    v = pv(sh, 0.0)
    if v is not None: CRACKS.append((v, (vat(sh["vs"], sh["ts"], 0.02) or v) - v > 0.1))
    for bt in P["hits"][pid]["bounces"][:6]:
        v = pv(sh, bt)
        if v is not None: cue("tap", v, -10)
    v = pv(sh, HT[pid]); cue("glove", v, -2)
    v = pv(sh, TR[pid]); cue("whoosh", v, -9)
for sh in SHOTS:                                                    # the receiver's mitt: approximately, the throw's flight after release
    pid = sh.get("play")
    if not pid or sh.get("talk"): continue
    th_ = 0.62 if pid not in ("ss2", "b2") else 0.45
    v = pv(sh, TR[pid] + th_ + (0.35 if pid in ("mid", "hole", "hole2", "routine", "bad", "chop") else 0)); cue("glove", v, -4)
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
SCENES = [(0.0, V2, "The hook", "A hard grounder up the middle: the shortstop dives, a freeze as he gloves it, up and the throw", "THE HARDEST POSITION?"),
          (V2, V3, "Covering ground", "Straight down on the left side of the infield: his range on the dirt, then three balls (up the middle, deep in the hole, a chopper in between) and his routes", "UP THE MIDDLE / DEEP IN THE HOLE / IN BETWEEN"),
          (V3, V4, "The hops", "Low on the dirt: a hard one takes a bad hop and his glove follows it; the backhand deep in the hole", "BAD HOP / BACKHAND"),
          (V4, V5, "The throw", "From the hole: plant and throw across the diamond, riding with the ball to first; a jump throw, off balance", "OFF BALANCE"),
          (V5, V6, "The mental side", "The middle infielders talk behind their gloves before the pitch; the second baseman covers second on one ball, the shortstop on the next", "WHO COVERS SECOND?"),
          (V6, D, "The payoff", "The dive, the backhand, the jump throw; a routine play; the camera pulls back to the whole field; the mark", "MORE THAN JUST GOOD HANDS")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Shortstop: The Hardest Position?", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
