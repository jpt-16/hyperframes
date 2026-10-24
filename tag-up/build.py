"""'Can he throw him out from here?': a runner tagging up from third against a throw home (1080x1920, voiceover + sound effects).

    python3 tools/physics.py                                   # the simulated play -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (hyperframes tts) + word timing
    python3 build.py                                           # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/tag-up.mp4 --video-bitrate 16M

Every number on screen is read from assets/play.json, so the labels, timers and 3D motion always agree.
Shots, captions and reveals are keyed to the words of the voiceover (assets/vo/timing.json).
"""
import json, os, re, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
A, DR, LP, FL = P["assume"], P["direct"], P["loop"], P["flips"]
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    """Video time a spoken word starts (or ends) in line `lid` (punctuation ignored)."""
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, ORANGE, WHITE, RED, GREEN, HOT = "#FFD84D", "#56D1FF", "#FF8A3D", "#F4F6F8", "#FF5A5A", "#3DD68C", "#FF6A3D"
GAP = A["r_dist"] - DR["runner_at_tag"]
f2 = lambda x: f"{x:.2f}"

# ----------------------------------------------------------------- shots: video time v, play time t (t = 0 at the catch), keyed to the voiceover
S = dict(sw0=0.55, ringT=W("catch", "outfielder"), catchV=W("catch", "catches", end=True) + 0.05,
         dl0=W("catch", "from"), dl1=W("catch", "plate", end=True) + 0.25,
         v3=LN("exch")["t0"] - 0.15, vRel=W("exch", "throw"), t4=1.0, v4=LN("speed")["t0"] - 0.15,
         v4b=W("speed", "but"), v5=LN("run")["t0"] - 0.1, t5=2.7, v6=LN("traj1")["t0"] - 0.2, t6=3.2,
         vLaunch=W("traj2", "a") - 0.05, rRep=0.51,
         v7=LN("race")["t0"] - 0.25, t7=2.95, vPlate=W("race", "plate"), vTime=W("race", "time", nth=-1) + 0.3,
         v8=LN("fact")["t0"] - 0.2, v9=LN("send")["t0"] - 0.3)
S["sw1"] = S["catchV"] - 0.9
S = {k: round(float(v), 4) for k, v in S.items()}

def vt(t):
    """Video time at which the live play reaches play time t (exchange -> throw -> runner shots)."""
    for vs, ts in [([S["v3"], S["vRel"], S["v4"]], [0, A["exchange"], S["t4"]]), ([S["v4"], S["v5"]], [S["t4"], S["t5"]]), ([S["v5"], S["v6"]], [S["t5"], S["t6"]])]:
        if ts[0] <= t <= ts[-1]: return float(np.interp(t, ts, vs))
    return None
def vt_race(t): return float(np.interp(t, [S["t7"], DR["glove_t"], DR["tag_t"]], [S["v7"], S["vPlate"], S["vTime"]]))

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("simtag", 0, D, '<div class="simtag"><i></i>Simulation · not MLB tracking data</div>', cls="layer", style="z-index:30")
c.ft(".simtag", o(opacity=0), o(opacity=1, duration=0.3), 0.05)

# ----------------------------------------------------------------- hook: a statement on frame one, then the question, word by word with the voice
c.clip("hook0", 0, S["sw0"] + 0.02, """<div class="eyebrow"><i></i>Sacrifice fly · the throw home</div>
  <div class="hk big"><span class="hl">Arm strength</span><span class="hl acc">isn't everything.</span></div>""", cls="layer", style="z-index:12")
c.to(".hk.big", o(opacity=0, y=-30, filter="blur(10px)", duration=0.14, ease="power2.in"), S["sw0"] - 0.14)
qw = LN("q")["words"]
HOOK_LINES = [(0, 4), (4, 7), (7, 9), (9, 13)]             # how hard is it / to throw out / a runner / tagging up from third?
html_lines = []
for li, (i0, i1) in enumerate(HOOK_LINES):
    html_lines.append('<span class="hl">' + " ".join(f'<span class="hw{" acc" if li == 3 else ""}" id="hw{k}">{esc(qw[k]["w"])}</span>' for k in range(i0, i1)) + "</span>")
c.clip("hook", S["sw0"], LN("brk")["t0"] - 0.1, '<div class="eyebrow"><i></i>Sacrifice fly · the throw home</div><div class="hk">' + "".join(html_lines) + "</div>", cls="layer", style="z-index:12")
for k, w in enumerate(qw):
    c.ft(f"#hw{k}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), w["t0"] - 0.04)
c.ft("#hw12", o(scale=1), o(scale=1.1, duration=0.12, ease="power2.out", yoyo=True, repeat=1), qw[12]["t0"])
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.16, ease="power2.in"), LN("brk")["t0"] - 0.26)

# ----------------------------------------------------------------- captions: the script word for word, each word arriving as it's spoken
ACC = {"300", "95", "fast", "time", "time?", "trajectory", "high", "looping", "low", "direct", "faster", "race", "tag", "alone", "sprinting", "accurate", "glove", "arm", "speed", "distance"}
def span_of(tok):
    if tok == "—": return 0
    if tok == "300": return 2                                     # three hundred
    return 1
def phrases(toks):
    out, cur = [], []
    for t in toks:
        if t == "—" and cur: cur.append(t); continue
        cur.append(t)
        n = len(" ".join(x for x in cur if x != "—"))
        if (t[-1] in ",.?:" and n >= 9) or n > 26:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out
CAP_TOP = lambda t: 278 if t < S["v3"] else 560
kcap = 0
for lid in ["brk", "catch", "exch", "speed", "run", "traj1", "traj2", "race", "why"]:
    ln = LN(lid); words = ln["words"]; toks = ln["text"].split()
    assert sum(span_of(t) for t in toks) == len(words), f"caption/voice mismatch on {lid}"
    times, j = [], 0
    for t in toks:
        n = span_of(t)
        times.append((words[j]["t0"], words[j + n - 1]["t1"]) if n else times[-1]); j += n
    groups, i = phrases(toks), 0
    nxt_line = TM["lines"][IDX[lid] + 1]["t0"] if IDX[lid] + 1 < len(TM["lines"]) else D
    for g in groups:
        gt = times[i:i + len(g)]
        start = gt[0][0] - 0.06
        end = times[i + len(g)][0] - 0.06 if i + len(g) < len(times) else min(ln["t1"] + 0.45, nxt_line - 0.08)
        cid = f"cap{kcap}"; kcap += 1
        spans = []
        for n, w in enumerate(g):
            if w == "—": continue
            key = re.sub(r"[^\w']", "", w).lower()
            spans.append(f'<span class="cw{" acc" if key in ACC else ""}" id="{cid}w{n}">{esc(w.rstrip(",:") if n == len(g) - 1 else w)}</span>')
        c.clip(cid, start, end, f'<div class="cap" style="top:{CAP_TOP(start)}px"><span class="cl">{" ".join(spans)}</span></div>', cls="layer", style="z-index:20")
        for n, (a_, b_) in enumerate(gt):
            if g[n] == "—": continue
            c.ft(f"#{cid}w{n}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.16, ease="power3.out"), a_ - 0.04)
        i += len(g)

# ----------------------------------------------------------------- freeze at the catch: the distance
cv = S["catchV"]
d_t = [W("catch", "three"), W("catch", "plate"), S["dl1"]]
c.clip("dist", cv, S["v3"] + 0.05, f"""<div class="frz" id="frz1"><i></i>Freeze · the catch</div>
  <div class="dcard" id="dcard">
    <div class="drow" id="d1"><span>Caught</span><b>{A["catch_dist"]:.0f} FT<small> from home</small></b></div>
    <div class="drow" id="d2"><span>Throw to the plate</span><b class="w">≈ {P["throw_dist"]:.0f} FT</b></div>
    <div class="drow" id="d3"><span>Runner, third to home</span><b class="cy">{A["r_dist"]:.0f} FT</b></div></div>""", cls="layer", style="z-index:10")
c.ft("#frz1", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), cv + 0.05)
c.ft("#dcard", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), d_t[0] - 0.2)
for sel, t in zip(["#d1", "#d2", "#d3"], d_t):
    c.ft(sel, o(opacity=0, x=-24), o(opacity=1, x=0, duration=0.28, ease="power3.out"), t)
c.to("#frz1, #dcard", o(opacity=0, duration=0.15), S["v3"] - 0.12)

# ----------------------------------------------------------------- the two clocks: runner and ball, both from the catch
HUD = f"""<div class="hud">
  <div class="clock run"><span class="cl">Runner</span><b><span id="tm-run">0.00</span><small>s</small></b><span class="cs" id="tm-run-ft">89.0 ft to go</span></div>
  <div class="clock ball"><span class="cl">Ball</span><b><span id="tm-ball">0.00</span><small>s</small></b><span class="cs" id="tm-ball-ph">exchange</span></div></div>"""
c.clip("hud", S["v3"] - 0.05, S["v6"], HUD.replace('class="hud"', 'class="hud" id="hud1"'), cls="layer", style="z-index:11")
c.ft("#hud1", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["v3"] - 0.05)
c.clip("hud2", S["v7"], S["v8"], HUD.replace('class="hud"', 'class="hud" id="hud2"').replace('id="tm-', 'id="tm2-'), cls="layer", style="z-index:11")
c.ft("#hud2", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["v7"])

v95 = W("speed", "ninety-five")
c.clip("thr", v95 - 0.05, S["v6"], f"""<div class="chips one"><div class="chip d" id="chd"><span class="ck">Release</span><b>{DR["mph"]:.0f}<small> mph</small></b><span class="ca">{DR["ang"]:.0f}° launch</span><span class="cf">flight <em id="tm-fl">0.00</em> s</span></div></div>""", cls="layer", style="z-index:11")
c.ft("#chd", o(opacity=0, scale=0.8), o(opacity=1, scale=1, duration=0.3, ease="back.out(2)"), v95 - 0.05)

# ----------------------------------------------------------------- trajectory: the replay, side view, to scale
v6, v7 = S["v6"], S["v7"]
land_d = S["vLaunch"] + DR["flight"] / S["rRep"]; land_l = S["vLaunch"] + LP["flight"] / S["rRep"]
c.clip("rep", v6 + 0.05, v7, f"""<div class="frz" id="rp0"><i></i>Replay · side view, to scale</div>
  <div class="chips"><div class="chip l" id="rpl"><span class="ck">High, looping</span><b>{LP["mph"]:.0f}<small> mph</small></b><span class="ca">{LP["ang"]:.0f}° launch</span><span class="cf">flight <em id="tm-rl">0.00</em> s</span></div>
  <div class="chip d" id="rpd"><span class="ck">Low, direct</span><b>{DR["mph"]:.0f}<small> mph</small></b><span class="ca">{DR["ang"]:.0f}° launch</span><span class="cf">flight <em id="tm-rd">0.00</em> s</span></div></div>
  <div class="arcl y" id="ald" style="top:1556px">Line · {DR["flight"]:.2f} s · {DR["apex"]:.0f} ft high</div>
  <div class="arcl o" id="all" style="top:1300px">Loop · {LP["flight"]:.2f} s in the air · {LP["apex"]:.0f} ft high</div>
  <div class="arce" style="left:34px">Right fielder</div><div class="arce" style="right:34px">Home</div>
  <div class="phys" id="phys">At {DR["mph"]:.0f} mph, {DR["ang"]:.0f}° is the flattest throw that still reaches the glove in the air.</div>""", cls="layer", style="z-index:11")
c.ft("#rp0", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), v6 + 0.1)
c.ft("#rpl, #rpd", o(opacity=0, y=-16), o(opacity=1, y=0, duration=0.28, ease="power3.out", stagger=0.08), S["vLaunch"] - 0.3)
c.ft("#rpl", o(scale=1), o(scale=1.07, duration=0.14, yoyo=True, repeat=1), W("traj2", "looping"))
c.ft("#rpd", o(scale=1), o(scale=1.07, duration=0.14, yoyo=True, repeat=1), W("traj2", "direct"))
c.ft("#ald", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.25), land_d)
c.ft("#all", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.25), land_l)
c.ft("#phys", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.3, ease="power3.out"), W("traj2", "physically") - 0.1)

# ----------------------------------------------------------------- freeze on the tag: OUT, and why
vT, v8 = S["vTime"], S["v8"]
vwhy = LN("why")["t0"]
c.clip("out", vT, v8, f"""<div class="stamp no" id="st1">OUT</div>
  <div class="why" id="why1">
    <div class="eqn"><span class="lab y">Ball</span><span class="parts"><b>{f2(A["exchange"])}</b><i>release</i></span><span class="op">+</span><span class="parts"><b>{f2(DR["flight"])}</b><i>flight</i></span><span class="op">+</span><span class="parts"><b>{f2(A["tag"])}</b><i>tag</i></span><span class="op">=</span><span class="parts tot y"><b>{f2(DR["tag_t"])}</b><i>seconds</i></span></div>
    <div class="eqn"><span class="lab cy">Runner</span><span class="need">needs <b class="cy">{f2(P["score_t"])} s</b> to reach the plate</span></div>
    <div class="marg" id="m1">Out by {f2(P["score_t"] - DR["tag_t"])} s · {GAP:.1f} ft short</div>
    <div class="alt" id="alt1">The {LP["ang"]:.0f}° loop: tag at <b class="o">{f2(LP["tag_t"])} s</b> · <b class="g">safe</b></div></div>""", cls="layer", style="z-index:12")
c.ft("#st1", o(opacity=0, scale=1.6, rotate=-8), o(opacity=1, scale=1, rotate=-8, duration=0.28, ease="back.out(2.2)"), vT + 0.05)
c.ft("#why1", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.32, ease="power3.out"), vwhy - 0.3)
c.ft("#m1", o(opacity=0, scale=0.9), o(opacity=1, scale=1, duration=0.3, ease="back.out(2)"), W("why", "alone"))
c.ft("#alt1", o(opacity=0, x=-20), o(opacity=1, x=0, duration=0.3, ease="power3.out"), W("why", "determine"))

# ----------------------------------------------------------------- what decides it: the rows light up as they're named
v9 = S["v9"]
rows = [("arm", "Arm strength", f'{DR["mph"]:.0f} mph', f'{FL["arm_mph"]:.1f} mph', S["v8"] + 0.35),
        ("dist", "Distance", f'{A["catch_dist"]:.0f} ft', f'{FL["catch_dist"]:.0f} ft', W("fact", "distance")),
        ("rel", "Release time", f'{A["exchange"]:.2f} s', f'{FL["exchange"]:.2f} s', W("fact", "release")),
        ("traj", "Trajectory", f'{DR["ang"]:.0f}° line', f'{LP["ang"]:.0f}° loop', W("fact", "trajectory")),
        ("acc", "Accuracy", "on the glove", "assumed", W("fact", "accuracy")),
        ("spd", "Runner's speed", f'{A["r_vmax"]:.1f} ft/s', f'{FL["runner_fps"]:.1f} ft/s', W("fact", "runner's"))]
rows_html = "".join(f'<div class="vr{" na" if k == "acc" else ""}" id="vr-{k}"><span class="vn">{esc(n)}</span><span class="va">{esc(a_)}</span><span class="arr">→</span><span class="vb">{esc(b_)}</span></div>' for k, n, a_, b_, _ in rows)
c.clip("end", S["v8"], v9 + 0.1, f"""<div class="endc" id="endc">
  <div class="eh">Out by <b>{f2(P["score_t"] - DR["tag_t"])} s</b>. Any one of these and he's safe:</div>
  <div class="vtab">{rows_html}</div>
  <div class="src">Accuracy isn't simulated: every throw here reaches the glove. Runner at {A["r_vmax"]:.0f} ft/s, the MLB average Statcast sprint speed (Baseball Savant). Drag + backspin lift (Cd {A["cd"]}, {A["throw_rpm"]:,} rpm); {A["r_react"]:.2f} s runner reaction; {A["tag"]:.2f} s tag.</div></div>""", cls="layer", style="z-index:12")
c.ft("#endc", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.35, ease="power3.out"), S["v8"] + 0.05)
for k, *_x, t in rows:
    c.ft(f"#vr-{k}", o(opacity=0.25, x=-18), o(opacity=1, x=0, duration=0.25, ease="power3.out"), t - 0.05)
c.to("#endc", o(opacity=0, y=-20, duration=0.2, ease="power2.in"), v9 - 0.1)

# ----------------------------------------------------------------- send him or hold him?
sw = LN("send")["words"]                                       # So, would you send the runner or hold him at third?
SEND_LINES = [(0, 3), (3, 6), (6, 9), (9, 11)]
send_html = "".join('<span class="hl">' + " ".join(f'<span class="hw{" acc" if sw[k]["w"].lower() in ("send", "hold") else ""}" id="sw{k}">{esc(sw[k]["w"])}</span>' for k in range(i0, i1)) + "</span>" for i0, i1 in SEND_LINES)
c.clip("send", v9, D, f'<div class="eyebrow"><i></i>Your call</div><div class="hk">{send_html}</div>', cls="layer", style="z-index:12")
for k, w in enumerate(sw):
    c.ft(f"#sw{k}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.2, ease="power3.out"), w["t0"] - 0.04)
for k, w in enumerate(sw):
    if w["w"].lower() in ("send", "hold"): c.ft(f"#sw{k}", o(scale=1), o(scale=1.12, duration=0.12, yoyo=True, repeat=1), w["t0"] + 0.18)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None: c.cue(n, t, db)
for k in ["v3", "v4", "v4b", "v5", "v6", "v7", "v8", "v9"]: cue("whoosh", S[k], -10)
cue("hit", 0.0, -6); cue("whoosh", S["sw0"] + 0.35, -5)
for w in qw: cue("tick", w["t0"], -13)
cue("glove", cv, -1); cue("impact", cv + 0.02, -9)
for t in d_t: cue("hit", t, -12)
cue("whoosh", S["vRel"], -3)
for t in np.arange(0.25, S["t6"], 0.25): cue("tick", vt(float(t)), -17)
cue("popup", v95, -9)
cue("whoosh", S["vLaunch"], -6); cue("glove", land_d, -6); cue("glove", land_l, -6); cue("popup", W("traj2", "physically"), -11)
for t in np.arange(S["t7"], DR["tag_t"], 0.1): cue("tick", vt_race(float(t)), -16)
cue("riser-m", vT, -9); cue("glove", S["vPlate"], -1); cue("impact", vT, -5); cue("hit", vT + 0.05, -4)
cue("popup", W("why", "alone"), -10)
for k, *_x, t in rows: cue("tick", t, -9)
for w in sw:
    if w["w"].lower() in ("send", "hold"): cue("hit", w["t0"] + 0.18, -8)
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -2.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0}

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
    crowd = np.concatenate([crowd, crowd[::-1]])[:n]               # 56 s bed, mirrored to cover the full length
    tt = np.arange(len(crowd)) / SR
    env = 1 + 1.0 * np.clip((tt - S["v7"]) / (vT - S["v7"]), 0, 1) * (tt < vT + 0.3)   # swells into the tag
    fx[: len(crowd)] += crowd * env[:, None] * 10 ** (-26 / 20)
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo              # effects sit under the voice
    pre = os.path.join(HERE, ".pre.wav")
    w = wave.open(pre, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(full * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
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
.shade-top {{ position:absolute; left:0; right:0; top:0; height:620px; background:linear-gradient(180deg, rgba(3,6,12,.62), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:820px; background:linear-gradient(0deg, rgba(3,6,12,.78) 0%, rgba(3,6,12,.42) 50%, rgba(3,6,12,0) 100%); }}
.simtag {{ position:absolute; left:40px; top:64px; display:inline-flex; align-items:center; gap:10px; padding:8px 14px; border-radius:8px; background:rgba(6,10,18,.7);
           {MONO} font-size:19px; letter-spacing:.14em; color:#cfd6e0; }}
.simtag i {{ width:10px; height:10px; border-radius:50%; background:{ORANGE}; }}

.eyebrow {{ position:absolute; left:56px; top:232px; display:flex; align-items:center; gap:14px; {MONO} font-size:24px; letter-spacing:.2em; color:#cfd6e0; text-shadow:0 2px 10px rgba(0,0,0,.8); }}
.eyebrow i {{ width:34px; height:3px; background:{HOT}; }}
.hk {{ position:absolute; left:52px; right:40px; top:278px; display:grid; gap:2px; font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase;
       font-size:124px; line-height:.94; letter-spacing:.005em; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.75), 0 2px 4px rgba(0,0,0,.6); }}
.hk.big {{ font-size:132px; }}
.hk .hl {{ display:block; }}
.hk .acc, .hk .hl.acc {{ color:{HOT}; }}
.hk .hw {{ display:inline-block; transform-origin:0 80%; }}
.hook {{ position:absolute; left:60px; right:60px; top:300px; font-family:"Inter", sans-serif; font-weight:800; font-size:96px; line-height:1.02; letter-spacing:-.03em;
         text-shadow:0 8px 34px rgba(0,0,0,.7); }}
.hook span, .hook em {{ display:inline-block; }}
.hook em {{ font-style:normal; color:{Y}; }}

.frz {{ position:absolute; left:50%; top:150px; transform:translateX(-50%); display:inline-flex; align-items:center; gap:12px; padding:10px 20px; border-radius:12px;
        background:rgba(6,10,18,.82); {MONO} font-size:24px; letter-spacing:.14em; color:{Y}; white-space:nowrap; }}
.frz.low {{ top:398px; }}
.frz i {{ width:12px; height:12px; border-radius:2px; background:{Y}; }}
.dcard {{ position:absolute; left:50px; right:50px; bottom:150px; display:grid; gap:14px; padding:26px 32px; border-radius:22px; background:rgba(6,10,18,.84); border:1px solid rgba(255,255,255,.1); }}
.drow {{ display:flex; align-items:baseline; justify-content:space-between; gap:20px; }}
.drow span {{ {MONO} font-size:24px; letter-spacing:.12em; color:#AEB8C6; }}
.drow b {{ font-weight:800; font-size:92px; line-height:1; color:{Y}; font-variant-numeric:tabular-nums; }}
.drow b small {{ font-size:40px; color:#cfd6e0; font-weight:700; }}
.drow b.w {{ color:{WHITE}; }} .drow b.cy {{ color:{CYAN}; }}

.hud {{ position:absolute; left:40px; right:40px; top:120px; display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.clock {{ display:grid; justify-items:start; padding:14px 26px 14px; border-radius:18px; background:rgba(6,10,18,.82); border:1px solid rgba(255,255,255,.12); }}
.clock .cl {{ {MONO} font-size:22px; letter-spacing:.16em; color:#AEB8C6; }}
.clock b {{ font-weight:800; font-size:110px; line-height:.95; font-variant-numeric:tabular-nums; }}
.clock b small {{ font-size:46px; margin-left:4px; opacity:.8; }}
.clock .cs {{ font-family:"Inter", sans-serif; font-weight:700; font-size:26px; color:#cfd6e0; font-variant-numeric:tabular-nums; }}
.clock.run b {{ color:{CYAN}; }} .clock.run {{ border-color:rgba(86,209,255,.35); }}
.clock.ball b {{ color:{Y}; }} .clock.ball {{ border-color:rgba(255,216,77,.35); }}

.chips {{ position:absolute; left:40px; right:40px; top:398px; display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.chips.one {{ grid-template-columns:1fr 1fr; }}
.chip {{ display:grid; grid-template-columns:auto 1fr; align-items:baseline; gap:2px 14px; padding:12px 22px; border-radius:16px; background:rgba(6,10,18,.8); border:2px solid; }}
.chip .ck {{ grid-column:1 / -1; {MONO} font-size:19px; letter-spacing:.12em; color:#AEB8C6; }}
.chip b {{ font-weight:800; font-size:66px; line-height:1; }}
.chip b small {{ font-size:30px; }}
.chip .ca {{ font-family:"Inter", sans-serif; font-weight:700; font-size:26px; color:#dfe5ec; }}
.chip .cf {{ grid-column:1 / -1; font-family:"Inter", sans-serif; font-weight:700; font-size:26px; color:#cfd6e0; font-variant-numeric:tabular-nums; }}
.chip .cf em {{ font-style:normal; font-weight:800; }}
.chip.d {{ border-color:rgba(255,216,77,.6); }} .chip.d b, .chip.d .cf em {{ color:{Y}; }}
.chip.l {{ border-color:rgba(255,138,61,.6); }} .chip.l b, .chip.l .cf em {{ color:{ORANGE}; }}

.stamp {{ position:absolute; left:0; right:0; top:760px; text-align:center; font-weight:800; font-size:260px; line-height:1; letter-spacing:.02em; text-shadow:0 12px 50px rgba(0,0,0,.7); }}
.stamp.no {{ color:{RED}; }} .stamp.ok {{ color:{GREEN}; }}
.why {{ position:absolute; left:40px; right:40px; bottom:120px; display:grid; gap:18px; padding:26px 28px; border-radius:22px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.1); }}
.eqn {{ display:flex; align-items:flex-end; gap:12px; }}
.lab {{ {MONO} font-size:24px; letter-spacing:.14em; width:120px; padding-bottom:30px; }}
.parts {{ display:grid; justify-items:center; }}
.parts b {{ font-weight:800; font-size:66px; line-height:1; font-variant-numeric:tabular-nums; }}
.parts i {{ font-style:normal; {MONO} font-size:16px; letter-spacing:.1em; color:#AEB8C6; }}
.parts.tot b {{ font-size:84px; }}
.op {{ font-weight:800; font-size:52px; color:#8b96a6; padding-bottom:24px; }}
.need {{ font-family:"Inter", sans-serif; font-weight:700; font-size:40px; color:#dfe5ec; padding-bottom:22px; }}
.need b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:66px; }}
.marg {{ justify-self:start; font-weight:800; font-size:58px; color:{RED}; }}
.arcs {{ font-family:"Inter", sans-serif; font-weight:700; font-size:34px; line-height:1.3; color:#dfe5ec; }}
.arcs b {{ font-weight:800; }}
.y {{ color:{Y}; }} .cy {{ color:{CYAN}; }} .o {{ color:{ORANGE}; }}
.lchip {{ position:absolute; left:50%; top:398px; transform:translateX(-50%); display:inline-flex; align-items:center; gap:12px; padding:10px 20px; border-radius:12px;
          background:rgba(6,10,18,.82); {MONO} font-size:24px; letter-spacing:.12em; color:{ORANGE}; white-space:nowrap; }}
.lchip i {{ width:12px; height:12px; border-radius:50%; background:{ORANGE}; }}

.endc {{ position:absolute; left:40px; right:40px; top:150px; display:grid; gap:26px; padding:34px 34px 30px; border-radius:26px; background:rgba(6,10,18,.88); border:1px solid rgba(255,255,255,.1); }}
.eh {{ font-family:"Inter", sans-serif; font-weight:800; font-size:54px; line-height:1.12; letter-spacing:-.02em; }}
.eh b {{ color:{RED}; }}
.vtab {{ display:grid; gap:4px; }}
.vr {{ display:grid; grid-template-columns:1fr auto 44px auto; align-items:baseline; gap:12px; padding:12px 0; border-top:1px solid rgba(255,255,255,.09); }}
.vn {{ font-weight:700; font-size:40px; color:#dfe5ec; }}
.va {{ font-weight:700; font-size:40px; color:#8b96a6; font-variant-numeric:tabular-nums; }}
.arr {{ font-weight:800; font-size:36px; color:#8b96a6; text-align:center; }}
.vb {{ font-weight:800; font-size:48px; color:{GREEN}; font-variant-numeric:tabular-nums; min-width:200px; text-align:right; }}
.ek {{ font-family:"Inter", sans-serif; font-weight:800; font-size:38px; line-height:1.25; color:{Y}; }}
.arcl {{ position:absolute; left:0; right:0; text-align:center; font-family:"Inter", sans-serif; font-weight:800; font-size:30px; text-shadow:0 3px 14px rgba(0,0,0,.9); }}
.arce {{ position:absolute; top:1608px; {MONO} font-size:20px; letter-spacing:.12em; color:#cfd6e0; }}
.arcs2 {{ position:absolute; left:0; right:0; top:1700px; text-align:center; {MONO} font-size:19px; letter-spacing:.12em; color:#8b96a6; }}
.cap {{ position:absolute; left:52px; right:40px; }}
.cap .cl {{ display:block; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:86px; line-height:.96; text-transform:uppercase; color:#fff;
            text-shadow:0 6px 28px rgba(0,0,0,.8), 0 2px 4px rgba(0,0,0,.7); }}
.cap .cw {{ display:inline-block; }}
.cap .cw.acc {{ color:{HOT}; }}
.phys {{ position:absolute; left:60px; right:60px; top:1660px; text-align:center; font-family:"Inter", sans-serif; font-weight:700; font-size:30px; line-height:1.3; color:#dfe5ec; text-shadow:0 3px 14px rgba(0,0,0,.9); }}
.alt {{ font-family:"Inter", sans-serif; font-weight:700; font-size:34px; color:#dfe5ec; }}
.alt b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:44px; }}
.g {{ color:{GREEN}; }}
.vr.na .vb {{ color:#8b96a6; font-size:40px; }}
.src {{ font-family:"Inter", sans-serif; font-weight:700; font-size:22px; line-height:1.4; color:#8b96a6; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "Can he throw him out from here?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, shots {S}; {kcap} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
