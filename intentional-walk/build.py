"""'Intentional walk: smart strategy or big mistake?': an intentional-walk breakdown (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the walk timeline, the pitch, the home run -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/intentional-walk.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. The 2024 NLCS scene is an illustrative 3D
reenactment with generic uniforms (not broadcast footage). As reported: NLCS Game 2 (Oct. 14, 2024), 2nd inning, 2 outs,
Mets up 2-0 with runners on 2nd and 3rd; the Dodgers intentionally walked Francisco Lindor to load the bases, and Mark
Vientos hit a grand slam off right-hander Landon Knack (a 95 mph fastball, 391 ft projected, to right-center).
The base diagrams follow the force rules (a walk moves a runner up only when he is forced); no probabilities are shown.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
IB, SL, HR = P["ibb"], P["pitches"]["slam"], P["hits"]["slam"]
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S3B, S4, SQ = (LN(k)["t0"] - 0.06 for k in ["target", "risk", "nlcs", "gamble", "q"])
TC = SL["t_contact"]

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r                    # the play time to start a shot at a so that play time t lands at video time v
def tv(sh, v): return sh["ts"][0] + (v - sh["vs"][0]) * (sh["ts"][1] - sh["ts"][0]) / (sh["vs"][1] - sh["vs"][0])
# 1 the hook: the star in, runners on 2nd and 3rd; the battery looks to the dugout; four fingers on "intentionally"; he drops the bat
H2, H3 = 1.0, 1.95
rate(0.0, H2, "plateHi", -1.75, play="ibb")
rate(H2, H3, "dugout", on(W("hook", "intentionally"), 0.0, H2), play="ibb", zt=0.0)
t3 = 0.7; ZOOM = W("hook", "base") - 0.06
rate(H3, S2, "walkOff", t3, play="ibb", zt=t3 + ZOOM - H3)
# 2 the strategy: he reaches first (bases loaded); the choice; the next hitter on deck
A2B, A2C = W("target", "real") - 0.12, W("target", "it's") - 0.12
ARR = 3.95
rate(S2, A2B, "firstB", on(ARR, IB["T_ARR"], S2), play="ibb")
rate(A2B, A2C, "wide", IB["T_ARR"] + 0.3, play="ibb")
rate(A2C, S3, "onDeck", IB["T_NB"] - 1.2, play="ibb", ring="next")
# 3 the backfire: the next hitter walks up ("risk"); 2024 NLCS, the walk to Lindor, Vientos, the grand slam, a replay
B2, B3, B3B, B4, B5, B6 = S3B, W("nlcs", "the", nth=1) - 0.08, 11.05, W("nlcs", "the", nth=2) - 0.08, 13.85, W("nlcs", "grand") - 0.02
rate(S3, B2, "risk", IB["T_NB"] + 2.6, play="ibb")
rate(B2, B3, "estab", -3.3, play="nlcs")
rate(B3, B3B, "dugout", on(W("nlcs", "intentionally"), 0.0, B3), play="nlcs", zt=0.0)
rate(B3B, B4, "walkL", 0.7, play="nlcs")
VC = W("nlcs", "responded") + 0.05                                 # contact
rate(B4, B5, "loaded", on(VC, TC, B4), play="slam", br=1)
rate(B5, B6, "bat", on(VC, TC, B5), play="slam")
LAND = 15.40
shot(B6, S4, "track", [B6, LAND, S4], [TC + HR["t_land"] - (LAND - B6) * 1.25, TC + HR["t_land"], TC + HR["t_land"] + (S4 - LAND)], play="slam")
T4 = W("gamble", "avoid") - 0.08
RPC = S4 + 0.42
rate(S4, T4, "batLow", on(RPC, TC, S4, 0.5), 0.5, "replay", play="slam")
# 4 the analytics: the tactical board over the field from above
S5 = W("analytics", "so") - 0.06
rate(T4, S5, "top", -6.0, 0.02, play="ibb")
# 5 the verdict: the manager weighs it (the hitter, the next matchup, the outs, the double play), signals, the next pitch, freeze
V2, V3, V4, V5 = W("analytics", "hitter") - 0.1, W("analytics", "the", nth=2) - 0.06, W("analytics", "the", nth=3) - 0.06, W("analytics", "whether") - 0.1
rate(S5, V2, "mgrCU", -5.2, play="ibb", think=1, mlook=[[-5.2, "plate"], [-4.9, "od"], [-4.5, "od"], [-4.25, "plate"]])
rate(V2, V3, "starCU", -4.2, play="ibb", ring="star")
rate(V3, V4, "onDeck", -3.7, play="ibb", ring="next")
rate(V4, V5, "outs", -2.9, play="ibb")
rate(V5, SQ, "dpTop", -2.1, play="ibb", ghost=1, dp=[-2.1 + W("analytics", "double") - V5, -2.1 + W("analytics", "possible") - V5])
V7, V8 = W("q", "superstar") + 0.25, W("q", "actually") + 0.25
rate(SQ, V7, "dugout", on(W("q", "walking"), 0.0, SQ), play="ibb", zt=0.0)
rate(V7, V8, "walkOff", 0.72, play="ibb")
FRZ = W("q", "baseball", end=True) + 0.08
TFR = IB["T_PG"] - P["pitches"]["final"]["flight"] - 0.36           # he's in his stride, just before he lets it go
shot(V8, D, "hook2", [V8, FRZ, D], [TFR - (FRZ - V8), TFR, TFR], play="ibb", freeze=round(FRZ, 3))
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
FLASH = [S2, S3B, B6, S4, T4, S5, FRZ]
for f in FLASH:
    c.set("#flash", '{"opacity":0.65}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=560):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def punch(pid, t0, t1, html, top=1300, cls=""):
    c.clip(pid, t0, t1, f'<div class="pt {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
WORD_IN = lambda sel, t: c.ft(sel, o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), t - 0.04)

# ----------------------------------------------------------------- 1 the hook: the question builds with the voice; a quick zoom on "base?"; a hard cut
c.clip("hook", 0, S2, """<div class="hk" id="hkx"><span class="hl"><span class="hw" id="hw0">Why</span> <span class="hw" id="hw1">give him</span></span>
  <span class="hl acc"><span class="hw" id="hw2">first base?</span></span></div>""", cls="layer", style="z-index:12")
for i, t_ in enumerate([W("hook", "why"), W("hook", "put"), W("hook", "on")]):
    c.ft(f"#hw{i}", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t_ - 0.03)
c.ft("#hkx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.09, duration=0.16, ease="power3.out"), ZOOM)
pinl("pst", 0.3, H2 - 0.02, "★ Star hitter", "star")
tag("tsig", H2 + 0.15, H3 - 0.02, "wh", "The manager's signal: <b class='yl'>intentional walk</b>", 1500)
tag("taw", H3 + 0.25, S2, "wh", "Awarded first base · <b class='yl'>no pitches thrown</b>", 1500)

# ----------------------------------------------------------------- captions: the voiceover, word by word (the hook and "In the 2024 NLCS" are titles instead)
CAPS = [("target", 0, 1, {}), ("target", 2, 4, {4: "acc"}), ("target", 5, 10, {7: "acc"}), ("target", 11, 16, {13: "acc", 16: "acc"}),
        ("risk", 0, 3, {3: "acc"}),
        ("nlcs", 8, 11, {10: "acc", 11: "acc"}), ("nlcs", 12, 13, {}), ("nlcs", 14, 16, {15: "acc"}), ("nlcs", 17, 18, {}), ("nlcs", 19, 23, {22: "acc", 23: "acc"}),
        ("gamble", 0, 2, {2: "acc"}), ("gamble", 3, 6, {5: "acc"}), ("gamble", 7, 11, {9: "acc"}), ("gamble", 12, 15, {13: "acc"}),
        ("analytics", 0, 1, {}), ("analytics", 2, 5, {3: "acc", 4: "acc"}), ("analytics", 6, 10, {10: "acc"}), ("analytics", 11, 15, {12: "acc", 15: "acc"}),
        ("analytics", 16, 17, {17: "acc"}), ("analytics", 18, 24, {21: "acc", 22: "acc"}),
        ("q", 0, 3, {3: "acc"}), ("q", 4, 5, {5: "acc"}), ("q", 6, 8, {7: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    elif lid == "q": end = FRZ - 0.02
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    if lid == "risk": end = S3B - 0.02
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",:") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): WORD_IN(f"#{cid}w{n - i0}", words[n]["t0"])

# ----------------------------------------------------------------- base diagrams
BXY = {"h": (0.5, 0.9), "1": (0.88, 0.5), "2": (0.5, 0.1), "3": (0.12, 0.5)}
def diamond(did, w, runners, batter=True, extra=""):
    h = w * 0.8; P_ = {k: (x * w, y * h) for k, (x, y) in BXY.items()}
    pts = " ".join(f"{P_[k][0]:.0f},{P_[k][1]:.0f}" for k in "h123")
    bases = "".join(f'<i class="bs{" hp" if k == "h" else ""}" id="{did}b{k}" style="left:{P_[k][0]:.0f}px;top:{P_[k][1]:.0f}px"></i>' for k in "h123")
    rs = "".join(f'<b class="rn" id="{did}r{k}" style="left:{P_[k][0]:.0f}px;top:{P_[k][1]:.0f}px"></b>' for k in runners)
    bt = f'<b class="rn bt" id="{did}rh" style="left:{P_["h"][0]:.0f}px;top:{P_["h"][1]:.0f}px">★</b>' if batter else ""
    return f'<div class="dia" style="width:{w:.0f}px;height:{h:.0f}px"><svg width="{w:.0f}" height="{h:.0f}"><polygon points="{pts}" /></svg>{bases}{rs}{bt}{extra}</div>', P_
def move(did, P_, frm, to, t, dur=0.45, new=False):
    dx, dy = P_[to][0] - P_[frm][0], P_[to][1] - P_[frm][1]
    c.to(f"#{did}r{frm}", o(x=round(dx), y=round(dy), duration=dur, ease="power2.inOut"), t)
    if new: c.to(f"#{did}r{frm}", o(backgroundColor=Y, color="#05080d", duration=0.15), t + dur - 0.1)

# ----------------------------------------------------------------- 2 the strategy
dm, PM = diamond("dm", 250, "23")
c.clip("mini", S2 + 0.1, A2B - 0.02, f'<div class="mini" id="minix">{dm}<span class="ml">Runners on 2nd & 3rd</span></div>', cls="layer", style="z-index:13")
pop("#minix", S2 + 0.1, 12)
move("dm", PM, "h", "1", ARR - 0.45, 0.45, new=True)
c.clip("mini2", ARR, A2B - 0.02, '<div class="rs yl" id="m2x" style="top:900px">+1 free baserunner</div>', cls="layer", style="z-index:13"); pop("#m2x", ARR, 10)
c.clip("path", A2B, A2C - 0.02, f"""<div class="fork" id="fkx"><span class="fh">The manager's choice</span>
  <div class="fr" id="fr1"><i>1</i><b>Pitch to the star hitter</b></div>
  <div class="fr" id="fr2"><i>2</i><b>Walk the star · <em>face the next hitter</em></b></div></div>""", cls="layer", style="z-index:13")
c.ft("#fkx", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.22, ease="power3.out"), A2B)
pop("#fr1", A2B + 0.08, 12); pop("#fr2", A2B + 0.16, 12)
TI = W("target", "isn't")
c.to("#fr1", o(opacity=0.38, duration=0.2), TI); c.to("#fr1 b", o(textDecoration="line-through", duration=0.01), TI)
c.to("#fr2", o(borderColor=HOT, scale=1.03, duration=0.2, ease="back.out(2)"), TI)
punch("pa", W("target", "hitter") - 0.05, S3 - 0.02, "Avoid one hitter.", 1270)
punch("pb", W("target", "matchup") - 0.05, S3 - 0.02, "<em>Face another.</em>", 1380)
pinl("pnx", A2C + 0.15, S3 - 0.02, "Next hitter", "next", "yl")
c.clip("dim", A2B, A2C, '<div class="dim" id="dimx"></div>', cls="layer", style="z-index:3"); c.ft("#dimx", o(opacity=0), o(opacity=1, duration=0.2), A2B)

# ----------------------------------------------------------------- 3 the backfire
c.clip("ttl", B2 + 0.1, B3 - 0.02, f'<div class="hk big" id="ttlx"><span class="hl"><span class="hw" id="tw0">2024</span> <span class="hw acc" id="tw1">NLCS</span></span></div>', cls="layer", style="z-index:12")
for i, t_ in enumerate([W("nlcs", "twenty"), W("nlcs", "n")]):
    c.ft(f"#tw{i}", o(opacity=0, scale=1.4, filter="blur(12px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.18, ease="power3.out"), t_ - 0.03)
c.clip("ttl2", W("nlcs", "c") - 0.1, B3 - 0.02, '<div class="gm" id="gmx"><b>Game 2</b><span>2nd inning · 2 outs · Mets lead 2–0 · runners on 2nd & 3rd</span></div>', cls="layer", style="z-index:12")
pop("#gmx", W("nlcs", "c") - 0.1, 12)
c.clip("rec", B2 + 0.1, T4 - 0.02, '<div class="rec">Illustrative 3D reenactment · not game footage</div>', cls="layer", style="z-index:16")
c.clip("bnr", B3, T4 - 0.02, '<div class="bnr" id="bnrx"><b>2024 NLCS</b><span>Game 2</span></div>', cls="layer", style="z-index:16"); pop("#bnrx", B3, 8)
punch("pc", W("nlcs", "intentionally") - 0.05, B4 - 0.02, "Intentional walk", 1400)         # off while Vientos bats (his pin sits there)
punch("pc2", W("nlcs", "grand") - 0.03, T4 - 0.02, "Intentional walk<br><em>→ Grand slam</em>", 1400)
pinl("pli", B3B + 0.2, B4 - 0.02, "Lindor", "lindor")
pinl("pvi", W("nlcs", "mark") - 0.05, B5 - 0.02, "Vientos", "vientos", "yl")
tag("tbl", W("nlcs", "next") - 0.05, 13.65, "wh", "Bases loaded · 2 outs", 560)
tag("tfb", 13.68, B6 - 0.02, "wh", "95 mph fastball", 560)
tag("tft", LAND, T4 - 0.02, "yl", "391 ft (Statcast projected)", 560)

# ----------------------------------------------------------------- 4 the analytics: two situations
da, PA = diamond("da", 330, "23")
db, PB = diamond("db", 330, "12")
c.clip("tac", T4, S5, f"""<div class="tac" id="tacx"></div>
  <div class="sit" id="sa"><span class="sk"><i>A</i>First base open</span>{da}<span class="so">1 out</span>
    <span class="sl2">At bat: <b class="yl">★ dangerous hitter</b></span><span class="sl2">On deck: <b>weaker hitter</b></span>
    <span class="sv yl" id="sav">Walk sets up a force at every base</span></div>
  <div class="sit r" id="sb"><span class="sk"><i>B</i>Bases already crowded</span>{db}<span class="so">1 out</span>
    <span class="sl2">At bat: <b class="yl">★ dangerous hitter</b></span><span class="sl2">On deck: <b>another good hitter</b></span>
    <span class="sv hot" id="sbv">Walk loads the bases: more ways to score</span></div>""", cls="layer", style="z-index:11")
c.ft("#tacx", o(opacity=0), o(opacity=1, duration=0.25), T4)
TA, TB = W("gamble", "avoid") - 0.02, W("gamble", "but") - 0.02
c.ft("#sa", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.3, ease="power3.out"), TA)
c.ft("#sb", o(opacity=0, x=40), o(opacity=1, x=0, duration=0.3, ease="power3.out"), TB)
WA = W("gamble", "hitter") + 0.05; move("da", PA, "h", "1", WA, new=True)
c.ft("#sav", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.25), WA + 0.45)
WB = W("gamble", "runners") - 0.1                                  # forced: 2nd to 3rd, 1st to 2nd, the batter to 1st
move("db", PB, "2", "3", WB); move("db", PB, "1", "2", WB); move("db", PB, "h", "1", WB, new=True)
c.ft("#sbv", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.25), WB + 0.45)
punch("pe", TA, S5 - 0.02, "The matchup matters.", 1470, "sm")
punch("pf", W("analytics", "extra") - 0.05, S5 - 0.02, "<em>So do the runners and outs.</em>", 1570, "sm")
for d_ in ["da", "db"]: c.to(f"#{d_}rh", o(scale=1.35, duration=0.14, yoyo=True, repeat=3, ease="power2.inOut"), W("analytics", "extra") - 0.05)

# ----------------------------------------------------------------- 5 the verdict
STEPS = [("hitter", 0, "Hitter"), ("matchup", 0, "Next matchup"), ("outs", 0, "Outs"), ("double", 0, "Double play?")]
c.clip("steps", S5 + 0.1, SQ - 0.02, '<div class="steps">' + "".join(f'<span id="st{i}">{esc(x)}</span>' for i, (_, _, x) in enumerate(STEPS)) + "</div>", cls="layer", style="z-index:13")
for i, (w_, n_, _) in enumerate(STEPS):
    c.ft(f"#st{i}", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.2, ease="back.out(2)"), W("analytics", w_, nth=n_) - 0.04)
pinl("pss", V2 + 0.06, V3 - 0.02, "★ The star", "star")
pinl("pnn", V3 + 0.06, V4 - 0.02, "Next hitter", "next", "yl")
tag("tou", V4 + 0.1, V5 - 0.02, "wh", "1 out · runners on 2nd & 3rd · first base open", 560)
pinl("pgh", V5 + 0.1, SQ - 0.02, "+1 runner", "ghost")
tag("tdp", W("analytics", "double") - 0.05, SQ - 0.02, "yl", "Walk him → a force at every base, a double play in order", 560)
punch("pg", W("q", "walking") - 0.05, FRZ - 0.02, "Smart strategy…", 1330)
punch("ph", W("q", "actually") - 0.05, FRZ - 0.02, "<em>or big mistake?</em>", 1440)
c.clip("q", FRZ, D, '<div class="hk qq2" id="qx"><span class="hl">Would you</span><span class="hl acc">walk him?</span></div>', cls="layer", style="z-index:22")
c.ft("#qx", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), FRZ + 0.02)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -8); cue("riser-s", ZOOM, -3); cue("impact", ZOOM, -1); cue("impact", S2, -4)
for t_ in [W("hook", "why"), W("hook", "put")]: cue("tick", t_, -2)
cue("tap", W("hook", "intentionally"), -2)
for t_ in CUTS: cue("whoosh", t_, -10)
cue("popup", ARR, -5); cue("popup", TI, -7); cue("impact", W("target", "hitter") - 0.05, -9); cue("impact", W("target", "matchup") - 0.05, -7)
cue("riser-m", S3B, -5); cue("impact", W("nlcs", "twenty"), -2); cue("impact", W("nlcs", "n"), -4)
cue("tap", W("nlcs", "intentionally"), -2); cue("impact", W("nlcs", "intentionally") - 0.05, -9)
cue("whoosh", VC - 0.4, -6)                                         # the pitch on its way
CRACKS = [(VC, 1.0), (RPC, 0.4)]
cue("impact", W("nlcs", "grand") - 0.03, -1); cue("riser-s", W("nlcs", "grand") - 0.03, -8)
cue("popup", WA, -6); cue("popup", WB, -6); cue("popup", TA, -9); cue("popup", TB, -9); cue("impact", W("analytics", "extra") - 0.05, -8)
for w_, n_, _ in STEPS: cue("tick", W("analytics", w_, nth=n_), -3)
cue("tap", W("q", "walking"), -2); cue("impact", W("q", "walking") - 0.05, -9)
cue("riser-m", FRZ, -6); cue("impact", FRZ, -2); cue("tick", FRZ, -2)
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
    tt = np.arange(n) / SR                                              # the crowd: a low murmur; it erupts on the grand slam and dies under the replay
    roar = np.clip((tt - VC) / 0.5, 0, 1) * np.clip((T4 + 0.3 - tt) / 0.6, 0, 1)
    fx += crowd * (10 ** (-32 / 20) + roar[:, None] * 10 ** (-14 / 20))
    # the music bed: made for this video (lands its chord on the freeze), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, FRZ, style="pulse", seed=23)
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

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Intentional walk: smart strategy or big mistake?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--novo" not in sys.argv:
        m = mixdown()
        print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {len(CAPS)} caption phrases; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
