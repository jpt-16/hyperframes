"""'Why every team wants a lefty': the left-hander's three edges (1080x1920, voiceover + effects).

    python3 tools/physics.py                                       # the pitches -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav, effects only)
    npx --yes hyperframes@0.8.154 render . -o renders/lefty.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover.
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
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S4, S5 = (LN(k)["t0"] - 0.06 for k in ["see", "ll", "run", "combo"])      # scene changes, on the voiceover

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r                   # the play time to start a shot at a so that play time t lands at video time v
# 1 hook: one continuous shot, the left-hander through his delivery at half speed; the question builds over it
rate(0.0, S2, "hookP", on(W("q", "pitcher") + 0.05, -0.48, 0.0, 0.5), 0.5, "none", play="sl_l_lhb")
# 2 a different look: what hitters see most (the pitch in on "more"); the same pitch from each side; the hitter's view of the lefty
A2 = LN("angle")["t0"] - 0.06
rate(S2, A2, "behind", on(W("see", "more"), 0.0, S2), 1, "rt", play="fb_r", show={"ghost": ["fb_r", "sl_r", "ch_r", "cu_r"], "ghostT0": on(W("see", "most"), 0.0, S2) - 0.1, "tube": "fb_r"})
B2 = W("angle", "can") - 0.08
rate(A2, B2, "behind", on(W("angle", "release") + 0.1, -0.43, A2, 0.5), 0.5, "slow2", mode="split")
rate(B2, S3, "eye", on(W("angle", "different") + 0.25, 0.0, B2, 0.5), 0.5, "slow2", play="fb_l", noHitter=True, show={"tube": "fb_l", "ghost": ["fb_r"]})
# 3 lefty vs lefty: the left-handed hitter chases (on "matchup"); the replay at the zone; the same pitch to a right-hander (on "same side")
A3 = LN("ll2")["t0"] - 0.06
rate(S3, A3, "plate", on(W("ll", "matchup") + 0.15, 0.0, S3), 1, "rt", play="sl_l_lhb")
B3 = W("ll2", "pitchers") - 0.1
rate(A3, B3, "zone", -0.85, 0.5, "replay", play="sl_l_lhb", show={"zone": 1, "mark": 1, "tube": "sl_l"})
rate(B3, S4, "plate", on(W("ll2", "same"), 0.0, B3), 1, "rt", play="sl_l_rhb", show={"tube": "sl_l"})
# 4 the running game: the lead; over his shoulder in the set; the pickoff (thrown on "easier"); the replay, frozen on his step
A4 = LN("run2")["t0"] - 0.06
rate(S4, A4, "wide", -6.3, 1, "rt", play="pick")
C4 = W("run2", "making") - 1.4
rate(A4, C4, "pov", -1.22 - (C4 - A4), 1, "rt", play="pick", show={"sight": 1})
TREL = W("run2", "easier") + 0.25
D4 = TREL + 0.8
rate(C4, D4, "pick", on(TREL, 0.0, C4), 1, "rt", play="pick")
FRZ = (D4 + 0.1, D4 + 0.55)
shot(D4, S5, "replay", [D4, FRZ[0], FRZ[1], S5], [-0.35, -0.3, -0.3, -0.3 + (S5 - FRZ[1]) * 0.5], "replay", play="pick", freeze=list(FRZ), show={"lead": 1, "step": 1})
# 5 the payoff: the pitch (released on "stuff"), the left-handed hitter, the runner frozen at first; the pitcher back on the mound
P2 = W("combo", "command") - 0.1
rate(S5, P2, "low", on(W("combo", "stuff"), -0.48, S5), 1, "none", play="sl_l_lhb")
P3 = W("combo", "who") - 0.1
rate(P2, P3, "catcherV", -0.3, 1, "none", play="sl_l_lhb")
END1 = LN("end")["t0"] - 0.25                                  # "ONE ARM. THREE ADVANTAGES."
rate(P3, END1 - 0.2, "first", 0.0, 1, "none", play="hold")
rate(END1 - 0.2, D, "walk", 0.2, 1, "none", play="walk")
END2 = W("end", "lefty") - 0.05                               # "THAT'S THE VALUE OF A LEFTY."
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

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def note(nid, t0, t1, text, top=1700):
    c.clip(nid, t0, t1, f'<div class="mdl" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12")
    c.ft(f"#{nid}x", o(opacity=0), o(opacity=1, duration=0.3), t0)
WORD_IN = lambda sel, t: c.ft(sel, o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), t - 0.04)

# ----------------------------------------------------------------- 1 the hook: the question, word by word with the voice ("lefty?" on "left-handed")
HQ = [("Why", "why"), ("does", "does"), ("every", "every"), ("team", "team"), ("want", "want"), ("a", "a"), ("lefty?", "left-handed")]
rows = [[0, 1], [2, 3], [4, 5, 6]]
html = "".join('<span class="hl">' + " ".join(f'<span class="hw{" acc" if k == 6 else ""}" id="hq{k}">{esc(HQ[k][0])}</span>' for k in r) + "</span>" for r in rows)
c.clip("hook", 0, S2 - 0.02, f'<div class="eyebrow"><i></i>Baseball Decoded</div><div class="hk" id="hkx">{html}</div>', cls="layer", style="z-index:12")
for k, (_, w) in enumerate(HQ): WORD_IN(f"#hq{k}", 0.04 if k == 0 else W("q", w))      # "Why" is there on frame one
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S2 - 0.16)

# ----------------------------------------------------------------- scene chips (top left)
for k, (a_, b_, name) in enumerate([(S2, S3, "A different look"), (S3, S4, "The lefty-lefty matchup"), (S4, S5, "Control the running game")]):
    c.clip(f"sk{k}", a_ + 0.05, b_ - 0.02, f'<div class="skill" id="sk{k}x"><b>{k + 1}</b><span>{name}</span></div>', cls="layer", style="z-index:21")
    c.ft(f"#sk{k}x", o(opacity=0, x=-40), o(opacity=1, x=0, duration=0.22, ease="power3.out"), a_ + 0.08)

# ----------------------------------------------------------------- captions: the voiceover, word by word (the hook and the end card are titles instead)
CAPS = [("see", 0, 1, {}), ("see", 2, 6, {3: "acc"}), ("see", 7, 10, {9: "cb", 10: "cb"}),
        ("angle", 0, 3, {1: "acc"}), ("angle", 4, 6, {6: "acc"}), ("angle", 7, 10, {10: "acc"}),
        ("ll", 0, 4, {3: "acc"}),
        ("ll2", 0, 2, {0: "acc"}), ("ll2", 3, 6, {5: "acc"}), ("ll2", 7, 9, {}), ("ll2", 10, 13, {12: "acc", 13: "acc"}),
        ("run", 0, 3, {3: "acc"}), ("run", 4, 5, {4: "acc", 5: "acc"}),
        ("run2", 0, 2, {1: "acc"}), ("run2", 3, 6, {5: "acc", 6: "acc"}), ("run2", 7, 11, {11: "acc"}), ("run2", 12, 15, {}), ("run2", 16, 18, {16: "acc"}), ("run2", 19, 22, {20: "acc", 22: "acc"}),
        ("combo", 0, 4, {}), ("combo", 5, 9, {7: "acc", 9: "acc"}), ("combo", 10, 13, {}), ("combo", 14, 19, {16: "acc", 18: "acc", 19: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1, END1 - 0.02)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",:") if n == i1 else w
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): WORD_IN(f"#{cid}w{n - i0}", words[n]["t0"])

# ----------------------------------------------------------------- 2 a different look
tag("fam", W("see", "most") - 0.05, A2 - 0.05, "wh", "Most hitters see far more right-handers", 1560)
c.clip("splt", A2, B2 - 0.02, '<div class="seam"></div><div class="side l" id="sdl"><b class="cb">Righty</b></div><div class="side r" id="sdr"><b class="hot">Lefty</b></div>', cls="layer", style="z-index:11")
pop("#sdl", A2 + 0.05, 12); pop("#sdr", A2 + 0.15, 12)
tag("same", A2 + 0.3, B2 - 0.05, "wh", "Same pitch, mirrored: a different release angle", 1560)
c.clip("eyel", B2 + 0.02, S3 - 0.02, '<div class="leg"><span class="mono">The hitter\'s view</span><span class="cb"><i></i>The usual righty path</span><span class="hot"><i></i>The lefty\'s pitch</span></div>', cls="layer", style="z-index:11")
tag("eyet", B2 + 0.2, S3 - 0.05, "hot", "From the other side: a less familiar look", 1560)

# ----------------------------------------------------------------- 3 lefty vs lefty
tag("ll", S3 + 0.3, A3 - 0.05, "hot", "Lefty pitcher vs. lefty hitter", 1560)
tag("away", A3 + 0.2, B3 - 0.05, "yl", "Starts on his side, then breaks away", 1560)
tag("rh", B3 + 0.2, S4 - 0.05, "cb", "Righty hitter: the same pitch breaks toward him", 1560)
note("avg", A3 + 0.2, S4 - 0.05, "On average, a tougher matchup · not true of every hitter")

# ----------------------------------------------------------------- 4 the running game
tag("rn", S4 + 0.3, A4 - 0.05, "wh", "Runner on first · lefty in the stretch", 1120)
c.clip("setc", A4 + 0.05, C4 - 0.05, """<div class="abs" id="setx"><div class="ar"><b class="cb">Righty in the set</b><span>Faces third base: the runner is behind him</span></div>
  <div class="ar" id="set2"><b class="hot">Lefty in the set</b><span>Faces first base: the runner is right in front of him</span></div></div>""", cls="layer", style="z-index:12")
pop("#setx", A4 + 0.1); pop("#set2", W("run2", "faces") - 0.05, 12)
c.clip("lead", FRZ[0] - 0.02, S5 - 0.02, '<div class="pinw" id="leadw"><div class="pin" id="leadx"><span>His lead</span></div></div><div class="pinw" id="stepw"><div class="pin" id="stepx"><span>Step to first</span></div></div>', cls="layer", style="z-index:12")
pop("#leadx", FRZ[0]); pop("#stepx", FRZ[0] + 0.12)
note("mv", FRZ[0] + 0.2, S5 - 0.05, "A good move is a threat · not a guaranteed out")

# ----------------------------------------------------------------- 5 the payoff
for k, (a_, b_, lab) in enumerate([(S5, P2, "1 · A different look"), (P2, P3, "2 · Lefty vs. lefty"), (P3, END1 - 0.2, "3 · The pickoff threat")]):
    c.clip(f"pay{k}", a_ + 0.03, b_ - 0.02, f'<div class="cbl" id="pay{k}x">{esc(lab)}</div>', cls="layer", style="z-index:21")
    pop(f"#pay{k}x", a_ + 0.05, 18)
c.clip("endt", END1, D, '<div class="endt"><span id="et1">One arm.</span><span class="acc" id="et2">Three advantages.</span></div><div class="endv" id="et3">That\'s the value of a <em class="acc">lefty.</em></div>', cls="layer", style="z-index:22")
c.ft("#et1", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), END1)
c.ft("#et2", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), END1 + 0.4)
c.ft("#et3", o(opacity=0, y=30, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.25, ease="power3.out"), END2)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -4)
for t_ in [S2, S3, S4, S5]: cue("whoosh", t_, -9)
for t_ in [P2, P3, END1 - 0.2]: cue("whoosh", t_, -11)
PICK = {"t_arr": 0.55, "t_tag": 0.68}
for x in SHOTS:
    pl = x.get("play") if x.get("mode") != "split" else "fb_r"
    slow = x["speed"] in ("slow2", "replay") or x["cam"] == "hookP"; g = -5 if slow else 0
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
cue("riser-m", END1, -4); cue("impact", END1, -3); cue("impact", END1 + 0.4, -6); cue("impact", END2, -4)
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
    fx += crowd * 10 ** (-28 / 20)
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo
    def wav(path, x):
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, pfx = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wav(pre, full); wav(pfx, fx * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=pfx)   # the same effects at the same level, without the voice
    os.remove(pre); os.remove(pfx)
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
.hk {{ top:300px; font-size:150px; }} .hk em {{ font-style:normal; }} .hk .hw {{ display:inline-block; }}
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
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {len(CAPS)} caption phrases; {m['lufs']} LUFS / {m['true_peak']} dBTP")
