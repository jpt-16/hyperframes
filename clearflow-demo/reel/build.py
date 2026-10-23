"""JT Builds Co reel: the ClearFlow website assistant demo (1080x1920, sound effects only, room for a voiceover).

    node tools/capture.mjs && python3 tools/prep.py      # record the real demo, re-time it
    python3 build.py                                     # write index.html + assets/mix.wav
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/clearflow-ai-assistant-reel.mp4 -q delivery

0.0-2.9    hook: 9:47 PM. / Pipe just burst. / Office is closed. / Website isn't.
2.9-24.2   the real demo on a phone: a question, a service-area check, then the lead form, "Request sent"
24.2-28.4  the lead arriving live in the dashboard
28.4-31.6  end card: JT Builds Co | DM 'AI'
The phone and dashboard footage is a frame-exact recording of the running app (see tools/capture.mjs).
ClearFlow Plumbing is fictional; the video says so on screen.
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc
from mix import read, codec_safe, measure, ANCHOR
from sfx import key_click
from audio import SR

TL = json.load(open(os.path.join(HERE, "assets", "media", "timeline.json")))
EV = TL["events"]
P0, P1 = TL["phone_start"], TL["phone_end"]
D0 = round(P1, 3); D1 = round(D0 + TL["dash_len"], 3)
END0 = D1
D = round(END0 + 3.2, 3)
first = lambda typ, **kw: next(e["t"] for e in EV if e["type"] == typ and all(e.get(k) == v for k, v in kw.items()))
T_OPEN = first("click", what="cf-launch")
T_ASK = first("click", what="cf-chip")
T_BOOK = [e["t"] for e in EV if e["type"] == "user" and e.get("text") == "Book a plumber"][0]
T_SENT = first("sent")
T_REVIEW = first("review")
STEPS = [(lbl, [e["t"] for e in EV if e["type"] == "user" and e.get("text") == txt][0])
         for lbl, txt in [("Name", "Marcus Bell"), ("Phone", "(555) 014-3391"), ("Service", "Water heater repair & installation"), ("Details", "No hot water since this morning.")]]

A, CREAM, INK, CHAR = "#FFB547", "#F2EADC", "#1A1206", "#121110"
c = Comp(D, 30)

# phone geometry (px on the 1080x1920 canvas); the capture is 390 css px wide at 2x, shown at 1.5x
S = 1.5
SW, SBH, VH = 390 * S, 44 * S, 716 * S
BZ = 12
PX, PT = 540 - SW / 2 - BZ, 392
SX, ST = PX + BZ, PT + BZ
VT = ST + SBH

# ----------------------------------------------------------------- 0-2.9 hook
HOOK = [("hk1", 0.00, '<span class="clock">9:47 PM.</span>'), ("hk2", 0.50, "Pipe just burst."),
        ("hk3", 1.12, "Office is closed."), ("hk4", 1.80, '<span class="am">Website isn’t.</span>')]
c.clip("hook", 0, 2.95, '<div class="hook">' + "".join(f'<div class="hl" id="{i}">{t}</div>' for i, _, t in HOOK) + "</div>", cls="layer", style="z-index:30")
for hid, t, _ in HOOK:
    if t > 0:                                      # the first line is on screen from frame one
        c.set(f"#{hid}", o(opacity=0), 0)
        c.ft(f"#{hid}", o(opacity=1, y=26, scale=1.04), o(y=0, scale=1, duration=0.26, ease="power3.out", immediateRender=False), t)
    else:
        c.ft(f"#{hid}", o(scale=1.06), o(scale=1, duration=0.4, ease="power3.out"), 0)
c.to(".hook", o(y=-160, opacity=0, duration=0.32, ease="power2.in"), 2.6)

# ----------------------------------------------------------------- the phone (a frame-exact recording of the real app)
def sb(cls):
    return (f'<div class="sb {cls}"><b>9:47</b><i class="island"></i><span class="sb-r">'
            '<svg viewBox="0 0 18 12"><rect x="0" y="8" width="3" height="4" rx=".7"/><rect x="5" y="5.5" width="3" height="6.5" rx=".7"/><rect x="10" y="3" width="3" height="9" rx=".7"/><rect x="15" y="0" width="3" height="12" rx=".7"/></svg>'
            '<svg viewBox="0 0 16 12"><path d="M8 11.5 5.6 9a3.4 3.4 0 0 1 4.8 0Z"/><path d="M3.4 6.8a6.5 6.5 0 0 1 9.2 0l-1.4 1.4a4.5 4.5 0 0 0-6.4 0Z"/><path d="M1.2 4.6a9.6 9.6 0 0 1 13.6 0l-1.4 1.4a7.6 7.6 0 0 0-10.8 0Z"/></svg>'
            '<i class="bat"><i></i></i></span></div>')
taps = "".join(f'<i class="tap" id="tap{k}" style="left:{SX + e["x"] * S:.1f}px;top:{VT + e["y"] * S:.1f}px"></i>'
               for k, e in enumerate(x for x in EV if x["type"] == "click"))
c.raw(f'''<div id="phone" data-layout-ignore>
        <div class="ph-body"></div>
        <div class="ph-sb">{sb("dark")}{sb("light")}</div>
        <video id="phone-v" class="clip" src="assets/media/phone.mp4" muted playsinline data-start="{P0}" data-duration="{round(P1 - P0, 3)}" data-track-index="2"></video>
        <div class="taps">{taps}</div>
      </div>''')
c.set("#phone", o(opacity=0), 0)
c.ft("#phone", o(opacity=0, y=300), o(opacity=1, y=0, duration=0.6, ease="power3.out", immediateRender=False), P0 - 0.05)
c.ft(".sb.light", o(opacity=0), o(opacity=1, duration=0.25, immediateRender=False), T_OPEN + 0.12)
for k, e in enumerate(x for x in EV if x["type"] == "click"):
    c.set(f"#tap{k}", o(opacity=0, scale=0.55), 0)
    c.to(f"#tap{k}", o(opacity=1, scale=0.85, duration=0.12, ease="power2.out"), e["t"] - 0.15)
    c.to(f"#tap{k}", o(opacity=0, scale=1.35, duration=0.32, ease="power2.out"), e["t"] + 0.02)
# "Request sent": push in on the phone (it grows downward, so the label stays clear)
c.to("#phone", o(scale=1.2, duration=0.7, ease="power3.inOut", transformOrigin="540px 392px"), T_SENT + 0.15)
c.to("#phone", o(x=-1150, opacity=0, duration=0.45, ease="power3.in"), P1 - 0.12)

# ----------------------------------------------------------------- labels above the phone
def label(lid, t0, t1, html, small=None):
    inner = f'<div class="lb-t" id="{lid}-t">{html}</div>' + (f'<div class="lb-s">{small}</div>' if small else "")
    c.clip(lid, t0, t1, f'<div class="lb">{inner}</div>', cls="layer", style="z-index:20")
    c.ft(f"#{lid}-t", o(opacity=0, y=22), o(opacity=1, y=0, duration=0.32, ease="power3.out"), t0)
label("lb1", P0 + 0.2, T_ASK, "Your website, <em>after hours.</em>")
label("lb2", T_ASK, T_BOOK, "Answers from your<br><em>real business info.</em>")
label("lb3", T_BOOK, T_SENT, "Then it <em>books the job.</em>")
label("lb4", T_SENT, P1, "<em>Lead captured.</em>")
c.clip("steps", STEPS[0][1] - 0.4, T_SENT, '<div class="steps">' + "".join(
    f'<span class="st" id="st{k}"><i></i>{lbl}</span>' for k, (lbl, _) in enumerate(STEPS)) + "</div>", cls="layer", style="z-index:20")
for k, (_, t) in enumerate(STEPS):
    c.ft(f"#st{k}", o(opacity=0.35), o(opacity=1, duration=0.2, immediateRender=False), t)
    c.set(f"#st{k}", o(opacity=0.35), STEPS[0][1] - 0.4)
    c.ft(f"#st{k} i", o(scale=0.3, backgroundColor="rgba(242,234,220,0)"), o(scale=1, backgroundColor=A, duration=0.3, ease="back.out(2.5)", immediateRender=False), t)
c.clip("demo-tag", P0 + 0.3, D1, '<div class="demo-tag" id="dtag">Demo · ClearFlow Plumbing is a fictional business</div>', cls="layer", style="z-index:20")
c.to("#dtag", o(opacity=0, duration=0.2), T_SENT + 0.05)          # the phone grows over it during the push-in
c.to("#dtag", o(opacity=1, duration=0.3), D0 + 0.4)

# ----------------------------------------------------------------- the dashboard
BW, BBAR = 1000, 46
BH = BBAR + 680 * BW / 1100
BX, BY = 40, 590
c.raw(f'''<div id="browser" data-layout-ignore>
        <div class="br-bar"><i></i><i></i><i></i><span>clearflowplumbing.example/dashboard</span></div>
        <video id="dash-v" class="clip" src="assets/media/dash.mp4" muted playsinline data-start="{D0}" data-duration="{round(D1 - D0, 3)}" data-track-index="3"></video>
      </div>''')
c.set("#browser", o(opacity=0), 0)
c.ft("#browser", o(opacity=0, x=1150), o(opacity=1, x=0, duration=0.5, ease="power3.out", immediateRender=False), D0 - 0.05)
c.to("#browser", o(scale=1.55, duration=0.9, ease="power3.inOut", transformOrigin=f"{360 * BW / 1100:.0f}px {BBAR + 250 * BW / 1100:.0f}px"), D0 + 1.25)
c.to("#browser", o(opacity=0, scale=1.7, duration=0.3, ease="power2.in"), D1 - 0.25)
label("lb5", D0 + 0.05, D1 - 0.1, "Straight to <em>your inbox.</em>")

# ----------------------------------------------------------------- end card
c.clip("end", END0 - 0.05, D, f"""<div class="end">
  <div class="end-h"><div id="e1">Never miss</div><div id="e2">the <em>9:47 PM</em> call.</div></div>
  <div class="lockup" id="lock"><span class="tile"><img src="assets/jt-mark.png" alt="JT Builds Co"></span><b>JT BUILDS CO</b><i class="sep"></i><span class="dm">DM ‘AI’</span></div>
  <div class="end-s" id="es">AI website assistants for local businesses</div>
  <div class="end-d">Demo shown: ClearFlow Plumbing, a fictional business</div></div>""", cls="layer", style="z-index:40")
c.ft(".end", o(opacity=0), o(opacity=1, duration=0.18), END0 - 0.05)
c.ft("#e1", o(opacity=0, y=40), o(opacity=1, y=0, duration=0.32, ease="power4.out"), END0)
c.ft("#e2", o(opacity=0, y=40), o(opacity=1, y=0, duration=0.32, ease="power4.out"), END0 + 0.18)
c.ft("#lock", o(opacity=0, y=30, scale=0.94), o(opacity=1, y=0, scale=1, duration=0.42, ease="back.out(1.6)"), END0 + 0.75)
c.ft("#es", o(opacity=0), o(opacity=1, duration=0.3), END0 + 1.05)
c.to("#lock .dm", o(scale=1.06, duration=0.22, yoyo=True, repeat=1, ease="sine.inOut"), END0 + 1.7)

# ----------------------------------------------------------------- sound: effects only (the voiceover goes on top)
for t, name, db in [(0.0, "impact", -3), (0.50, "hit", -6), (1.12, "hit", -6), (1.80, "impact", -6), (P0, "riser-m", -6), (P0 + 0.1, "whoosh", -8)]:
    c.cue(name, t, db)
for e in EV:
    if e["type"] == "click": c.cue("tap", e["t"] - 0.01, -3)
    elif e["type"] == "key": c.key(e["t"], -2)
    elif e["type"] == "bot": c.cue("bubble", e["t"], -9)
    elif e["type"] == "review": c.cue("popup", e["t"], -8)
for _, t in STEPS: c.cue("popup", t + 0.02, -13)
for t in (T_ASK, T_BOOK): c.cue("whoosh", t + 0.05, -16)
c.cue("impact", T_SENT, -6); c.cue("hit", T_SENT, -5); c.cue("riser-s", T_SENT, -9)
c.cue("whoosh", D0 + 0.05, -6)
c.cue("popup", D0 + 0.73, -5)                  # the toast + new row (dashboard replay fires 0.7 s in)
c.cue("whoosh", D0 + 1.45, -12)
c.cue("riser-m", END0, -5); c.cue("whoosh", END0 - 0.1, -9); c.cue("impact", END0, -2)
c.cue("hit", END0 + 0.75, -5); c.cue("popup", END0 + 0.8, -8)

LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "tap": -6.0, "bubble": -8.0, "popup": -8.0, "riser-s": -8.0, "riser-m": -7.0}

def mixdown(path):
    L = int(round(D * SR)); buf = np.zeros((L, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(L, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: buf[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    for t, gdb in c.keys:
        x = key_click(int(t * 1000)); i = int(t * SR); j = min(L, i + len(x))
        if j > i: buf[i:j] += x[: j - i] * 10 ** ((-14 + gdb) / 20)
    buf *= 10 ** (-2.5 / 20) / (np.max(np.abs(buf)) + 1e-12)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    return measure(path), codec_safe(path)

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
CSS = "\n".join([F("Inter", 700, "Inter-700-latin.woff2"), F("Inter", 800, "Inter-800-latin.woff2"), F("Inter", 900, "Inter-900-latin.woff2"),
                 F("Montserrat", "100 900", "Montserrat-var-latin.woff2"), F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:{CHAR}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"Inter", sans-serif; color:{CREAM};
         background:radial-gradient(ellipse 90% 55% at 50% 45%, #1c1a18 0%, {CHAR} 70%); }}
#grid, #glow, #vignette {{ display:none; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}

.hook {{ position:absolute; left:60px; right:60px; top:560px; display:grid; gap:14px; }}
.hl {{ font-weight:900; font-size:96px; line-height:1.0; letter-spacing:-.045em; color:{CREAM}; }}
.hl .clock {{ font-family:"Plex Mono", monospace; font-weight:500; font-size:120px; letter-spacing:-.02em; color:{A}; }}
.hl .am {{ color:{A}; }}

#phone {{ position:absolute; inset:0; transform-origin:540px 392px; }}
.ph-body {{ position:absolute; left:{PX:.1f}px; top:{PT}px; width:{SW + 2 * BZ:.1f}px; height:{SBH + VH + 2 * BZ:.1f}px; border-radius:70px; background:#050505;
            box-shadow:0 0 0 2px #2c2a27, 0 0 0 7px #161514, 0 60px 120px -30px rgba(0,0,0,.75); }}
.ph-sb {{ position:absolute; left:{SX:.1f}px; top:{ST}px; width:{SW:.1f}px; height:{SBH:.1f}px; border-radius:58px 58px 0 0; overflow:hidden; }}
.sb {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:space-between; padding:6px 54px 0 66px; font-family:"Inter", sans-serif; }}
.sb b {{ font-weight:700; font-size:24px; letter-spacing:-.01em; }}
.sb.dark {{ background:#08142a; color:#fff; }}
.sb.light {{ background:#fff; color:#0a0a0a; opacity:0; }}
.island {{ position:absolute; left:50%; top:13px; width:150px; height:42px; margin-left:-75px; border-radius:21px; background:#000; }}
.sb-r {{ display:flex; align-items:center; gap:9px; }}
.sb-r svg {{ height:17px; width:auto; fill:currentColor; }}
.bat {{ display:block; width:38px; height:18px; border-radius:5px; border:2px solid currentColor; opacity:.9; padding:2px; position:relative; }}
.bat i {{ display:block; width:72%; height:100%; border-radius:2px; background:currentColor; }}
#phone-v {{ position:absolute; left:{SX:.1f}px; top:{VT:.1f}px; width:{SW:.1f}px; height:{VH:.1f}px; border-radius:0 0 58px 58px; object-fit:cover; }}
.taps {{ position:absolute; inset:0; }}
.tap {{ position:absolute; width:76px; height:76px; margin:-38px 0 0 -38px; border-radius:50%; opacity:0;
        background:rgba(20,22,26,.26); border:3px solid rgba(255,255,255,.92); box-shadow:0 0 0 1.5px rgba(0,0,0,.28), 0 6px 18px rgba(0,0,0,.25); }}

.lb {{ position:absolute; left:50px; right:50px; top:168px; text-align:center; }}
.lb-t {{ font-weight:800; font-size:62px; line-height:1.06; letter-spacing:-.035em; color:{CREAM}; }}
.lb-t em {{ font-style:normal; color:{A}; }}
.steps {{ position:absolute; left:0; right:0; top:318px; display:flex; justify-content:center; gap:12px; }}
.st {{ display:inline-flex; align-items:center; gap:10px; padding:9px 18px 9px 12px; border-radius:999px; background:rgba(242,234,220,.08); border:1px solid rgba(242,234,220,.16);
       font-weight:700; font-size:26px; color:{CREAM}; }}
.st i {{ width:16px; height:16px; border-radius:50%; border:2px solid {A}; }}
.demo-tag {{ position:absolute; left:0; right:0; top:1588px; text-align:center; font-family:"Plex Mono", monospace; font-weight:500; font-size:22px;
             letter-spacing:.06em; text-transform:uppercase; color:#9a958d; }}

#browser {{ position:absolute; left:{BX}px; top:{BY}px; width:{BW}px; height:{BH:.1f}px; border-radius:18px; overflow:hidden; background:#fff;
            box-shadow:0 0 0 1px rgba(255,255,255,.1), 0 50px 110px -30px rgba(0,0,0,.75); }}
.br-bar {{ height:{BBAR}px; background:#e9e7e3; display:flex; align-items:center; gap:9px; padding:0 18px; }}
.br-bar i {{ width:13px; height:13px; border-radius:50%; background:#cdc9c3; }}
.br-bar span {{ margin-left:16px; flex:1; height:28px; border-radius:14px; background:#fff; display:flex; align-items:center; padding:0 14px;
                font-size:16px; color:#5f6368; font-family:"Inter", sans-serif; font-weight:700; }}
#dash-v {{ position:absolute; left:0; top:{BBAR}px; width:{BW}px; height:{BH - BBAR:.1f}px; }}

.end {{ position:absolute; inset:0; background:radial-gradient(ellipse 90% 55% at 50% 45%, #1c1a18 0%, {CHAR} 70%); }}
.end-h {{ position:absolute; left:50px; right:50px; top:600px; text-align:center; font-weight:900; font-size:104px; line-height:1.0; letter-spacing:-.045em; color:{CREAM}; }}
.end-h em {{ font-style:normal; color:{A}; }}
.lockup {{ position:absolute; left:0; right:0; top:1000px; display:flex; align-items:center; justify-content:center; gap:22px; font-family:"Montserrat", sans-serif; }}
.lockup .tile {{ width:92px; height:92px; border-radius:22px; background:#201E1D; display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 1px rgba(255,255,255,.1); }}
.lockup .tile img {{ width:58px; height:49px; }}
.lockup b {{ font-weight:800; font-size:46px; letter-spacing:.06em; color:#F7F6F4; }}
.lockup .sep {{ width:3px; height:56px; background:rgba(255,255,255,.35); }}
.lockup .dm {{ display:inline-block; padding:18px 30px; border-radius:999px; background:{A}; color:{INK}; font-weight:800; font-size:44px; }}
.end-s {{ position:absolute; left:0; right:0; top:1150px; text-align:center; font-weight:700; font-size:36px; color:#BDB6AC; }}
.end-d {{ position:absolute; left:0; right:0; top:1588px; text-align:center; font-family:"Plex Mono", monospace; font-weight:500; font-size:22px; letter-spacing:.06em; text-transform:uppercase; color:#938e86; }}
"""])

if __name__ == "__main__":
    h = c.page(CSS, "JT Builds Co · AI website assistant demo", script=True).replace('<script src="assets/gsap.min.js">', '<script src="assets/vendor/gsap.min.js">')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    (I, tp), dips = mixdown(os.path.join(HERE, "assets", "mix.wav"))
    print(f"index.html: {D}s (phone {P0}-{P1}, dashboard {D0}-{D1}, end {END0}); {len(c.cues)} sounds + {len(c.keys)} key clicks; {I} LUFS, {tp} dBTP, dips {dips}")
