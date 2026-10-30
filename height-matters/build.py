"""'Does height matter in baseball?': the 2026 World Series as the way in (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the two fastballs, the ground ball, the line drive -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/height-matters.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. The players are Brewers- and Rays-inspired
figures (team colors, no names or logos) scaled to illustrative heights; no figure stands for a real player and no
height is labeled. The only numbers on screen are the ones in the script (one Rays starter over six feet, per
reports; the 2023 study's 319 first-round picks) and a 6 ft reference line.
The release-point demo is simulated: the same 94 mph fastball to the same spot from a high and a lower release.
The strike zones are measured on the posed figures with the rulebook definition (midpoint of the shoulders and the
top of the pants, down to the hollow below the kneecap).
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc, R
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
HI, GB = P["pitches"]["hi"], P["gb"]
FL, TC = HI["flight"], HI["t_contact"]
T_SSF = TC + GB["t_field"]; T_SSREL = T_SSF + 0.62; T_SSC = T_SSREL + 0.95          # mirrors assets/field.js
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:'").lower() == word.lower().strip("'")]
    return hits[nth]["t1" if end else "t0"]
WI = lambda lid, i: LN(lid)["words"][i]["t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S = {x["id"]: x["t0"] - 0.06 for x in TM["lines"]}

# ----------------------------------------------------------------- shots (video time v) and the scene time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r
VHL = 1.0                                                     # the hook: the shorter players light up
VONE = W("rays", "one")
A2, A3, A4, A5, A6 = S["short"] - 0.02, S["rays"] - 0.02, S["q"] - 0.02, S["tall"] - 0.02, W("tall", "and") - 0.08
A7, A8, A9, A10 = S["but"] - 0.02, S["shortadv"] - 0.02, W("shortadv", "while") - 0.08, S["research"] - 0.08
A11, A12, A13, A14, A15 = W("study", "examining") + 0.6, W("study", "relationship") - 0.15, W("study", "and") - 0.08, S["take"] - 0.06, S["height"] - 0.04
M2, M3, M4, A16 = W("height", "player") - 0.04, W("height", "plays") + 0.12, W("height", "determine"), S["end"] - 0.06
rate(0.0, A2, "hookLine", 0.0, sc="lines", set="intro", rope="3b", hl="short", hlt=VHL)
rate(A2, A3, "wsWide", 0.0, sc="lines")
rate(A3, A4, "raysLine", A3, sc="lines", rope="1b", hl="tall", hlt=VONE)
rate(A4, A5, "qHigh", 0.0, sc="lines")
VSPAN = W("tall", "longer")
rate(A5, A6, "pair", 0.0, sc="pair", span=round(VSPAN - A5, 3))
VARR = W("tall", "release")                                   # the pitch reaches the plate as he says "release"
rate(A6, A7, "pitchSide", on(VARR, 0.0, A6), sc="pitch", tubes=2)
VREL = VARR - FL
rate(A7, A8, "batHero", 0.0, sc="bat")
VZS, VZT = W("shortadv", "smaller"), W("shortadv", "strike")
rate(A8, A9, "catcherV", 0.0, sc="bat", zone=round(VZS - A8, 3), ghost=round(VZT - A8, 3))
VLOW = W("shortadv", "lower")
rate(A9, A10, "ssLow", on(VLOW, T_SSF, A9), sc="field")
rate(A10, A11, "buildsA", 0.0, sc="builds")
rate(A11, A12, "buildsB", 0.0, sc="builds")
rate(A12, A13, "buildsC", 0.0, sc="builds")
rate(A13, A14, "buildsD", 2.0, sc="builds")
rate(A14, A15, "qHigh", 1.0, sc="lines")
# the montage: a taller pitcher, a shorter hitter, a shorter shortstop, a taller first baseman
VM1 = A15 + 0.42
rate(A15, M2, "pitcherCU", on(VM1, -FL, A15), sc="pitch")
VCT = W("height", "moves")
rate(M2, M3, "batSide", on(VCT, TC, M2), sc="bat", hit=1)
VF2 = M3 + 0.3
rate(M3, M4, "ssLow2", on(VF2, T_SSF, M3), sc="field")
VCATCH = VF2 + (T_SSC - T_SSF)
rate(M4, A16, "b1Low", on(VCATCH, T_SSC, M4), sc="field")
rate(A16, D, "endWide", 0.0, sc="lines")
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [0.0, VHL, A5, A10, A14, A16]:
    c.set("#flash", '{"opacity":0.55}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def words(wid, t0, t1, parts, top=300, cls="hk"):
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, (w, _) in enumerate(ws)) + "</span>" for i, (ws, k) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (ws, _) in enumerate(parts):
        for j, (_, ts_) in enumerate(ws):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.4, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.14, ease="power3.out"), ts_ - 0.03)
seq = lambda txt, t0, dt=0.07: [(w, t0 + dt * i) for i, w in enumerate(txt.split())]
wt = lambda lid, *ix: [(LN(lid)["words"][i]["w"].strip(",."), WI(lid, i)) for i in ix]

# ----------------------------------------------------------------- titles: the hook question, the question again, the takeaway, the last line
words("hook", 0.0, A2 - 0.02, [(seq("Does height", 0.04, 0.09), ""), (seq("actually matter", 0.24, 0.1), "acc"), (seq("in baseball?", 0.48, 0.09), "")], 300)
c.ft("#hookx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.05, duration=0.14, ease="power3.out"), VHL)
tag("tsh", VHL + 0.02, A2 - 0.02, "yl", "Shorter players, <b class='wh'>highlighted</b>", 1640)
tag("t6", 0.5, A2 - 0.02, "yl", "Yellow line: <b class='wh'>6 ft</b>", 1560)
words("q", WI("q", 0) - 0.03, A5 - 0.02, [(wt("q", 0, 1, 2), ""), (wt("q", 3, 4), "acc"), ([("in baseball?", WI("q", 5))], "")], 300, "hk mid")
words("take", WI("take", 0) - 0.03, A15 - 0.02, [([("The", WI("take", 0)), ("takeaway?", WI("take", 1))], "acc")], 300, "hk mid")

# ----------------------------------------------------------------- captions: the voiceover, word by word (the script's own spelling)
STUDY = [("A", 0), ("2023", 1), ("study", 3), ("examining", 4), ("|", 0), ("319", 5), ("first-round", 8), ("MLB", 9), ("draft", 12), ("picks", 13), ("|", 0),
         ("found", 14), ("no", 15), ("relationship", 16), ("between", 17), ("|", 0), ("players'", 18), ("physical", 19), ("measurements", 20), ("|", 0),
         ("in", 21), ("high", 22), ("school", 23), ("and", 24), ("their", 25), ("|", 0), ("eventual", 26), ("MLB", 27), ("performance,", 30), ("|", 0), ("measured", 31), ("by", 32), ("WAR.", 33)]
def chunks_from(lid, spec, acc):
    out, cur = [], []
    for w, i in spec:
        if w == "|": out.append(cur); cur = []; continue
        cur.append((w, WI(lid, i), w.strip(",.'").lower() in acc))
    out.append(cur); return [(lid, ch) for ch in out]
def plain(lid, i0, i1, acc=()):
    wd = LN(lid)["words"]; return [(lid, [(wd[n]["w"], wd[n]["t0"], n in acc) for n in range(i0, i1 + 1)])]
CAPS = (plain("short", 0, 3, (1, 3)) + plain("short", 4, 9, (8, 9)) + plain("short", 10, 14, (12, 13, 14))
        + plain("rays", 0, 5, (3,)) + plain("rays", 6, 9, (8,)) + plain("rays", 10, 13, (10, 12, 13))
        + plain("tall", 0, 4, (1,)) + plain("tall", 5, 6, (5, 6)) + plain("tall", 7, 11, (8,)) + plain("tall", 12, 15, (13, 14, 15))
        + plain("but", 0, 3, (2,)) + plain("but", 4, 7, (6,))
        + plain("shortadv", 0, 4, (1, 2)) + plain("shortadv", 5, 8, (6, 7, 8)) + plain("shortadv", 9, 12, (11, 12)) + plain("shortadv", 13, 16, ()) + plain("shortadv", 17, 20, (17, 20))
        + plain("research", 0, 4, (2,))
        + chunks_from("study", STUDY, {"2023", "319", "first-round", "no", "relationship", "physical", "war"})
        + plain("height", 0, 2, (0, 2)) + plain("height", 3, 8, (5, 6, 8)) + plain("height", 9, 12, (11, 12)) + plain("height", 13, 16, (14,))
        + plain("end", 0, 6, (1, 3)))
for k, (lid, ws) in enumerate(CAPS):
    ln = LN(lid); start = ws[0][1] - 0.06
    nxt = CAPS[k + 1] if k + 1 < len(CAPS) else None
    if nxt and nxt[0] == lid: end = nxt[1][0][1] - 0.06
    elif lid == "end": end = WI("end", 7) - 0.08
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    cid = f"cap{k}"; sp = []
    for n, (w, t0, a) in enumerate(ws):
        w = w.rstrip(",:") if n == len(ws) - 1 else w
        sp.append(f'<span class="cw{" acc" if a else ""}" id="{cid}w{n}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n, (w, t0, a) in enumerate(ws): c.ft(f"#{cid}w{n}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), t0 - 0.04)

# ----------------------------------------------------------------- the World Series, the lineups
c.clip("ws", A2 + 0.05, A4 - 0.02, '<div class="bnr" id="wsx"><b>2026 World Series</b><span>Brewers vs. Rays</span></div>', cls="layer", style="z-index:13"); pop("#wsx", A2 + 0.05, 10)
c.clip("ill", A2 + 0.05, A5 - 0.02, '<div class="rec" id="illx">Brewers- and Rays-inspired players · heights illustrative</div>', cls="layer", style="z-index:13"); pop("#illx", A2 + 0.2, 8)
pinl("pbw", W("short", "brewers") - 0.03, A3 - 0.02, "Brewers", "bwLine", "nv")
pinl("prs", W("short", "rays") - 0.03, A3 - 0.02, "Rays", "rsLine", "lb")
pinl("p6b", A3 + 0.15, A4 - 0.02, "6 ft", "rope1", "yl sm")
pinl("p1", VONE - 0.03, A4 - 0.02, "1 of 9 over 6 ft", "rayTall", "yl")
c.clip("src1", VONE, A4 - 0.02, '<div class="rec r2" id="src1x">Rays starting lineup: one starter over 6 ft, per reports</div>', cls="layer", style="z-index:13"); pop("#src1x", VONE + 0.05, 8)
# levers, release point
pinl("ptl", A5 + 0.25, A6 - 0.02, "Taller", "tallP", "yl")
pinl("psh", A5 + 0.35, A6 - 0.02, "Shorter", "shortP", "cy")
tag("tlev", VSPAN - 0.03, A6 - 0.02, "yl", "Longer arms: <b class='wh'>longer levers</b>", 1560)
VHR = W("tall", "higher")
pinl("phr", VHR - 0.03, A7 - 0.02, "Higher release", "hiRel", "yl")
pinl("plr", VHR + 0.1, A7 - 0.02, "Lower release", "loRel", "cy")
tag("tang", VARR + 0.05, A7 - 0.02, "wh", "Same pitch, same target: <b class='yl'>a steeper angle in</b>", 1560)
c.clip("sim", VARR + 0.05, A7 - 0.02, f'<div class="rec" id="simx">Simulated 94 mph fastball · comes in at {abs(HI["vaa"]):.1f}° vs {abs(P["pitches"]["lo"]["vaa"]):.1f}°</div>', cls="layer", style="z-index:13"); pop("#simx", VARR + 0.1, 8)
# the strike zone, getting low
pinl("pzs", VZS - 0.03, A9 - 0.02, "Shorter hitter’s zone", "zoneS", "yl")
pinl("pzt", VZT - 0.03, A9 - 0.02, "Taller hitter’s zone", "zoneT", "wh")
c.clip("rule", VZT + 0.1, A9 - 0.02, '<div class="rec" id="rulex">Zone: midpoint of shoulders and belt → hollow below the knee</div>', cls="layer", style="z-index:13"); pop("#rulex", VZT + 0.15, 8)
pinl("plow", VLOW - 0.08, A10 - 0.02, "Gets low", "ss", "yl")
# different builds, different jobs
for j, (key, lab) in enumerate([("bC", "C"), ("b1B", "1B"), ("bSS", "SS"), ("bCF", "CF"), ("bP", "P")]):
    pinl(f"pb{j}", A10 + 0.12 + 0.12 * j, A11 - 0.02, lab, key, "sm" + (" yl" if j % 2 else ""))
# the study card
VST, V319, VPK, VNO, VPH, VHS, VPF = W("study", "study"), W("study", "three"), W("study", "first-round"), W("study", "no"), W("study", "physical"), W("study", "high"), W("study", "performance")
c.clip("dim", VST - 0.1, A14 - 0.02, '<div class="dim" id="dimx"></div>', cls="layer", style="z-index:9"); c.ft("#dimx", o(opacity=0), o(opacity=1, duration=0.25), VST - 0.1)
c.clip("card", VST - 0.05, A14 - 0.02, f"""<div class="sc" id="scx">
  <div class="sh">2023 study · first-round MLB draft picks</div>
  <div class="sn"><b id="n319">0</b><span id="snl">first-round picks<br><i>2005–2015 drafts</i></span></div>
  <div class="sm2" id="smx"><span id="m1">High-school height</span><span id="m2">weight</span><span id="m3">BMI</span></div>
  <div class="sa" id="sax">↓</div>
  <div class="sw" id="swx">MLB performance (WAR)</div>
  <div class="sno" id="snox">No relationship found</div>
  <div class="sf">Journal of Strength and Conditioning Research, 2023</div>
</div>""", cls="layer", style="z-index:14")
c.ft("#scx", o(opacity=0, y=40), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VST - 0.05)
c.ft("#n319", o(innerText=0), o(innerText=319, snap=R("{innerText:1}"), duration=0.55, ease="power2.out"), V319 - 0.03)
pop("#snl", VPK - 0.03, 10)
pop("#snox", VNO - 0.03, 10); c.ft("#snox", o(scale=1.25), o(scale=1, duration=0.22, ease="back.out(2)"), VNO - 0.03)
for i, tt in enumerate([VPH, W("study", "measurements"), VHS]): pop(f"#m{i + 1}", tt - 0.03, 10)
pop("#sax", VPF - 0.15, 10); pop("#swx", VPF - 0.03, 10)
# the montage
pinl("pm1", A15 + 0.05, M2 - 0.02, "Taller pitcher", "bP", "yl sm")
pinl("pm2", M2 + 0.05, M3 - 0.02, "Shorter hitter", "batter", "cy sm")
pinl("pm3", M3 + 0.05, M4 - 0.02, "Shorter shortstop", "ss", "cy sm")
pinl("pm4", M4 + 0.05, A16 - 0.02, "Taller first baseman", "b1", "yl sm")
# the end
VT = WI("end", 7)
c.clip("endb", VT - 0.06, D, '<div class="endq" id="endx"><span id="ew0">Talent doesn’t come</span><br><em id="ew1">in one size.</em></div>', cls="layer", style="z-index:22")
c.ft("#endx", o(opacity=0), o(opacity=1, duration=0.15), VT - 0.06)
c.ft("#ew0", o(opacity=0, scale=1.3, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), VT - 0.03)
c.ft("#ew1", o(opacity=0, scale=1.3, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), WI("end", 10) - 0.03)
c.clip("ill2", A16 + 0.1, D, '<div class="rec" id="ill2x">Brewers- and Rays-inspired players · heights illustrative</div>', cls="layer", style="z-index:13"); pop("#ill2x", A16 + 0.2, 8)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -10)
cue("impact", 0.0, -3); cue("riser-s", 0.25, -8); cue("impact", VHL, -4); cue("tick", VHL, -4)
cue("popup", VONE, -5); cue("impact", W("q", "matter"), -5)
cue("popup", VSPAN, -7); cue("whoosh", VREL, -8); cue("glove", VARR, -2); cue("popup", VHR, -7)
cue("popup", VZS, -7); cue("popup", VZT, -8); cue("glove", VLOW, -2); cue("popup", VLOW, -8)
for j in range(5): cue("tap", A10 + 0.12 + 0.12 * j, -10)
cue("tick", V319, -4); cue("impact", VNO, -4); cue("popup", VPF, -8)
cue("impact", A14 + 0.05, -4)
cue("whoosh", VM1, -9); cue("glove", VF2, -3); cue("glove", VCATCH, -1)
cue("riser-m", VT - 1.2, -7); cue("impact", VT - 0.03, -2)
CRACKS = [(VCT, 0.9)]
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
    fx += crowd * 10 ** (-30 / 20)
    # the music bed: made for this video (lands its chord on the closing question), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, W("end", "talent"), style="drive", seed=63)
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
.hk.mid {{ font-size:132px; }}
.pin.sm span {{ font-size:36px; padding:6px 13px; }}
.pin.cy span {{ background:{CYAN}; }} .pin.wh span {{ background:#eef2f7; }}
.pin.nv span {{ background:#13294b; color:#ffc52f; border:3px solid #ffc52f; }} .pin.lb span {{ background:#8fbce6; color:#092c5c; border:3px solid #092c5c; }}
.rec.r2 {{ top:1770px; color:{Y}; }}
.sc {{ position:absolute; left:44px; right:44px; top:1000px; display:grid; gap:14px; padding:26px 30px 24px; {CARD} border:2px solid rgba(255,255,255,.14); }}
.sc .sh {{ {MONO} font-size:25px; letter-spacing:.12em; color:{MUTED}; }}
.sn {{ display:flex; align-items:center; gap:24px; }}
.sn b {{ {BC} font-size:190px; line-height:.85; color:{Y}; min-width:330px; }}
.sn span {{ {BC} font-size:62px; line-height:1; color:#fff; }} .sn i {{ {MONO} font-style:normal; font-size:26px; letter-spacing:.1em; color:{MUTED}; }}
.sm2 {{ display:flex; gap:12px; flex-wrap:wrap; }}
.sm2 span {{ padding:8px 16px; border-radius:10px; background:#1d2636; {BC} font-size:46px; }}
.sa {{ {BC} font-size:46px; line-height:.8; color:{MUTED}; padding-left:20px; }}
.sw {{ justify-self:start; padding:8px 16px; border-radius:10px; background:#1d2636; {BC} font-size:46px; color:#fff; }}
.sno {{ justify-self:start; padding:10px 22px; border-radius:12px; background:{HOT}; color:#05080d; {BC} font-size:66px; transform-origin:0 50%; }}
.sf {{ {MONO} font-size:20px; letter-spacing:.06em; color:{MUTED}; }}
.endq {{ position:absolute; left:0; right:0; top:830px; padding:26px 0 30px; background:rgba(5,8,13,.9); text-align:center; {BC} font-size:124px; line-height:.95; color:#fff; text-shadow:0 8px 34px rgba(0,0,0,.9); }}
.endq em {{ font-style:normal; color:{Y}; }}
.dim {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(4,7,12,0) 30%, rgba(4,7,12,.55) 52%, rgba(4,7,12,.7) 100%); }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Does height matter in baseball?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
