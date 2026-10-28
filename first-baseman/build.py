"""'First base is harder than it looks': the glove work and the bat (1080x1920, sound effects only).

    python3 tools/physics.py        # the home run -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (effects only)
    npx --yes hyperframes@0.8.154 render . -o renders/first-baseman.mp4 --video-bitrate 16M

There is no narration: the voiceover is recorded separately and laid on top. The effects are mastered to -20 LUFS so a
voiceover at normal level sits over them. Every throw is worked out in assets/field.js from the 3D figures (the fielder's
hand at release, the first baseman's glove at the catch, his right foot pinned to the bag).
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
HR = P["hr"]
D = 40.0
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S4, S5, S6 = 3.0, 11.0, 20.0, 28.0, 36.0                 # the brief's scene starts

# the throws' timing, as field.js works it out (release at -distance/speed; the fielder fields it EXCH earlier)
PLAYS = {"hook": ("backhand", (-41, -113), 80), "low": ("field", (36, -108), 74), "glove": ("field", (-24, -110), 82), "pull": ("field", (-52, -72), 84),
         "scoop": ("charge", (-20, -98), 76), "late": ("charge", (-20, -98), 76), "high": ("field", (-26, -112), 82), "wide": ("field", (-50, -70), 80),
         "p3b": ("backhand", (-66, -86), 82), "p2b": ("dive", (42, -114), 66), "pss": ("bare", (-12, -80), 72)}
EXCH = {"field": 0.75, "backhand": 0.85, "charge": 0.6, "bare": 0.42, "dive": 1.15}
def tr_of(k):
    kind, (x, z), mph = PLAYS[k]; return -(np.hypot(63.64 - x, -63.64 - z) - 2.0) / (mph * 1.4667 * 0.98)
def tf_of(k): return tr_of(k) - EXCH[PLAYS[k][0]]

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def hold(a, b, cam, t0, speed="none", **kw): shot(a, b, cam, [a, b], [t0, t0], speed, **kw)
FLASH = []
# 1 hook: the shortstop goes deep in the hole, backhands it, throws falling away; the first baseman at full stretch, the runner a step away; freeze on the catch
H1 = 1.0; FRZ0 = 2.2
rate(0.0, H1, "fielder", tf_of("hook") - 0.2, 1, "none", play="hook")
t_h = tf_of("hook") - 0.2 + H1
rate(H1, FRZ0, "fbSide", t_h, -t_h / (FRZ0 - H1), "none", play="hook")
hold(FRZ0, S2, "fbSide", 0.0, "none", play="hook", freeze=[FRZ0, S2], show={"foot": 1})
# 2 the stretch: a low throw, one to his glove side, one that pulls him up the line; then a replay with the distance the stretch gains
rate(S2, 4.7, "fbSide", -1.2, 1, "rt", play="low")
rate(4.7, 6.4, "fbFront", -1.2, 1, "rt", play="glove")
rate(6.4, 8.2, "fbLine", -1.3, 1, "rt", play="pull")
rate(8.2, S3, "gain", -0.85, 0.5, "replay", play="glove", show={"gain": 1, "foot": 1})
# 3 bad throws: the shortstop charges, throws on the run, it short-hops; the first baseman who stays tall vs. the one who scoops it; high; wide
rate(S3, 12.5, "fielder", tf_of("scoop") - 0.45, 1, "rt", play="scoop")
rate(12.5, 14.3, "fbIn", -0.75, 1, "rt", play="late")
rate(14.3, 16.3, "fbIn", -0.6, 0.5, "replay", play="scoop", show={"foot": 1})
rate(16.3, 18.15, "fbFront", -1.1, 1, "rt", play="high")
rate(18.15, S4, "fbWide", -1.1, 1, "rt", play="wide")
# 4 they finish the play: three tough plays, three clean picks, three fielders who know it
v = S4
for k, (play, cb) in enumerate([("p3b", "fbSide"), ("p2b", "fbFront"), ("pss", "fbIn")]):
    tr, tf = tr_of(play), tf_of(play)
    a1 = 1.05 if play != "p2b" else 1.15
    rate(v, v + a1, "fielder", tr - a1 + 0.2, 1, "rt", play=play); FLASH.append(v)
    rate(v + a1, v + a1 + 0.95, cb, -0.75, 1, "rt", play=play)
    rate(v + a1 + 0.95, v + 8 / 3 if k < 2 else S5, "fielder", 0.45, 1, "rt", play=play)
    v = v + 8 / 3
# 5 the bat: the same first baseman hits; load, stride, turn; the line drive leaves the park
rate(S5, 29.4, "batLow", -1.6, 1, "rt", play="hr")
rate(29.4, 30.6, "bat", -0.25, 1, "rt", play="hr")
rate(30.6, 33.9, "track", 0.95, 1, "rt", play="hr", show={"hrPath": 1})
rate(33.9, S6, "wall", 4.2, 0.5, "slow2", play="hr", show={"hrPath": 1})
# finale: the stretch, the scoop, the swing; then around first base
rate(S6, 36.5, "fbSide", -0.05, 0.3, "none", play="hook"); FLASH.append(S6)
rate(36.5, 37.0, "fbIn", -0.08, 0.4, "none", play="scoop"); FLASH.append(36.5)
rate(37.0, 37.5, "bat", -0.12, 0.5, "none", play="hr"); FLASH.append(37.0)
rate(37.5, D, "trot", 4.0, 1, "none", play="trot"); FLASH.append(37.5)
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)

def at_play(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]):
            return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd rt" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [FRZ0] + FLASH:
    c.set("#flash", '{"opacity":0.75}', f); c.to("#flash", o(opacity=0, duration=0.16, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1560):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="mdl" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12")
    c.ft(f"#{nid}x", o(opacity=0), o(opacity=1, duration=0.3), t0)

# ----------------------------------------------------------------- 1 the hook: the title on frame one
c.clip("hook", 0, S2 - 0.02, """<div class="eyebrow"><i></i>Baseball Decoded</div>
  <div class="hk" id="hkx"><span class="hl">First base is</span><span class="hl"><em class="acc">harder</em> than</span><span class="hl">it looks</span></div>""", cls="layer", style="z-index:12")
c.ft("#hkx", o(scale=1.07, transformOrigin="0% 50%"), o(scale=1, duration=0.35, ease="power3.out"), 0.0)
c.ft("#hkx .acc", o(scale=1.0), o(scale=1.12, duration=0.12, ease="power2.out", yoyo=True, repeat=1), FRZ0)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S2 - 0.16)
c.clip("frzt", FRZ0 + 0.05, S2 - 0.02, '<div class="pinw" id="footw"><div class="pin" id="footx"><span>Foot on the bag</span></div></div>', cls="layer", style="z-index:12")
pop("#footx", FRZ0 + 0.08)

# ----------------------------------------------------------------- scene titles
for k, (a, b, html) in enumerate([(S2, S3, 'The stretch can <em class="acc">save an out</em>'), (S3, S4, 'Bad throw? <em class="acc">Save it.</em>'),
                                   (S4, S5, 'They <em class="acc">finish</em> the play'), (S5, S6, 'And they have to <em class="acc">hit bombs</em>')]):
    c.clip(f"ttl{k}", a + 0.02, b - 0.02, f'<div class="st" id="ttl{k}x">{html}</div>', cls="layer", style="z-index:12")
    c.ft(f"#ttl{k}x", o(opacity=0, y=40, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.25, ease="power3.out"), a + 0.04)

# ----------------------------------------------------------------- 2 the stretch
tag("t1", S2 + 0.3, 4.65, "wh", "Low throw: get down to it")
tag("t2", 4.75, 6.35, "wh", "Glove side: lead with the glove")
tag("t3", 6.45, 8.15, "wh", "Pulled up the line: the toe stays on the bag")
c.clip("gain", 8.2 + 0.85 * 2 - 0.5, S3 - 0.02, '<div class="pinw" id="gainw"><div class="pin" id="gainx"><span id="gainv">+0 ft</span></div></div>', cls="layer", style="z-index:12")
pop("#gainx", 8.2 + 0.85 * 2 - 0.45)
tag("t4", 8.35, S3 - 0.05, "cb", "Reads it, then stretches · foot on the bag until it's in the glove")
note("n4", 9.6, S3 - 0.05, "3D model · how much closer the stretch takes the catch")

# ----------------------------------------------------------------- 3 bad throws
tag("b1", S3 + 0.3, 12.45, "wh", "Charging, throwing on the run")
tag("b2", 12.6, 14.25, "hot", "Stays tall: the short hop gets by him")
tag("b3", 14.4, 16.25, "cb", "Reads the hop · glove out front · scoops it")
tag("b4", 16.4, 18.1, "wh", "High: stay on the bag, go up and get it")
tag("b5", 18.25, S4 - 0.05, "yl", "Too wide: off the bag, but it stays in front")
note("n5", 18.6, S4 - 0.05, "Not every bad throw can be caught · keep the ball in front")

# ----------------------------------------------------------------- 4 they finish the play
for k, (a, lab) in enumerate([(S4, "Anticipation"), (S4 + 8 / 3, "Soft hands"), (S4 + 16 / 3, "Footwork")]):
    c.clip(f"fp{k}", a + 0.05, a + 8 / 3 - 0.03, f'<div class="cbl" id="fp{k}x">{esc(lab)}</div>', cls="layer", style="z-index:21")
    pop(f"#fp{k}x", a + 0.08, 18)

# ----------------------------------------------------------------- 5 the bat
tag("h1", 30.65, 33.85, "yl", f"{HR['ev']} mph off the bat · over the wall", 1560)
note("n6", 30.9, 33.85, "3D model · drag and spin included")

# ----------------------------------------------------------------- finale
c.clip("endt", 37.55, D, '<div class="endt"><span id="et1">Defense saves outs.</span><span class="acc" id="et2">Bats win games.</span></div>', cls="layer", style="z-index:22")
c.ft("#et1", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), 37.6)
c.ft("#et2", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), 38.3)

# ----------------------------------------------------------------- sound (effects only; the voiceover is added later)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -3)
for t_ in [S2, S3, S4, S5, S6]: cue("whoosh", t_, -8)
for t_ in FLASH: cue("whoosh", t_, -11)
BOUNCE = {"scoop", "late", "pss"}
CRACKS = []
for x in SHOTS:
    pl = x.get("play"); slow = x["speed"] in ("slow2", "replay"); g = -5 if slow else 0
    if pl in PLAYS:
        cue("whoosh", at_play(x, tr_of(pl) + 0.03), -7 + g)                            # the throw
        if pl in BOUNCE: cue("tap", at_play(x, -0.05), -2 + g)                         # the short hop off the dirt
        if pl == "late": cue("tap", at_play(x, 0.32), -6); cue("tap", at_play(x, 0.62), -9)
        else: cue("glove", at_play(x, 0.0), g)
        cue("tap", at_play(x, {"hook": 0.07, "low": 0.35, "glove": 0.3, "pull": 0.85, "scoop": 0.12, "late": 0.12, "high": 0.3, "wide": 0.0, "p3b": 0.15, "p2b": 0.18, "pss": 0.08}[pl]), -9 + g)   # his foot on the bag
        cue("glove", at_play(x, tf_of(pl)), -8 + g)                                    # the fielder's glove
    if pl == "hr" and x["cam"] in ("bat", "batLow"):
        v0 = at_play(x, 0.0)
        if v0 is not None: CRACKS.append((v0, 0.9 if not slow else 0.5)); cue("glove", at_play(x, -0.45 + 0.43), -30)
    if pl == "trot":
        for k in range(8): cue("tap", at_play(x, 4.1 + k * 0.3), -16)
cue("tick", FRZ0, -1); cue("impact", FRZ0, -6)
cue("riser-m", 37.6, -4); cue("impact", 37.6, -3); cue("impact", 38.3, -5)
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
    tt = np.arange(n) / SR; env = np.ones(n)
    for vt, g in CRACKS: env += 2.2 * np.exp(-np.clip(tt - vt, 0, None) / 2.5) * (tt > vt)          # the crowd comes up on the home run
    fx += crowd * env[:, None] * 10 ** (-26 / 20)
    pre = os.path.join(HERE, ".pre.wav")
    w = wave.open(pre, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(fx * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-20.0)
    os.remove(pre)
    return m

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
MONO = 'font-family:"Plex Mono", monospace; font-weight:500; text-transform:uppercase;'
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:640px; background:linear-gradient(180deg, rgba(3,6,12,.6), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:760px; background:linear-gradient(0deg, rgba(3,6,12,.72) 0%, rgba(3,6,12,.35) 55%, rgba(3,6,12,0) 100%); }}
.spd {{ position:absolute; left:52px; top:150px; display:inline-flex; align-items:center; gap:10px; padding:8px 16px; border-radius:8px; background:rgba(6,10,18,.72);
        {MONO} font-size:21px; letter-spacing:.14em; }}
.spd.rt {{ color:#cfd6e0; }} .spd.sl {{ color:{Y}; }}
.spd::before {{ content:""; width:10px; height:10px; border-radius:50%; background:currentColor; }}

.eyebrow {{ position:absolute; left:56px; top:232px; display:flex; align-items:center; gap:14px; {MONO} font-size:24px; letter-spacing:.2em; color:#cfd6e0; text-shadow:0 2px 10px rgba(0,0,0,.8); }}
.eyebrow i {{ width:34px; height:3px; background:{HOT}; }}
.hk {{ position:absolute; left:52px; right:40px; top:278px; display:grid; gap:2px; font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase;
       font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.75), 0 2px 4px rgba(0,0,0,.6); }}
.hk.big {{ font-size:176px; }}
.hk .hl {{ display:block; }}
.hk .acc, .hk .hl.acc {{ color:{HOT}; }}
.hk .hw {{ display:inline-block; transform-origin:0 80%; }}

.cap {{ position:absolute; left:52px; right:40px; }}
.cap .cl {{ display:block; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:88px; line-height:.96; text-transform:uppercase; color:#fff;
            text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.cap .cw {{ display:inline-block; }} .cap .cw.acc {{ color:{HOT}; }}

.cb, .cap .cw.cb, .hk .cb {{ color:{CYAN}; }} .hot, .cap .cw.hot {{ color:{HOT}; }} .yl {{ color:{Y}; }} .wh {{ color:#eef2f7; }}
.hk.sm {{ font-size:100px; }} .hk.mid {{ font-size:124px; }} .hk em {{ font-style:normal; }}
.qq {{ position:absolute; left:50px; right:50px; top:250px; padding:22px 26px; border-radius:24px; background:rgba(4,7,13,.74); font-family:"Barlow Condensed", sans-serif; font-weight:800;
       font-size:96px; line-height:.95; text-transform:uppercase; color:#fff; }}
.seam {{ position:absolute; left:539px; top:0; bottom:0; width:2px; background:rgba(255,255,255,.55); box-shadow:0 0 18px rgba(0,0,0,.6); }}
.half {{ position:absolute; top:0; bottom:0; width:540px; }} .half.l {{ left:0; }} .half.r {{ left:540px; }}
.hd {{ position:absolute; left:0; right:0; top:1640px; display:grid; justify-items:center; gap:4px; text-align:center; }}
.hd span {{ {MONO} font-size:26px; letter-spacing:.14em; padding:6px 14px; border-radius:8px; background:rgba(6,10,18,.78); }}
.hd b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:88px; line-height:1; text-transform:uppercase; text-shadow:0 4px 24px rgba(0,0,0,.85); }}
.res {{ position:absolute; left:24px; right:24px; top:1440px; display:grid; gap:10px; }}
.res em {{ font-style:normal; font-family:"Inter", sans-serif; font-weight:800; font-size:27px; line-height:1.15; padding:10px 14px; border-radius:12px; background:rgba(6,10,18,.84); }}
.mdl {{ position:absolute; left:0; right:0; top:1390px; text-align:center; {MONO} font-size:21px; letter-spacing:.1em; color:#e8edf3; text-shadow:0 2px 10px rgba(0,0,0,.9); }}
.leg {{ position:absolute; left:40px; top:470px; display:grid; gap:8px; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.72); {MONO} font-size:21px; letter-spacing:.06em; }}
.leg.low {{ top:1500px; right:40px; }}
.leg span {{ display:flex; align-items:center; gap:12px; }}
.leg i {{ width:40px; height:6px; border-radius:3px; background:currentColor; flex:none; }}
.leg .dash i {{ background:repeating-linear-gradient(90deg, currentColor 0 9px, transparent 9px 16px); }}
.tg {{ position:absolute; left:50%; transform:translateX(-50%); max-width:1000px; padding:10px 20px; border-radius:12px; background:rgba(6,10,18,.84); white-space:nowrap;
       font-family:"Inter", sans-serif; font-weight:800; font-size:31px; }}
.tg.hot {{ color:{HOT}; }}
.chipb {{ position:absolute; left:50px; right:50px; top:450px; display:grid; gap:6px; padding:18px 24px; border-radius:18px; background:rgba(6,10,18,.84); border-left:6px solid {HOT}; }}
.chipb b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:62px; line-height:1; text-transform:uppercase; color:#fff; }}
.chipb span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:29px; line-height:1.3; color:#dfe5ec; }}
.rma {{ position:absolute; left:52px; top:560px; display:grid; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:150px; line-height:.92; text-transform:uppercase; color:#fff;
        text-shadow:0 6px 30px rgba(0,0,0,.8); }}
.rma .acc {{ color:{HOT}; }}
.flash {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.hk {{ font-size:118px; }}
.skill {{ position:absolute; left:40px; top:205px; display:flex; align-items:center; gap:12px; padding:6px 16px 6px 6px; border-radius:12px; background:rgba(6,10,18,.84); border:1px solid rgba(255,255,255,.12); }}
.skill b {{ display:grid; place-items:center; width:46px; height:46px; border-radius:9px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:34px; }}
.skill span {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:40px; text-transform:uppercase; letter-spacing:.02em; }}
.spd {{ left:auto; right:44px; }}
.plan {{ position:absolute; left:44px; right:44px; top:1250px; display:grid; gap:12px; }}
.pr {{ display:flex; justify-content:space-between; align-items:baseline; gap:18px; padding:14px 22px; border-radius:16px; background:rgba(6,10,18,.84); }}
.pr span {{ {MONO} font-size:22px; letter-spacing:.1em; color:{MUTED}; }}
.pr b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:48px; text-transform:uppercase; color:#fff; }}
.leg {{ position:absolute; left:44px; top:540px; display:grid; gap:8px; padding:12px 18px; border-radius:12px; background:rgba(6,10,18,.72); {MONO} font-size:22px; letter-spacing:.06em; }}
.leg span {{ display:flex; align-items:center; gap:12px; }} .leg i {{ width:22px; height:22px; border-radius:5px; background:currentColor; opacity:.8; }}
.abs {{ position:absolute; left:44px; right:44px; top:1300px; display:grid; gap:12px; }}
.ar {{ display:grid; gap:4px; padding:16px 22px; border-radius:16px; background:rgba(6,10,18,.86); }}
.ar b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:52px; line-height:1; text-transform:uppercase; color:#fff; }}
.ar span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:29px; color:#dfe5ec; line-height:1.25; }}
.steps {{ position:absolute; left:44px; right:44px; top:1560px; display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }}
.steps span {{ display:grid; place-items:center; padding:14px 6px; border-radius:12px; background:rgba(6,10,18,.86); border-bottom:5px solid {HOT}; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:36px; text-transform:uppercase; opacity:0; white-space:nowrap; }}
.cbl {{ position:absolute; left:50%; top:1600px; transform:translateX(-50%); padding:10px 24px; border-radius:12px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:56px; text-transform:uppercase; white-space:nowrap; }}
.endt {{ position:absolute; left:52px; right:40px; top:440px; display:grid; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:136px; line-height:.92; text-transform:uppercase; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.8); }}
.endt .acc {{ color:{HOT}; }}
"""])
CSS += f"""
.hk {{ top:300px; font-size:138px; }} .hk em {{ font-style:normal; }}
.st {{ position:absolute; left:52px; right:40px; top:250px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:100px; line-height:.94; text-transform:uppercase; color:#fff;
       text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.st em {{ font-style:normal; color:{HOT}; }}
.mdl {{ font-size:23px; left:50%; right:auto; transform:translateX(-50%); white-space:nowrap; padding:8px 16px; border-radius:10px; background:rgba(6,10,18,.8); }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:30px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:46px; text-transform:uppercase; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
#footx span {{ background:{CYAN}; font-size:38px; }}
.cbl {{ top:1580px; }}
.tg {{ max-width:1020px; white-space:normal; text-align:center; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}}
    h = c.page(CSS, "First base is harder than it looks", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; effects {m['lufs']} LUFS / {m['true_peak']} dBTP")
