"""'The infield fly rule': why an infielder can't drop an easy pop-up for a cheap double play (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the pitch and the pop-up -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/infield-fly.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. The rule as shown (MLB Official Baseball Rules,
definition of an infield fly and 5.09(a)(12)): a fair fly ball (not a line drive or a bunt) that an infielder can catch
with ordinary effort, with runners on 1st and 2nd or the bases loaded and fewer than two out. The umpire declares it
while the ball is in the air; the batter is out whether or not it's caught; the ball stays live and the runners may
advance at their own risk (no force, since the batter is out). The play: bases loaded, one out, a pop-up that comes down
on the infield dirt in front of the shortstop.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PO = P["pop"]; TL = PO["t_land"]
T_CALL, TF = 1.2, TL + 0.36
TR1 = TF + 0.34; TC1 = TR1 + 0.42; TR2 = TC1 + 0.25; TC2 = TR2 + 0.8              # mirrors assets/field.js
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S4, S5, S6, S7, S8 = (LN(k)["t0"] - 0.06 for k in ["setup", "trap", "name", "rule", "why", "twist", "end"])

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def vat(sh, t):                                                    # the video time a shot shows play time t
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
# 1-2 the trap, one continuous pop-up (contact at 0.3; it reaches the dirt as he says "on purpose"): the swing, the climb,
#     bases loaded, the shortstop under it, the glove pulled away; freeze just above the dirt
CT = 0.3
FRZ1 = W("setup", "on") + 0.05; TFZ = TL - 0.015
R = TFZ / (FRZ1 - CT)                                             # a touch under real time so the pop-up spans the two lines
A2, A3, A4, A5 = 0.75, S2, W("setup", "the") - 0.06, W("setup", "and") - 0.06
t_ = lambda v: (v - CT) * R
rate(0.0, A2, "plateHi", t_(0.0), R, play="rule")
rate(A2, A3, "rise", t_(A2), R, play="rule")
rate(A3, A4, "loaded", t_(A3), R, play="rule", marks="run")
rate(A4, A5, "under", t_(A4), R, play="rule")
shot(A5, S3, "drop", [A5, FRZ1, S3], [t_(A5), TFZ, TFZ], play="rule", zt=TFZ - 0.14, freeze=FRZ1)
# 3 "the runners take off, the defense gets easy outs": without the rule, the drop becomes a double play
B2 = W("trap", "except") + 0.04
shot(S3, B2, "dpWide", [S3, B2], [TL - 0.05, TC2 + 0.12], play="norule", marks=1)
# "...except they don't": the umpire's arm goes up (½ speed); "That's the infield fly rule"
rate(B2, S5, "umpCU", T_CALL - 0.2, 0.5, "slow", play="rule", zt=T_CALL)
VCALL = vat(SHOTS[-1], T_CALL + 0.04)
# 4 the conditions: fair fly, ordinary effort (the shortstop camped under it), then the board: runners, bases loaded, outs;
#   "the umpire can call the batter out immediately"
C2, C3 = W("rule", "with", nth=1) - 0.12, W("rule", "the", nth=1) - 0.06
rate(S5, C2, "under", 2.2, 0.35, "slow", play="rule")
rate(C2, C3, "top", -1.0, 0.02, play="rule")
rate(C3, S6, "wideAir", 1.7, play="rule")
# 5 why: the same pop-up, no rule (top) vs. the rule (bottom)
shot(S6, S7, "split", [S6, S7], [TL - 0.55, TC2 + 0.35], mode="split", play="rule", marks=1)
SP = SHOTS[-1]; VL3, VC1, VC2 = (vat(SP, x) for x in (TL, TC1, TC2))
# 6 the twist: it falls in (½ speed); the runner on third breaks for home at his own risk and is looked back
D2 = W("twist", "the", nth=1) - 0.08
rate(S7, D2, "dirt", TL - 0.42, 0.5, "slow", play="rule")
rate(D2, S8, "runners", TL + 0.12, play="rule")
# 7 "Baseball has a rule for a play that looks too easy": the batter walks off; freeze
FRZ2 = LN("end")["t1"] + 0.06
shot(S8, D, "final", [S8, FRZ2, D], [TL + 1.6, TL + 1.6 + (FRZ2 - S8), TL + 1.6 + (FRZ2 - S8)], play="rule", freeze=FRZ2)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
VL7 = vat(SHOTS[-3], TL)
CUTS = [x["a"] for x in SHOTS[1:]]
DPS = SHOTS[5]; VDC1, VDC2, VDL = vat(DPS, TC1), vat(DPS, TC2), S3 + 0.05

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [FRZ1, S3, B2, S5, C2, S6, S7, FRZ2]:
    c.set("#flash", '{"opacity":0.6}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def punch(pid, t0, t1, html, top=1300, cls=""):
    c.clip(pid, t0, t1, f'<div class="pt {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def words(wid, t0, t1, parts, top=300, cls="hk"):                # a headline that lands word by word, each on its own time
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, (w, _) in enumerate(ws)) + "</span>" for i, (ws, k) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (ws, _) in enumerate(parts):
        for j, (_, ts_) in enumerate(ws):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), ts_ - 0.03)
LW = lambda lid, i0, i1: [(LN(lid)["words"][n]["w"].rstrip(",:"), LN(lid)["words"][n]["t0"]) for n in range(i0, i1 + 1)]

# ----------------------------------------------------------------- 1 the hook: the line builds with the voice over the pop-up
words("hook", 0.0, S2 - 0.02, [(LW("hook", 0, 3), ""), (LW("hook", 4, 6), "acc")], 300)
c.to("#hookx", o(opacity=0, y=-24, duration=0.12, ease="power2.in"), S2 - 0.14)

# ----------------------------------------------------------------- captions: the voiceover, word by word (titles instead on the hook, "on purpose" and "That's the infield fly rule")
CAPS = [("setup", 0, 1, {0: "acc", 1: "acc"}), ("setup", 2, 5, {4: "acc"}), ("setup", 6, 10, {10: "acc"}), ("setup", 11, 16, {16: "acc"}),
        ("trap", 0, 3, {2: "acc", 3: "acc"}), ("trap", 4, 8, {7: "acc", 8: "acc"}), ("trap", 9, 11, {11: "acc"}),
        ("rule", 0, 4, {2: "acc", 3: "acc", 4: "acc"}), ("rule", 5, 10, {10: "acc"}), ("rule", 11, 13, {12: "acc", 13: "acc"}), ("rule", 14, 19, {17: "acc", 19: "acc"}),
        ("rule", 20, 23, {22: "acc", 23: "acc"}), ("rule", 24, 28, {25: "acc", 27: "acc", 28: "acc"}), ("rule", 29, 32, {30: "acc"}), ("rule", 33, 36, {35: "acc", 36: "acc"}),
        ("why", 0, 0, {0: "acc"}), ("why", 1, 4, {}), ("why", 5, 9, {6: "acc"}), ("why", 10, 13, {}), ("why", 14, 17, {15: "acc", 16: "acc", 17: "acc"}),
        ("twist", 0, 3, {3: "acc"}), ("twist", 4, 8, {8: "acc"}), ("twist", 9, 12, {11: "acc", 12: "acc"}),
        ("end", 0, 3, {3: "acc"}), ("end", 4, 10, {9: "acc", 10: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif lid == "setup": end = FRZ1 - 0.12
    elif lid == "end": end = FRZ2 - 0.02
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"].replace("...", "…"); w = w.rstrip(",:") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- 2 the trap
tag("sit", A3 + 0.05, A4 - 0.02, "wh", "Bases loaded · 1 out", 560)
pinl("pss", A4 + 0.1, A5 - 0.02, "Shortstop: “I got it”", "ss", "yl")
words("hookq", FRZ1 - 0.12, S3 - 0.02, [([("Wait…", FRZ1 - 0.12)], ""), ([("He", FRZ1 + 0.05), ("did", FRZ1 + 0.1), ("that", FRZ1 + 0.15)], ""), ([("on", FRZ1 + 0.22), ("purpose?", FRZ1 + 0.27)], "acc")], 300)
c.ft("#hookqx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.06, duration=0.14, ease="power3.out"), FRZ1 + 0.27)

# ----------------------------------------------------------------- 3 without the rule, then the call
c.clip("nor", S3 + 0.02, B2 - 0.02, '<span class="hlab hot nr" id="norx">Without the rule</span>', cls="layer", style="z-index:13"); pop("#norx", S3 + 0.02, 10)
tag("d2b", VDC1, VDC2 - 0.02, "hot", "Force out at 2nd", 1500)
tag("d1b", VDC2, B2 - 0.02, "hot", "And 1st: double play", 1500)
words("ifr", W("name", "that's") - 0.03, S5 - 0.02, [(LW("name", 0, 1), ""), (LW("name", 2, 4), "acc")], 300)
tag("tif", VCALL + 0.1, S5 - 0.02, "wh", "Arm straight up: called while the ball is <b class='yl'>still in the air</b>", 1500)

# ----------------------------------------------------------------- 4 the conditions
BXY = {"h": (0.5, 0.9), "1": (0.88, 0.5), "2": (0.5, 0.1), "3": (0.12, 0.5)}
def diamond(did, w, runners, batter=True, extra=""):
    h = w * 0.8; P_ = {k: (x * w, y * h) for k, (x, y) in BXY.items()}
    pts = " ".join(f"{P_[k][0]:.0f},{P_[k][1]:.0f}" for k in "h123")
    bases = "".join(f'<i class="bs{" hp" if k == "h" else ""}" id="{did}b{k}" style="left:{P_[k][0]:.0f}px;top:{P_[k][1]:.0f}px"></i>' for k in "h123")
    rs = "".join(f'<b class="rn" id="{did}r{k}" style="left:{P_[k][0]:.0f}px;top:{P_[k][1]:.0f}px"></b>' for k in runners)
    bt = f'<b class="rn bt" id="{did}rh" style="left:{P_["h"][0]:.0f}px;top:{P_["h"][1]:.0f}px">★</b>' if batter else ""
    return f'<div class="dia" style="width:{w:.0f}px;height:{h:.0f}px"><svg width="{w:.0f}" height="{h:.0f}"><polygon points="{pts}" /></svg>{bases}{rs}{bt}{extra}</div>', P_
dc, PC = diamond("cd", 420, "", batter=False)
dc = dc.replace("</div>", "".join(f'<b class="rn" id="cr{k}" style="left:{PC[k][0]:.0f}px;top:{PC[k][1]:.0f}px;opacity:0"></b>' for k in "123") + "</div>", 1)
CX = [("Fair fly ball", W("rule", "fair")), ("Catchable with ordinary effort", W("rule", "ordinary")), ("Runners on 1st + 2nd", W("rule", "first")),
      ("…or bases loaded", W("rule", "bases")), ("Less than 2 outs", W("rule", "fewer"))]
c.clip("clist", S5 + 0.05, C3 - 0.02, '<div class="clst" id="clx">' + "".join(f'<div class="ci" id="ci{i}"><i>✓</i><b>{esc(t)}</b></div>' for i, (t, _) in enumerate(CX)) + "</div>", cls="layer", style="z-index:13")
for i, (_, t_c) in enumerate(CX): c.ft(f"#ci{i}", o(opacity=0, x=-60), o(opacity=1, x=0, duration=0.22, ease="power3.out"), t_c - 0.03)
c.clip("cond", C2, C3, f'<div class="tac" id="tacx"></div><div class="cdia" id="cdx">{dc}</div>', cls="layer", style="z-index:11")
c.ft("#tacx", o(opacity=0), o(opacity=1, duration=0.2), C2); pop("#cdx", C2 + 0.02, 14)
for k_, t_c in [("1", W("rule", "first")), ("2", W("rule", "second")), ("3", W("rule", "bases"))]:
    c.ft(f"#cr{k_}", o(opacity=0, scale=1.8), o(opacity=1, scale=1, duration=0.25, ease="back.out(2)"), t_c - 0.03)
c.clip("cfn", C2 + 0.3, C3 - 0.02, '<div class="cfn" id="cfnx">Not on a line drive or a bunt · the umpire’s judgment</div>', cls="layer", style="z-index:13")
c.ft("#cfnx", o(opacity=0), o(opacity=1, duration=0.3), C2 + 0.3)
pinl("pout", C3 + 0.08, S6 - 0.02, "Out", "batter")
punch("pbo", W("rule", "batter") - 0.05, S6 - 0.02, "Batter:<br><em>automatically out</em>", 1300)

# ----------------------------------------------------------------- 5 why: no cheap double play
c.clip("splt", S6, S7, f"""<div class="seam"></div>
  <div class="half t"><span class="hlab hot" id="hl1">Without the rule</span></div>
  <div class="half b"><span class="hlab yl" id="hl2">With the rule · batter already out</span></div>""", cls="layer", style="z-index:11")
pop("#hl1", S6 + 0.05, 10); pop("#hl2", S6 + 0.15, 10)
tag("sdrop", VL3 - 0.1, VC1 - 0.05, "hot", "Dropped on purpose", 760)
tag("s2b", VC1, VC2 - 0.05, "hot", "Force out at 2nd", 760)
tag("s1b", VC2, S7 - 0.02, "hot", "And at 1st: <b>double play</b>", 760)
tag("sno", VL3 + 0.1, S7 - 0.02, "yl", "No force: runners may advance at their own risk", 1730)
punch("pdp", W("why", "cheap") - 0.05, S7 - 0.02, "No cheap<br><em>double play.</em>", 1240, "ctr")

# ----------------------------------------------------------------- 6 the twist; 7 the end
punch("pcd", W("twist", "twist") - 0.05, D2 - 0.02, "The catch<br><em>doesn't matter.</em>", 1280)
pinl("pr3", D2 + 0.1, S8 - 0.02, "Runner", "r3", "yl")
tag("trn", W("twist", "advance") - 0.05, S8 - 0.02, "wh", "Ball's live: he can try for home <b class='yl'>at his own risk</b>", 1500)
pinl("pout2", S8 + 0.1, D, "Out", "batter")
tag("tbo", S8 + 0.2, FRZ2 - 0.02, "wh", "The batter was out the moment it was called", 1500)
words("q", FRZ2, D, [([("Did", FRZ2 + 0.02), ("you", FRZ2 + 0.08), ("know", FRZ2 + 0.14)], ""), ([("this", FRZ2 + 0.24), ("rule?", FRZ2 + 0.3)], "acc")], 300)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_c in CUTS: cue("whoosh", t_c, -10)
cue("impact", 0.0, -8); cue("riser-s", FRZ1, -4); cue("impact", FRZ1, 0); cue("tick", FRZ1, -1)
cue("glove", VDC1, -1); cue("glove", VDC2, -1); cue("popup", VDC1, -7); cue("popup", VDC2, -5)
cue("tap", VCALL, 0); cue("impact", VCALL, -1); cue("riser-s", VCALL, -9); cue("impact", W("name", "infield") - 0.03, -5)
for _, t_c in CX: cue("tick", t_c, -2)
for k_ in ["first", "second", "bases"]: cue("popup", W("rule", k_), -8)
cue("impact", W("rule", "batter") - 0.05, -5)
cue("glove", VC1, -6); cue("glove", VC2, -6); cue("impact", W("why", "cheap") - 0.05, -4)
cue("impact", W("twist", "twist") - 0.05, -6)
cue("riser-m", FRZ2, -6); cue("impact", FRZ2, -1); cue("tick", FRZ2, -2)
CRACKS = [(CT, 0.6)]
THUDS = [(vat(SHOTS[5], TL), 0.8), (VL3, 0.6), (VL7, 1.0, 0.5)]   # the ball on the dirt (the last one at half speed)
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
    for th in THUDS:
        x = thud(rng, th[2] if len(th) > 2 else 1.0); i = int(th[0] * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * th[1]
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-30 / 20)
    # the music bed: made for this video (lands its chord on the closing question), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, FRZ2, style="drive", seed=31)
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
.hlab.nr {{ position:absolute; left:40px; top:200px; }}
.clst {{ top:1080px; gap:12px; }} .ci b {{ font-size:58px; }}
.cfn {{ top:1760px; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The infield fly rule", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
