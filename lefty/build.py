"""'Why every team wants a lefty': the left-hander's three edges (1080x1920, sound effects only).

    python3 tools/physics.py        # the pitches -> assets/play.json
    python3 build.py                # index.html + assets/mix.wav (effects only) + vo-cues.txt / vo-cues.srt
    npx --yes hyperframes@0.8.154 render . -o renders/lefty.mp4 --video-bitrate 16M

There is NO narration in this video: the voiceover is recorded separately and laid on top. Every scene change sits
on a planned voiceover cue (VO below), and vo-cues.txt / vo-cues.srt give the window each line should land in.
The effects are mastered to -20 LUFS so a voiceover at normal level sits on top without fighting them.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
PI_ = P["pitches"]
D = 40.0
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"

# ----------------------------------------------------------------- the voiceover plan (recorded separately)
# (in, out): the window each line should land in. Scene changes are cut to these.
VO = [
    (0.25, 2.75, "Why does every team want a left-handed pitcher?"),
    (3.1, 7.1, "For starters, most hitters grow up seeing far more right-handed pitching."),
    (7.4, 11.6, "A lefty's release angle and pitch movement can look completely different."),
    (12.0, 14.0, "Then there's the lefty-on-lefty matchup."),
    (14.3, 20.3, "Left-handed hitters generally have a tougher time against pitchers throwing from the same side."),
    (20.8, 23.2, "But here's another advantage: controlling runners."),
    (23.5, 30.1, "A left-handed pitcher naturally faces first base when delivering from the stretch, making it easier to watch the runner and threaten a pickoff."),
    (30.6, 36.9, "And when you combine that with great stuff and command, you get a pitcher who can change an entire matchup."),
    (37.3, 39.8, "That's why a quality lefty is such a valuable weapon."),
]
S2, S3, S4, S5 = 2.9, 11.8, 20.6, 30.4                         # scene starts (the brief: 0-3, 3-12, 12-21, 21-31, 31-40)
END1, END2 = 35.6, 37.3                                        # "ONE ARM. THREE ADVANTAGES." / "THAT'S THE VALUE OF A LEFTY."

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
# 1 hook: the left-hander explodes into his delivery; the left-handed hitter can't pick up the slider
rate(0.0, 1.15, "hookP", -1.5, 1, "none", play="sl_l_lhb")
rate(1.15, 1.95, "hookB", -0.35, 0.5, "slow2", play="sl_l_lhb")             # tracking it in...
rate(1.95, S2, "front", -0.22, 0.5, "slow2", play="sl_l_lhb")                 # ...and swinging right through it
# 2 a different look: what hitters see most; the same pitch from each side; the hitter's view of the lefty
rate(S2, 5.3, "behind", -1.9, 1, "rt", play="fb_r", show={"ghost": ["fb_r", "sl_r", "ch_r", "cu_r"], "ghostT0": -1.75, "tube": "fb_r"})
rate(5.3, 8.9, "behind", -1.25, 0.5, "slow2", mode="split")
rate(8.9, S3, "eye", -0.95, 0.5, "slow2", play="fb_l", noHitter=True, show={"tube": "fb_l", "ghost": ["fb_r"]})
# 3 lefty vs lefty: the slider runs away from the left-handed hitter; the same pitch at a right-hander's back foot
rate(S3, 14.8, "plate", -2.3, 1, "rt", play="sl_l_lhb")
rate(14.8, 17.6, "zone", -0.75, 0.5, "replay", play="sl_l_lhb", show={"zone": 1, "mark": 1, "tube": "sl_l"})
rate(17.6, S4, "plate", -2.3, 1, "rt", play="sl_l_rhb", show={"tube": "sl_l"})
# 4 the running game: the lead; the lefty facing first in the set; the pickoff; a replay with a freeze on the move
rate(S4, 23.0, "wide", -6.0, 1, "rt", play="pick")
rate(23.0, 25.2, "pov", -3.6, 1, "rt", play="pick", show={"sight": 1})
rate(25.2, 27.5, "pick", -1.3, 1, "rt", play="pick")
FRZ = (27.9, 28.35)
shot(27.5, S5, "replay", [27.5, FRZ[0], FRZ[1], S5], [-0.5, -0.3, -0.3, -0.3 + (S5 - FRZ[1]) * 0.5], "replay", play="pick", freeze=list(FRZ), show={"lead": 1, "step": 1})
# 5 the payoff: the pitch, the left-handed hitter, the runner frozen at first; the pitcher back on the mound
rate(S5, 31.9, "low", -1.65, 1, "none", play="sl_l_lhb")
rate(31.9, 33.5, "catcherV", -0.2, 1, "none", play="sl_l_lhb")
rate(33.5, END1 - 0.2, "first", 0.0, 1, "none", play="hold")
rate(END1 - 0.2, D, "walk", 0.2, 1, "none", play="walk")
for x, y in zip(SHOTS, SHOTS[1:]): assert abs(x["b"] - y["a"]) < 1e-3 and x["b"] > x["a"], (x, y)

def at_play(sh, t):
    vs, ts = sh["vs"], sh["ts"]
    for i in range(1, len(vs)):
        if ts[i] != ts[i - 1] and min(ts[i - 1], ts[i]) <= t <= max(ts[i - 1], ts[i]):
            return vs[i - 1] + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (vs[i] - vs[i - 1])
    return None
def first_shot(**kw): return next(x for x in SHOTS if all(x.get(k) == v for k, v in kw.items()))

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", 0, D, '<div class="spd rt" id="spd"></div>', cls="layer", style="z-index:30")
c.clip("flash", 0, D, '<div class="flash" id="flash"></div>', cls="layer", style="z-index:40")
for f in [1.15, 1.95]: c.set("#flash", '{"opacity":0.8}', f); c.to("#flash", o(opacity=0, duration=0.16, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="mdl" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12")
    c.ft(f"#{nid}x", o(opacity=0), o(opacity=1, duration=0.3), t0)

# ----------------------------------------------------------------- 1 the hook: readable on frame one
c.clip("hook", 0, S2 - 0.02, """<div class="eyebrow"><i></i>Baseball Decoded</div>
  <div class="hk" id="hkx"><span class="hl">Why does</span><span class="hl">every team</span><span class="hl">want a <em class="acc">lefty?</em></span></div>""", cls="layer", style="z-index:12")
c.ft("#hkx", o(scale=1.07, transformOrigin="0% 50%"), o(scale=1, duration=0.35, ease="power3.out"), 0.0)
c.ft("#hkx .acc", o(scale=1.0), o(scale=1.12, duration=0.12, ease="power2.out", yoyo=True, repeat=1), 1.15)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S2 - 0.16)

# ----------------------------------------------------------------- scene titles
for k, (a, b, html) in enumerate([(S2, S3, 'A <em class="acc">different</em> look'), (S3, S4, 'The <em class="acc">lefty-lefty</em> matchup'),
                                   (S4, S5, 'Control the <em class="acc">running game</em>')]):
    c.clip(f"ttl{k}", a + 0.02, b - 0.02, f'<div class="st" id="ttl{k}x">{html}</div>', cls="layer", style="z-index:12")
    c.ft(f"#ttl{k}x", o(opacity=0, y=40, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.25, ease="power3.out"), a + 0.04)

# ----------------------------------------------------------------- 2 a different look
tag("fam", S2 + 0.35, 5.25, "wh", "Most hitters see far more right-handers", 1560)
c.clip("splt", 5.3, 8.88, '<div class="seam"></div><div class="side l" id="sdl"><b class="cb">Righty</b></div><div class="side r" id="sdr"><b class="hot">Lefty</b></div>', cls="layer", style="z-index:11")
pop("#sdl", 5.35, 12); pop("#sdr", 5.45, 12)
tag("same", 5.6, 8.85, "wh", "Same pitch, mirrored: a different release angle", 1560)
c.clip("eyel", 8.92, S3 - 0.02, '<div class="leg"><span class="mono">The hitter\'s view</span><span class="cb"><i></i>The usual righty path</span><span class="hot"><i></i>The lefty\'s pitch</span></div>', cls="layer", style="z-index:11")
tag("eyet", 9.3, S3 - 0.05, "hot", "From the other side: a less familiar look", 1560)

# ----------------------------------------------------------------- 3 lefty vs lefty
tag("ll", S3 + 0.4, 14.75, "hot", "Lefty pitcher vs. lefty hitter", 1560)
tag("away", 15.0, 17.55, "yl", "Starts on his side, then breaks away", 1560)
tag("rh", 17.8, S4 - 0.05, "cb", "Righty hitter: the same pitch breaks toward him", 1560)
note("avg", 15.0, S4 - 0.05, "On average, a tougher matchup · not true of every hitter")

# ----------------------------------------------------------------- 4 the running game
tag("rn", S4 + 0.4, 22.95, "wh", "Runner on first · lefty in the stretch", 1120)
c.clip("setc", 23.05, 25.15, """<div class="abs" id="setx"><div class="ar"><b class="cb">Righty in the set</b><span>Faces third base: the runner is behind him</span></div>
  <div class="ar" id="set2"><b class="hot">Lefty in the set</b><span>Faces first base: the runner is right in front of him</span></div></div>""", cls="layer", style="z-index:12")
pop("#setx", 23.1); pop("#set2", 23.6, 12)
c.clip("lead", FRZ[0] - 0.02, S5 - 0.02, '<div class="pinw" id="leadw"><div class="pin" id="leadx"><span>His lead</span></div></div><div class="pinw" id="stepw"><div class="pin" id="stepx"><span>Step to first</span></div></div>', cls="layer", style="z-index:12")
pop("#leadx", FRZ[0]); pop("#stepx", FRZ[0] + 0.12)
note("mv", FRZ[0] + 0.2, S5 - 0.05, "A good move is a threat · not a guaranteed out")

# ----------------------------------------------------------------- 5 the payoff
for k, (a, b, lab) in enumerate([(S5, 31.9, "1 · A different look"), (31.9, 33.5, "2 · Lefty vs. lefty"), (33.5, END1 - 0.2, "3 · The pickoff threat")]):
    c.clip(f"pay{k}", a + 0.03, b - 0.02, f'<div class="cbl" id="pay{k}x">{esc(lab)}</div>', cls="layer", style="z-index:21")
    pop(f"#pay{k}x", a + 0.05, 18)
c.clip("endt", END1, D, '<div class="endt"><span id="et1">One arm.</span><span class="acc" id="et2">Three advantages.</span></div><div class="endv" id="et3">That\'s the value of a <em class="acc">lefty.</em></div>', cls="layer", style="z-index:22")
c.ft("#et1", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), END1)
c.ft("#et2", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), END1 + 0.45)
c.ft("#et3", o(opacity=0, y=30, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.25, ease="power3.out"), END2)

# ----------------------------------------------------------------- sound (effects only; the voiceover is added later)
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -2); cue("whoosh", 1.15, -6); cue("impact", 1.15, -8); cue("whoosh", 1.95, -8)
for t_ in [S2, S3, S4, S5]: cue("whoosh", t_, -9)
for t_ in [31.9, 33.5, END1 - 0.2]: cue("whoosh", t_, -11)
PICK = {"t_arr": 0.55, "t_tag": 0.68}
for x in SHOTS:
    pl = x.get("play") if x.get("mode") != "split" else "fb_r"
    slow = x["speed"] in ("slow2", "replay"); g = -5 if slow else 0
    if pl in ("fb_r", "fb_l", "sl_l_lhb", "sl_l_rhb"):
        pk = {"fb_r": "fb_r", "fb_l": "fb_l", "sl_l_lhb": "sl_l", "sl_l_rhb": "sl_l"}[pl]; fl = PI_[pk]["flight"]
        cue("whoosh", at_play(x, -fl + 0.08), -6 + g); cue("glove", at_play(x, 0.0), g)
        if pl == "sl_l_lhb": cue("whoosh", at_play(x, -0.06), -4 + g)                               # the swing through it
    if pl == "pick":
        cue("whoosh", at_play(x, 0.04), -4 + g); cue("glove", at_play(x, PICK["t_arr"]), -1 + g)
        cue("impact", at_play(x, 0.38), -10 + g); cue("tap", at_play(x, 0.42), -3 + g)             # the runner hits the dirt
        if x.get("freeze"): cue("tick", x["freeze"][0], -2)
    if pl == "hold": cue("tap", at_play(x, 0.95), -8)
    if pl == "walk":
        for k in range(8): cue("tap", at_play(x, 0.35 + k * 0.33), -16)
cue("riser-m", END1, -4); cue("impact", END1, -3); cue("impact", END1 + 0.45, -6); cue("impact", END2, -4)
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
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav"))
    crowd = np.concatenate([crowd] * (n // len(crowd) + 1))[:n]
    fx += crowd * 10 ** (-26 / 20)
    pre = os.path.join(HERE, ".pre.wav")
    w = wave.open(pre, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(fx * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-20.0)
    os.remove(pre)
    return m

def vo_cues():
    fmt = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)):03d}"
    with open(os.path.join(HERE, "vo-cues.srt"), "w") as f:
        for k, (a, b, line) in enumerate(VO): f.write(f"{k + 1}\n{fmt(a)} --> {fmt(b)}\n{line}\n\n")
    with open(os.path.join(HERE, "vo-cues.txt"), "w") as f:
        f.write("Voiceover cue sheet: start each line at its IN time and finish by its OUT time. The picture cuts on these.\n\n")
        for a, b, line in VO: f.write(f"{a:5.2f}  -  {b:5.2f}  ({b - a:3.1f} s)   {line}\n")

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
.hk {{ top:300px; font-size:150px; }} .hk em {{ font-style:normal; }}
.st {{ position:absolute; left:52px; right:40px; top:250px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:104px; line-height:.94; text-transform:uppercase; color:#fff;
       text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.st em {{ font-style:normal; color:{HOT}; }}
.side {{ position:absolute; top:560px; width:540px; display:grid; justify-items:center; }} .side.l {{ left:0; }} .side.r {{ left:540px; }}
.side b {{ padding:8px 22px; border-radius:12px; background:rgba(6,10,18,.84); font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:60px; text-transform:uppercase; }}
.leg .mono {{ color:#cfd6e0; }}
.leg {{ top:560px; }}
.mdl {{ font-size:23px; left:50%; right:auto; transform:translateX(-50%); white-space:nowrap; padding:8px 16px; border-radius:10px; background:rgba(6,10,18,.8); }}
.pinw {{ position:absolute; left:0; top:0; width:0; height:0; }}
.pin {{ position:absolute; left:-300px; width:600px; bottom:26px; display:flex; justify-content:center; }}
.pin span {{ padding:8px 16px; border-radius:10px; background:{HOT}; color:#05080d; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:44px; text-transform:uppercase; white-space:nowrap; box-shadow:0 4px 18px rgba(0,0,0,.5); }}
.abs {{ top:1250px; }}
.endt {{ top:300px; font-size:150px; }}
.endv {{ position:absolute; left:52px; right:40px; top:1610px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:96px; line-height:.95; text-transform:uppercase; color:#fff;
         text-shadow:0 6px 28px rgba(0,0,0,.85); }}
.endv em {{ font-style:normal; color:{HOT}; }}
.cbl {{ top:1580px; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}}
    h = c.page(CSS, "Why every team wants a lefty", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    vo_cues()
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; effects {m['lufs']} LUFS / {m['true_peak']} dBTP; {len(VO)} voiceover cues")
