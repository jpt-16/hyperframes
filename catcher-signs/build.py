"""'From finger signs to PitchCom' (1080x1920), cut to the voiceover (tools/vo.py + tools/assemble.py).

    python3 tools/physics.py        # the pitches -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                # index.html + assets/mix.wav (+ mix-novo.wav without the voice) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/catcher-signs.mp4 --video-bitrate 16M

The same catcher (white home uniform) and pitcher throughout. The hand-signal era is graded warm, like old film; the
PitchCom era is clean and cool. Finger counts, sequences and indicators are examples: every team set its own.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PI_ = P["pitches"]
TMJ = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TMJ["lines"])}
LN = lambda lid: TMJ["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TMJ["duration"]
S = {x["id"]: x["t0"] - 0.08 for x in TMJ["lines"]}
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def live(a, b, cam, **kw): shot(a, b, cam, [a, b], [a, b], **kw)          # play time = video time
def seq(*pairs): return [[round(t, 3), n] for t, n in pairs]
HANDCAM = dict(cam="rel", o="croot", lo="hand", l=[0.0, 0.12, 0.0], close=1, bokeh=0)
POV = dict(cam="aim", c0=[0.15, 5.9, -59.4], c1=[0.15, 5.9, -59.4], lo="hand", l=[0.0, 0.0, 0.0])
BEHIND_C = dict(cam="aim", c0=[0.6, 5.4, 7.6], c1=[0.5, 5.3, 6.8], lo="neck", l=[0.0, 0.0, 0.0])
OLD0 = S["century"]
# 1 "Before PitchCom, calling one pitch could involve an entire secret code.": low between his legs, the hand flashing; the pitcher looking in
A1 = W("q", "involve") - 0.1
live(0.0, A1, signs=seq((0.25, 1), (0.85, 3), (1.45, 2)), **dict(HANDCAM, c0=[0.00, -1.50, 3.20], c1=[0.10, 0.00, 2.50], f0=40, f1=32))
live(A1, OLD0, nod=W("q", "code"), signs=seq((A1 + 0.1, 2)), **dict(BEHIND_C, f0=7.5, f1=6.5))
# 2 "For over a century, catchers communicated with pitchers using hand signals hidden between their legs."
A2 = W("century", "using") - 0.1
live(OLD0, A2, signs=seq((OLD0 + 0.5, 1), (OLD0 + 1.2, 4), (OLD0 + 1.8, 2)), **dict(POV, f0=9, f1=5.5))
live(A2, S["fingers"], signs=seq((A2 + 0.3, 3), (A2 + 1.0, 1)), **dict(HANDCAM, c0=[1.10, 0.30, 3.00], c1=[0.90, 0.24, 2.60], f0=34, f1=32))
# 3 "One finger might mean a fastball, two might mean a curveball, and three might mean a slider."
V1, V2, V3 = W("fingers", "one"), W("fingers", "two"), W("fingers", "three")
SG = seq((V1, 1), (V2, 2), (V3, 3)); SG.append  # (held to the end of the shot)
live(S["fingers"], S["problem"], signs=SG, **dict(HANDCAM, c0=[-0.24, 0.10, 2.90], c1=[-0.20, 0.10, 2.60], f0=32))
# 4 "But there was a problem. The opposing team could sometimes steal those signs, especially when a runner reached second base and could see…"
A3 = W("steal", "steal") - 0.1; A4 = W("steal", "and") - 0.1
live(S["problem"], A3, signs=seq((S["problem"] + 0.4, 2)), cam="world", c0=[-9.6, 7.4, -153.0], c1=[-9.3, 7.2, -150.0], l=[0.0, 2.0, 1.0], f0=13, f1=11)
live(A3, A4, signs=seq((A3 + 0.4, 1), (A3 + 1.3, 3)), sight=W("steal", "runner"), cam="world", c0=[2.0, 4.9, -116.0], c1=[1.4, 4.8, -116.6], l=[-6.45, 3.9, -121.7], f0=24)
live(A4, S["systems"], signs=seq((A4 + 0.2, 2), (A4 + 0.8, 4)), cam="aim", c0=[-6.3, 4.35, -120.6], c1=[-6.3, 4.35, -120.6], lo="hand", l=[0, 0, 0], f0=3.2, f1=2.4, lens=1)
# 5 "So teams developed different systems to hide their calls.": the sequence changes, fast
SYS = seq((S["systems"] + 0.15, 2), (S["systems"] + 0.6, 1), (S["systems"] + 1.05, 3), (S["systems"] + 1.5, 1))
live(S["systems"], S["seq"], signs=SYS, **dict(HANDCAM, c0=[0.60, 0.20, 2.80], c1=[0.50, 0.16, 2.50], f0=32))
# 6 "…a specific sign sequence, where only the first, second, or third sign actually mattered.": three panes, one sequence, three systems
SQ = seq((S["seq"] + 0.5, 2), (S["seq"] + 1.15, 1), (S["seq"] + 1.8, 3)); SQT = [x[0] for x in SQ]
PANE = dict(HANDCAM, c0=[0.0, 0.05, 1.25], c1=[0.0, 0.05, 1.1], f0=30)
shot(S["seq"], S["ind"], "obj", [S["seq"], S["ind"]], [S["seq"], S["ind"]], signs=SQ, panes=[dict(PANE, rect=[0, 0, 1080, 640]), dict(PANE, rect=[0, 640, 1080, 640]), dict(PANE, rect=[0, 1280, 1080, 640])])
LIVE3 = [W("seq", "first"), W("seq", "second"), W("seq", "third")]
# 7 "Other teams used an indicator sign, or even changed the system depending on the inning or number of outs."
A5 = W("ind", "or") - 0.1
IND = seq((S["ind"] + 0.25, 1), (W("ind", "indicator") - 0.05, 3), (W("ind", "sign") + 0.05, 2), (W("ind", "sign") + 0.6, 4))
live(S["ind"], A5, signs=IND, **dict(HANDCAM, c0=[-0.60, 0.20, 2.90], c1=[-0.50, 0.16, 2.60], f0=32))
live(A5, S["goal"], signs=seq((A5 + 0.3, 3), (A5 + 1.0, 1), (A5 + 1.7, 2)), **dict(POV, f0=6.5, f1=5.0))
# 8 "The goal was simple: make the signs look random to the other team (the runner can't read it) while keeping them understandable to the pitcher (he nods)."
A6 = W("goal", "while") - 0.1
live(S["goal"], A6, signs=seq((S["goal"] + 0.2, 4), (S["goal"] + 0.65, 1), (S["goal"] + 1.1, 3), (S["goal"] + 1.55, 2), (S["goal"] + 2.0, 1)), puzzle=W("goal", "random"), cam="world", c0=[2.0, 4.9, -116.0], c1=[1.6, 4.8, -116.4], l=[-6.45, 3.9, -121.7], f0=24)
live(A6, S["then"], nod=W("goal", "pitcher"), signs=seq((A6 + 0.2, 2)), **dict(BEHIND_C, f0=7, f1=6.2))
# 9 "Then came PitchCom.": in on the fingers, a flash, and the keypad on his wrist
OLD1 = W("then", "pitch") + 0.05
live(S["then"], OLD1, signs=seq((S["then"] + 0.1, 2)), **dict(HANDCAM, c0=[0.00, 0.10, 2.60], c1=[0.00, 0.10, 0.90], f0=32, f1=28))
# 10 "Introduced in MLB in 2022, it allowed catchers to press buttons on a wrist device and send the pitch call directly to a receiver in the pitcher's cap."
VPRESS = W("intro", "press") + 0.15
A7 = W("intro", "allowed") - 0.1
DEVCAM = dict(cam="obj", o="dev", lo="dev", close=1, bokeh=6)
live(OLD1, A7, act="press", macro=1, press=99, btn=2, **dict(DEVCAM, c0=[0.25, 1.25, 0.55], c1=[0.2, 1.05, 0.45], l=[0, 0.02, 0], f0=30))
live(A7, W("intro", "and") - 0.05, act="press", macro=1, press=VPRESS, btn=2, **dict(DEVCAM, c0=[0.12, 0.8, 0.3], c1=[0.1, 0.72, 0.26], l=[0, 0.02, 0], f0=30))
A8 = W("intro", "and") - 0.05; A9 = W("intro", "receiver") - 0.15
live(A8, A9, act="press", press=A8 + 0.25, btn=2, arc=1, cam="world", c0=[4.0, 15.0, 24.0], c1=[3.5, 14.0, 21.0], l=[0.0, 1.5, -30.0], f0=42)
live(A9, S["nomore"], act="press", press=A9 - 0.5, set=99, xray=A9 + 0.1, btn=2, cam="obj", o="neck", lo="neck", c0=[-2.6, 1.1, 1.9], c1=[-2.3, 1.0, 1.6], l=[-0.2, 0.2, 0.15], f0=28, close=1)
# 11 "No more complicated finger sequences. No more worrying about a runner at second stealing the signs.": then | now
COLS = dict(cam="world", c0=[0.3, 16.0, 16.0], c1=[0.3, 15.0, 14.5], l=[0.0, 0.0, -20.0], f0=50)
NM = S["nomore"]
shot(NM, S["end"], "world", [NM, S["end"]], [NM, S["end"]], panes=[
    dict(COLS, rect=[0, 0, 540, 1920], signs=seq((NM + 0.2, 2), (NM + 0.8, 1), (NM + 1.4, 3), (NM + 2.0, 2), (NM + 2.6, 1)), nod=NM + 3.4, sight=W("nomore", "runner"), sightScale=1.6),
    dict(COLS, rect=[540, 0, 540, 1920], act="press", press=NM + 0.3, set=NM + 0.9, arc=1, puzzle=W("nomore", "runner"))])
# 12 "A century of hand signals, replaced by a few buttons.": the pitch at full speed; the catch
VREL = W("end", "century") + 0.3; A10 = VREL + 0.3
live(S["end"], A10, act="pitch", kind="end", streak=1, cam="world", c0=[1.4, 9.6, -85.0], c1=[1.2, 9.3, -83.0], l=[0.0, 3.2, -28.0], f0=19)
SHOTS[-1]["ts"] = [round(S["end"] - VREL, 4), round(A10 - VREL, 4)]
shot(A10, D, "obj", [A10, D], [A10 - VREL, D - VREL], act="pitch", kind="end", o="croot", lo="glove", c0=[-4.2, 1.2, 5.2], c1=[-3.8, 1.15, 4.8], l=[0.0, 0.0, 0.0], f0=26, close=1)
VBRAND = round(LN("end")["t1"] + 0.45, 2)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
GRAIN = "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='240' height='240' filter='url(%23n)' opacity='0.9'/></svg>\")"
def grade(gid, t0, t1, left=0, width=1080):
    c.clip(gid, t0, t1, f'<div class="grade" style="left:{left}px;width:{width}px"><div class="tint"></div><div class="warm"></div><div class="grain"></div><div class="vig"></div></div>', cls="layer", style="z-index:2")
grade("g1", OLD0, OLD1); grade("g2", NM, S["end"], 0, 540)
c.clip("era1", OLD0 + 0.2, OLD1, '<div class="era" id="era1x">The hand-signal era</div>', cls="layer", style="z-index:14")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [OLD0, S["problem"], S["seq"], NM, VBRAND]:
    c.set("#flash", '{"opacity":0.45}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)
c.set("#flash", '{"opacity":1}', OLD1); c.to("#flash", o(opacity=0, duration=0.35, ease="power2.out"), OLD1 + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls="", pane=0):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, pane])
def title(tid, t0, t1, lines, top=1150, cls="hk2 band"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.06 * i)
def note(nid, t0, t1, text, top=1700, style=""):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px;{style}">{text}</div>', cls="layer", style="z-index:13"); pop(f"#{nid}x", t0, 8)
def seqrow(rid, t0, t1, times, nums, top, live=None, result=None, left=60):
    """The signs as he flashes them, one chip each; at live=(index, time) the live one lights up and the call appears."""
    chips = "".join(f'<span class="sg" id="{rid}c{i}">{n}</span>' for i, n in enumerate(nums))
    res = f'<span class="sgr" id="{rid}r">{result}</span>' if result else ""
    c.clip(rid, t0, t1, f'<div class="sgrow" style="top:{top}px;left:{left}px">{chips}{res}</div>', cls="layer", style="z-index:15")
    for i, tt in enumerate(times): c.ft(f"#{rid}c{i}", o(opacity=0, scale=0.5), o(opacity=1, scale=1, duration=0.16, ease="back.out(2)"), tt)
    if live:
        i, tt = live
        c.ft(f"#{rid}c{i}", o(backgroundColor="rgba(6,10,18,.88)", color="#ffffff", scale=1), o(backgroundColor=Y, color="#05080d", scale=1.18, duration=0.2, ease="back.out(2)"), tt)
        if result: c.ft(f"#{rid}r", o(opacity=0, x=-20), o(opacity=1, x=0, duration=0.22, ease="power3.out"), tt + 0.1)

# ----------------------------------------------------------------- 1 the hook (the opening line is the big title instead of captions)
title("hook", 0.1, OLD0 - 0.02, [("One pitch.", False), ("A secret code.", True)], 260, "hk2 big2")
# 3 the fingers: illustrative mapping
c.clip("map", V1 - 0.05, S["problem"] - 0.02, f"""<div class="mapc"><div class="mr" id="mr1"><i>1</i><b>= Fastball</b></div><div class="mr" id="mr2"><i>2</i><b>= Curveball</b></div><div class="mr" id="mr3"><i>3</i><b>= Slider</b></div></div>""", cls="layer", style="z-index:14")
for i, tt in enumerate([V1, V2, V3]): pop(f"#mr{i + 1}", tt - 0.03, 14)
note("nmap", V1 + 0.6, S["problem"] - 0.02, "Example only: every team set its <b>own</b> signs.", 1760)
# 4 the problem
pinl("prun", S["problem"] + 0.3, A3 - 0.02, "Runner at second", "runner", "")
pinl("psee", W("steal", "runner"), A4 - 0.02, "He can see the catcher’s fingers", "runner", "yl sm")
c.clip("lens", A4, S["systems"], '<div class="lens"></div><div class="lenstag">Runner’s view</div>', cls="layer", style="z-index:4")
# 5 change the sequence
title("t2", S["systems"] + 0.05, S["seq"] - 0.02, [("Change the", False), ("sequence", True)])
seqrow("sq0", S["systems"], S["seq"] - 0.02, [x[0] for x in SYS], [x[1] for x in SYS], 1500)
# 6 three systems, one sequence
for i, (lab, res) in enumerate([("Example A: 1st sign is live", "→ 2 = Curveball"), ("Example B: 2nd sign is live", "→ 1 = Fastball"), ("Example C: 3rd sign is live", "→ 3 = Slider")]):
    c.clip(f"pl{i}", S["seq"] + 0.05, S["ind"] - 0.02, f'<div class="plab" style="top:{i * 640 + 24}px" id="pl{i}x">{lab}</div>', cls="layer", style="z-index:15")
    pop(f"#pl{i}x", S["seq"] + 0.1 + 0.12 * i, 10)
    seqrow(f"sq{i + 1}", S["seq"], S["ind"] - 0.02, SQT, [2, 1, 3], i * 640 + 520, live=(i, LIVE3[i]), result=res)
c.clip("seams", S["seq"], S["ind"] - 0.02, '<div class="hseam" style="top:638px"></div><div class="hseam" style="top:1278px"></div>', cls="layer", style="z-index:16")
# 7 the indicator; changing systems
title("t3", W("ind", "indicator") - 0.05, A5 - 0.02, [("Use an", False), ("indicator", True)])
seqrow("sqi", S["ind"], A5 - 0.02, [x[0] for x in IND], [x[1] for x in IND], 1500, live=(2, IND[2][0] + 0.15), result="→ 2 = Curveball")
pinl("pind", IND[1][0] + 0.05, IND[2][0] - 0.05, "Indicator: the next sign is live", "hand", "yl sm")
c.clip("innc", A5 + 0.05, S["goal"] - 0.02, """<div class="innc"><div class="ih">Example: the system changes by inning</div>
  <div class="ir" id="ir1"><i>Innings 1–3</i><b>1st sign</b></div><div class="ir" id="ir2"><i>Innings 4–6</i><b>2nd sign</b></div><div class="ir" id="ir3"><i>Innings 7–9</i><b>3rd sign</b></div></div>""", cls="layer", style="z-index:15")
for i in range(3): pop(f"#ir{i + 1}", A5 + 0.15 + 0.25 * i, 10)
# 8 keep them guessing
title("t4", W("goal", "make") - 0.05, S["then"] - 0.02, [("Keep the opponent", False), ("guessing", True)])
pinl("pq", W("goal", "random"), A6 - 0.02, "?", "runner", "big")
pinl("pnod", W("goal", "pitcher"), S["then"] - 0.02, "Got it", "pitcher", "cy")
# 10 PitchCom
title("t5", OLD1 + 0.05, A7 + 0.6, [("Introducing", False), ("PitchCom", True)], 1150, "hk2 band cy")
c.clip("yr", W("intro", "twenty") - 0.05, A8 - 0.02, '<div class="yr" id="yrx"><span>Introduced in MLB</span><b>2022</b></div>', cls="layer", style="z-index:15")
pop("#yrx", W("intro", "twenty") - 0.05, 16)
pinl("pdev", A7 + 0.2, A8 - 0.02, "Wrist keypad", "dev", "cy sm")
pinl("prcv", A9 + 0.3, S["nomore"] - 0.02, "Receiver in the cap", "rcvlo", "cy sm")
pinl("pcall", A9 + 0.65, S["nomore"] - 0.02, "In his ear: “Slider… away”", "rcv", "sm")
note("n22", A8 + 0.1, S["nomore"] - 0.02, "Approved for MLB’s 2022 regular season. The call plays as a voice in the pitcher’s ear.", 1700)
# 11 then | now
c.clip("cols", NM, S["end"], f"""<div class="vseam"></div>
  <div class="colh" style="left:0" id="ch1"><span class="old">Then</span><b>Secret hand signals</b></div>
  <div class="colh" style="left:540px" id="ch2"><span class="new">Now</span><b>Electronic communication</b></div>""", cls="layer", style="z-index:15")
pop("#ch1", NM + 0.05, 12); pop("#ch2", NM + 0.25, 12)
pinl("pc1", NM + 0.2, S["end"] - 0.02, "Fingers", "hand", "yl sm", 0)
pinl("pc2", NM + 0.4, S["end"] - 0.02, "One button", "dev", "cy sm", 1)
pinl("pc3", W("nomore", "runner"), S["end"] - 0.02, "Sees the signs", "runner", "yl sm", 0)
pinl("pc4", W("nomore", "runner") + 0.1, S["end"] - 0.02, "Nothing to see", "runner", "cy sm", 1)
note("nstill", W("nomore", "no", nth=1), S["end"] - 0.02, "In MLB. Hand signs are still used across baseball, and as a backup.", 1560)
# 12 the ending
title("t6", S["end"] + 0.05, VBRAND - 0.02, [("A century of signals.", False), ("A new way to communicate.", True)], 1150)
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.2), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- captions: the voiceover, word by word (the opening line is the big title instead)
DISP = {("intro", 2): "MLB", ("intro", 3): "", ("intro", 4): "", ("intro", 6): "2022,", ("intro", 7): "", ("then", 2): "PitchCom.", ("then", 3): ""}
CAPS = [("century", 0, 3, {3: "acc"}), ("century", 4, 7, {}), ("century", 8, 10, {9: "acc", 10: "acc"}), ("century", 11, 14, {11: "acc", 14: "acc"}),
        ("fingers", 0, 5, {0: "acc", 5: "acc"}), ("fingers", 6, 10, {6: "acc", 10: "acc"}), ("fingers", 11, 16, {12: "acc", 16: "acc"}),
        ("problem", 0, 4, {4: "acc"}),
        ("steal", 0, 7, {5: "acc"}), ("steal", 8, 13, {12: "acc", 13: "acc"}), ("steal", 14, 20, {19: "acc"}),
        ("systems", 0, 4, {4: "acc"}), ("systems", 5, 8, {6: "acc"}),
        ("seq", 0, 3, {}), ("seq", 4, 8, {7: "acc", 8: "acc"}), ("seq", 9, 14, {12: "acc", 13: "acc", 14: "acc"}), ("seq", 15, 18, {18: "acc"}),
        ("ind", 0, 5, {4: "acc"}), ("ind", 6, 10, {8: "acc"}), ("ind", 11, 18, {14: "acc", 18: "acc"}),
        ("goal", 0, 3, {}), ("goal", 4, 8, {8: "acc"}), ("goal", 9, 12, {}), ("goal", 13, 18, {15: "acc", 18: "acc"}),
        ("then", 0, 3, {2: "acc"}),
        ("intro", 0, 7, {2: "acc", 6: "acc"}), ("intro", 8, 14, {11: "acc", 12: "acc"}), ("intro", 15, 19, {18: "acc", 19: "acc"}), ("intro", 20, 25, {21: "acc", 22: "acc"}), ("intro", 26, 30, {28: "acc", 29: "acc"}),
        ("nomore", 0, 4, {2: "acc", 3: "acc"}), ("nomore", 5, 10, {8: "acc"}), ("nomore", 11, 15, {13: "acc"}),
        ("end", 0, 4, {3: "acc", 4: "acc"}), ("end", 5, 9, {9: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]; i1 = min(i1, len(wd) - 1)
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TMJ["lines"]): end = min(ln["t1"] + 0.35, TMJ["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, VBRAND - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = DISP.get((lid, n), wd[n]["w"])
        if not w: continue
        w = w.rstrip(",:") if n == i1 and i1 > i0 else w
        w = w.replace("'", "’")
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        if DISP.get((lid, n), wd[n]["w"]): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8); cue("impact", 0.1, -6)
for tt in [S["systems"] + 0.05, W("ind", "indicator") - 0.05, W("goal", "make") - 0.05, OLD1, S["end"] + 0.05]: cue("impact", tt, -6)
TICKS = sorted({round(t, 3) for sh in SHOTS for t, n in (sh.get("signs") or []) if sh["a"] <= t < sh["b"]})
for t_ in TICKS: cue("tick", t_, -16)                                       # a soft tick as each sign flashes
BEEPS = [VPRESS, A8 + 0.25, NM + 0.3]
cue("whoosh", VREL, -6); cue("glove", VREL + PI_["end"]["flight"], 0)
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}

def beep(rng):
    """The keypad: a short, clean electronic chirp."""
    t = np.arange(int(0.16 * SR)) / SR
    x = (np.sin(2 * np.pi * 1760 * t) * (t < 0.06) + np.sin(2 * np.pi * 2350 * t) * (t >= 0.07)) * np.exp(-((t % 0.07) / 0.05))
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
    rng = np.random.default_rng(3)
    for vt in BEEPS:
        x = beep(rng); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * 10 ** (-14 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-30 / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=131)
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
.ttl {{ position:absolute; left:40px; right:40px; display:grid; justify-items:center; text-align:center; {BC} font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.6); }}
.ttl.big {{ font-size:158px; }} .ttl .tl {{ display:block; }} .ttl .acc {{ color:{HOT}; }} .ttl .tw {{ display:inline-block; }}
.ttl.band {{ left:0; right:0; padding:22px 30px 26px; background:rgba(5,8,13,.84); font-size:104px; }}
.ttl.nyk {{ top:820px; font-size:150px; }} .ttl.nyk .acc {{ color:{Y}; }}
.seam {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.75); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; left:0; right:0; height:960px; }} .half.t {{ top:0; }} .half.b {{ top:960px; }}
.hlab {{ position:absolute; left:50%; transform:translateX(-50%); top:40px; padding:8px 20px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:54px; white-space:nowrap; }}
.half.b .hlab {{ top:175px; }}
.yl {{ color:{Y}; }} .hot {{ color:{HOT}; }} .cy {{ color:{CYAN}; }}
.fpl {{ position:absolute; left:0; right:0; top:1770px; text-align:center; {MONO} font-size:24px; letter-spacing:.1em; color:{CYAN}; }}
.note {{ position:absolute; left:60px; right:60px; text-align:center; font-family:"Inter", sans-serif; font-weight:700; font-size:31px; line-height:1.3; color:#dfe5ec; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.84); }}
.note b {{ color:#fff; font-weight:800; }}
.chip {{ position:absolute; left:50%; transform:translateX(-50%); padding:12px 26px; border-radius:14px; background:rgba(6,10,18,.88); {BC} font-size:64px; white-space:nowrap; }}
.pin.cy span {{ background:{CYAN}; }} .pin.gr span {{ background:#3dd68c; }}
.rs2 {{ position:absolute; left:50%; transform:translateX(-50%); padding:10px 22px; border-radius:12px; background:rgba(6,10,18,.9); {BC} font-size:60px; white-space:nowrap; }}
.stamp {{ position:absolute; left:0; right:0; top:1180px; text-align:center; {BC} font-size:190px; line-height:1; color:{Y}; text-shadow:0 10px 40px rgba(0,0,0,.9); }}
.brand {{ position:absolute; inset:0; display:grid; place-content:center; justify-items:center; gap:28px; background:radial-gradient(ellipse at 50% 45%, rgba(10,16,28,.94), rgba(3,6,11,.98)); }}
.bname {{ display:grid; justify-items:center; {BC} line-height:.9; }} .bname span {{ font-size:120px; color:#fff; }} .bname em {{ font-style:normal; font-size:150px; color:{HOT}; letter-spacing:.02em; }}
"""


CSS += f"""
.ttl.hk2 {{ font-size:112px; }}
.nc {{ position:absolute; left:40px; top:1380px; display:flex; align-items:center; gap:18px; padding:12px 24px 12px 12px; border-radius:16px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.14); }}
.nc i {{ display:grid; place-items:center; width:84px; height:84px; border-radius:12px; background:{Y}; color:#05080d; font-style:normal; {BC} font-size:72px; }}
.nc b {{ {BC} font-size:60px; line-height:1; color:#fff; }}
.chip.lb {{ color:{CYAN}; }}
.pin.sm span {{ font-size:34px; padding:6px 12px; }}
"""


CSS += f"""
.ttl.band {{ left:0; right:0; padding:20px 30px 24px; background:rgba(5,8,13,.86); font-size:92px; }}
.ttl.big {{ font-size:150px; }}
.howto {{ position:absolute; left:48px; right:48px; top:1430px; display:grid; gap:14px; }}
.hrow {{ display:flex; align-items:center; gap:18px; padding:14px 22px 14px 14px; border-radius:16px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.12); }}
.hrow i {{ display:grid; place-items:center; width:64px; height:64px; flex:none; border-radius:12px; background:{CYAN}; color:#05080d; font-style:normal; {BC} font-size:52px; }}
.hrow + .hrow i {{ background:#f4f2ec; }}
.hrow span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:36px; line-height:1.2; color:#dfe5ec; }} .hrow b {{ color:#fff; font-weight:800; }}
.vd {{ position:absolute; left:50%; transform:translateX(-50%); top:40px; display:inline-flex; align-items:center; gap:14px; padding:10px 22px 10px 12px; border-radius:14px; background:rgba(6,10,18,.9); {BC} font-size:56px; white-space:nowrap; }}
.half.b .vd {{ top:auto; bottom:40px; }}
.vd i {{ display:grid; place-items:center; width:62px; height:62px; border-radius:50%; font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:40px; color:#05080d; }}
.vd.ok {{ color:{GREEN}; }} .vd.ok i {{ background:{GREEN}; }} .vd.no {{ color:{RED}; }} .vd.no i {{ background:{RED}; }}
"""

CSS += f"""
.ttl.band {{ left:0; right:0; padding:20px 30px 24px; background:rgba(5,8,13,.86); font-size:92px; }}
.ttl.band.cy .acc {{ color:{CYAN}; }}
.ttl.big2 {{ font-size:132px; }}
.grade {{ position:absolute; top:0; bottom:0; overflow:hidden; }}
.grade .tint {{ position:absolute; inset:0; background:#9c7347; mix-blend-mode:color; opacity:.48; }}
.grade .warm {{ position:absolute; inset:0; background:rgba(255,222,170,.16); mix-blend-mode:multiply; }}
.grade .grain {{ position:absolute; inset:0; background-image:{GRAIN}; background-size:240px 240px; opacity:.16; mix-blend-mode:overlay; }}
.grade .vig {{ position:absolute; inset:0; background:radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 52%, rgba(24,12,2,.5) 100%); }}
.era {{ position:absolute; right:40px; top:200px; padding:6px 14px; border-radius:8px; background:rgba(40,24,8,.75); {MONO} font-size:21px; letter-spacing:.14em; color:#f2d9b0; }}
.mapc {{ position:absolute; right:48px; top:1240px; display:grid; gap:12px; }}
.mr {{ display:flex; align-items:center; gap:16px; padding:10px 22px 10px 10px; border-radius:14px; background:rgba(30,18,6,.86); border:2px solid rgba(242,217,176,.3); }}
.mr i {{ display:grid; place-items:center; width:70px; height:70px; border-radius:12px; background:{Y}; color:#05080d; font-style:normal; {BC} font-size:60px; }}
.mr b {{ {BC} font-size:62px; color:#fff; }}
.sgrow {{ position:absolute; display:flex; align-items:center; gap:14px; }}
.sg {{ display:grid; place-items:center; width:84px; height:84px; border-radius:14px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.25); color:#fff; {BC} font-size:64px; }}
.sgr {{ margin-left:10px; padding:10px 20px; border-radius:14px; background:rgba(6,10,18,.9); {BC} font-size:58px; color:{Y}; white-space:nowrap; }}
.plab {{ position:absolute; left:40px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:50px; color:#fff; }}
.hseam {{ position:absolute; left:0; right:0; height:4px; background:rgba(255,255,255,.8); }}
.vseam {{ position:absolute; top:0; bottom:0; left:538px; width:4px; background:rgba(255,255,255,.8); box-shadow:0 0 16px rgba(0,0,0,.6); }}
.colh {{ position:absolute; top:520px; width:540px; display:grid; justify-items:center; gap:6px; text-align:center; }}
.colh span {{ padding:6px 18px; border-radius:10px; {BC} font-size:46px; color:#05080d; }}
.colh span.old {{ background:#f2d9b0; }} .colh span.new {{ background:{CYAN}; }}
.colh b {{ {BC} font-size:60px; line-height:.95; color:#fff; padding:6px 14px; background:rgba(5,8,13,.8); border-radius:12px; }}
.lens {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 52%, rgba(0,0,0,0) 30%, rgba(0,0,0,.92) 44%); }}
.lenstag {{ position:absolute; left:50%; transform:translateX(-50%); top:1420px; {MONO} font-size:24px; letter-spacing:.16em; color:{Y}; padding:6px 14px; border-radius:8px; background:rgba(6,10,18,.8); }}
.innc {{ position:absolute; left:48px; right:48px; top:1330px; display:grid; gap:10px; padding:18px; border-radius:16px; background:rgba(30,18,6,.88); }}
.innc .ih {{ {MONO} font-size:22px; letter-spacing:.1em; color:#f2d9b0; }}
.ir {{ display:flex; justify-content:space-between; align-items:center; padding:8px 16px; border-radius:10px; background:rgba(255,255,255,.06); }}
.ir i {{ font-style:normal; font-family:"Inter", sans-serif; font-weight:700; font-size:32px; color:#dfe5ec; }} .ir b {{ {BC} font-size:48px; color:{Y}; }}
.yr {{ position:absolute; left:0; right:0; top:1380px; display:grid; justify-items:center; gap:2px; }}
.yr span {{ {MONO} font-size:26px; letter-spacing:.16em; color:{CYAN}; }} .yr b {{ {BC} font-size:190px; line-height:.9; color:#fff; text-shadow:0 0 40px rgba(86,209,255,.45); }}
.pin.big span {{ font-size:120px; padding:4px 34px; background:{Y}; }}
"""

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "From finger signs to PitchCom", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Voiceover cue sheet", "", f"When each line starts, to land on its shots (the video is {D:.1f} s). Record your own read over assets/mix-novo.wav to these times.", "",
             "| Line | Starts |", "|---|---|"] + [f"| {x['text']} | {x['t0']:.1f} s |" for x in TMJ["lines"]]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
