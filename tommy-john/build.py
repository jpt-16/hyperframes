"""'Tommy John surgery: back on the mound isn't back to peak' (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the pitches -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/tommy-john.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. The elbow is an illustrative anatomical model (a right
elbow seen from the inner side): the UCL's anterior bundle from the medial epicondyle to the sublime tubercle, and a
reconstruction with a tendon graft in a figure-of-eight through bone tunnels. The 28.1% is from a 2025 study of MLB
pitchers after UCL reconstruction (full performance by the study's criteria within three seasons; reported 3.9% after one);
it is not a return-to-play rate. The analytics screen is illustrative (no data); recovery commonly takes 12-18 months
and varies by pitcher.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc, R
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PI_ = P["pitches"]; FL = lambda k: PI_[k]["flight"]
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S4, S5, S6 = (LN(k)["t0"] - 0.06 for k in ["rebuild", "stat", "diff", "recovery", "end"])

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r                    # the play time to start a shot at a so that play time t lands at video time v
# 1 the hook: a hard fastball, frozen just out of his hand (zoom); later, the same pitcher misses the target badly; his reaction
REL1, FRZ0 = 0.62, 0.67
TF0 = -FL("peak") + (FRZ0 - REL1)
shot(0.0, 1.2, "hookP", [0.0, FRZ0, 1.2], [TF0 - FRZ0, TF0, TF0], play="peak", zt=TF0 - 0.14, freeze=FRZ0)
H3 = W("hook", "throw") - 0.01
rate(1.2, H3, "behind", on(W("hook", "pitchers"), 0.0, 1.2), play="miss", zone=1, target=1, mark=1)
rate(H3, S2, "frust", 0.45, play="miss", after="frust")
# 2 the surgery: into his elbow at the cocked arm; the elbow: the UCL, the pull on it in a throw, torn, the graft woven in
E2 = W("rebuild", "ligament") + 0.12
TCOCK = -FL("good") - 0.32
shot(S2, E2, "elbowIn", [S2, E2], [TCOCK, TCOCK], play="good", glow=1)
rate(E2, S3 + 0.85, "elbow", 0.0, mode="elbow", a0=0.1, a1=0.42, r0=24, r1=17)
EL0 = E2
ev = lambda te: EL0 + te                                           # video time of an elbow-clock moment
# 3 the statistic: he takes the mound again; then the number
R1 = S3 + 0.85; R2 = W("stat", "found") - 0.06
rate(R1, R2, "walkCF", 0.0, play="walk")
rate(R2, S4, "stat", -1.6, 0.02, play="good")
# 4 the difference: side by side (return to play | full performance); then the timeline; then working on command
L_PITCH = W("diff", "mound")                                       # the left pitch reaches the glove on "mound"
shot(S4, S5, "split", [S4, S5], [on(L_PITCH, 0.0, S4), on(L_PITCH, 0.0, S4) + (S5 - S4)], mode="split", play="good",
     left=dict(cam="behindP", play="good", after="comp"), right=dict(cam="zoneR", play="c1", zone=1, target=1, mark=1, after="none"))
TQ = on(L_PITCH, 0.0, S4)
MARKS_R = [["c2", 0.9], ["c3", 1.7], ["c4", 2.45]]
SHOTS[-1]["right"]["marks"] = MARKS_R
C2 = W("recovery", "pitchers") - 0.06
rate(S5, C2, "bull", -1.4, 0.6, play="good", after="comp")
rate(C2, S6, "cmd", on(W("recovery", "command"), 0.0, C2), play="c5", zone=1, target=1, mark=1, marks=[["c1", -9], ["c2", -9], ["c3", -9], ["c4", -9]])
# 5 the payoff: a composed delivery; the analytics screen; the bookend: released, frozen; the question
A5 = W("end", "but") - 0.06
REL5 = W("end", "save")
rate(S6, A5, "comp", on(REL5, -FL("good"), S6), play="good", after="comp")
QV = LN("end")["t1"] + 0.08
rate(A5, QV, "ana", -1.6, 0.02, play="good")
REL6, FRZ6 = QV + 0.25, QV + 0.3
TF6 = -FL("good") + (FRZ6 - REL6)
shot(QV, D, "hookP", [QV, FRZ6, D], [TF6 - (FRZ6 - QV), TF6, TF6], play="good", zt=TF6 - 0.14, freeze=FRZ6)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [FRZ0, 1.2, E2, R1, S4, QV]:
    c.set("#flash", '{"opacity":0.6}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def punch(pid, t0, t1, html, top=1300, cls=""):
    c.clip(pid, t0, t1, f'<div class="pt {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def pinl(pid, t0, t1, text, key, cls="", mode="field"):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, mode])
def words(wid, t0, t1, parts, top=300, cls="hk"):                # a headline that lands word by word, each on its own time
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, (w, _) in enumerate(ws)) + "</span>" for i, (ws, k) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (ws, _) in enumerate(parts):
        for j, (_, ts_) in enumerate(ws):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), ts_ - 0.03)

# ----------------------------------------------------------------- 1 the hook
words("hook", 0.0, S2 - 0.02, [([("Back", W("hook", "tommy")), ("from", W("hook", "tommy") + 0.08), ("Tommy", W("hook", "john")), ("John…", W("hook", "john") + 0.08)], ""),
                               ([("But", W("hook", "make")), ("not", W("hook", "pitchers")), ("the", W("hook", "pitchers") + 0.06), ("same?", W("hook", "pitchers") + 0.12)], "acc")], 300)
c.ft("#hookx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.06, duration=0.14, ease="power3.out"), FRZ0)
tag("tb4", 0.05, 1.18, "wh", "Before surgery", 1560)
tag("taf", 1.22, S2 - 0.02, "hot", "After surgery: <b class='wh'>way off the target</b>", 1560)

# ----------------------------------------------------------------- captions: the voiceover, word by word (the hook is the title above)
DISP = {("stat", 8): "MLB", ("stat", 9): None, ("stat", 10): None, ("stat", 15): "28%", ("stat", 16): None, ("recovery", 3): "12", ("recovery", 5): "18"}
CAPS = [("rebuild", 0, 3, {1: "acc", 3: "acc"}), ("rebuild", 4, 7, {5: "acc", 7: "acc"}), ("rebuild", 8, 10, {10: "acc"}),
        ("stat", 0, 4, {3: "acc"}), ("stat", 5, 11, {8: "acc"}), ("stat", 12, 16, {14: "acc", 15: "acc"}), ("stat", 17, 20, {19: "acc", 20: "acc"}), ("stat", 21, 25, {22: "acc", 23: "acc"}),
        ("diff", 0, 4, {4: "acc"}), ("diff", 5, 11, {10: "acc", 11: "acc"}), ("diff", 12, 16, {14: "acc", 15: "acc"}),
        ("recovery", 0, 6, {3: "acc", 5: "acc", 6: "acc"}), ("recovery", 7, 10, {}), ("recovery", 11, 15, {14: "acc"}), ("recovery", 16, 20, {18: "acc", 20: "acc"}),
        ("end", 0, 5, {3: "acc", 5: "acc"}), ("end", 6, 10, {8: "acc", 9: "acc"}), ("end", 11, 15, {13: "acc", 14: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif lid == "end": end = QV - 0.02
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    cid = f"cap{k}"; sp = []; ins = []
    for n in range(i0, i1 + 1):
        w = DISP.get((lid, n), wd[n]["w"])
        if w is None: continue
        w = w.rstrip(",:") if n == i1 or (lid, n) in DISP else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>'); ins.append((n - i0, wd[n]["t0"]))
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for j, t0 in ins: c.ft(f"#{cid}w{j}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), t0 - 0.04)

# ----------------------------------------------------------------- 2 the surgery
pinl("pel", S2 + 0.05, E2 - 0.02, "Elbow", "elbow", "yl")
pinl("pucl", E2 + 0.1, ev(0.93), "UCL · inner elbow", "ucl", "yl", "elbow")
tag("tld", ev(0.45), ev(1.22), "wh", "In a throw it holds the inner elbow together", 1500)
pinl("ptorn", ev(0.97), ev(1.3), "Torn UCL", "ucl", "", "elbow")
pinl("pgr", ev(1.35), S3 + 0.83, "Tendon graft", "graft", "yl", "elbow")
punch("prb", ev(1.3), S3 + 0.83, "Rebuild<br><em>the ligament.</em>", 1330)
tag("tgn", ev(2.0), S3 + 0.83, "wh", "Illustrative · the graft then needs months to heal", 1650)

# ----------------------------------------------------------------- 3 the statistic
tag("tret", R1 + 0.1, R2 - 0.02, "wh", "Back on the mound", 1560)
c.clip("stat", R2, S4 - 0.02, f"""<div class="dim" id="sdim"></div>
  <div class="st" id="stx"><span class="sk">Only</span><b><span id="stn">0</span>%</b>
  <span class="sl">returned to full performance within 3 seasons</span>
  <div class="bar"><i id="bfill"></i><em id="brest"></em></div>
  <div class="bl"><span class="yl" id="bl1">28.1% full performance</span><span id="bl2">71.9% not by year 3</span></div>
  <span class="src">MLB pitchers · UCL surgery study (2025)</span>
  <span class="nt" id="ntx">“Full performance” = the study’s performance benchmarks, not just pitching again</span></div>""", cls="layer", style="z-index:15")
c.ft("#sdim", o(opacity=0), o(opacity=1, duration=0.25), R2)
pop("#stx", R2 + 0.02, 14)
T28 = W("stat", "twenty-eight")
c.ft("#stn", o(innerText=0), o(innerText=28.1, duration=0.42, ease="power2.out", snap=R("{innerText:0.1}")), T28 - 0.05)
c.ft("#bfill", o(width="0%"), o(width="28.1%", duration=0.55, ease="power2.out"), T28 - 0.05)
c.ft("#brest", o(opacity=0), o(opacity=1, duration=0.3), W("stat", "full") - 0.05)
c.ft("#bl1", o(opacity=0), o(opacity=1, duration=0.2), T28 + 0.4); c.ft("#bl2", o(opacity=0), o(opacity=1, duration=0.2), W("stat", "full") - 0.05)
c.ft("#ntx", o(opacity=0), o(opacity=1, duration=0.3), W("stat", "seasons"))

# ----------------------------------------------------------------- 4 the difference
c.clip("splt", S4, S5, """<div class="seamv"></div>
  <div class="sd l" id="sdl"><b class="yl">Return to play</b><span>Back on the mound ✓</span></div>
  <div class="sd r" id="sdr"><b class="hot">Full performance?</b><span>Command · consistency</span></div>""", cls="layer", style="z-index:11")
pop("#sdl", S4 + 0.05, 12); pop("#sdr", W("diff", "getting", nth=1) - 0.05, 12)
punch("pne", W("diff", "two") - 0.05, S5 - 0.02, "Return to play<br><em>≠ full performance</em>", 1460, "ctr")
c.clip("tl", S5, C2 - 0.02, f"""<div class="dim" id="tdim"></div>
  <div class="tl" id="tlx"><span class="th">The road back</span>
   <div class="tr"><i class="dot"></i><b>Surgery</b></div>
   <div class="tr" id="tr2"><div class="seg"><i id="sgf"></i></div><b class="yl">Recovery: often 12–18 months</b></div>
   <div class="tr" id="tr3"><i class="dot hot"></i><b>Return to the mound</b></div>
   <div class="tr" id="tr4"><div class="seg dash"></div><b class="hot">Rebuilding command &amp; performance →</b></div>
   <span class="tn" id="tnx">Every pitcher’s timeline is different</span></div>""", cls="layer", style="z-index:12")
c.ft("#tdim", o(opacity=0), o(opacity=1, duration=0.25), S5)
pop("#tlx", S5 + 0.03, 14)
c.ft("#tr2", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22), W("recovery", "twelve") - 0.08)
c.ft("#sgf", o(height="0%"), o(height="100%", duration=0.7, ease="none"), W("recovery", "twelve"))
c.ft("#tr3", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22), W("recovery", "even") - 0.05)
c.ft("#tr4", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22), W("recovery", "after") + 0.05)
c.ft("#tnx", o(opacity=0), o(opacity=1, duration=0.3), W("recovery", "that"))
tag("tcm", W("recovery", "regain") - 0.05, S6 - 0.02, "hot", "Same target, five pitches: <b class='wh'>command comes back slowly</b>", 1560)

# ----------------------------------------------------------------- 5 the payoff
punch("phs", W("end", "career") - 0.05, QV - 0.02, "The comeback is<br><em>only half the story.</em>", 1460)
ROWS = [("Velocity", 0.86, W("end", "doesn't")), ("Command", 0.62, W("end", "guarantee")), ("Consistency", 0.7, W("end", "get"))]
c.clip("ana", A5, QV - 0.02, '<div class="dim" id="adim"></div><div class="an" id="anx"><span class="ah">Pitch tracking · illustrative</span>' +
       "".join(f'<div class="ar"><b>{n}</b><div class="ab"><span>Before</span><div class="bb"><i style="width:100%"></i></div></div><div class="ab"><span>After</span><div class="bb af"><i id="af{i}"></i><em>?</em></div></div></div>' for i, (n, _, _) in enumerate(ROWS)) +
       "</div>", cls="layer", style="z-index:12")
c.ft("#adim", o(opacity=0), o(opacity=1, duration=0.2), A5); pop("#anx", A5 + 0.03, 14)
for i, (_, f, t_) in enumerate(ROWS): c.ft(f"#af{i}", o(width="0%"), o(width=f"{f * 100:.0f}%", duration=0.5, ease="power2.out"), t_ - 0.05)
words("q", QV, D, [([("Would", QV + 0.02), ("you", QV + 0.08), ("risk", QV + 0.14)], ""), ([("losing", QV + 0.24), ("your", QV + 0.3)], ""), ([("best", QV + 0.4), ("stuff?", QV + 0.46)], "acc")], 300)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -10)
for v_ in [REL1, W("hook", "pitchers") - FL("miss"), L_PITCH - FL("good"), W("recovery", "command") - FL("c5"), REL5, REL6]: cue("whoosh", v_, -8)
cue("riser-s", FRZ0, -4); cue("impact", FRZ0, 0); cue("tick", FRZ0, -1)
cue("glove", W("hook", "pitchers") + 0.02, -6); cue("impact", W("hook", "pitchers"), -2)
cue("riser-s", E2, -6); cue("popup", E2 + 0.1, -7); cue("tap", ev(0.95), -3); cue("popup", ev(1.35), -6); cue("impact", ev(1.3), -8)
cue("riser-m", T28, -6); cue("impact", T28, -1)
cue("glove", L_PITCH, -2); cue("impact", W("diff", "two") - 0.05, -4)
cue("tick", W("recovery", "twelve"), -2); cue("tick", W("recovery", "even"), -2); cue("tick", W("recovery", "after"), -2)
cue("glove", W("recovery", "command"), -3); cue("glove", REL5 + FL("good"), -1); cue("impact", W("end", "career") - 0.05, -5)
for _, _, t_ in ROWS: cue("popup", t_, -8)
cue("riser-m", FRZ6, -6); cue("impact", FRZ6, -1); cue("tick", FRZ6, -2)
CRACKS = []
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
    fx += crowd * 10 ** (-30 / 20)
    # the music bed: made for this video (lands its chord on the closing question), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, QV, style="glow", seed=41)
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
.hk.qq {{ font-size:132px; }}
.dim {{ position:absolute; inset:0; background:rgba(4,7,12,.72); }}
.st {{ position:absolute; left:52px; right:52px; top:560px; display:grid; gap:14px; }}
.st .sk {{ {BC} font-size:72px; color:#fff; line-height:1; }}
.st b {{ {BC} font-size:300px; line-height:.82; color:{Y}; text-shadow:0 8px 34px rgba(0,0,0,.85); }}
.st .sl {{ {BC} font-size:62px; line-height:1; color:#fff; }}
.bar {{ position:relative; height:56px; border-radius:14px; background:#1b2432; overflow:hidden; margin-top:10px; }}
.bar i {{ position:absolute; left:0; top:0; bottom:0; width:0; background:{Y}; }}
.bar em {{ position:absolute; left:28.1%; right:0; top:0; bottom:0; background:repeating-linear-gradient(135deg, rgba(255,106,61,.55) 0 14px, rgba(255,106,61,.25) 14px 28px); }}
.bl {{ display:flex; justify-content:space-between; font-family:"Inter", sans-serif; font-weight:800; font-size:30px; }} .bl span:last-child {{ color:{HOT}; }}
.st .src {{ {MONO} font-size:24px; letter-spacing:.12em; color:#dfe5ec; margin-top:16px; }}
.st .nt {{ font-family:"Inter", sans-serif; font-weight:700; font-size:26px; line-height:1.3; color:{MUTED}; }}
.seamv {{ position:absolute; left:539px; top:0; bottom:0; width:3px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.sd {{ position:absolute; top:640px; width:540px; display:grid; justify-items:center; gap:10px; text-align:center; }} .sd.l {{ left:0; }} .sd.r {{ left:540px; }}
.sd b {{ padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:54px; }}
.sd span {{ padding:6px 14px; border-radius:10px; background:rgba(6,10,18,.88); font-family:"Inter", sans-serif; font-weight:800; font-size:28px; }}
.pt.ctr {{ left:0; right:0; text-align:center; font-size:100px; }}
.tl {{ position:absolute; left:60px; right:52px; top:560px; display:grid; gap:0; }}
.tl .th {{ {MONO} font-size:26px; letter-spacing:.16em; color:{MUTED}; margin-bottom:22px; }}
.tr {{ display:flex; align-items:center; gap:30px; min-height:96px; }}
.tr b {{ {BC} font-size:62px; line-height:1; color:#fff; }}
.tr .dot {{ width:44px; height:44px; flex:none; border-radius:50%; background:#fff; margin:0 8px; }} .tr .dot.hot {{ background:{HOT}; }}
.tr .seg {{ position:relative; width:12px; height:150px; flex:none; margin:0 24px; border-radius:6px; background:#26303f; overflow:hidden; }}
.tr .seg i {{ position:absolute; left:0; right:0; top:0; height:0; background:{Y}; }}
.tr .seg.dash {{ background:repeating-linear-gradient(180deg, {HOT} 0 16px, transparent 16px 30px); }}
.tl .tn {{ font-family:"Inter", sans-serif; font-weight:700; font-size:30px; color:{MUTED}; margin-top:24px; }}
.an {{ position:absolute; left:52px; right:52px; top:560px; display:grid; gap:22px; padding:28px 30px; {CARD} border:2px solid rgba(255,255,255,.12); }}
.an .ah {{ {MONO} font-size:24px; letter-spacing:.14em; color:{MUTED}; }}
.ar {{ display:grid; gap:8px; }} .ar > b {{ {BC} font-size:58px; color:#fff; line-height:1; }}
.ab {{ display:grid; grid-template-columns:120px 1fr; align-items:center; gap:14px; }} .ab span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:24px; color:{MUTED}; }}
.bb {{ position:relative; height:30px; border-radius:8px; background:#1b2432; overflow:hidden; }} .bb i {{ position:absolute; left:0; top:0; bottom:0; background:#dfe5ec; }}
.bb.af i {{ width:0; background:{HOT}; }} .bb em {{ position:absolute; right:12px; top:-4px; font-style:normal; {BC} font-size:34px; color:{Y}; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Tommy John: back, but not the same?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
