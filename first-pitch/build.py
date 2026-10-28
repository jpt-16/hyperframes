"""'Take the first pitch, or swing?': a first-pitch breakdown (1080x1920, voiceover + music + effects).

    python3 tools/physics.py                                       # pitches + batted balls -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_michael) + word timing
    python3 build.py                                               # index.html + assets/mix.wav (+ assets/mix-novo.wav without the voice)
    npx --yes hyperframes@0.8.154 render . -o renders/first-pitch.mp4 --video-bitrate 16M

Shots, captions and reveals are keyed to the words of the voiceover. The first-pitch strike rate shown (~60%) is the
approximate MLB league average in recent seasons (about 61-62%); it varies by season, pitcher and hitter. The ten
pitches drawn on the zone are an illustration (6 of them are strikes by the zone test in tools/physics.py).
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
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
S2, S3, S3B, S4, S4B, S5, S6 = (LN(k)["t0"] - 0.06 for k in ["data", "twist", "twist2", "drive", "edge", "goal", "q"])
TC = lambda k: PI_[k]["t_contact"]

# ----------------------------------------------------------------- shots (video time v) and the play time each one shows
SHOTS = []
def shot(a, b, cam, vs, ts, speed, **kw):
    SHOTS.append(dict(a=round(a, 4), b=round(b, 4), cam=cam, vs=[round(x, 4) for x in vs], ts=[round(x, 4) for x in ts], speed=speed, **kw))
def rate(a, b, cam, t0, r, speed, **kw): shot(a, b, cam, [a, b], [t0, t0 + (b - a) * r], speed, **kw)
def on(v, t, a, r=1.0): return t - (v - a) * r                    # the play time to start a shot at a so that play time t lands at video time v
FLASH = []
# 1 hook: over his shoulder as the pitcher lets go; the ball slows and freezes a foot from the plate; the camera pushes in
FRZ = 2.0
shot(0.0, S2, "hook", [0.0, 0.55, FRZ, S2], [-0.98, -0.43, -0.07, -0.07], "none", play="hook", show={"zone": 1})
# 2 the data: four first pitches in a row, marked strike or ball where they cross; then the zone with ten of them, ~60%
DEL = ["d1", "d2", "d6", "d5"]
v = S2
for k, d in enumerate(DEL):
    rate(v, v + 0.5, "cf", -0.3, 1, "rt", play=d, show={"zone": 1, "mark": 1, "marks": DEL[:k]}); FLASH.append(v); v += 0.5
REST = ["d3", "d4", "d7", "d8", "d9", "d10"]
rate(v, S3, "zone", -0.5, 1, "rt", play="d10", show={"zone": 1, "mark": 1, "marks": DEL}, marksT={d: -0.5 + 0.12 * (i + 1) for i, d in enumerate(REST[:-1])})
ZV = v
# 3 the twist: he takes a strike (it crosses on "pitch"); behind the catcher, at half speed, it crosses on "count"; the call
A3 = W("twist", "behind") - 0.14
rate(S3, A3, "cf", on(W("twist", "pitch"), 0.0, S3), 1, "rt", play="take", call="strike")
rate(A3, S3B, "ump", on(W("twist", "count"), -0.03, A3, 0.5), 0.5, "replay", play="take", call="strike", show={"zone": 1, "mark": 1, "tube": 1})
#   ...but swinging at everything: a chase at a slider in the dirt, on "everything"
rate(S3B, S4, "cf", on(W("twist2", "everything"), -0.05, S3B), 1, "rt", play="chase", show={"zone": 1, "mark": 1})
# 4 a pitch he can drive: contact on "drive", into the gap
A4 = W("drive", "in") - 0.1
rate(S4, A4, "bat", on(W("drive", "drive"), TC("mid"), S4), 1, "rt", play="mid")
rate(A4, S4B, "gap", on(W("drive", "drive"), TC("mid"), S4) + (A4 - S4), 1, "rt", play="mid")             # the line drive into the gap
#   on the edge vs. in his zone, side by side (contact on "edge"); then an edge pitch just off, taken (it crosses on "smarter")
B4 = W("edge", "taking") - 0.1
rate(S4B, B4, "front", on(W("edge", "edge"), TC("edge"), S4B), 1, "rt", mode="split")
rate(B4, S5, "ump", on(W("edge", "smarter"), -0.03, B4), 1, "rt", play="off", show={"zone": 1, "mark": 1, "tube": 1})
# 5 composed: close on his eyes as the pitch comes; over his shoulder, slowing; the freeze (the hook's frame, so it loops)
A5 = W("goal", "it's") - 0.1
rate(S5, A5, "face", -2.35, 1, "rt", play="final")
shot(A5, D, "hook", [A5, S6, D], [on(S6, -0.07, A5, 0.3), -0.07, -0.07], "none", play="final", show={"zone": 1})
FLASH.append(A5)
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
for f in [FRZ] + FLASH[1:]:
    c.set("#flash", '{"opacity":0.7}', f); c.to("#flash", o(opacity=0, duration=0.14, ease="power2.out"), f + 0.001)

def pop(sel, t, dy=24):
    c.ft(sel, o(opacity=0, y=dy, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.26, ease="back.out(1.7)"), t)
def tag(tid, t0, t1, cls, text, top=1180):
    c.clip(tid, t0, t1, f'<div class="tg {cls}" id="{tid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12"); pop(f"#{tid}x", t0, 14)
def note(nid, t0, t1, text, top=1300):
    c.clip(nid, t0, t1, f'<div class="mdl" id="{nid}x" style="top:{top}px">{text}</div>', cls="layer", style="z-index:12")
    c.ft(f"#{nid}x", o(opacity=0), o(opacity=1, duration=0.3), t0)
def punch(pid, t0, t1, html, top=1020):
    c.clip(pid, t0, t1, f'<div class="pt" id="{pid}x" style="top:{top}px">{html}</div>', cls="layer", style="z-index:14")
    c.ft(f"#{pid}x", o(opacity=0, scale=1.25, filter="blur(8px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.2, ease="power3.out"), t0)
WORD_IN = lambda sel, t: c.ft(sel, o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), t - 0.04)

# ----------------------------------------------------------------- 1 the hook: the question, readable on frame one
c.clip("hook", 0, S2 - 0.02, """<div class="eyebrow"><i></i>Baseball Decoded</div>
  <div class="hk" id="hkx"><span class="hl">Take it…</span><span class="hl acc">or swing?</span></div>""", cls="layer", style="z-index:12")
c.ft("#hkx", o(scale=1.08, transformOrigin="0% 50%"), o(scale=1, duration=0.3, ease="power3.out"), 0.0)
c.ft("#hkx .acc", o(scale=1.0), o(scale=1.1, duration=0.1, ease="power2.out", yoyo=True, repeat=1), FRZ)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.12, ease="power2.in"), S2 - 0.14)

# ----------------------------------------------------------------- captions: the voiceover, word by word (not over the hook or the closing question)
CAPS = [("data", 0, 2, {0: "acc"}), ("data", 3, 5, {}), ("data", 6, 10, {9: "acc", 10: "acc"}), ("data", 11, 15, {13: "acc"}), ("data", 16, 18, {}),
        ("twist", 0, 5, {2: "acc"}), ("twist", 6, 12, {9: "acc"}), ("twist", 13, 18, {18: "acc"}),
        ("twist2", 0, 3, {1: "acc", 3: "acc"}), ("twist2", 4, 7, {}),
        ("drive", 0, 6, {6: "acc"}), ("drive", 7, 10, {9: "acc", 10: "acc"}), ("drive", 11, 17, {11: "acc", 16: "acc"}),
        ("edge", 0, 5, {5: "acc"}), ("edge", 6, 12, {10: "acc"}), ("edge", 13, 19, {13: "cb", 18: "cb"}),
        ("goal", 0, 6, {4: "acc"}), ("goal", 7, 10, {9: "acc"}), ("goal", 11, 16, {13: "acc", 15: "acc"})]
for k, (lid, i0, i1, acc) in enumerate(CAPS):
    ln = LN(lid); words = ln["words"]
    start = words[i0]["t0"] - 0.06
    if k + 1 < len(CAPS) and CAPS[k + 1][0] == lid: end = words[CAPS[k + 1][1]]["t0"] - 0.06
    else: end = min(ln["t1"] + 0.35, TM["lines"][IDX[lid] + 1]["t0"] - 0.1)
    cid = f"cap{k}"; sp = []
    for n in range(i0, i1 + 1):
        w = words[n]["w"]; w = w.rstrip(",:") if n == i1 else w
        if lid == "data" and n == 9: w = "60"                                       # spoken "sixty", written as the number
        sp.append(f'<span class="cw{(" " + acc[n]) if n in acc else ""}" id="{cid}w{n - i0}">{esc(w)}</span>')
    c.clip(cid, start, end, f'<div class="cap" style="top:300px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
    for n in range(i0, i1 + 1): WORD_IN(f"#{cid}w{n - i0}", words[n]["t0"])

# ----------------------------------------------------------------- 2 the data
for k, d in enumerate(DEL):
    a = S2 + 0.5 * k; tt = a + 0.3 + 0.02
    lab, cls = ("Strike", "yl") if PI_[d]["strike"] else ("Ball", "gr")
    c.clip(f"dl{k}", tt, a + 0.5, f'<div class="rs {cls}" id="dl{k}x">{lab}</div>', cls="layer", style="z-index:13"); pop(f"#dl{k}x", tt, 10)
c.clip("leg", ZV + 0.05, S3 - 0.02, '<div class="leg"><span class="yl"><i></i>Strike</span><span class="gr"><i class="ring"></i>Ball</span></div>', cls="layer", style="z-index:12")
T60 = W("data", "sixty")
c.clip("pct", T60 - 0.45, S3 - 0.02, '<div class="pct" id="pctx"><b><span class="ap">~</span><span id="pctn">60</span>%</b><span class="pl">First-pitch strike rate</span></div>', cls="layer", style="z-index:15")
c.ft("#pctx", o(opacity=0, scale=0.85), o(opacity=1, scale=1, duration=0.22, ease="back.out(1.6)"), T60 - 0.45)
c.ft("#pctn", o(innerText=0), o(innerText=60, duration=0.45, ease="power2.out", snap="innerText"), T60 - 0.45)
note("src", T60 + 0.4, S3 - 0.02, "Approx. MLB average (≈61–62% recent seasons) · varies by season, pitcher, hitter", 1520)

# ----------------------------------------------------------------- 3 the twist: the count
def count(cid, t0, t1, frm, to_, tchange):
    c.clip(cid, t0, t1, f'<div class="cnt" id="{cid}x"><span class="cl2">Count</span><b><span id="{cid}a">{frm}</span><span id="{cid}b" class="nw">{to_}</span></b></div>', cls="layer", style="z-index:21")
    pop(f"#{cid}x", t0, 10)
    c.set(f"#{cid}b", '{"opacity":0}', t0); c.to(f"#{cid}a", o(opacity=0, duration=0.08), tchange); c.ft(f"#{cid}b", o(opacity=0, scale=1.6), o(opacity=1, scale=1, duration=0.25, ease="back.out(2)"), tchange)
count("ct1", S3 + 0.1, S3B - 0.02, "0–0", "0–1", W("twist", "count"))
punch("p1", W("twist", "behind") - 0.05, S3B - 0.02, 'Take = possibly<br><em>down 0–1</em>', 1400)
tag("tc", S3B + 0.2, S4 - 0.05, "gr", "Chasing a slider in the dirt", 1180)

# ----------------------------------------------------------------- 4 the breakdown
punch("p2", W("drive", "drive") - 0.05, S4B - 0.02, 'Good pitch?<br><em>Attack it.</em>')
c.clip("splt", S4B, B4 - 0.02, '<div class="seam"></div><div class="side l" id="sdl"><b>On the edge</b><span id="sdl2" class="gr">Weak contact</span></div><div class="side r" id="sdr"><b class="acc">In his zone</b><span id="sdr2" class="yl">Driven</span></div>', cls="layer", style="z-index:11")
pop("#sdl", S4B + 0.05, 12); pop("#sdr", S4B + 0.12, 12)
TCV = W("edge", "edge") + 0.25
c.set("#sdl2", '{"opacity":0}', S4B); c.set("#sdr2", '{"opacity":0}', S4B); pop("#sdl2", TCV, 10); pop("#sdr2", TCV + 0.08, 10)
punch("p3", W("edge", "pitch") - 0.05, B4 - 0.02, 'Pitch location<br><em>matters.</em>', 1240)
count("ct2", B4 + 0.05, S5 - 0.02, "0–0", "1–0", W("edge", "smarter") + 0.05)
tag("to", B4 + 0.2, S5 - 0.05, "wh", "Just off the edge: take it", 1180)

# ----------------------------------------------------------------- 5 the conclusion
punch("p4", W("goal", "swing") - 0.05, S6 - 0.02, "Don't swing early.", 1020)
punch("p5", W("goal", "attack") - 0.05, S6 - 0.02, '<em>Swing at the right pitch.</em>', 1150)
c.clip("q", S6 + 0.02, D, '<div class="hk qq2" id="qx"><span class="hl">Would you</span><span class="hl"><em class="acc">swing</em> or <em class="cb">take?</em></span></div>', cls="layer", style="z-index:22")
c.ft("#qx", o(opacity=0, y=40, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.22, ease="power3.out"), S6 + 0.04)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -6); cue("impact", FRZ, -1); cue("tick", FRZ, -2)
for t_ in [S2, S3, S3B, S4, S4B, S5]: cue("whoosh", t_, -9)
CRACKS = []
for x in SHOTS:
    pl = x.get("play") if x.get("mode") != "split" else "mid"
    if pl not in PI_: continue
    slow = x["speed"] in ("slow2", "replay"); g = -5 if slow else 0
    fl = PI_[pl]["flight"]
    cue("whoosh", at_play(x, -fl + 0.08), -8 + g)
    if pl in ("mid", "edge"):
        v0 = at_play(x, TC(pl))
        if v0 is not None: CRACKS.append((v0, 0.85 if pl == "mid" else 0.35))
        if x.get("mode") == "split" and v0 is not None: CRACKS.append((v0 + 0.02, 0.3))
    elif pl == "chase": cue("whoosh", at_play(x, -0.08), -3 + g); cue("glove", at_play(x, 0.0), -2 + g)
    elif pl not in ("hook", "final"): cue("glove", at_play(x, 0.0), -1 + g)
    if x.get("call") == "strike": cue("impact", at_play(x, 0.33), -9 + g)
for k in range(len(DEL)): cue("popup", S2 + 0.5 * k + 0.32, -12)
cue("popup", W("twist", "count"), -6); cue("popup", W("edge", "smarter") + 0.05, -6)
cue("riser-s", T60 - 0.45, -6); cue("impact", T60 - 0.02, -5)
cue("impact", W("goal", "swing") - 0.05, -9); cue("impact", W("goal", "attack") - 0.05, -7)
cue("riser-m", S6 + 0.04, -6); cue("impact", S6 + 0.04, -3)
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
    fx += crowd * 10 ** (-32 / 20)
    # the music bed: made for this video (lands its chord on the closing question), ducked under the voice
    bedp = os.path.join(HERE, "assets", "bed.wav"); make_bed(bedp, D, S6 + 0.04, style="pulse", seed=11)
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
.hk {{ top:300px; font-size:150px; }} .hk em {{ font-style:normal; }} .hk .hl.acc {{ color:{HOT}; }}
.hk.qq2 {{ top:300px; font-size:132px; }} .hk .cb {{ color:{CYAN}; }}
.pt {{ position:absolute; left:52px; right:120px; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:104px; line-height:.95; text-transform:uppercase; color:#fff;
       text-shadow:0 6px 28px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.7); }}
.pt em {{ font-style:normal; color:{HOT}; }}
.pct {{ position:absolute; left:52px; right:120px; top:1130px; display:grid; gap:2px; }}
.pct b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:280px; line-height:.85; color:{Y}; text-shadow:0 8px 34px rgba(0,0,0,.85); }}
.pct .ap {{ font-size:200px; color:#fff; }}
.pct .pl {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:64px; text-transform:uppercase; color:#fff; text-shadow:0 4px 20px rgba(0,0,0,.85); }}
.mdl {{ font-size:22px; left:52px; right:auto; transform:none; white-space:normal; max-width:880px; text-align:left; padding:8px 14px; border-radius:10px; background:rgba(6,10,18,.8); }}
.rs {{ position:absolute; left:52px; top:1180px; padding:10px 22px; border-radius:12px; background:rgba(6,10,18,.86); font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:64px; text-transform:uppercase; }}
.rs.yl, .yl {{ color:{Y}; }} .gr, .rs.gr {{ color:#c4ccd6; }}
.leg {{ top:560px; }} .leg i.ring {{ background:transparent; border:4px solid currentColor; }}
.cnt {{ position:absolute; left:40px; top:205px; display:flex; align-items:center; gap:14px; padding:8px 18px; border-radius:12px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.14); }}
.cnt .cl2 {{ {MONO} font-size:22px; letter-spacing:.14em; color:{MUTED}; }}
.cnt b {{ position:relative; display:inline-grid; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:56px; color:#fff; }}
.cnt b > span {{ grid-area:1/1; }} .cnt .nw {{ color:{HOT}; }}
.tg {{ left:52px; transform:none; }}
.side {{ position:absolute; top:560px; width:540px; display:grid; justify-items:center; gap:10px; }} .side.l {{ left:0; }} .side.r {{ left:540px; }}
.side b {{ padding:8px 20px; border-radius:12px; background:rgba(6,10,18,.84); font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:50px; text-transform:uppercase; color:#fff; }}
.side b.acc {{ color:{HOT}; }}
.side span {{ padding:6px 16px; border-radius:10px; background:rgba(6,10,18,.84); font-family:"Inter", sans-serif; font-weight:800; font-size:30px; }}
"""

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": {"list": SHOTS}}
    h = c.page(CSS, "Take the first pitch, or swing?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, {len(SHOTS)} shots; {len(c.cues)} sounds; {len(CAPS)} caption phrases; {m['lufs']} LUFS / {m['true_peak']} dBTP")
