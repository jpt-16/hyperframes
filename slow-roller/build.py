"""'The slow ground ball trap' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the grounders (a hard one at him, a slow roller) -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav + CUES.md
    node render_par.js . <chunk dir> 30 <duration> 90 <port>

One shortstop on the series' fielding rig, two plays: a hard grounder right at him and a slow roller that barely gets past the mound.
The exit speeds are illustrative and never shown. A slow roller is not always harder: that is said on screen.
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


HT = {k: P["hits"][k]["tf"] for k in ("hard", "roll", "hard2", "roll2")}
DT = {"hard": 0.58, "roll": 0.34, "hard2": 0.58, "roll2": 0.34}
TR = {k: HT[k] + DT[k] for k in DT}                                   # release of the throw
LR = [[0, 0, 540, 1920], [540, 0, 540, 1920]]
TB = [[0, 0, 1080, 960], [0, 960, 1080, 960]]
# cameras: follow2 rides with the shortstop (who="ss"); the field is home at the origin, center field toward -z, first base toward +x
RUNIN = dict(who="ss", off=[-6, 6, -22], lo=[4, -1, 12], f0=40)               # high behind him, toward second
RUNN = dict(who="ss", off=[-5, 5, -17], lo=[2, -1, 6], f0=50)                 # narrow panes
HOPCU = dict(who="ss", off=[-8, 1.7, 13], lo=[1, -1.3, -2], f0=34, close=1)  # low on the dirt beside the hop
SIDEC = dict(who="ss", off=[-12, 2.8, 4], lo=[2, -0.4, -1], f0=32)             # side on, low: the body and the feet
UPTHROW = dict(who="ss", off=[-15, 7, -13.2], lo=[11, -1.5, 10], f0=42)
BEHIND = dict(c0=[-46, 8.5, -170], c1=[-44, 8.0, -165], l=[-28, 2.2, -128], f0=40)   # behind him, toward home
TOPD = dict(c0=[-30, 80, -102], l=[-30, 0, -102], up=[0, 0, -1], f0=40)                           # straight down on the roller and him
OVER = dict(c0=[-22, 118, -36], c1=[-24, 108, -44], l=[-31, 0, -128], f0=40)       # straight down on the left side
FACE = dict(who="ss", off=[3, 3.4, 9], lo=[0, 0.2, 0], f0=30, close=1)           # his eyes and glove, from the front
CATCH1 = dict(c0=[42, 6.0, -48], c1=[44, 5.8, -50], l=[62, 4.0, -64], f0=32)       # first base, the catch
V2, V3, V4, V5 = S["c1"], S["p1"], S["r1"], S["y1"]
def pair(vs, ta, tb, cam, **kw):
    kw.setdefault("bglow", 1)
    return [dict(rect=LR[0], play=ta[0], vs=vs, ts=ta[1], **kw), dict(rect=LR[1], play=tb[0], vs=vs, ts=tb[1], **kw)]
def tbp(vs, ta, tb, _c=None, **kw):
    return [dict(rect=TB[0], play=ta[0], vs=vs, ts=ta[1], **kw), dict(rect=TB[1], play=tb[0], vs=vs, ts=tb[1], **kw)]

# ----------------------------------------------------------------- 1 the hook: a hard one at him, a slow roller; split screen
H1 = 2.7
shot(0.0, H1, "follow2", [0.0, H1], [0.0, 0.0], streak=1, panes=pair([0.0, H1], ("hard", [-0.5, 1.0]), ("roll", [-0.5, 1.0]), None), **RUNN)
shot(H1, V2, "follow2", [H1, V2], [0.0, 0.0], streak=1, panes=pair([H1, V2], ("hard", [1.0, 2.5]), ("roll", [1.0, 3.2]), None), **RUNN)

# ----------------------------------------------------------------- 2 the hard-hit ball: less time, a true hop
th = HT["hard"]
C1, C2, C3, C4 = V2 + 1.5, V2 + 3.0, V2 + 4.3, V3 - 0.0
shot(V2, C1, "world", [V2, C1], [th - 1.2, th - 0.55], play="hard", streak=1, **BEHIND)
shot(C1, C2, "follow2", [C1, C2], [th - 0.7, th - 0.2], play="hard", **FACE)
shot(C2, C3, "follow2", [C2, C3], [th - 0.3, th + 0.5], play="hard", streak=1, **SIDEC)
shot(C3, C4, "follow2", [C3, C4], [th - 0.45, th + 0.1], play="hard", **HOPCU)

# ----------------------------------------------------------------- 3 the slow roller: charge, the changing hop, the feet, the throw
tr = HT["roll"]
P1, P2, P3 = V3 + 2.0, V3 + 4.0, V3 + 5.7
shot(V3, P1, "world", [V3, P1], [1.1, 2.3], play="roll", streak=1, bglow=1, **TOPD)
shot(P1, P2, "follow2", [P1, P2], [2.0, tr - 0.35], play="roll", streak=1, bglow=1, **RUNIN)
shot(P2, P3, "follow2", [P2, P3], [tr - 0.7, tr + 0.05], play="roll", **HOPCU)
shot(P3, V4, "follow2", [P3, V4], [tr - 0.2, tr + 0.55], play="roll", **SIDEC)

# ----------------------------------------------------------------- 4 the reveal: side by side, then a replay of the slow roller
R1, R2 = V4 + 3.0, V4 + 5.2
shot(V4, R1, "follow2", [V4, R1], [0, 0], panes=pair([V4, R1], ("hard", [th - 0.7, th + 0.35]), ("roll", [tr - 0.7, tr + 0.35]), None), **dict(SIDEC, off=[-12, 2.8, 5], f0=40))
shot(R1, R2, "follow2", [R1, R2], [0, 0], panes=pair([R1, R2], ("hard", [th + 0.3, TR["hard"] + 0.3]), ("roll", [tr + 0.3, TR["roll"] + 0.3]), None), **dict(SIDEC, off=[-12, 2.8, 5], f0=40))
shot(R2, V5, "follow2", [R2, V5], [tr - 1.0, TR["roll"] + 0.3], play="roll", **dict(SIDEC, off=[-10, 3.0, 8], f0=34))

# ----------------------------------------------------------------- 5 the payoff: both again, the throw on the slow roller
Y1, Y2 = V5 + 2.4, V5 + 5.0
shot(V5, Y1, "follow2", [V5, Y1], [0, 0], panes=pair([V5, Y1], ("hard2", [HT["hard2"] - 0.6, HT["hard2"] + 0.6]), ("roll2", [HT["roll2"] - 0.6, HT["roll2"] + 0.6]), None), **RUNN)
shot(Y1, Y2, "follow2", [Y1, Y2], [0, 0], panes=tbp([Y1, Y2], ("hard2", [HT["hard2"] + 0.4, TR["hard2"] + 0.4]), ("roll2", [HT["roll2"] + 0.2, TR["roll2"] + 0.4]), None), **UPTHROW)
shot(Y2, D, "follow2", [Y2, Y2 + 1.0, D], [HT["roll2"] - 0.1, TR["roll2"] - 0.05, TR["roll2"] + 0.5], play="roll2", streak=1, **UPTHROW)

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
title("t1", 0.0, V2, [("Which one", ""), ("is harder?", "yl")], 250, "big")
chip("k1a", 0.1, V2, "HARD HIT", 1400, "sm cy", 40); chip("k1b", 0.1, V2, "SLOW ROLLER", 1400, "sm or", 580)
c.clip("vdiv1", 0, V2, '<div class="vdiv"></div>', cls="layer", style="z-index:11")
# 2 the hard-hit ball
title("t2", V2 + 0.1, V3, [("Less time.", ""), ("A truer hop.", "yl")], 1450, "band")
chip("k2a", C4 - 1.3, V3, "REPLAY", 250, "sm yl")
# 3 the slow roller
title("t3", V3 + 0.1, V4, [("Charge. Judge.", ""), ("Adjust. Throw.", "yl")], 1450, "band")
# 4 the reveal
title("t4", V4 + 0.1, V5, [("Fielding on the move,", ""), ("then throwing", "yl")], 250, "mid")
chip("k4a", V4 + 0.1, R2, "HARD HIT", 1500, "sm cy", 40); chip("k4b", V4 + 0.1, R2, "SLOW ROLLER", 1500, "sm or", 580)
c.clip("vdiv4", V4, R2, '<div class="vdiv"></div>', cls="layer", style="z-index:11")
chip("k4c", R2 + 0.2, V5, "REPLAY", 250, "sm yl")
# 5 the payoff
chip("k5a", V5 + 0.1, Y1, "HARD HIT", 1500, "sm cy", 40); chip("k5b", V5 + 0.1, Y1, "SLOW ROLLER", 1500, "sm or", 580)
c.clip("vdiv5", V5, Y1, '<div class="vdiv"></div>', cls="layer", style="z-index:11")
hdiv("h5", Y1, Y2, [958])
note("n5", Y2, D - 1.6, "Not always: it depends on the ball, the hop and the fielder.", 1620)
VBRAND = round(D - 1.55, 3)
title("t5", Y2 - 0.2, D, [("Hard hit or", ""), ("slow roller?", "yl")], 290, "q")

# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"hardest", "hard", "slow", "roller", "hop", "charge", "forward", "throw", "footwork", "harder", "clean", "toughest", "grounder", "position", "moving"}
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
    if lid == "y2": end = min(end, VBRAND)
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
for tt in [V2 + 0.1, V3 + 0.1, V4 + 0.1, Y2 - 0.2]: cue("impact", tt, -7)
def pv(sh, t, pi=0):
    p0 = sh["panes"][pi] if "panes" in sh else sh
    v = vat(p0.get("vs", sh["vs"]), p0.get("ts", sh["ts"]), t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
for sh in SHOTS:
    for pi, p0 in enumerate(sh.get("panes") or [sh]):
        pl = p0.get("play") or sh.get("play")
        if not pl: continue
        v = pv(sh, HT[pl], pi if "panes" in sh else 0)
        if v is not None: cue("glove", v, -4 if pi == 0 else -9)           # the ball into the glove
        v = pv(sh, TR[pl], pi if "panes" in sh else 0)
        if v is not None and pi == 0: cue("whoosh", v, -10)               # the throw
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
SCENES = [(0.0, V2, "The hook", "Split screen: a hard grounder at the shortstop and a slow roller that barely gets past the mound; he fields the first cleanly, the second forces a charge", "WHICH ONE IS HARDER?"),
          (V2, V3, "The hard-hit ball", "The grounder arrives fast; he reads it, sets, fields it cleanly; a slow-motion replay of the hop", "LESS TIME. A TRUER HOP."),
          (V3, V4, "The slow roller", "From above, the roller creeps in and he charges; the changing hop; his feet adjust; into the throw", "CHARGE. JUDGE. ADJUST. THROW."),
          (V4, V5, "The reveal", "Side by side: the hard-hit play with his body under control, the slow roller on the move; the throw; a replay of the slow roller", "FIELDING ON THE MOVE, THEN THROWING"),
          (V5, D, "The payoff", "Both plays once more, side by side; the throw on the slow roller; the question; the mark", "HARD HIT OR SLOW ROLLER?")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The Slow Ground Ball Trap", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
