"""'Look at the clock': why a stolen base isn't just the catcher's fault (1080x1920, voiceover + sound effects).

    python3 tools/vo.py && python3 tools/assemble.py   # scratch voiceover (local TTS) + line timing
    python3 tools/sfx.py                               # crowd bed, glove pop, stopwatch tick
    python3 build.py                                   # index.html + assets/mix.wav (+ mix-novo.wav)
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/look-at-the-clock.mp4 --video-bitrate 16M

Shots follow the voiceover (assets/vo/timing.json); the 3D play (assets/field.js) is computed from the
script's numbers: time to plate 1.4 s or 1.2 s, pop time 1.9 s, so the ball reaches second at 3.30 s or 3.10 s.
"""
import json, os, re, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

TM = json.load(open(os.path.join(HERE, "assets", "vo", "timing.json")))
L = [(x["t0"], x["t1"], x["text"]) for x in TM["lines"]]
WORDS = [x["words"] for x in TM["lines"]]
IDX = {x["id"]: k for k, x in enumerate(TM["lines"])}
LN = lambda lid: L[IDX[lid]]
def W(lid, word, end=False, nth=0):
    """Video time a spoken word starts (or ends) in line `lid` (word as spoken, punctuation ignored)."""
    hits = [w for w in WORDS[IDX[lid]] if w["w"].strip(".,!?").lower() == word.lower()]
    return hits[nth]["t1" if end else "t0"]
D = TM["duration"]
Y, CYAN, WHITE = "#FFD84D", "#56D1FF", "#F4F6F8"

# the runner model in field.js (0.05 s reaction, 30 ft/s top speed, 0.62 s time constant, 78 ft to go)
def run_dist(p, r=0.05, v=30, tau=0.62): return 0 if p <= r else v * ((p - r) - tau * (1 - np.exp(-(p - r) / tau)))
RUN = next(p for p in np.arange(0, 6, 0.0005) if run_dist(p) >= 78)

# shot boundaries, keyed to the voiceover lines
# the timers land on the spoken numbers: 1.40 as "seconds" ends, 1.90 as "pop time" ends, 1.20 as "seconds" ends
S = dict(s1b=3.0, s2=LN("deliver")[0] - 0.3, go2=LN("deliver")[0] + 0.7, s3=LN("numbers")[0] - 0.25,
         go3a=W("numbers", "seconds", end=True) - 1.4 / 0.5, go3b=W("numbers", "time", end=True) - 1.9 / 0.5,
         s4=LN("total")[0] - 0.15, s4b=LN("lead")[0] - 0.25, s5=LN("compare")[0] - 0.2)
S["run"] = round(float(RUN), 4)
S["go4b"] = float(W("runner", "seconds", end=True) - RUN)      # the runner reaches second as "3.2 seconds" is said
S["go5"] = W("compare", "seconds", end=True) - 1.2 / 0.42
S["s6"] = round(S["go5"] + 3.10 / 0.42 + 0.12, 3)      # freeze just after the ball reaches second
S["s7"] = LN("next")[0] - 0.15
S = {k: round(v, 3) for k, v in S.items()}
c = Comp(D, 30)

c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")

# ----------------------------------------------------------------- timers (digits are written by field.js from the play clock)
c.clip("t-del", S["s2"] + 0.3, S["s4"], f'<div class="timer" id="tbox-del"><span class="tl">Time to plate</span><b><span id="tm-del">0.00</span><small>s</small></b></div>', cls="layer", style="z-index:10")
c.ft("#tbox-del", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["s2"] + 0.3)
c.clip("split", S["s3"], S["s4"], f'''<div class="divider"></div>
  <div class="timer bot" id="tbox-pop"><span class="tl">Pop time</span><b><span id="tm-pop">0.00</span><small>s</small></b></div>
  <div class="panel-tag top">Pitcher's delivery</div><div class="panel-tag bot">Catcher's throw</div>''', cls="layer", style="z-index:10")
c.ft(".divider", o(scaleX=0), o(scaleX=1, duration=0.35, ease="power3.out"), S["s3"])
c.ft("#tbox-pop", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["s3"] + 0.2)

# ----------------------------------------------------------------- 1.40 + 1.90 = 3.30
eq_t = [S["s4"] + 0.1, S["s4"] + 0.35, W("total", "three"), W("total", "accounting")]
c.clip("eq", S["s4"], S["s4b"], f'''<div class="eq">
  <div class="eq-row"><span class="eq-n" id="eq1"><i>Delivery</i>1.40</span><span class="eq-op" id="eqp">+</span><span class="eq-n" id="eq2"><i>Pop time</i>1.90</span></div>
  <div class="eq-total" id="eq3"><span>=</span>3.30<small>s</small></div>
  <div class="eq-more" id="eq4">+ the runner's jump &nbsp;+ the tag</div></div>''', cls="layer", style="z-index:10")
for i, (sel, t) in enumerate(zip(["#eq1", "#eqp, #eq2", "#eq3", "#eq4"], eq_t)):
    c.ft(sel, o(opacity=0, y=24, scale=1.05), o(opacity=1, y=0, scale=1, duration=0.32, ease="power3.out"), t)

# ----------------------------------------------------------------- the runner's side: 90 ft, a 10-12 ft lead, 78-80 ft to go, ~3.2 s
lead_t = [W("lead", "ninety-foot"), W("lead", "ten"), W("lead", "seventy-eight")]
run_t0 = LN("runner")[0]
c.clip("leadc", S["s4b"], run_t0 + 0.1, f'''<div class="dist" id="dist">
  <div class="dr" id="dr1"><b>90 FT</b><span>basepath</span></div>
  <div class="dr" id="dr2"><b><i>−</i>10–12 FT</b><span>lead</span></div>
  <div class="dr tot" id="dr3"><b><i>=</i>78–80 FT</b><span>left to cover</span></div></div>''', cls="layer", style="z-index:10")
c.ft("#dist", o(opacity=0), o(opacity=1, duration=0.25), lead_t[0] - 0.12)
for sel, t in zip(["#dr1", "#dr2", "#dr3"], lead_t):
    c.ft(sel, o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.3, ease="power3.out"), t)
c.to("#dist", o(opacity=0, y=-20, duration=0.25, ease="power2.in"), run_t0 - 0.15)
safe_t, out_t = W("runner", "safe"), W("runner", "out")
c.clip("runc", run_t0 - 0.05, S["s5"], f'''<div class="timer" id="tbox-run"><span class="tl">Runner to second</span><b class="cy"><span id="tm-run">0.00</span><small>s</small></b></div>
  <div class="verdicts"><div class="vd ok" id="vd1"><span>Ball at 3.30</span><b>SAFE</b></div><div class="vd no" id="vd2"><span>Ball at 3.10</span><b>OUT</b></div></div>''', cls="layer", style="z-index:10")
c.ft("#tbox-run", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), run_t0 - 0.05)
c.ft("#vd1", o(opacity=0, y=16, scale=0.9), o(opacity=1, y=0, scale=1, duration=0.3, ease="back.out(2)"), safe_t)
c.ft("#vd2", o(opacity=0, y=16, scale=0.9), o(opacity=1, y=0, scale=1, duration=0.3, ease="back.out(2)"), out_t)

# ----------------------------------------------------------------- 1.2 s delivery: the comparison
cmp_t = LN("compare")[0] + 1.2
c.clip("cmp", S["s5"], S["s6"], f'''<div class="timer" id="tbox-b"><span class="tl">Time to plate</span><b><span id="tm-b-del">0.00</span><small>s</small></b></div>
  <div class="bars" id="bars">
    <div class="bar-row"><span class="bl">1.4 s delivery</span><div class="track"><i class="fill a" id="fa"></i></div><span class="bv">3.30</span></div>
    <div class="bar-row"><span class="bl">1.2 s delivery</span><div class="track"><i class="fill b" id="fb"></i></div><span class="bv y">3.10</span></div>
    <div class="delta" id="delta">−0.20 s <span>for the runner</span></div></div>''', cls="layer", style="z-index:10")
c.ft("#tbox-b", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["s5"] + 0.2)
c.ft("#bars", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), cmp_t)
c.ft("#fa", o(scaleX=0), o(scaleX=1, duration=0.7, ease="power2.out"), cmp_t + 0.1)
c.ft("#fb", o(scaleX=0), o(scaleX=3.10 / 3.30, duration=0.7, ease="power2.out"), cmp_t + 0.25)
c.ft("#delta", o(opacity=0, scale=0.85), o(opacity=1, scale=1, duration=0.35, ease="back.out(2)"), W("tenths", "two-tenths"))

# ----------------------------------------------------------------- freeze: the race
race_t = LN("race")[0] - 0.2
c.clip("frz", S["s6"], S["s7"], f'''<div class="frz" id="frz"><i></i>Ball at second · 3.10 s</div>
  <div class="race" id="race">
    <div class="lane"><span class="ln">Pitcher's delivery</span><div class="lt"><i class="seg del" id="r1"></i></div><span class="lv">1.20</span></div>
    <div class="lane"><span class="ln">Catcher's throw</span><div class="lt"><i class="seg pad" style="width:{1.2 / 3.4 * 100:.2f}%"></i><i class="seg thr" id="r2"></i></div><span class="lv">1.90</span></div>
    <div class="lane"><span class="ln">Runner, jump to bag</span><div class="lt"><i class="seg run" id="r3"></i></div><span class="lv">{RUN:.2f}</span></div>
    <div class="finish" style="left:calc(var(--lane0) + {3.10 / 3.4:.4f} * var(--lanew))"></div></div>''', cls="layer", style="z-index:10")
c.ft("#frz", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), S["s6"] + 0.05)
c.ft("#race", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), race_t)
c.ft("#r1", o(scaleX=0), o(scaleX=1, duration=0.55, ease="power2.inOut"), W("race", "delivery"))
c.ft("#r2", o(scaleX=0), o(scaleX=1, duration=0.7, ease="power2.inOut"), W("race", "throw"))
c.ft("#r3", o(scaleX=0), o(scaleX=1, duration=0.9, ease="power2.inOut"), W("race", "jump"))

# ----------------------------------------------------------------- the end: look at the clock
end_t = LN("clock")[0]
c.clip("end", end_t - 0.1, D, f'''<div class="endc" id="endc"><div class="watch"><span class="wl">Stolen base</span><b>3.10<small>s</small></b></div>
  <div class="end-t"><span id="ew0">Look</span> <span id="ew1">at</span> <span id="ew2">the</span> <em id="ew3">clock.</em></div></div>''', cls="layer", style="z-index:12")
for k, w in enumerate(WORDS[IDX["clock"]]):                    # the last line, word by word as it's said
    c.ft(f"#ew{k}", o(opacity=0, y=18), o(opacity=1, y=0, duration=0.16, ease="power2.out"), w["t0"])
c.ft("#endc", o(opacity=0, scale=1.08), o(opacity=1, scale=1, duration=0.35, ease="power3.out"), end_t - 0.1)

# ----------------------------------------------------------------- captions: the script word for word, each word lit while it's spoken
# A caption word covers one spoken word, except numbers, which the voice reads out ("1.9-second" = one point nine second).
def span_of(tok):
    m = re.match(r"^(\d)\.(\d)(-second)?", tok)
    if m: return 3 + (1 if m.group(3) else 0)                 # 1.9-second = one point nine second
    m = re.match(r"^\d+–\d+(-foot)?", tok)
    if m: return 3 + (1 if m.group(1) else 0)                 # 10–12-foot = ten to twelve foot, 78–80 = seventy-eight to eighty
    if tok.lower().startswith("baserunner"): return 2         # spoken as "base runner"
    return tok.count("—") + 1                                 # jump—which = jump, which
def phrases(toks):
    out, cur = [], []
    for t in toks:
        cur.append(t)
        if t[-1] in ",.?" or len(cur) >= 4 or (len(cur) >= 3 and len(" ".join(cur)) > 17):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out
k = 0
for li, (t0, t1, text) in enumerate(L):
    if li == IDX["clock"]: continue                           # the end card says it, word by word
    toks = text.split()
    assert sum(span_of(t) for t in toks) == len(WORDS[li]), f"caption/voice mismatch on line {li}"
    times, j = [], 0
    for t in toks:
        n = span_of(t); times.append((WORDS[li][j]["t0"], WORDS[li][j + n - 1]["t1"])); j += n
    groups, i = phrases(toks), 0
    for gi, g in enumerate(groups):
        gt = times[i:i + len(g)]
        start = gt[0][0] - 0.06
        nxt = times[i + len(g)][0] - 0.06 if i + len(g) < len(times) else min(t1 + 0.35, L[li + 1][0] - 0.06 if li + 1 < len(L) else D)
        cid = f"cap{k}"; k += 1
        words_html = " ".join(f'<span class="cw" id="{cid}w{n}">{esc(w.rstrip(","))}</span>' for n, w in enumerate(g))
        c.clip(cid, start, nxt, f'<div class="cap"><span class="cl" id="{cid}-t">{words_html}</span></div>', cls="layer", style="z-index:20")
        c.ft(f"#{cid}-t", o(opacity=0, y=10, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.1, ease="power2.out"), start)
        for n, (a_, b_) in enumerate(gt):
            c.set(f"#{cid}w{n}", o(color=Y), a_)
            c.set(f"#{cid}w{n}", o(color="#ffffff"), max(b_, a_ + 0.12))
        i += len(g)

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0): c.cue(n, t, db)
for k_ in ["s1b", "s2", "s3", "s4", "s4b", "s5", "s7"]: cue("whoosh", S[k_], -10)
for t in lead_t: cue("hit", t, -13)
cue("glove", S["go4b"] + 1.4, -6); cue("glove", S["go4b"] + 3.30, -2)          # basepath shot: catch, then the late throw
for t in np.arange(S["go4b"], S["go4b"] + RUN, 0.25): cue("tick", float(t), -15)
cue("popup", safe_t, -9); cue("popup", out_t, -9)
cue("impact", 0.0, -10)
cue("glove", S["go2"] + 1.4 / 0.5, -2)                         # center-field shot: the catch
cue("glove", S["go3a"] + 1.4 / 0.5, -6)                        # split, top panel
cue("glove", S["go5"] + 1.2 / 0.42, -4)                        # 1.2 s delivery: the catch
cue("glove", S["go5"] + 3.10 / 0.42, 0); cue("impact", S["s6"], -6); cue("riser-m", S["s6"], -8)   # ball beats the runner; freeze
for t0, t1 in [(S["go2"], S["go2"] + 1.4 / 0.5), (S["go3a"], S["go3a"] + 1.4 / 0.5), (S["go3b"], S["go3b"] + 1.9 / 0.5), (S["go5"], S["go5"] + 1.2 / 0.42)]:
    for t in np.arange(t0, t1, 0.25): cue("tick", float(t), -14)
for t in eq_t: cue("hit", t, -12)
cue("popup", W("tenths", "two-tenths"), -8); cue("popup", race_t, -10)
cue("hit", end_t - 0.1, -5)
for i in range(4): cue("tick", end_t + 0.35 + i * 0.25, -8)

LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "glove": -2.0, "tick": -6.0, "popup": -8.0, "riser-m": -7.0}

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav"))[:n]
    fx[: len(crowd)] += crowd * 10 ** (-27 / 20)
    vo = read(os.path.join(HERE, "assets", "vo", "vo.wav"))[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo           # effects sit under the voice
    def wr(p, x):
        w = wave.open(p, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, fxp = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wr(pre, full); wr(fxp, fx * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    f = master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=fxp)
    os.remove(pre); os.remove(fxp)
    return m, f

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
LANE0, LANEW = 330, 560
CSS = "\n".join([F("Barlow Condensed", 600, "BarlowCondensed-600.woff2"), F("Barlow Condensed", 700, "BarlowCondensed-700.woff2"),
                 F("Barlow Condensed", 800, "BarlowCondensed-800.woff2"), F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#05080d; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#05080d; font-family:"Barlow Condensed", sans-serif; color:{WHITE}; }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#field-gl {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.shade-top {{ position:absolute; left:0; right:0; top:0; height:420px; background:linear-gradient(180deg, rgba(3,6,12,.55), rgba(3,6,12,0)); }}
.shade-bot {{ position:absolute; left:0; right:0; bottom:0; height:760px; background:linear-gradient(0deg, rgba(3,6,12,.72) 0%, rgba(3,6,12,.4) 45%, rgba(3,6,12,0) 100%); }}

.timer {{ position:absolute; left:50%; top:200px; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; padding:14px 34px 10px;
          border-radius:18px; background:rgba(6,10,18,.8); border:1px solid rgba(255,255,255,.12); box-shadow:0 18px 40px rgba(0,0,0,.35); }}
.timer .tl {{ font-family:"Plex Mono", monospace; font-weight:500; font-size:22px; letter-spacing:.16em; text-transform:uppercase; color:#AEB8C6; }}
.timer b {{ font-weight:800; font-size:104px; line-height:1; letter-spacing:.01em; color:{Y}; font-variant-numeric:tabular-nums; }}
.timer b small {{ font-size:48px; margin-left:6px; color:#d9c46a; }}
.timer.bot {{ top:1000px; }}
.timer.bot b {{ color:{WHITE}; }}
.divider {{ position:absolute; left:0; right:0; top:957px; height:6px; background:#05080d; box-shadow:0 0 0 1px rgba(255,255,255,.08); }}
.panel-tag {{ position:absolute; left:36px; font-family:"Plex Mono", monospace; font-weight:500; font-size:22px; letter-spacing:.14em; text-transform:uppercase;
              padding:8px 14px; border-radius:8px; background:rgba(6,10,18,.7); color:#cfd6e0; }}
.panel-tag.top {{ top:880px; }} .panel-tag.bot {{ top:1840px; }}

.dist {{ position:absolute; left:60px; right:60px; top:190px; display:grid; gap:10px; padding:22px 30px; border-radius:20px; background:rgba(6,10,18,.8); border:1px solid rgba(255,255,255,.1); }}
.dr {{ display:flex; align-items:baseline; justify-content:space-between; gap:20px; }}
.dr b {{ font-weight:800; font-size:84px; line-height:1; color:{WHITE}; }}
.dr b i {{ font-style:normal; color:#AEB8C6; margin-right:16px; }}
.dr span {{ font-family:"Plex Mono", monospace; font-weight:500; font-size:24px; letter-spacing:.14em; text-transform:uppercase; color:#AEB8C6; }}
.dr.tot b {{ color:{Y}; }}
#dr2 b {{ color:{CYAN}; }}
.timer b.cy {{ color:{CYAN}; }}
.verdicts {{ position:absolute; left:0; right:0; top:390px; display:flex; justify-content:center; gap:18px; }}
.vd {{ display:grid; justify-items:center; padding:12px 26px 10px; border-radius:16px; background:rgba(6,10,18,.82); border:2px solid; }}
.vd span {{ font-family:"Plex Mono", monospace; font-weight:500; font-size:20px; letter-spacing:.12em; text-transform:uppercase; color:#AEB8C6; }}
.vd b {{ font-weight:800; font-size:64px; line-height:1; }}
.vd.ok {{ border-color:rgba(61,214,140,.7); }} .vd.ok b {{ color:#3DD68C; }}
.vd.no {{ border-color:rgba(255,97,97,.7); }} .vd.no b {{ color:#FF6161; }}
.eq {{ position:absolute; left:40px; right:40px; top:560px; display:grid; justify-items:center; gap:18px; }}
.eq-row {{ display:flex; align-items:flex-end; gap:28px; }}
.eq-n {{ display:grid; justify-items:center; font-weight:800; font-size:150px; line-height:.9; color:{WHITE}; padding:22px 30px 18px; border-radius:22px; background:rgba(6,10,18,.78); }}
.eq-n i {{ font-style:normal; font-family:"Plex Mono", monospace; font-weight:500; font-size:22px; letter-spacing:.16em; text-transform:uppercase; color:#AEB8C6; margin-bottom:6px; }}
.eq-op {{ font-weight:800; font-size:110px; line-height:1.3; color:#AEB8C6; }}
.eq-total {{ font-weight:800; font-size:220px; line-height:.9; color:{Y}; text-shadow:0 10px 40px rgba(0,0,0,.6); }}
.eq-total span {{ color:#AEB8C6; font-size:130px; margin-right:24px; }}
.eq-total small {{ font-size:90px; margin-left:8px; }}
.eq-more {{ font-family:"Inter", sans-serif; font-weight:800; font-size:40px; color:{CYAN}; padding:10px 22px; border-radius:12px; background:rgba(6,10,18,.75); }}

.bars {{ position:absolute; left:60px; right:60px; top:420px; display:grid; gap:14px; padding:22px 26px; border-radius:20px; background:rgba(6,10,18,.8); border:1px solid rgba(255,255,255,.1); }}
.bar-row {{ display:grid; grid-template-columns:230px 1fr 110px; align-items:center; gap:18px; }}
.bl {{ font-weight:700; font-size:36px; color:#cfd6e0; }}
.track {{ height:26px; border-radius:13px; background:rgba(255,255,255,.08); overflow:hidden; }}
.fill {{ display:block; height:100%; border-radius:13px; transform-origin:0 50%; }}
.fill.a {{ background:#8b96a6; }} .fill.b {{ background:{Y}; }}
.bv {{ font-weight:800; font-size:48px; text-align:right; font-variant-numeric:tabular-nums; }}
.bv.y {{ color:{Y}; }}
.delta {{ justify-self:end; font-weight:800; font-size:56px; color:{CYAN}; }}
.delta span {{ font-family:"Inter", sans-serif; font-weight:700; font-size:30px; color:#cfd6e0; margin-left:8px; }}

.frz {{ position:absolute; left:50%; top:200px; transform:translateX(-50%); display:inline-flex; align-items:center; gap:12px; padding:12px 22px; border-radius:12px;
        background:rgba(6,10,18,.82); font-family:"Plex Mono", monospace; font-weight:500; font-size:26px; letter-spacing:.12em; text-transform:uppercase; color:{Y}; white-space:nowrap; }}
.frz i {{ width:12px; height:12px; border-radius:2px; background:{Y}; }}
.race {{ --lane0:{LANE0}px; --lanew:{LANEW}px; position:absolute; left:40px; right:40px; top:300px; display:grid; gap:16px; padding:24px 26px 26px; border-radius:20px;
         background:rgba(6,10,18,.82); border:1px solid rgba(255,255,255,.1); }}
.lane {{ display:grid; grid-template-columns:{LANE0 - 66}px {LANEW}px 1fr; align-items:center; gap:0 18px; }}
.ln {{ font-weight:700; font-size:36px; color:#dfe5ec; white-space:nowrap; }}
.lt {{ height:28px; border-radius:14px; background:rgba(255,255,255,.07); display:flex; overflow:hidden; }}
.seg {{ display:block; height:100%; transform-origin:0 50%; }}
.seg.del {{ width:{1.2 / 3.4 * 100:.2f}%; background:{Y}; border-radius:14px 0 0 14px; }}
.seg.pad {{ background:transparent; }}
.seg.thr {{ width:{1.9 / 3.4 * 100:.2f}%; background:#fff3c2; }}
.seg.run {{ width:{RUN / 3.4 * 100:.2f}%; background:{CYAN}; border-radius:14px; }}
.lv {{ font-weight:800; font-size:40px; font-variant-numeric:tabular-nums; text-align:right; }}
.finish {{ position:absolute; top:16px; bottom:16px; width:3px; margin-left:26px; background:{Y}; box-shadow:0 0 12px {Y}; }}

.endc {{ position:absolute; left:0; right:0; top:620px; display:grid; justify-items:center; gap:26px; }}
.watch {{ display:grid; justify-items:center; padding:20px 46px 14px; border-radius:26px; background:rgba(6,10,18,.85); border:2px solid rgba(255,216,77,.45); }}
.watch .wl {{ font-family:"Plex Mono", monospace; font-weight:500; font-size:24px; letter-spacing:.16em; text-transform:uppercase; color:#AEB8C6; }}
.watch b {{ font-weight:800; font-size:200px; line-height:.95; color:{Y}; font-variant-numeric:tabular-nums; }}
.watch b small {{ font-size:84px; margin-left:8px; }}
.end-t {{ font-family:"Inter", sans-serif; font-weight:800; font-size:92px; letter-spacing:-.03em; color:{WHITE}; text-shadow:0 10px 40px rgba(0,0,0,.6); }}
.end-t em {{ font-style:normal; color:{Y}; }}

.cap {{ position:absolute; left:40px; right:40px; top:1380px; text-align:center; }}
.cap .cl {{ display:inline-block; font-weight:800; font-size:84px; line-height:1.0; letter-spacing:.005em; text-transform:uppercase; color:#fff;
             -webkit-text-stroke:12px rgba(0,0,0,.85); paint-order:stroke fill; text-shadow:0 6px 24px rgba(0,0,0,.6); }}
.cap .cw {{ color:#ffffff; }}
"""])

HEAD = '''<script type="importmap">{"imports":{"three":"./assets/vendor/three.module.min.js"}}</script>'''
if __name__ == "__main__":
    cc = {"duration": D, "shots": S}
    h = c.page(CSS, "Look at the clock", script=True).replace('<script src="assets/gsap.min.js"></script>',
        '<script src="assets/vendor/gsap.min.js"></script>\n    ' + HEAD + f'\n    <script>window.__CC = {json.dumps(cc)};</script>')
    h = h.replace("</body>", '  <script type="module" src="./assets/field.js"></script>\n  </body>')
    h = h.replace('src="assets/mix.wav"', 'src="assets/mix.wav"')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m, f = mixdown()
    print(f"index.html: {D}s, shots {S}; {len(c.cues)} sounds; with voice {m['lufs']} LUFS / {m['true_peak']} dBTP; no voice {f['lufs']} LUFS")
