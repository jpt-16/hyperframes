"""'The hit-and-run': why the runner is already running (1080x1920, music + effects, no narration).

    python3 tools/physics.py        # the pitch, the ground ball, the right fielder -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/hit-and-run.mp4 --video-bitrate 16M

The play as shown: a runner on first, a right-handed batter. The runner breaks with the pitcher's first move; the
batter's job is to swing and make contact. With a right-handed hitter the second baseman covers second on the runner's
break, which opens a hole on the right side. Contact: a ground ball through that hole into right field, and the runner
goes first to third. A miss: the catcher throws to second and the runner, who left on the pitch, is tagged out sliding in.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
FBP, GB = P["pitches"]["fb"], P["gb"]
FL, TC = FBP["flight"], FBP["t_contact"]
T_MOVE = -1.3 - FL; T_BRK = T_MOVE + 0.15                       # mirrors assets/field.js
T_FIELD = GB["t_field"]; T_RFTHROW = T_FIELD + 0.45; T_RFC = T_RFTHROW + 0.95
T_CREL, T_CAT = 0.72, 0.72 + 1.1; T_TAG = T_CAT + 0.18; T_OUT = T_CAT + 0.6
T_SAFE3 = 5.55
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed="rt", **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r=1.0, speed="rt", **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def vat(sh, t):                                                    # the video time a shot shows play time t
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]): return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
# hook: the runner is already going as the pitcher delivers; the batter starts his swing; freeze just before contact
FRZ0 = 1.72
rate(0.0, 1.05, "cfHigh", T_BRK - 0.25, play="hit", rings=["r"])
shot(1.05, 2.3, "batSide", [1.05, FRZ0, 2.3], [-0.06 - (FRZ0 - 1.05), -0.06, -0.06], play="hit", zt=-0.2, freeze=FRZ0)
# 1 the situation; 2 the delivery, the runner breaks with it; 3 contact, a ground ball
E2, E3, E4 = 4.4, 6.4, 7.9
rate(2.3, E2, "wideHigh", -3.6, play="hit", rings=["r"])
rate(E2, E3, "runner", -2.0, play="hit", arR=[T_BRK, T_BRK + 0.7])
rate(E3, E4, "batSide", -0.5, play="hit")
VCT = vat(SHOTS[-1], TC)
# 4 replay from above: the second baseman goes to cover second, the hole opens, the ball goes through it
E5 = 11.0
rate(E4, E5, "overhead", T_BRK - 0.2, speed="replay", play="hit", ar2=[T_BRK + 0.15, T_BRK + 1.5], gap=-0.35, trace=[TC, TC + 1.3], rings=["b2", "r"])
OV = SHOTS[-1]; V2B, VGAP, VHOLE = vat(OV, T_BRK + 0.3), vat(OV, -0.35), vat(OV, TC + 1.25)
# 5 through the hole into right field; the runner goes first to third
E6, F1 = 13.0, 15.8
rate(E5, E6, "track", 1.25, play="hit")
rate(E6, F1, "third", 3.0, play="hit", ar3=[3.0, 3.7], rings=["r"])
VSAFE = vat(SHOTS[-1], T_SAFE3)
# 6 the same setup; he swings and misses; the catcher throws to second; the tag (½ speed)
F2, F3, F4, SP = 17.9, 19.3, 21.3, 23.6
rate(F1, F2, "cfHigh", -3.2, play="miss", rings=["r"])
rate(F2, F3, "batSide", -0.6, play="miss")
VMISS = vat(SHOTS[-1], TC)
rate(F3, F4, "throwCam", 0.55, play="miss", rings=["r"])
VCREL, VCAT = vat(SHOTS[-1], T_CREL), vat(SHOTS[-1], T_CAT)
rate(F4, SP, "tag2", 1.5, 0.5, "slow", play="miss")
VTAG, VOUT = vat(SHOTS[-1], T_TAG), vat(SHOTS[-1], T_OUT)
# 7 side by side: contact (top) vs. a miss (bottom), the same pitch; freeze on the outcomes
S0 = T_BRK - 0.3; SEND = SP + (T_SAFE3 + 0.15 - S0)
D = round(SEND + 1.6, 2)
shot(SP, D, "split", [SP, SEND, D], [S0, T_SAFE3 + 0.15, T_SAFE3 + 0.15], mode="split", play="hit", rings=["r"], freeze=round(SEND, 3))
SPS = SHOTS[-1]; VS_CT, VS_CAT, VS_OUT, VS_SAFE = (vat(SPS, x) for x in (TC, T_CAT, T_OUT, T_SAFE3))
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [FRZ0, 2.3, E4, F1, SP, SEND]:
    c.set("#flash", '{"opacity":0.6}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def punch(pid, t0, t1, html, top=1300, cls=""):
    c.clip(pid, t0, t1, f'<div class="pt {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def words(wid, t0, t1, parts, top=300, cls="hk"):
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, (w, _) in enumerate(ws)) + "</span>" for i, (ws, k) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (ws, _) in enumerate(parts):
        for j, (_, ts_) in enumerate(ws):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), ts_ - 0.03)
seq = lambda txt, t0, dt=0.07: [(w, t0 + dt * i) for i, w in enumerate(txt.split())]

# ----------------------------------------------------------------- hook
words("hook", 0.0, 2.28, [(seq("Why is the runner", 0.05), ""), (seq("already running?", 0.55), "acc")], 300)
c.ft("#hookx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.06, duration=0.14, ease="power3.out"), FRZ0)
pinl("ph0", 0.3, 1.03, "Runner", "runner", "yl")
# ----------------------------------------------------------------- 1-3
words("ttl", 2.32, E2 - 0.02, [(seq("The", 2.34), ""), (seq("hit-and-run", 2.44), "acc")], 300)
pinl("pr1", 2.6, E2 - 0.02, "Runner", "runner", "yl")
pinl("pb1", 2.8, E2 - 0.02, "Batter", "batter")
tag("tgo", vat(SHOTS[3], T_BRK) + 0.05, E3 - 0.02, "yl", "He runs <b class='wh'>with the pitch</b>")
tag("tsw", E3 + 0.05, E4 - 0.02, "wh", "The batter’s job: <b class='yl'>swing and make contact</b>")
# ----------------------------------------------------------------- 4 the hole
pinl("p2b", V2B, E5 - 0.02, "2B covers second", "b2", "")
pinl("pgap", VGAP, E5 - 0.02, "The hole", "gap", "yl")
tag("tth", VHOLE - 0.4, E5 - 0.02, "wh", "Ground ball <b class='yl'>right where he was</b>")
# ----------------------------------------------------------------- 5 first to third
tag("trf", E5 + 0.05, E6 - 0.02, "wh", "Through the right side")
pinl("pr3", E6 + 0.05, F1 - 0.02, "Runner", "runner", "yl")
punch("p13", VSAFE - 1.1, F1 - 0.02, "First<br><em>to third.</em>", 1360)
# ----------------------------------------------------------------- 6 the miss
words("ttl2", F1 + 0.02, F2 - 0.02, [(seq("Same play.", F1 + 0.04), ""), (seq("He misses.", F1 + 0.45), "acc")], 300)
tag("tmi", VMISS + 0.05, F3 - 0.02, "hot", "Swing and miss")
tag("tct", VCREL - 0.1, F4 - 0.02, "wh", "The catcher throws to second")
c.clip("out", VOUT - 0.05, SP - 0.02, '<div class="stamp" id="outx">Out</div>', cls="layer", style="z-index:15")
c.ft("#outx", o(opacity=0, scale=1.8, rotation=-8), o(opacity=1, scale=1, rotation=-8, duration=0.18, ease="back.out(2)"), VOUT - 0.05)
tag("tex", VOUT + 0.15, SP - 0.02, "wh", "No contact: <b class='hot'>the runner is exposed</b>")
# ----------------------------------------------------------------- 7 side by side
c.clip("splt", SP, D, f"""<div class="seam"></div>
  <div class="half t"><span class="hlab yl" id="hl1">Contact</span></div>
  <div class="half b"><span class="hlab hot" id="hl2">Swing and miss</span></div>""", cls="layer", style="z-index:11")
pop("#hl1", SP + 0.05, 10); pop("#hl2", SP + 0.15, 10)
c.clip("rs1", VS_SAFE - 0.05, D, '<div class="rs2 yl" id="rs1x" style="top:210px">1st to 3rd ✓</div>', cls="layer", style="z-index:13"); pop("#rs1x", VS_SAFE - 0.05, 10)
c.clip("rs2", VS_OUT, D, '<div class="rs2 hot" id="rs2x" style="top:1780px">Out at 2nd</div>', cls="layer", style="z-index:13"); pop("#rs2x", VS_OUT, 10)
c.clip("end", SEND + 0.05, D, '<div class="endq" id="endx">One swing<br><em>decides it.</em></div>', cls="layer", style="z-index:22")
c.ft("#endx", o(opacity=0, scale=1.2, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.22, ease="power3.out"), SEND + 0.05)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -10)
cue("impact", 0.0, -8); cue("riser-s", FRZ0, -4); cue("impact", FRZ0, -1); cue("tick", FRZ0, -2)
cue("impact", 2.34, -5); cue("impact", F1 + 0.04, -5)
for sh in SHOTS[:-1]:                                              # the pitch on its way in each shot that shows it
    v = vat(sh, -FL + 0.08)
    if v is not None and v > sh["a"] + 0.05: cue("whoosh", v, -9 if sh["speed"] == "rt" else -13)
cue("glove", VMISS + 0.04, -1); cue("whoosh", VCREL, -6); cue("glove", VCAT, -2)
cue("glove", vat(SHOTS[-2], T_CAT), -6); cue("popup", VTAG, -7); cue("impact", VOUT, -2)
cue("glove", vat(SHOTS[5], T_FIELD), -6)
cue("popup", VGAP, -6); cue("popup", V2B, -8)
cue("impact", VSAFE - 1.1, -6)
cue("glove", VS_CAT, -7); cue("impact", VS_OUT, -6); cue("popup", VS_SAFE, -5)
cue("riser-m", SEND, -6); cue("impact", SEND + 0.05, -1)
CRACKS = [(VCT, 0.9), (vat(SHOTS[0], TC), 0.0), (vat(OV, TC), 0.35), (VS_CT, 0.45)]
SLIDES = [(vat(SHOTS[-3], T_CAT - 0.12), 0.6, 1.0), (vat(SHOTS[-2], T_CAT - 0.12), 0.7, 0.5)]
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
        if vt is None or g <= 0: continue
        i = int(vt * SR); j = min(n, i + len(cr)); fx[i:j] += cr[: j - i] * g
    for vt, g, sl in SLIDES:
        x = slide(rng, 1 / sl if sl < 1 else 1.0); i = int(vt * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * g * 10 ** (-10 / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    tt = np.arange(n) / SR                                               # the crowd: a murmur; it rises as the ball goes through and the runner goes to third
    lift = np.clip((tt - VCT) / 0.6, 0, 1) * np.clip((F1 - tt) / 0.8, 0, 1)
    fx += crowd * (10 ** (-30 / 20) + lift[:, None] * 10 ** (-20 / 20))
    # the music bed (no narration, so it sits higher); it lands its chord on "One swing decides it"
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, SEND + 0.05, style="drive", seed=51)
    bed = read(bedp)[:n]; bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    full = fx + bed * 10 ** (-9 / 20)
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre = os.path.join(HERE, ".pre.wav"); wav(pre, full)
    m = master(pre, os.path.join(HERE, "assets", "mix.wav")); os.remove(pre)
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

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The hit-and-run", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
