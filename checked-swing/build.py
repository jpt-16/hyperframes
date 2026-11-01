"""'What counts as a swing?': how umpires judge a checked swing (1080x1920, music + effects, no voice).

    python3 tools/physics.py                                       # the pitch and the checked-swing dribbler -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # a timing guide only: reads the script to place the shots
    python3 build.py                                               # index.html + assets/mix.wav (music + effects, mastered low for a voice on top)
    npx --yes hyperframes@0.8.154 render . -o renders/checked-swing.mp4 --video-bitrate 16M

The video ships without a voice: the narrator records it separately. The shots are timed to the script read at a
natural pace (assets/vo/timing.json, written by the guide read); CUES.md lists when each line lands. Visuals: the
check swing (frozen where the bat stops), a check vs a full swing from the side with the front of the plate as a
plane and the bat tip's path, a borderline check (no rule draws that line), the plate umpire's no-call, the appeal
(the catcher asks, the plate umpire points; a right-handed batter goes to the first-base umpire, a left-handed batter
to the third-base umpire; "yes he went" is the strike fist, "no" is the safe sign), a check swing that hits the ball
(a dribbler fair down the third-base line: in play), and the replay.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
FB, DRB = P["pitches"]["fb"], P["dribbler"]
FL, TC = FB["flight"], FB["t_contact"]
T_F = TC + DRB["t_field"]; T_REL3 = T_F + 0.45; T_C3 = T_REL3 + 1.05            # mirrors assets/field.js
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S = {x["id"]: x["t0"] - 0.08 for x in TM["lines"]}

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def vat(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
A2, A3, A4, A6, A10, A13 = S["think"], S["norule"], S["judge"], S["appeal"], S["live"], S["end"]
# 1 the hook: he starts, he checks it; freeze where the bat stops, push in on the bat
VFRZ = 1.2
shot(0.0, A2, "hook", [0.0, VFRZ, A2], [-1.25, -0.05, -0.05], play="check", depth=0, freeze=VFRZ, zv=VFRZ + 0.05)
# 2 "you might think it's as simple as whether the bat crosses home plate": a check (top) vs a full swing (bottom), from the side, slowed
VCR = W("think", "crosses")
half = dict(vs=[A2, VCR - 0.4, W("think", "but"), A3], ts=[-0.95, -0.35, 0.25, 0.42], cam="side", plane=-5, trail=-0.4, tipEnd=0.22)
shot(A2, A3, "side", [A2, A3], [0, 0], speed="slow", mode="split", top=dict(half, play="check", depth=0), bot=dict(half, play="full"))
# 3 "there is no universal rule…": a borderline check, frozen, the camera circling it
shot(A3, A4, "sideOrbit", [A3, A3 + 0.5, A4], [-0.3, 0.22, 0.22], play="check", depth=0.5, plane=-5, trail=-0.4, tipEnd=0.2, freeze=round(A3 + 0.5, 3))
# 4 "umpires use their judgment": from behind the plate, a check; the plate umpire stays down (ball)
A5 = W("judge", "determine") - 0.1
rate(A4, A5, "catcherV", -1.1, play="check", depth=0.15)
# 5 "…whether the batter attempted to strike the ball": close on the hands and bat, slowed
shot(A5, A6, "close", [A5, A6], [-0.55, 0.32], speed="slow", play="check", depth=0.15, trail=-0.4)
# 6-7 the appeal: "if the home plate umpire initially calls a pitch a ball" (over his shoulder), "the defensive team can appeal…" (from the front)
VBALL = W("appeal", "ball")
V0 = W("appeal", "plate") + 0.35                                              # the pitch arrives
A7 = W("appeal", "the", nth=0, end=False) if False else W("appeal", "defensive") - 0.18
APPEAL, POINT = W("appeal", "appeal") - V0, W("appeal", "checked") + 0.1 - V0
rate(A6, A7, "umpBack", A6 - V0, play="check", depth=0.15)
A8 = W("appeal", "first") - 0.06
rate(A7, A8, "front", A7 - V0, play="check", depth=0.15, appeal=round(APPEAL, 3), point=round(POINT, 3))
# 8 the whip to the first-base umpire on "first"
A9 = A8 + 0.62
CALL1 = A9 + 0.05 - V0
rate(A8, A9, "toFirst", A8 - V0, play="check", depth=0.15, appeal=round(APPEAL, 3), point=round(POINT, 3), call=round(CALL1 + 0.3, 3), callKind="yes", rings=["u1"])
# 9 "…or third base umpire. That umpire then makes the final decision.": the two umpires, split (right-handed batter: first; left-handed: third)
VC1, VC3 = W("appeal", "third") + 0.25, W("appeal", "umpire", nth=1) + 0.05
hv = dict(vs=[A9, A10], ts=[A9 - V0, A10 - V0], appeal=round(APPEAL, 3), point=round(POINT, 3), play="check", depth=0.15)
shot(A9, A10, "u1", [A9, A10], [0, 0], mode="split", top=dict(hv, cam="u1", call=round(VC1 - V0, 3), callKind="yes"), bot=dict(hv, cam="u3", lhb=1, call=round(VC3 - V0, 3), callKind="no"))
# 10 "and here's something interesting": runner on first
A11 = W("live", "if") - 0.1
VHIT = W("live", "hit")
rate(A10, A11, "wideHome", -3.3, play="contact", depth=0.15, rings=["r"])
# 11 "if the batter checks his swing but the ball is hit": contact on the check, from the side, slowed
A12 = VHIT + 0.42
shot(A11, A12, "side", [A11, VHIT, A12], [TC - 0.85, TC, TC + 0.17], speed="slow", play="contact", depth=0.15)
# 12 "into fair or foul territory, it's a live ball": the dribbler, the runner, the throw
VFAIR = W("live", "fair")
rate(A12, A13, "dribble", TC + 0.17, play="contact", depth=0.15, fair=round(TC + 0.17 + (VFAIR - A12), 3), rings=["r"])
DRS = SHOTS[-1]; VFIELD, VCATCH = vat(DRS, T_F), vat(DRS, T_C3)
# 13 the replay from the side: batter, catcher, umpire; slowed, the bat's path, where it ended up
VENDS = W("end", "ends")
A14 = W("end", "swing", nth=1) + 0.25
shot(A13, A14, "replay", [A13, A13 + 1.9, VENDS - 0.3, A14], [-1.0, -0.45, 0.25, 0.6], speed="replay", play="check", depth=0, trail=-0.4, tipEnd=0.24)
VTIP = vat(SHOTS[-1], 0.24) or VENDS - 0.3
rate(A14, D, "endWide", 0.6, r=0.15, play="check", depth=0)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]
VEND = A14 + 0.05; VBRAND = min(D - 1.6, VEND + 1.15)

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [VFRZ, A3, A9, VHIT, VBRAND]:
    c.set("#flash", '{"opacity":0.55}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def title(tid, t0, t1, lines, top=300, cls=""):
    """Big centered title, word by word (a quick stagger)."""
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.06 * i)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def note(nid, t0, t1, text, top=1560):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:13"); pop(f"#{nid}x", t0, 8)

# ----------------------------------------------------------------- 1 the hook
title("hook", 0.1, A2 - 0.02, [("What actually", False), ("counts as", False), ("a swing?", True)], 300, "big")
c.ft("#hookx", o(scale=1.0), o(scale=1.06, duration=0.14, ease="power3.out"), VFRZ)
# 2 the misconception (split)
c.clip("splt", A2, A3, """<div class="seam"></div>
  <div class="half t"><span class="hlab yl" id="hl1">Checked</span></div>
  <div class="half b"><span class="hlab hot" id="hl2">Full swing</span></div>""", cls="layer", style="z-index:11")
pop("#hl1", A2 + 0.1, 10); pop("#hl2", A2 + 0.2, 10)
c.clip("fp", VCR - 0.05, A3, '<div class="fpl" id="fpx">Blue line: the front of the plate</div>', cls="layer", style="z-index:13"); pop("#fpx", VCR, 8)
VBUT = W("think", "but")
title("t2", VBUT - 0.04, A3 - 0.02, [("It’s not just about", False), ("crossing the plate", True)], 870, "band")
title("t3", A3, A4 - 0.02, [("It’s not just about", False), ("crossing the plate", True)], 1250, "band")
# 3 no rule draws the line
note("n3", W("norule", "no") - 0.03, A4 - 0.02, "MLB’s rulebook doesn’t define a swing: <b>it’s the umpire’s call</b>", 1600)
pinl("pq", W("norule", "specific") - 0.03, A4 - 0.02, "Where’s the line?", "plane", "cy")
# 4-5 the umpire's judgment
pinl("pu", A4 + 0.2, A5 - 0.02, "Plate umpire", "ump", "")
title("t4", W("judge", "judgment") - 0.04, A6 - 0.02, [("The umpire", False), ("uses judgment", True)], 300)
pinl("ptip", W("judge", "attempted") - 0.03, A6 - 0.02, "An attempt to hit it?", "tip", "yl")
# 6-9 the appeal
chip("cb", VBALL - 0.03, A8 - 0.02, "Plate umpire: <b class='yl'>Ball</b>", 1560)
pinl("pc", A7 + APPEAL - (A7 - V0) + (A7 - V0) - 0.03 if False else V0 + APPEAL - 0.03, A8 - 0.02, "Catcher appeals", "catcher", "yl")
pinl("pp", V0 + POINT - 0.03, A8 - 0.02, "“Did he go?”", "ump", "")
title("t9", A9 + 0.02, A10 - 0.02, [("First or third", False), ("base umpire", True)], 870, "band")
c.clip("spl2", A9, A10, """<div class="seam"></div>
  <div class="half t"><span class="hlab yl" id="hm1">Right-handed batter → 1B umpire</span></div>
  <div class="half b"><span class="hlab yl" id="hm2">Left-handed batter → 3B umpire</span></div>""", cls="layer", style="z-index:11")
pop("#hm1", A9 + 0.1, 10); pop("#hm2", A9 + 0.2, 10)
c.clip("rs1", VC1 + 0.1, A10 - 0.02, '<div class="rs2 hot" id="rs1x" style="top:760px">“He went”: strike</div>', cls="layer", style="z-index:13"); pop("#rs1x", VC1 + 0.1, 10)
c.clip("rs2", VC3 + 0.1, A10 - 0.02, '<div class="rs2 cy" id="rs2x" style="top:1720px">“No swing”: ball</div>', cls="layer", style="z-index:13"); pop("#rs2x", VC3 + 0.1, 10)
VFIN = W("final", "final")
c.clip("fin", VFIN - 0.05, A10 - 0.02, '<div class="stamp" id="finx">Final call</div>', cls="layer", style="z-index:15")
c.ft("#finx", o(opacity=0, scale=1.8, rotation=-6), o(opacity=1, scale=1, rotation=-6, duration=0.18, ease="back.out(2)"), VFIN - 0.05)
# 10-12 the exception
VLIVE = W("live", "live")
pinl("prn", A10 + 0.3, A11 - 0.02, "Runner on first", "runner", "yl")
pinl("pch", VHIT - 0.45, A12 - 0.02, "Checked swing…", "batter", "")
pinl("pfair", VFAIR - 0.03, VFIELD, "Fair", "ball", "gr")
pinl("prun", VFAIR + 0.3, VLIVE - 0.1, "Runner goes", "runner", "yl")
title("t12", VLIVE - 0.05, A13 - 0.02, [("The ball is", False), ("still live!", True)], 300)
note("n12", W("live", "foul") - 0.03, A13 - 0.02, "Contact makes it a batted ball: <b>fair is in play; foul is a foul ball</b>", 1600)
# 13 the replay and the end
pinl("pend", VTIP - 0.03, W("end", "it's", nth=1) - 0.05, "Where the bat ended up", "mid", "yl")
pinl("patt", W("end", "attempted") - 0.03, VEND - 0.02, "Did he try to hit it?", "mid", "")
c.clip("nyk", VEND, VBRAND - 0.02, '<div class="ttl band nyk" id="nykx"><span class="tl acc">Now you know.</span></div>', cls="layer", style="z-index:22")
c.ft("#nykx", o(opacity=0, scale=1.25, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.22, ease="power3.out"), VEND)
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.2), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- sound (no voice: room left for the narrator)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -11)
cue("riser-s", 0.05, -6); cue("whoosh", 0.75, -9); cue("impact", VFRZ, -2); cue("tick", VFRZ, -4)
cue("popup", VCR, -9); cue("impact", VBUT, -6); cue("tick", A3 + 0.5, -6)
cue("glove", A4 + 1.1, -2); cue("impact", W("judge", "judgment"), -7)
cue("glove", V0, -2); cue("popup", VBALL, -8); cue("popup", V0 + APPEAL, -8); cue("popup", V0 + POINT, -8)
cue("whoosh", A8 + 0.05, -4); cue("impact", A9 + 0.02, -6)
cue("popup", VC1 + 0.1, -6); cue("popup", VC3 + 0.1, -7); cue("impact", VFIN - 0.05, -3)
cue("riser-s", A11 - 0.6, -9); cue("popup", VFAIR, -8); cue("glove", VFIELD, -3); cue("glove", VCATCH, -1); cue("impact", VLIVE - 0.05, -3)
cue("whoosh", A13 + 0.02, -8); cue("glove", vat(SHOTS[-2], 0.0), -6)
cue("impact", VEND, -3); cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
CRACKS = [(VHIT, 0.35)]
THUDS = []
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
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-27 / 20)                                             # stadium ambience
    # the music bed: subtle, lands its chord on the end card; no voice to duck under, so it sits low throughout
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="glow", seed=83)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 2.5, 0.55, 1.0)[:, None]               # builds in over the opening
    full = (fx + bed * ramp * 10 ** (-15 / 20)) * 10 ** (-6 / 20)
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre = os.path.join(HERE, ".pre.wav"); wav(pre, full)
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-20.0)    # low: headroom for a voice recorded on top
    os.remove(pre)
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
.half.b .hlab {{ top:40px; }}
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

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "What counts as a swing?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    cues = ["| Line | Starts | Scene |", "|---|---|---|"]
    names = {"q": "the hook", "think": "check vs full swing (split)", "norule": "the borderline check, circling", "judge": "the plate umpire; close on the bat",
             "appeal": "the call, the appeal, the whip to 1B, the two base umpires", "final": "the final call", "live": "contact on a check: the dribbler, live ball", "end": "the replay; Now you know; the end card"}
    for x in TM["lines"]: cues.append(f"| {x['text'] if 'text' in x else x['id']} | {x['t0']:.1f} s | {names[x['id']]} |")
    open(os.path.join(HERE, "CUES.md"), "w").write("# Voiceover cue sheet\n\nWhen each line of the script should start, to land on the shots it goes with (the video is " + f"{D:.1f}" + " s).\n\n" + "\n".join(cues) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
