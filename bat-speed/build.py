"""'What actually creates bat speed?' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the fastball and the home run -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
    node tools/render_chunks.js . <chunk dir> 30 <duration> 90 <port>

One right-handed hitter (white kit, navy helmet) and one swing: a load into the rear leg, a stride, the pelvis then the
torso turning, the arms and hands delivering the barrel into a 95 mph fastball, driven out to left-center. The ballpark
carries the real swing; a dark capture lab (a force plate under each foot) carries the teaching shots. Segment colours:
legs/ground amber, pelvis orange, torso cyan, arms/hands green, the bat gold. The force arrows and the rotation traces are
qualitative (from the keyed swing itself): no measured numbers are shown.
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
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED, AMBER = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D", "#FFB547"

SHOTS = []
def shot(a, b, cam, vs, ts, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], **kw))
def vat(vs, ts, t):
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
K = lambda k: round(TCON + k, 4)                                    # play time of k (seconds from contact); the pitch is released at t = 0
TOPP, BOTP, FULL = [0, 0, 1080, 960], [0, 960, 1080, 960], [0, 0, 1080, 1920]
HR = dict(who="B", rel=0.0, hit="hr")
NEVER = 1e9
ALLSEG = dict(legs=[-1, NEVER], pelvis=[-1, NEVER], torso=[-1, NEVER], arms=[-1, NEVER], bat=[-1, NEVER])
# cameras (the hitter is a right-hander in the box on the third-base side, facing +x; the pitcher is toward -z)
HANDCU = dict(c0=[3.0, 4.2, -4.6], c1=[3.6, 4.3, -4.2], l=[-2.6, 4.5, 0.7], l1=[-2.2, 3.9, 0.0], f0=22, f1=32, close=1, bokeh=60)       # tight on the hands and bat
FACE = dict(c0=[11.5, 4.2, -0.3], c1=[10.9, 4.15, -0.3], l=[-2.4, 3.6, -0.4], f0=46)                                         # square to his chest, full body
FACEX = dict(c0=[8.6, 4.6, -2.6], c1=[11.6, 4.3, -0.8], l=[-2.4, 4.2, -0.2], l1=[-2.4, 3.5, -0.4], f0=40, f1=46)                 # the freeze: pull back to the whole body
LEGS = dict(c0=[4.6, 2.0, -8.6], c1=[3.9, 1.9, -7.8], l=[-2.9, 2.2, 0.2], f0=44)                                            # lab: low, front three-quarter, both feet and plates
LEGS2 = dict(c0=[9.4, 2.6, 2.6], c1=[8.8, 2.6, 2.2], l=[-2.6, 2.4, -0.4], f0=46)                                            # lab: low side view from across the plate, the stride
SIDE2 = dict(c0=[10.2, 3.9, -0.8], c1=[9.6, 3.9, -0.8], l=[-2.6, 3.4, -0.4], f0=40)                                          # lab, half pane: side view
TOP2 = dict(c0=[-2.8, 17.0, 1.2], c1=[-2.8, 16.0, 1.2], l=[-2.8, 2.0, 1.15], f0=38, up=[0, 0, -1])                    # lab, half pane: overhead, the pitcher up
UPPER = dict(c0=[9.4, 6.4, -6.2], c1=[8.8, 6.1, -5.6], l=[-1.6, 3.9, -1.0], f0=42)                                          # lab: the upper body from the open side
FRONTL = dict(c0=[5.0, 6.0, -12.6], c1=[4.4, 5.8, -11.8], l=[-2.2, 3.3, 0.0], f0=44)                                          # lab: from in front, toward the pitcher's side
WRIST = dict(c0=[1.4, 4.0, -4.6], c1=[1.1, 3.8, -4.1], l=[-1.4, 3.3, -1.4], l1=[-0.9, 3.0, -1.9], f0=30, close=1, bokeh=60)     # park: close on the hands and wrists
CONT = dict(c0=[3.2, 2.4, -9.0], c1=[3.0, 2.35, -8.5], l=[-0.6, 2.9, -1.8], f0=38, close=1)                                    # park: low, in front of the plate, the contact point
FOLC = dict(c0=[-1.6, 6.6, 11.5], c1=[-1.3, 7.6, 9.8], l=[-0.8, 2.6, -15.0], f0=34, f1=40, lag=0.3, fw=0.4, bglow=1)          # park: over his shoulder, then with the ball
FIN = dict(c0=[7.6, 5.0, -6.4], c1=[6.9, 4.8, -5.6], l=[-2.6, 4.6, 0.0], f0=40, close=1, bokeh=70)                           # park: the finish, front three-quarter

V2, V3, V4, V5, V6 = S["g1"], S["p1"], S["a1"], S["w1"], S["e1"]

# ----------------------------------------------------------------- 1 the hook: tight on the hands, the swing, a freeze before contact, the x-ray
HF = 1.75
shot(0.0, HF, "world", [0.0, 1.15, HF], [K(-1.0), K(-0.62), K(-0.045)], hit=HR, streak=1, **HANDCU)
XR = W("h2", "entire") - 0.1
shot(HF, V2, "world", [HF, V2], [K(-0.045), K(-0.045)], hit=HR, xray=[XR, NEVER], xin=0.5, seg=ALLSEG, **FACEX)

# ----------------------------------------------------------------- 2 the lower body: the lab, the force plates, support moving from the rear leg to the lead leg
G2 = W("g2", "ground") - 0.12
shot(V2, G2, "world", [V2, G2], [K(-1.05), K(-0.6)], hit=HR, noball=1, lab=1, xray=[-1, NEVER], xin=0.01, seg=dict(legs=[-1, NEVER]), grf=[V2 + 0.4, NEVER], **LEGS)
GP = W("g2", "swing") - 0.1
shot(G2, V3, "world", [G2, GP, V3], [K(-0.6), K(-0.16), K(-0.1)], hit=HR, noball=1, lab=1, xray=[-1, NEVER], xin=0.01,
     seg=dict(legs=[-1, NEVER], pelvis=[GP, NEVER]), grf=[-1, NEVER], **LEGS2)

# ----------------------------------------------------------------- 3 pelvis -> torso: side view over the overhead view; slow motion, a freeze at separation
PF0 = W("p2", "their") - 0.05; PF1 = W("p2", "conditions") - 0.05
PV = [V3, PF0, PF1, V4]; PT = [K(-0.78), K(-0.11), K(-0.11), K(0.08)]
P3 = dict(hit=HR, noball=1, lab=1, xray=[-1, NEVER], xin=0.01, seg=dict(pelvis=[-1, NEVER], torso=[W("p1", "torso") - 0.05, NEVER]))
shot(V3, V4, "world", PV, PT, panes=[dict(rect=TOPP, **P3, **SIDE2), dict(rect=BOTP, **P3, sep=[PF0 - 0.3, NEVER], **TOP2)])

# ----------------------------------------------------------------- 4 arms, hands and the barrel
A2 = S["a2"]
shot(V4, A2, "world", [V4, A2], [K(-0.5), K(-0.2)], hit=HR, noball=1, lab=1, xray=[-1, NEVER], xin=0.01,
     seg=dict(legs=[-1, W("a1", "itself") - 0.2], pelvis=[-1, W("a1", "itself") - 0.2], arms=[W("a1", "itself"), NEVER], bat=[W("a1", "itself"), NEVER]), **FRONTL)
AB = W("a2", "barrel") + 0.15
shot(A2, AB, "world", [A2, AB], [K(-0.2), K(0.04)], hit=HR, noball=1, lab=1, xray=[-1, NEVER], xin=0.01, ghost=0.016,
     seg=dict(arms=[-1, NEVER], bat=[-1, NEVER]), tip=dict(from_=-0.2, v=[A2 + 0.2, NEVER], c=Y), **UPPER)
AC = W("a2", "path") - 0.05
shot(AB, AC, "world", [AB, AC], [K(-0.14), K(-0.035)], hit=HR, batglow=[AB, NEVER], **WRIST)
shot(AC, V5, "world", [AC, AC + 0.9, V5], [K(-0.03), K(0.0), K(0.05)], hit=HR, streak=1, ghost=0.012, **CONT)

# ----------------------------------------------------------------- 5 all together: full speed, then the x-ray replay lighting segment by segment, contact, the home run
F1 = V5 + 1.55
shot(V5, F1, "world", [V5, V5 + 0.1, F1], [K(-1.1), K(-1.1), K(0.35)], hit=HR, streak=1, **FACE)
X0 = F1; X1 = W("w3", "entire") - 0.05
def at(k): return round(X0 + (k + 0.8) / 0.8 * (X1 - X0), 3)                     # the replay runs k = -0.8 .. 0 over X0 .. X1
shot(X0, X1 + 0.4, "world", [X0, X1, X1 + 0.4], [K(-0.8), K(0.0), K(0.02)], hit=HR, streak=1, xray=[X0 - 1, NEVER], xin=0.01,
     seg=dict(legs=[at(-0.7), NEVER], pelvis=[at(-0.2), NEVER], torso=[at(-0.12), NEVER], arms=[at(-0.07), NEVER], bat=[at(-0.03), NEVER]), **FACE)
FL0 = X1 + 0.4
shot(FL0, V6, "hfollow", [FL0, V6], [K(0.02), K(0.02) + (V6 - FL0) * 1.15], hit=HR, streak=1, **FOLC)

# ----------------------------------------------------------------- 6 the series end: the finish in slow motion, a freeze, the mark
FZ = V6 + 1.6
D_ = D
shot(V6, D_, "world", [V6, FZ, D_], [K(0.1), K(0.62), K(0.62)], hit=HR, noball=1, look=[-30, 30, -300], **FIN)

for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
for sh in SHOTS:                                                    # field.js reads trail starts as "from"
    for p in [sh] + sh.get("panes", []):
        for key in ("knob", "tip", "knob2"):
            if key in p and "from_" in p[key]: p[key]["from"] = p[key].pop("from_")
CUTS = [x["a"] for x in SHOTS[1:]]

# ----------------------------------------------------------------- overlays
c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in CUTS:
    c.set("#flash", '{"opacity":0.35}', f); c.to("#flash", o(opacity=0, duration=0.12, ease="power2.out"), f + 0.001)

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
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style=f"z-index:{26 if cls == 'q' else 22}")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.05 * i)
def seam(sid, t0, t1):
    c.clip(sid, t0, t1, '<div class="hseam"></div>', cls="layer", style="z-index:11")
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def note(nid, t0, t1, text, top):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{esc(text)}</div>', cls="layer", style="z-index:14"); pop(f"#{nid}x", t0, 8)
def legend(lid, t0, t1, keys, top):
    html = "".join(f'<span class="lg"><i style="background:{col}"></i>{lab}</span>' for lab, col in keys)
    c.clip(lid, t0, t1, f'<div class="legend" id="{lid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14"); pop(f"#{lid}x", t0, 8)
BAND = 1660
LEG = [("Legs", AMBER), ("Pelvis", HOT), ("Torso", CYAN), ("Arms + hands", GREEN), ("Bat", Y)]

# 1 the hook
title("t1", 0.12, V2 - 0.02, [("What actually creates", ""), ("bat speed?", "yl")], 1500, "band")
legend("lg1", XR + 0.25, V2 - 0.02, LEG, 1800)

# 2 the lower body
title("t2", W("g2", "ground") - 0.05, V3 - 0.02, [("Ground reaction forces", "am")], BAND)
c.clip("sup", V2 + 0.4, V3 - 0.02, f'''<div class="sup" id="supx"><div class="sl"><span>Rear leg</span><b>Support</b><span>Lead leg</span></div>
  <div class="st"><div class="sk" id="supk"></div></div></div>''', cls="layer", style="z-index:14"); pop("#supx", V2 + 0.4, 10)
note("n2", V2 + 0.9, V3 - 0.02, "Arrows show direction and relative size. Illustration, not measured data.", 1585)
pinl("p2a", V2 + 0.6, G2 - 0.02, "Rear leg", "footR", "am sm"); pinl("p2b", V2 + 0.6, G2 - 0.02, "Lead leg", "footL", "am sm")
pinl("p2c", GP + 0.05, V3 - 0.02, "Pelvis starts to turn", "pelvis", "sm")

# 3 pelvis -> torso
seam("sm3", V3, V4)
title("t3", V3 + 0.1, V4 - 0.02, [("Pelvis → Torso", "")], 880, "mid")
pinl("p3a", V3 + 0.3, V4 - 0.02, "Pelvis", "pelvis", "sm", 0); pinl("p3b", W("p1", "torso") - 0.05, V4 - 0.02, "Torso", "chest", "cy sm", 0)
c.clip("trc", W("p1", "sequence") - 0.1, V4 - 0.02, f'''<div class="trw" id="trcx"><div class="trl"><span class="or">Pelvis</span><span class="cyt">Torso</span><em>turning speed</em></div>
  <canvas id="trace" width="880" height="250"></canvas><div class="trx">time →</div></div>''', cls="layer", style="z-index:14"); pop("#trcx", W("p1", "sequence") - 0.1, 10)
chip("c3", PF0 + 0.05, PF1 + 0.3, '<span class="or">Pelvis open</span> · <span class="cyt">torso still closed</span>', 1015, "sm")

# 4 arms, hands, barrel
pinl("p4a", W("a1", "itself"), A2 - 0.02, "Arms + hands", "elbow", "gr sm")
title("t4", A2 + 0.05, V5 - 0.02, [("Barrel acceleration", "yl")], BAND)
note("n4", A2 + 0.4, AB - 0.02, "Bat positions at equal time steps: wider gaps, faster barrel.", 1585)
pinl("p4b", AB + 0.1, AC - 0.02, "Hands + wrists steer the barrel", "hands", "gr sm")

# 5 all together
legend("lg5", X0 + 0.1, X1 + 0.38, LEG, 1800)
for k_, key, lab, cls in [(-0.7, "footR", "Legs", "am"), (-0.2, "pelvis", "Pelvis", ""), (-0.12, "chest", "Torso", "cy"), (-0.07, "elbow", "Arms", "gr"), (-0.03, "barrel", "Bat", "yl")]:
    pinl(f"p5{lab}", at(k_), X1 + 0.38, lab, key, f"{cls} sm")
title("t5", W("w3", "entire") - 0.05, V6 - 0.02, [("The entire body", ""), ("works together.", "yl")], 1290, "big")
note("n5", W("w3", "entire") + 0.3, V6 - 0.02, "Sequence and timing vary from hitter to hitter.", 1585)

# 6 the series end
VBRAND = round(S["e2"] + 0.1, 3)
title("t6", VBRAND, D, [("Follow along for our", ""), ("biomechanics series", "yl")], 360, "q")
CAPS_END = VBRAND

# ----------------------------------------------------------------- captions: the voiceover, word by word, a few words at a time
KEY = {"bat", "speed", "arms", "entire", "body", "ground", "ground", "reaction", "forces", "pelvis", "torso", "sequence", "timing", "acceleration", "accelerate",
       "accelerating", "barrel", "hands", "coordination", "together", "biomechanics", "hitting", "zone", "lower", "upper", "muscle", "cue", "beginning"}
CAPS = []
for ln in TM["lines"]:
    wd = ln["words"]; chunk = []
    for n, w in enumerate(wd):
        chunk.append(n)
        brk = w["w"].endswith((",", ".")) or len(chunk) >= 4
        if brk or n == len(wd) - 1: CAPS.append((ln["id"], chunk[0], chunk[-1])); chunk = []
for k, (lid, i0, i1) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TM["lines"]): end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, D)
    if lid == "e2": end = min(end, VBRAND)
    if start >= end: continue
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"].rstrip(",.").replace("'", "’")
        acc = w.lower().strip("’s").rstrip("’") in KEY or w.lower() in KEY
        sp.append(f'<span class="cw{" acc" if acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" id="{cid}c"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0, y=40), o(opacity=1, y=0, duration=0.35, ease="power3.out"), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8); cue("impact", 0.12, -5)
cue("impact", HF, -4); cue("riser-m", XR - 0.6, -12)
for tt in [W("g2", "ground") - 0.05, V3 + 0.1, A2 + 0.05, W("w3", "entire") - 0.05]: cue("impact", tt, -7)
for tt in [at(-0.7), at(-0.2), at(-0.12), at(-0.07), at(-0.03), W("p1", "torso") - 0.05, PF0, W("a1", "itself"), AB + 0.1]: cue("tick", tt, -6)
CRACKS = []
def pv(sh, t):                                                      # video time of play time t in a shot (its first pane's clock)
    p = sh["panes"][0] if "panes" in sh else sh
    v = vat(p.get("vs", sh["vs"]), p.get("ts", sh["ts"]), t)
    return v if v is not None and sh["a"] <= v < sh["b"] else None
for sh in SHOTS:
    p0 = sh["panes"][0] if "panes" in sh else sh
    if not p0.get("hit"): continue
    v = pv(sh, K(-0.12)); cue("whoosh", v, -10)                     # the swing
    if p0.get("noball") or sh.get("noball"): continue
    v = pv(sh, K(0.0))
    if v is not None:
        r = (vat(sh["vs"], sh["ts"], K(0.02)) or v) - v
        CRACKS.append((v, r > 0.1))
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)

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
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=311)
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
.ttl.big {{ font-size:150px; }} .ttl.q {{ font-size:96px; z-index:30; }} .ttl.mid {{ font-size:112px; left:0; right:0; padding:18px 30px 24px; background:rgba(5,8,13,.86); }}
.ttl.band {{ left:0; right:0; padding:18px 30px 22px; background:rgba(5,8,13,.86); font-size:86px; line-height:.98; }}

.plb {{ position:absolute; left:50%; transform:translateX(-50%); padding:4px 18px; border-radius:12px; background:rgba(6,10,18,.88); border:3px solid {CYAN}; {BC} font-size:44px; line-height:1.0; color:{CYAN}; white-space:nowrap; }}
.plb.or {{ border-color:{HOT}; color:{HOT}; }} .plb b {{ color:#fff; font-weight:700; }}
.chip {{ position:absolute; left:50%; transform:translateX(-50%); padding:12px 26px; border-radius:14px; background:rgba(6,10,18,.88); {BC} font-size:60px; white-space:nowrap; }}
.chip.big {{ font-size:96px; padding:10px 30px; }} .chip.or {{ color:{HOT}; border:3px solid {HOT}; }}
.chip .cyt {{ color:{CYAN}; }} .chip .yt {{ color:{Y}; }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:24px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; {BC} font-size:46px; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.pin.sm span {{ font-size:38px; padding:6px 14px; }}
.pin.cy span {{ background:{CYAN}; }} .pin.yl span {{ background:{Y}; }} .pin.wh span {{ background:{WHITE}; }}

.brand {{ position:absolute; inset:0; display:grid; place-content:center; justify-items:center; gap:28px; padding-top:640px; background:linear-gradient(180deg, rgba(3,6,11,0) 42%, rgba(3,6,11,.8) 66%, rgba(3,6,11,.95)); }}
.bname {{ display:grid; justify-items:center; {BC} line-height:.9; }} .bname span {{ font-size:110px; color:#fff; }} .bname em {{ font-style:normal; font-size:140px; color:{HOT}; letter-spacing:.02em; }}

.ttl.am {{ color:{AMBER}; }} .ttl .am {{ color:{AMBER}; }}
.pin.am span {{ background:{AMBER}; }} .pin.gr span {{ background:{GREEN}; }}
.chip.sm {{ font-size:46px; padding:8px 20px; }} .chip .or {{ color:{HOT}; }}
.note {{ position:absolute; left:50%; transform:translateX(-50%); width:960px; text-align:center; {MONO} font-size:22px; letter-spacing:.06em; line-height:1.35; color:{MUTED}; text-transform:none; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.legend {{ position:absolute; left:0; right:0; display:flex; justify-content:center; gap:22px; {MONO} font-size:22px; letter-spacing:.08em; color:#e8edf4; text-shadow:0 2px 8px rgba(0,0,0,.9); }}
.legend .lg {{ display:inline-flex; align-items:center; gap:8px; }} .legend i {{ width:16px; height:16px; border-radius:50%; display:inline-block; box-shadow:0 0 10px currentColor; }}
.sup {{ position:absolute; left:110px; right:110px; top:1440px; }}
.sup .sl {{ display:flex; justify-content:space-between; align-items:baseline; {BC} font-size:40px; color:{AMBER}; margin-bottom:10px; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.sup .sl b {{ {MONO} font-size:22px; letter-spacing:.14em; color:{MUTED}; }}
.sup .st {{ position:relative; height:18px; border-radius:9px; background:linear-gradient(90deg, rgba(255,181,71,.85), rgba(255,181,71,.15) 50%, rgba(255,181,71,.85)); box-shadow:0 0 0 2px rgba(5,8,13,.8); }}
.sup .sk {{ position:absolute; top:50%; width:44px; height:44px; margin:-22px 0 0 -22px; border-radius:50%; background:#fff; border:6px solid {AMBER}; box-shadow:0 0 22px {AMBER}; left:50%; }}
.trw {{ position:absolute; left:80px; width:920px; top:1580px; padding:14px 20px 10px; border-radius:16px; background:rgba(5,8,13,.78); }}
.trw canvas {{ display:block; width:880px; height:250px; }}
.trl {{ display:flex; gap:28px; align-items:baseline; {BC} font-size:40px; }} .trl .or {{ color:{HOT}; }} .trl .cyt {{ color:{CYAN}; }}
.trl em {{ margin-left:auto; font-style:normal; {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; }}
.trx {{ text-align:right; {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; margin-top:-4px; }}
.ttl.big {{ font-size:128px; line-height:.9; }}
"""])

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [(0.0, V2, "The hook", "Ballpark, tight on the hands and bat; the swing starts, freezes just before contact, pulls back and turns to x-ray", "WHAT ACTUALLY CREATES BAT SPEED?"),
          (V2, V3, "The lower body", "Lab: the load into the rear leg on force plates, support moving to the lead leg as he strides; ground-force arrows at each foot; the pelvis starts to turn", "GROUND REACTION FORCES"),
          (V3, V4, "Pelvis and torso", "Lab, side view over the overhead view: pelvis (orange) then torso (cyan) turning in slow motion, a freeze with the pelvis open and the torso still closed; the turning-speed traces", "PELVIS → TORSO"),
          (V4, V5, "Arms, hands, barrel", "Lab, upper body: arms and hands light up; the barrel at equal time steps through the zone; close on the hands and wrists; contact", "BARREL ACCELERATION"),
          (V5, V6, "All together", "Ballpark: the full swing at full speed; the x-ray replay lighting legs, pelvis, torso, arms and bat in turn; contact and the home run to left-center", "THE ENTIRE BODY WORKS TOGETHER."),
          (V6, D, "Series end", "The finish in slow motion, a freeze, the Baseball Decoded mark", "FOLLOW ALONG FOR OUR BIOMECHANICS SERIES / BASEBALL DECODED")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "What Actually Creates Bat Speed", script=True).replace('<script src="assets/gsap.min.js"></script>',
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
