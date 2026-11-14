"""JT Builds: 'The hardest app to build' (1080x1920), cut to the voiceover.

    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/marketplace.mp4 --video-bitrate 16M

A two-sided marketplace needs both of its sides at once. Customers are ivory and the supply side (drivers, restaurants,
detailers) is amber, everywhere: in the studio, in the city, on the map and in every app screen. The 3D lives in assets/js/
(core: renderer, people, phone, car; ui: the app screens; one module per set). Shots and controls are keyed to the words.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
S = {x["id"]: round(x["t0"] - 0.08, 3) for x in TM["lines"]}
E = {x["id"]: x["t1"] for x in TM["lines"]}
WHITE, GREY, MUTED, AMBER, INK, BG = "#F7F6F4", "#A09D9B", "#8A8580", "#FFB547", "#1A1206", "#121110"

# ----------------------------------------------------------------- shots: video time [a, b), the set, the camera, and the set's controls
SHOTS = []
def shot(a, b, set_, t0=None, rate=1.0, **kw):
    """The set's local clock starts at t0 (default: video time) and runs at `rate`."""
    t0 = a if t0 is None else t0
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), set=set_, vs=[round(a, 4), round(b, 4)], ts=[round(t0, 4), round(t0 + (b - a) * rate, 4)], **kw))

# 1 the hook: "The hardest app to build isn't necessarily the one with the most complicated code. It's the one that needs two
#   completely different groups of people to succeed."  A giant phone in a dark studio; code, then an empty marketplace; two crowds.
V1 = S["u1"]
H1 = W("h1", "necessarily") - 0.05
H2 = S["h2"]
TEMPTY = W("h1", "complicated") + 0.25
shot(0.0, H1, "stage", ui="code", tEmpty=TEMPTY, lit=0.2, ease="out", c0=[0.0, 0.8, 19.0], c1=[0.0, 1.3, 11.5], l=[0.0, 4.2, 0.0], l1=[0.0, 4.6, 0.0], f0=54, f1=50)
shot(H1, H2, "stage", ui="code", tEmpty=TEMPTY, lit=0.2, c0=[3.4, 5.4, 9.6], c1=[1.0, 4.9, 8.4], l=[0.0, 4.9, 0.0], f0=44)
TRY = [round(W("h2", "people") + 0.12 * k, 3) for k in range(8)]
DIVE = V1 - 0.42
shot(H2, DIVE, "stage", ui="empty", tA=W("h2", "two"), tB=W("h2", "different"), tTry=TRY, c0=[0.0, 7.0, 17.5], c1=[0.0, 4.6, 15.2], l=[0.0, 4.5, 0.0], f0=50)
# the camera dives into the phone's map...
shot(DIVE, V1, "stage", ui="empty", lit=1, tTry=TRY, ease="in", c0=[0.0, 4.6, 15.2], c1=[0.0, 6.72, 1.5], l=[0.0, 4.5, 0.0], l1=[0.0, 6.72, 0.0], f0=50)

# 2 the ride: "And this is a problem companies like Uber and DoorDash had to solve. Think about it. Customers won't use Uber if
#   there are no drivers. And drivers won't join Uber if there are no customers."   ...and comes out over a real city.
V2 = S["d1"]
U2 = S["u2"]
shot(V1, U2, "city", mode="kerb", fog=0.0012, traffic=0.25, ease="out", c0=[8.0, 420.0, 22.0], c1=[20.0, 9.0, 46.0], l=[8.0, 0.0, 21.0], l1=[8.0, 1.6, 21.0], f0=46, f1=40, r0=0.5, r1=0.0)
U3 = W("u3", "won't") - 0.05
shot(U2, U3, "city", mode="kerb", fog=0.006, traffic=0.0, c0=[13.5, 1.5, 28.5], c1=[12.6, 1.5, 27.6], l=[8.0, 1.25, 21.0], f0=34)
U4 = S["u4"]
PCAM = dict(c0=[9.5, 1.62, 24.0], c1=[9.52, 1.62, 24.03], l=[60.0, 5.0, 40.0], f0=30, fog=0.01, pd=0.37, pry=-0.12, prx=0.03, py=0.013)
shot(U3, U4, "city", mode="phone", ui="ride", none=[W("u3", "no") - 0.1, W("u3", "no") + 0.25], traffic=0.0, **PCAM)
U5 = W("u4", "join") + 0.25
shot(U4, U5, "city", mode="drivers", fog=0.006, traffic=0.0, c0=[112.0, 1.7, 34.5], c1=[113.5, 1.7, 33.6], l=[124.5, 1.3, 24.6], f0=38)
U6 = E["u4"] + 0.62
REQ = E["u4"] + 0.05
shot(U5, U6, "city", mode="phone", ui="driver", req=[REQ, REQ + 0.3], acc=[REQ + 0.38, REQ + 0.55], traffic=0.0, **dict(PCAM, c0=[119.0, 1.62, 27.0], c1=[119.02, 1.62, 27.03], l=[160.0, 5.0, 60.0]))
# the two sides connect: a link from the driver to the rider, and the car pulls up
shot(U6, V2, "city", mode="match", fog=0.004, traffic=0.3, link=[U6, U6 + 0.5], linkR=0.09, go=U6 - 2.2, goDur=3.0, riderUp=U6 - 0.3, c0=[-9.0, 14.0, 23.5], c1=[-5.0, 11.0, 23.2], l=[30.0, 0.0, 24.5], f0=50)

# 3 the delivery: "It's the same problem with DoorDash. No restaurants means no customers, and no customers means no reason
#   for restaurants to join."   A kitchen with food ready and no orders; an app with nothing to order; then they connect.
V3 = S["s1"]
K2 = S["d2"]
shot(V2, K2, "kitchen", c0=[0.5, 1.5, 4.3], c1=[0.15, 1.62, 3.7], l=[0.0, 1.72, 0.0], f0=46)
K3 = W("d2", "and") - 0.06
shot(K2, K3, "city", mode="phone", ui="food", traffic=0.0, **dict(PCAM, c0=[-9.5, 1.62, 24.0], c1=[-9.52, 1.62, 24.03], l=[-60.0, 5.0, 40.0], pry=0.12))
K4 = E["d2"] + 0.62
ORD = E["d2"] + 0.06
shot(K3, K4, "kitchen", fill=[ORD, ORD + 0.5], c0=[0.75, 1.75, 3.0], c1=[0.3, 2.0, 2.45], l=[0.05, 2.05, -0.3], f0=42)
# restaurants, customers and couriers, linked across the city; the camera lifts off...
S2_ = S["s2"]
shot(K4, S2_, "city", mode="net", fog=0.0011, traffic=0.7, net=dict(c=[0, 0], ph=[[K4 - 0.25, K4 + 0.9, 0, 210]], dens=0.75, r=0.55), ease="in", c0=[-110.0, 120.0, 170.0], c1=[-150.0, 330.0, 190.0], l=[0.0, 20.0, 0.0], f0=48)

# 4 the answer: "So how did they solve it? They didn't try to take over the entire country on day one. They focused on one city,
#   built up enough supply and demand to make the platform useful, proved the model worked, and then expanded into new markets."
V5 = S["k1"]
HOME = [-20.87, 0.66, 0.23]                                            # San Francisco on the map (assets/js/usmap.js)
ONE = W("s3", "one") - 0.05
M2 = S["s3"]
shot(S2_, M2, "usmap", flick=W("s2", "entire") - 0.15, one=ONE, ease="out", c0=[-46.0, 44.0, 2.5], c1=[-37.0, 35.0, 2.0], l=[2.0, 0.0, 1.0], f0=56)
M3 = W("s3", "built") - 0.06
shot(M2, M3, "usmap", one=ONE, ease="in", c0=[-37.0, 35.0, 2.0], c1=[HOME[0] - 4.0, 5.0, HOME[2] + 1.6], l=[2.0, 0.0, 1.0], l1=HOME, f0=56, f1=40)
M4 = W("s3", "and", nth=1) - 0.08
BLD = M3
shot(M3, M4, "city", mode="net", fog=0.001, traffic=0.8, net=dict(c=[0, 0], ph=[[BLD - 0.1, W("s3", "to") , 0, 150], [W("s3", "to"), W("s3", "proved") + 0.3, 150, 300]], dens=1.0, r=0.6),
     c0=[150.0, 300.0, 250.0], c1=[60.0, 130.0, 180.0], l=[0.0, 0.0, 0.0], l1=[0.0, 20.0, 0.0], f0=48)
shot(M4, V5, "usmap", spread=[M4 + 0.1, V5 - 0.25], ease="out", c0=[HOME[0] - 7.0, 8.0, HOME[2] + 2.5], c1=[-38.0, 36.0, 2.0], l=HOME, l1=[2.0, 0.0, 1.0], f0=46, f1=56)

# 5 DetailDash: "Now think about an app like DetailDash. It's essentially DoorDash for car detailing. It connects people who
#   want their cars detailed with detailers who want more customers."
V6 = S["c1"]
BCAM = dict(c0=[2.9, 1.45, 5.4], c1=[2.7, 1.45, 5.2], l=[-0.6, 1.0, 0.2], f0=30, pd=0.37, py=0.013)
B2 = S["k2"]
shot(V5, B2, "bay", mode="phone", ui="dd", rise=V5, show=[V5 + 0.25, V5 + 1.3], **BCAM)
B3 = S["k3"]
TAP = W("k2", "detailing") + 0.1
shot(B2, B3, "bay", mode="phone", ui="dd", scroll=[B2 + 0.1, B2 + 0.9], tap=[TAP, TAP + 0.3], booked=[TAP + 0.2, TAP + 0.4], **dict(BCAM, c0=[-3.2, 1.5, 5.0], c1=[-3.0, 1.5, 4.8], l=[0.4, 1.0, 0.0], pd=0.36, pry=0.14))
B4 = W("k3", "with") - 0.06
shot(B3, B4, "bay", mode="wide", custUp=W("k3", "cars"), c0=[3.6, 1.9, 9.0], c1=[3.0, 1.75, 8.2], l=[0.0, 0.95, 0.6], f0=44)
B5 = W("k3", "more") - 0.02
shot(B4, B5, "bay", mode="wide", c0=[-3.0, 1.05, -2.6], c1=[-2.7, 1.1, -2.35], l=[-1.5, 1.1, 0.9], f0=40)
NOTE = B5 + 0.05
shot(B5, V6, "bay", mode="phone", ui="pro", note=[NOTE, NOTE + 0.5], **dict(BCAM, c0=[-2.7, 1.3, -2.35], c1=[-2.68, 1.3, -2.33], l=[-1.5, 1.2, 0.9], pry=-0.1))

# 6 the challenge: "But building the app is only half the battle. You need enough detailers in an area to attract customers,
#   and enough customers to make joining worthwhile for detailers."   Back in the studio: the app is built, and both sides are empty.
V7 = S["e1"]
T2 = S["c2"]
shot(V6, T2, "stage", ui="dd", sup=[1e6, 1e6 + 1], dem=[1e6, 1e6 + 1], lit=0.15, c0=[2.2, 3.6, 9.6], c1=[0.5, 3.2, 8.0], l=[0.0, 2.9, 0.0], f0=44)
TB, TA = W("c2", "detailers"), W("c2", "enough", nth=1)
CH = dict(ui="dd", tB=TB - 0.1, tA=TA - 0.1, sup=[TB, TB + 1.0], dem=[TA, TA + 0.9], link=[W("c2", "make") - 0.1, E["c2"] + 0.35])
T3 = W("c2", "and") - 0.06
shot(T2, T3, "stage", **CH, c0=[0.0, 3.2, 16.8], c1=[0.0, 4.2, 15.2], l=[0.0, 4.4, 0.0], f0=50)
shot(T3, V7, "stage", **CH, c0=[-5.2, 2.0, 11.5], c1=[-3.6, 2.6, 12.6], l=[0.4, 4.2, 0.5], f0=50)

# 7 the close: "That's why the smartest way to build a marketplace isn't to launch everywhere. It's to dominate one market
#   first. Then expand."
E2_, E3_ = S["e2"], S["e3"]
END1 = E["e3"] + 1.0
NB = [0, 0]
shot(V7, E2_, "city", mode="net", fog=0.001, traffic=0.6, net=dict(c=NB, thin=[V7 + 0.1, W("e1", "isn't") - 0.1], sz=2.4), c0=[40.0, 380.0, 330.0], c1=[20.0, 330.0, 280.0], l=[0.0, 0.0, 10.0], f0=50)
NET7 = dict(c=NB, ph=[[E2_ - 0.05, E3_ - 0.25, 0, 110], [E3_ + 0.05, END1 + 0.6, 110, 420]], dens=1.0, r=0.8, sz=1.5)
shot(E2_, E3_, "city", mode="net", fog=0.001, traffic=0.6, net=NET7, c0=[20.0, 330.0, 280.0], c1=[60.0, 150.0, 190.0], l=[0.0, 0.0, 10.0], f0=50)
shot(E3_, END1, "city", mode="net", fog=0.001, traffic=0.8, net=NET7, c0=[60.0, 150.0, 190.0], c1=[30.0, 360.0, 330.0], l=[0.0, 0.0, 10.0], f0=50)
# the phone, over the city that is now lit
shot(END1, D, "city", mode="phone", ui="ddmap", fog=0.001, traffic=0.8, net=dict(c=NB, ph=[[-10, -9, 0, 500]], dens=1.0, r=0.8, sz=1.5), c0=[30.0, 360.0, 330.0], c1=[34.0, 372.0, 342.0], l=[0.0, 0.0, 10.0], f0=50, pd=0.3, py=-0.008, pry=0.0, prx=0.0, rise=END1)

for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

# ----------------------------------------------------------------- the page
c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("grade", 0, D, '<div class="vig"></div>', cls="layer", style="z-index:2")

def title(tid, t0, t1, lines, top, cls=""):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    return k

# the hook title: on screen from the first frame, landing word by word with the voice
hk = LN("h1")["words"]
title("hook", 0.0, H2 - 0.02, [("The hardest app", False), ("to build", True)], 250)
c.ft("#hookx", o(scale=1.12, transformOrigin="0% 50%"), o(scale=1, duration=0.5, ease="power3.out"), 0.0)   # readable from the first frame

# ----------------------------------------------------------------- captions: a quiet lower third, a few words at a time
A_ = "acc"
DISP = {("u1", 9): "DoorDash", ("u1", 10): "", ("d1", 5): "DoorDash.", ("d1", 6): "", ("k1", 6): "DetailDash.", ("k1", 7): "", ("k2", 2): "DoorDash", ("k2", 3): ""}
CAPS = [("h1", 5, 9, {}), ("h1", 10, 13, {12: A_, 13: A_}),
        ("h2", 0, 4, {}), ("h2", 5, 8, {5: A_, 8: A_}), ("h2", 9, 12, {}),
        ("u1", 0, 5, {4: A_}), ("u1", 6, 10, {7: A_, 9: A_}), ("u1", 11, 13, {}),
        ("u2", 0, 2, {}),
        ("u3", 0, 3, {0: A_}), ("u3", 4, 8, {7: A_, 8: A_}),
        ("u4", 0, 4, {1: A_}), ("u4", 5, 9, {8: A_, 9: A_}),
        ("d1", 0, 6, {5: A_}),
        ("d2", 0, 4, {0: A_, 1: A_}), ("d2", 5, 8, {6: A_, 7: A_}), ("d2", 9, 14, {9: A_, 10: A_}),
        ("s1", 0, 5, {4: A_}),
        ("s2", 0, 5, {}), ("s2", 6, 11, {7: A_, 8: A_}),
        ("s3", 0, 4, {3: A_, 4: A_}), ("s3", 5, 10, {8: A_, 10: A_}), ("s3", 11, 15, {15: A_}), ("s3", 16, 19, {16: A_}), ("s3", 20, 25, {22: A_}),
        ("k1", 0, 3, {}), ("k1", 4, 7, {6: A_}),
        ("k2", 0, 3, {2: A_}), ("k2", 4, 6, {5: A_, 6: A_}),
        ("k3", 0, 2, {1: A_}), ("k3", 3, 7, {}), ("k3", 8, 9, {9: A_}), ("k3", 10, 13, {12: A_, 13: A_}),
        ("c1", 0, 3, {}), ("c1", 4, 8, {6: A_}),
        ("c2", 0, 3, {3: A_}), ("c2", 4, 9, {9: A_}), ("c2", 10, 12, {12: A_}), ("c2", 13, 18, {15: A_}),
        ("e1", 0, 4, {3: A_}), ("e1", 5, 8, {8: A_}), ("e1", 9, 12, {12: A_}),
        ("e2", 0, 2, {2: A_})]                                            # "one market first. Then expand." is the title
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]; i1 = min(i1, len(wd) - 1)
    start = wd[i0]["t0"] - 0.08
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.08
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.3, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = ln["t1"] + 0.45
    if lid == "e2": end = W("e2", "one") - 0.04                                # the title takes over
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = DISP.get((lid, n), wd[n]["w"])
        if not w: continue
        w = w.rstrip(",") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w.replace(chr(39), "’"))}</span>')
    c.clip(cid, start, end, f'<div class="cap"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        if DISP.get((lid, n), wd[n]["w"]): c.ft(f"#{cid}w{n - i0}", o(opacity=0.32), o(opacity=1, duration=0.12, ease="power2.out"), wd[n]["t0"] - 0.05)

# ----------------------------------------------------------------- the payoff: the last line lands as the title, word for word with the voice
VEND = END1 + 0.15
TT = W("e2", "one") - 0.06
c.clip("endshade", TT - 0.2, D, '<div class="endshade" id="endshadex"></div>', cls="layer", style="z-index:5")
c.ft("#endshadex", o(opacity=0), o(opacity=1, duration=0.4), TT - 0.2)
n_ = title("endt", TT, D, [("One market first.", False), ("Then expand.", True)], 190, "end")
for i in range(n_): c.ft(f"#endt{i}", o(opacity=0, y=36, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), [W("e2", "one"), W("e2", "market"), W("e2", "first"), W("e3", "Then"), W("e3", "expand")][i] - 0.06)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -17)
cue("riser-s", 0.0, -8); cue("land", TEMPTY + 0.1, -8)
cue("riser-m", V1, -9)                                                # the dive into the phone
for tt in [W("h2", "two"), W("h2", "different")]: cue("tap", tt, -8)  # each side lights up
cue("bubble", W("u3", "no") - 0.05, -4); cue("popup", REQ, -3); cue("tap", REQ + 0.42, -2)
cue("riser-s", U6 + 0.45, -9); cue("land", U6 + 0.5, -8)              # the ride connects
cue("bubble", K2 + 0.25, -5)
for k in range(4): cue("popup", ORD + 0.1 * k, -7)                    # orders come in
cue("riser-m", S2_, -10)
cue("tap", ONE, -4); cue("land", ONE + 0.02, -9)
cue("riser-m", M4 + 0.9, -9)                                          # the network spreads across the map
cue("popup", V5 + 0.3, -6); cue("tap", TAP + 0.05, -2); cue("popup", NOTE + 0.05, -3)
for k in range(5): cue("tap", TB + 0.2 * k, -10); cue("tap", TA + 0.18 * k, -11)
cue("riser-m", E["c2"] + 0.3, -10)
cue("land", TT, -7); cue("land", W("e3", "Then"), -4); cue("riser-l", END1, -10); cue("land", VEND, -9)
LEVEL = {"whoosh": -6.0, "popup": -8.0, "tap": -4.0, "land": -4.0, "bubble": -6.0, "riser-m": -7.0, "riser-s": -7.0, "riser-l": -7.0}
VBRAND = VEND
def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="glow", seed=41)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 2.0, 0.6, 1.0)[:, None]
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]; vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
    env = np.convolve(np.abs(vo).mean(1), np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
    duck = 10 ** (-7 * np.clip(env / 0.05, 0, 1) / 20)
    duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), "same")
    music = bed * ramp * duck[:, None] * 10 ** (-15 / 20)
    full = (fx + music) * 10 ** (-6 / 20) + vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, (fx + bed * ramp * 10 ** (-15 / 20)) * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=pfx)
    os.remove(pre); os.remove(pfx)
    return m

# ----------------------------------------------------------------- CSS: Montserrat + Inter, charcoal / warm white / amber
MONT = 'font-family:"Montserrat", sans-serif;'
CSS = f"""
@font-face {{ font-family:"Montserrat"; font-weight:100 900; font-display:block; src:url("assets/fonts/Montserrat-var-latin.woff2") format("woff2"); }}
@font-face {{ font-family:"Inter"; font-weight:400; font-display:block; src:url("assets/fonts/Inter-400-latin.woff2") format("woff2"); }}
@font-face {{ font-family:"Inter"; font-weight:600; font-display:block; src:url("assets/fonts/Inter-600-latin.woff2") format("woff2"); }}
@font-face {{ font-family:"Inter"; font-weight:700; font-display:block; src:url("assets/fonts/Inter-700-latin.woff2") format("woff2"); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:{BG}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#070605; font-family:"Inter", sans-serif; color:{WHITE}; -webkit-font-smoothing:antialiased; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.vig {{ position:absolute; inset:0; background:radial-gradient(ellipse 85% 70% at 50% 46%, rgba(0,0,0,0) 55%, rgba(0,0,0,.5) 100%); }}
.ttl {{ position:absolute; left:70px; right:70px; display:grid; justify-items:start; {MONT} font-weight:800; font-size:104px; line-height:1.0; letter-spacing:-.02em; color:{WHITE}; text-shadow:0 6px 40px rgba(0,0,0,.75), 0 2px 6px rgba(0,0,0,.6); }}
.ttl .tl {{ display:block; }} .ttl .acc {{ color:{AMBER}; }} .ttl .tw {{ display:inline-block; }}
.ttl.end {{ justify-items:center; text-align:center; font-size:84px; text-transform:uppercase; letter-spacing:-.01em; }}
.cap {{ position:absolute; left:70px; right:70px; top:1492px; display:flex; justify-content:center; text-align:center; }}
.cap .cl {{ display:inline-block; padding:10px 26px 14px; border-radius:22px; background:rgba(10,9,8,.6); {MONT} font-weight:700; font-size:52px; line-height:1.18; letter-spacing:-.01em; color:{WHITE}; text-shadow:0 2px 10px rgba(0,0,0,.6); text-wrap:balance; }}
.endshade {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(8,7,6,.9) 0%, rgba(8,7,6,.7) 20%, rgba(8,7,6,0) 34%, rgba(8,7,6,0) 80%, rgba(8,7,6,.7) 100%); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{AMBER}; }}
"""

SCENES = [(0.0, V1, "The hook", "A giant phone on a dark stage: code on its screen, then an empty marketplace; customers (ivory) on the left, providers (amber) on the right; links try to cross and fail; the camera dives into the screen", "THE HARDEST APP TO BUILD"),
          (V1, V2, "Ride-hailing", "A night city: a rider at the kerb; their app finds no cars; drivers parked with no requests; a request arrives, a driver accepts, the car pulls up", "app screens only"),
          (V2, K4, "Delivery", "A restaurant pass with bagged orders and an empty order screen; a customer's app with no restaurants; orders arrive", "app screens only"),
          (K4, V5, "The solution", "The city lights up with connections; a dark map of the US seen from the west coast; one city lights; into that city as activity builds; back out as the network spreads", "none"),
          (V5, V6, "DetailDash", "The DetailDash app: detailers near you, a booking; a detailing bay with a car being polished and the customer on their phone; the detailer's phone gets the booking", "app screens only"),
          (V6, V7, "The challenge", "The stage again: the DetailDash map with zero detailers and zero customers; detailers light up, then customers, then bookings connect and count up", "app screens only"),
          (V7, D, "The close", "The city from above: one neighbourhood fills with connections, then the network expands; a phone showing the DetailDash marketplace", "ONE MARKET FIRST. THEN EXPAND.")]
def write_cues():
    lines = ["# Voiceover cues", "", f"The video is {D:.1f} s. To record your own read over `assets/mix-novo.wav`, start each line at its time (seconds).", "",
             "| Start | End | Scene | Line |", "|---|---|---|---|"]
    for a, b, name, desc, _ in SCENES:
        for ln in TM["lines"]:
            if a - 0.01 <= ln["t0"] + 0.08 < b: lines.append(f"| {ln['t0']:.2f} | {ln['t1']:.2f} | {name} | {ln['text']} |")
    lines += ["", "## Scenes", "", "| From | To | Scene | Shots | Text on screen |", "|---|---|---|---|---|"] + [f"| {a:.2f} | {b:.2f} | {n} | {d} | {t} |" for a, b, n, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js","three/addons/":"./assets/vendor/addons/"}}</script>'
if __name__ == "__main__":
    cc = {"duration": D, "shots": SHOTS}
    h = c.page(CSS, "The hardest app to build", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/js/main.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    write_cues()
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
