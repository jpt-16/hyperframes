"""'Five ways to balk' (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the fastball and the intentional-ball pitch -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/balk.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. A right-hander in the set with a runner on first:
1 he starts his delivery and stops; 2 hands come together and he goes with no stop at the set; 3 he throws to first
with his stride going toward home, not first; 4 the ball slips out of his hand on the rubber; 5 on a pitched
intentional walk the catcher leaves the catcher's box before the release (OBR 5.02(a): both feet in the box until
the ball leaves the pitcher's hand on an intentional walk; penalty: balk). Then the penalty: the runner is awarded
second.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
FB, IBB = P["pitches"]["fb"], P["pitches"]["ibb"]
PK_T, IBB_STEP = 0.5, -1.1                                     # mirrors assets/field.js
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
WI = lambda lid, i: LN(lid)["words"][i]["t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S = {x["id"]: x["t0"] - 0.06 for x in TM["lines"]}

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r
def vat(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
A = {k: S[k] - 0.04 for k in S}
A1, A2, A3, A4, A5, A6, A7, A8, A9, A10 = A["five"], A["one"], A["two"], A["three"], A["four"], A["five2"], A["box"], A["detail"], A["end"], D
# hook: the umpire stands and points at the pitcher; the runner is waved to second
VB0 = 0.3
rate(0.0, A1, "umpPoint", -0.9, play="adv", balk=-0.6)
rate(A1, A2, "wideHigh", -6.0, play="set", rings=["r"])
# 1: the leg starts up on "starts", stops on "stops"
V1 = W("one", "starts"); VB1 = W("one", "ball") - 0.1
rate(A2, A3, "p3b", on(V1, 0.0, A2), play="stop")
# 2: hands together on "set", and he goes, no pause
V2SET = W("two", "set"); V2REL = V2SET + 1.35
rate(A3, A4, "p3b2", on(V2SET, -1.35 - FB["flight"], A3), play="nostop")
V2CATCH = V2REL + FB["flight"]; VB2 = V2CATCH + 0.25
V2GO = V2SET + 0.45
# 3: the throw on "throws"; his step on "stepping", the line to first on "directly"
V3 = W("three", "throws"); V3STEP, V3NEED = W("three", "stepping"), W("three", "directly"); VB3 = W("three", "base") + 0.1
rate(A4, A5, "pick", on(V3, 0.0, A4), play="pick", arStep=round(V3STEP - V3, 3), arNeed=round(V3NEED - V3, 3), rings=["r"])
# 4: the ball slips out on "drops"; the rubber lights up on "touching"
V4 = W("four", "drops"); V4RUB = W("four", "touching"); VB4 = W("four", "rubber") + 0.15
rate(A5, A6, "dropLow", on(V4, 0.0, A5), play="drop", rub=round(V4RUB - V4, 3))
# 5: a pitched intentional walk. The catcher, standing, glove out wide; the box lights up
V5BOX = W("yes", "catcher")
rate(A6, A7, "ibbHigh", -6.2, play="ibb", box=round(-6.2 + (V5BOX - A6), 3))
# he steps out on "steps" (slow motion), the release lands on "releases" (freeze), then the catch
V5STEP, V5REL = W("box", "steps"), W("box", "releases") - 0.05
V5F1 = V5REL + 0.65
shot(A7, A8, "ibbBack", [A7, V5STEP, V5REL, V5F1, A8], [-1.3, IBB_STEP, -IBB["flight"], -IBB["flight"], -IBB["flight"] + (A8 - V5F1)], speed="slow", play="ibb",
     box=-1.3, boxRed=-IBB["flight"] - 0.001, foot=IBB_STEP + 0.25, freeze=round(V5REL, 3), freezeEnd=round(V5F1, 3), slowEnd=round(V5REL, 3))
IBS = SHOTS[-1]; V5CATCH = vat(IBS, 0.0) if vat(IBS, 0.0) else A8 + 1
# the penalty: runners on base (the runner lights up on "runners"); he's awarded second on "advance"
V6R, V6ADV = W("detail", "runners"), W("detail", "advance")
rate(A8, A9, "runner", on(V6ADV, 0.0, A8), play="adv", rings=["r"], arAdv=round(V6ADV - 0.25 - V6ADV, 3))
rate(A9, D, "wideHigh", 3.0, play="adv")
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [0.0, A1, A6, V5REL]:
    c.set("#flash", '{"opacity":0.55}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def words(wid, t0, t1, parts, top=300, cls="hk"):
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, (w, _) in enumerate(ws)) + "</span>" for i, (ws, k) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (ws, _) in enumerate(parts):
        for j, (_, ts_) in enumerate(ws):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.4, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.14, ease="power3.out"), ts_ - 0.03)
def stamp(sid, t0, t1, text="Balk"):
    c.clip(sid, t0, t1, f'<div class="stamp" id="{sid}x">{text}</div>', cls="layer", style="z-index:15")
    c.ft(f"#{sid}x", o(opacity=0, scale=1.8, rotation=-8), o(opacity=1, scale=1, rotation=-8, duration=0.18, ease="back.out(2)"), t0)
def card(cid, t0, t1, n, text):
    c.clip(cid, t0, t1, f'<div class="nc" id="{cid}x"><i>{n}</i><b>{text}</b></div>', cls="layer", style="z-index:13")
    c.ft(f"#{cid}x", o(opacity=0, x=-60), o(opacity=1, x=0, duration=0.24, ease="power3.out"), t0)

# ----------------------------------------------------------------- the hook stamp, the "five ways" title
stamp("st0", VB0, A1 - 0.02, "Balk!")
words("t5", WI("five", 0) - 0.03, A2 - 0.02, [([("5", WI("five", 2)), ("ways", WI("five", 4))], "acc"), ([("a", WI("five", 5)), ("balk", WI("five", 6))], ""), ([("can", WI("five", 7)), ("be", WI("five", 8)), ("called", WI("five", 9))], "")], 300)

# ----------------------------------------------------------------- captions: the voiceover, word by word
CAPS = [("hook", 0, 3, {1: "acc"}), ("hook", 4, 7, {7: "acc"}), ("hook", 8, 10, {10: "acc"}),
        ("one", 0, 1, {1: "acc"}), ("one", 2, 6, {4: "acc"}), ("one", 7, 12, {8: "acc"}),
        ("two", 0, 1, {1: "acc"}), ("two", 2, 5, {5: "acc"}), ("two", 6, 12, {11: "acc", 12: "acc"}), ("two", 13, 16, {}),
        ("three", 0, 1, {1: "acc"}), ("three", 2, 6, {6: "acc"}), ("three", 7, 12, {8: "acc", 9: "acc"}),
        ("four", 0, 1, {1: "acc"}), ("four", 2, 6, {4: "acc"}), ("four", 7, 11, {10: "acc", 11: "acc"}),
        ("five2", 0, 2, {2: "acc"}), ("five2", 3, 5, {4: "acc", 5: "acc"}), ("yes", 0, 3, {2: "acc"}), ("yes", 4, 7, {5: "acc", 7: "acc"}),
        ("box", 0, 4, {3: "acc", 4: "acc"}), ("box", 5, 7, {7: "acc"}), ("box", 8, 13, {8: "acc", 11: "acc"}), ("box", 14, 16, {16: "acc"}),
        ("detail", 0, 5, {4: "acc", 5: "acc"}), ("detail", 6, 9, {9: "acc"}), ("detail", 10, 12, {10: "acc", 12: "acc"}), ("detail", 13, 17, {15: "acc"}), ("detail", 18, 21, {19: "acc", 20: "acc", 21: "acc"}),
        ("end", 0, 3, {3: "acc"}), ("end", 4, 9, {6: "acc", 8: "acc", 9: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = D
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"]; w = w.rstrip(",:") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- the five
card("n1", WI("one", 1) - 0.03, A3 - 0.02, "1", "Starts, then stops")
pinl("p1", V1 + 0.9, A3 - 0.02, "Stops", "pitcher", "")
stamp("st1", VB1, A3 - 0.02)
card("n2", WI("two", 1) - 0.03, A4 - 0.02, "2", "No complete stop")
pinl("p2a", V2SET - 0.03, V2GO - 0.02, "Hands together", "hands", "yl")
pinl("p2b", V2GO, V2CATCH, "No pause", "hands", "")
stamp("st2", VB2, A4 - 0.02)
card("n3", WI("three", 1) - 0.03, A5 - 0.02, "3", "No step toward first")
pinl("p3a", V3STEP - 0.03, A5 - 0.02, "His step", "step", "")
pinl("p3b", V3NEED - 0.03, A5 - 0.02, "Toward first", "need", "wh")
stamp("st3", VB3, A5 - 0.02)
card("n4", WI("four", 1) - 0.03, A6 - 0.02, "4", "Drops the ball on the rubber")
pinl("p4", V4RUB - 0.03, A6 - 0.02, "Foot on the rubber", "rubber", "yl")
stamp("st4", VB4, A6 - 0.02)
card("n5", WI("five2", 2) - 0.03, A8 - 0.02, "5", "The catcher balk")
tag("t5ibb", V5BOX - 0.03, A7 - 0.02, "yl", "Pitched intentional walk: <b class='wh'>both feet in the box</b>", 1660)
pinl("p5box", V5BOX - 0.03, A7 - 0.02, "Catcher’s box", "box", "yl")
pinl("p5c", A6 + 0.3, A7 - 0.02, "Catcher", "catcher", "yl")
pinl("p5out", V5STEP + 0.3, V5REL + 0.08, "Out before the release", "catcher", "")
c.clip("rule5", V5REL, A8 - 0.02, '<div class="rec" id="rule5x">OBR 5.02(a): on an intentional walk, both feet stay in the box until the pitch is released</div>', cls="layer", style="z-index:13"); pop("#rule5x", V5REL + 0.05, 8)
stamp("st5", V5REL + 0.12, A8 - 0.02)
# the penalty
tag("trb", V6R - 0.03, A9 - 0.02, "yl", "Runners on base", 1560)
c.clip("adv", W("detail", "one", nth=1) - 0.05, A9 - 0.02, '<div class="pt ctr" id="advx" style="top:1260px">+1 base</div>', cls="layer", style="z-index:14")
c.ft("#advx", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), W("detail", "one", nth=1) - 0.05)
c.clip("empty", W("detail", "penalty") - 0.05, A9 - 0.02, '<div class="rec" id="emptyx">With the bases empty, an illegal pitch is called a ball instead</div>', cls="layer", style="z-index:13"); pop("#emptyx", W("detail", "penalty"), 8)
# recap
items = ["Starts, then stops", "No complete stop", "No step toward first", "Drops the ball on the rubber", "The catcher balk"]
c.clip("rc", A9 + 0.05, D, '<div class="rcap" id="rcx">' + "".join(f'<div class="ri" id="ri{i}"><i>{i + 1}</i><b>{t}</b></div>' for i, t in enumerate(items)) + "</div>", cls="layer", style="z-index:14")
for i in range(5): c.ft(f"#ri{i}", o(opacity=0, x=-50), o(opacity=1, x=0, duration=0.22, ease="power3.out"), A9 + 0.1 + 0.12 * i)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -10)
for t_ in [VB0, VB1, VB2, VB3, VB4, V5REL + 0.12]: cue("impact", t_, -3); cue("tick", t_, -5)
cue("impact", WI("five", 2), -6)
for t_ in [WI(k, 1) for k in ("one", "two", "three", "four")] + [WI("five2", 2)]: cue("popup", t_, -8)
cue("whoosh", V2REL, -8); cue("glove", V2CATCH, -2)
cue("whoosh", V3, -9); cue("glove", V3 + PK_T, -2); cue("popup", V3STEP, -8)
cue("popup", V4RUB, -8)
cue("popup", V5BOX, -8); cue("riser-s", V5STEP, -9); cue("glove", V5CATCH, -3)
cue("popup", V6R, -8); cue("impact", W("detail", "one", nth=1) - 0.05, -5)
for i in range(5): cue("tap", A9 + 0.1 + 0.12 * i, -10)
CRACKS = []
THUDS = [(V4 + 0.36, 0.5)]
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

def thud(rng, slow=1.0):
    """A baseball landing on infield dirt: a dull low thump and a short gritty burst."""
    t = np.arange(int(0.5 * SR)) / SR / slow
    body = np.sin(2 * np.pi * np.cumsum(120 * slow + 90 * np.exp(-t / 0.02)) / SR) * np.exp(-t / 0.06)
    grit = rng.standard_normal(len(t)) * np.exp(-t / 0.03) * 0.35
    x = body + np.convolve(grit, np.ones(12) / 12, "same")
    x /= np.max(np.abs(x)); return np.stack([x, x], 1)

def slide(rng, slow=1.0):
    """A runner sliding into the bag: a scrape of dirt that fades out."""
    t = np.arange(int(0.6 * SR * slow)) / SR / slow
    x = rng.standard_normal(len(t)); x = np.convolve(x, np.ones(18) / 18, "same") * np.exp(-((t - 0.18) / 0.16) ** 2) * 1.6
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
    rng = np.random.default_rng(5); cr = crack(rng)
    for vt, g in CRACKS:
        i = int(vt * SR); j = min(n, i + len(cr)); fx[i:j] += cr[: j - i] * g
    for vt, g in THUDS:
        x = thud(rng); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-30 / 20)
    # the music bed: made for this video (lands its chord on the closing question), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, W("end", "baseball"), style="drive", seed=71)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]; vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
    env = np.convolve(np.abs(vo).mean(1), np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
    duck = 10 ** (-7 * np.clip(env / 0.05, 0, 1) / 20)                         # up to 7 dB under the voice
    duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), "same")
    music = bed * duck[:, None] * 10 ** (-17 / 20)
    full = (fx + music) * 10 ** (-6 / 20) + vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, (fx + bed * 10 ** (-17 / 20)) * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=pfx)       # music + effects at the same level, without the voice
    os.remove(pre); os.remove(pfx)
    return m

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
MONO = 'font-family:"Plex Mono", monospace; font-weight:500; text-transform:uppercase;'
BC = 'font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase;'
CARD = "background:rgba(6,10,18,.86); border-radius:14px;"
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:700px; background:linear-gradient(180deg, rgba(3,6,12,.66), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:820px; background:linear-gradient(0deg, rgba(3,6,12,.75) 0%, rgba(3,6,12,.38) 55%, rgba(3,6,12,0) 100%); }}
.flash {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.dim {{ position:absolute; inset:0; background:rgba(4,7,12,.62); }}
.spd {{ position:absolute; right:44px; top:150px; display:inline-flex; align-items:center; gap:10px; padding:8px 16px; border-radius:8px; background:rgba(6,10,18,.72); {MONO} font-size:21px; letter-spacing:.14em; color:{Y}; opacity:0; }}
.spd::before {{ content:""; width:10px; height:10px; border-radius:50%; background:currentColor; }}

.hk {{ position:absolute; left:52px; right:40px; top:300px; display:grid; gap:2px; {BC} font-size:150px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.75), 0 2px 4px rgba(0,0,0,.6); }}
.hk .hl {{ display:block; }} .hk .acc, .hk .hl.acc {{ color:{HOT}; }} .hk .hw {{ display:inline-block; transform-origin:0 80%; }}
.hk.big {{ font-size:210px; }} .hk.qq2 {{ font-size:140px; }}
.cap {{ position:absolute; left:52px; right:40px; }}
.cap .cl {{ display:block; {BC} font-size:88px; line-height:.96; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{HOT}; }}
.yl {{ color:{Y}; }} .hot {{ color:{HOT}; }} .wh {{ color:#eef2f7; }}
.pt {{ position:absolute; left:52px; right:60px; {BC} font-size:104px; line-height:.95; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.7); }}
.pt.sm {{ font-size:84px; }} .pt em {{ font-style:normal; color:{HOT}; }}
.tg {{ position:absolute; left:52px; max-width:980px; padding:10px 20px; border-radius:12px; background:rgba(6,10,18,.86); white-space:nowrap; font-family:"Inter", sans-serif; font-weight:800; font-size:33px; }}
.tg b {{ font-weight:800; }}
.rs {{ position:absolute; left:52px; padding:10px 22px; border-radius:12px; {CARD} {BC} font-size:60px; }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:24px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; {BC} font-size:46px; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.pin.yl span {{ background:{Y}; }}

.mini {{ position:absolute; right:52px; top:560px; display:grid; justify-items:center; gap:10px; padding:20px 22px 16px; {CARD} }}
.mini .ml {{ {MONO} font-size:20px; letter-spacing:.08em; color:{MUTED}; }}
.dia {{ position:relative; }}
.dia svg {{ position:absolute; left:0; top:0; overflow:visible; }}
.dia polygon {{ fill:rgba(63,110,47,.28); stroke:rgba(244,246,248,.7); stroke-width:4; }}
.dia .bs {{ position:absolute; width:30px; height:30px; margin:-15px 0 0 -15px; background:#f4f6f8; transform:rotate(45deg); border-radius:3px; }}
.dia .bs.hp {{ width:26px; height:26px; margin:-13px 0 0 -13px; border-radius:2px 2px 50% 2px; }}
.dia .rn {{ position:absolute; width:52px; height:52px; margin:-26px 0 0 -26px; border-radius:50%; background:{HOT}; border:4px solid #05080d; box-shadow:0 0 0 3px {HOT}; display:grid; place-items:center; color:#05080d; font-size:30px; }}
.dia .rn.bt {{ background:{Y}; box-shadow:0 0 0 3px {Y}; }}
.fork {{ position:absolute; left:52px; right:52px; top:620px; display:grid; gap:16px; }}
.fork .fh {{ {MONO} font-size:24px; letter-spacing:.16em; color:{MUTED}; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.fr {{ display:flex; align-items:center; gap:20px; padding:20px 24px; {CARD} border:3px solid rgba(255,255,255,.16); transform-origin:0 50%; }}
.fr i {{ display:grid; place-items:center; width:62px; height:62px; flex:none; border-radius:12px; background:#26303f; {BC} font-style:normal; font-size:44px; }}
.fr b {{ {BC} font-size:58px; line-height:1; color:#fff; }} .fr em {{ font-style:normal; color:{HOT}; }}
#fr2 i {{ background:{HOT}; color:#05080d; }}
.gm {{ position:absolute; left:52px; right:52px; top:520px; display:grid; gap:8px; }}
.gm b {{ {BC} font-size:82px; line-height:1; color:{Y}; text-shadow:0 4px 22px rgba(0,0,0,.85); }}
.gm span {{ justify-self:start; padding:10px 18px; {CARD} font-family:"Inter", sans-serif; font-weight:800; font-size:31px; line-height:1.25; }}
.rec {{ position:absolute; left:52px; top:1820px; {MONO} font-size:21px; letter-spacing:.1em; color:#cfd6e0; padding:6px 12px; border-radius:8px; background:rgba(6,10,18,.72); }}
.bnr {{ position:absolute; left:52px; top:205px; display:flex; align-items:center; gap:12px; padding:6px 16px 6px 8px; border-radius:12px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.14); }}
.bnr b {{ padding:4px 12px; border-radius:8px; background:{HOT}; color:#05080d; {BC} font-size:36px; }} .bnr span {{ {BC} font-size:36px; }}
.tac {{ position:absolute; inset:0; background:radial-gradient(ellipse at 50% 45%, rgba(8,14,24,.82), rgba(3,6,11,.94)); }}
.sit {{ position:absolute; left:36px; top:560px; width:492px; display:grid; justify-items:center; gap:10px; padding:20px 18px 22px; {CARD} border:2px solid rgba(255,255,255,.12); }}
.sit.r {{ left:552px; }}
.sit .sk {{ justify-self:start; display:flex; align-items:center; gap:12px; {BC} font-size:44px; }}
.sit .sk i {{ display:grid; place-items:center; width:50px; height:50px; border-radius:10px; background:{Y}; color:#05080d; font-style:normal; }}
.sit.r .sk i {{ background:{HOT}; }}
.sit .so {{ {MONO} font-size:22px; letter-spacing:.12em; padding:4px 12px; border-radius:8px; background:#26303f; }}
.sit .sl2 {{ justify-self:stretch; font-family:"Inter", sans-serif; font-weight:700; font-size:25px; color:#dfe5ec; }}
.sit .sl2 b {{ font-weight:800; }}
.sit .sv {{ justify-self:stretch; margin-top:4px; padding:12px 14px; border-radius:10px; background:#141b27; {BC} font-size:38px; line-height:1; }}
.steps {{ position:absolute; left:36px; right:36px; top:1660px; display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }}
.steps span {{ display:grid; place-items:center; padding:14px 6px; border-radius:12px; background:rgba(6,10,18,.88); border-bottom:5px solid {HOT}; {BC} font-size:37px; white-space:nowrap; opacity:0; }}
"""])

CSS += f"""
.hk.mid {{ font-size:124px; }}
.pt.ctr {{ left:0; right:0; text-align:center; font-size:112px; }}
.seam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; left:0; right:0; height:960px; }} .half.t {{ top:0; }} .half.b {{ top:960px; }}
.hlab {{ position:absolute; left:40px; top:180px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:56px; }}
.half.b .hlab {{ top:28px; }}
.ch {{ position:absolute; left:52px; top:250px; display:grid; gap:4px; }}
.ch span {{ {MONO} font-size:26px; letter-spacing:.16em; color:{MUTED}; }} .ch b {{ {BC} font-size:110px; line-height:.95; color:#fff; }}
.cdia {{ position:absolute; left:0; right:0; top:620px; display:flex; justify-content:center; }}
.clst {{ position:absolute; left:52px; right:52px; top:960px; display:grid; gap:14px; }}
.ci {{ display:flex; align-items:center; gap:22px; padding:16px 22px; {CARD} border-left:6px solid {Y}; }}
.ci i {{ display:grid; place-items:center; width:58px; height:58px; flex:none; border-radius:50%; background:{Y}; color:#05080d; font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:36px; }}
.ci b {{ {BC} font-size:64px; line-height:1; color:#fff; }}
.cbl {{ position:absolute; left:52px; right:52px; top:1530px; padding:16px 22px; border-radius:14px; background:{HOT}; color:#05080d; {BC} font-size:62px; text-align:center; }}
.cbl em {{ font-style:normal; color:#fff; }}
.cfn {{ position:absolute; left:52px; right:52px; top:1680px; {MONO} font-size:24px; letter-spacing:.08em; color:#cfd6e0; text-align:center; }}
"""

CSS += f"""
.seam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; left:0; right:0; height:960px; }} .half.t {{ top:0; }} .half.b {{ top:960px; }}
.hlab {{ position:absolute; left:40px; top:120px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:60px; }}
.half.b .hlab {{ top:28px; }}
.rs2 {{ position:absolute; right:40px; padding:10px 22px; border-radius:12px; background:rgba(6,10,18,.9); {BC} font-size:62px; }}
.stamp {{ position:absolute; left:0; right:0; top:620px; text-align:center; {BC} font-size:260px; line-height:1; color:{HOT}; text-shadow:0 10px 40px rgba(0,0,0,.85); }}
.endq {{ position:absolute; left:0; right:0; top:830px; padding:26px 0 30px; background:rgba(5,8,13,.9); text-align:center; {BC} font-size:128px; line-height:.95; color:#fff; text-shadow:0 8px 34px rgba(0,0,0,.9); }}
.endq em {{ font-style:normal; color:{Y}; }}
"""

CSS += f"""
.hk.big {{ font-size:220px; }}
"""


CSS += f"""
.hk {{ font-size:140px; }}
.stamp {{ position:absolute; left:0; right:0; top:700px; text-align:center; {BC} font-size:240px; line-height:1; color:{HOT}; text-shadow:0 10px 40px rgba(0,0,0,.85); }}
.nc {{ position:absolute; left:40px; top:1500px; display:flex; align-items:center; gap:18px; padding:12px 24px 12px 12px; border-radius:16px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.14); }}
.nc i {{ display:grid; place-items:center; width:84px; height:84px; border-radius:12px; background:{Y}; color:#05080d; font-style:normal; {BC} font-size:72px; }}
.nc b {{ {BC} font-size:60px; line-height:1; color:#fff; }}
.pt.ctr {{ left:0; right:0; text-align:center; font-size:150px; color:{Y}; }}
.rcap {{ position:absolute; left:44px; right:44px; top:720px; display:grid; gap:14px; }}
.ri {{ display:flex; align-items:center; gap:20px; padding:14px 22px; {CARD} border-left:6px solid {Y}; }}
.ri i {{ display:grid; place-items:center; width:62px; height:62px; flex:none; border-radius:12px; background:{Y}; color:#05080d; font-style:normal; {BC} font-size:50px; }}
.ri b {{ {BC} font-size:60px; line-height:1; color:#fff; }}
.pin.wh span {{ background:#eef2f7; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Five ways to balk", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
