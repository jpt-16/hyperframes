"""'Reading fly balls': how outfielders judge fly balls, charge or retreat, and the corners vs. center (1080x1920, voiceover + effects).

    python3 tools/physics.py                                       # fly balls (drag, backspin, modest sidespin) + fielder routes -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/fly-balls.mp4 --video-bitrate 16M

The balls, routes and every number on screen come from assets/play.json (a model, labeled as one).
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
BB = P["balls"]; A_ = P["assume"]
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def hold(a, b, cam, t0, **kw): shot(a, b, cam, [a, b], [t0, t0], "freeze", **kw)
SPLIT0, POS0, SPIN0, HIT0 = (LN(k)["t0"] - 0.06 for k in ["split", "pos", "spin", "hitter"])
TC = {k: b["t_catch"] for k, b in BB.items()}
bad_v = BB["deep"]["routes"]["bad"]["v"]; HZ_ = P["hz"]
T_TURN = min(range(int(0.6 * HZ_), int(1.8 * HZ_)), key=lambda i: bad_v[i]) / HZ_        # the wrong-step fielder stops and turns around

# hook: contact, then behind the center fielder as he steps in on a ball going over his head; freeze as he turns
S = dict(hC=0.45)
rate(0, 1.0, "plate", -S["hC"], 1, "rt", ball="deep", fielders=[["CF", "bad"]])
S["h2"] = 1.0 + (0.7 - (1.0 - S["hC"]))
rate(1.0, S["h2"], "behindCF", 1.0 - S["hC"], 1, "rt", ball="deep", fielders=[["CF", "bad"]], show={"path": 1}, cu=[1.0, SPLIT0])
S["h3"] = S["h2"] + (T_TURN - 0.7) * 3
rate(S["h2"], S["h3"], "behindCF", 0.7, 1 / 3, "slow3", ball="deep", fielders=[["CF", "bad"]], show={"path": 1}, cu=[1.0, SPLIT0])
hold(S["h3"], SPLIT0, "behindCF", T_TURN, ball="deep", fielders=[["CF", "bad"]], show={"path": 1, "land": 0, "routes": ["bad"]}, cu=[1.0, SPLIT0])
# charge or retreat: split screen, a correct first step (solid) and a wrong one (ghost) on each side; each freezes at its catch
HALVES = [dict(ball="shallow", fielders=[["CF", "ok"], ["CF", "bad", 1]]), dict(ball="deep", fielders=[["CF", "ok"], ["CF", "bad", 1]])]
SH = {"path": 1, "land": 0.6, "routes": ["ok", "bad"]}
S["sRel"] = SPLIT0 + 0.3
S["s1"] = S["sRel"] + max(TC["shallow"], TC["deep"]) + 0.02
rate(SPLIT0, S["s1"], "half", -0.3, 1, "rt", mode="split", halves=HALVES, show=SH, hold=True)
hold(S["s1"], POS0, "half", max(TC["shallow"], TC["deep"]) + 0.02, mode="split", halves=HALVES, show=SH, hold=True)
# position by position
S["p1"] = W("pos", "center") - 0.2
rate(POS0, S["p1"], "aerial", -1.4, 0.3, "pre", ball="deep", show={"start": ["LF", "CF", "RF"], "tags": 1})
S["p2"] = W("pos", "corner") - 0.12
rate(S["p1"], S["p2"], "gap", TC["gap"] + 0.15 - (S["p2"] - S["p1"]), 1, "rt", ball="gap", fielders=[["CF", "ok"], ["RF", "help"]], show={"path": 1, "land": 0.6, "routes": ["ok", "help"], "start": ["CF", "RF"]})
S["p3"] = W("pos", "their") - 0.12
rate(S["p2"], S["p3"], "lfc", TC["lfline"] + 0.2 - (S["p3"] - S["p2"]), 1, "rt", ball="lfline", fielders=[["LF", "ok"]], show={"path": 1, "land": 0.6, "routes": ["ok"], "start": ["LF"]})
rate(S["p3"], SPIN0, "rfc", TC["rfslice"] + 0.25 - (SPIN0 - S["p3"]), 1, "rt", ball="rfslice", fielders=[["RF", "ok"]], show={"path": 1, "land": 0.6, "routes": ["ok"], "start": ["RF"]})
# why it moves: with the ball (spin axis), then straight down: the same launch without sidespin, and where he'd end up
S["q2"] = W("spin", "you", nth=1) - 0.12
rate(SPIN0, S["q2"], "ballcam", 0.25, 0.25, "slow4", ball="rfslice", show={"spin": 1})
rate(S["q2"], HIT0, "top", TC["rfslice"] + 0.2 - (HIT0 - S["q2"]), 1, "rt", ball="rfslice", fielders=[["RF", "ok"], ["RF", "naive", 1]],
     show={"path": 1, "straight": 1, "naive": 0, "land": 0, "routes": ["ok", "naive"]})
# the hitter: a right-handed hitter, his opposite-field tendency; contact on "but once the ball's hit"; then with the right fielder to the catch
S["kC"] = W("hitter", "but") - 0.05
S["k2"] = S["kC"] + 0.45
rate(HIT0, S["k2"], "hitter", HIT0 - S["kC"], 1, "rt", ball="rfslice", fielders=[["RF", "ok"]], show={"wedge": 1, "path": 1})
S["kCatch"] = S["kC"] + TC["rfslice"]
S["r0"] = S["kCatch"] + 0.25
rate(S["k2"], S["r0"], "rftrack", S["k2"] - S["kC"], 1, "rt", ball="rfslice", fielders=[["RF", "ok"]], show={"path": 1, "land": 0.6, "routes": ["ok"], "start": ["RF"]})
S["r1"] = S["r0"] + 1.15
rate(S["r0"], S["r1"], "rftrack", 0.1, 1 / 3, "replay", ball="rfslice", fielders=[["RF", "ok"]], show={"path": 1, "routes": ["ok"], "start": ["RF"], "land": 0})
rate(S["r1"], D, "endwide", TC["rfslice"] + 0.3, 0.6, "rt", ball="rfslice", fielders=[["RF", "ok"]])
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
S = {k: round(v, 4) for k, v in S.items()}
S["list"] = SHOTS

def at_play(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]):
            return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0.45, D, '<div class="spd rt" id="spd">Real time</div>', cls="layer", style="z-index:30")

# ----------------------------------------------------------------- hook: a statement on frame one, then the line word by word
c.clip("hook0", 0, 0.44, """<div class="eyebrow"><i></i>Reading fly balls</div>
  <div class="hk big"><span class="hl">One wrong</span><span class="hl acc">step.</span></div>""", cls="layer", style="z-index:12")
c.to(".hk.big", o(opacity=0, y=-30, filter="blur(10px)", duration=0.12, ease="power2.in"), 0.3)
hw = LN("hook")["words"]
HOOK = [("The", 0, 0), ("hardest", 1, 0), ("part", 2, 0), ("of", 3, 1), ("catching", 4, 1), ("a", 5, 2), ("fly", 6, 2), ("ball", 7, 2), ("happens", 8, 2),
        ("before", 9, 3), ("you", 10, 3), ("even", 11, 3), ("start", 12, 4), ("running.", 13, 4)]
lines = {}
for k, (w, wi, ln) in enumerate(HOOK):
    lines.setdefault(ln, []).append(f'<span class="hw{" acc" if ln >= 3 else ""}" id="hw{k}">{esc(w)}</span>')
c.clip("hook", 0.44, S["h3"] - 0.02, '<div class="eyebrow"><i></i>Reading fly balls</div><div class="hk sm">' + "".join(f'<span class="hl">{" ".join(v)}</span>' for v in lines.values()) + "</div>", cls="layer", style="z-index:12")
for k, (w, wi, ln) in enumerate(HOOK):
    c.ft(f"#hw{k}", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.16, ease="power3.out"), hw[wi]["t0"] - 0.04)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S["h3"] - 0.16)
c.clip("q", S["h3"], SPLIT0 - 0.02, '<div class="qq" id="qq">One wrong step can <span class="acc">cost you the play.</span></div>', cls="layer", style="z-index:13")
c.ft("#qq", o(opacity=0, scale=1.16, filter="blur(12px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), S["h3"])
c.clip("hkm", S["h3"] + 0.1, SPLIT0 - 0.02, '<div class="tg hot" id="hkmx" style="top:1500px">Ball going over his head · he stepped in</div>', cls="layer", style="z-index:12")

# ----------------------------------------------------------------- captions
CAPS = [("split", 0, 3, {2: "cb"}), ("split", 4, 7, {7: "cb"}), ("split", 8, 11, {10: "acc"}), ("split", 12, 17, {15: "acc", 16: "acc", 17: "acc"}),
        ("split", 18, 20, {20: "acc"}), ("split", 21, 24, {23: "acc", 24: "acc"}), ("split", 25, 29, {}),
        ("pos", 0, 3, {}), ("pos", 4, 6, {6: "acc"}), ("pos", 7, 8, {7: "acc", 8: "acc"}), ("pos", 9, 11, {10: "acc", 11: "acc"}), ("pos", 12, 13, {12: "acc", 13: "acc"}),
        ("pos", 14, 17, {}), ("pos", 18, 20, {19: "acc", 20: "acc"}), ("pos", 21, 22, {}), ("pos", 23, 26, {}), ("pos", 27, 30, {27: "acc"}),
        ("spin", 0, 3, {0: "cb", 1: "cb", 3: "cb"}), ("spin", 4, 7, {}), ("spin", 8, 11, {8: "acc"}), ("spin", 12, 15, {}), ("spin", 16, 19, {19: "acc"}), ("spin", 20, 23, {}),
        ("hitter", 0, 3, {3: "acc"}), ("hitter", 4, 7, {7: "acc"}), ("hitter", 8, 12, {}), ("hitter", 13, 16, {15: "acc", 16: "acc"}), ("hitter", 17, 18, {18: "acc"})]
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
def tag(tid, t0, t1, cls, text, top):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)

# ----------------------------------------------------------------- charge or retreat
sb, db = BB["shallow"], BB["deep"]
c.clip("split", SPLIT0, POS0, f"""<div class="seam"></div>
  <div class="half l"><div class="hd cb"><span>Shallow ball</span><b>Charge</b></div>
    <div class="res" id="resL"><em class="cb">Right first step: caught</em><em class="hot">Wrong first step: {sb["short_bad"]:.0f} ft short</em></div></div>
  <div class="half r"><div class="hd hot"><span>Deep ball</span><b>Turn and run</b></div>
    <div class="res" id="resR"><em class="cb">Right first step: caught</em><em class="hot">Wrong first step: {db["short_bad"]:.0f} ft short</em></div></div>
  <div class="mdl" id="mdl">3D model · same ball, same fielder, different first step</div>""", cls="layer", style="z-index:11")
c.ft(".half .hd", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.25, ease="power3.out"), SPLIT0 + 0.1)
vL, vR = S["sRel"] + TC["shallow"], S["sRel"] + TC["deep"]
pop("#resL", vL); pop("#resR", vR); pop("#mdl", max(vL, vR) + 0.25, 10)
c.clip("leg", SPLIT0 + 1.0, vL - 0.1, '<div class="leg"><span class="yl"><i></i>Ball\'s flight · landing spot</span><span class="cb"><i></i>Right first step</span><span class="hot"><i></i>Wrong first step</span></div>', cls="layer", style="z-index:11")

# ----------------------------------------------------------------- position by position
gb, lb, rb = BB["gap"], BB["lfline"], BB["rfslice"]
tag("pz1", S["p1"] + 0.1, S["p2"] - 0.05, "cb", f'Center field · {gb["run_ft"]:.0f} ft to the gap, right fielder backing up', 1500)
tag("pz2", S["p2"] + 0.1, S["p3"] - 0.05, "cb", "Left field · hooking toward the line", 1500)
tag("pz3", S["p3"] + 0.1, SPIN0 - 0.05, "cb", "Right field · slicing toward the line", 1500)

# ----------------------------------------------------------------- why it moves
tag("sp1", SPIN0 + 0.35, S["q2"] - 0.05, "cb", "Backspin, axis tilted a little: some sidespin", 1500)
c.clip("cmp", S["q2"] + 0.1, HIT0 - 0.05, f"""<div class="leg low"><span class="wh dash"><i></i>Same launch, no sidespin: where it first looks like it's going</span>
  <span class="yl"><i></i>Actual flight: slices {rb["drift_ft"]:.0f} ft toward the line</span><span class="hot dash"><i></i>Runs to the first look: {rb["short_naive"]:.0f} ft off</span></div>""", cls="layer", style="z-index:11")
pop("#cmp .leg", S["q2"] + 0.15)
tag("sp2", S["q2"] + 0.9, HIT0 - 0.05, "wh", "Most fly balls drift only a little", 1330)

# ----------------------------------------------------------------- the hitter, then the catch, the replay, the payoff
c.clip("rhb", HIT0 + 0.2, S["k2"] + 0.1, '<div class="chipb" id="rhbx"><b>Right-handed hitter</b><span>Fly balls to the opposite field tend to slice toward the line</span></div>', cls="layer", style="z-index:12")
pop("#rhbx", HIT0 + 0.25)
RW = ["Read it.", "Move.", "Adjust."]
c.clip("rma", S["kCatch"] - 0.25, S["r1"] + 0.05, '<div class="rma">' + "".join(f'<span id="rm{k}" class="{"acc" if k == 2 else ""}">{w}</span>' for k, w in enumerate(RW)) + "</div>", cls="layer", style="z-index:20")
for k in range(3): c.ft(f"#rm{k}", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), S["kCatch"] - 0.2 + 0.28 * k)
tag("rpl", S["r0"] + 0.1, S["r1"], "cb", "The first step: toward where it's really going", 1500)
c.clip("endq", S["r1"] + 0.05, D, '<div class="hk mid endq"><span class="hl" id="eq1">What\'s the</span><span class="hl" id="eq2">hardest ball</span><span class="hl acc" id="eq3">to judge?</span></div>', cls="layer", style="z-index:20")
for k in range(3): c.ft(f"#eq{k + 1}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), S["r1"] + 0.1 + 0.12 * k)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for k, (w, wi, ln) in enumerate(HOOK): cue("tick", hw[wi]["t0"], -14)
for x, y in zip(SHOTS, SHOTS[1:]):
    if x["cam"] != y["cam"]: cue("whoosh", y["a"], -12)
CRACKS = []
for x in SHOTS:
    if x["speed"] == "freeze": continue
    slow = x["speed"] not in ("rt", "pre"); g = -5 if slow else 0
    v0 = at_play(x, 0.0)
    if v0 is not None and x["cam"] in ("plate", "hitter"): CRACKS.append((v0, 0.9))
    balls = [h["ball"] for h in x.get("halves", [])] or [x.get("ball")]
    for bn in set(balls):
        if bn and any(f[1] == "ok" for f in (x.get("fielders") or HALVES[0]["fielders"])):
            cue("glove", at_play(x, TC[bn]), g)
cue("riser-s", S["h3"], -10); cue("impact", S["h3"], -6)
cue("popup", vL, -8); cue("popup", vR, -8)
for t_ in (S["p1"] + 0.1, S["p2"] + 0.1, S["p3"] + 0.1, SPIN0 + 0.35, S["q2"] + 0.15, HIT0 + 0.25): cue("popup", t_, -11)
for k in range(3): cue("hit", S["kCatch"] - 0.2 + 0.28 * k, -9)
cue("impact", S["r1"] + 0.1, -6)
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -4.0}

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
.endq {{ top:560px; font-size:140px; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "Reading fly balls", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(CAPS)} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
