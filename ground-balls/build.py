"""'Work through the ball': why infielders read the hop and work through ground balls (1080x1920, voiceover + effects).

    python3 tools/physics.py                                       # four ground balls (bounces) + the shortstop's plays -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/ground-balls.mp4 --video-bitrate 16M

The balls' hops and the shortstop's footwork come from assets/play.json. No times or time savings are shown.
Shots, captions and reveals are keyed to the words of the voiceover.
"""
import json, os, re, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
f2 = lambda x: f"{x:.2f}"

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows (t = 0 at contact)
PLS, BLS = P["plays"], P["balls"]
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def hold(a, b, cam, t0, **kw): shot(a, b, cam, [a, b], [t0, t0], "freeze", **kw)
WRONG0, HOP0, WORK0, PAY0 = (LN(k)["t0"] - 0.06 for k in ["wrong", "hop", "work", "pay"])
ST, TH = PLS["stand"], PLS["through"]
hop_aw = [b[0] for b in BLS["awkward"]["bounces"] if 130 < (b[1][0] ** 2 + b[1][2] ** 2) ** 0.5 < 145][0]
SHW = {"path": 1, "hops": 1}
# hook: contact; the shortstop waits, flat-footed; the long hop comes down right in front of him; freeze as it kicks up at him
S = dict(hC=0.35, h1=0.9, h2=1.25)
rate(0, S["h1"], "plate", -S["hC"], 1, "rt", play="stand")
rate(S["h1"], S["h2"], "hook", S["h1"] - S["hC"], 1, "rt", play="stand", show=SHW, cu=[S["h1"], WRONG0])
S["hT"] = hop_aw + 0.035
S["h3"] = S["h2"] + (S["hT"] - (S["h2"] - S["hC"])) * 2
rate(S["h2"], S["h3"], "hook", S["h2"] - S["hC"], 0.5, "slow2", play="stand", show=SHW, cu=[S["h1"], WRONG0])
hold(S["h3"], WRONG0, "hook", S["hT"], play="stand", show=SHW, cu=[S["h1"], WRONG0])
# the wrong way: on from the freeze, the late field at his body, the gather, the throw; then a replay that counts the extra steps
S["w1"] = WRONG0 + (ST["t_release"] + 0.3 - S["hT"])
rate(WRONG0, S["w1"], "hook", S["hT"], 1, "rt", play="stand", show=SHW, cu=[WRONG0, S["w1"]])
S["w2"] = W("wrong", "you", nth=1) + 0.55
rate(S["w1"], S["w2"], "wide", ST["t_release"] + 0.3, 1, "rt", play="stand")
S["wT0"] = ST["t_field"] - 0.3
rate(S["w2"], HOP0, "side", S["wT0"], 0.5, "replay", play="stand", show={"path": 1, "hops": 1, "glove": ST["t_field"], "foot": 1})
# read the hop: routine (attack it) and short hop (stay down) side by side; then the high hop (create space)
HALVES = [dict(play="routine", cam="halfL"), dict(play="short", cam="halfL")]
S["r1"] = W("hop", "if") - 0.08
rate(HOP0, S["r1"], "halfL", 2.0 - (W("hop", "attack") + 0.25 - HOP0), 1, "rt", mode="split", halves=HALVES, show={"path": 1, "hops": 1, "glove": 0.3})
HI = PLS["high"]
S["r2"] = S["r1"] + 0.8
rate(S["r1"], S["r2"], "high", 1.35, 1, "rt", play="high", show={"path": 1, "hops": 1, "glove": 1.0})
S["r3"] = S["r2"] + 2.2
rate(S["r2"], S["r3"], "high", 1.35 + 0.8, 0.5, "slow2", play="high", show={"path": 1, "hops": 1, "glove": 1.0})
rate(S["r3"], WORK0, "high", 1.35 + 0.8 + 1.1, 1, "rt", play="high", show={"path": 1, "hops": 1, "glove": 1.0})
# work through it: real time in front of him, then a half-speed replay with the movement arrow
S["k1"] = WORK0 + 2.55
rate(WORK0, S["k1"], "through", -0.1, 1, "rt", play="through", show={"path": 1, "hops": 1})
S["kT0"] = 0.55
rate(S["k1"], PAY0, "behind", S["kT0"], 0.5, "replay", play="through", show={"path": 1, "hops": 1, "glove": TH["t_field"], "arrow": "through", "foot": 1})
# payoff: side by side on the same ball, then a half-speed replay of glove-to-release
PH = [dict(play="stand", cam="halfL"), dict(play="through", cam="halfL")]
SHP = {"path": 1, "hops": 1, "glove": 0.3, "foot": 1}
S["p1"] = PAY0 + 3.2
rate(PAY0, S["p1"], "halfL", 0.0, 1, "rt", mode="split", halves=PH, show=SHP)
S["p2"] = LN("pay")["t1"] + 0.05
rate(S["p1"], S["p2"], "halfL", 0.95, 0.5, "replay", mode="split", halves=PH, show=SHP)
rate(S["p2"], D, "wide", TH["t_release"] - 0.3, 1, "rt", play="through")
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
S = {k: round(v, 4) for k, v in S.items()}
S["list"] = SHOTS

def at_play(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]):
            return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
def first_v(cond_shots, t):
    for x in cond_shots:
        v = at_play(x, t)
        if v is not None: return v
    return None

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0.45, D, '<div class="spd rt" id="spd">Real time</div>', cls="layer", style="z-index:30")

# ----------------------------------------------------------------- hook
c.clip("hook0", 0, 0.44, """<div class="eyebrow"><i></i>Infield defense</div>
  <div class="hk big"><span class="hl">Don't let the ball</span><span class="hl acc">play you.</span></div>""", cls="layer", style="z-index:12")
c.to(".hk.big", o(opacity=0, y=-30, filter="blur(10px)", duration=0.12, ease="power2.in"), 0.3)
hw = LN("hook")["words"]
HOOK = [("Great", 0, 0), ("infielders", 1, 0), ("don't", 2, 1), ("just", 3, 1), ("field", 4, 1), ("the", 5, 2), ("ball.", 6, 2), ("They", 7, 3), ("work", 8, 3), ("through", 9, 4), ("it.", 10, 4)]
lines = {}
for k, (w, wi, ln) in enumerate(HOOK):
    lines.setdefault(ln, []).append(f'<span class="hw{" acc" if ln >= 3 else ""}" id="hw{k}">{esc(w)}</span>')
c.clip("hook", 0.44, S["h3"] - 0.02, '<div class="eyebrow"><i></i>Infield defense</div><div class="hk sm">' + "".join(f'<span class="hl">{" ".join(v)}</span>' for v in lines.values()) + "</div>", cls="layer", style="z-index:12")
for k, (w, wi, ln) in enumerate(HOOK):
    c.ft(f"#hw{k}", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.16, ease="power3.out"), hw[wi]["t0"] - 0.04)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S["h3"] - 0.16)
c.clip("q", S["h3"], WRONG0 - 0.02, '<div class="qq" id="qq">Don\'t let the ball <span class="acc">play you.</span></div>', cls="layer", style="z-index:13")
c.ft("#qq", o(opacity=0, scale=1.16, filter="blur(12px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), S["h3"])
c.clip("hkm", S["h3"] + 0.1, WRONG0 - 0.02, '<div class="tg hot" id="hkmx" style="top:1560px">Flat-footed · the hop is on top of him</div>', cls="layer", style="z-index:12")

# ----------------------------------------------------------------- captions
CAPS = [("wrong", 0, 5, {2: "acc"}), ("wrong", 6, 9, {9: "acc"}), ("wrong", 10, 13, {13: "acc"}), ("wrong", 14, 17, {17: "acc"}), ("wrong", 18, 23, {}),
        ("hop", 0, 5, {3: "acc", 4: "acc", 5: "acc"}), ("hop", 6, 9, {6: "cb"}), ("hop", 10, 14, {13: "cb", 14: "cb"}), ("hop", 15, 21, {}), ("hop", 22, 23, {22: "acc", 23: "acc"}), ("hop", 24, 29, {}),
        ("work", 0, 1, {}), ("work", 2, 5, {3: "acc"}), ("work", 6, 8, {}), ("work", 9, 11, {9: "cb", 10: "cb", 11: "cb"}), ("work", 12, 13, {13: "cb"}), ("work", 14, 17, {17: "cb"}), ("work", 18, 22, {}),
        ("pay", 0, 4, {4: "cb"}), ("pay", 5, 10, {10: "hot"}), ("pay", 11, 15, {}), ("pay", 16, 17, {17: "cb"}), ("pay", 18, 23, {}), ("pay", 24, 26, {25: "cb"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, (TM["lines"][IDX[lid] + 1]["t0"] - 0.1) if IDX[lid] + 1 < len(TM["lines"]) else D)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), words[n]["t0"] - 0.04)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top, left=None):
    pos = f"top:{top}px" + (f";left:{left}px;transform:none" if left is not None else "")
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="{pos}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)

# ----------------------------------------------------------------- the wrong way, counted
rp = [x for x in SHOTS if x["speed"] == "replay" and x.get("play") == "stand"][0]
vF = at_play(rp, ST["t_field"]); vS = [at_play(rp, s_) for s_ in ST["steps"]]; vR = at_play(rp, ST["t_release"])
tag("w1", vF - 0.05, vS[0] - 0.05, "hot", "Fields it at his body", 1500)
c.clip("w2", vS[0] - 0.05, vR, '<div class="tg hot" id="w2x" style="top:1500px">Extra steps to reset: <b class="stk">' + "".join(f'<i id="n{k + 1}">{k + 1}</i>' for k in range(len(vS))) + '</b></div>', cls="layer", style="z-index:12"); pop("#w2x", vS[0] - 0.05, 14)
for k, vs_ in enumerate(vS):                                  # the count goes up as each foot comes down
    c.ft(f"#n{k + 1}", o(opacity=0, scale=1.6), o(opacity=1, scale=1, duration=0.12), vs_ - 0.02)
    if k: c.to(f"#n{k}", o(opacity=0, duration=0.05), vs_ - 0.02)
tag("w3", vR, HOP0 - 0.05, "hot", "Then the throw, from a standstill", 1500)

# ----------------------------------------------------------------- read the hop
c.clip("splitA", HOP0, S["r1"], """<div class="seam"></div>
  <div class="half l"><div class="hd cb"><span>Routine hop</span><b>Attack it</b></div></div>
  <div class="half r"><div class="hd yl"><span>Short hop</span><b>Stay down</b></div></div>""", cls="layer", style="z-index:11")
c.ft("#splitA .hd", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.25, ease="power3.out"), HOP0 + 0.1)
tag("hh", S["r1"] + 0.1, WORK0 - 0.05, "wh", "High hop: back up a step, let it come down", 1560)

# ----------------------------------------------------------------- work through it
kr = [x for x in SHOTS if x["speed"] == "replay" and x.get("play") == "through"][0]
tag("k1", kr["a"] + 0.15, at_play(kr, TH["t_field"]) - 0.1, "cb", "Eyes on the ball, angled approach", 1560)
tag("k2", at_play(kr, TH["t_field"]) - 0.1, at_play(kr, TH["t_field"] + 0.3), "cb", "Glove out front", 1560)
tag("k3", at_play(kr, TH["t_field"] + 0.3), PAY0 - 0.05, "cb", "Momentum carries toward first", 1560)

# ----------------------------------------------------------------- payoff
c.clip("splitB", PAY0, S["p2"], f"""<div class="seam"></div>
  <div class="half l"><div class="hd hot"><span>Waits on it</span><b>Gather, reset</b></div></div>
  <div class="half r"><div class="hd cb"><span>Works through it</span><b>Field, throw</b></div></div>
  <div class="mdl">3D model · same ball, same shortstop</div>""", cls="layer", style="z-index:11")
c.ft("#splitB .hd", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.25, ease="power3.out"), PAY0 + 0.1)
pays = [x for x in SHOTS if x.get("mode") == "split" and x["halves"] == PH]
for side, play, cls in (("L", "stand", "hot"), ("R", "through", "cb")):
    for j, x in enumerate(pays):
        vr = at_play(x, PLS[play]["t_release"])
        if vr is None: continue
        end = pays[j + 1]["a"] - 0.02 if j + 1 < len(pays) else S["p2"]
        c.clip(f"rel{side}{j}", vr, end, f'<div class="relx {cls} {side.lower()}" id="rel{side}{j}x">Release</div>', cls="layer", style="z-index:12"); pop(f"#rel{side}{j}x", vr, 12)
c.clip("endc", S["p2"], D, '<div class="hk mid endq"><span class="hl" id="eq1">Read the hop.</span><span class="hl cb" id="eq2">Work through it.</span></div>', cls="layer", style="z-index:20")
for k in range(2): c.ft(f"#eq{k + 1}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), S["p2"] + 0.1 + 0.25 * k)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for k, (w, wi, ln) in enumerate(HOOK): cue("tick", hw[wi]["t0"], -14)
for x, y in zip(SHOTS, SHOTS[1:]):
    if x["cam"] != y["cam"] or x.get("mode") != y.get("mode"): cue("whoosh", y["a"], -12)
CRACKS = []
for x in SHOTS:
    if x["speed"] == "freeze": continue
    slow = x["speed"] != "rt"; g = -5 if slow else 0
    plays = [h["play"] for h in x.get("halves", [])] or [x.get("play")]
    for pn in plays:
        pl = PLS[pn]; bn = pl["ball"]; gg = g - (3 if len(plays) > 1 else 0)
        v0 = at_play(x, 0.0)
        if v0 is not None and x["cam"] == "plate": CRACKS.append((v0, 0.9))
        for b in BLS[bn]["bounces"]:
            if b[0] < pl["t_field"] and (b[1][0] ** 2 + b[1][2] ** 2) ** 0.5 > 40: cue("tap", at_play(x, b[0]), -6 + gg)       # the ball off the dirt
        cue("glove", at_play(x, pl["t_field"]), -2 + gg)
        for s_ in pl["steps"]: cue("tap", at_play(x, s_), -9 + gg)                                                             # footwork after the field
        cue("whoosh", at_play(x, pl["t_release"] + 0.04), -4 + gg)                                                           # the throw
        cue("glove", at_play(x, pl["t_arrive"]), -3 + gg)
cue("riser-s", S["h3"], -10); cue("impact", S["h3"], -6)
for t_ in (vF, vS[0], vR, S["r1"] + 0.1): cue("popup", t_, -10)
cue("impact", S["p2"] + 0.1, -6)
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}

def crack(rng):
    """Ash bat on a ball: a hard broadband click and a short wooden ring (~1.1-2.4 kHz)."""
    t = np.arange(int(0.6 * SR)) / SR
    click = rng.standard_normal(len(t)) * np.exp(-t / 0.0025)
    ring = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d) for f, a, d in [(1150, .55, .05), (1720, .4, .035), (2380, .3, .025), (640, .3, .07)])
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.03) * 0.5
    x = click * 0.9 + ring + body
    x /= np.max(np.abs(x))
    return np.stack([x, x], 1)

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    rng = np.random.default_rng(5); cr = crack(rng)
    for vt, g in CRACKS:                                      # bat on ball
        i = int(vt * SR); j = min(n, i + len(cr)); fx[i:j] += cr[: j - i] * g
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav"))[:n]
    tt = np.arange(len(crowd)) / SR; env = np.ones_like(tt)
    for vt, g in CRACKS: env += 1.4 * np.exp(-np.clip(tt - vt, 0, None) / 1.4) * (tt > vt)    # the crowd comes up on contact
    fx[: len(crowd)] += crowd * env[:, None] * 10 ** (-28 / 20)
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo
    pre = os.path.join(HERE, ".pre.wav")
    w = wave.open(pre, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(full * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    os.remove(pre)
    return m

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
MONO = 'font-family:"Plex Mono", monospace; font-weight:500; text-transform:uppercase;'
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:640px; background:linear-gradient(180deg, rgba(3,6,12,.6), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:760px; background:linear-gradient(0deg, rgba(3,6,12,.72) 0%, rgba(3,6,12,.35) 55%, rgba(3,6,12,0) 100%); }}
.spd {{ position:absolute; left:52px; top:150px; display:inline-flex; align-items:center; gap:10px; padding:8px 16px; border-radius:8px; background:rgba(6,10,18,.72);
        {MONO} font-size:21px; letter-spacing:.14em; }}
.spd.rt {{ color:#cfd6e0; }} .spd.sl {{ color:{Y}; }}
.spd::before {{ content:""; width:10px; height:10px; border-radius:50%; background:currentColor; }}

.eyebrow {{ position:absolute; left:56px; top:232px; display:flex; align-items:center; gap:14px; {MONO} font-size:24px; letter-spacing:.2em; color:#cfd6e0; text-shadow:0 2px 10px rgba(0,0,0,.8); }}
.eyebrow i {{ width:34px; height:3px; background:{HOT}; }}
.hk {{ position:absolute; left:52px; right:40px; top:278px; display:grid; gap:2px; font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase;
       font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.75), 0 2px 4px rgba(0,0,0,.6); }}
.hk.big {{ font-size:176px; }}
.hk .hl {{ display:block; }}
.hk .acc, .hk .hl.acc {{ color:{HOT}; }}
.hk .hw {{ display:inline-block; transform-origin:0 80%; }}

.cap {{ position:absolute; left:52px; right:40px; }}
.cap .cl {{ display:block; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:88px; line-height:.96; text-transform:uppercase; color:#fff;
            text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{HOT}; }}

.cb, .cap .cw.cb, .hk .cb {{ color:{CYAN}; }} .hot, .cap .cw.hot {{ color:{HOT}; }} .yl {{ color:{Y}; }} .wh {{ color:#eef2f7; }}
.hk.sm {{ font-size:100px; }} .hk.mid {{ font-size:124px; }} .hk em {{ font-style:normal; }}
.qq {{ position:absolute; left:50px; right:50px; top:250px; padding:22px 26px; border-radius:24px; background:rgba(4,7,13,.74); font-family:"Barlow Condensed", sans-serif; font-weight:800;
       font-size:96px; line-height:.95; text-transform:uppercase; color:#fff; }}
.seam {{ position:absolute; left:539px; top:0; bottom:0; width:2px; background:rgba(255,255,255,.55); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; top:0; bottom:0; width:540px; }} .half.l {{ left:0; }} .half.r {{ left:540px; }}
.hd {{ position:absolute; left:0; right:0; top:1640px; display:grid; justify-items:center; gap:4px; text-align:center; }}
.hd span {{ {MONO} font-size:26px; letter-spacing:.14em; padding:6px 14px; border-radius:8px; background:rgba(6,10,18,.78); }}
.hd b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:88px; line-height:1; text-transform:uppercase; text-shadow:0 4px 24px rgba(0,0,0,.85); }}
.res {{ position:absolute; left:24px; right:24px; top:1440px; display:grid; gap:10px; }}
.res em {{ font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:27px; line-height:1.15; padding:10px 14px; border-radius:12px; background:rgba(6,10,18,.84); }}
.mdl {{ position:absolute; left:0; right:0; top:1390px; text-align:center; {MONO} font-size:21px; letter-spacing:.1em; color:#e8edf3; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.leg {{ position:absolute; left:40px; top:470px; display:grid; gap:8px; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.72); {MONO} font-size:21px; letter-spacing:.06em; }}
.leg.low {{ top:1500px; right:40px; }}
.leg span {{ display:flex; align-items:center; gap:12px; }}
.leg i {{ width:40px; height:6px; border-radius:3px; background:currentColor; flex:none; }}
.leg .dash i {{ background:repeating-linear-gradient(90deg, currentColor 0 9px, transparent 9px 16px); }}
.tg {{ position:absolute; left:50%; transform:translateX(-50%); max-width:1000px; padding:10px 20px; border-radius:12px; background:rgba(6,10,18,.84); white-space:nowrap;
       font-family:"Inter", sans-serif; font-weight:800; font-size:31px; }}
.tg.hot {{ color:{HOT}; }}
.chipb {{ position:absolute; left:50px; right:50px; top:450px; display:grid; gap:6px; padding:18px 24px; border-radius:18px; background:rgba(6,10,18,.84); border-left:6px solid {HOT}; }}
.chipb b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:62px; line-height:1; text-transform:uppercase; color:#fff; }}
.chipb span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:29px; line-height:1.3; color:#dfe5ec; }}
.rma {{ position:absolute; left:52px; top:560px; display:grid; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:150px; line-height:.92; text-transform:uppercase; color:#fff;
        text-shadow:0 6px 30px rgba(0,0,0,.8); }}
.rma .acc {{ color:{HOT}; }}
.stk {{ display:inline-grid; }} .stk i {{ grid-area:1 / 1; font-style:normal; opacity:0; color:#fff; }}
.relx {{ position:absolute; top:1500px; padding:8px 18px; border-radius:10px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:56px; text-transform:uppercase;
         background:rgba(6,10,18,.84); }}
.relx.l {{ left:150px; }} .relx.r {{ left:690px; }}
.endq {{ top:560px; font-size:140px; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "Work through the ball", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(CAPS)} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
