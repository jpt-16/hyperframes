"""'The complete catcher': six skills, one position (1080x1920, voiceover + effects).

    python3 tools/physics.py                                       # pitches, the ball in the dirt, the steal, the gap double -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/complete-catcher.mp4 --video-bitrate 16M

No statistics or times are shown. Shots, captions and reveals are keyed to the words of the voiceover.
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

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
PI_, ST, DB, RN = P["pitches"], P["steal"], P["double"], P["runner"]
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def hold(a, b, cam, t0, speed="none", **kw): shot(a, b, cam, [a, b], [t0, t0], speed, **kw)
CALL0, FRAME0, BLOCK0, THROW0, HIT0, RUN0, END0 = (LN(k)["t0"] - 0.06 for k in ["call", "frame", "block", "throw", "hit", "run", "end"])
FLASH = []                                                    # cut points that get a white flash
# hook: the catcher, and quick flashes of what he does
HK = [(0.0, 0.42, "hero", "slider", -2.0, 0), (0.42, 0.72, "plate", "slider", -0.25, 1), (0.72, 1.02, "dirt", "block", -0.15, 1),
      (1.02, 1.32, "steal", "steal", 0.62, 1), (1.32, 1.62, "bat", "hit", -0.12, 1)]
for a, b, cam, play, t0, r in HK:
    rate(a, b, cam, t0, r, "none", play=play); FLASH.append(a)
rate(1.62, CALL0, "hero", -1.8, 0.3, "none", play="slider"); FLASH.append(1.62)
# 1 pitch calling: the sign; the chase; the plan for the next pitch
S = dict(c1=W("call", "he") - 0.15)
rate(CALL0, S["c1"], "sign", -3.4, 1, "none", play="sign")
S["cC"] = W("call", "breaking") - 0.05                         # the slider reaches the glove (and the swing goes by it) on "breaking ball"
S["c2"] = S["cC"] + 0.55
rate(S["c1"], S["c2"], "plate", S["c1"] - S["cC"], 1, "rt", play="slider")
S["c3"] = W("call", "count") - 0.3
rate(S["c2"], S["c3"], "mound", -3.0, 0.5, "none", play="sign", nodAt=-2.3)
rate(S["c3"], FRAME0, "zone", -2.0, 0.15, "none", play="slider", show={"zone": 1, "chase": 1, "marks": ["slider"], "target": 1, "slider": 1})
# 2 framing: the pitch, a half-speed replay at the glove, the zone and the call
S["fC"] = W("frame", "it") + 0.25
S["f1"] = S["fC"] + 0.6
rate(FRAME0, S["f1"], "plate", FRAME0 - S["fC"], 1, "rt", play="frame", strike=True)
S["f2"] = W("frame", "with") - 0.1
rate(S["f1"], S["f2"], "glove", -0.4, 0.5, "replay", play="frame", strike=True)
rate(S["f2"], BLOCK0, "zone", 0.3, 0.3, "none", play="frame", strike=True, show={"zone": 1, "marks": ["fastball"]})
# 3 blocking: in the dirt; drop and smother (replay from the side); the runner stays at first
S["bC"] = W("block", "can't") + 0.25
S["b1"] = S["bC"] + 0.45
rate(BLOCK0, S["b1"], "dirt", BLOCK0 - S["bC"], 1, "rt", play="block")
S["b2"] = S["b1"] + 2.0
rate(S["b1"], S["b2"], "side", -0.45, 0.5, "replay", play="block")
rate(S["b2"], THROW0, "first", 0.55, 1, "rt", play="block")
# 4 throwing: the runner goes; half speed through the catch, exchange and footwork; real time for the release; the tag at second
S["tR"] = W("throw", "release") + 0.05                          # release on "fast release"
S["tS"] = W("throw", "exchange") - 0.6                          # slow motion from just before the catch
TC_ = -0.42
S["t2"] = S["tS"]
# play time at tS so that half speed from tS reaches the release (t_release) at tR
t_at_tS = ST["t_release"] - (S["tR"] - S["tS"]) * 0.5
rate(THROW0, S["tS"], "steal", t_at_tS - (S["tS"] - THROW0), 1, "rt", play="steal")
rate(S["tS"], S["tR"] + 0.35, "steal", t_at_tS, 0.5, "slow2", play="steal")
S["t3"] = S["tR"] + 0.35
t3 = ST["t_release"] + 0.35 * 0.5
rate(S["t3"], HIT0, "tag", t3, 1, "rt", play="steal", show={"throwPath": 1})
# 5 hitting: the catcher at the plate, into the gap
S["hC"] = W("hit", "plate") - 0.05
S["h2"] = W("hit", "driving") - 0.25
rate(HIT0, S["h2"], "bat", HIT0 - S["hC"], 1, "rt", play="hit")
rate(S["h2"], RUN0, "gap", S["h2"] - S["hC"], 1, "rt", play="run", show={"hitPath": 1})
# 6 speed: out of the box and around first
rate(RUN0, END0, "run", RUN0 - S["hC"], 1, "rt", play="run")
# finale: quick callbacks, then the catcher behind the plate
CB_ = [("sign", "sign", -2.0, 1, "1 · Pitch calling"), ("zone", "frame", 0.4, 0.3, "2 · Framing"), ("dirt", "block", -0.1, 1, "3 · Blocking"),
       ("steal", "steal", ST["t_release"] - 0.1, 1, "4 · Throwing"), ("bat", "hit", -0.15, 1, "5 · Hitting"), ("run", "run", 3.6, 1, "6 · Speed")]
v = END0; CBV = []
for cam, play, t0, r, lab in CB_:
    kw = {"show": {"zone": 1, "marks": ["fastball"]}} if play == "frame" else {}
    rate(v, v + 0.5, cam, t0, r, "none", play=play, **kw); FLASH.append(v); CBV.append((v, lab)); v += 0.5
rate(v, D, "hero", -2.0, 0.2, "none", play="slider"); FLASH.append(v); S["e1"] = v
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
S = {k: round(v_, 4) for k, v_ in S.items()}
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
c.clip("spdc", 0, D, '<div class="spd rt" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in FLASH[1:]:                                           # a quick white flash on each hard cut
    c.set("#flash", '{"opacity":0.85}', f); c.to("#flash", o(opacity=0, duration=0.16, ease="power2.out"), f + 0.001)

# ----------------------------------------------------------------- hook title (frame one), skill labels
c.clip("hook", 0, CALL0 - 0.02, """<div class="eyebrow"><i></i>Baseball Decoded</div>
  <div class="hk"><span class="hl">Being a catcher</span><span class="hl">is more than</span><span class="hl acc">you think.</span></div>""", cls="layer", style="z-index:12")
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), CALL0 - 0.17)
SK = [(CALL0, FRAME0, "1", "Pitch calling"), (FRAME0, BLOCK0, "2", "Framing"), (BLOCK0, THROW0, "3", "Blocking"), (THROW0, HIT0, "4", "Throwing"),
      (HIT0, RUN0, "5", "Hitting"), (RUN0, END0, "6", "Speed")]
for k, (a, b, n, name) in enumerate(SK):
    c.clip(f"sk{k}", a + 0.05, b - 0.02, f'<div class="skill" id="sk{k}x"><b>{n}</b><span>{name}</span></div>', cls="layer", style="z-index:21")
    c.ft(f"#sk{k}x", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22, ease="power3.out"), a + 0.08)

# ----------------------------------------------------------------- captions (the hook and "six skills" are on screen as titles)
CAPS = [("call", 0, 5, {3: "acc", 4: "acc", 5: "acc"}), ("call", 6, 9, {7: "acc"}), ("call", 10, 15, {12: "acc"}), ("call", 16, 21, {}), ("call", 22, 26, {24: "acc", 26: "acc"}), ("call", 27, 32, {30: "acc", 31: "acc", 32: "acc"}),
        ("frame", 0, 5, {4: "acc"}), ("frame", 6, 9, {7: "cb", 8: "cb", 9: "cb"}), ("frame", 10, 14, {13: "acc"}), ("frame", 15, 18, {18: "acc"}), ("frame", 19, 24, {21: "acc"}),
        ("frame", 25, 28, {26: "cb", 27: "cb", 28: "cb"}), ("frame", 29, 33, {33: "acc"}), ("frame", 34, 39, {}),
        ("block", 0, 2, {}), ("block", 3, 7, {7: "acc"}), ("block", 8, 10, {}), ("block", 11, 14, {12: "acc", 13: "acc"}), ("block", 15, 19, {18: "acc", 19: "acc"}), ("block", 20, 23, {}),
        ("throw", 0, 3, {}), ("throw", 4, 7, {7: "acc"}), ("throw", 8, 9, {9: "acc"}), ("throw", 10, 12, {12: "acc"}), ("throw", 13, 19, {19: "acc"}),
        ("hit", 0, 2, {1: "acc"}), ("hit", 3, 8, {7: "acc"}), ("hit", 9, 14, {14: "acc"}),
        ("run", 0, 4, {}), ("run", 5, 7, {7: "cb"}), ("run", 8, 10, {}), ("run", 11, 15, {14: "acc", 15: "acc"}), ("run", 16, 18, {}),
        ("end", 2, 8, {7: "acc", 8: "acc"}), ("end", 9, 13, {}), ("end", 14, 18, {16: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, (TM["lines"][IDX[lid] + 1]["t0"] - 0.1) if IDX[lid] + 1 < len(TM["lines"]) else D)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    top = 1360 if lid == "end" else 300
    c.clip(cid, start, end, f'<div class="cap" style="top:{top}px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), words[n]["t0"] - 0.04)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)

# ----------------------------------------------------------------- 1 pitch calling: the read and the plan
tag("cs", CALL0 + 0.3, S["c1"] - 0.05, "wh", "The sign: two fingers, slider", 1560)
tag("cc", W("call", "chase") - 0.05, S["c2"] - 0.05, "hot", "Chases the breaking ball, low and away", 1560)
PLAN = [("count", "Count", "1–2: he's protecting"), ("location", "Location", "Low and away, off the plate"), ("pitcher", "Pitcher's strength", "His slider")]
c.clip("plan", W("call", "count") - 0.1, FRAME0 - 0.05, '<div class="plan">' + "".join(f'<div class="pr" id="pl{k}"><span>{a}</span><b>{b}</b></div>' for k, (_, a, b) in enumerate(PLAN)) + "</div>", cls="layer", style="z-index:11")
for k, (w, a, b) in enumerate(PLAN): pop(f"#pl{k}", W("call", w) - 0.05, 16)
c.clip("plg", S["c3"] + 0.2, FRAME0 - 0.05, '<div class="leg"><span class="hot"><i></i>Where he chases</span><span class="cb"><i></i>The target</span></div>', cls="layer", style="z-index:11")

# ----------------------------------------------------------------- 2 framing
tag("fb", W("frame", "borderline") - 0.05, S["f2"] - 0.05, "cb", "Borderline: the bottom edge · a quiet glove, held there", 1560)
c.clip("abs", W("frame", "with") - 0.05, BLOCK0 - 0.05, """<div class="abs" id="absx"><div class="ar"><b>Umpire's call</b><span>Receiving can influence borderline pitches</span></div>
  <div class="ar" id="ab2"><b class="cb">ABS</b><span>The call can be challenged, or made by the system</span></div></div>""", cls="layer", style="z-index:12")
pop("#absx", W("frame", "with") - 0.05); pop("#ab2", W("frame", "challenged") - 0.05, 12)

# ----------------------------------------------------------------- 3 blocking
tag("bk", W("block", "drops") - 0.08, S["b2"] - 0.05, "cb", "Drop · square up · keep it in front", 1560)
tag("bk2", S["b2"] + 0.1, THROW0 - 0.05, "wh", "The runner stays at first", 1560)

# ----------------------------------------------------------------- 4 throwing: the steps, as they happen
ss = [x for x in SHOTS if x.get("play") == "steal" and x["a"] >= THROW0]
def v_of(t):
    for x in ss:
        r_ = at_play(x, t)
        if r_ is not None: return r_
TH = [("Exchange", 0.08), ("Footwork", 0.38), ("Release", ST["t_release"]), ("On the bag", ST["t_tag"])]
c.clip("thr", v_of(0.08) - 0.05, HIT0 - 0.05, '<div class="steps">' + "".join(f'<span id="ts{k}">{w}</span>' for k, (w, _) in enumerate(TH)) + "</div>", cls="layer", style="z-index:12")
for k, (w, t_) in enumerate(TH): c.ft(f"#ts{k}", o(opacity=0.0, y=14), o(opacity=1, y=0, duration=0.18, ease="power3.out"), v_of(t_) - 0.03)
tag("out", v_of(ST["t_tag"]) + 0.1, HIT0 - 0.05, "hot", "Tag down before he gets there", 1440)

# ----------------------------------------------------------------- 6 speed: a bonus
tag("bon", W("run", "bonus") - 0.05, END0 - 0.05, "cb", "A bonus, not a requirement", 1560)

# ----------------------------------------------------------------- finale
for k, (v_, lab) in enumerate(CBV):
    c.clip(f"cbk{k}", v_ + 0.03, v_ + 0.5, f'<div class="cbl" id="cbk{k}x">{esc(lab)}</div>', cls="layer", style="z-index:21")
c.clip("endt", END0 + 0.1, D, '<div class="endt"><span id="et1">6 skills.</span><span class="acc" id="et2">One complete catcher.</span></div>', cls="layer", style="z-index:22")
c.ft("#et1", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), W("end", "six") - 0.04)
c.ft("#et2", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), S["e1"] + 0.05)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for f in FLASH[1:]: cue("whoosh", f, -10)
CRACKS = []
for x in SHOTS:
    if x["vs"][0] == x["vs"][-1] or x["ts"][0] == x["ts"][-1]: continue
    slow = x["speed"] in ("slow2", "replay"); g = -5 if slow else 0
    pl = x.get("play")
    if pl in ("slider", "frame", "steal", "block"):
        pk = {"slider": "slider", "frame": "fastball", "steal": "steal", "block": "curve_dirt"}[pl]
        fl = PI_[pk]["flight"]
        cue("whoosh", at_play(x, -fl + 0.08), -6 + g)                                       # out of the pitcher's hand
        if pl == "block":
            b = PI_["curve_dirt"]["bounce"][0] - fl
            cue("tap", at_play(x, b), -2 + g); cue("impact", at_play(x, 0.0), -7 + g)          # off the dirt; into his chest protector
        else: cue("glove", at_play(x, 0.0), g)
        if pl == "slider": cue("whoosh", at_play(x, -0.08), -5 + g)                        # the swing that chases it
        if pl == "steal":
            cue("whoosh", at_play(x, ST["t_release"] + 0.04), -3 + g); cue("glove", at_play(x, ST["t_tag"]), -2 + g)
            cue("tap", at_play(x, ST["t_bag"] - 0.25), -6 + g)                               # the slide
    if pl == "hit":
        v0 = at_play(x, 0.0)
        if v0 is not None: CRACKS.append((v0, 0.9 if not slow else 0.5))
    if pl in ("run",) and x["cam"] == "run":
        for k in range(1, 40):                                                             # his footsteps
            t_ = k * 0.27 + 0.3
            if t_ < 7: cue("tap", at_play(x, t_), -12)
for t_ in [W("call", "count"), W("call", "location"), W("call", "pitcher"), W("frame", "with"), W("frame", "challenged")]: cue("popup", t_ - 0.05, -10)
for k, (w, t_) in enumerate(TH): cue("hit", v_of(t_) - 0.03, -10)
cue("impact", W("end", "six") - 0.04, -5); cue("impact", S["e1"] + 0.05, -4)
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
.flash {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.hk {{ font-size:118px; }}
.skill {{ position:absolute; left:40px; top:205px; display:flex; align-items:center; gap:12px; padding:6px 16px 6px 6px; border-radius:12px; background:rgba(6,10,18,.84); border:1px solid rgba(255,255,255,.12); }}
.skill b {{ display:grid; place-items:center; width:46px; height:46px; border-radius:9px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:34px; }}
.skill span {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:40px; text-transform:uppercase; letter-spacing:.02em; }}
.spd {{ left:auto; right:44px; }}
.plan {{ position:absolute; left:44px; right:44px; top:1250px; display:grid; gap:12px; }}
.pr {{ display:flex; justify-content:space-between; align-items:baseline; gap:18px; padding:14px 22px; border-radius:16px; background:rgba(6,10,18,.84); }}
.pr span {{ {MONO} font-size:22px; letter-spacing:.1em; color:{MUTED}; }}
.pr b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:48px; text-transform:uppercase; color:#fff; }}
.leg {{ position:absolute; left:44px; top:460px; display:grid; gap:8px; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.72); {MONO} font-size:22px; letter-spacing:.06em; }}
.leg span {{ display:flex; align-items:center; gap:12px; }} .leg i {{ width:22px; height:22px; border-radius:5px; background:currentColor; opacity:.8; }}
.abs {{ position:absolute; left:44px; right:44px; top:1300px; display:grid; gap:12px; }}
.ar {{ display:grid; gap:4px; padding:16px 22px; border-radius:16px; background:rgba(6,10,18,.86); }}
.ar b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:52px; line-height:1; text-transform:uppercase; color:#fff; }}
.ar span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:29px; color:#dfe5ec; line-height:1.25; }}
.steps {{ position:absolute; left:44px; right:44px; top:1560px; display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }}
.steps span {{ display:grid; place-items:center; padding:14px 6px; border-radius:12px; background:rgba(6,10,18,.86); border-bottom:5px solid {HOT}; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:36px; text-transform:uppercase; opacity:0; white-space:nowrap; }}
.cbl {{ position:absolute; left:50%; top:1600px; transform:translateX(-50%); padding:10px 24px; border-radius:12px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:56px; text-transform:uppercase; white-space:nowrap; }}
.endt {{ position:absolute; left:52px; right:40px; top:440px; display:grid; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:136px; line-height:.92; text-transform:uppercase; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.8); }}
.endt .acc {{ color:{HOT}; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "The complete catcher", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(CAPS)} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
