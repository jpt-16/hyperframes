"""'The hit-and-run': why the runner is already running (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the pitch, the ground balls, the fielders -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/hit-and-run.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. The play as shown: a runner on first, a
right-handed batter. The runner breaks with the pitcher's first move; the batter's job is to swing and make contact.
With a right-handed hitter the second baseman covers second on the break, which opens a hole on the right side.
Contact: a ground ball through the hole, and the runner goes first to third. A ground ball to short: the runner is
already at second, so there's no force there, only the out at first. A miss: the catcher throws to second and the
runner is tagged out sliding in.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
FBP, GB, DPP = P["pitches"]["fb"], P["gb"], P["dp"]
FL, TC = FBP["flight"], FBP["t_contact"]
T_MOVE = -1.3 - FL; T_BRK = T_MOVE + 0.15                       # mirrors assets/field.js
T_CREL, T_CAT = 0.72, 0.72 + 1.1; T_TAG = T_CAT + 0.18; T_OUT = T_CAT + 0.6
T_SSF = TC + DPP["t_field"]; T_SSREL = T_SSF + 0.6; T_SSC = T_SSREL + 1.0
T_SAFE3 = 5.55; T_THROUGH = TC + 1.27
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S4, S5, S6, S7, S8, S9, S10 = (LN(k)["t0"] - 0.06 for k in ["setup", "catch", "why", "cover", "gap", "dp", "miss", "end", "name"])

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
# hook: the runner is already going; the batter swings at the incoming pitch; freeze just before contact
H2, FRZ0 = 1.15, 2.0
rate(0.0, H2, "cfHigh", T_BRK - 0.3, play="hit", rings=["r"])
shot(H2, S2, "batSide", [H2, FRZ0, S2], [-0.06 - (FRZ0 - H2), -0.06, -0.06], play="hit", zt=-0.2, freeze=FRZ0)
# "With a runner on first, the runner takes off as soon as the pitcher delivers the ball"
E2 = W("setup", "the", nth=0) - 0.06
rate(S2, E2, "wideHigh", -3.6, play="hit", rings=["r"])
E3 = 5.85
rate(E2, E3, "runner", on(W("setup", "takes") + 0.1, T_BRK, E2), play="hit", arR=[T_BRK, T_BRK + 0.7])
# "But here's the catch: the hitter is expected to swing and make contact" (behind the pitcher, then the swing at ½ speed)
E4 = W("catch", "the", nth=1) - 0.06
rate(E3, E4, "mound", -1.75, play="hit")
rate(E4, S4, "batSide", on(W("catch", "contact"), TC, E4, 0.4), 0.4, "slow", play="hit")
VCT = W("catch", "contact")
# "Why?" ... "the second baseman or shortstop has to cover second base, opening up a hole" ... "through that gap" (from above, slow)
OR = (T_THROUGH - TC) / (W("gap", "gap") - W("cover", "hole"))
rate(S4, S6 + 1.32, "overhead", on(W("cover", "hole"), TC, S4, OR), OR, "replay", play="hit", ar2=[T_BRK + 0.15, T_BRK + 1.5], gap=-0.27, trace=[TC, TC + 1.3], rings=["b2", "r"])
OV = SHOTS[-1]; V2B = W("cover", "cover"); VGAP = W("cover", "hole")
# "the runner can advance an extra base"
E6 = OV["b"]
rate(E6, S7, "third", on(S7 - 0.05, T_SAFE3, E6), play="hit", ar3=[3.0, 3.7], rings=["r"])
VSAFE = vat(SHOTS[-1], T_SAFE3)
# "It can also make a double play much harder because the runner is already moving toward second" (a ground ball to short)
rate(S7, S8, "wideDP", on(W("dp", "already") - 0.35, T_SSF + 0.25, S7), play="dp", rings=["r", "ss"])
DPS = SHOTS[-1]; VDPCT, VSSF, VSSREL, VSSC = (vat(DPS, x) for x in (TC, T_SSF, T_SSREL, T_SSC))
# "But if the hitter swings and misses, the runner could be an easy target for the catcher"
M2, M3 = W("miss", "the", nth=1) - 0.12, W("miss", "for") - 0.12
rate(S8, M2, "batSide", on(W("miss", "misses"), TC, S8), play="miss")
VMISS = W("miss", "misses")
rate(M2, M3, "throwCam", on(M2, TC + 0.5, M2), play="miss", rings=["r"])
VCREL = vat(SHOTS[-1], T_CREL)
rate(M3, S9, "tag2", on(M3, T_CAT - 0.16, M3), play="miss")
VCAT, VTAG, VOUT = (vat(SHOTS[-1], x) for x in (T_CAT, T_TAG, T_OUT))
# "One pitch can turn a smart strategy into a costly mistake." / "That's the hit-and-run." Side by side, freezing on the outcomes
VS1, VS2 = S9 + (T_SAFE3 + 0.05 - 4.2), S9 + (T_OUT + 0.1 - 1.55)
shot(S9, D, "split", [S9, D], [0, 0], mode="split", play="hit", freeze=round(max(VS1, VS2), 3),
     top=dict(play="hit", vs=[S9, VS1, D], ts=[4.2, T_SAFE3 + 0.05, T_SAFE3 + 0.05], rings=["r"]),
     bot=dict(play="miss", vs=[S9, VS2, D], ts=[1.55, T_OUT + 0.1, T_OUT + 0.1], rings=["r"]))
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [FRZ0, S2, S4, S7, S8, S9]:
    c.set("#flash", '{"opacity":0.6}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def punch(pid, t0, t1, html, top=1300, cls=""):
    c.clip(pid, t0, t1, f'<div class="pt {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def words(wid, t0, t1, parts, top=300, cls="hk"):
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, (w, _) in enumerate(ws)) + "</span>" for i, (ws, k) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (ws, _) in enumerate(parts):
        for j, (_, ts_) in enumerate(ws):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), ts_ - 0.03)
seq = lambda txt, t0, dt=0.07: [(w, t0 + dt * i) for i, w in enumerate(txt.split())]

# ----------------------------------------------------------------- titles: the hook question, "Why?", the name at the end (captions everywhere else)
words("hook", 0.0, S2 - 0.02, [(seq("Why is the runner", 0.05), ""), (seq("already running?", 0.55), "acc")], 300)
c.ft("#hookx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.06, duration=0.14, ease="power3.out"), FRZ0)
pinl("ph0", 0.3, H2 - 0.02, "Runner", "runner", "yl")
words("why", W("why", "why") - 0.03, S5 - 0.02, [([("Why?", W("why", "why"))], "acc")], 300, "hk big")

# ----------------------------------------------------------------- captions: the voiceover, word by word
CAPS = [("setup", 0, 4, {2: "acc", 4: "acc"}), ("setup", 5, 8, {7: "acc", 8: "acc"}), ("setup", 9, 16, {14: "acc"}),
        ("catch", 0, 3, {3: "acc"}), ("catch", 4, 7, {7: "acc"}), ("catch", 8, 12, {9: "acc", 12: "acc"}),
        ("cover", 0, 5, {2: "acc", 3: "acc", 5: "acc"}), ("cover", 6, 10, {8: "acc"}), ("cover", 11, 17, {14: "acc"}),
        ("gap", 0, 8, {8: "acc"}), ("gap", 9, 15, {12: "acc", 14: "acc", 15: "acc"}),
        ("dp", 0, 8, {5: "acc", 6: "acc", 8: "acc"}), ("dp", 9, 16, {13: "acc", 14: "acc"}),
        ("miss", 0, 6, {4: "acc", 6: "acc"}), ("miss", 7, 16, {12: "acc", 13: "acc", 16: "acc"}),
        ("end", 0, 6, {1: "acc", 5: "acc", 6: "acc"}), ("end", 7, 10, {9: "acc", 10: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"]; w = w.rstrip(",:") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- the play
pinl("pr1", W("setup", "runner") - 0.03, E2 - 0.02, "Runner", "runner", "yl")
pinl("pb1", W("setup", "first") - 0.03, E2 - 0.02, "Batter", "batter")
tag("tgo", W("setup", "takes") + 0.1, E3 - 0.02, "yl", "He runs <b class='wh'>with the pitch</b>")
tag("tsw", E4 + 0.05, S4 - 0.02, "wh", "His job: <b class='yl'>swing and make contact</b>")
pinl("p2b", V2B - 0.03, E6 - 0.02, "2B covers second", "b2", "")
pinl("pgap", VGAP - 0.03, E6 - 0.02, "The hole", "gap", "yl")
pinl("pr3", E6 + 0.05, S7 - 0.02, "Runner", "runner", "yl")
punch("p13", W("gap", "extra") - 0.05, S7 - 0.02, "First<br><em>to third.</em>", 1360)
tag("tns", vat(DPS, T_SSF + 0.2), S8 - 0.02, "wh", "He’s already at second: <b class='yl'>no double play</b>")
c.clip("o1", VSSC - 0.03, S8 - 0.02, '<div class="rs2 hot" id="o1x" style="top:1420px">Out at 1st only</div>', cls="layer", style="z-index:13"); pop("#o1x", VSSC - 0.03, 10)
tag("tmi", VMISS + 0.04, M2 - 0.02, "hot", "Swing and miss")
c.clip("out", VTAG + 0.15, S9 - 0.02, '<div class="stamp" id="outx">Out</div>', cls="layer", style="z-index:15")
c.ft("#outx", o(opacity=0, scale=1.8, rotation=-8), o(opacity=1, scale=1, rotation=-8, duration=0.18, ease="back.out(2)"), VTAG + 0.15)
# the comparison
c.clip("splt", S9, D, f"""<div class="seam"></div>
  <div class="half t"><span class="hlab yl" id="hl1">Contact</span></div>
  <div class="half b"><span class="hlab hot" id="hl2">Swing and miss</span></div>""", cls="layer", style="z-index:11")
pop("#hl1", S9 + 0.05, 10); pop("#hl2", S9 + 0.15, 10)
c.clip("rs1", W("end", "smart") - 0.05, D, '<div class="rs2 yl" id="rs1x" style="top:820px">1st to 3rd ✓</div>', cls="layer", style="z-index:13"); pop("#rs1x", W("end", "smart") - 0.05, 10)
c.clip("rs2", W("end", "costly") - 0.05, D, '<div class="rs2 hot" id="rs2x" style="top:1780px">Out at 2nd</div>', cls="layer", style="z-index:13"); pop("#rs2x", W("end", "costly") - 0.05, 10)
c.clip("endb", S10, D, '<div class="endq" id="endx"><span id="ew0">That’s the</span><br><em id="ew1">hit-and-run.</em></div>', cls="layer", style="z-index:22")
c.ft("#endx", o(opacity=0), o(opacity=1, duration=0.15), S10)
c.ft("#ew0", o(opacity=0, scale=1.3, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), W("name", "that's") - 0.03)
c.ft("#ew1", o(opacity=0, scale=1.3, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), W("name", "hit-and-run") - 0.03)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -10)
cue("impact", 0.0, -8); cue("riser-s", FRZ0, -4); cue("impact", FRZ0, -1); cue("tick", FRZ0, -2)
cue("impact", W("why", "why"), -3)
for sh in SHOTS[:-1]:
    v = vat(sh, -FL + 0.08)
    if v is not None and v > sh["a"] + 0.05: cue("whoosh", v, -9 if sh["speed"] == "rt" else -13)
cue("popup", V2B, -8); cue("popup", VGAP, -6); cue("impact", W("gap", "extra") - 0.05, -6)
cue("glove", VSSF, -4); cue("glove", VSSC, -2); cue("popup", VSSC, -7)
cue("glove", VMISS + 0.04, -1); cue("whoosh", VCREL, -6); cue("glove", VCAT, -2); cue("popup", VTAG, -7); cue("impact", VTAG + 0.15, -2)
cue("popup", W("end", "smart") - 0.05, -6); cue("impact", W("end", "costly") - 0.05, -5)
cue("riser-m", W("name", "that's"), -6); cue("impact", W("name", "hit-and-run") - 0.03, -2)
CRACKS = [(VCT, 0.9), (vat(OV, TC), 0.35), (VDPCT, 0.7)]
SLIDES = [(vat(SHOTS[-2], T_CAT - 0.12), 0.7, 1.0)]
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
    for vt, g, sl in SLIDES:
        x = slide(rng, 1 / sl if sl < 1 else 1.0); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g * 10 ** (-10 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-30 / 20)
    # the music bed: made for this video (lands its chord on the closing question), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, W("name", "that's"), style="drive", seed=51)
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

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The hit-and-run", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
