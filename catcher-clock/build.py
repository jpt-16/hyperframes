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
D = TM["duration"]
Y, CYAN, WHITE = "#FFD84D", "#56D1FF", "#F4F6F8"

# the runner model in field.js (0.05 s reaction, 30 ft/s top speed, 0.62 s time constant, 78 ft to go)
def run_dist(p, r=0.05, v=30, tau=0.62): return 0 if p <= r else v * ((p - r) - tau * (1 - np.exp(-(p - r) / tau)))
RUN = next(p for p in np.arange(0, 6, 0.0005) if run_dist(p) >= 78)

# shot boundaries, keyed to the voiceover lines
S = dict(s1b=3.0, s2=L[2][0] - 0.3, go2=L[2][0] + 0.7, s3=L[3][0] - 0.25, go3a=L[3][0] + 0.15, go3b=L[3][0] + 3.45,
         s4=L[4][0] - 0.15, s5=L[5][0] - 0.2)
S["go5"] = S["s5"] + 0.6
S["s6"] = round(S["go5"] + 3.10 / 0.42 + 0.12, 3)      # freeze just after the ball reaches second
S["s7"] = L[9][0] - 0.15
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
eq_t = [S["s4"] + 0.15, S["s4"] + 0.55, S["s4"] + 0.95, L[4][0] + 1.1]
c.clip("eq", S["s4"], S["s5"], f'''<div class="eq">
  <div class="eq-row"><span class="eq-n" id="eq1"><i>Delivery</i>1.40</span><span class="eq-op" id="eqp">+</span><span class="eq-n" id="eq2"><i>Pop time</i>1.90</span></div>
  <div class="eq-total" id="eq3"><span>=</span>3.30<small>s</small></div>
  <div class="eq-more" id="eq4">+ the runner's jump &nbsp;+ the tag</div></div>''', cls="layer", style="z-index:10")
for i, (sel, t) in enumerate(zip(["#eq1", "#eqp, #eq2", "#eq3", "#eq4"], eq_t)):
    c.ft(sel, o(opacity=0, y=24, scale=1.05), o(opacity=1, y=0, scale=1, duration=0.32, ease="power3.out"), t)

# ----------------------------------------------------------------- 1.2 s delivery: the comparison
cmp_t = L[6][0] + 0.2
c.clip("cmp", S["s5"], S["s6"], f'''<div class="timer" id="tbox-b"><span class="tl">Time to plate</span><b><span id="tm-b-del">0.00</span><small>s</small></b></div>
  <div class="bars" id="bars">
    <div class="bar-row"><span class="bl">1.4 s delivery</span><div class="track"><i class="fill a" id="fa"></i></div><span class="bv">3.30</span></div>
    <div class="bar-row"><span class="bl">1.2 s delivery</span><div class="track"><i class="fill b" id="fb"></i></div><span class="bv y">3.10</span></div>
    <div class="delta" id="delta">−0.20 s <span>for the runner</span></div></div>''', cls="layer", style="z-index:10")
c.ft("#tbox-b", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["s5"] + 0.2)
c.ft("#bars", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), cmp_t)
c.ft("#fa", o(scaleX=0), o(scaleX=1, duration=0.7, ease="power2.out"), cmp_t + 0.1)
c.ft("#fb", o(scaleX=0), o(scaleX=3.10 / 3.30, duration=0.7, ease="power2.out"), cmp_t + 0.25)
c.ft("#delta", o(opacity=0, scale=0.85), o(opacity=1, scale=1, duration=0.35, ease="back.out(2)"), cmp_t + 1.0)
c.clip("note", S["s4"], S["s7"], '<div class="note">Illustrative timings</div>', cls="layer", style="z-index:10")

# ----------------------------------------------------------------- freeze: the race
race_t = L[8][0] + 0.1
c.clip("frz", S["s6"], S["s7"], f'''<div class="frz" id="frz"><i></i>Ball at second · 3.10 s</div>
  <div class="race" id="race">
    <div class="lane"><span class="ln">Pitcher's delivery</span><div class="lt"><i class="seg del" id="r1"></i></div><span class="lv">1.20</span></div>
    <div class="lane"><span class="ln">Catcher's throw</span><div class="lt"><i class="seg pad" style="width:{1.2 / 3.4 * 100:.2f}%"></i><i class="seg thr" id="r2"></i></div><span class="lv">1.90</span></div>
    <div class="lane"><span class="ln">Runner, jump to bag</span><div class="lt"><i class="seg run" id="r3"></i></div><span class="lv">{RUN:.2f}</span></div>
    <div class="finish" style="left:calc(var(--lane0) + {3.10 / 3.4:.4f} * var(--lanew))"></div></div>''', cls="layer", style="z-index:10")
c.ft("#frz", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), S["s6"] + 0.05)
c.ft("#race", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), race_t)
c.ft("#r1", o(scaleX=0), o(scaleX=1, duration=0.6, ease="power2.inOut"), race_t + 0.3)
c.ft("#r2", o(scaleX=0), o(scaleX=1, duration=0.8, ease="power2.inOut"), race_t + 0.9)
c.ft("#r3", o(scaleX=0), o(scaleX=1, duration=1.4, ease="power2.inOut"), race_t + 0.3)

# ----------------------------------------------------------------- the end: look at the clock
end_t = L[10][0]
c.clip("end", end_t - 0.1, D, f'''<div class="endc" id="endc"><div class="watch"><span class="wl">Stolen base</span><b>3.10<small>s</small></b></div>
  <div class="end-t">Look at the <em>clock.</em></div></div>''', cls="layer", style="z-index:12")
c.ft("#endc", o(opacity=0, scale=1.08), o(opacity=1, scale=1, duration=0.35, ease="power3.out"), end_t - 0.1)

# ----------------------------------------------------------------- captions: the script, in short phrases timed across each line
HL = re.compile(r"(\d\.\d(?:-second)?|two-tenths|clock)")
def chunks(text):
    words = text.split(); out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w[-1] in ",.?" or (len(cur) >= 3 and len(" ".join(cur)) > 18):
            out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out
cap_html, k = [], 0
for t0, t1, text in L:
    if text == "Look at the clock.": continue          # the end card says it
    parts = chunks(text); w = [len(p) + 3 for p in parts]; tot = sum(w); t = t0
    for p, wi in zip(parts, w):
        dt = (t1 - t0) * wi / tot
        cid = f"cap{k}"; k += 1
        html_ = HL.sub(r"<em>\1</em>", esc(p.rstrip(",")))
        c.clip(cid, t, min(t + dt, t1 + 0.05), f'<div class="cap"><span id="{cid}-t">{html_}</span></div>', cls="layer", style="z-index:20")
        c.ft(f"#{cid}-t", o(opacity=0, y=10, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.12, ease="power2.out"), t)
        t += dt

# ----------------------------------------------------------------- sound
def cue(n, t, db=0.0): c.cue(n, t, db)
for k_ in ["s1b", "s2", "s3", "s4", "s5", "s7"]: cue("whoosh", S[k_], -10)
cue("impact", 0.0, -10)
cue("glove", S["go2"] + 1.4 / 0.5, -2)                         # center-field shot: the catch
cue("glove", S["go3a"] + 1.4 / 0.5, -6)                        # split, top panel
cue("glove", S["go5"] + 1.2 / 0.42, -4)                        # 1.2 s delivery: the catch
cue("glove", S["go5"] + 3.10 / 0.42, 0); cue("impact", S["s6"], -6); cue("riser-m", S["s6"], -8)   # ball beats the runner; freeze
for t0, t1 in [(S["go2"], S["go2"] + 1.4 / 0.5), (S["go3a"], S["go3a"] + 1.4 / 0.5), (S["go3b"], S["go3b"] + 1.9 / 0.5), (S["go5"], S["go5"] + 1.2 / 0.42)]:
    for t in np.arange(t0, t1, 0.25): cue("tick", float(t), -14)
for t in eq_t: cue("hit", t, -12)
cue("popup", cmp_t + 1.0, -8); cue("popup", race_t, -10)
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
.note {{ position:absolute; left:0; right:0; top:1840px; text-align:center; font-family:"Plex Mono", monospace; font-weight:500; font-size:21px; letter-spacing:.12em; text-transform:uppercase; color:#95a0b0; }}

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
.cap span {{ display:inline-block; font-weight:800; font-size:84px; line-height:1.0; letter-spacing:.005em; text-transform:uppercase; color:#fff;
             -webkit-text-stroke:12px rgba(0,0,0,.85); paint-order:stroke fill; text-shadow:0 6px 24px rgba(0,0,0,.6); }}
.cap em {{ font-style:normal; color:{Y}; }}
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
