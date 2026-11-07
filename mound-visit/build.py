"""'What should a catcher say?' (1080x1920), cut to the voiceover.

    python3 tools/physics.py                                       # the pitches -> assets/play.json
    export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
    python3 build.py                # index.html + assets/mix.wav (+ mix-novo.wav without the voice) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/mound-visit.mp4 --video-bitrate 16M

One pitcher and one catcher throughout. The story runs on one clock (EV below), keyed to the narration: the hit, the
frustration, the visit (the catcher asks and listens first, then the calm talk, the breath, the plan), the imagined pitch,
back to work, the real pitch, the reset.
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
# ----------------------------------------------------------------- the story clock (video seconds), keyed to the narration
EV = dict(hit=0.45, hips=1.6, cap=2.1, look=2.7, cup=3.5, visit0=3.9, jog=[[3.9, 0.0], [5.4, 0.3], [5.42, 0.82], [6.5, 1.0]], visit1=6.5,
          ask=W("instead", "instead") + 0.05, ptalk=12.3, ptalk1=13.9, close0=14.4, close1=17.4, inhale=17.7, exhale=18.8, point=19.9,
          nod=25.6, tap=26.2, back0=26.6, back1=29.8, setP=30.6, rel=32.6, toss=34.9, reset=37.2, newb0=38.6, newb1=40.4)
VREL_V = 24.0                                                     # the imagined pitch's release, in play time
VBRAND = round(LN("end")["t1"] + 0.2, 3)

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def live(a, b, cam, **kw): shot(a, b, cam, [a, b], [a, b], **kw)
# 1 "When a pitcher starts struggling…": a single up the middle; the pitcher, hands on hips, the cap; the scoreboard
live(0.0, 1.5, "world", c0=[3.6, 7.2, -82.0], c1=[3.3, 7.0, -80.0], l=[0.0, 3.0, -30.0], f0=26)
live(1.5, 2.6, "obj", o="proot", lo="pneck", c0=[3.0, 6.4, 14.0], c1=[2.6, 6.2, 12.0], l=[0.0, -0.9, 0.0], f0=24)
live(2.6, 3.6, "world", c0=[-30.0, 20.0, -170.0], c1=[-34.0, 23.0, -190.0], l=[-70.0, 72.0, -432.0], f0=27, f1=23)
# 2 "Don't make it worse… figure out what's happening": mask up, the jog out; he asks, then listens
live(3.6, 5.4, "obj", o="croot", lo="croot", c0=[2.0, 5.0, -7.0], c1=[1.8, 5.2, -6.4], l=[0.0, 3.6, 14.0], f0=30)
live(5.4, 10.2, "world", c0=[14.0, 5.6, -55.2], c1=[12.4, 5.6, -55.3], l=[0.35, 7.3, -55.8], f0=30, f1=28)
live(10.2, 14.2, "world", c0=[-12.0, 6.0, -58.0], c1=[-11.0, 5.9, -57.8], l=[0.35, 7.0, -55.6], f0=30)
# 3 "The best thing to say is simple": the calm talk, mitts over mouths; the breath
live(14.2, 17.6, "world", c0=[12.5, 5.8, -54.6], c1=[11.4, 5.7, -54.9], l=[0.4, 6.6, -55.3], f0=26)
live(17.6, 19.7, "world", c0=[-9.5, 5.6, -55.4], c1=[-8.8, 5.5, -55.6], l=[0.2, 6.4, -56.9], f0=24)
# 4 "Focus on one target": he shows the spot; the imagined pitch from the pitcher's eyes, slowed, into the mitt
live(19.7, 21.2, "world", c0=[10.5, 5.2, -50.5], c1=[9.8, 5.1, -51.0], l=[0.4, 6.4, -55.2], f0=32)
VIS = dict(vision=1, rel=VREL_V)
shot(21.2, 22.6, "aim", [21.2, 22.6], [VREL_V - 2.65, VREL_V - 1.25], lo="glove", l=[0.0, 0.0, 0.0], c0=[0.1, 6.0, -59.4], f0=7.0, f1=5.4, **VIS)
SL, VS0 = 0.5, VREL_V - 0.6
shot(22.6, 24.8, "world", [22.6, 24.8], [VS0, VS0 + 2.2 * SL], speed="slow", c0=[1.2, 7.4, -76.0], c1=[1.1, 7.2, -74.4], l=[0.3, 2.6, 0.0], f0=13, **VIS)
VREL_VID = 22.6 + (VREL_V - VS0) / SL
VCATCH_V = 22.6 + (VREL_V + PI_["tgt"]["flight"] - VS0) / SL
live(24.8, 25.4, "obj", o="croot", lo="glove", c0=[-3.2, 1.6, 4.2], c1=[-3.0, 1.6, 3.9], l=[0.0, 0.0, 0.0], f0=24, **VIS)
# 5 "Bring his attention back to the next pitch": the nod, mitt to glove; back to work; set; the pitch
live(25.4, 26.9, "world", c0=[13.0, 5.6, -55.0], c1=[12.3, 5.5, -55.2], l=[0.35, 7.3, -55.8], f0=30)
live(26.9, 29.7, "world", c0=[2.5, 12.0, 23.0], c1=[2.2, 11.4, 20.5], l=[0.0, 3.0, -32.0], f0=36)
live(29.7, 33.0, "world", c0=[-9.5, 3.4, -44.5], c1=[-8.8, 3.2, -45.4], l=[0.0, 4.4, -58.5], f0=30)
# 6 "Confidence, a clear plan, and a reason to trust the next pitch": on the mitt; the throw back; both ready
live(33.0, 34.6, "obj", o="croot", lo="glove", c0=[-3.4, 1.8, 3.8], c1=[-3.6, 2.0, 4.2], l=[0.0, 0.2, 0.0], f0=26, tgtReal=1)
live(34.6, 37.3, "world", c0=[2.2, 7.6, 14.0], c1=[1.9, 7.4, 12.6], l=[0.0, 4.0, -40.0], f0=26)
live(37.3, 41.0, "world", c0=[0.4, 8.0, -68.8], c1=[0.4, 7.8, -67.8], l=[0.0, 3.0, 0.0], f0=24)
live(41.0, D, "world", c0=[0.9, 12.5, 31.0], c1=[0.8, 12.0, 28.0], l=[0.0, 4.6, -34.0], f0=26)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("vis", 21.2, 25.4, '<div class="visg"></div><div class="vistag" id="vistagx">Picture it</div>', cls="layer", style="z-index:2")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [3.6, 14.2, 21.2, 25.4, VBRAND]:
    c.set("#flash", '{"opacity":0.45}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def say(pid, t0, t1, who, text, key, label=None, cls=""):
    """A speech bubble over a player's head: who is 'C' (the catcher) or 'P' (the pitcher)."""
    lab = label or ("Catcher" if who == "C" else "Pitcher")
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="bub {who} {cls}" id="{pid}x"><i>{lab}</i><span>{text}</span></div></div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, y=16, scale=0.9), o(opacity=1, y=0, scale=1, duration=0.24, ease="back.out(1.8)"), t0); PINS.append([f"{pid}w", key])
def title(tid, t0, t1, lines, top=260, cls="hk2"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.06 * i)
BAND = 540                                                        # scene titles sit in a band low in the frame; captions own the top
def band(tid, t0, t1, lines): title(tid, t0, t1, lines, BAND, "band")
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:13"); pop(f"#{nid}x", t0, 8)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def rows(rid, t0, t1, head, items, top=BAND, extra="", cls=""):
    """A stacked card: each row (time, mark, text) pops on its word."""
    rs = "".join(f'<div class="hrow" id="{rid}r{i}"><i>{m}</i><span>{tx}</span></div>' for i, (_, m, tx) in enumerate(items))
    c.clip(rid, t0, t1, f'<div class="howto {cls}" style="top:{top}px"><div class="hhead" id="{rid}h">{head}</div>{rs}{extra}</div>', cls="layer", style="z-index:13")
    pop(f"#{rid}h", t0, 8)
    for i, (t, _, _) in enumerate(items): c.ft(f"#{rid}r{i}", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22, ease="power3.out"), t)

# ----------------------------------------------------------------- 1 the struggle (the hook title covers the opening line)
title("t1", 0.1, S["first"] + 0.04, [("What should a", False), ("catcher say?", True)])
pinl("phit", EV["hit"] + 0.3, 1.48, "Another hit", "pitcher", "")
pinl("pfr", EV["hips"], 2.58, "Frustrated", "pitcher", "sm")
# 2 don't make it worse; listen first
say("s0", W("list", "listing") - 0.05, S["instead"] - 0.02, "C", "You’re rushing. You’re up. Your arm’s late. Your front side…", "cmouth", "✕ Not this", "no")
band("b2", S["instead"] + 0.05, S["ask"] - 0.02, [("First: figure out", False), ("the problem", True)])
say("s1", EV["ask"], S["ask"] - 0.02, "C", "What’s going on?", "cmouth")
CK = [(W("ask", "rushing") - 0.05, "?", "Rushing?"), (W("ask", "losing") - 0.05, "?", "Losing confidence?"),
      (W("ask", "missing") - 0.05, "?", "Missing his spots?"), (W("ask", "struggling") - 0.05, "?", "Falling behind in counts?")]
rows("ck", S["ask"], S["simple"] - 0.02, "Listen first: what’s happening?", CK, extra='<div class="ckok" id="ckok">✓ Rushing: his answer</div>', cls="grid")
pop("#ckok", EV["ptalk"] + 0.1, 0)
say("s2", EV["ptalk"], S["simple"] - 0.02, "P", "I’m rushing. Everything’s up.", "pmouth")
# 3 keep it simple: the calm talk, the breath
band("b3", W("simple", "simple") - 0.03, 19.68, [("Keep it simple", True)])
qa, qb, qc = W("quote", "take"), W("quote", "slow"), W("quote", "we've")
say("s3", qa - 0.05, qb - 0.06, "C", "Take a breath.", "cmouth"); say("s4", qb - 0.05, qc - 0.06, "C", "Slow everything down.", "cmouth")
say("s5", qc - 0.05, LN("quote")["t1"] + 0.3, "C", "We’ve got this.", "cmouth")
chip("inh", EV["inhale"], EV["exhale"] - 0.05, "Inhale", 1560, "cy"); chip("exh", EV["exhale"], 19.68, "Exhale", 1560, "cy")
pinl("psh", EV["exhale"] + 0.4, 19.68, "Shoulders drop", "pchest", "sm")
# 4 command: one target
say("s6", EV["point"] + 0.2, 21.18, "C", "Low and away. Hit my glove.", "cmouth")
band("b4", W("command", "one") - 0.03, 25.38, [("One target.", False), ("One pitch at a time.", True)])
pinl("ptg", 21.4, 22.58, "The target", "tgt", "cy sm")
pinl("phit2", VCATCH_V + 0.03, 25.38, "Right on the glove", "glove", "cy sm")
# 5 frustration: the next pitch
band("b5", W("frus", "next") - 0.03, 26.88, [("Focus on the", False), ("next pitch", True)])
say("s7", EV["nod"] + 0.05, 26.88, "P", "Yeah. Next one.", "pmouth")
pinl("ptap", EV["tap"], 26.88, "Mitt to glove", "pchest", "sm")
note("nvis", 27.1, 29.68, "Every visit is different: command, frustration, tipping pitches, mechanics, signs, or just a breather.", 1700)
band("b6", W("tip", "specific") - 0.03, S["big"] - 0.02, [("One specific", False), ("adjustment", True)])
pinl("pgl", W("tip", "specific") - 0.03, 31.9, "Example: same glove set, every pitch", "pchest", "sm")
# 6 don't fix everything; confidence, a plan, trust
band("b7", W("fix", "fix") - 0.03, S["trust"] - 0.02, [("Not everything", False), ("in one talk", True)])
pinl("pcl", EV["rel"] + 0.5, 34.58, "Right where he set up", "glove", "cy sm")
rows("tr", S["trust"], S["because"] - 0.02, "What he leaves him with", [(W("trust", "confidence") - 0.05, "1", "Confidence"),
     (W("trust", "plan") - 0.25, "2", "A clear plan"), (W("trust", "trust") - 0.05, "3", "Trust in the next pitch")])
band("b8", W("end", "it's") - 0.03, VBRAND - 0.02, [("Good catchers don’t", False), ("just call pitches.", False), ("They build confidence.", True)])
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.2), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- captions: the voiceover, word by word
# The opening line is the hook title; the quoted line ("Take a breath…") is the catcher's speech bubbles instead.
CAPS = [("first", 0, 2, {1: "acc"}), ("first", 3, 6, {6: "acc"}),
        ("list", 0, 6, {2: "acc"}), ("list", 7, 10, {9: "acc"}), ("list", 11, 15, {15: "acc"}),
        ("instead", 0, 3, {}), ("instead", 4, 7, {4: "acc", 5: "acc"}),
        ("ask", 0, 3, {3: "acc"}), ("ask", 4, 5, {5: "acc"}), ("ask", 6, 8, {8: "acc"}), ("ask", 9, 14, {14: "acc"}),
        ("simple", 0, 3, {}), ("simple", 4, 7, {7: "acc"}),
        ("command", 0, 6, {6: "acc"}), ("command", 7, 12, {}), ("command", 13, 16, {15: "acc", 16: "acc"}), ("command", 17, 22, {22: "acc"}),
        ("frus", 0, 3, {3: "acc"}), ("frus", 4, 7, {}), ("frus", 8, 11, {10: "acc", 11: "acc"}), ("frus", 12, 15, {14: "acc"}),
        ("tip", 0, 7, {5: "acc", 7: "acc"}), ("tip", 8, 11, {11: "acc"}), ("tip", 12, 16, {}), ("tip", 17, 20, {19: "acc", 20: "acc"}),
        ("big", 0, 4, {3: "acc", 4: "acc"}),
        ("fix", 0, 5, {}), ("fix", 6, 10, {7: "acc", 9: "acc", 10: "acc"}),
        ("trust", 0, 4, {4: "acc"}), ("trust", 5, 7, {6: "acc", 7: "acc"}), ("trust", 8, 11, {}), ("trust", 12, 15, {12: "acc"}),
        ("because", 0, 1, {}), ("because", 2, 5, {4: "acc"}), ("because", 6, 9, {}), ("because", 10, 14, {14: "acc"}),
        ("end", 0, 5, {}), ("end", 6, 10, {7: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); wd = ln["words"]; i1 = min(i1, len(wd) - 1)
    start = wd[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = wd[CAPS[k + 1][1]]["t0"] - 0.06
    elif IDX[lid] + 1 < len(TMJ["lines"]): end = min(ln["t1"] + 0.35, TMJ["lines"][IDX[lid] + 1]["t0"] - 0.1)
    else: end = min(ln["t1"] + 0.3, VBRAND - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = wd[n]["w"]
        w = w.rstrip(",:") if n == i1 and i1 > i0 else w
        w = w.replace("'", "’")
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1):
        c.ft(f"#{cid}w{n - i0}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), wd[n]["t0"] - 0.04)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8)
for tt in [0.1, S["instead"] + 0.05, W("command", "one") - 0.03, W("frus", "next") - 0.03, W("end", "it's") - 0.03]: cue("impact", tt, -6)
cue("whoosh", EV["hit"] - PI_["fb"]["flight"], -9)
cue("whoosh", VREL_VID, -10); cue("glove", VCATCH_V, -1)
cue("whoosh", EV["rel"], -6); cue("glove", EV["rel"] + PI_["tgt"]["flight"], 0)
cue("glove", EV["toss"] + 0.75, -8)
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
CRACKS = [EV["hit"]]
LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}

def crack(rng):
    """Ash bat on a ball: a hard broadband click and a short wooden ring."""
    t = np.arange(int(0.6 * SR)) / SR
    click = rng.standard_normal(len(t)) * np.exp(-t / 0.0025)
    ring = sum(a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d) for f, a, d in [(1150, .55, .05), (1720, .4, .035), (2380, .3, .025), (640, .3, .07)])
    x = click * 0.9 + ring + np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.03) * 0.5
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
    for vt in CRACKS:
        x = crack(rng); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * 10 ** (-4 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-28 / 20)
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="glow", seed=141)
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
.ttl.t3l {{ font-size:100px; }}
.bub {{ position:absolute; left:-260px; width:520px; bottom:30px; display:flex; flex-direction:column; align-items:center; }}
.bub i {{ font-style:normal; {MONO} font-size:20px; letter-spacing:.14em; color:{MUTED}; margin-bottom:6px; padding:3px 10px; border-radius:6px; background:rgba(6,10,18,.75); }}
.bub span {{ position:relative; padding:14px 24px; border-radius:22px; background:#f4f6f8; color:#0b1018; font-family:"Inter", sans-serif; font-weight:800; font-size:40px; line-height:1.15; text-align:center; box-shadow:0 8px 26px rgba(0,0,0,.45); }}
.bub span::after {{ content:""; position:absolute; left:50%; bottom:-16px; margin-left:-14px; border:14px solid transparent; border-top-color:#f4f6f8; border-bottom:0; }}
.bub.P span {{ background:{Y}; }} .bub.P span::after {{ border-top-color:{Y}; }}
.chip.cy {{ color:{CYAN}; }} .chip b.y {{ color:{Y}; }}
.chip .ear::before {{ content:"●"; color:{CYAN}; margin-right:12px; font-size:40px; vertical-align:middle; }}
.visg {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 50%, rgba(10,40,70,0) 34%, rgba(4,14,28,.78) 78%); mix-blend-mode:normal; }}
.vistag {{ position:absolute; right:40px; top:200px; padding:6px 14px; border-radius:8px; background:rgba(6,18,30,.8); {MONO} font-size:22px; letter-spacing:.16em; color:{CYAN}; text-transform:uppercase; }}
"""

CSS += f"""
.ttl.band {{ font-size:88px; padding:18px 30px 22px; }}
.bub.no span {{ background:#2a1416; color:#ffb3b3; text-decoration:line-through; text-decoration-color:{RED}; text-decoration-thickness:4px; border:3px solid {RED}; }}
.bub.no span::after {{ border-top-color:{RED}; }}
.bub.no i {{ color:#fff; background:{RED}; }}
.howto {{ top:1360px; }}
.hhead {{ {MONO} font-size:24px; letter-spacing:.14em; color:{MUTED}; padding:6px 12px; justify-self:start; border-radius:8px; background:rgba(6,10,18,.8); }}
.hrow {{ padding:10px 22px 10px 12px; }} .hrow i {{ width:56px; height:56px; font-size:44px; background:{Y}; }} .hrow + .hrow i {{ background:{Y}; }}
.hrow span {{ {BC} font-family:"Barlow Condensed", sans-serif; font-size:52px; line-height:1; color:#fff; }}
.ckok {{ position:absolute; right:0; top:-8px; padding:6px 14px; border-radius:10px; background:{GREEN}; color:#05080d; {BC} font-size:40px; }}
.howto.grid {{ grid-template-columns:1fr 1fr; }} .howto.grid .hhead {{ grid-column:1 / -1; }} .howto.grid .hrow span {{ font-size:44px; }}

"""

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS, "ev": EV}
    h = c.page(CSS, "What should a catcher say?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Voiceover cue sheet", "", f"When each line starts, to land on its shots (the video is {D:.1f} s). Record your own read over assets/mix-novo.wav to these times.", "",
             "| Line | Starts |", "|---|---|"] + [f"| {x['text']} | {x['t0']:.1f} s |" for x in TMJ["lines"]]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
