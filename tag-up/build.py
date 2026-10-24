"""'Can he throw him out from here?': a runner tagging up from third against a throw home (1080x1920, sound effects, no narration).

    python3 tools/physics.py     # the simulated play -> assets/play.json
    python3 build.py             # index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 render . -o renders/tag-up.mp4 --video-bitrate 16M

Every number on screen is read from assets/play.json, so the labels, timers and 3D motion always agree.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, master, ANCHOR
from audio import SR

P = json.load(open(os.path.join(HERE, "assets", "play.json")))
A, DR, LP, FL = P["assume"], P["direct"], P["loop"], P["flips"]
Y, CYAN, ORANGE, WHITE, RED, GREEN = "#FFD84D", "#56D1FF", "#FF8A3D", "#F4F6F8", "#FF5A5A", "#3DD68C"
GAP = A["r_dist"] - DR["runner_at_tag"]
f2 = lambda x: f"{x:.2f}"

# ----------------------------------------------------------------- shots: video time v, play time t (t = 0 at the catch)
S = dict(v1=1.35, catchV=2.8, v3=5.0, r3=0.75, v4=6.45, v5=8.3, t5=2.85, v6=9.5, t6=3.45, v7=10.9, v8=14.8, t8=3.4, v9=17.6)
S["t4"] = (S["v4"] - S["v3"]) * S["r3"]
S["r4"] = (S["t5"] - S["t4"]) / (S["v5"] - S["v4"])
S["r5"] = (S["t6"] - S["t5"]) / (S["v6"] - S["v5"])
S["r6"] = (DR["tag_t"] - S["t6"]) / (S["v7"] - S["v6"] - 0.15)       # lands on the tag, holds 0.15 s, freezes
S["r8"] = (LP["tag_t"] + 0.15 - S["t8"]) / (S["v9"] - S["v8"] - 0.3)
D = 23.8
S = {k: round(v, 4) for k, v in S.items()}

def vt(t):
    """Video time at which the direct-throw play reaches play time t (first appearance)."""
    if t <= 0: return S["catchV"] + t
    for v0, v1, t0, r in [(S["v3"], S["v4"], 0, S["r3"]), (S["v4"], S["v5"], S["t4"], S["r4"]), (S["v5"], S["v6"], S["t5"], S["r5"]), (S["v6"], S["v7"], S["t6"], S["r6"])]:
        if t <= t0 + (v1 - v0) * r + 1e-9: return v0 + (t - t0) / r
    return S["v7"]
def vt_loop(t): return S["v8"] + (t - S["t8"]) / S["r8"]

c = Comp(D, 30)
c.clip("fieldl", 0, D, '<canvas id="field-gl" width="1080" height="1920" data-layout-ignore></canvas>', cls="layer", style="z-index:1")
c.clip("shade", 0, D, '<div class="shade-top"></div><div class="shade-bot"></div>', cls="layer", style="z-index:2")
c.clip("simtag", 0, D, '<div class="simtag"><i></i>Simulation · not MLB tracking data</div>', cls="layer", style="z-index:30")
c.ft(".simtag", o(opacity=0), o(opacity=1, duration=0.3), 0.05)

# ----------------------------------------------------------------- hook
c.clip("hook", 0, S["catchV"] - 0.05, '<div class="hook" id="hook"><span id="h1">Can an outfielder</span> <span id="h2">throw him out</span> <em id="h3">from here?</em></div>', cls="layer", style="z-index:12")
for sel, t in [("#h1", 0.12), ("#h2", 0.42), ("#h3", 0.85)]:
    c.ft(sel, o(opacity=0, y=26), o(opacity=1, y=0, duration=0.3, ease="power3.out"), t)

# ----------------------------------------------------------------- freeze at the catch: the distance
cv = S["catchV"]; dist_dur = S["v3"] - cv
c.clip("dist", cv, S["v3"] + 0.05, f'''<div class="frz" id="frz1"><i></i>Freeze · the catch</div>
  <div class="dcard" id="dcard">
    <div class="drow" id="d1"><span>Caught</span><b>{P["assume"]["catch_dist"]:.0f} FT<small> from home</small></b></div>
    <div class="drow" id="d2"><span>Throw to the plate</span><b class="w">≈ {P["throw_dist"]:.0f} FT</b></div>
    <div class="drow" id="d3"><span>Runner, third to home</span><b class="cy">{A["r_dist"]:.0f} FT</b></div></div>''', cls="layer", style="z-index:10")
c.ft("#frz1", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), cv + 0.05)
c.ft("#dcard", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), cv + 0.25)
d_t = [cv + 0.3, cv + dist_dur * 0.42, cv + dist_dur * 0.62]
for sel, t in zip(["#d1", "#d2", "#d3"], d_t):
    c.ft(sel, o(opacity=0, x=-24), o(opacity=1, x=0, duration=0.28, ease="power3.out"), t)

# ----------------------------------------------------------------- the two clocks: runner and ball, both from the catch
c.clip("hud", S["v3"] - 0.1, S["v9"], f'''<div class="hud" id="hud">
  <div class="clock run"><span class="cl">Runner</span><b><span id="tm-run">0.00</span><small>s</small></b><span class="cs" id="tm-run-ft">89.0 ft to go</span></div>
  <div class="clock ball"><span class="cl">Ball</span><b><span id="tm-ball">0.00</span><small>s</small></b><span class="cs" id="tm-ball-ph">exchange</span></div></div>''', cls="layer", style="z-index:11")
c.ft("#hud", o(opacity=0, y=-20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), S["v3"] - 0.1)

# release speed + flight time, the comparison throw beside it
rel_v = vt(A["exchange"])
c.clip("thr", rel_v - 0.05, S["v7"], f'''<div class="chips">
  <div class="chip d" id="chd"><span class="ck">Throw</span><b>{DR["mph"]:.0f}<small> mph</small></b><span class="ca">{DR["ang"]:.0f}° launch</span><span class="cf">flight <em id="tm-fl">0.00</em> s</span></div>
  <div class="chip l" id="chl"><span class="ck">Comparison · loop</span><b>{LP["mph"]:.0f}<small> mph</small></b><span class="ca">{LP["ang"]:.0f}° launch</span><span class="cf">flight <em id="tm-fl2">0.00</em> s</span></div></div>''', cls="layer", style="z-index:11")
c.ft("#chd", o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.28, ease="back.out(1.6)"), rel_v - 0.05)
c.ft("#chl", o(opacity=0, x=30), o(opacity=1, x=0, duration=0.28, ease="back.out(1.6)"), S["v4"] + 0.25)

# ----------------------------------------------------------------- freeze on the tag: OUT, and why
v7, v8 = S["v7"], S["v8"]
c.clip("out", v7, v8, f'''<div class="frz low" id="frz2"><i></i>Freeze · the tag</div>
  <div class="stamp no" id="st1">OUT</div>
  <div class="why" id="why1">
    <div class="eqn"><span class="lab y">Ball</span><span class="parts"><b>{f2(A["exchange"])}</b><i>exchange</i></span><span class="op">+</span><span class="parts"><b>{f2(DR["flight"])}</b><i>flight</i></span><span class="op">+</span><span class="parts"><b>{f2(A["tag"])}</b><i>tag</i></span><span class="op">=</span><span class="parts tot y"><b>{f2(DR["tag_t"])}</b><i>seconds</i></span></div>
    <div class="eqn"><span class="lab cy">Runner</span><span class="need">needs <b class="cy">{f2(P["score_t"])} s</b> to reach the plate</span></div>
    <div class="marg" id="m1">Out by {f2(P["score_t"] - DR["tag_t"])} s · {GAP:.1f} ft short</div></div>''', cls="layer", style="z-index:12")
c.ft("#frz2", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), v7 + 0.02)
c.ft("#st1", o(opacity=0, scale=1.6, rotate=-8), o(opacity=1, scale=1, rotate=-8, duration=0.28, ease="back.out(2.2)"), v7 + 0.25)
c.ft("#why1", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.32, ease="power3.out"), v7 + 0.9)
c.ft("#m1", o(opacity=0, scale=0.9), o(opacity=1, scale=1, duration=0.3, ease="back.out(2)"), v7 + 1.8)

# ----------------------------------------------------------------- same play, the looping throw
safe_v = vt_loop(P["score_t"])
c.clip("loop", v8, S["v9"], f'''<div class="lchip" id="lc"><i></i>Same play · {LP["mph"]:.0f} mph, {LP["ang"]:.0f}° loop</div>
  <div class="stamp ok" id="st2">SAFE</div>
  <div class="why" id="why2">
    <div class="eqn"><span class="lab o">Loop</span><span class="parts"><b>{f2(A["exchange"])}</b><i>exchange</i></span><span class="op">+</span><span class="parts"><b>{f2(LP["flight"])}</b><i>flight</i></span><span class="op">+</span><span class="parts"><b>{f2(A["tag"])}</b><i>tag</i></span><span class="op">=</span><span class="parts tot o"><b>{f2(LP["tag_t"])}</b><i>seconds</i></span></div>
    <div class="arcs">Peak height <b class="o">{LP["apex"]:.0f} ft</b> vs <b class="y">{DR["apex"]:.0f} ft</b> · <b class="o">{LP["flight"] - DR["flight"]:.2f} s</b> longer in the air</div></div>''', cls="layer", style="z-index:12")
c.ft("#lc", o(opacity=0, y=-14), o(opacity=1, y=0, duration=0.25, ease="power3.out"), v8 + 0.05)
c.ft("#st2", o(opacity=0, scale=1.6, rotate=-8), o(opacity=1, scale=1, rotate=-8, duration=0.28, ease="back.out(2.2)"), safe_v + 0.05)
c.ft("#why2", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.32, ease="power3.out"), safe_v + 0.5)

# ----------------------------------------------------------------- what decided it
v9 = S["v9"]
rows = [("Runner speed", f'{A["r_vmax"]:.1f} ft/s', f'{FL["runner_fps"]:.1f} ft/s'),
        ("Catch-to-release", f'{A["exchange"]:.2f} s', f'{FL["exchange"]:.2f} s'),
        ("Catch depth", f'{A["catch_dist"]:.0f} ft', f'{FL["catch_dist"]:.0f} ft'),
        ("Arm (flattest throw)", f'{DR["mph"]:.0f} mph', f'{FL["arm_mph"]:.1f} mph'),
        ("Trajectory", f'{DR["ang"]:.0f}° line', f'{LP["ang"]:.0f}° loop')]
rows_html = "".join(f'<div class="vr" id="vr{i}"><span class="vn">{esc(n)}</span><span class="va">{esc(a)}</span><span class="arr">→</span><span class="vb">{esc(b)}</span></div>' for i, (n, a, b) in enumerate(rows))
c.clip("end", v9, D, f'''<div class="endc" id="endc">
  <div class="eh">Out by <b>{f2(P["score_t"] - DR["tag_t"])} s</b>. Change one thing and he's safe:</div>
  <div class="vtab">{rows_html}</div>
  <div class="ek" id="ek">No arm speed guarantees an out. Distance, the exchange, the trajectory, the runner and the tag all go on the same clock.</div>
  <div class="src" id="src">Simulation: drag + backspin lift (Cd {A["cd"]}, {A["throw_rpm"]:,} rpm), {A["r_react"]:.2f} s runner reaction, {A["tag"]:.2f} s tag. Runner at {A["r_vmax"]:.0f} ft/s, the MLB average Statcast sprint speed (Baseball Savant).</div></div>''', cls="layer", style="z-index:12")
c.clip("arcl", v9, D, f'''<div class="arcl o" style="top:1318px">Loop · {LP["flight"]:.2f} s in the air · {LP["apex"]:.0f} ft high</div>
  <div class="arcl y" style="top:1548px">Line · {DR["flight"]:.2f} s · {DR["apex"]:.0f} ft high</div>
  <div class="arce" style="left:34px">Right fielder</div><div class="arce" style="right:34px">Home</div>
  <div class="arcs2">Both throws drawn to scale, side view</div>''', cls="layer", style="z-index:11")
c.ft(".arcl, .arce, .arcs2", o(opacity=0), o(opacity=1, duration=0.4, stagger=0.1), v9 + 0.4)
c.ft("#endc", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.35, ease="power3.out"), v9 + 0.1)
for i in range(len(rows)):
    c.ft(f"#vr{i}", o(opacity=0, x=-26), o(opacity=1, x=0, duration=0.26, ease="power3.out"), v9 + 0.7 + i * 0.32)
c.ft("#ek", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.3, ease="power3.out"), v9 + 0.7 + len(rows) * 0.32 + 0.3)
c.ft("#src", o(opacity=0), o(opacity=1, duration=0.4), v9 + 0.7 + len(rows) * 0.32 + 0.7)

# ----------------------------------------------------------------- sound (no narration)
def cue(n, t, db=0.0): c.cue(n, t, db)
for k in ["v1", "v3", "v4", "v5", "v6", "v8", "v9"]: cue("whoosh", S[k], -9)
cue("glove", cv, -1); cue("impact", cv + 0.02, -10); cue("riser-s", S["v3"], -10)
cue("whoosh", rel_v, -3)                                                     # the throw
for t in np.arange(0.25, DR["tag_t"], 0.25): cue("tick", vt(float(t)), -15)
cue("glove", vt(DR["glove_t"]), 0)
cue("impact", v7, -4); cue("riser-m", v7, -9); cue("hit", v7 + 0.25, -3); cue("popup", v7 + 1.8, -8)
for t in np.arange(S["t8"] + 0.05, LP["tag_t"], 0.25): cue("tick", vt_loop(float(t)), -16)
cue("hit", safe_v + 0.05, -4); cue("glove", vt_loop(LP["glove_t"]), -3)
cue("hit", v9 + 0.1, -7)
for i in range(len(rows)): cue("tick", v9 + 0.7 + i * 0.32, -8)
cue("popup", v9 + 0.7 + len(rows) * 0.32 + 0.3, -9)
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
    crowd = read(os.path.join(HERE, "assets", "sfx", "crowd.wav"))[:n]
    env = np.ones(len(crowd))                                    # the crowd swells with the throw and peaks at the plate
    tt = np.arange(len(crowd)) / SR
    env += 1.2 * np.clip((tt - rel_v) / (v7 - rel_v), 0, 1) * (tt < v7 + 0.2)
    env += 0.8 * np.clip((tt - v8) / (safe_v - v8), 0, 1) * (tt > v8) * (tt < S["v9"])
    fx[: len(crowd)] += crowd * env[:, None] * 10 ** (-22 / 20)
    pre = os.path.join(HERE, ".pre.wav")
    w = wave.open(pre, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(fx * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"), target=-17.0)    # effects only, no narration: a little under speech loudness
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
.chip {{ display:grid; grid-template-columns:auto 1fr; align-items:baseline; gap:2px 14px; padding:12px 22px; border-radius:16px; background:rgba(6,10,18,.8); border:2px solid; }}
.chip .ck {{ grid-column:1 / -1; {MONO} font-size:19px; letter-spacing:.12em; color:#AEB8C6; }}
.chip b {{ font-weight:800; font-size:66px; line-height:1; }}
.chip b small {{ font-size:30px; }}
.chip .ca {{ font-family:"Inter", sans-serif; font-weight:700; font-size:26px; color:#dfe5ec; }}
.chip .cf {{ grid-column:1 / -1; font-family:"Inter", sans-serif; font-weight:700; font-size:26px; color:#cfd6e0; font-variant-numeric:tabular-nums; }}
.chip .cf em {{ font-style:normal; font-weight:800; }}
.chip.d {{ border-color:rgba(255,216,77,.6); }} .chip.d b, .chip.d .cf em {{ color:{Y}; }}
.chip.l {{ border-color:rgba(255,138,61,.6); }} .chip.l b, .chip.l .cf em {{ color:{ORANGE}; }}

.stamp {{ position:absolute; left:0; right:0; top:560px; text-align:center; font-weight:800; font-size:260px; line-height:1; letter-spacing:.02em; text-shadow:0 12px 50px rgba(0,0,0,.7); }}
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
    print(f"index.html: {D}s, shots {S}; release at {rel_v:.2f}s, tag freeze {S['v7']}s, safe {safe_v:.2f}s; {len(c.cues)} sounds; {m['lufs']} LUFS / {m['true_peak']} dBTP")
