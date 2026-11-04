"""'How catchers adjust to the hitter' (1080x1920, music + effects; the narration is recorded separately).

    python3 tools/physics.py        # the pitches -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (music + effects, mastered low for a voice on top) + CUES.md
    npx --yes hyperframes@0.8.154 render . -o renders/catcher-setup.mp4 --video-bitrate 16M

The same catcher and plate umpire throughout. The umpire works from the slot: between the catcher and the batter, on the
batter's side, so he moves across when a left-handed hitter steps in. The catcher sets up to the pitch that was called
(inside, outside, on the edge), late, then takes the glove to the ball with a small move and holds it. Two marks keep
the pitch's location apart from the glove's: where the ball crossed the front of the plate (the zone, where the call is
made) and where it was caught, 3.6 ft behind it.
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
D = 43.5
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def vat(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
def pitch_shot(a, b, cam, k, vcatch, **kw):                    # a pitch caught at video time vcatch; the catcher sets up 1.3 s before
    rate(a, b, cam, -(vcatch - a), pitch=k, setup=-1.3, **kw)
    return SHOTS[-1]
# 1 the hook (0-5): a right-handed hitter steps in, the catcher and umpire get down; a left-handed hitter in the other box; freeze
rate(0.0, 2.3, "broadcast", 0.0, walk=1.6, rings=[])
shot(2.3, 5.0, "broadcast", [2.3, 4.0, 5.0], [0.0, 1.7, 1.7], lhb=1, walk=1.5, freeze=4.0)
# 2 the right-handed hitter (5-14): from above; then over the umpire's shoulder, an inside pitch and an outside pitch
rate(5.0, 7.6, "overhead", 3.0, rings=["bat", "c", "u"])
V_IN, V_OUT = 9.7, 13.0
pitch_shot(7.6, 10.8, "umpView", "inR", V_IN, zone=-9, sight=-1.6, marks=-0.2)
pitch_shot(10.8, 14.0, "umpView", "outR", V_OUT, zone=-9, sight=-9, marks=-0.2)
# 3 the left-handed hitter (14-23): he steps in; the umpire moves to the other slot; then right vs left, split
rate(14.0, 17.2, "overhead", 0.0, lhb=1, walk=1.4, umpMove=0.9, rings=["bat", "u"])
V_SP = 21.0
half = dict(vs=[17.2, 23.0], ts=[-(V_SP - 17.2), 23.0 - V_SP], cam="umpView", setup=-1.3, zone=-9, sight=-9, marks=-0.2)
shot(17.2, 23.0, "umpView", [17.2, 23.0], [0, 0], mode="split", top=dict(half, pitch="outR"), bot=dict(half, pitch="outL", lhb=1))
# 4 the catcher's adjustment (23-33): an inside pitch, an outside pitch, one on the edge (slowed at the catch)
V4 = [25.4, 28.7, 32.0]
A1 = pitch_shot(23.0, 26.3, "umpView", "inR", V4[0], zone=-9, sight=-9, marks=-0.2)
A2 = pitch_shot(26.3, 29.6, "frontC", "outR", V4[1], marks=-0.2)
shot(29.6, 33.0, "umpView", [29.6, 31.4, 32.6, 33.0], [-2.1, -0.3, 0.18, 0.58], speed="slow", pitch="edgeR", setup=-1.3, zone=-9, sight=-9, marks=-0.2)
A3 = SHOTS[-1]; V4[2] = vat(A3, 0.0)
# 5 the takeaway (33-43.5): an edge pitch to each hitter, received cleanly; the throw back; the end card
V5 = [35.0, 37.8]
B1 = pitch_shot(33.0, 35.8, "sideCatch", "edgeR", V5[0], marks=-0.2)
B2 = pitch_shot(35.8, 38.6, "sideCatch", "edgeL", V5[1], lhb=1, marks=-0.2)
VTOSS = 39.7
rate(38.6, D, "toss", 38.6 - V5[1], pitch="edgeL", lhb=1, setup=-1.3, toss=round(VTOSS - V5[1], 3))
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]
VBRAND = 41.3

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [4.0, 5.0, 14.0, 23.0, 33.0, VBRAND]:
    c.set("#flash", '{"opacity":0.5}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

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


def card(cid, t0, t1, n, text):
    c.clip(cid, t0, t1, f'<div class="nc" id="{cid}x"><i>{n}</i><b>{text}</b></div>', cls="layer", style="z-index:13")
    c.ft(f"#{cid}x", o(opacity=0, x=-60), o(opacity=1, x=0, duration=0.24, ease="power3.out"), t0)
def marks(pid, vcatch, t1, cross="Crossed the zone", glove="Caught here"):
    pinl(pid + "a", vcatch - 0.02, t1, cross, "cross", "yl sm"); pinl(pid + "b", vcatch + 0.08, t1, glove, "glove", "cy sm")

# ----------------------------------------------------------------- 1 the hook
title("hook", 0.08, 4.98, [("Why does catcher", False), ("positioning change", False), ("with the hitter?", True)], 260, "hk2")
chip("hr", 0.5, 2.28, "Right-handed hitter", 1560); chip("hl", 2.45, 4.98, "Left-handed hitter", 1560, "lb")
# 2 the right-handed hitter
title("t2", 5.08, 13.98, [("The hitter", False), ("changes the view", True)], 260, "hk2")
pinl("pb", 5.3, 7.58, "Batter", "batter", "")
pinl("pc", 5.6, 7.58, "Catcher", "catcher", "yl")
pinl("pu", 5.9, 7.58, "Umpire: in the slot", "ump", "cy")
pinl("peye", 7.9, 10.78, "Umpire’s view", "eye", "cy sm")
chip("ci", 8.0, 10.78, "Inside pitch", 1740); chip("co", 11.0, 13.98, "Outside pitch", 1740)
marks("m1", V_IN, 10.78); marks("m2", V_OUT, 13.98)
# 3 the left-handed hitter
title("t3", 14.08, 22.98, [("Opposite side.", False), ("Different angle.", True)], 260, "hk2")
pinl("pu2", 14.9, 17.18, "Umpire moves to the other slot", "ump", "cy")
pinl("pb2", 15.4, 17.18, "Left-handed hitter", "batter", "")
c.clip("splt", 17.2, 23.0, """<div class="seam"></div>
  <div class="half t"><span class="hlab yl" id="hs1">Right-handed hitter</span></div>
  <div class="half b"><span class="hlab yl" id="hs2">Left-handed hitter</span></div>""", cls="layer", style="z-index:11")
pop("#hs1", 17.25, 10); pop("#hs2", 17.35, 10)
# 4 the adjustment
title("t4", 23.08, 32.98, [("Positioning", False), ("+ presentation", True)], 260, "hk2")
card("k1", 23.1, 26.28, "1", "Inside"); card("k2", 26.4, 29.58, "2", "Outside"); card("k3", 29.7, 32.98, "3", "On the edge")
note("n4", 23.4, 26.28, "He sets up for the pitch that’s called: <b>inside, outside or on the edge</b>, depending on the hitter and the situation", 1640)
pinl("pset", V4[1] - 1.25, V4[1] - 0.05, "Sets up outside", "catcher", "yl")
marks("m3", V4[0], 26.28); marks("m4", V4[1], 29.58); marks("m5", V4[2], 32.98, "Crossed the edge", "Caught off the plate")
note("n5", V4[2] + 0.1, 32.98, "The call is where it <b>crosses the zone</b>, not where it’s caught. Good receivers catch it cleanly and hold it.", 1640)
# 5 the takeaway
chip("r1", 33.1, 35.78, "Right-handed hitter · on the edge", 1560); chip("r2", 35.9, 38.58, "Left-handed hitter · on the edge", 1560, "lb")
pinl("pq1", V5[0] + 0.1, 35.78, "Quiet glove", "glove", "cy sm"); pinl("pq2", V5[1] + 0.1, 38.58, "Quiet glove", "glove", "cy sm")
title("t5", 38.7, VBRAND - 0.02, [("Elite catchers read", False), ("the entire field.", True)], 1480, "hk2")
c.clip("brand", VBRAND, D, """<div class="brand" id="brx"><div class="bmark"><svg viewBox="0 0 100 100" width="150" height="150"><circle cx="50" cy="50" r="44" fill="#f4f2ec" stroke="#05080d" stroke-width="3"/>
  <path d="M26 16 C40 34 40 66 26 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/><path d="M74 16 C60 34 60 66 74 84" fill="none" stroke="#ff6a3d" stroke-width="4" stroke-dasharray="6 5"/></svg></div>
  <div class="bname"><span>Baseball</span><em>Decoded</em></div></div>""", cls="layer", style="z-index:24")
c.ft("#brx", o(opacity=0), o(opacity=1, duration=0.2), VBRAND)
c.ft(".bmark", o(scale=0.4, rotation=-120), o(scale=1, rotation=0, duration=0.5, ease="back.out(1.6)"), VBRAND)
c.ft(".bname", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), VBRAND + 0.15)

# ----------------------------------------------------------------- sound (no voice: room left for the narrator)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -12)
cue("riser-s", 0.0, -8)
for tt in [0.08, 4.0, 5.08, 14.08, 23.08, 38.7]: cue("impact", tt, -6)
FLs = {k: v["flight"] for k, v in PI_.items()}
for vc, k in [(V_IN, "inR"), (V_OUT, "outR"), (V4[0], "inR"), (V4[1], "outR"), (V5[0], "edgeR"), (V5[1], "edgeL")]:
    cue("whoosh", vc - FLs[k], -10); cue("glove", vc, -1); cue("tick", vc - 0.03, -8)
cue("glove", V_SP, 0); cue("whoosh", V_SP - 0.43, -9)
cue("whoosh", vat(A3, -FLs["edgeR"]), -10); cue("glove", V4[2], 0); cue("tick", V4[2] - 0.05, -6)
cue("popup", 14.9, -8); cue("whoosh", VTOSS, -9); cue("glove", VTOSS + 0.75, -5)
cue("riser-m", VBRAND - 1.0, -10); cue("impact", VBRAND, -4)
CRACKS = []
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -1.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0, "tap": -3.0}

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-27 / 20)                                             # stadium ambience
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, VBRAND, style="glow", seed=101)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    ramp = np.clip(np.arange(n) / SR / 3.0, 0.5, 1.0)[:, None]
    full = (fx + bed * ramp * 10 ** (-16 / 20)) * 10 ** (-6 / 20)
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre = os.path.join(HERE, ".pre.wav"); wav(pre, full)
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-20.0)    # low: headroom for a voice recorded on top
    os.remove(pre)
    return m

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

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "How catchers adjust to the hitter", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    scenes = [("0.0", "5.0", "The hook: a right-handed hitter steps in (catcher and umpire get set), then a left-handed hitter; freeze", "WHY DOES CATCHER POSITIONING CHANGE WITH THE HITTER?"),
              ("5.0", "14.0", "Right-handed hitter: from above (batter, catcher, umpire in the slot); over the umpire's shoulder, an inside pitch (9.7) and an outside pitch (13.0)", "THE HITTER CHANGES THE VIEW"),
              ("14.0", "23.0", "Left-handed hitter: he steps in, the umpire moves to the other slot; then right vs left side by side (catch at 21.0)", "OPPOSITE SIDE. DIFFERENT ANGLE."),
              ("23.0", "33.0", "The adjustment: 1 inside (catch 25.4), 2 outside (28.7), 3 on the edge, slowed (32.0); where it crossed vs where it was caught", "POSITIONING + PRESENTATION"),
              ("33.0", "41.3", "The takeaway: an edge pitch to each hitter (35.0, 37.8), the throw back to the pitcher (39.7)", "ELITE CATCHERS READ THE ENTIRE FIELD. (from 38.7)"),
              ("41.3", f"{D:.1f}", "End card", "BASEBALL DECODED")]
    lines = ["# Scene timing for the voiceover", "", f"The video is {D:.1f} s. Record each part of the narration inside its scene (times in seconds).", "",
             "| From | To | Scene | On screen |", "|---|---|---|---|"] + [f"| {a} | {b} | {d} | {t} |" for a, b, d, t in scenes]
    open(os.path.join(HERE, "CUES.md"), "w").write("\n".join(lines) + "\n")
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
