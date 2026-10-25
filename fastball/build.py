"""'100 MPH. Could you hit it?': what it takes to hit a 100 mph fastball (1080x1920, voiceover + sound effects).

    python3 tools/physics.py                                       # the pitch, the swing timing, the batted ball -> assets/play.json
    $HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # Kokoro voiceover (am_adam) + word timing
    python3 build.py                                               # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/fastball-100.mp4 --video-bitrate 16M

Every number on screen is read from assets/play.json, so labels, timers and the 3D motion agree.
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
TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: TM["lines"][IDX[lid]]
def W(lid, word, end=False, nth=0):
    hits = [w for w in LN(lid)["words"] if w["w"].strip(".,!?:").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE, HOT, MUTED = "#FFD84D", "#56D1FF", "#F4F6F8", "#FF6A3D", "#AEB8C6"
f2 = lambda x: f"{x:.2f}"

# ----------------------------------------------------------------- shots (video time) and play-time mapping (t = 0 at release)
S = dict(h1=0.75, h2=1.35, hRel=2.42, p0=LN("speed")["t0"] - 0.12)
S["pRel"] = W("speed", "ball") + 0.0                       # center-field view: the pitch leaves the hand on "ball"
S["p1"] = S["pRel"] + P["t_glove"] + 0.38
S["p2"] = LN("time")["t0"] - 0.1
S["p1r"] = 0.33 / (S["p2"] - S["p1"])                      # 1/8 speed, alongside the ball
S["p2Rate"] = 0.25
S["p2Rel"] = W("time", "four-tenths") - P["t_front"] / S["p2Rate"]   # the 1/4-speed replay reaches the plate on "four-tenths"
S["d0"] = LN("catch")["t0"] - 0.12
S["dRel"] = W("catch", "reaches") - P["t_front"]
S["d1"] = LN("steps")["t0"] - 0.08
S["d1v"] = [S["d1"], W("steps", "decision"), W("steps", "swing"), W("steps", "there", end=True) - 0.2, LN("steps")["t1"] + 0.55]
S["d1t"] = [-0.06, P["recognize"], P["t_swing"], P["t_contact"], P["t_contact"] + 0.05]
S["s0"] = S["d1v"][-1]
S["sC"] = W("why", "so") - 0.05                             # slow-motion replay: contact just before "so difficult"
S["sF"] = LN("why")["t1"] + 0.55
S["e0"] = LN("end")["t0"] - 0.2
S["eC"] = W("end", "honest") + 0.05                         # real time: the crack on "honest"
S = {k: (round(v, 4) if not isinstance(v, list) else [round(x, 4) for x in v]) for k, v in S.items()}

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("spdc", S["h2"], D, '<div class="spd rt" id="spd">Real time</div>', cls="layer", style="z-index:30")

# ----------------------------------------------------------------- hook: a statement on frame one, then the question word by word
c.clip("hook0", 0, 0.44, """<div class="eyebrow"><i></i>The fastball</div>
  <div class="hk big"><span class="hl acc">100 MPH.</span><span class="hl">0.38 seconds.</span></div>""", cls="layer", style="z-index:12")
c.to(".hk.big", o(opacity=0, y=-30, filter="blur(10px)", duration=0.12, ease="power2.in"), 0.3)
qw = LN("q")["words"]                                       # you think you could hit a hundred mile per hour fastball?
HOOK = [("You", 0, 0), ("think", 1, 0), ("you", 2, 0), ("could", 3, 1), ("hit", 4, 1), ("a", 5, 1), ("100", 6, 2), ("MPH", 7, 2), ("fastball?", 10, 3)]
lines = {}
for k, (w, wi, ln) in enumerate(HOOK):
    lines.setdefault(ln, []).append(f'<span class="hw{" acc" if ln == 2 else ""}" id="hw{k}">{esc(w)}</span>')
c.clip("hook", 0.44, S["p0"] - 0.05, '<div class="eyebrow"><i></i>The fastball</div><div class="hk">' + "".join(f'<span class="hl">{" ".join(v)}</span>' for v in lines.values()) + "</div>", cls="layer", style="z-index:12")
for k, (w, wi, ln) in enumerate(HOOK):
    c.ft(f"#hw{k}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), qw[wi]["t0"] - 0.04)
c.ft("#hw8", o(scale=1), o(scale=1.1, duration=0.1, yoyo=True, repeat=1), qw[10]["t0"] + 0.1)
c.to("#hook .hk, #hook .eyebrow", o(opacity=0, y=-24, duration=0.14, ease="power2.in"), S["p0"] - 0.2)

# ----------------------------------------------------------------- captions: the voiceover, word by word (lines that aren't already on screen)
ACC = {"147", "feet", "four-tenths", "second", "catch", "wait", "decide", "swing", "difficult", "100-mile-per-hour"}
def span_of(tok):
    if tok == "147": return 4                               # a hundred and forty-seven
    if tok.startswith("100-mile-per-hour"): return 4        # hundred mile per hour
    return 1
def phrases(toks):
    out, cur = [], []
    for t in toks:
        cur.append(t)
        n = len(" ".join(cur))
        if (t[-1] in ",.?:" and n >= 10) or n > 24: out.append(cur); cur = []
    if cur: out.append(cur)
    return out
CAP_TOP = {"speed": 300, "time": 300, "catch": 300, "why": 300}
kcap = 0
for lid in ["speed", "time", "catch", "why"]:
    ln = LN(lid); words = ln["words"]; toks = ln["text"].split()
    spans = [span_of(t) for t in toks]                     # "147" and "100-mile-per-hour" are spoken as several words
    assert sum(spans) == len(words), f"caption/voice mismatch on {lid}: {sum(spans)} vs {len(words)}"
    times, j = [], 0
    for n in spans: times.append((words[j]["t0"], words[j + n - 1]["t1"])); j += n
    nxt = TM["lines"][IDX[lid] + 1]["t0"] if IDX[lid] + 1 < len(TM["lines"]) else D
    groups, i = phrases(toks), 0
    for g in groups:
        gt = times[i:i + len(g)]
        start = gt[0][0] - 0.06
        end = times[i + len(g)][0] - 0.06 if i + len(g) < len(times) else min(ln["t1"] + 0.4, nxt - 0.08)
        cid = f"cap{kcap}"; kcap += 1
        sp = []
        for n, w in enumerate(g):
            key = re.sub(r"[^\w'-]", "", w).lower()
            shown = w.replace("100-mile-per-hour", "100 MPH")
            sp.append(f'<span class="cw{" acc" if key in ACC else ""}" id="{cid}w{n}">{esc(shown.rstrip(",:") if n == len(g) - 1 else shown)}</span>')
        c.clip(cid, start, end, f'<div class="cap" style="top:{CAP_TOP[lid]}px"><span class="cl">{" ".join(sp)}</span></div>', cls="layer", style="z-index:20")
        for n, (a_, b_) in enumerate(gt):
            c.ft(f"#{cid}w{n}", o(opacity=0, y=34, filter="blur(10px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.15, ease="power3.out"), a_ - 0.04)
        i += len(g)

# ----------------------------------------------------------------- the speed, the distance, the time
v47 = W("speed", "forty-seven")
c.clip("fps", v47 - 0.1, S["p2"], f"""<div class="card mid" id="cfps"><b class="y">{P["v0_mph"]:.0f} MPH</b><i>=</i><b>{P["fps"]:.1f}</b><span>feet per second</span>
  <div class="sub">White lines: where a constant 100 mph ball would be every 0.1 s ({P["fps"] / 10:.1f} ft apart)</div></div>""", cls="layer", style="z-index:11")
c.ft("#cfps", o(opacity=0, y=30, scale=0.94), o(opacity=1, y=0, scale=1, duration=0.3, ease="back.out(1.8)"), v47 - 0.1)
vft = W("time", "four-tenths")
c.clip("dist", S["p2"] + 0.2, S["d0"], f"""<div class="dcard" id="dcard">
    <div class="drow" id="dr1"><span>Rubber to plate · constant 100 mph</span><b>60 FT 6 IN <i>→</i> {P["const_time"]:.2f} S</b></div>
    <div class="drow y" id="dr2"><span>Real pitch · released {P["extension"]:.1f} ft in front of the rubber, slows to {P["mph_front"]:.0f} mph</span><b>{P["release_dist"]:.1f} FT <i>→</i> {P["t_front"]:.2f} S</b></div>
    <div class="flt" id="flt">Flight <b id="tm-fl">0.00</b> s</div></div>""", cls="layer", style="z-index:11")
c.ft("#dcard", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["p2"] + 0.25)
c.ft("#dr1", o(opacity=0, x=-24), o(opacity=1, x=0, duration=0.28, ease="power3.out"), W("time", "mound"))
c.ft("#dr2", o(opacity=0, x=-24), o(opacity=1, x=0, duration=0.28, ease="power3.out"), vft + 0.35)

# ----------------------------------------------------------------- the hitter's clock: recognize, decide, swing
bar_html = f"""<div class="bar" id="bar">
    <div class="bl"><span>Release</span><span>Ball reaches the plate · {P["t_front"]:.2f} s</span></div>
    <div class="track"><i class="sg r" style="width:{P["recognize"] / P["t_front"] * 100:.2f}%"></i><i class="sg d" style="width:{(P["t_swing"] - P["recognize"]) / P["t_front"] * 100:.2f}%"></i><i class="sg s" style="width:{(P["t_contact"] - P["t_swing"]) / P["t_front"] * 100:.2f}%"></i>
      <b class="ph" id="bar-ph"></b></div>
    <div class="bk"><span class="r">Recognize</span><span class="d">Decide</span><span class="s">Swing ≈ {P["swing"]:.2f} s</span></div>
    <div class="bn" id="bn">The swing has to start by ≈ {P["t_swing"]:.2f} s, before the ball is even halfway... <b id="bar-t">0.00 s</b></div></div>"""
bar_html = bar_html.replace(", before the ball is even halfway...", "")
c.clip("barc", S["d0"] + 0.1, S["s0"], bar_html, cls="layer", style="z-index:11")
c.ft("#bar", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["d0"] + 0.15)
c.ft("#bn", o(opacity=0), o(opacity=1, duration=0.3), W("catch", "decide"))
BIG = [("Recognize.", W("steps", "recognize")), ("Decide.", W("steps", "decision")), ("Swing.", W("steps", "swing"))]
c.clip("big", S["d1"], S["s0"], '<div class="bigw">' + "".join(f'<span id="bw{k}">{w}</span>' for k, (w, t) in enumerate(BIG)) + "</div>", cls="layer", style="z-index:12")
for k, (w, t) in enumerate(BIG):
    c.ft(f"#bw{k}", o(opacity=0, x=-40, filter="blur(10px)"), o(opacity=1, x=0, filter="blur(0px)", duration=0.2, ease="power3.out"), t - 0.04)
    if k < 2: c.to(f"#bw{k}", o(opacity=0.32, duration=0.2), BIG[k + 1][1] - 0.05)

# ----------------------------------------------------------------- the freeze: how small the window is
c.clip("frz", S["sC"], S["sF"], f"""<div class="frzc" id="frzc"><i></i>Freeze · contact</div>
  <div class="card win" id="cwin"><b class="y">{P["inch_per_ms"]:.1f} IN</b><span>the ball still covers every millisecond at the plate ({P["mph_contact"]:.0f} mph)</span>
    <div class="sub">Swing 10 ms early or late and the ball is ≈ {P["inch_per_ms"] * 10:.0f} in from where the bat meets it.</div></div>""", cls="layer", style="z-index:11")
c.ft("#frzc", o(opacity=0, y=-12), o(opacity=1, y=0, duration=0.22), S["sC"] + 0.02)
c.ft("#cwin", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["sC"] + 0.35)

# ----------------------------------------------------------------- payoff
ew = LN("end")["words"]                                     # be honest. could you make contact?
c.clip("end", S["e0"], D, f"""<div class="endt"><div class="e1" id="e1">That's why <em>100 MPH</em> is elite.</div>
  <div class="e2">{" ".join(f'<span class="ew" id="ew{k}">{esc(w["w"].upper())}</span>' for k, w in enumerate(ew[2:]))}</div></div>""", cls="layer", style="z-index:12")
c.ft("#e1", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["e0"] + 0.05)
for k, w in enumerate(ew[2:]):
    c.ft(f"#ew{k}", o(opacity=0, y=46, filter="blur(12px)"), o(opacity=1, y=0, filter="blur(0px)", duration=0.18, ease="power3.out"), w["t0"] - 0.04)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0):
    if t is not None and 0 <= t < D: c.cue(n, t, db)
cue("impact", 0.0, -2); cue("whoosh", S["h1"], -6); cue("whoosh", S["h2"], -8)
for k, (w, wi, ln) in enumerate(HOOK): cue("tick", qw[wi]["t0"], -12)
for rel in [S["hRel"], S["pRel"], S["dRel"]]:
    cue("whoosh", rel + 0.12, -2)                           # the pitch
    cue("glove", rel + P["t_glove"], 0)
cue("impact", S["hRel"] + P["t_glove"], -6)
for k in ["p0", "p1", "p2", "d0", "d1", "s0", "e0"]: cue("whoosh", S[k], -12)
cue("whoosh", S["p2Rel"] + 0.5, -10); cue("glove", S["p2Rel"] + P["t_glove"] / S["p2Rate"], -6)
cue("popup", v47, -8); cue("popup", vft + 0.35, -9)
for k, (w, t) in enumerate(BIG): cue("hit", t, -7)
cue("impact", S["sC"], -5); cue("riser-m", S["sC"], -10); cue("hit", S["sC"] + 0.35, -8)
cue("whoosh", S["eC"] - 0.06, -4)                           # the swing, real time
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -2.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0, "riser-s": -7.0}

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
    for t, g in [(S["eC"], 0.9), (S["sC"], 0.35)]:            # the real crack, and a softer one under the replay's contact
        i = int(t * SR); j = min(n, i + len(cr)); fx[i:j] += cr[: j - i] * g
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav"))[:n]
    tt = np.arange(len(crowd)) / SR
    env = 1 + 1.6 * np.exp(-np.clip(tt - S["eC"], 0, None) / 1.2) * (tt > S["eC"])     # the crowd comes up on the contact
    fx[: len(crowd)] += crowd * env[:, None] * 10 ** (-27 / 20)
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo
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

.card {{ position:absolute; left:50px; right:50px; display:grid; grid-template-columns:auto auto 1fr; align-items:baseline; gap:6px 18px; padding:24px 30px;
         border-radius:22px; background:rgba(6,10,18,.84); border:1px solid rgba(255,255,255,.1); }}
.card.mid {{ top:1240px; }} .card.win {{ top:1220px; grid-template-columns:auto 1fr; }}
.card b {{ font-weight:800; font-size:96px; line-height:1; font-variant-numeric:tabular-nums; }}
.card i {{ font-style:normal; font-weight:800; font-size:64px; color:#8b96a6; }}
.card span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:30px; color:#dfe5ec; line-height:1.2; }}
.card .sub {{ grid-column:1 / -1; font-family:"Inter", sans-serif; font-weight:700; font-size:24px; color:{MUTED}; line-height:1.35; }}
.y {{ color:{Y}; }}

.dcard {{ position:absolute; left:44px; right:44px; top:1180px; display:grid; gap:18px; padding:24px 28px; border-radius:22px; background:rgba(6,10,18,.86); border:1px solid rgba(255,255,255,.1); }}
.drow {{ display:grid; gap:4px; }}
.drow span {{ {MONO} font-size:20px; letter-spacing:.1em; color:{MUTED}; line-height:1.4; }}
.drow b {{ font-weight:800; font-size:78px; line-height:1; color:{WHITE}; font-variant-numeric:tabular-nums; }}
.drow b i {{ font-style:normal; color:#8b96a6; margin:0 8px; }}
.drow.y b {{ color:{Y}; }}
.flt {{ font-family:"Inter", sans-serif; font-weight:700; font-size:30px; color:#cfd6e0; }}
.flt b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:48px; color:{Y}; font-variant-numeric:tabular-nums; }}

.bar {{ position:absolute; left:44px; right:44px; top:1300px; display:grid; gap:12px; padding:22px 26px; border-radius:22px; background:rgba(6,10,18,.84); border:1px solid rgba(255,255,255,.1); }}
.bl {{ display:flex; justify-content:space-between; {MONO} font-size:19px; letter-spacing:.1em; color:{MUTED}; }}
.track {{ position:relative; height:30px; border-radius:15px; background:rgba(255,255,255,.06); display:flex; overflow:visible; }}
.sg {{ display:block; height:100%; }}
.sg.r {{ background:{CYAN}; border-radius:15px 0 0 15px; opacity:.85; }} .sg.d {{ background:{HOT}; opacity:.85; }} .sg.s {{ background:#f4f6f8; opacity:.8; }}
.ph {{ position:absolute; top:-10px; bottom:-10px; width:5px; margin-left:-2px; background:{Y}; box-shadow:0 0 12px {Y}; border-radius:3px; left:0; }}
.bk {{ display:flex; gap:22px; font-family:"Inter", sans-serif; font-weight:800; font-size:28px; }}
.bk .r {{ color:{CYAN}; }} .bk .d {{ color:{HOT}; }} .bk .s {{ color:#f4f6f8; }}
.bn {{ font-family:"Inter", sans-serif; font-weight:700; font-size:28px; color:#dfe5ec; line-height:1.3; }}
.bn b {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:40px; color:{Y}; margin-left:10px; font-variant-numeric:tabular-nums; }}
.bigw {{ position:absolute; left:52px; top:560px; display:grid; gap:0; font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:150px; line-height:.92; text-transform:uppercase;
         text-shadow:0 6px 30px rgba(0,0,0,.75); }}
.bigw span:nth-child(1) {{ color:{CYAN}; }} .bigw span:nth-child(2) {{ color:{HOT}; }} .bigw span:nth-child(3) {{ color:#fff; }}

.frzc {{ position:absolute; left:50%; top:150px; transform:translateX(-50%); display:inline-flex; align-items:center; gap:12px; padding:10px 20px; border-radius:12px;
         background:rgba(6,10,18,.82); {MONO} font-size:24px; letter-spacing:.14em; color:{Y}; white-space:nowrap; }}
.frzc i {{ width:12px; height:12px; border-radius:2px; background:{Y}; }}

.endt {{ position:absolute; left:52px; right:40px; top:278px; display:grid; gap:24px; }}
.e1 {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:92px; line-height:.95; text-transform:uppercase; text-shadow:0 6px 30px rgba(0,0,0,.75); }}
.e1 em {{ font-style:normal; color:{HOT}; }}
.e2 {{ font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:132px; line-height:.92; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.75); }}
.ew {{ display:inline-block; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "100 MPH. Could you hit it?", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)}; window.__PLAY = {json.dumps(P)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m = mixdown()
    print(f"index.html: {D}s, shots {S}; {kcap} caption phrases; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
