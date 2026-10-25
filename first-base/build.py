"""'Dive or sprint through?': a head-first dive into first base versus running through it (1080x1920, voiceover + effects).

    python3 tools/physics.py                                       # the model: two runners, the ground ball, the throw -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/dive-or-run.mp4 --video-bitrate 16M

The runners' motion and the model numbers on screen come from assets/play.json (a model, labeled as one); the study
result is quoted as measured. Shots, captions and reveals are keyed to the words of the voiceover.
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

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows (t = 0 at his first step)
T_RUN, T_DIVE, T_PLANT, T_LAND, T_STOP = P["t_run"], P["t_dive"], P["t_plant"], P["t_land"], P["t_stop"]
T_FIELD, T_REL, T_ARR = P["t_field"], P["t_release"], P["t_arrive"]
T_FIRST = min(T_RUN, T_DIVE)
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def hold(a, b, cam, t0, **kw): shot(a, b, cam, [a, b], [t0, t0], "freeze", **kw)
RACE0, SCI0, RISK0, TAKE0 = (LN(k)["t0"] - 0.06 for k in ["race", "sci", "risk", "take"])

# hook: the shortstop backhands it in the hole and throws; down the line, the runner and the ball arrive together; freeze
S = dict(h1=1.25, hRel=-1.95)
S["h2"] = S["h1"] + (3.6 - (S["h1"] - S["hRel"]))
S["hT"] = T_FIRST - 0.04                                    # freeze just before he gets there, the ball just short of the glove
S["h3"] = S["h2"] + (S["hT"] - 3.6) * 2
rate(0, S["h1"], "ss", -S["hRel"], 1, "rt")
rate(S["h1"], S["h2"], "hook", S["h1"] - S["hRel"], 1, "rt", cu=[S["h1"], RACE0])
rate(S["h2"], S["h3"], "hook", 3.6, 0.5, "slow2", cu=[S["h1"], RACE0])
hold(S["h3"], RACE0, "hook", S["hT"], cu=[S["h1"], RACE0])
# the race: split screen, identical plays; each side freezes on its own touch, then both carry on
S["r1"] = RACE0 + 0.15 + (T_RUN - 0.7)
rate(RACE0, S["r1"], "half", -0.15, 1, "rt", mode="split")
S["r2"] = S["r1"] + (max(T_RUN, T_DIVE) + 0.02 - (T_RUN - 0.7)) * 2
rate(S["r1"], S["r2"], "half", T_RUN - 0.7, 0.5, "slow2", mode="split", hold=True)
S["r3"] = S["r2"] + 1.05
hold(S["r2"], S["r3"], "half", max(T_RUN, T_DIVE) + 0.02, mode="split", hold=True)
rate(S["r3"], SCI0, "half", max(T_RUN, T_DIVE) + 0.02, 1, "rt", mode="split")
# the science: from the side at 1/4 speed, the dive with the run-through as a ghost on the same clock; then wide
S["sT0"] = T_RUN - 1.0
S["s2"] = SCI0 + 1.4 * 4
rate(SCI0, S["s2"], "side", S["sT0"], 0.25, "slow4", who="both")
rate(S["s2"], RISK0, "wide1", T_RUN + 0.4, 0.5, "slow2", who="both")
# why it can backfire: low at the bag, hands first; then the throw gets away while he is on the ground
S["k2"] = W("risk", "if") - 0.16
rate(RISK0, S["k2"], "low", T_DIVE - 0.32, 1 / 6, "slow6", who="dive")
S["k2T"] = T_ARR - 0.15
rate(S["k2"], TAKE0, "wide1", S["k2T"], 1, "rt", who="dive", ball="away")
# the takeaway: a bang-bang run-through, safe; then he eases up in foul ground
S["tRel"] = W("take", "sprinting") + 0.15 - T_RUN           # his foot hits the bag on "sprinting through"
S["t2"] = W("take", "save") - 0.15
rate(TAKE0, S["t2"], "take", TAKE0 - S["tRel"], 1, "rt", who="run", call=True)
rate(S["t2"], D, "end", S["t2"] - S["tRel"], 0.8, "rt", who="run", call=True)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
S = {k: round(v, 4) for k, v in S.items()}
S["list"] = SHOTS

def at_play(sh, t):                                         # the video time a shot shows play time t (None if it doesn't)
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]):
            return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
def shot_at(v): return next(x for x in SHOTS if v < x["b"])
def video_t(t, a, b):                                       # first video time in [a, b) that shows play time t
    for x in SHOTS:
        if x["b"] <= a or x["a"] >= b: continue
        v = at_play(x, t)
        if v is not None and a <= v < b: return v
    return None

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0.45, D, '<div class="spd rt" id="spd">Real time</div>', cls="layer", style="z-index:30")

# ----------------------------------------------------------------- hook: a statement on frame one, then the question word by word
c.clip("hook0", 0, 0.44, """<div class="eyebrow"><i></i>Bang-bang at first</div>
  <div class="hk big"><span class="hl"><em class="dv">Dive</em> or</span><span class="hl rn">sprint through?</span></div>""", cls="layer", style="z-index:12")
c.to(".hk.big", o(opacity=0, y=-30, filter="blur(10px)", duration=0.12, ease="power2.in"), 0.3)
hw = LN("hook")["words"]                                    # in a bang-bang play at first, is diving actually faster?
HOOK = [("In", 0, 0), ("a", 1, 0), ("bang-bang", 2, 0), ("play", 3, 1), ("at", 4, 1), ("first,", 5, 1), ("is", 6, 2), ("diving", 7, 2), ("actually", 8, 3), ("faster?", 9, 3)]
lines = {}
for k, (w, wi, ln) in enumerate(HOOK):
    cls = " dv" if w == "diving" else (" acc" if ln == 3 else "")
    lines.setdefault(ln, []).append(f'<span class="hw{cls}" id="hw{k}">{esc(w)}</span>')
c.clip("hook", 0.44, RACE0 - 0.02, '<div class="eyebrow"><i></i>Bang-bang at first</div><div class="hk">' + "".join(f'<span class="hl">{" ".join(v)}</span>' for v in lines.values()) + "</div>", cls="layer", style="z-index:12")
for k, (w, wi, ln) in enumerate(HOOK):
    c.ft(f"#hw{k}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), hw[wi]["t0"] - 0.04)
c.ft("#hw9", o(scale=1), o(scale=1.1, duration=0.1, yoyo=True, repeat=1), hw[9]["t0"] + 0.1)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), RACE0 - 0.18)
c.clip("q", S["h3"], RACE0 - 0.02, '<div class="qq" id="qq"><span class="dv">Dive</span> <i>or</i> <span class="rn">sprint through?</span></div>', cls="layer", style="z-index:13")
c.ft("#qq", o(opacity=0, scale=1.18, filter="blur(12px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), S["h3"])

# ----------------------------------------------------------------- captions: key phrases of the voiceover, word by word
CAPS = [("race", 0, 2, {0: "dv"}), ("race", 3, 4, {3: "dv", 4: "dv"}), ("race", 5, 7, {}), ("race", 8, 9, {}), ("race", 10, 13, {}), ("race", 14, 16, {16: "acc"}),
        ("race", 17, 20, {17: "rn", 18: "rn"}), ("race", 21, 24, {}), ("race", 25, 27, {26: "rn", 27: "rn"}),
        ("sci", 0, 3, {2: "acc"}),
        ("risk", 0, 3, {}), ("risk", 4, 5, {4: "acc", 5: "acc"}), ("risk", 6, 9, {}), ("risk", 10, 13, {10: "acc", 11: "acc"}), ("risk", 14, 16, {}), ("risk", 17, 21, {}),
        ("take", 0, 3, {}), ("take", 4, 7, {}), ("take", 8, 9, {8: "rn", 9: "rn"}), ("take", 10, 12, {}), ("take", 13, 14, {14: "dv"}), ("take", 15, 17, {}), ("take", 18, 23, {23: "acc"}), ("take", 24, 28, {25: "acc"})]
CAP_END = {("sci", 0): W("sci", "fastest") - 0.12}
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, (TM["lines"][IDX[lid] + 1]["t0"] - 0.1) if IDX[lid] + 1 < len(TM["lines"]) else D)
    end = CAP_END.get((lid, i0), end)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), words[n]["t0"] - 0.04)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)

# ----------------------------------------------------------------- the race: two halves, one clock
c.clip("split", RACE0, SCI0, f"""<div class="seam"></div>
  <div class="half l"><div class="hd dv" id="hdL"><span>Dive</span><b id="tmL">0.0 s</b><em>Hand on the bag</em></div></div>
  <div class="half r"><div class="hd rn" id="hdR"><span>Run through</span><b id="tmR">0.0 s</b><em>Foot on the bag</em></div></div>
  <div class="same" id="same">Same start · same sprint · same throw</div>""", cls="layer", style="z-index:11")
c.ft("#hdL, #hdR", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.25, ease="power3.out"), RACE0 + 0.05)
c.ft("#same", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.25), RACE0 + 0.2)
c.to("#same", o(opacity=0, duration=0.2), S["r1"] - 0.2)
c.clip("tie", S["r2"] + 0.1, S["r3"] + 0.25, f"""<div class="tie" id="tie"><b>Too close to call</b><span>3D model · both ≈ {T_RUN:.1f} s · not measured</span></div>""", cls="layer", style="z-index:12")
pop("#tie", S["r2"] + 0.12)

# ----------------------------------------------------------------- the science: momentum, the transition, the reach, then the study
c.clip("meters", SCI0 + 0.1, S["s2"], """<div class="meters" id="mtr"><div class="mh">Speed · 3D model</div>
  <div class="mv dv" id="mvD"><span>Dive</span><i></i><b>0</b><em>ft/s</em></div>
  <div class="mv rn" id="mvR"><span>Run through</span><i></i><b>0</b><em>ft/s</em></div></div>""", cls="layer", style="z-index:11")
pop("#mtr", SCI0 + 0.15)
def tag(tid, t0, t1, cls, text, top):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
vs_ = lambda t: at_play(SHOTS[[x["cam"] for x in SHOTS].index("side")], t)
tag("tg1", vs_(T_PLANT - P["assume"]["stride"]), vs_(T_LAND) + 0.2, "dv", "Extra step to get down: speed drops", 1180)
tag("tg2", vs_(T_LAND) - 0.25, S["s2"], "dv", f'Reach: hand ≈ {P["assume"]["reach"]:.1f} ft ahead of his hips', 1180)
tag("tg3", vs_(T_RUN), S["s2"], "rn", "Full speed through the bag", 1260)
fo = W("sci", "fastest")
c.clip("study", fo - 0.08, RISK0 - 0.05, f"""<div class="study" id="stu"><div class="sk">Biomechanics study · measured</div>
  <div class="s1" id="s1"><span class="rn">Running through:</span> fastest overall in the study</div>
  <div class="s2" id="s2"><span class="dv">Dive advantage:</span> not proven</div>
  <div class="s3" id="s3">Researchers: the risks likely outweigh any tiny gain</div>
  <div class="src">Ficklin, Dapena &amp; Brunfeldt, J. Sport Health Sci., 2016 · 9 college players</div></div>""", cls="layer", style="z-index:20")
pop("#stu", fo - 0.06); c.ft("#s2", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.25, ease="power3.out"), W("sci", "wasn't") - 0.05)
c.ft("#s3", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.25, ease="power3.out"), W("sci", "risks") - 0.05)
c.ft("#stu .src", o(opacity=0), o(opacity=1, duration=0.3), fo + 0.3)

# ----------------------------------------------------------------- why diving can backfire
tag("tg4", W("risk", "injury") - 0.05, S["k2"], "hot", "Hands and head go in first", 1320)
vgot = video_t(T_ARR + 0.25, S["k2"], TAKE0)
tag("tg5", vgot, TAKE0 - 0.02, "hot", "Throw gets away · he's still on the ground", 1320)

# ----------------------------------------------------------------- the takeaway, and the question
vtouch = W("take", "sprinting") + 0.15
c.clip("safec", vtouch + 0.28, S["t2"], '<div class="tg rn" id="safex" style="top:1320px">Safe · and still at full speed</div>', cls="layer", style="z-index:12"); pop("#safex", vtouch + 0.28, 14)
KT = W("take", "keep") - 0.05
ENDQ = LN("take")["t1"] + 0.12
c.clip("rule", KT, ENDQ, '<div class="rule" id="rule"><span class="k">At first:</span> <span class="rn">sprint through</span> when you can.</div>', cls="layer", style="z-index:13")
pop("#rule", KT)
c.clip("endq", ENDQ, D, '<div class="hk mid endq"><span class="hl" id="eq1">Would you</span><span class="hl" id="eq2"><em class="dv">dive</em> or</span><span class="hl rn" id="eq3">run through?</span></div>', cls="layer", style="z-index:20")
for k in range(3): c.ft(f"#eq{k + 1}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), ENDQ + 0.12 * k)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for k, (w, wi, ln) in enumerate(HOOK): cue("tick", hw[wi]["t0"], -13)
for x in SHOTS[1:]:
    if x["cam"] != SHOTS[SHOTS.index(x) - 1]["cam"]: cue("whoosh", x["a"], -12)
SLIDES = []
for x in SHOTS:
    if x["speed"] == "freeze": continue
    slow = x["speed"] != "rt"; g = -5 if slow else 0
    who = "both" if x.get("mode") == "split" else x.get("who", "run")
    kinds = ["dive", "run"] if who == "both" else [who]
    if x["cam"] not in ("ss",):
        for kind in kinds:                                  # footsteps
            for st in P["steps_dive" if kind == "dive" else "steps_run"]:
                if kind == "dive" and st > T_PLANT + 0.01: continue
                cue("tap", at_play(x, st), -11 + g)
        if "run" in kinds: cue("impact", at_play(x, T_RUN), -9 + g); cue("tap", at_play(x, T_RUN), -2 + g)      # foot on the bag
        if "dive" in kinds:
            vl = at_play(x, T_LAND)
            if vl is not None: SLIDES.append((vl, 1 / ((x["ts"][-1] - x["ts"][0]) / (x["vs"][-1] - x["vs"][0])), 0.8 if not slow else 0.5)); cue("impact", vl, -7 + g)
    cue("whoosh", at_play(x, T_REL + 0.05), -3 + g)           # the throw
    cue("glove", at_play(x, T_ARR), g)
    cue("glove", at_play(x, T_FIELD), -4 + g)
cue("riser-s", S["h3"], -10); cue("impact", S["h3"], -6)
cue("impact", S["r2"], -7); cue("popup", S["r2"] + 0.12, -9)
cue("popup", fo, -8); cue("popup", W("sci", "wasn't"), -9); cue("popup", W("sci", "risks"), -10)
cue("hit", W("risk", "injury"), -8); cue("hit", vgot, -8)
cue("popup", KT, -8); cue("impact", ENDQ, -6)
for k in range(3): cue("tick", ENDQ + 0.12 * k, -12)
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -2.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -4.0}

def slide_sound(rng, stretch):
    """A body sliding on infield dirt: band-passed noise with a fast attack and a decaying scrape (~0.5 s at real time)."""
    n = int(0.55 * stretch * SR); tt = np.arange(n) / SR / stretch
    x = rng.standard_normal(n)
    from numpy.fft import rfft, irfft, rfftfreq
    X = rfft(x); f = rfftfreq(n, 1 / SR); X *= np.exp(-((np.log(f + 1) - np.log(1400 / stretch ** 0.5)) ** 2) / 0.9); x = irfft(X, n)
    env = (1 - np.exp(-tt / 0.012)) * np.exp(-tt / 0.22)
    x = x * env; x /= np.max(np.abs(x)) + 1e-9
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
    rng = np.random.default_rng(7)
    for vt, stretch, g in SLIDES:                             # the dive landing and sliding on the dirt
        x = slide_sound(rng, stretch); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g * 0.5
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav"))[:n]
    fx[: len(crowd)] += crowd * 10 ** (-28 / 20)
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

.dv, .cap .cw.dv, .hk .dv {{ color:{CYAN}; }} .rn, .cap .cw.rn, .hk .rn {{ color:{HOT}; }}
.hk.mid {{ font-size:124px; }} .hk em {{ font-style:normal; }}
.qq {{ position:absolute; left:40px; right:40px; top:1520px; text-align:center; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:110px; line-height:.95; text-transform:uppercase;
       text-shadow:0 6px 30px rgba(0,0,0,.85); }}
.qq i {{ font-style:normal; color:#fff; }}

.seam {{ position:absolute; left:539px; top:0; bottom:0; width:2px; background:rgba(255,255,255,.55); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; top:0; bottom:0; width:540px; }} .half.l {{ left:0; }} .half.r {{ left:540px; }}
.hd {{ position:absolute; left:0; right:0; top:1650px; display:grid; justify-items:center; gap:2px; text-align:center; }}
.hd span {{ {MONO} font-size:30px; letter-spacing:.16em; padding:6px 14px; border-radius:8px; background:rgba(6,10,18,.78); }}
.hd b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:112px; line-height:1; color:#fff; font-variant-numeric:tabular-nums; text-shadow:0 4px 24px rgba(0,0,0,.85); }}
.hd em {{ font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:30px; color:#05080d; background:currentColor; padding:6px 14px; border-radius:8px; opacity:0; transition:none; }}
.hd.dv em {{ background:{CYAN}; }} .hd.rn em {{ background:{HOT}; }}
.hd.hit em {{ opacity:1; }} .hd.hit b {{ color:currentColor; }}
.same {{ position:absolute; left:0; right:0; top:800px; text-align:center; {MONO} font-size:26px; letter-spacing:.12em; color:#e8edf3; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.tie {{ position:absolute; left:60px; right:60px; top:760px; display:grid; justify-items:center; gap:6px; padding:18px 24px; border-radius:20px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.12); }}
.tie b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:80px; line-height:1; text-transform:uppercase; color:#fff; }}
.tie span {{ {MONO} font-size:22px; letter-spacing:.1em; color:{MUTED}; }}

.meters {{ position:absolute; left:44px; right:44px; top:1560px; display:grid; gap:12px; padding:18px 24px; border-radius:20px; background:rgba(6,10,18,.84); }}
.mh {{ {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; }}
.mv {{ display:grid; grid-template-columns:200px 1fr 70px 50px; align-items:center; gap:14px; }}
.mv span {{ {MONO} font-size:24px; letter-spacing:.08em; }}
.mv i {{ display:block; height:16px; border-radius:8px; background:currentColor; width:0; box-shadow:0 0 12px currentColor; }}
.mv b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:52px; text-align:right; color:#fff; font-variant-numeric:tabular-nums; }}
.mv em {{ font-style:normal; font-family:"Inter", sans-serif; font-weight:700; font-size:20px; color:{MUTED}; }}
.tg {{ position:absolute; left:50%; transform:translateX(-50%); max-width:960px; padding:10px 20px; border-radius:12px; background:rgba(6,10,18,.84); white-space:nowrap;
       font-family:"Inter", sans-serif; font-weight:800; font-size:32px; }}
.tg.hot {{ color:{Y}; }}
.study {{ position:absolute; left:44px; right:44px; top:250px; display:grid; gap:12px; padding:24px 28px; border-radius:22px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.1); }}
.sk {{ {MONO} font-size:22px; letter-spacing:.14em; color:{Y}; }}
.s1 {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:76px; line-height:.98; text-transform:uppercase; color:#fff; }}
.s2 {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:60px; line-height:1; text-transform:uppercase; color:#fff; }}
.s3 {{ font-family:"Inter", sans-serif; font-weight:700; font-size:30px; line-height:1.3; color:#dfe5ec; }}
.src {{ font-family:"Inter", sans-serif; font-weight:700; font-size:21px; color:{MUTED}; }}
.rule {{ position:absolute; left:40px; right:40px; top:1500px; padding:24px 26px; border-radius:24px; background:rgba(4,7,13,.72); font-family:"Barlow Condensed", sans-serif; font-weight:800;
         font-size:96px; line-height:.95; text-transform:uppercase; color:#fff; text-shadow:0 4px 20px rgba(0,0,0,.6); }}
.rule .k {{ color:{MUTED}; }}
.endq {{ top:620px; font-size:150px; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "Dive or sprint through", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(CAPS)} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
