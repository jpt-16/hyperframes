"""'Pitch sequencing': why every pitch is designed to mess with the hitter's timing (1080x1920, voiceover + sound effects).

    python3 tools/physics.py                                       # the three pitches and the swing timing -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/pitch-sequencing.mp4 --video-bitrate 16M

Every number on screen is read from assets/play.json, so labels and the 3D motion agree.
Shots, captions and reveals are keyed to the words of the voiceover (assets/vo/timing.json).
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

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows (t = 0 at release)
PT = P["pitches"]; FB1, CB, FB2 = PT["fb1"], PT["cb"], PT["fb2"]
SHOTS = []
def shot(a, b, pitch, cam, vs, ts, speed, swing=None, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), pitch=pitch, cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, swing=swing, **kw))
def real(a, b, pitch, cam, rel, **kw):                     # real time, released at video time rel
    shot(a, b, pitch, cam, [a, b], [a - rel, b - rel], kw.pop("speed", "rt"), **kw)
def rate(a, b, pitch, cam, t0, r, speed, **kw):             # slowed to r (play seconds per video second) from play time t0
    shot(a, b, pitch, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
SEQ0, LOOK0, WAIT0, MIND0, PAY0 = (LN(k)["t0"] - 0.07 for k in ["seq", "look", "wait", "mind", "pay"])

# hook: a fastball out of the hand, the hitter's eyes, then a curveball on a different path
real(0, 0.45, "fb1", "behind", 0.30)
real(0.45, 1.25, "fb1", "pov", 0.30)
real(1.25, 2.42, "cb", "pov", 1.40, lines={"fb1": "all", "cb": "t"})
rate(2.42, SEQ0, "cb", "track", 0.18, 1 / 3, "replay", ghost="fb1", lines={"fb1": "g", "cb": "t"})
# "a high fastball, then come back with a curveball": real time, each reaching the glove on its word
S = dict(q1Rel=W("seq", "fastball") - FB1["t_glove"], q2Rel=W("seq", "curveball") + 0.05 - CB["t_glove"])
S["q2"] = W("seq", "then") - 0.1
real(SEQ0, S["q2"], "fb1", "cf", S["q1Rel"])
real(S["q2"], LOOK0, "cb", "pov", S["q2Rel"])
# "early on they can look similar, but the curveball breaks": the batter's eyes at 1/6 speed, the fastball's path alongside
S["l1Rel"] = W("look", "breaks") - 0.42 * 6
S["l2"] = W("look", "and") + 0.6
rate(LOOK0, S["l2"], "cb", "povw", (LOOK0 - S["l1Rel"]) / 6, 1 / 6, "slow6", ghost="fb1", gmode="z", lines={"fb1": "g", "cb": "t"})
# "adjust your timing and where you expect the ball to arrive": from the side at 1/8 speed, on the same clock
rate(S["l2"], WAIT0, "cb", "track", 0.15, 1 / 8, "slow8", ghost="fb1", lines={"fb1": "g", "cb": "t"})
# the dilemma: recognize, predict, commit (the batter's eyes, slowed right down), then real time: too late
S["rec"], S["pre"], S["com"], S["late"] = W("wait", "see"), W("wait", "pitch"), W("wait", "by"), W("wait", "too")
LATE_SWING = CB["t_commit"] + 0.04                           # he waited to see it: the swing starts after the commit point
shot(WAIT0, S["com"], "cb", "povw", [WAIT0, S["rec"], S["pre"], S["com"]], [-0.06, 0.10, 0.22, CB["t_commit"]], "slowv", swing=LATE_SWING)
shot(S["com"], S["late"], "cb", "povw", [S["com"], S["late"]], [CB["t_commit"]] * 2, "freeze", swing=LATE_SWING)
S["w2"] = LN("wait")["t1"] - 0.55
real(S["late"], S["w2"], "cb", "povw", S["late"] - CB["t_commit"], swing=LATE_SWING)
rate(S["w2"], MIND0, "cb", "swing", LATE_SWING - 0.02, 1 / 4, "replay", swing=LATE_SWING, lines={"cb": "t"})
# the mind game: he has been early on breaking balls; this time he sits on one, and gets a fastball
S["m2"] = W("mind", "if") - 0.05
shot(MIND0, S["m2"], "fb2", "stare", [MIND0, S["m2"]], [-2.4, -2.4 + (S["m2"] - MIND0) * 0.35], "rt")
S["m3"] = W("mind", "the", nth=1) - 0.12
rate(S["m2"], S["m3"], "cb", "swing", -0.02, 1 / 4, "replay", swing=FB1["t_commit"], lines={"cb": "t"})          # a fastball swing on a curveball: out in front
S["m3Rel"] = W("mind", "fastball") - FB2["t_glove"]
real(S["m3"], PAY0, "fb2", "pov", S["m3Rel"], swing=CB["t_commit"], expect=[S["m3"] + 0.15, S["m3"] + 0.9], lines={"fb2": "t"})
# payoff: high fastball, curveball, fastball, the paths stacking up, then a freeze as he commits to the last one
S["p1Rel"], S["p2Rel"], S["p3Rel"] = PAY0 + 0.1, W("pay", "sequencing") + 0.05, W("pay", "the") - 0.1
FRZ_T = CB["t_commit"] + 0.06                                # his swing just under way, the fastball already at the plate
S["frz"] = S["p3Rel"] + FRZ_T
cu = [PAY0, S["frz"]]                                       # one slow camera move across the three pitches
real(PAY0, S["p2Rel"] - 0.12, "fb1", "track", S["p1Rel"], cu=cu, lines={"fb1": "t"})
real(S["p2Rel"] - 0.12, S["p3Rel"] - 0.12, "cb", "track", S["p2Rel"], cu=cu, lines={"fb1": "all", "cb": "t"})
real(S["p3Rel"] - 0.12, S["frz"], "fb2", "track", S["p3Rel"], cu=cu, swing=CB["t_commit"], lines={"fb1": "all", "cb": "all", "fb2": "t"})
shot(S["frz"], D, "fb2", "freeze", [S["frz"], D], [FRZ_T] * 2, "freeze", swing=CB["t_commit"], cu=[S["frz"], D],
     lines={"fb1": "all", "cb": "all", "fb2": "t"})
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

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0.45, D, '<div class="spd rt" id="spd">Real time</div>', cls="layer", style="z-index:30")

# ----------------------------------------------------------------- hook: a statement on frame one, then the line word by word
c.clip("hook0", 0, 0.44, """<div class="eyebrow"><i></i>The hitter's view</div>
  <div class="hk big"><span class="hl fb">Fastball?</span><span class="hl cb">Curveball?</span></div>""", cls="layer", style="z-index:12")
c.to(".hk.big", o(opacity=0, y=-30, filter="blur(10px)", duration=0.12, ease="power2.in"), 0.3)
hw = LN("hook")["words"]                                    # every pitch is designed to mess with the hitter's timing
HOOK = [("Every", 0, 0), ("pitch", 1, 0), ("is", 2, 1), ("designed", 3, 1), ("to", 4, 2), ("mess", 5, 2), ("with", 6, 2), ("your", 7, 3), ("timing.", 9, 3)]
lines = {}
for k, (w, wi, ln) in enumerate(HOOK):
    lines.setdefault(ln, []).append(f'<span class="hw{" acc" if ln == 3 else ""}" id="hw{k}">{esc(w)}</span>')
c.clip("hook", 0.44, SEQ0 - 0.02, '<div class="eyebrow"><i></i>Pitch sequencing</div><div class="hk">' + "".join(f'<span class="hl">{" ".join(v)}</span>' for v in lines.values()) + "</div>", cls="layer", style="z-index:12")
for k, (w, wi, ln) in enumerate(HOOK):
    c.ft(f"#hw{k}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), hw[wi]["t0"] - 0.04)
c.ft("#hw8", o(scale=1), o(scale=1.1, duration=0.1, yoyo=True, repeat=1), hw[9]["t0"] + 0.1)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), SEQ0 - 0.18)

# ----------------------------------------------------------------- captions: key phrases of the voiceover, word by word
# (lid, first word, last word, accent words {index: class}); the lines that are already on screen as titles are left out
CAPS = [("seq", 0, 4, {}), ("seq", 5, 8, {7: "fb", 8: "fb"}), ("seq", 9, 11, {}), ("seq", 12, 14, {14: "cb"}),
        ("look", 0, 3, {}), ("look", 4, 6, {6: "acc"}), ("look", 7, 10, {9: "cb", 10: "cb"}), ("look", 11, 15, {}), ("look", 16, 18, {18: "acc"}),
        ("look", 19, 22, {22: "acc"}), ("look", 23, 26, {}),
        ("wait", 0, 3, {2: "acc"}), ("wait", 4, 6, {}), ("wait", 7, 10, {}), ("wait", 11, 12, {}), ("wait", 13, 17, {16: "acc", 17: "acc"}), ("wait", 18, 22, {}),
        ("mind", 5, 7, {}), ("mind", 8, 9, {9: "acc"}), ("mind", 10, 12, {11: "cb", 12: "cb"}), ("mind", 13, 15, {}), ("mind", 16, 18, {16: "acc"}),
        ("pay", 0, 2, {2: "acc"}), ("pay", 3, 6, {}), ("pay", 7, 8, {}), ("pay", 9, 12, {12: "acc"}), ("pay", 13, 16, {15: "acc", 16: "acc"})]
CAP_END = {("mind", 16): W("mind", "and", nth=1) - 0.1}     # the "think again" title takes over from "and challenge you"
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = LN(lid)["words"][CAPS[k + 1][1]]["t0"] - 0.06
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

# ----------------------------------------------------------------- which pitch is which
def chip(cid, t0, t1, cls, text):
    c.clip(cid, t0, t1, f'<div class="pc {cls}" id="{cid}x"><i></i>{text}</div>', cls="layer", style="z-index:11"); pop(f"#{cid}x", t0)
chip("pc1", W("seq", "high") - 0.05, S["q2"], "fb", f'High fastball · {FB1["mph"]:.0f} mph')
chip("pc2", W("seq", "come") - 0.05, LOOK0, "cb", f'Curveball · {CB["mph"]:.0f} mph')

# ----------------------------------------------------------------- the tunnel: alike early, apart late
G = P["gap"]; vbr = W("look", "breaks")
c.clip("gapc", vbr + 0.15, S["l2"] - 0.05, f"""<div class="dcard" id="gapd"><div class="dh">Fastball vs curveball · same distance from the plate</div>
    <div class="drow"><span>{G["commit_dist_ft"]:.0f} ft from the plate</span><b class="y">{G["commit_in"]:.0f} IN APART</b></div>
    <div class="drow"><span>At the plate</span><b class="c">{G["plate_in"]:.0f} IN APART</b></div></div>""", cls="layer", style="z-index:11")
pop("#gapd", vbr + 0.2)
c.clip("arrc", W("look", "timing") - 0.1, WAIT0 - 0.05, f"""<div class="dcard" id="arrd"><div class="dh">The curveball, compared with the fastball</div>
    <div class="drow" id="ar1"><span>Gets there</span><b class="c">+{P["cb_later_s"]:.2f} S LATER</b></div>
    <div class="drow" id="ar2"><span>Arrives</span><b class="c">≈{P["cb_lower_in"]:.0f} IN LOWER</b></div></div>""", cls="layer", style="z-index:11")
pop("#arrd", W("look", "timing") - 0.05); pop("#ar2", W("look", "where"), 16)
c.clip("leg", S["l2"], WAIT0 - 0.05, '<div class="leg"><span class="fb"><i></i>High fastball</span><span class="cb"><i></i>Curveball</span></div>', cls="layer", style="z-index:11")

# ----------------------------------------------------------------- the dilemma: recognize, predict, commit
BIG = [("Recognize", S["rec"]), ("Predict", S["pre"]), ("Commit", S["com"])]
c.clip("big", WAIT0 + 0.1, S["late"] + 0.1, '<div class="bigw">' + "".join(f'<span id="bw{k}">{w}</span>' for k, (w, t) in enumerate(BIG)) +
       f'<em id="bw3">Ball still {G["commit_dist_ft"]:.0f} ft away · most of the break still to come</em></div>', cls="layer", style="z-index:12")
for k, (w, t) in enumerate(BIG):
    c.ft(f"#bw{k}", o(opacity=0, x=-40, filter="blur(10px)"), o(opacity=1, x=0, filter="blur(0px)", duration=0.2, ease="power3.out"), t - 0.04)
    if k: c.to(f"#bw{k - 1}", o(opacity=0.3, duration=0.2), t - 0.05)
c.ft("#bw3", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.25, ease="power3.out"), S["com"] + 0.22)
c.to("#big .bigw", o(opacity=0, duration=0.1), S["late"])
vlate = at_play(shot_at(S["w2"] + 0.01), LATE_SWING + P["swing"])
c.clip("latec", vlate - 0.05, MIND0, '<div class="tagd hot" id="lated">Late</div>', cls="layer", style="z-index:12"); pop("#lated", vlate - 0.05)

# ----------------------------------------------------------------- the mind game
c.clip("eb1", W("mind", "mind") - 0.1, S["m2"] - 0.04, '<div class="hk mid"><span class="hl" id="eb1a">Expecting</span><span class="hl" id="eb1b">the <em class="cb">breaker?</em></span></div>', cls="layer", style="z-index:12")
c.ft("#eb1a", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), W("mind", "mind") - 0.08)
c.ft("#eb1b", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), W("mind", "game") - 0.08)
vfront = at_play(shot_at(S["m2"] + 0.01), FB1["t_commit"] + P["swing"])
c.clip("frontc", vfront - 0.05, S["m3"], '<div class="tagd" id="frontd">Out in front</div>', cls="layer", style="z-index:12"); pop("#frontd", vfront - 0.05)
c.clip("expc", S["m3"] + 0.2, PAY0, '<div class="leg"><span class="cb dash"><i></i>What he expects: curveball</span><span class="hot" id="expf"><i></i>What he gets: fastball</span></div>', cls="layer", style="z-index:11")
c.ft("#expc .leg", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.25), S["m3"] + 0.25)
c.ft("#expf", o(opacity=0), o(opacity=1, duration=0.2), S["m3Rel"])
TA = W("mind", "and", nth=1) - 0.06
c.clip("eb2", TA, PAY0 - 0.02, f'<div class="hk mid"><span class="hl">Expecting</span><span class="hl">the <em class="cb">breaker?</em></span><span class="hl acc" id="eb2b">Think again.</span></div>', cls="layer", style="z-index:12")
c.ft("#eb2b", o(opacity=0, scale=1.25, filter="blur(14px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), S["m3Rel"] + FB2["t_glove"] - 0.05)
c.clip("note", S["m3"] + 0.9, PAY0 - 0.02, '<div class="note" id="noted">Whether it works depends on the count, the hitter\'s tendencies, and where the pitcher puts it.</div>', cls="layer", style="z-index:11")
c.ft("#noted", o(opacity=0), o(opacity=1, duration=0.3), S["m3"] + 0.95)

# ----------------------------------------------------------------- payoff: the sequence, then the freeze
SEQ = [("1", "High fastball", "fb", S["p1Rel"] + FB1["t_front"]), ("2", "Curveball", "cb", S["p2Rel"] + CB["t_front"]), ("3", "Fastball", "hot", S["frz"])]
c.clip("seqc", SEQ[0][3] - 0.05, D, '<div class="seqs">' + "".join(f'<span class="{cl}" id="sq{k}"><b>{n}</b>{esc(w)}</span>' for k, (n, w, cl, t) in enumerate(SEQ)) + "</div>", cls="layer", style="z-index:11")
for k, (n, w, cl, t) in enumerate(SEQ): pop(f"#sq{k}", t - 0.05, 16)
ENDW = "Now imagine doing this against 100 MPH.".split()
ET = W("pay", "expect") - 0.05
c.clip("endc", ET, D, '<div class="endt">' + " ".join(f'<span class="ew{" acc" if w in ("100", "MPH.") else ""}" id="ew{k}">{esc(w.upper())}</span>' for k, w in enumerate(ENDW)) + "</div>", cls="layer", style="z-index:12")
for k, w in enumerate(ENDW):
    c.ft(f"#ew{k}", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), ET + 0.09 * k)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for k, (w, wi, ln) in enumerate(HOOK): cue("tick", hw[wi]["t0"], -12)
for x in SHOTS[1:]: cue("whoosh", x["a"], -12)              # the cuts
for x in SHOTS:                                             # each pitch: out of the hand, and into the glove
    pc = PT[x["pitch"]]; slow = x["speed"] != "rt"
    cue("whoosh", at_play(x, 0.1), -9 if slow else -2)
    cue("glove", at_play(x, pc["t_glove"]), -5 if slow else 0)
    if x["swing"] is not None: cue("whoosh", at_play(x, x["swing"] + 0.06), -7 if slow else -1)   # the bat through the zone
for k, (w, t) in enumerate(BIG): cue("hit", t, -6)
cue("impact", S["com"], -5); cue("riser-m", S["com"], -10)
cue("popup", vbr + 0.2, -9); cue("popup", W("look", "timing") - 0.05, -9); cue("popup", W("look", "where"), -10)
cue("hit", vlate, -7); cue("hit", vfront, -8)
cue("hit", W("mind", "mind"), -7); cue("impact", S["m3Rel"] + FB2["t_glove"], -6)
for k, (n, w, cl, t) in enumerate(SEQ): cue("popup", t, -9)
cue("impact", S["frz"], -4); cue("riser-s", S["frz"], -9)
for k in range(len(ENDW)): cue("tick", ET + 0.09 * k, -13)
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -2.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0}

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
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

.cap .cw.fb, .hk .fb, .fb {{ color:{Y}; }} .cap .cw.cb, .hk .cb, .cb {{ color:{CYAN}; }} .hot {{ color:{HOT}; }}
.hk.mid {{ font-size:124px; }} .hk em {{ font-style:normal; }}

.pc {{ position:absolute; left:52px; top:1600px; display:inline-flex; align-items:center; gap:14px; padding:12px 22px; border-radius:12px; background:rgba(6,10,18,.8);
       {MONO} font-size:30px; letter-spacing:.12em; }}
.pc i {{ width:16px; height:16px; border-radius:50%; background:currentColor; box-shadow:0 0 12px currentColor; }}

.dcard {{ position:absolute; left:44px; right:44px; top:1330px; display:grid; gap:14px; padding:22px 28px; border-radius:22px; background:rgba(6,10,18,.84); border:1px solid rgba(255,255,255,.1); }}
.dh {{ {MONO} font-size:20px; letter-spacing:.1em; color:{MUTED}; }}
.drow {{ display:flex; align-items:baseline; justify-content:space-between; gap:20px; }}
.drow span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:30px; color:#dfe5ec; }}
.drow b {{ font-weight:800; font-size:76px; line-height:1; font-variant-numeric:tabular-nums; }}
.drow b.y {{ color:{Y}; }} .drow b.c {{ color:{CYAN}; }}

.leg {{ position:absolute; left:52px; top:1220px; display:grid; gap:10px; padding:14px 20px; border-radius:12px; background:rgba(6,10,18,.72); {MONO} font-size:24px; letter-spacing:.1em; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.leg span {{ display:flex; align-items:center; gap:14px; }}
.leg i {{ width:44px; height:6px; border-radius:3px; background:currentColor; }}
.leg .dash i {{ background:repeating-linear-gradient(90deg, currentColor 0 9px, transparent 9px 16px); }}

.bigw {{ position:absolute; left:52px; top:1180px; display:grid; gap:0; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:140px; line-height:.92; text-transform:uppercase;
         text-shadow:0 6px 30px rgba(0,0,0,.75); }}
.bigw span:nth-child(1) {{ color:{CYAN}; }} .bigw span:nth-child(2) {{ color:{Y}; }} .bigw span:nth-child(3) {{ color:{HOT}; }}
.bigw em {{ font-style:normal; font-size:50px; line-height:1.05; color:#fff; margin-top:16px; max-width:940px; }}

.tagd {{ position:absolute; left:50%; top:1300px; transform:translateX(-50%); padding:10px 26px; border-radius:14px; background:rgba(6,10,18,.84); white-space:nowrap;
         font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:84px; line-height:1; text-transform:uppercase; color:{Y}; }}
.tagd.hot {{ color:{HOT}; }}
.note {{ position:absolute; left:52px; right:52px; top:1700px; font-family:"Inter", sans-serif; font-weight:700; font-size:27px; line-height:1.35; color:#cfd6e0; text-shadow:0 2px 10px rgba(0,0,0,.9); }}

.seqs {{ position:absolute; left:44px; right:44px; top:1660px; display:flex; gap:14px; }}
.seqs span {{ flex:1; display:flex; align-items:center; gap:10px; padding:12px 14px; border-radius:12px; background:rgba(6,10,18,.82); {MONO} font-size:22px; letter-spacing:.06em; white-space:nowrap; }}
.seqs b {{ display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:currentColor; color:#05080d; font-family:"Inter", sans-serif; font-weight:800; font-size:20px; }}

.endt {{ position:absolute; left:34px; right:34px; top:1160px; padding:22px 20px 26px; border-radius:24px; background:rgba(4,7,13,.62); font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:112px; line-height:.94; text-transform:uppercase; color:#fff;
         text-shadow:0 6px 30px rgba(0,0,0,.8); }}
.endt .acc {{ color:{HOT}; }}
.ew {{ display:inline-block; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "Pitch sequencing", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(CAPS)} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
