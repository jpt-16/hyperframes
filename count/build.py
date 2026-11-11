"""'The count' (1080x1920, music + effects; the narration is recorded separately).

    python3 tools/physics.py        # the pitches and the foul ball -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (music + effects, mastered low for a voice on top) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/count.mp4 --video-bitrate 16M

One pitcher, batter, catcher and umpire throughout. Every count is on the center-field board (B / S / O lights and the
numbers) and in a broadcast-style count bug on screen. The strike zone and where each pitch crossed it are drawn at the
front of the plate; a pitch is a strike if any part of the ball touches the zone.
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
D = 40.5
Y, CYAN, WHITE, HOT, MUTED, GREEN, RED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6", "#3DD68C", "#FF4D4D"
D_SWEET = round(2.30 - 0.283, 3)
TC = lambda pk: PI_[pk]["t_contact"]
FRONT = lambda pk: PI_[pk]["front"]

SHOTS = []
BD = None
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    if "board" not in kw and BD: kw["board"] = BD
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def live(a, b, cam, **kw): shot(a, b, cam, [a, b], [a, b], **kw)
def vt(play, after=0.0):
    for s in SHOTS:
        if s["a"] < after: continue
        for (v0, v1), (t0, t1) in zip(zip(s["vs"], s["vs"][1:]), zip(s["ts"], s["ts"][1:])):
            if t1 > t0 and t0 <= play <= t1: return v0 + (play - t0) / (t1 - t0) * (v1 - v0)
    return None
TOPP, BOTP = [0, 0, 1080, 960], [0, 960, 1080, 960]
def ab(pk, rel, hold=1.0, hit=None, swing=False, check=None): return dict(pk=pk, rel=rel, tell=dict(glove="hi", hold=hold), hit=hit, swing=swing, check=check, D=D_SWEET)
BOARDCAM = dict(c0=[-30.0, 20.0, -170.0], c1=[-36.0, 24.0, -196.0], l=[-70.0, 62.0, -432.0], f0=27, f1=22)
UMPV = dict(c0=[-0.4, 8.6, 12.5], c1=[-0.4, 8.5, 12.0], l=[-0.7, 2.3, -3.0], f0=24)
UMPVF = dict(c0=[-0.4, 7.8, 12.5], c1=[-0.4, 7.7, 11.8], l=[-0.6, 2.7, -3.0], f0=46)
CF = dict(c0=[-3.0, 9.0, -112.0], c1=[-3.0, 9.0, -110.0], l=[-0.9, 3.2, 0.0], f0=7.5, f1=7.2)
# 1 the hook: a 95 mph fastball, frozen just before it reaches the hitter; the same pitch at 0-2 and at 3-0
BD = [[0, -1, 0, 1, "95"]]
HR = 1.6; AH = ab("hook", HR, hold=0.7)
live(0.0, 1.65, "world", ab=AH, streak=1, board=[[0, 0, 0, 1]], c0=[-2.4, 6.6, -70.0], c1=[-2.2, 6.4, -69.0], l=[0.0, 4.0, -20.0], f0=26)
FZ = HR + 0.3
live(1.65, FZ, "world", ab=AH, streak=1, c0=[5.2, 3.3, -4.0], c1=[5.0, 3.3, -3.2], l=[0.0, 4.2, -40.0], f0=30)
shot(FZ, 4.2, "world", [FZ, 4.2], [FZ, FZ], speed="freeze", ab=AH, zone=1, panes=[dict(rect=TOPP), dict(rect=BOTP)], c0=[1.6, 6.4, 10.5], c1=[1.4, 6.2, 9.8], l=[-0.4, 3.0, -8.0], f0=30)
# 2 0-2: the board; a slider just off the plate; he has to start the swing and holds up; the zone, slowed
BD = [[0, 0, 2, 1, ""]]
live(4.2, 5.4, "world", board=[[4.2, 0, 2, 1]], **BOARDCAM)
R2 = 6.9; A2 = ab("sl02", R2, swing=True, check=0.1)
live(5.4, 7.85, "world", ab=A2, **CF)
shot(7.85, 10.2, "world", [7.85, 10.2], [R2 + 0.2, R2 + 0.2 + 2.35 * 0.3], speed="slow", ab=A2, zone=1, mark=1, c0=[2.4, 7.0, 12.5], c1=[2.2, 6.9, 11.8], l=[0.0, 2.6, -3.0], f0=40)
# 3 3-0: the board; a fastball just off the plate, taken; ball four; he drops the bat and jogs to first
BD = [[0, 3, 0, 1, ""]]
live(10.2, 11.0, "world", board=[[10.2, 3, 0, 1]], **BOARDCAM)
R3 = 12.6; A3 = ab("fb30", R3)
live(11.0, 13.4, "world", ab=A3, zone=1, mark=1, **UMPVF)
live(13.4, 14.6, "world", board=[[13.4, 3, 0, 1], [13.75, 4, 0, 1, "BALL FOUR"]], **BOARDCAM)
BD = [[0, 4, 0, 1, "BALL FOUR"]]
live(14.6, 17.2, "world", ab=A3, bwalk=[14.7, 17.9], c0=[-24.0, 7.5, 10.0], c1=[-21.0, 7.2, 6.0], l=[10.0, 2.4, -14.0], f0=32)
# 4 1-1: the board; the same pitch moment, two outcomes: a strike (1-2) and a ball (2-1)
BD = [[0, 1, 1, 1, ""]]
live(17.2, 18.2, "world", board=[[17.2, 1, 1, 1]], **BOARDCAM)
R4 = 20.0
A4S, A4B = ab("st11", R4), ab("bl11", R4)
shot(18.2, 25.2, "world", [18.2, 19.7, 21.9, 25.2], [18.2, 19.7, 20.6, 23.9], speed="rt", zone=1, mark=1,
     panes=[dict(rect=TOPP, ab=A4S, ucall=R4 + FRONT("st11") + 0.15), dict(rect=BOTP, ab=A4B)], **UMPV)
# 5 3-2: the board; he comes set (a long hold); the hitter's hands; the pitch from the hitter's eyes; fouled back to stay alive
BD = [[0, 3, 2, 1, "FULL COUNT"]]
live(25.2, 26.2, "world", board=[[25.2, 3, 2, 1, "FULL COUNT"]], **BOARDCAM)
R5 = 31.4; A5 = ab("fb32", R5, hold=2.2, hit="foul32", swing=True)
live(26.2, 28.4, "world", ab=A5, c0=[-9.0, 3.2, -48.0], c1=[-8.4, 3.4, -50.0], l=[0.0, 5.4, -60.4], f0=26, f1=22)
live(28.4, 30.0, "obj", ab=A5, o="bat", lo="bat", bokeh=2.4, close=1, fore=1, c0=[1.65, 0.4, 0.3], c1=[1.45, 0.38, 0.24], l=[0.0, 0.3, 0.0], f0=30)
live(30.0, 31.6, "world", ab=A5, streak=1, c0=[-3.3, 7.0, 3.2], c1=[-3.3, 6.95, 2.9], l=[0.0, 5.0, -60.4], f0=14, f1=16)
S5 = 0.3
shot(31.6, 33.0, "world", [31.6, 33.0], [R5 + 0.05, R5 + 0.05 + 1.4 * S5], speed="slow", ab=A5, ghost=0.016, zone=1, c0=[2.8, 3.4, -8.6], c1=[2.5, 3.3, -8.0], l=[-1.6, 3.0, -1.6], f0=34)
T5 = R5 + 0.05 + 1.4 * S5
shot(33.0, 34.2, "world", [33.0, 34.2], [T5 - 0.1, T5 + 0.42], speed="slow", ab=A5, streak=1, c0=[5.0, 3.0, -22.0], c1=[5.0, 3.6, -23.5], l=[-1.0, 9.5, 8.0], f0=56)
# 6 the four counts, quickly; then the stadium
BD = [[0, 0, 2, 1, ""]]
shot(34.2, 34.8, "world", [34.2, 34.8], [R2 + TC("sl02") - 0.1, R2 + TC("sl02") - 0.1], speed="freeze", ab=A2, **dict(CF, f0=7.0))
BD = [[0, 3, 0, 1, ""]]
shot(34.8, 35.4, "world", [34.8, 35.4], [R3 + 0.5, R3 + 0.5], speed="freeze", ab=A3, zone=1, mark=1, **UMPVF)
BD = [[0, 1, 1, 1, ""]]
shot(35.4, 36.0, "world", [35.4, 36.0], [R4 + 0.6, R4 + 0.6], speed="freeze", ab=A4S, zone=1, mark=1, ucall=R4 + FRONT("st11") + 0.15, **UMPVF)
BD = [[0, 3, 2, 1, "FULL COUNT"]]
shot(36.0, 36.6, "world", [36.0, 36.6], [R5 + TC("fb32") + 0.01, R5 + TC("fb32") + 0.01], speed="freeze", ab=A5, ghost=0.016, c0=[2.8, 3.4, -8.6], l=[-1.6, 3.0, -1.6], f0=34)
VBRAND = 38.7
live(36.6, D, "world", board=[[36.6, 3, 2, 1, "FULL COUNT"]], c0=[14.0, 58.0, 92.0], c1=[10.0, 78.0, 128.0], l=[0.0, 0.0, -150.0], f0=42, f1=46)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:3")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [4.2, 10.2, 17.2, 25.2, 34.2, 34.8, 35.4, 36.0, 36.6]:
    c.set("#flash", '{"opacity":0.45}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def pinl(pid, t0, t1, text, key, cls="", pane=0):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key, pane])
def title(tid, t0, t1, lines, top=250, cls="hk2"):
    k, spans = 0, []
    for ln, acc in lines:
        ws = []
        for w in ln.split(): ws.append(f'<span class="tw" id="{tid}{k}">{esc(w)}</span>'); k += 1
        spans.append(f'<span class="tl{" acc" if acc else ""}">{" ".join(ws)}</span>')
    c.clip(tid, t0, t1, f'<div class="ttl {cls}" id="{tid}x" style="top:{top}px">{"".join(spans)}</div>', cls="layer", style="z-index:22")
    for i in range(k): c.ft(f"#{tid}{i}", o(opacity=0, scale=1.45, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), t0 + 0.06 * i)
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="note" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:13"); pop(f"#{nid}x", t0, 8)
def chip(cid, t0, t1, html, top, cls=""):
    c.clip(cid, t0, t1, f'<div class="chip {cls}" id="{cid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:13"); pop(f"#{cid}x", t0, 10)
def panes2(pid, t0, t1, a, b, top=150):
    c.clip(pid, t0, t1, f'<div class="vseam"></div><div class="plab" style="left:270px;top:{top}px" id="{pid}a">{a}</div><div class="plab cy" style="left:810px;top:{top}px" id="{pid}b">{b}</div>', cls="layer", style="z-index:15")
    pop(f"#{pid}a", t0 + 0.05, 10); pop(f"#{pid}b", t0 + 0.15, 10)
def panesTB(pid, t0, t1, a, b):
    c.clip(pid, t0, t1, f'<div class="hseam2"></div><div class="plab" style="left:200px;top:560px" id="{pid}a">{a}</div><div class="plab cy" style="left:200px;top:1520px" id="{pid}b">{b}</div>', cls="layer", style="z-index:15")
    pop(f"#{pid}a", t0 + 0.05, 10); pop(f"#{pid}b", t0 + 0.15, 10)
def panesTB(pid, t0, t1, a, b):
    c.clip(pid, t0, t1, f'<div class="hseam2"></div><div class="plab" style="left:230px;top:60px" id="{pid}a">{a}</div><div class="plab cy" style="left:230px;top:1020px" id="{pid}b">{b}</div>', cls="layer", style="z-index:15")
    pop(f"#{pid}a", t0 + 0.05, 10); pop(f"#{pid}b", t0 + 0.15, 10)
def frz(fid, t0, t1):
    c.clip(fid, t0, t1, f'<div class="frz" id="{fid}x">Freeze</div>', cls="layer", style="z-index:31"); pop(f"#{fid}x", t0, 6)
def tbar(bid, t0, t1, top, fill0, fill1, label, cls=""):
    c.clip(bid, t0, t1, f'<div class="tbar {cls}" style="top:{top}px"><i>Time in the set</i><div class="tb"><span id="{bid}f"></span></div><b id="{bid}l">{label}</b></div>', cls="layer", style="z-index:16")
    c.ft(f"#{bid}f", o(width="0%"), o(width="100%", duration=fill1 - fill0, ease="none"), fill0)
    c.ft(f"#{bid}l", o(opacity=0, scale=0.6), o(opacity=1, scale=1, duration=0.2, ease="back.out(2)"), fill1)
def tag(tid, t0, t1, text, cls=""):
    c.clip(tid, t0, t1, f'<div class="tagc {cls}" id="{tid}x">{text}</div>', cls="layer", style="z-index:16"); pop(f"#{tid}x", t0, 10)


def dots(n, mx, cls): return "".join(f'<i class="{cls if k < n else "off"}"></i>' for k in range(mx))
def bug(bid, t0, t1, b, s_, o_, top=60, label=None):
    """A broadcast-style count bug: balls and strikes as lights, and the count in big numbers."""
    big = "WALK" if b >= 4 else f"{b}-{s_}"
    lab = f'<em>{label}</em>' if label else ""
    c.clip(bid, t0, t1, f'<div class="bug" id="{bid}x" style="top:{top}px"><div class="bl"><span>B</span>{dots(min(b, 3), 3, "b")}<span>S</span>{dots(s_, 2, "s")}<span>O</span>{dots(o_, 2, "o")}</div><b class="{"w" if b >= 4 else ""}">{big}</b>{lab}</div>', cls="layer", style="z-index:18")
    pop(f"#{bid}x", t0, 8)
def meter(mid, t0, t1, p0, p1=None, tch=None, top=1560, label=""):
    """Who the count favors: a marker between PITCHER and HITTER."""
    c.clip(mid, t0, t1, f'<div class="meter" style="top:{top}px"><span class="pl">Pitcher</span><div class="tr"><div class="mk" id="{mid}m" style="left:{p0 * 100:.0f}%"></div></div><span class="hl">Hitter</span>{f"<em>{label}</em>" if label else ""}</div>', cls="layer", style="z-index:17")
    pop(f"#{mid}m", t0 + 0.05, 6)
    if p1 is not None: c.to(f"#{mid}m", o(left=f"{p1 * 100:.0f}%", duration=0.45, ease="power3.inOut"), tch)
def stamp(sid, t0, t1, big, small):
    c.clip(sid, t0, t1, f'<div class="stampc" id="{sid}x"><b>{big}</b><span>{small}</span></div>', cls="layer", style="z-index:21")
    c.ft(f"#{sid}x", o(opacity=0, scale=1.25), o(opacity=1, scale=1, duration=0.18, ease="power3.out"), t0)

# 1 the hook
title("t1", 0.1, FZ - 0.02, [("95 mph", True)], 240, "hk2")
# (no count bug in the first two hook shots: the pitch has no count yet)
panesTB("pp", FZ, 4.18, "", "")
bug("g1a", FZ + 0.05, 4.18, 0, 2, 1, 60, "Pitcher’s count"); bug("g1b", FZ + 0.12, 4.18, 3, 0, 1, 1020, "Hitter’s count")
title("t1b", FZ + 0.15, 4.18, [("Same pitch.", False), ("Different advantage.", True)], 852, "band")
# 2 0-2
title("t2", 4.3, 10.18, [("0-2: Pitcher’s", False), ("advantage", True)], 240)
bug("g2", 5.4, 10.18, 0, 2, 1)
meter("m2", 5.5, 10.18, 0.18)
pinl("p2a", vt(R2 + TC("sl02") - 0.1, 5.4), 7.83, "He starts the swing… and holds up", "batter", "sm")
pinl("p2b", vt(R2 + FRONT("sl02"), 7.85) + 0.1, 10.18, "Just off the plate", "mark", "gr sm")
note("n2", 8.1, 10.18, "<b>Hitter:</b> anything close could be strike three, so he has to protect the zone.<br><b>Pitcher:</b> can work just off the plate and try to get a chase.", 1680)
# 3 3-0
title("t3", 10.3, 17.18, [("3-0: Hitter’s", False), ("advantage", True)], 240)
bug("g3", 11.0, 13.38, 3, 0, 1)
meter("m3", 11.05, 17.18, 0.85)
chip("c3", 11.1, 12.55, "One more ball is a walk", 1450, "rd")
pinl("p3", vt(R3 + FRONT("fb30"), 11.0) + 0.1, 13.38, "Ball four: just off the plate", "mark", "gr sm")
bug("g3b", 13.75, 17.18, 4, 0, 1)
note("n3", 14.7, 17.18, "At 3-0 the pitcher can’t afford another ball, so the hitter can wait for a strike he likes.", 1700)
# 4 1-1
title("t4", 17.3, 18.18, [("1-1", True)], 240, "hk2 big1")
bug("g4", 17.25, 18.18, 1, 1, 1)
CR4 = vt(R4 + FRONT("st11"), 18.2)
bug("g4a", 18.25, CR4 + 0.4, 1, 1, 1, 60); bug("g4b", 18.3, CR4 + 0.4, 1, 1, 1, 1020)
bug("g4c", CR4 + 0.42, 25.18, 1, 2, 1, 60, "Strike: pitcher ahead"); bug("g4d", CR4 + 0.5, 25.18, 2, 1, 1, 1020, "Ball: hitter ahead")
panesTB("pq", 18.2, 25.18, "", "")
title("t4b", 18.3, 25.18, [("1-1: The next pitch", False), ("changes everything", True)], 852, "band")
meter("m4a", 18.4, 25.18, 0.5, 0.3, CR4 + 0.45, 780); meter("m4b", 18.45, 25.18, 0.5, 0.68, CR4 + 0.5, 1740)
pinl("p4a", CR4 + 0.1, 25.18, "Strike", "mark", "sm", 0); pinl("p4b", CR4 + 0.15, 25.18, "Ball", "mark", "gr sm", 1)
# 5 3-2
title("t5", 25.3, 34.18, [("3-2: Every pitch", False), ("matters", True)], 240)
bug("g5", 26.2, 34.18, 3, 2, 1)
meter("m5", 26.3, 30.0, 0.5, label="Both under pressure")
note("n5", 26.4, 29.98, "<b>Hitter:</b> a strike he takes is strike three.<br><b>Pitcher:</b> a ball is ball four.", 1700)
pinl("p5", vt(R5 + TC("fb32"), 31.6) + 0.15, 32.98, "Fouled off: he stays alive", "batter", "yl sm")
chip("c5", 33.1, 34.18, "Foul with two strikes: still <b class=\"y\">3-2</b>", 1500)
# 6 the four counts
stamp("s1", 34.2, 34.78, "0-2", "Pitcher’s advantage"); stamp("s2", 34.8, 35.38, "3-0", "Hitter’s advantage")
stamp("s3", 35.4, 35.98, "1-1", "Up for grabs"); stamp("s4", 36.0, 36.58, "3-2", "Every pitch matters")
title("t6", 36.75, VBRAND - 0.02, [("The count is more", False), ("than a number.", True)], 300)
c.clip("brand", VBRAND, D, """<div class="brand ov" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.3), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- sound (no voice: room left for the narrator)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -13)
cue("riser-s", 0.0, -8)
for tt in [0.1, FZ, 4.3, 10.3, 17.3, 18.3, 25.3, 34.2, 34.8, 35.4, 36.0, 36.75]: cue("impact", tt, -6)
for tt in [4.25, 10.25, 13.75, 17.25, 25.25, CR4 + 0.42]: cue("tick", tt, -8)
for a_, after in [(AH, 0), (A2, 5.4), (A3, 11.0), (A4S, 18.2), (A5, 30.0)]: cue("whoosh", vt(a_["rel"], after), -8)
for a_, after in [(A2, 7.85), (A3, 11.0), (A4S, 18.2)]: cue("glove", vt(a_["rel"] + PI_[a_["pk"]]["flight"], after), -1)
CRACKS = [(vt(R5 + TC("fb32"), 31.6), True)]
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
LEVEL = {"impact": -3.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}
def crack(rng, slow=False):
    """Ash bat on a ball: a hard broadband click and a short wooden ring (lower and longer in slow motion)."""
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
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="pulse", seed=181)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 3.0, 0.5, 1.0)[:, None]
    full = (fx + bed * ramp * 10 ** (-16 / 20)) * 10 ** (-6 / 20)
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre = os.path.join(HERE, ".pre.wav"); wav(pre, full)
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-20.0)
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
.ttl.hk2 {{ font-size:112px; }} .ttl.band {{ font-size:88px; padding:18px 30px 22px; }} .ttl.big1 {{ font-size:220px; }}
.bug {{ position:absolute; left:40px; display:flex; align-items:center; gap:22px; padding:12px 22px 12px 18px; border-radius:16px; background:rgba(6,10,18,.9); border:2px solid rgba(255,255,255,.16); box-shadow:0 8px 26px rgba(0,0,0,.5); }}
.bug .bl {{ display:grid; grid-template-columns:auto repeat(3, 26px); gap:6px 8px; align-items:center; }}
.bug .bl span {{ {MONO} font-size:22px; color:{MUTED}; }} .bug .bl span:nth-of-type(n) {{ grid-column:1; }}
.bug .bl i {{ width:24px; height:24px; border-radius:50%; background:#1b2230; border:2px solid #2c3646; }}
.bug .bl i.b {{ background:{GREEN}; border-color:{GREEN}; }} .bug .bl i.s {{ background:{RED}; border-color:{RED}; }} .bug .bl i.o {{ background:{Y}; border-color:{Y}; }}
.bug b {{ {BC} font-size:118px; line-height:.9; color:#fff; letter-spacing:.02em; }} .bug b.w {{ color:{Y}; font-size:96px; }}
.bug em {{ font-style:normal; {BC} font-size:46px; color:{Y}; max-width:330px; line-height:1; }}
.meter {{ position:absolute; left:60px; right:60px; display:grid; grid-template-columns:auto 1fr auto; gap:18px; align-items:center; padding:14px 22px; border-radius:16px; background:rgba(6,10,18,.85); }}
.meter span {{ {BC} font-size:44px; }} .meter .pl {{ color:{HOT}; }} .meter .hl {{ color:{CYAN}; }}
.meter .tr {{ position:relative; height:18px; border-radius:9px; background:linear-gradient(90deg, {HOT}, #3a4250 50%, {CYAN}); }}
.meter .mk {{ position:absolute; top:50%; width:44px; height:44px; margin:-22px 0 0 -22px; border-radius:50%; background:#fff; border:5px solid #05080d; box-shadow:0 0 0 3px #fff; }}
.meter em {{ grid-column:1 / -1; justify-self:center; font-style:normal; {MONO} font-size:22px; letter-spacing:.12em; color:{MUTED}; text-transform:uppercase; }}
.stampc {{ position:absolute; left:0; right:0; top:620px; display:grid; justify-items:center; gap:10px; }}
.stampc b {{ {BC} font-size:300px; line-height:.9; color:#fff; text-shadow:0 10px 40px rgba(0,0,0,.85); }}
.stampc span {{ padding:8px 22px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:64px; color:{Y}; }}
.brand.ov {{ background:radial-gradient(ellipse at 50% 45%, rgba(10,16,28,.72), rgba(3,6,11,.55)); }}
.pin.gr span {{ background:{GREEN}; }} .ttl.big2 {{ font-size:124px; }} .ttl.h3 {{ font-size:104px; }}
.frz {{ position:absolute; right:44px; top:150px; padding:8px 16px; border-radius:8px; background:rgba(6,10,18,.8); {MONO} font-size:22px; letter-spacing:.14em; color:{CYAN}; }}
.frz::before {{ content:"❚❚ "; }}
.tbar {{ position:absolute; left:48px; width:520px; display:grid; grid-template-columns:1fr auto; gap:6px 14px; align-items:center; padding:12px 18px; border-radius:14px; background:rgba(6,10,18,.88); }}
.tbar i {{ grid-column:1 / -1; font-style:normal; {MONO} font-size:20px; letter-spacing:.12em; color:{MUTED}; }}
.tbar .tb {{ height:18px; border-radius:9px; background:#26303f; overflow:hidden; }} .tbar .tb span {{ display:block; height:100%; width:0; background:{WHITE}; }}
.tbar.yl .tb span {{ background:{Y}; }} .tbar b {{ {BC} font-size:52px; color:#fff; }} .tbar.yl b {{ color:{Y}; }}
.lens {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 38%, rgba(0,0,0,.9) 62%); }}
.lenstag {{ position:absolute; left:50%; top:1480px; transform:translateX(-50%); padding:6px 16px; border-radius:8px; background:rgba(6,10,18,.85); {MONO} font-size:24px; letter-spacing:.14em; color:{CYAN}; text-transform:uppercase; }}
.vseam {{ position:absolute; top:0; bottom:0; left:538px; width:4px; background:rgba(255,255,255,.8); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.plab {{ position:absolute; transform:translateX(-50%); padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:54px; white-space:nowrap; color:{Y}; }}
.plab.cy {{ color:{CYAN}; }}
.hseam2 {{ position:absolute; left:0; right:0; top:958px; height:4px; background:rgba(255,255,255,.8); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.tagc {{ position:absolute; left:0; right:0; margin:0 auto; width:max-content; top:1400px; padding:8px 24px; border-radius:12px; background:#05080d; border:3px solid {WHITE}; color:#fff; {BC} font-size:50px; white-space:nowrap; }}
.chip.seamc {{ background:{WHITE}; color:#05080d; font-size:50px; padding:6px 24px; z-index:20; }}
.chip.hdr {{ font-size:52px; padding:8px 22px; }} .chip .vsd {{ color:{MUTED}; }}
.chip.rd {{ color:#fff; }} .chip .radar {{ color:{Y}; font-size:84px; vertical-align:-4px; }}
.pin.cy span {{ background:{CYAN}; }}
"""

HEAD = '<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'
SCENES = [("0.0", "4.2", "A 95 mph fastball, frozen just before it reaches the hitter; split: the same pitch at 0-2 and at 3-0", "SAME PITCH. DIFFERENT ADVANTAGE."),
          ("4.2", "10.2", "The board: 0-2; a slider just off the plate; he starts the swing and holds up; the zone and where it crossed, slowed", "0-2: PITCHER'S ADVANTAGE"),
          ("10.2", "17.2", "The board: 3-0; a fastball just off the plate, taken; the board: ball four, walk; he drops the bat and jogs to first", "3-0: HITTER'S ADVANTAGE"),
          ("17.2", "25.2", "The board: 1-1; split: the same pitch moment, a strike (1-2) and a ball (2-1)", "1-1: THE NEXT PITCH CHANGES EVERYTHING"),
          ("25.2", "34.2", "The board: 3-2, full count; he comes set and holds; the hitter's hands; the pitch from his eyes; fouled back", "3-2: EVERY PITCH MATTERS"),
          ("34.2", "36.6", "The four counts, one after another", "0-2 · 3-0 · 1-1 · 3-2"),
          ("36.6", f"{D:.1f}", "Wide over the stadium; Baseball Decoded", "THE COUNT IS MORE THAN A NUMBER.")]
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The count", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    lines = ["# Scene timing for the voiceover", "", f"The video is {D:.1f} s. Record each part of the narration inside its scene (times in seconds).", "",
             "| From | To | Scene | On screen |", "|---|---|---|---|"] + [f"| {a} | {b} | {d} | {t} |" for a, b, d, t in SCENES]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
