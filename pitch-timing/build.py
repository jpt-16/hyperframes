"""'Why pitchers vary their timing' (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # the pitch -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael, 1.5x) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav without the voice) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/pitch-timing.mp4 --video-bitrate 16M

A right-handed pitcher in the stretch, a runner on first with a 12.5 ft lead, a right-handed batter. A meter on screen
shows how long the pitcher holds the set before his first move.
  1 the hook: two pitches, the same 1.2 s hold; the runner studying him
  2 the pattern: the same hold, pitch after pitch (split); the runner's eyes and feet, rocking in rhythm
  3 the jump: the same hold again; he goes as the pitcher moves (time to plate 1.48 s), the catcher's throw (pop time
    1.95 s), safe by about 0.2 s (3.3 s first move to the bag)
  4 the counters: a slide step (0.4 s hold, 1.23 s to the plate), a long 2.6 s hold (he leans at 1.2 s and has to
    stop), and a pickoff (a jump turn and a step straight at first; he dives back)
  5 the takeaway: a varied hold with looks at the runner, the pitch; the runner and the pitcher; the end card
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
FL = P["pitches"]["fb"]["flight"]
FIRST = {"pitch": 1.05, "quick": 0.8}                                         # mirrors assets/field.js
tmove = lambda kind="pitch": -0.55 if kind == "pick" else -FIRST[kind] - FL
tset = lambda kind="pitch", hold=1.2: tmove(kind) - hold
T_CREL, T_CAT = 0.8, 1.95; T_TAG = T_CAT + 0.12; T_SAFE = 1.85; PK_T = 0.55
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"

TMJ = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TMJ["lines"])}
LN = lambda lid: TMJ["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
WI = lambda lid, i: LN(lid)["words"][i]["t0"]
D = TMJ["duration"]
S = {x["id"]: x["t0"] - 0.08 for x in TMJ["lines"]}

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows, keyed to the voiceover
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r            # the play time at video time a, if play time t falls at video time v
def vat(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
TM, TS = tmove(), tset()
PITCH = dict(kind="pitch", hold=1.2)
BRK = TM - 0.02
# "Why do pitchers constantly change how long they take to deliver the ball?": a pitch from behind the runner; another, the same timing
A1 = 1.6
rate(0.0, A1, "behindR", TM - 0.3, **PITCH, runner="lead", meter=1, rings=["r"])
rate(A1, S["watch"], "side3b", TM - 0.25, **PITCH, runner="lead", meter=1)
# "Because runners are watching their every move.": his profile, his line of sight to the pitcher
rate(S["watch"], S["pattern"], "runnerFace", TS - 0.2, **PITCH, runner="watch", sight=round(TS, 3), meter=1)
# "When a pitcher repeatedly uses the same timing,": two pitches, side by side; first move on "same"
A4 = W("pattern", "baserunners") - 0.12
VSAME = W("pattern", "same")
half = dict(vs=[S["pattern"], A4], ts=[on(VSAME, TM, S["pattern"]), on(VSAME, TM, S["pattern"]) + (A4 - S["pattern"])], cam="side3b", kind="pitch", hold=1.2, runner="lead")
shot(S["pattern"], A4, "side3b", [S["pattern"], A4], [0, 0], mode="split", top=dict(half), bot=dict(half))
# "baserunners can recognize patterns and anticipate exactly when the ball is coming.": his feet, rocking in rhythm; the first move on "anticipate"
rate(A4, S["steal"], "runnerFeet", on(W("pattern", "anticipate"), TM, A4), **PITCH, runner="watch", meter=1)
# "This gives them a better opportunity to steal a base.": he goes as the pitcher moves (from up behind him)
VB1 = W("steal", "better")
rate(S["steal"], S["mix"], "highHome", on(VB1, BRK, S["steal"]), **PITCH, runner="steal", brk=round(BRK, 3), meter=1, rings=["r"])
J1 = SHOTS[-1]
# "That's why pitchers mix things up.": a hold, a look over at the runner
rate(S["mix"], S["vary"], "behindR", tset("pitch", 3.0) + 0.2, kind="pitch", hold=3.0, checks=[round(tset("pitch", 3.0) + 0.45, 3)], runner="lead")
MX = SHOTS[-1]
# "Sometimes they'll use a quick delivery," (a slide step on "quick")
TMQ = tmove("quick"); VQ = W("vary", "quick")
A8 = W("vary", "other") - 0.06
rate(S["vary"], A8 + 0.05, "side3b", on(VQ, TMQ, S["vary"]), kind="quick", hold=0.4, runner="hesitate", lean=round(TMQ + 0.18, 3), meter=1)
# "other times they'll take longer," (the hold has run 1.3 s at the cut; he leans, expecting it, and has to stop; the pitch at 2.6 s)
A8 += 0.05
TSL = tset("pitch", 2.6); A9 = W("vary", "and") - 0.06
rate(A8, A9, "highHome", TSL + 2.6 - (A9 - A8), kind="pitch", hold=2.6, runner="hesitate", lean=round(TSL + 1.45, 3), meter=1)
LH = SHOTS[-1]; VLEAN = vat(LH, TSL + 1.45) or A8 + 0.1
# "and they'll vary their pickoff moves to keep runners guessing." (the throw on "moves"; the dive back)
VPK = W("vary", "moves")
A10 = VPK + 0.55
rate(A9, A10, "pick", on(VPK, 0.0, A9), kind="pick", hold=1.0, runner="dive", arPk=-0.3, meter=1)
PKS = SHOTS[-1]
rate(A10, S["what"], "dive1", 0.55, kind="pick", hold=1.0, runner="dive")
# "But what happens if a pitcher doesn't change their timing?": the same 1.2 s again
rate(S["what"], S["jumps"], "side3b", on(W("what", "change"), TM, S["what"]), **PITCH, runner="lead", meter=1)
# "Runners can start getting bigger jumps," (he goes on "bigger", slowed) "stealing bases more easily," (the throw) "and putting pressure on the defense." (safe)
VJ = W("jumps", "bigger"); A13 = W("jumps", "stealing") - 0.1
shot(S["jumps"], A13, "wideR", [S["jumps"], VJ, A13], [BRK - (VJ - S["jumps"]), BRK, BRK + 0.35], speed="slow", slowStart=round(VJ, 3), **PITCH, runner="steal", brk=round(BRK, 3), meter=1, rings=["r"], arJump=round(BRK + 0.05, 3))
J = SHOTS[-1]; VBRK, VMOVE = vat(J, BRK), vat(J, TM)
A14 = W("jumps", "and") - 0.06
rate(A13, A14, "throwCam", on(W("jumps", "easily"), T_CREL, A13), **PITCH, runner="steal", brk=round(BRK, 3))
TH = SHOTS[-1]; VCATCH, VCREL = vat(TH, 0.0), vat(TH, T_CREL)
rate(A14, S["level"], "tag2", on(W("jumps", "defense"), T_TAG, A14), **PITCH, runner="steal", brk=round(BRK, 3))
TG = SHOTS[-1]; VTAG = vat(TG, T_TAG)
# "At higher levels, even a tiny timing advantage can make the difference between safe and out.": the play at second again, very slow; safe on "safe"
VSAFE = W("level", "safe")
shot(S["level"], S["end"], "tag2b", [S["level"], VSAFE, S["end"]], [T_SAFE - 0.75, T_SAFE + 0.02, T_TAG + 0.35], speed="replay", **PITCH, runner="steal", brk=round(BRK, 3))
RP = SHOTS[-1]; VRTAG = vat(RP, T_TAG)
# "In baseball, pitchers aren't just competing against hitters. They're competing against the runners, too.": the runner and the pitcher; the end card
rate(S["end"], D, "finalLow", -6.5, r=0.4, kind="pitch", hold=6.0, runner="watch", speed="slow")
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]
VBRAND = round(LN("end")["t1"] + 0.3, 3)

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [S["pattern"], S["mix"], S["jumps"], VBRAND]:
    c.set("#flash", '{"opacity":0.5}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)
METER = '<div class="meter{cls}" id="{id}" style="top:{top}px"><span class="ml">Set</span><div class="mb"><i class="mf"></i></div><b class="mv">0.0 s</b><em class="mk"></em></div>'
c.clip("mtc", 0, D, METER.format(cls="", id="mt", top=1530), cls="layer", style="z-index:13")

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


# ----------------------------------------------------------------- titles (in a lower band, under the captions) and the graphics
title("hook", 0.08, S["watch"] - 0.02, [("Why don’t pitchers", False), ("always use", False), ("the same timing?", True)], 240, "hk2")
c.clip("splt", S["pattern"], A4, """<div class="seam"></div>
  <div class="half t"><span class="hlab yl" id="hl1">Pitch 1</span></div>
  <div class="half b"><span class="hlab yl" id="hl2">Pitch 2</span></div>""", cls="layer", style="z-index:11")
pop("#hl1", S["pattern"] + 0.05, 10); pop("#hl2", S["pattern"] + 0.15, 10)
c.clip("mts", S["pattern"], A4, METER.format(cls=" sm", id="mtA", top=820) + METER.format(cls=" sm", id="mtB", top=1780), cls="layer", style="z-index:13")
c.clip("same", VSAME - 0.03, A4, '<div class="ttl band same" id="samex"><span class="tl acc">Same timing</span></div>', cls="layer", style="z-index:14")
c.ft("#samex", o(opacity=0, scale=1.2), o(opacity=1, scale=1, duration=0.2, ease="power3.out"), VSAME - 0.03)
title("t2", W("pattern", "patterns") - 0.04, S["steal"] - 0.02, [("Runners look", False), ("for patterns", True)], 1090, "mid")
pinl("pft", A4 + 0.1, S["steal"] - 0.02, "Rocking with his rhythm", "feet", "yl")
pinl("pgo1", vat(J1, BRK) - 0.03, S["mix"] - 0.02, "Gone on first move", "runner", "yl")
pinl("pck", vat(MX, tset("pitch", 3.0) + 0.45) - 0.03, S["vary"] - 0.02, "A look over", "pitcher", "cy")
def card(cid, t0, t1, n, text):
    c.clip(cid, t0, t1, f'<div class="nc" id="{cid}x"><i>{n}</i><b>{text}</b></div>', cls="layer", style="z-index:13")
    c.ft(f"#{cid}x", o(opacity=0, x=-60), o(opacity=1, x=0, duration=0.24, ease="power3.out"), t0)
card("c1", VQ - 0.05, A8 - 0.02, "1", "Quick to the plate")
card("c2", A8 + 0.02, A9 - 0.02, "2", "A long hold")
card("c3", A9 + 0.02, S["what"] - 0.02, "3", "Pickoff")
title("t4", W("mix", "mix") - 0.04, A8 - 0.02, [("Keep runners", False), ("guessing", True)], 1090, "mid")
pinl("ph2", VLEAN - 0.03, A9 - 0.02, "Go? Wait?", "runner", "")
pinl("ppk", VPK - 0.32, A10 - 0.02, "Steps toward first", "step", "")
pinl("pbk", A10 + 0.05, S["what"] - 0.02, "Back in time", "runner", "yl")
c.clip("same2", W("what", "change") - 0.03, S["jumps"] - 0.02, '<div class="chip" id="same2x" style="top:1180px">Same <b class="yl">1.2 s</b>, every pitch</div>', cls="layer", style="z-index:13"); pop("#same2x", W("what", "change") - 0.03, 10)
pinl("pmv", VMOVE - 0.03, A13 - 0.02, "First move", "pitcher", "cy")
pinl("pgo", VBRK - 0.03, A13 - 0.02, "He’s already going", "runner", "yl")
title("t3", VJ - 0.04, A14 - 0.02, [("Predictable timing", False), ("= better jumps", True)], 1090, "mid")
c.clip("safe", VTAG + 0.1, S["level"] - 0.02, '<div class="stamp" id="safex">Safe</div>', cls="layer", style="z-index:15")
c.ft("#safex", o(opacity=0, scale=1.8, rotation=-6), o(opacity=1, scale=1, rotation=-6, duration=0.18, ease="back.out(2)"), VTAG + 0.1)
c.clip("safe2", VSAFE - 0.03, S["end"] - 0.02, '<div class="stamp" id="safe2x">Safe</div>', cls="layer", style="z-index:15")
c.ft("#safe2x", o(opacity=0, scale=1.8, rotation=-6), o(opacity=1, scale=1, rotation=-6, duration=0.18, ease="back.out(2)"), VSAFE - 0.03)
note("n3", W("level", "tiny") - 0.03, S["end"] - 0.02, "Runner: <b>3.33 s</b> first move to the bag · the ball: <b>3.55 s</b> to the tag", 1660)
title("t5", WI("end", 2) - 0.04, VBRAND - 0.02, [("The battle isn’t just", False), ("against the hitter.", True)], 1090, "mid")
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.2), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- captions: the voiceover, word by word (the opening question is the big title instead)
CAPS = [("watch", 0, 6, {1: "acc", 3: "acc"}),
        ("pattern", 0, 3, {3: "acc"}), ("pattern", 4, 7, {6: "acc", 7: "acc"}), ("pattern", 8, 11, {11: "acc"}), ("pattern", 12, 14, {13: "acc"}), ("pattern", 15, 19, {17: "acc"}),
        ("steal", 0, 5, {4: "acc"}), ("steal", 6, 9, {7: "acc"}),
        ("mix", 0, 5, {3: "acc"}),
        ("vary", 0, 5, {4: "acc"}), ("vary", 6, 10, {10: "acc"}), ("vary", 11, 16, {15: "acc"}), ("vary", 17, 20, {20: "acc"}),
        ("what", 0, 5, {}), ("what", 6, 9, {6: "acc", 9: "acc"}),
        ("jumps", 0, 5, {4: "acc", 5: "acc"}), ("jumps", 6, 9, {6: "acc", 7: "acc"}), ("jumps", 10, 15, {12: "acc"}),
        ("level", 0, 2, {1: "acc"}), ("level", 3, 7, {5: "acc", 6: "acc"}), ("level", 8, 11, {11: "acc"}), ("level", 12, 15, {13: "acc", 15: "acc"}),
        ("end", 0, 7, {2: "acc", 7: "acc"}), ("end", 8, 13, {12: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TMJ["lines"]): end = min(ln["t1"] + 0.35, TMJ["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, VBRAND - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"]; w = w.rstrip(",:") if n == i1 and i1 > i0 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -12)
cue("riser-s", 0.0, -8); cue("impact", 0.08, -5)
for tid, tt in [("t2", W("pattern", "patterns")), ("t4", W("mix", "mix")), ("t3", VJ), ("t5", WI("end", 2))]: cue("impact", tt, -6)
for sh in SHOTS[:-1]:                                                         # every pitch: the whoosh out of his hand, the pop of the glove; ticks when he sets and when he moves
    if sh.get("mode") == "split": continue
    if sh.get("kind", "pitch") != "pick":
        cue("whoosh", vat(sh, -FL), -10); cue("glove", vat(sh, 0.0), -4)
    if sh.get("meter"): cue("tick", vat(sh, tset(sh.get("kind", "pitch"), sh.get("hold", 1.2))), -9); cue("tick", vat(sh, tmove(sh.get("kind", "pitch"))), -7)
sp = SHOTS[3]["top"]
for tt in [tset(), tmove()]: cue("tick", vat(sp, tt), -6)
cue("whoosh", vat(sp, -FL), -10); cue("glove", vat(sp, 0.0), -3)
cue("impact", VBRK, -7)
cue("whoosh", VCREL, -6); cue("glove", vat(TG, T_CAT), -2); cue("impact", VTAG + 0.1, -3); cue("impact", VSAFE - 0.03, -4)
cue("popup", VLEAN, -8); cue("whoosh", VPK, -7); cue("glove", VPK + PK_T, -2); cue("popup", VPK - 0.3, -8)
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
CRACKS = []
SLIDES = [(vat(TG, T_SAFE - 0.4) or A14 + 0.1, 0.8, 1.0), (vat(RP, T_SAFE - 0.4) or S["level"] + 0.1, 0.5, 0.3)]
THUDS = [(vat(PKS, 0.32) or A10 + 0.05, 0.5)]
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
    rng = np.random.default_rng(5)
    for vt, g, sl in SLIDES:
        x = slide(rng, 1 / sl if sl < 1 else 1.0); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g * 10 ** (-10 / 20)
    for vt, g in THUDS:
        x = thud(rng); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-30 / 20)                                             # stadium ambience
    # the music bed: tension under the holds, lands its chord on the end card; ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=91)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 3.0, 0.5, 1.0)[:, None]
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]; vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
    env = np.convolve(np.abs(vo).mean(1), np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
    duck = 10 ** (-7 * np.clip(env / 0.05, 0, 1) / 20)                         # up to 7 dB under the voice
    duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), "same")
    music = bed * ramp * duck[:, None] * 10 ** (-17 / 20)
    full = (fx + music) * 10 ** (-6 / 20) + vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, (fx + bed * ramp * 10 ** (-17 / 20)) * 10 ** (-6 / 20))
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
.meter {{ position:absolute; left:50%; transform:translateX(-50%); display:flex; align-items:center; gap:16px; padding:12px 22px; border-radius:14px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.14); opacity:0; }}
.meter .ml {{ {MONO} font-size:24px; letter-spacing:.14em; color:{MUTED}; }}
.meter .mb {{ position:relative; width:330px; height:16px; border-radius:8px; background:#1d2636; overflow:hidden; }}
.meter .mf {{ position:absolute; left:0; top:0; bottom:0; width:0; background:{CYAN}; border-radius:8px; }}
.meter .mv {{ {BC} font-size:54px; line-height:1; color:#fff; min-width:120px; text-align:right; }}
.meter .mk {{ {MONO} font-style:normal; font-size:22px; letter-spacing:.12em; color:{CYAN}; min-width:120px; }}
.meter.go .mf {{ background:{Y}; }} .meter.go .mk {{ color:{Y}; }}
.meter.sm {{ transform:translateX(-50%) scale(.82); }}
.ttl.same {{ top:880px; font-size:90px; padding:14px 0 18px; }}
.nc {{ position:absolute; left:40px; top:1380px; display:flex; align-items:center; gap:18px; padding:12px 24px 12px 12px; border-radius:16px; background:rgba(6,10,18,.88); border:2px solid rgba(255,255,255,.14); }}
.nc i {{ display:grid; place-items:center; width:84px; height:84px; border-radius:12px; background:{Y}; color:#05080d; font-style:normal; {BC} font-size:72px; }}
.nc b {{ {BC} font-size:60px; line-height:1; color:#fff; }}
.stamp {{ color:{Y}; top:1150px; }}
.ttl.hk2 {{ font-size:112px; }}
.ttl.mid {{ font-size:100px; text-shadow:0 6px 30px rgba(0,0,0,.95), 0 2px 6px rgba(0,0,0,.9); }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "Why pitchers vary their timing", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    cues = ["# Voiceover cue sheet", "", f"When each line starts, to land on its shots (the video is {D:.1f} s). Record your own read over assets/mix-novo.wav to these times.", "",
            "| Line | Starts |", "|---|---|"] + [f"| {x['text']} | {x['t0']:.1f} s |" for x in TMJ["lines"]]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(cues) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
