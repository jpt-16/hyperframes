"""'The infield fly rule': why an infielder can't drop an easy pop-up for a cheap double play (1080x1920, music + effects, no narration).

    python3 tools/physics.py        # the pitch and the pop-up -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/infield-fly.mp4 --video-bitrate 16M

The rule as shown (MLB Official Baseball Rules, definition of an infield fly and 5.09(a)(12)): a fair fly ball (not a
line drive or a bunt) that an infielder can catch with ordinary effort, with runners on 1st and 2nd or the bases loaded
and fewer than two out. The umpire declares it while the ball is in the air; the batter is out whether or not it's
caught; the ball stays live and the runners may advance at their own risk (no force, since the batter is out). The play
has one out, runners on 1st and 2nd; the pop-up comes down on the infield dirt in front of the shortstop.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR, make_bed

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PO = P["pop"]; TL = PO["t_land"]
T_CALL, TF = 1.2, TL + 0.36
TR1 = TF + 0.34; TC1 = TR1 + 0.42; TR2 = TC1 + 0.3; TC2 = TR2 + 1.0              # mirrors assets/field.js
D = 29.4
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
# 1 the trap: the swing (contact at 0.3), the ball going up, the shortstop under it, the glove pulled away; freeze just above the dirt
S2, S3, S4, S5 = 3.9, 9.4, 16.6, 23.4
CT = 0.3
rate(0.0, 0.7, "plateHi", -CT, play="rule")
rate(0.7, 1.5, "rise", 0.55, play="rule")
rate(1.5, 2.35, "under", TL - 2.0, play="rule")
FRZ1 = 3.0; TFZ = TL - 0.015
shot(2.35, S2, "drop", [2.35, FRZ1, S2], [TFZ - (FRZ1 - 2.35), TFZ, TFZ], play="rule", zt=TFZ - 0.14, freeze=FRZ1)
# 2 the rule: the replay from the infield at half speed; the umpire's arm goes up while it's climbing; the batter is out
rate(S2, 5.4, "mound", -0.25, 0.5, "replay", play="rule")
rate(5.4, 7.2, "umpCU", 0.55, 0.5, "replay", play="rule", zt=T_CALL)
rate(7.2, S3, "wideAir", TL - 1.9, play="rule")
VCALL = vat(SHOTS[-2], T_CALL); VLAND2 = vat(SHOTS[-1], TL)
# 3 why it exists: the same pop-up, no rule (top) vs. the rule (bottom)
SPL = 15.2
shot(S3, S4, "split", [S3, SPL, S4], [TL - 1.0, TC2 + 0.45, TC2 + 0.45], mode="split", play="rule", marks=1)
SP = SHOTS[-1]; VL3, VC1, VC2, VF3 = (vat(SP, x) for x in (TL, TC1, TC2, TF))
# 4 the conditions: the board over the field from above
rate(S4, S5, "top", -1.0, 0.02, play="rule")
# 5 the twist: it falls in (half speed), the runner tries his luck and is looked back, the batter walks off; freeze
rate(S5, 25.0, "dirt", TL - 0.5, 0.5, "slow", play="rule")
rate(25.0, 26.8, "runners", TL + 0.1, play="rule")
FRZ2 = 27.6
shot(26.8, D, "final", [26.8, FRZ2, D], [TL + 1.6, TL + 2.4, TL + 2.4], play="rule", freeze=FRZ2)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)
VL5 = vat(SHOTS[-3], TL); VF5 = vat(SHOTS[-2], TF)
CUTS = [x["a"] for x in SHOTS[1:]]

c = Comp(D, 30)
PINS = []
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [FRZ1, S2, VCALL, S3, S4, S5, FRZ2]:
    c.set("#flash", '{"opacity":0.6}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=560, extra=""):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px;{extra}">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def punch(pid, t0, t1, html, top=1300, cls=""):
    c.clip(pid, t0, t1, f'<div class="pt {cls}" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
def pinl(pid, t0, t1, text, key, cls=""):
    c.clip(pid, t0, t1, f'<div class="pinw" id="{pid}w"><div class="pin {cls}" id="{pid}x"><span>{text}</span></div></div>', cls="layer", style="z-index:12")
    pop(f"#{pid}x", t0, 10); PINS.append([f"{pid}w", key])
def words(wid, t0, t1, parts, top=300, cls="hk"):                # a headline that lands word group by word group
    spans = "".join(f'<span class="hl{(" " + k) if k else ""}">' + " ".join(f'<span class="hw" id="{wid}{i}_{j}">{esc(w)}</span>' for j, w in enumerate(txt.split())) + "</span>" for i, (txt, k, _) in enumerate(parts))
    c.clip(wid, t0, t1, f'<div class="{cls}" id="{wid}x" style="top:{top}px">{spans}</div>', cls="layer", style="z-index:22")
    for i, (txt, _, ts_) in enumerate(parts):
        for j, _w in enumerate(txt.split()):
            c.ft(f"#{wid}{i}_{j}", o(opacity=0, scale=1.35, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.16, ease="power3.out"), ts_ + 0.07 * j)

# ----------------------------------------------------------------- 1 the trap
tag("sit", 0.05, 2.3, "wh", "1 out · runners on 1st & 2nd", 300)
pinl("pss", 1.6, 2.33, "Shortstop: “I got it”", "ss", "yl")
words("hook", FRZ1 - 0.3, S2, [("Wait…", "", FRZ1 - 0.3), ("He did that", "", FRZ1 - 0.05), ("on purpose?", "acc", FRZ1 + 0.1)], 300)
c.ft("#hookx", o(scale=1.0, transformOrigin="0% 0%"), o(scale=1.06, duration=0.14, ease="power3.out"), FRZ1 + 0.1)

# ----------------------------------------------------------------- 2 the rule
c.clip("ttl", S2 + 0.05, S3 - 0.02, '<div class="bnr" id="bnrx"><b>The rule</b><span>Infield fly</span></div>', cls="layer", style="z-index:16"); pop("#bnrx", S2 + 0.05, 8)
words("ifly", VCALL - 0.02, 7.2 - 0.02, [("“Infield fly!”", "acc", VCALL - 0.02)], 300)
tag("tif", VCALL + 0.2, 7.2 - 0.02, "wh", "Arm straight up: called while the ball is <b class='yl'>still in the air</b>", 1500)
pinl("pout", 7.3, S3 - 0.02, "Out", "batter")
words("bout", 7.3, S3 - 0.02, [("Batter:", "", 7.32), ("automatically out", "acc", 7.55)], 300, "hk mid")
tag("tnc", VLAND2 + 0.05, S3 - 0.02, "yl", "…even though nobody caught it", 1500)

# ----------------------------------------------------------------- 3 why the rule exists
c.clip("splt", S3, S4, f"""<div class="seam"></div>
  <div class="half t"><span class="hlab hot" id="hl1">Without the rule</span></div>
  <div class="half b"><span class="hlab yl" id="hl2">With the rule · batter already out</span></div>""", cls="layer", style="z-index:11")
pop("#hl1", S3 + 0.05, 10); pop("#hl2", S3 + 0.15, 10)
tag("sdrop", VL3 - 0.1, VC1 - 0.05, "hot", "Dropped on purpose", 760)
tag("s2b", VC1, VC2 - 0.05, "hot", "Force out at 2nd", 760)
tag("s1b", VC2, S4 - 0.02, "hot", "And at 1st: <b>double play</b>", 760)
tag("sno", VL3 + 0.1, S4 - 0.02, "yl", "No force: runners may advance at their own risk", 1730)
punch("pdp", 14.9, S4 - 0.02, "No cheap<br><em>double play.</em>", 1240, "ctr")

# ----------------------------------------------------------------- 4 the conditions
BXY = {"h": (0.5, 0.9), "1": (0.88, 0.5), "2": (0.5, 0.1), "3": (0.12, 0.5)}
def diamond(did, w, runners, batter=True, extra=""):
    h = w * 0.8; P_ = {k: (x * w, y * h) for k, (x, y) in BXY.items()}
    pts = " ".join(f"{P_[k][0]:.0f},{P_[k][1]:.0f}" for k in "h123")
    bases = "".join(f'<i class="bs{" hp" if k == "h" else ""}" id="{did}b{k}" style="left:{P_[k][0]:.0f}px;top:{P_[k][1]:.0f}px"></i>' for k in "h123")
    rs = "".join(f'<b class="rn" id="{did}r{k}" style="left:{P_[k][0]:.0f}px;top:{P_[k][1]:.0f}px"></b>' for k in runners)
    bt = f'<b class="rn bt" id="{did}rh" style="left:{P_["h"][0]:.0f}px;top:{P_["h"][1]:.0f}px">★</b>' if batter else ""
    return f'<div class="dia" style="width:{w:.0f}px;height:{h:.0f}px"><svg width="{w:.0f}" height="{h:.0f}"><polygon points="{pts}" /></svg>{bases}{rs}{bt}{extra}</div>', P_
dc, PC = diamond("cd", 460, "12", batter=False, extra="")
dc = dc.replace("</div>", f'<b class="rn" id="cr3" style="left:{PC["3"][0]:.0f}px;top:{PC["3"][1]:.0f}px;opacity:0"></b></div>', 1)
CX = [("Less than 2 outs", 17.0), ("Runners on 1st + 2nd", 18.1), ("Fair fly ball", 19.2), ("Catchable with ordinary effort", 20.3)]
TBL = 21.5
c.clip("cond", S4, S5, f"""<div class="tac" id="tacx"></div>
  <div class="ch" id="chx"><span>Infield fly rule</span><b>When it applies</b></div>
  <div class="cdia" id="cdx">{dc}</div>
  <div class="cl">""" + "".join(f'<div class="ci" id="ci{i}"><i>✓</i><b>{esc(t)}</b></div>' for i, (t, _) in enumerate(CX)) + """</div>
  <div class="cbl" id="cblx">Bases loaded <em>also qualifies</em></div>
  <div class="cfn" id="cfnx">Not on a line drive or a bunt · the umpire's judgment</div>""", cls="layer", style="z-index:11")
c.ft("#tacx", o(opacity=0), o(opacity=1, duration=0.25), S4)
pop("#chx", S4 + 0.05, 14); pop("#cdx", S4 + 0.15, 14)
for i, (_, t_) in enumerate(CX): c.ft(f"#ci{i}", o(opacity=0, x=-60), o(opacity=1, x=0, duration=0.22, ease="power3.out"), t_)
c.ft("#cr3", o(opacity=0, scale=1.8), o(opacity=1, scale=1, duration=0.25, ease="back.out(2)"), TBL)
pop("#cblx", TBL + 0.05, 14); c.ft("#cfnx", o(opacity=0), o(opacity=1, duration=0.3), 20.9)

# ----------------------------------------------------------------- 5 the twist
words("cdm", S5 + 0.5, FRZ2 - 0.02, [("The catch", "", S5 + 0.5), ("doesn't matter.", "acc", S5 + 0.75)], 300, "hk mid")
tag("trn", 25.15, 26.78, "wh", "Ball's live: he can try for 3rd <b class='yl'>at his own risk</b>", 1500)
pinl("pr2", 25.15, 26.78, "Runner", "r2", "yl")
pinl("pout2", 26.9, D, "Out", "batter")
tag("tbo", 26.9, FRZ2 - 0.02, "wh", "The batter was out the moment it was called", 1500)
words("q", FRZ2, D, [("Did you know", "", FRZ2 + 0.02), ("this rule?", "acc", FRZ2 + 0.25)], 300)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
for t_ in CUTS: cue("whoosh", t_, -10)
cue("riser-s", FRZ1, -4); cue("impact", FRZ1, 0); cue("tick", FRZ1, -1); cue("impact", S2, -5)
cue("tap", VCALL, 0); cue("impact", VCALL, -1); cue("riser-s", VCALL, -9)
cue("popup", 7.32, -6); cue("impact", 7.55, -6)
cue("glove", VC1, -1); cue("glove", VC2, -1); cue("popup", VC1, -7); cue("popup", VC2, -5); cue("impact", 14.9, -4)
for _, t_ in CX: cue("tick", t_, -2)
cue("popup", TBL, -4)
cue("glove", VF5, -6); cue("impact", S5 + 0.75, -5)
cue("riser-m", FRZ2, -5); cue("impact", FRZ2, -1); cue("tick", FRZ2, -2)
CRACKS = [(CT, 0.6), (vat(SHOTS[4], 0.0), 0.3)]
THUDS = [(VLAND2, 0.9), (VL3, 0.7), (VL5, 1.0, 0.5)]                # the ball hitting the dirt (the last one at half speed)
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
    for th in THUDS:
        x = thud(rng, th[2] if len(th) > 2 else 1.0); i = int(th[0] * SR); j = min(n, i + len(x)); fx[i:j] += x[: j - i] * th[1]
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav")); crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-28 / 20)
    # the music bed: made for this video (lands its chord on the closing question); no voice, so it sits higher
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, FRZ2, style="drive", seed=31)
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
.hlab {{ position:absolute; left:40px; top:200px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.88); {BC} font-size:56px; }}
.half.b .hlab {{ top:28px; }}
.ch {{ position:absolute; left:52px; top:250px; display:grid; gap:4px; }}
.ch span {{ {MONO} font-size:26px; letter-spacing:.16em; color:{MUTED}; }} .ch b {{ {BC} font-size:110px; line-height:.95; color:#fff; }}
.cdia {{ position:absolute; left:0; right:0; top:480px; display:flex; justify-content:center; }}
.cl {{ position:absolute; left:52px; right:52px; top:960px; display:grid; gap:14px; }}
.ci {{ display:flex; align-items:center; gap:22px; padding:16px 22px; {CARD} border-left:6px solid {Y}; }}
.ci i {{ display:grid; place-items:center; width:58px; height:58px; flex:none; border-radius:50%; background:{Y}; color:#05080d; font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:36px; }}
.ci b {{ {BC} font-size:64px; line-height:1; color:#fff; }}
.cbl {{ position:absolute; left:52px; right:52px; top:1530px; padding:16px 22px; border-radius:14px; background:{HOT}; color:#05080d; {BC} font-size:62px; text-align:center; }}
.cbl em {{ font-style:normal; color:#fff; }}
.cfn {{ position:absolute; left:52px; right:52px; top:1680px; {MONO} font-size:24px; letter-spacing:.08em; color:#cfd6e0; text-align:center; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}, "pins": PINS}
    h = c.page(CSS, "The infield fly rule", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    if "--nomix" not in sys.argv:
        m = mixdown(); print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
    else: print(f"index.html: {D}s, {len(SHOTS)} shots")
