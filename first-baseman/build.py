"""'First base is harder than it looks': the glove work and the bat (1080x1920, voiceover + effects).

    python3 tools/physics.py                                       # the home run -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav, effects only)
    npx --yes hyperframes@0.8.154 render . -o renders/first-baseman.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. Every throw is worked out in assets/field.js from
the 3D figures (the fielder's hand at release, the first baseman's glove at the catch, his right foot pinned to the bag).
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
HR = P["hr"]
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3B, S3, S4, S5, S6, S7 = (LN(k)["t0"] - 0.06 for k in ["stretch", "types", "bad", "help", "power", "both", "end"])   # scene changes, on the voiceover

# the throws' timing, as field.js works it out (release at -distance/speed; the fielder fields it EXCH earlier)
PLAYS = {"hook": ("backhand", (-41, -113), 80), "low": ("field", (36, -108), 74), "glove": ("field", (-24, -110), 82), "pull": ("field", (-52, -72), 84),
         "scoop": ("charge", (-20, -98), 76), "late": ("charge", (-20, -98), 76), "high": ("field", (-26, -112), 82), "wide": ("field", (-50, -70), 80),
         "p3b": ("backhand", (-66, -86), 82), "p2b": ("dive", (42, -114), 66), "pss": ("bare", (-12, -80), 72)}
EXCH = {"field": 0.75, "backhand": 0.85, "charge": 0.6, "bare": 0.42, "dive": 1.15}
def tr_of(k):
    kind, (x, z), mph = PLAYS[k]; return -(np.hypot(63.64 - x, -63.64 - z) - 2.0) / (mph * 1.4667 * 0.98)
def tf_of(k): return tr_of(k) - EXCH[PLAYS[k][0]]
RUNNER = {"hook": 0.07, "low": 0.35, "glove": 0.3, "pull": 0.85, "scoop": 0.12, "late": 0.12, "high": 0.3, "wide": 0.0, "p3b": 0.15, "p2b": 0.18, "pss": 0.08}

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def hold(a, b, cam, t0, speed="none", **kw): shot(a, b, cam, [a, b], [t0, t0], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r                    # the play time to start a shot at a so that play time t lands at video time v
FLASH = []
# 1 hook: the shortstop deep in the hole, the throw falling away; the first baseman at full stretch, the runner a step away; freeze on "looks"
FRZ0 = W("hook", "looks") + 0.05
H1 = 1.0
rate(0.0, H1, "fielder", tf_of("hook") - 0.2, 1, "none", play="hook")
t_h = tf_of("hook") - 0.2 + H1
rate(H1, FRZ0, "fbSide", t_h, -t_h / (FRZ0 - H1), "none", play="hook")
hold(FRZ0, S2, "fbSide", 0.0, "none", play="hook", freeze=[FRZ0, S2], show={"foot": 1})
# 2 the stretch: a throw to his glove side, caught on "throws"; the replay with the reach the stretch gains, on "keeping a foot on the bag"
A2 = W("stretch", "while") - 0.1
rate(S2, A2, "fbFront", on(W("stretch", "throws") + 0.1, 0.0, S2), 1, "rt", play="glove")
rate(A2, S3B, "gain", on(W("stretch", "foot"), 0.0, A2, 0.5), 0.5, "replay", play="glove", show={"gain": 1, "foot": 1})
#   low throws, high throws, pulled off the base; a split-second reaction up the line
B1_ = W("types", "high") - 0.1; B2_ = W("types", "balls") - 0.1; B3_ = W("types", "they") - 0.1
rate(S3B, B1_, "fbSide", on(W("types", "throws") + 0.1, 0.0, S3B), 1, "rt", play="low")
rate(B1_, B2_, "fbFront", on(W("types", "throws", nth=1) + 0.1, 0.0, B1_), 1, "rt", play="high")
rate(B2_, B3_, "fbWide", on(W("types", "base") + 0.1, 0.0, B2_), 1, "rt", play="wide")
rate(B3_, S3, "fbLine", on(W("types", "second") + 0.05, 0.0, B3_), 1, "rt", play="pull")
# 3 bad throws: the shortstop's play; the throw isn't perfect: the first baseman who stays tall (an error); the one who scoops it (an out)
C1 = W("bad", "but") - 0.1; C2 = W("bad", "the", nth=1) - 0.1
rate(S3, C1, "fielder", on(W("bad", "play"), tr_of("scoop"), S3), 1, "rt", play="scoop")
rate(C1, C2, "fbIn", on(W("bad", "perfect") + 0.1, 0.0, C1), 1, "rt", play="late")
rate(C2, S4, "fbIn", on(W("bad", "out"), 0.0, C2, 0.5), 0.5, "replay", play="scoop", show={"foot": 1})
# 4 they help the whole infield: three tough plays, three clean picks, a fielder who knows it
SEG = [("p3b", "fbSide", 0.75, 0.8), ("p2b", "fbFront", 0.75, 0.8), ("pss", "fbIn", 0.7, 0.7)]
v = S4; FP = []
for k, (play, cb, f1, f2) in enumerate(SEG):
    tr = tr_of(play)
    rate(v, v + f1, "fielder", tr - f1 + 0.15, 1, "rt", play=play); FLASH.append(v); FP.append(v)
    end = v + f1 + f2 if k < 2 else v + f1 + f2
    rate(v + f1, end, cb, -f2 + 0.25, 1, "rt", play=play)
    v = end
rate(v, S5, "fielder", 0.5, 1, "rt", play="pss")                                  # the shortstop: that's an out
# 5 the bat: the same first baseman hits; contact on "power"; the line drive heads out
TC = W("power", "power") + 0.05
rate(S5, S5 + 1.6, "bat", -(TC - 0.3 - S5), 1, "rt", play="hr")                  # in front of him: in the box, the pitcher sets
rate(S5 + 1.6, TC - 0.3, "batLow", -(TC - 0.3 - S5 - 1.6) - 0.3, 1, "rt", play="hr")   # behind him: load, stride
rate(TC - 0.3, TC + 0.35, "bat", -0.3, 1, "rt", play="hr")                         # the turn, contact on "power"
rate(TC + 0.35, S6, "track", 0.35, 1, "rt", play="hr", show={"hrPath": 1})
# 6 "save outs on defense and do damage on offense": the stretch, the scoop, the home run clearing the wall
E1 = W("both", "on") - 0.1; E2 = W("both", "and") - 0.1
rate(S6, E1, "fbSide", -0.05, 0.25, "none", play="hook"); FLASH.append(S6)
rate(E1, E2, "fbIn", -0.1, 0.3, "none", play="scoop"); FLASH.append(E1)
rate(E2, S7, "wall", 4.2, 0.5, "slow2", play="hr", show={"hrPath": 1}); FLASH.append(E2)
# end: around first base
rate(S7, D, "trot", 4.0, 1, "none", play="trot"); FLASH.append(S7)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)

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
for f in [FRZ0] + FLASH:
    c.set("#flash", '{"opacity":0.75}', f); c.to("#flash", o(opacity=0, duration=0.16, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1560):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="mdl" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12")
    c.ft(f"#{nid}x", o(opacity=0), o(opacity=1, duration=0.3), t0)
WORD_IN = lambda sel, t: c.ft(sel, o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), t - 0.04)

# ----------------------------------------------------------------- 1 the hook: the title, word by word with the voice ("First" on frame one)
HQ = [("First", "first"), ("base", "base"), ("is", "is"), ("harder", "harder"), ("than", "than"), ("it", "it"), ("looks", "looks")]
rows = [[0, 1, 2], [3, 4], [5, 6]]
html = "".join('<span class="hl">' + " ".join(f'<span class="hw{" acc" if k == 3 else ""}" id="hq{k}">{esc(HQ[k][0])}</span>' for k in r) + "</span>" for r in rows)
c.clip("hook", 0, S2 - 0.02, f'<div class="eyebrow"><i></i>Baseball Decoded</div><div class="hk" id="hkx">{html}</div>', cls="layer", style="z-index:12")
for k, (_, w) in enumerate(HQ): WORD_IN(f"#hq{k}", 0.04 if k == 0 else W("hook", w))
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S2 - 0.16)
c.clip("frzt", FRZ0 + 0.05, S2 - 0.02, '<div class="pinw" id="footw"><div class="pin" id="footx"><span>Foot on the bag</span></div></div>', cls="layer", style="z-index:12")
pop("#footx", FRZ0 + 0.08)

# ----------------------------------------------------------------- scene chips (top left)
for k, (a_, b_, name) in enumerate([(S2, S3, "The stretch can save an out"), (S3, S4, "Bad throw? Save it."), (S4, S5, "They finish the play"), (S5, S6, "And they have to hit bombs")]):
    c.clip(f"sk{k}", a_ + 0.05, b_ - 0.02, f'<div class="skill" id="sk{k}x"><b>{k + 1}</b><span>{esc(name)}</span></div>', cls="layer", style="z-index:21")
    c.ft(f"#sk{k}x", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22, ease="power3.out"), a_ + 0.08)

# ----------------------------------------------------------------- captions: the voiceover, word by word (the hook and the end card are titles instead)
CAPS = [("stretch", 0, 3, {2: "acc", 3: "acc"}), ("stretch", 4, 6, {6: "acc"}), ("stretch", 7, 10, {9: "acc"}), ("stretch", 11, 17, {14: "cb", 17: "cb"}),
        ("types", 0, 1, {0: "acc"}), ("types", 2, 3, {2: "acc"}), ("types", 4, 9, {5: "acc", 7: "acc"}), ("types", 10, 13, {13: "acc"}), ("types", 14, 17, {16: "acc", 17: "acc"}),
        ("bad", 0, 3, {}), ("bad", 4, 7, {6: "acc", 7: "acc"}), ("bad", 8, 12, {11: "acc", 12: "acc"}), ("bad", 13, 15, {}), ("bad", 16, 20, {19: "acc"}), ("bad", 21, 25, {22: "cb", 25: "acc"}),
        ("help", 0, 5, {3: "acc"}), ("help", 6, 12, {9: "acc", 10: "acc"}),
        ("power", 0, 3, {}), ("power", 4, 8, {}), ("power", 9, 12, {11: "acc", 12: "acc"}), ("power", 13, 16, {}),
        ("both", 0, 6, {3: "cb", 4: "cb"}), ("both", 7, 11, {9: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1, S7 - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",:") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): WORD_IN(f"#{cid}w{n - i0}", words[n]["t0"])

# ----------------------------------------------------------------- 2 the stretch
tag("t2", S2 + 0.3, A2 - 0.05, "wh", "Glove side: lead with the glove")
T0G = on(W("stretch", "foot"), 0.0, A2, 0.5)                   # the replay's starting play time; the line draws from t = -0.25
c.clip("gain", A2 + (-0.25 - T0G) / 0.5, S3B - 0.02, '<div class="pinw" id="gainw"><div class="pin" id="gainx"><span id="gainv">+0 ft</span></div></div>', cls="layer", style="z-index:12")
pop("#gainx", A2 + (-0.2 - T0G) / 0.5)
tag("t4", A2 + 0.15, S3B - 0.05, "cb", "Foot stays on the bag until it's in the glove")
tag("t5", S3B + 0.1, B1_ - 0.03, "wh", "Low: get down to it")
tag("t6", B1_ + 0.05, B2_ - 0.03, "wh", "High: stay on the bag, go up")
tag("t7", B2_ + 0.05, B3_ - 0.03, "yl", "Too wide: off the bag, keep it in front")
tag("t8", B3_ + 0.05, S3 - 0.05, "wh", "Pulled up the line: toe stays on the bag")

# ----------------------------------------------------------------- 3 bad throws
tag("b1", S3 + 0.3, C1 - 0.05, "wh", "Charging, throwing on the run")
tag("b2", W("bad", "perfect") - 0.05, C2 - 0.05, "hot", "Stays tall: the short hop gets by · error")
tag("b3", C2 + 0.15, S4 - 0.05, "cb", "Reads the hop · glove out front · scoops it")
c.clip("outc", W("bad", "out") - 0.05, S4 - 0.02, '<div class="cbl" id="outx" style="top:1400px">Out</div>', cls="layer", style="z-index:21"); pop("#outx", W("bad", "out") - 0.05, 18)
note("n5", C2 + 0.4, S4 - 0.05, "Not every bad throw can be caught", 1700)

# ----------------------------------------------------------------- 4 they help the whole infield
for k, (a, lab) in enumerate(zip(FP, ["Anticipation", "Soft hands", "Footwork"])):
    b_ = FP[k + 1] if k + 1 < len(FP) else S5
    c.clip(f"fp{k}", a + 0.05, b_ - 0.03, f'<div class="cbl" id="fp{k}x">{esc(lab)}</div>', cls="layer", style="z-index:21")
    pop(f"#fp{k}x", a + 0.08, 18)

# ----------------------------------------------------------------- 5 the bat
tag("h1", TC + 0.4, S6 - 0.05, "yl", f"{HR['ev']} mph off the bat · over the wall", 1560)

# ----------------------------------------------------------------- end
c.clip("endt", S7, D, '<div class="endt"><span id="et1">Defense saves outs.</span><span class="acc" id="et2">Bats win games.</span></div>', cls="layer", style="z-index:22")
c.ft("#et1", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), S7 + 0.05)
c.ft("#et2", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), W("end", "complete") - 0.04)

# ----------------------------------------------------------------- sound (effects only; the voiceover is added later)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for t_ in [S2, S3B, S3, S4, S5, S6, S7]: cue("whoosh", t_, -8)
for t_ in FLASH: cue("whoosh", t_, -11)
BOUNCE = {"scoop", "late", "pss"}
CRACKS = []
for x in SHOTS:
    pl = x.get("play"); slow = x["speed"] in ("slow2", "replay"); g = -5 if slow else 0
    if pl in PLAYS:
        cue("whoosh", at_play(x, tr_of(pl) + 0.03), -7 + g)                            # the throw
        if pl in BOUNCE: cue("tap", at_play(x, -0.05), -2 + g)                         # the short hop off the dirt
        if pl == "late": cue("tap", at_play(x, 0.32), -6); cue("tap", at_play(x, 0.62), -9)
        else: cue("glove", at_play(x, 0.0), g)
        cue("tap", at_play(x, RUNNER[pl]), -9 + g)                                     # the runner's foot on the bag
        cue("glove", at_play(x, tf_of(pl)), -8 + g)                                    # the fielder's glove
    if pl == "hr" and x["cam"] in ("bat", "batLow"):
        v0 = at_play(x, 0.0)
        if v0 is not None: CRACKS.append((v0, 0.9 if not slow else 0.5)); cue("glove", at_play(x, -0.45 + 0.43), -30)
    if pl == "trot":
        for k in range(8): cue("tap", at_play(x, 4.1 + k * 0.3), -16)
cue("tick", FRZ0, -1); cue("impact", FRZ0, -6)
cue("riser-m", S7 + 0.05, -4); cue("impact", S7 + 0.05, -3); cue("impact", W("end", "complete") - 0.04, -5)
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
    for vt, g in CRACKS:
        i = int(vt * SR); j = min(n, i + len(cr)); fx[i:j] += cr[: j - i] * g
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    tt = np.arange(n) / SR; env = np.ones(n)
    for vt, g in CRACKS: env += 2.2 * np.exp(-np.clip(tt - vt, 0, None) / 2.5) * (tt > vt)          # the crowd comes up on the home run
    fx += crowd * env[:, None] * 10 ** (-28 / 20)
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, fx * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=pfx)   # the same effects at the same level, without the voice
    os.remove(pre); os.remove(pfx)
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
.leg {{ position:absolute; left:44px; top:540px; display:grid; gap:8px; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.72); {MONO} font-size:22px; letter-spacing:.06em; }}
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
CSS += f"""
.hk {{ top:300px; font-size:138px; }} .hk em {{ font-style:normal; }} .hk .hw {{ display:inline-block; }}
.st {{ position:absolute; left:52px; right:40px; top:250px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:100px; line-height:.94; text-transform:uppercase; color:#fff;
       text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.st em {{ font-style:normal; color:{HOT}; }}
.mdl {{ font-size:23px; left:50%; right:auto; transform:translateX(-50%); white-space:nowrap; padding:8px 16px; border-radius:10px; background:rgba(6,10,18,.8); }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:30px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:46px; text-transform:uppercase; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
#footx span {{ background:{CYAN}; font-size:38px; }}
.cbl {{ top:1580px; }}
.tg {{ max-width:1020px; white-space:normal; text-align:center; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}}
    h = c.page(CSS, "First base is harder than it looks", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {len(CAPS)} caption phrases; {m['lufs']} LUFS / {m['true_peak']} dBTP")
