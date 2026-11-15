"""'Why catchers struggle with pop-ups' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the pitch, the game pop-ups and the fungoes -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

One catcher in full gear throughout (cream jersey, green gear). Game pop-ups come off a 95 mph fastball with heavy backspin and
curve as they rise and fall; the practice fungoes carry far less spin. In every play he comes up out of the crouch, pulls the
mask off with his throwing hand, turns, finds the ball, tosses the mask away from his path, gets under the ball and catches it
with the mitt up in front of his face.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
TCON = P["pitches"]["fb"]["t_contact"]
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
S = {x["id"]: round(x["t0"] - 0.08, 3) for x in TM["lines"]}
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
SHOTS = []
def shot(a, b, cam, vs, ts, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], **kw))
def vat(vs, ts, t):
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
POPS = P["pops"]
T0 = 2.0                                                             # every play: the ball leaves the bat at play time 2.0 s
K = lambda k: round(T0 + k, 4)
TC = lambda pid: POPS[pid]["t_catch"]
def play(pop, **kw): return dict(pop=pop, t0=T0, **kw)
TOPP, BOTP, FULL = [0, 0, 1080, 960], [0, 960, 1080, 960], [0, 0, 1080, 1920]
PA = play("pa", tossSide=-1); PD = play("pd", tossSide=1); PB = play("pb", tossSide=1)
PM = play("pm", misread=[2.0, 9.0], misreadK=1.25, tossSide=1); PF = play("pf", tossSide=-1, settle=0.9)
V1, V2, V3, V4 = S["d1"], S["g1"], S["p1"], S["e1"]

# ----------------------------------------------------------------- 1 the hook: the ball goes straight up; he rips the mask off and looks for it
H1 = 1.25
shot(0.0, H1, "world", [0.0, H1], [K(-0.12), K(0.9)], cp=PA, ump=[-5.5, 7.0],
     c0=[3.4, 7.2, 10.0], c1=[3.1, 7.4, 9.4], l=[0.0, 3.6, 0.0], l1=[0.2, 6.5, 2.4], f0=46, f1=54)
H2 = 2.55                                                            # in front of him, low: the mask comes off (slow motion)
shot(H1, H2, "world", [H1, H2], [K(0.2), K(0.72)], cp=PA, ump=[-5.5, 7.0], close=1, c0=[6.5, 4.0, 1.0], c1=[6.1, 4.1, 1.4], l=[0.3, 5.0, 3.0], l1=[0.4, 5.4, 3.2], f0=44)
H3 = 4.3                                                             # straight up past him: the ball against the lights, drifting
shot(H2, H3, "world", [H2, H3], [K(0.9), K(2.65)], cp=PA, ump=[-5.5, 7.0], bglow=1, btrail=[dict(pop="pa", t0=T0)],
     c0=[-4.5, 1.0, 11.0], c1=[-4.3, 0.9, 10.6], l=[1.0, 12.0, 5.0], f0=70)
shot(H3, V1, "world", [H3, V1], [K(3.2), K(5.0)], cp=PA, ump=[-5.5, 7.0], bglow=1,         # tracking him as he settles under it
     c0=[12.5, 4.5, -2.5], c1=[11.5, 4.8, 0.0], l=[6.0, 5.0, 14.0], l1=[6.5, 6.5, 15.0], f0=40)

# ----------------------------------------------------------------- 2 three pop-ups, three directions; then from above: judging it on the move
D1 = W("d1", "backstop") - 0.08; D2 = W("d1", "or") - 0.05; D3 = S["d2"]
shot(V1, D1, "world", [V1, D1], [K(3.5), K(3.5 + (D1 - V1))], cp=PD, ump=[4.0, 8.0], bglow=1, c0=[-14.0, 6.0, -26.0], c1=[-16.0, 6.5, -24.0], l=[-40.0, 6.0, 6.0], f0=44)
shot(D1, D2, "world", [D1, D2], [K(4.3), K(4.3 + (D2 - D1))], cp=PB, ump=[-5.0, 7.0], bglow=1, c0=[3.0, 6.0, 10.0], c1=[2.5, 6.4, 12.0], l=[-3.0, 7.0, 40.0], f0=44)
shot(D2, D3, "world", [D2, D3], [K(0.7), K(0.7 + (D3 - D2) * 1.0)], cp=PM, ump=[-5.0, 7.5], bglow=1, c0=[-4.0, 14.0, 44.0], c1=[-3.0, 13.0, 40.0], l=[1.0, 3.0, -10.0], f0=40)
shot(D3, V2, "world", [D3, V2], [K(0.0), K(TC("pm") + 0.3)], cp=PM, ump=[-5.0, 7.5], track=dict(ring=1), cpath=1, bglow=1,
     c0=[2.0, 105.0, 24.0], c1=[2.0, 98.0, 22.0], l=[1.5, 0.0, -4.0], f0=34, near=5.0)

# ----------------------------------------------------------------- 3 the gear, the obstacles, getting under it (the opening pop-up again)
G1 = W("g1", "avoid") - 0.1; G2 = W("g1", "and") - 0.1
shot(V2, G1, "world", [V2, G1], [K(0.12), K(0.78)], cp=PA, ump=[-5.5, 7.0], close=1, c0=[4.6, 4.4, -3.2], c1=[4.3, 4.4, -2.8], l=[0.3, 3.4, 3.0], f0=44)
shot(G1, G2, "world", [G1, G2], [K(0.6), K(0.6 + (G2 - G1))], cp=PA, ump=[-5.5, 7.0], c0=[-6.0, 12.0, -10.0], c1=[-6.5, 12.5, -9.0], l=[1.5, 1.5, 4.5], f0=46)
G3 = W("g1", "underneath") - 0.05
shot(G2, V3, "world", [G2, G3, V3], [K(3.0), K(4.6), K(TC("pa") + 0.55)], cp=PA, ump=[-5.5, 7.0], track=dict(ring=1), bglow=1,
     close=1, c0=[-2.5, 2.2, 8.0], c1=[-1.6, 2.3, 8.8], l=[6.8, 9.5, 16.5], f0=56)

# ----------------------------------------------------------------- 4 practice (day): a coach's fungoes; every one different; then game vs. practice
PR1 = W("p2", "every") - 0.06; PR2 = W("p2", "different") - 0.05; PR3 = S["p3"]; PR4 = S["p4"]
F1 = play("f1", tossSide=1)
shot(V3, PR1, "world", [V3, PR1], [K(-0.6), K(-0.6 + (PR1 - V3))], day=1, cp=F1, coach=dict(hits=[T0]), bglow=1, batter=False,
     c0=[14.0, 30.0, 46.0], c1=[12.0, 26.0, 40.0], l=[-6.0, 10.0, 0.0], f0=48)
shot(PR1, PR2, "world", [PR1, PR2], [K(3.4), K(3.4 + (PR2 - PR1))], day=1, cp=play("f2", tossSide=-1), coach=dict(hits=[T0]), batter=False, bglow=1,
     c0=[0.0, 5.0, 8.0], c1=[0.5, 5.5, 10.0], l=[22.0, 9.0, 34.0], f0=44)
shot(PR2, PR3, "world", [PR2, PR3], [K(3.6), K(3.6 + (PR3 - PR2))], day=1, cp=play("f4", tossSide=1), coach=dict(hits=[T0]), batter=False, bglow=1,
     c0=[8.0, 5.5, 12.0], c1=[7.0, 6.0, 11.0], l=[-12.0, 7.0, -26.0], f0=44)
MULTI = [dict(pop=f"f{i}", t0=T0 + 0.45 * (i - 1)) for i in range(1, 7)]
shot(PR3, PR4, "world", [PR3, PR4], [K(-0.2), K(-0.2 + (PR4 - PR3) * 2.2)], day=1, cp=play("f5", tossSide=1), coach=dict(hits=[m["t0"] for m in MULTI]), batter=False, multi=MULTI,
     c0=[-3.0, 175.0, 10.0], c1=[-3.0, 165.0, 9.0], l=[-3.0, 0.0, 2.0], f0=48, near=10.0)
SIDEC = dict(c0=[-265.0, 88.0, 16.0], c1=[-258.0, 88.0, 16.0], l=[0.0, 86.0, 16.0], f0=48, near=5.0)
shot(PR4, V4, "world", [PR4, V4], [K(0.0), K(0.0 + (V4 - PR4) * 2.4)], panes=[
    dict(rect=TOPP, cp=play("pb", tossSide=1), btrail=[dict(pop="pb", t0=T0)], bglow=1, ump=[-5.0, 7.0]),
    dict(rect=BOTP, day=1, cp=play("f7", tossSide=1), btrail=[dict(pop="f7", t0=T0, c="#56d1ff")], coach=dict(hits=[T0]), batter=False, bglow=1)], **SIDEC)

# ----------------------------------------------------------------- 5 the payoff: back to the wall, the catch in slow motion
E1 = S["e2"]; E2 = W("e2", "making") - 0.08; E3 = W("e2", "seconds", end=True) + 0.4
shot(V4, E1, "world", [V4, E1], [K(3.0), K(3.0 + (E1 - V4))], cp=PF, ump=[-5.0, 7.0], bglow=1, c0=[9.0, 13.0, 54.6], c1=[9.4, 12.6, 54.4], l=[5.0, 5.0, 30.0], f0=44)
shot(E1, E2, "world", [E1, E2], [K(TC("pf") - 1.35), K(TC("pf") - 0.3)], cp=PF, ump=[-5.0, 7.0], bglow=1, c0=[-10.0, 5.0, 36.0], c1=[-8.0, 5.2, 40.0], l=[10.0, 7.0, 45.0], f0=40)
shot(E2, E3, "world", [E2, E2 + 0.9, E3], [K(TC("pf") - 0.3), K(TC("pf")), K(TC("pf") + 0.12)], cp=PF, ump=[-5.0, 7.0], close=1,
     c0=[14.2, 6.8, 43.6], c1=[13.9, 6.7, 43.9], l=[11.2, 6.0, 47.0], f0=32)
shot(E3, D, "world", [E3, D], [K(TC("pf") + 0.12), K(TC("pf") + 0.12 + (D - E3) * 0.35)], cp=PF, ump=[-5.0, 7.0], c0=[0.0, 6.0, 30.0], c1=[1.5, 6.5, 33.0], l=[10.0, 4.5, 46.0], f0=44)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

# ----------------------------------------------------------------- overlays
c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in CUTS:
    c.set("#flash", '{"opacity":0.3}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)
def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls="", pane=0):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, pane])
def title(tid, t0, t1, lines, top, cls="band"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{(" " + acc) if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.05 * i)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def plab(pid, t0, t1, top, cls, html):
    c.clip(pid, t0, t1, f'<div class="plb {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:16"); pop(f"#{pid}x", t0, 10)
BAND = 1650

# 1 the hook
title("t1", 0.0, H2 - 0.15, [("Why is this", ""), ("so hard?", "yl")], 300, "big")
# 2 three directions
chip("c2a", W("d1", "dugout") - 0.05, D1 - 0.02, "Toward the dugout", 1460, "big")
chip("c2b", D1 + 0.02, D2 - 0.02, "Toward the backstop", 1460, "big")
chip("c2c", W("d1", "mound") - 0.08, D3 - 0.02, "Toward the mound", 1460, "big")
pinl("p2a", W("d2", "judge") - 0.05, V2 - 0.05, "First read: back", "misread", "wh sm")
pinl("p2b", W("d2", "direction") + 0.3, V2 - 0.05, "It drifts toward the mound", "catch", "yl sm")
# 3 the gear, the obstacles, under the ball
pinl("p3a", W("g1", "gear") - 0.05, G1 - 0.02, "Mask", "mask", "wh sm")
pinl("p3b", W("g1", "gear") + 0.12, G1 - 0.02, "Chest protector", "chest", "wh sm")
pinl("p3c", W("g1", "gear") + 0.24, G1 - 0.02, "Shin guards", "shin", "wh sm")
pinl("p3d", W("g1", "obstacles") - 0.1, G2 - 0.02, "Umpire", "ump", "sm")
pinl("p3e", W("g1", "obstacles") + 0.05, G2 - 0.02, "Bat", "bat", "sm")
pinl("p3f", W("g1", "obstacles") + 0.2, G2 - 0.02, "Plate", "plate", "sm")
pinl("p3g", G3 - 0.05, V3 - 0.05, "Under the ball", "catch", "yl sm")
# 4 practice
title("t4", W("p1", "difficult") - 0.05, PR1 - 0.02, [("Hard to", ""), ("practice", "yl")], 1560, "band")
chip("c4a", PR3 + 0.1, PR4 - 0.02, "6 pop-ups · 6 different spots", 1500, "")
plab("l4a", PR4 + 0.02, V4 - 0.02, 30, "", 'Game pop-up <b>· heavy backspin</b>')
plab("l4b", PR4 + 0.06, V4 - 0.02, 1840, "cy", 'Practice fungo <b>· far less spin</b>')
c.clip("sm4", PR4, V4, '<div class="hseam"></div>', cls="layer", style="z-index:11")
chip("c4c", W("p4", "recreate") - 0.05, V4 - 0.02, "The path bends", 800, "yl")
chip("c4d", W("p4", "recreate") + 0.15, V4 - 0.02, "A plainer arc", 1760, "cy")
# 5 the payoff
for i, (wd, txt) in enumerate([("finding", "Find it"), ("getting", "Get under it"), ("making", "Make the play")]):
    chip(f"c5{i}", W("e2", wd) - 0.05, E3 - 0.05, f'<i>{i + 1}</i>{txt}', 330 + 104 * i, "step")
title("t5", E3, D, [("It's harder", ""), ("than it looks.", "yl")], 560, "big")
VBRAND = round(E3 + 1.2, 3)

# ----------------------------------------------------------------- captions: the voiceover, word by word
A_ = "acc"
CAPS = [("h1", 0, 2, {2: A_}), ("h1", 3, 9, {8: A_}), ("h1", 10, 12, {12: A_}),
        ("d1", 0, 3, {3: A_}), ("d1", 4, 6, {6: A_}), ("d1", 7, 7, {7: A_}), ("d1", 8, 12, {12: A_}),
        ("d2", 0, 3, {1: A_}), ("d2", 4, 6, {4: A_, 6: A_}), ("d2", 7, 11, {8: A_}),
        ("g1", 0, 7, {7: A_}), ("g1", 8, 9, {9: A_}), ("g1", 10, 15, {11: A_, 13: A_}),
        ("p1", 0, 6, {3: A_}), ("p1", 7, 13, {10: A_, 11: A_, 13: A_}),
        ("p2", 0, 3, {1: A_, 3: A_}),
        ("p3", 0, 3, {3: A_}), ("p3", 4, 7, {6: A_}), ("p3", 8, 14, {13: A_, 14: A_}),
        ("p4", 0, 3, {1: A_, 3: A_}), ("p4", 4, 8, {5: A_}),
        ("e1", 0, 3, {3: A_}), ("e1", 4, 9, {5: A_}),
        ("e2", 0, 3, {2: A_}), ("e2", 4, 6, {4: A_}), ("e2", 7, 12, {8: A_, 12: A_})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]; i1 = min(i1, len(wd) - 1)
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, E3 - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"]; w = w.rstrip(",:") if n == i1 and i1 > i0 else w
        w = w.replace("'", "’")
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" id="{cid}c"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="96" height="96"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.4, ease="power3.out"), VBRAND)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -14)
cue("impact", 0.04, -5)
for tt in [W("d1", "dugout") - 0.05, D1, W("d1", "mound") - 0.08, W("p1", "difficult") - 0.05, PR3 + 0.1, E3]: cue("impact", tt, -8)
for tt in [W("g1", "gear") - 0.05, W("g1", "obstacles") - 0.1, G3, W("e2", "finding") - 0.05, W("e2", "getting") - 0.05, W("e2", "making") - 0.05]: cue("tick", tt, -6)
CRACKS = []
def pv(sh, t):                                                      # video time of play time t in a shot (its first pane's clock)
    p = sh["panes"][0] if "panes" in sh else sh
    v = vat(p.get("vs", sh["vs"]), p.get("ts", sh["ts"]), t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
for sh in SHOTS:
    p_ = sh["panes"][0] if "panes" in sh else sh
    cp = p_.get("cp")
    if not cp: continue
    v = pv(sh, cp["t0"])
    if v is not None:
        if p_.get("day") or sh.get("day"): cue("tap", v, -2)        # a fungo: a lighter knock
        else: CRACKS.append((v, False))
    v = pv(sh, cp["t0"] + TC(cp["pop"])); cue("glove", v, 0)      # into the mitt
cue("riser-m", VBRAND - 1.0, -12); cue("impact", VBRAND, -8)

LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}
def crack(rng, slow=False):
    """Maple bat on a ball: a hard broadband click and a short wooden ring (lower and longer in slow motion)."""
    k = 0.55 if slow else 1.0
    t = np.arange(int((1.2 if slow else 0.6) * SR)) / SR
    click = rng.standard_normal(len(t)) * np.exp(-t / (0.0025 / k))
    ring = sum(a * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) * np.exp(-t / (d / k)) for f, a, d in [(1150, .55, .05), (1720, .4, .035), (2380, .3, .025), (640, .3, .07)])
    x = click * 0.9 + ring + np.sin(2 * np.pi * 180 * k * t) * np.exp(-t / (0.03 / k)) * 0.5
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
    rng = np.random.default_rng(9)
    for vt_, sp in CRACKS:
        x = crack(rng, sp); i = int(vt_ * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * 10 ** (-4 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-26 / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=57)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 3.0, 0.5, 1.0)[:, None]
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]; vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
    env = np.convolve(np.abs(vo).mean(1), np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
    duck = 10 ** (-7 * np.clip(env / 0.05, 0, 1) / 20)
    duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), "same")
    music = bed * ramp * duck[:, None] * 10 ** (-17 / 20)
    full = (fx + music) * 10 ** (-6 / 20) + vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, (fx + bed * ramp * 10 ** (-17 / 20)) * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=pfx)
    os.remove(pre); os.remove(pfx)
    return m

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
MONO = 'font-family:"Plex Mono", monospace; font-weight:500; text-transform:uppercase;'
BC = 'font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase;'
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:560px; background:linear-gradient(180deg, rgba(3,6,12,.6), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:620px; background:linear-gradient(0deg, rgba(3,6,12,.7) 0%, rgba(3,6,12,.3) 55%, rgba(3,6,12,0) 100%); }}
.flash {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.spd {{ position:absolute; right:40px; top:1856px; display:inline-flex; align-items:center; gap:10px; padding:6px 14px; border-radius:8px; background:rgba(6,10,18,.72); {MONO} font-size:20px; letter-spacing:.14em; color:{Y}; opacity:0; }}
.spd::before {{ content:""; width:10px; height:10px; border-radius:50%; background:currentColor; }}
.hseam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.85); box-shadow:0 0 18px rgba(0,0,0,.6); }}

.cap {{ position:absolute; left:52px; right:52px; top:118px; text-align:center; }}
.cap .cl {{ display:block; {BC} font-size:74px; line-height:.98; color:#fff; text-shadow:0 6px 28px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.75); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{Y}; }}

.ttl {{ position:absolute; left:40px; right:40px; display:grid; justify-items:center; text-align:center; {BC} font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.6); }}
.ttl .tl {{ display:block; }} .ttl .tw {{ display:inline-block; }}
.ttl .acc {{ color:{HOT}; }} .ttl .yl {{ color:{Y}; }} .ttl .cy {{ color:{CYAN}; }} .ttl .or {{ color:{HOT}; }}
.ttl.big {{ font-size:150px; }} .ttl.mid {{ font-size:112px; left:0; right:0; padding:18px 30px 24px; background:rgba(5,8,13,.86); }}
.ttl.band {{ left:0; right:0; padding:18px 30px 22px; background:rgba(5,8,13,.86); font-size:86px; line-height:.98; }}

.plb {{ position:absolute; left:50%; transform:translateX(-50%); padding:4px 18px; border-radius:12px; background:rgba(6,10,18,.88); border:3px solid {CYAN}; {BC} font-size:44px; line-height:1.0; color:{CYAN}; white-space:nowrap; }}
.plb.or {{ border-color:{HOT}; color:{HOT}; }} .plb b {{ color:#fff; font-weight:700; }}
.chip {{ position:absolute; left:50%; transform:translateX(-50%); padding:12px 26px; border-radius:14px; background:rgba(6,10,18,.88); {BC} font-size:60px; white-space:nowrap; }}
.chip.big {{ font-size:78px; padding:8px 30px; color:{Y}; }} .chip.yl {{ color:{Y}; }} .chip.cy {{ color:{CYAN}; }}
.chip.step {{ left:60px; transform:none; display:flex; align-items:center; gap:18px; font-size:64px; padding:8px 26px 8px 10px; }}
.chip.step i {{ display:grid; place-items:center; width:66px; height:66px; border-radius:10px; background:{Y}; color:#05080d; font-style:normal; }}
.chip .cyt {{ color:{CYAN}; }} .chip .yt {{ color:{Y}; }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:24px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; {BC} font-size:46px; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.pin.sm span {{ font-size:38px; padding:6px 14px; }}
.pin.cy span {{ background:{CYAN}; }} .pin.yl span {{ background:{Y}; }} .pin.wh span {{ background:{WHITE}; }}

.brand {{ position:absolute; left:0; right:0; top:1640px; display:flex; justify-content:center; align-items:center; gap:22px; }}
.bname {{ display:grid; justify-items:center; {BC} line-height:.9; }} .bname span {{ font-size:54px; color:#fff; }} .bname em {{ font-style:normal; font-size:66px; color:{HOT}; letter-spacing:.02em; }}
"""])

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [(0.0, V1, "The hook", "A pop-up straight up behind the plate: from behind him, his head snaps up; in front of him, the mask comes off; straight up past him at the ball against the lights; tracking him as he settles under it", "WHY IS THIS SO HARD?"),
          (V1, V2, "Three directions", "One pop-up drifting toward the third-base dugout, one carrying back to the backstop, one that goes up and curls toward the mound; then from above: his first read is back, the ball comes down in front, and he has to turn and go", "TOWARD THE DUGOUT / BACKSTOP / MOUND"),
          (V2, V3, "Gear and obstacles", "Close on the mask coming off (mask, chest protector, shin guards); from above the plate: the umpire, the bat, the plate; low behind him as he gets under the ball and catches it", "pins only"),
          (V3, V4, "Hard to practice", "A day practice: a coach hits fungo pop-ups; quick cuts of the catcher chasing them to different places; six fungoes from above, each landing somewhere new; a game pop-up against a fungo, side by side", "HARD TO PRACTICE / 6 POP-UPS, 6 DIFFERENT SPOTS"),
          (V4, D, "The payoff", "A pop-up back toward the wall: through the net, he comes back under it; slow motion as the ball goes into the mitt; Baseball Decoded", "FIND IT / GET UNDER IT / MAKE THE PLAY / IT'S HARDER THAN IT LOOKS.")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Why catchers struggle with pop-ups", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Voiceover cues", "", f"The video is {D:.1f} s. To record your own read over `assets/mix-novo.wav`, start each line at its time (seconds).", "",
             "| Start | End | Scene | Line |", "|---|---|---|---|"]
    for a, b, name, desc, _ in SCENES:
        for ln in TM["lines"]:
            if a - 0.01 <= ln["t0"] + 0.08 < b: lines.append(f"| {ln['t0']:.2f} | {ln['t1']:.2f} | {name} | {ln['text']} |")
    lines += ["", "## Scenes", "", "| From | To | Scene | Shots | On screen |", "|---|---|---|---|---|"] + [f"| {a:.2f} | {b:.2f} | {n} | {d} | {t} |" for a, b, n, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
