"""JT Builds Co reel: Claude Duet and what it means for small business owners (1080x1920, 30 fps, ~36 s).

    python3 build.py                      # index.html + assets/mix.wav (voice) + assets/mix-novo.wav (no voice)
    npx --yes hyperframes@0.8.154 render . -o renders/claude-duet-reel.mp4 --video-bitrate 16M
    python3 tools/finish.py               # Instagram-ready MP4s: with the voice, and a no-voice version

The voiceover is the creator's own recording (assets/vo/voice.wav, not committed). Shots and captions are
timed to it. Every interface is an illustrative mockup: no real Claude Duet footage is used, and the reel
labels the mockups as such. Facts about Duet follow Anthropic's announcement and help-center article
(research preview, US Pro and Max, waitlist; asks before sending, paying, signing or deleting).
"""
import json, os, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jtb-shorts", "lib"))
from comp import Comp, o, esc, rich
from mix import read, master, ANCHOR
from audio import SR, make_bed

VO = os.path.join(HERE, "assets", "vo", "voice.wav")
D = 36.0
BG, PANEL, PANEL2, LINE = "#0C0B0A", "#161412", "#1E1B18", "rgba(255,255,255,.08)"
INK, MUTED, DIM = "#F3EFE9", "#9B958D", "#6E6962"
ACC, ACC_SOFT = "#D97757", "rgba(217,119,87,.14)"      # restrained, Claude-inspired orange
OK = "#7FC8A0"

# ----------------------------------------------------------------- timing, from the voiceover
# (word times from a local speech recognizer run on the recording; each scene cuts on the phrase it shows)
T = dict(title=3.92, pro=7.62, inv=11.72, fol=13.88, cal=15.58, mkt=17.48, focus=18.42, shift=21.45, later=23.62,
         stop=26.55, start=28.52, end=31.5)
CAPS = [   # key-phrase captions, on the words they echo
    ("Could change how *small businesses* operate", 2.02, 3.85),
    ("It's called *Claude Duet*", 4.05, 5.55),
    ("Things that *need your attention*", 7.68, 10.02),
    ("Working on tasks *in the background*", 10.06, 11.66),
    ("Checking for *unpaid invoices*", 11.76, 13.84),
    ("Preparing *customer follow-ups*", 13.92, 15.52),
    ("Organizing *your calendar*", 15.62, 17.42),
    ("Helping with *marketing*", 17.52, 18.38),
    ("While you focus on *running your business*", 18.46, 21.36),
    ("From AI that *gives answers*", 21.52, 23.58),
    ("To AI that helps *get work done*", 23.66, 26.42),
]

# layout: you full screen ("face"), you on top / the mockup below ("split"), or the mockup full screen ("ui")
MODES = [(0, 2.0, "face"), (2.0, 3.92, "split"), (3.92, 7.62, "ui"), (7.62, 11.72, "split"), (11.72, 13.88, "ui"), (13.88, 15.58, "split"),
         (15.58, 18.42, "ui"), (18.42, 21.45, "split"), (21.45, 23.62, "face"), (23.62, 26.55, "ui"), (26.55, 31.5, "split"), (31.5, D, "ui")]
SPLIT_SCENE = {2.0: ("s1", 850, 0.62, 1170), 7.62: ("s3", 300, 0.66, 1172), 13.88: ("s5", 300, 0.66, 1172), 18.42: ("s7b", 330, 0.66, 1172), 26.55: ("s9", 520, 0.62, 1030)}
SPLIT_TOP, CAM_Y = 1118, -380            # where the mockup starts in split; how far your frame shifts up so your face fills the top half
def mode_at(t): return next(m for a, b, m in MODES if a <= t < b)

c = Comp(D, 30)
def tag(cid, t0, t1, text, top=150):
    c.clip(cid, t0, t1, f'<div class="mtag" style="top:{top}px"><i></i>{esc(text)}</div>', cls="layer", style="z-index:25")

# ----------------------------------------------------------------- 1. hook: a phone at 2 AM, the work arriving
NOTES = [("Invoices", "3 invoices are past due. Reminders drafted.", "Needs your OK"),
         ("Calendar", "Thursday's install overlaps a client call. Move it?", "Needs your OK"),
         ("Marketing", "Next week's newsletter draft is ready to review.", "For review")]
notes_html = "".join(f'''<div class="ntf" id="n{k}"><div class="nh"><span class="nd"></span><b>Duet</b><span class="nt">{w}</span><span class="nw">{esc(a)}</span></div>
    <div class="nb">{esc(b)}</div><span class="nk">{esc(k_)}</span></div>''' for k, (a, b, k_), w in zip(range(3), NOTES, ["now", "1m ago", "4m ago"]))
c.clip("s1h", 0, MODES[1][0], """<div class="hook">
    <div class="hk-k" id="hk0">Anthropic · research preview</div>
    <h1 id="hk1">AI that works</h1><h1 class="a" id="hk2">while you don't?</h1></div>""", cls="layer", style="z-index:20")
c.ft("#hk0", o(opacity=0), o(opacity=1, duration=0.4), 0.9)
c.clip("s1", 0, T["title"], f'''<div class="phone" id="ph1"><div class="ls-time">2:14</div><div class="ls-date">Tuesday</div><div class="ntfs">{notes_html}</div></div>''', cls="scene clip")
c.set("#s1", o(opacity=1), 0)
c.ft("#ph1", o(y=80), o(y=0, duration=1.9, ease="power2.out"), MODES[1][0])
for k, t in enumerate([2.3, 2.75], 1):                          # the first notification is already waiting when the split opens
    c.ft(f"#n{k}", o(opacity=0, y=-40, scale=0.96), o(opacity=1, y=0, scale=1, duration=0.32, ease="power3.out"), t)

# ----------------------------------------------------------------- 2. Claude Duet: what it is
c.clip("s2", T["title"], T["pro"], f'''<div class="title">
    <div class="t-k">New from Anthropic · announced Oct 21, 2026</div>
    <div class="t-n" id="tn"><span>Claude</span> <em>Duet</em></div>
    <p class="t-d" id="td">A proactive agent app. It brings you what needs your attention, works on tasks you hand it, and <b>checks with you before it acts</b> on your behalf.</p>
    <div class="t-b" id="tb"><span class="badge">Early research preview</span><span class="badge q">US · Pro &amp; Max · waitlist</span></div></div>''', cls="scene clip")
c.ft("#s2", o(opacity=0), o(opacity=1, duration=0.12), T["title"])
c.ft("#tn", o(opacity=0, y=40, letterSpacing="0.06em"), o(opacity=1, y=0, letterSpacing="-0.02em", duration=0.7, ease="power4.out"), T["title"] + 0.05)
c.ft("#td", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.45, ease="power3.out"), T["title"] + 1.0)
c.ft("#tb", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.4, ease="power3.out"), T["title"] + 1.7)

# ----------------------------------------------------------------- the app frame used by every mock (illustrative)
def app(cid, t0, t1, title, body, sub=""):
    c.clip(cid, t0, t1, f'''<div class="app" id="{cid}-a"><div class="ab"><span class="nd"></span><b>Duet</b><span class="at">{esc(title)}</span><span class="as">{esc(sub)}</span></div>
      <div class="abody">{body}</div></div>''', cls="scene clip")
    c.ft(f"#{cid}", o(opacity=0), o(opacity=1, duration=0.1), t0)
    c.ft(f"#{cid}-a", o(y=60, scale=0.97), o(y=0, scale=1, duration=0.45, ease="power3.out"), t0)

# 3. proactive: the morning brief and the tasks running in the background
p0 = T["pro"]
brief = [("Two invoices are more than 30 days overdue", "Invoices"), ("Maria asked to move Thursday's install", "Calendar"), ("Newsletter goes out Friday, no draft yet", "Marketing")]
tasks = [("Chase overdue invoices", "Waiting on you", "w"), ("Draft customer follow-ups", "Working", "r"), ("Plan next week's posts", "Working", "r")]
body = '<div class="sec">Morning brief</div>' + "".join(f'<div class="bi" id="bi{k}"><span class="bt">{esc(t)}</span><span class="bg">{esc(g)}</span></div>' for k, (t, g) in enumerate(brief)) + \
       '<div class="sec">Tasks</div>' + "".join(f'<div class="ti" id="ti{k}"><span class="tt">{esc(t)}</span><span class="ts {s}"><i></i>{esc(st)}</span></div>' for k, (t, st, s) in enumerate(tasks))
app("s3", p0, T["inv"], "Main thread", body, "Tue 7:02 AM")
for k in range(3): c.ft(f"#bi{k}", o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.3, ease="power3.out"), p0 + 0.35 + k * 0.32)
for k in range(3): c.ft(f"#ti{k}", o(opacity=0, x=-30), o(opacity=1, x=0, duration=0.3, ease="power3.out"), p0 + 2.45 + k * 0.28)
c.line(f'tl.to("#s3 .ts.r i", {{ rotation: 720, duration: {T["inv"] - p0 - 2.4:.2f}, ease: "none" }}, {p0 + 2.4:.2f});')

# 4. unpaid invoices
i0 = T["inv"]
INV = [("#1038", "Harbor Street Bakery", "$1,240", "41 days late", True), ("#1042", "Pine & Co. Landscaping", "$860", "33 days late", True),
       ("#1047", "Delgado Family Dental", "$2,720", "31 days late", True), ("#1051", "Northside Fitness", "$950", "Due in 5 days", False)]
rows = "".join(f'<div class="iv{" od" if late else ""}" id="iv{k}"><span class="in">{n}</span><span class="ic">{esc(cn)}</span><span class="ia">{amt}</span><span class="il">{esc(st)}</span></div>' for k, (n, cn, amt, st, late) in enumerate(INV))
app("s4", i0, T["fol"], "Unpaid invoices", f'<div class="isum" id="isum"><b>3 overdue</b><span>$4,820 outstanding</span></div>{rows}', "from your accounting app")
for k in range(4): c.ft(f"#iv{k}", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.25, ease="power3.out"), i0 + 0.2 + k * 0.14)
c.ft("#s4 .iv.od", o(backgroundColor="rgba(217,119,87,0)"), o(backgroundColor=ACC_SOFT, duration=0.3, stagger=0.12), i0 + 0.95)
c.ft("#isum", o(opacity=0, y=-10), o(opacity=1, y=0, duration=0.3), i0 + 1.35)

# 5. a follow-up, drafted, waiting for approval
f0 = T["fol"]
mail = "Hi Dana, a quick reminder that invoice #1038 for $1,240 is now 41 days past due. You can pay it here. Thanks so much! Sam"
words = mail.split()
mail_html = " ".join(f'<span class="mw" id="mw{k}">{esc(w)}</span>' for k, w in enumerate(words))
app("s5", f0, T["cal"], "Follow-up draft", f'''<div class="mh"><span>To</span><b>Dana · Harbor Street Bakery</b></div><div class="mh"><span>Re</span><b>Invoice #1038</b></div>
    <div class="mb">{mail_html}</div>
    <div class="appr" id="appr"><span class="aq">Duet asks before sending</span><span class="btn g">Edit</span><span class="btn p" id="send">Approve &amp; send</span></div>''', "draft · not sent")
for k in range(len(words)): c.set(f"#mw{k}", o(opacity=1), f0 + 0.25 + k * 0.045)
c.set("#s5 .mw", o(opacity=0), f0)
c.ft("#appr", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), f0 + 0.25 + len(words) * 0.045 + 0.05)

# 6. the calendar, reorganized (a proposal)
k0 = T["cal"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
EV = [(0, 9, 2, "Site visit", ""), (1, 13, 1.5, "Payroll", ""), (3, 10, 1.5, "Client call", ""), (2, 15, 1.5, "Supplier", ""), (3, 10.5, 2, "Install · Maria", "mv")]
cal = '<div class="cg">' + "".join(f'<div class="cd"><span>{d}</span></div>' for d in DAYS) + "".join(
    f'<div class="ce {cl}" id="ce{k}" style="left:{8 + d * 20:.1f}%;top:{(h - 8) * 52 + 50}px;height:{dur * 52 - 6}px"><b>{esc(n)}</b></div>' for k, (d, h, dur, n, cl) in enumerate(EV)) + "</div>"
app("s6", k0, T["mkt"], "Calendar", cal + '<div class="prop" id="prop"><b>1 change proposed</b><span>Move the install to Friday, 10 AM</span><span class="btn p">Approve</span></div>', "this week")
c.ft("#ce4", o(borderColor="rgba(255,97,97,.9)"), o(borderColor="rgba(255,97,97,.9)", duration=0.01), k0 + 0.05)
c.to("#ce4", o(left="88%", top=(10 - 8) * 52 + 50, borderColor=ACC, duration=0.55, ease="power3.inOut"), k0 + 0.7)
c.ft("#prop", o(opacity=0, y=20), o(opacity=1, y=0, duration=0.3, ease="power3.out"), k0 + 1.05)

# 7. marketing drafts, then the whole board while the owner does the actual work
m0 = T["mkt"]
POSTS = [("Fall maintenance checklist", "Carousel · 6 slides"), ("Customer spotlight: Harbor Street Bakery", "Reel script"), ("Weekend availability", "Story")]
app("s7", m0, T["focus"], "Content drafts", "".join(f'<div class="pc" id="pc{k}"><b>{esc(a)}</b><span>{esc(b)}</span><span class="st">Draft · for your review</span></div>' for k, (a, b) in enumerate(POSTS)), "next week")
for k in range(3): c.ft(f"#pc{k}", o(opacity=0, y=24), o(opacity=1, y=0, duration=0.22, ease="power3.out"), m0 + 0.05 + k * 0.1)
q0 = T["focus"]
TILES = [("Invoices", "3 reminders drafted"), ("Follow-ups", "2 drafts ready"), ("Calendar", "1 change proposed"), ("Marketing", "3 posts to review")]
c.clip("s7b", q0, T["shift"], f'''<div class="board"><div class="bh" id="bh">Waiting on <em>you</em> · 4 approvals</div>
    <div class="tiles">{"".join(f'<div class="tile" id="tl{k}"><span>{esc(a)}</span><b>{esc(b)}</b><i>Needs your OK</i></div>' for k, (a, b) in enumerate(TILES))}</div>
    <div class="you" id="you">Nothing goes out until you approve it.</div></div>''', cls="scene clip")
c.ft("#s7b", o(opacity=0), o(opacity=1, duration=0.12), q0)
for k in range(4): c.ft(f"#tl{k}", o(opacity=0, scale=0.92), o(opacity=1, scale=1, duration=0.3, ease="back.out(1.6)"), q0 + 0.1 + k * 0.12)
c.ft("#bh", o(opacity=0, y=-12), o(opacity=1, y=0, duration=0.3), q0 + 0.7)
c.ft("#you", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.35), q0 + 1.3)
tag("mt", 0, T["shift"], "Illustrative mockup · not real product footage")

# ----------------------------------------------------------------- 8. the shift: answers -> delegated work
s0 = T["shift"]
c.clip("s8", s0, T["stop"], f'''<div class="shift">
    <div class="col was" id="was"><div class="ck">Asking AI</div>
      <div class="bq">Which invoices are overdue?</div><div class="ba">Three: #1038, #1042 and #1047.</div><div class="ce2">Then you do the rest.</div></div>
    <div class="arrow" id="arw"></div>
    <div class="col now" id="now"><div class="ck">Delegating to AI</div>
      <div class="job"><b>Collect on overdue invoices</b>
        <div class="stp" id="sp0"><i class="d"></i>Found 3 overdue invoices</div>
        <div class="stp" id="sp1"><i class="d"></i>Drafted 3 reminders</div>
        <div class="stp" id="sp2"><i class="w"></i>Send · waiting for your approval</div></div></div></div>''', cls="scene clip")
c.ft("#s8", o(opacity=0), o(opacity=1, duration=0.12), s0)
c.ft("#was", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.4, ease="power3.out"), s0 + 0.05)
c.to("#was", o(opacity=0.38, scale=0.97, duration=0.5), T["later"] - 0.1)
c.ft("#arw", o(scaleY=0), o(scaleY=1, duration=0.35, ease="power2.out"), T["later"] - 0.05)
c.ft("#now", o(opacity=0, y=30), o(opacity=1, y=0, duration=0.4, ease="power3.out"), T["later"] + 0.2)
for k in range(3): c.ft(f"#sp{k}", o(opacity=0, x=-20), o(opacity=1, x=0, duration=0.28, ease="power3.out"), T["later"] + 0.75 + k * 0.45)
tag("mt2", s0 + 0.1, T["stop"], "Illustrative mockup · not real product footage")

# ----------------------------------------------------------------- 9. stop just using AI. start building systems.  10. JT Builds Co
e0 = T["end"]
c.clip("s9", T["stop"], D, f'''<div class="sys"><svg class="flow" viewBox="0 0 1080 700" id="flow"><path d="M140 560 C 320 560, 300 300, 540 300 S 760 140, 940 140" /></svg>
    <h2 id="l1">Stop just<br>using AI.</h2><h2 class="a" id="l2">Start building<br>systems.</h2></div>
  <div class="endc" id="endc">
    <div class="lock" id="lock"><span class="tile"><img src="assets/jt-mark.png" alt=""></span><b>JT BUILDS CO</b></div>
    <p class="q2" id="q2">The question isn't just what AI can tell you. It's what it can do for your business.</p>
    <p class="fine" id="fine">Claude Duet is an early research preview (US Pro &amp; Max plans, by waitlist). It asks before it sends, pays, signs or deletes, and it can make mistakes, so review its work. Interfaces shown are illustrative mockups.</p></div>''', cls="scene clip")
c.ft("#s9", o(opacity=0), o(opacity=1, duration=0.1), T["stop"])
c.ft("#l1", o(opacity=0, y=50), o(opacity=1, y=0, duration=0.5, ease="power4.out"), T["stop"] + 0.05)
c.ft("#l2", o(opacity=0, y=50), o(opacity=1, y=0, duration=0.5, ease="power4.out"), T["start"])
c.ft("#flow path", o(strokeDashoffset=1400), o(strokeDashoffset=0, duration=2.6, ease="power2.inOut"), T["start"] - 0.2)
c.to(".sys", o(y=-330, scale=0.78, duration=0.7, ease="power3.inOut"), e0)
c.ft("#lock", o(opacity=0, y=30, scale=0.94), o(opacity=1, y=0, scale=1, duration=0.45, ease="back.out(1.6)"), e0 + 0.35)
c.ft("#q2", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.4), e0 + 0.85)
c.ft("#fine", o(opacity=0), o(opacity=1, duration=0.5), e0 + 1.6)

# ----------------------------------------------------------------- you: full screen, top half, or off (your recording; the voice comes from the same file)
c.raw(f'''<div id="camw"><video id="cam" class="clip" src="assets/media/talk.mp4" muted playsinline data-start="0" data-duration="{D}" data-track-index="2"></video>
        <div class="cg-top"></div><div class="cg-bot"></div><i class="seam"></i></div>''')
for a, b, m in MODES:
    if m == "face": c.set("#camw", o(opacity=1, height=1920), a); c.set("#cam", o(y=0), a); c.set("#camw .seam", o(opacity=0), a)
    elif m == "split": c.set("#camw", o(opacity=1, height=960), a); c.set("#cam", o(y=CAM_Y), a); c.set("#camw .seam", o(opacity=1), a)
    else: c.set("#camw", o(opacity=0), a)
    if m == "split":                                            # the mockup drops into the bottom half
        sid, top, sc, to = SPLIT_SCENE[a]
        c.set(f"#{sid}", o(y=to - top * sc, scale=sc, transformOrigin="50% 0%"), a)
        c.set(f"#{sid}", o(y=0, scale=1), b)
    for tid in ["#mt .mtag", "#mt2 .mtag"]:                     # the mockup label follows the mockup, and steps aside for you
        c.set(tid, o(opacity=0) if m == "face" else o(opacity=1, top=SPLIT_TOP if m == "split" else 150), a)

# ----------------------------------------------------------------- captions: large, key phrases, on the words
for k, (txt, a, b) in enumerate(CAPS):
    ws = txt.split()
    acc, html_ = False, []
    for n, w in enumerate(ws):
        s = w.startswith("*"); acc = acc or s; e = w.endswith("*")
        html_.append(f'<span class="cw{" a" if acc else ""}" id="c{k}w{n}">{esc(w.strip("*"))}</span>')
        if e: acc = False
    c.clip(f"cap{k}", a, b, f'<div class="cap {mode_at(a)}"><span class="cl">{" ".join(html_)}</span></div>', cls="layer", style="z-index:30")
    for n in range(len(ws)):
        c.ft(f"#c{k}w{n}", o(opacity=0, y=26), o(opacity=1, y=0, duration=0.2, ease="power3.out"), a + n * 0.06)

# ----------------------------------------------------------------- sound: subtle, under the voice
cue = c.cue
cue("impact", 0.0, -8)
for t in [0.4, 0.85]: cue("popup", t, -10)
for k_ in ["title", "pro", "inv", "fol", "cal", "mkt", "focus", "shift", "stop"]: cue("whoosh", T[k_], -14)
for k in range(3): cue("tap", p0 + 0.35 + k * 0.32, -14)
cue("tap", i0 + 0.95, -12); cue("popup", i0 + 1.35, -12)
for k in range(0, len(words), 2): cue("tap", f0 + 0.25 + k * 0.045, -22)
cue("popup", f0 + 0.25 + len(words) * 0.045 + 0.05, -11)
cue("tap", k0 + 0.7, -12); cue("popup", k0 + 1.05, -12)
for k in range(4): cue("tap", q0 + 0.1 + k * 0.12, -14)
cue("riser-m", T["stop"], -12); cue("hit", T["stop"] + 0.05, -8); cue("hit", T["start"], -8); cue("impact", e0 + 0.35, -10)
LEVEL = {"impact": -3.0, "hit": -5.0, "whoosh": -6.0, "tap": -4.0, "popup": -8.0, "riser-m": -7.0, "bubble": -8.0}

def mixdown():
    n = int(round(D * SR)); fx = np.zeros((n, 2)); cache = {}
    for name, t, gdb in c.cues:
        x = cache.setdefault(name, read(os.path.join(HERE, "assets", "sfx", f"{name}.wav")))
        a = ANCHOR.get(name)
        st = t - len(x) / SR if a == "end" else (t - np.argmax(np.abs(x).sum(1)) / SR if a == "peak" else t)
        i = int(round(st * SR)); j = min(n, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j > i: fx[i:j] += x[: j - i] * 10 ** ((LEVEL.get(name, -8.0) + gdb) / 20)
    bed = os.path.join(HERE, ".bed.wav")
    make_bed(bed, D, T["stop"], style="glow", seed=11)
    fx[:] += read(bed)[:n] * 10 ** (-17 / 20); os.remove(bed)
    vo = read(VO)[:n]
    full = fx * 10 ** (-6 / 20); full[: len(vo)] += vo
    def wr(p, x):
        w = wave.open(p, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x * 0.5, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    pre, fxp = os.path.join(HERE, ".pre.wav"), os.path.join(HERE, ".fx.wav")
    wr(pre, full); wr(fxp, fx * 10 ** (-6 / 20))
    m = master(pre, os.path.join(HERE, "assets", "mix.wav"))
    f = master(pre, os.path.join(HERE, "assets", "mix-novo.wav"), fx_path=fxp)    # same gain: drop a voiceover on top
    os.remove(pre); os.remove(fxp)
    return m, f

# ----------------------------------------------------------------- CSS
F = lambda fam, w, f, rng=False: f'@font-face {{ font-family:"{fam}"; font-weight:{w}; font-display:block; src:url("assets/fonts/{f}") format("woff2"); }}'
MONO = 'font-family:"Plex Mono", monospace; font-weight:500; text-transform:uppercase;'
CSS = "\n".join([F("Inter", 400, "Inter-400-latin.woff2"), F("Inter", 600, "Inter-600-latin.woff2"), F("Inter", 700, "Inter-700-latin.woff2"),
                 F("Inter", 800, "Inter-800-latin.woff2"), F("Fraunces", "300 900", "Fraunces-var-latin.woff2"), F("Montserrat", "100 900", "Montserrat-var-latin.woff2"),
                 F("Plex Mono", 500, "plex-mono-500.woff2"), f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:{BG}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"Inter", sans-serif; color:{INK}; -webkit-font-smoothing:antialiased;
         background:radial-gradient(ellipse 120% 70% at 50% 38%, #171513 0%, {BG} 70%); }}
#grid, #glow {{ display:none; }}
#vignette {{ position:absolute; inset:0; pointer-events:none; z-index:50; background:radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 60%, rgba(0,0,0,.45) 100%); }}
.scene {{ position:absolute; inset:0; opacity:0; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
.nd {{ width:14px; height:14px; border-radius:50%; background:{ACC}; display:inline-block; flex:none; }}

.mtag {{ position:absolute; left:50%; transform:translateX(-50%); display:inline-flex; align-items:center; gap:10px; padding:8px 16px; border-radius:999px;
         background:rgba(22,20,18,.86); border:1px solid {LINE}; {MONO} font-size:19px; letter-spacing:.14em; color:{MUTED}; white-space:nowrap; }}
.mtag i {{ width:8px; height:8px; border-radius:50%; background:{ACC}; }}

/* 1. hook */
.hook {{ position:absolute; left:64px; right:60px; top:118px; }}
.hk-k {{ {MONO} font-size:22px; letter-spacing:.18em; color:{MUTED}; margin-bottom:22px; }}
.hook h1 {{ font-family:"Inter", sans-serif; font-weight:800; font-size:106px; text-shadow:0 6px 36px rgba(0,0,0,.6); line-height:.98; letter-spacing:-.04em; text-transform:uppercase; }}
.hook h1.a {{ color:{ACC}; }}
.phone {{ position:absolute; left:150px; width:780px; top:850px; height:1300px; border-radius:76px; background:linear-gradient(180deg, #1A1714, #100E0C);
          border:2px solid rgba(255,255,255,.10); box-shadow:0 40px 120px rgba(0,0,0,.6), inset 0 0 0 10px #0A0908; padding:80px 46px 0; }}
.ls-time {{ text-align:center; font-family:"Inter", sans-serif; font-weight:600; font-size:150px; letter-spacing:-.04em; color:#EDE7DF; line-height:1; }}
.ls-date {{ text-align:center; font-size:30px; color:{MUTED}; margin:8px 0 40px; }}
.ntfs {{ display:grid; gap:16px; }}
.ntf {{ background:rgba(40,36,32,.82); border:1px solid {LINE}; border-radius:30px; padding:20px 24px 18px; display:grid; gap:6px; }}
.nh {{ display:flex; align-items:center; gap:10px; font-size:22px; color:{MUTED}; }}
.nh b {{ color:{INK}; font-weight:700; }} .nh .nw {{ margin-left:auto; {MONO} font-size:16px; letter-spacing:.1em; }}
.nb {{ font-size:30px; line-height:1.28; font-weight:600; color:{INK}; }}
.nk {{ justify-self:start; font-size:19px; font-weight:700; color:{ACC}; background:{ACC_SOFT}; padding:4px 12px; border-radius:999px; }}

/* 2. title */
.title {{ position:absolute; left:70px; right:70px; top:470px; display:grid; gap:34px; }}
.t-k {{ {MONO} font-size:22px; letter-spacing:.16em; color:{MUTED}; }}
.t-n {{ font-family:"Fraunces", serif; font-weight:500; font-size:190px; line-height:.92; letter-spacing:-.02em; font-variation-settings:"opsz" 144; }}
.t-n em {{ font-style:italic; color:{ACC}; font-weight:400; }}
.t-d {{ font-size:42px; line-height:1.34; color:#D8D2CA; max-width:900px; }}
.t-d b {{ color:{INK}; font-weight:700; }}
.t-b {{ display:flex; gap:14px; flex-wrap:wrap; }}
.badge {{ {MONO} font-size:22px; letter-spacing:.1em; padding:10px 18px; border-radius:999px; border:1.5px solid {ACC}; color:{ACC}; }}
.badge.q {{ border-color:{LINE}; color:{MUTED}; }}

/* the app frame */
.app {{ position:absolute; left:60px; right:60px; top:300px; border-radius:44px; background:{PANEL}; border:1px solid {LINE};
        box-shadow:0 40px 120px rgba(0,0,0,.55); overflow:hidden; }}
.ab {{ display:flex; align-items:center; gap:12px; padding:28px 34px; border-bottom:1px solid {LINE}; font-size:28px; }}
.ab b {{ font-weight:700; }} .ab .at {{ color:{MUTED}; }} .ab .as {{ margin-left:auto; {MONO} font-size:18px; letter-spacing:.1em; color:{DIM}; }}
.abody {{ padding:26px 34px 34px; display:grid; gap:14px; }}
.sec {{ {MONO} font-size:20px; letter-spacing:.16em; color:{DIM}; margin-top:6px; }}
.bi, .ti {{ display:flex; align-items:center; gap:16px; padding:20px 22px; border-radius:22px; background:{PANEL2}; font-size:32px; font-weight:600; }}
.bi .bt, .ti .tt {{ flex:1; line-height:1.25; }}
.bg {{ {MONO} font-size:17px; letter-spacing:.1em; color:{MUTED}; }}
.ts {{ display:inline-flex; align-items:center; gap:10px; font-size:22px; font-weight:700; white-space:nowrap; }}
.ts.w {{ color:{ACC}; }} .ts.w i {{ width:12px; height:12px; border-radius:50%; background:{ACC}; }}
.ts.r {{ color:{MUTED}; }} .ts.r i {{ width:22px; height:22px; border-radius:50%; border:3px solid rgba(255,255,255,.18); border-top-color:{INK}; display:inline-block; }}
.isum {{ display:flex; align-items:baseline; gap:18px; padding:4px 4px 10px; }}
.isum b {{ font-size:60px; font-weight:800; letter-spacing:-.02em; color:{ACC}; }} .isum span {{ font-size:30px; color:{MUTED}; }}
.iv {{ display:grid; grid-template-columns:100px 1fr auto; grid-template-rows:auto auto; gap:2px 16px; padding:20px 22px; border-radius:22px; background:{PANEL2}; }}
.iv .in {{ {MONO} font-size:20px; color:{DIM}; grid-row:1 / 3; align-self:center; }}
.iv .ic {{ font-size:32px; font-weight:600; }} .iv .ia {{ font-size:32px; font-weight:700; text-align:right; font-variant-numeric:tabular-nums; }}
.iv .il {{ grid-column:2 / 4; font-size:24px; color:{MUTED}; }}
.iv.od .il {{ color:{ACC}; font-weight:700; }}
.mh {{ display:flex; gap:18px; font-size:28px; padding:4px 0; border-bottom:1px solid {LINE}; padding-bottom:14px; }}
.mh span {{ color:{DIM}; width:50px; }} .mh b {{ font-weight:600; }}
.mb {{ font-size:36px; line-height:1.45; color:#E4DED6; min-height:420px; padding-top:6px; }}
.mw {{ opacity:0; }}
.appr {{ display:flex; align-items:center; gap:14px; padding-top:10px; border-top:1px solid {LINE}; }}
.aq {{ flex:1; font-size:24px; color:{MUTED}; }}
.btn {{ font-size:26px; font-weight:700; padding:16px 26px; border-radius:18px; white-space:nowrap; }}
.btn.g {{ background:{PANEL2}; color:{INK}; }} .btn.p {{ background:{ACC}; color:#1B0F0A; }}
.cg {{ position:relative; height:560px; background:{PANEL2}; border-radius:22px; overflow:hidden; }}
.cd {{ position:absolute; top:0; height:100%; width:20%; border-left:1px solid {LINE}; }}
""" + "".join(f".cd:nth-child({k + 1}) {{ left:{k * 20}%; }}\n" for k in range(5)) + f"""
.cd span {{ position:absolute; top:12px; left:16px; {MONO} font-size:19px; letter-spacing:.1em; color:{DIM}; }}
.ce {{ position:absolute; width:18.5%; margin-left:-6.5%; border-radius:14px; background:#2A2622; border:2px solid rgba(255,255,255,.06); padding:10px 12px; }}
.ce b {{ font-size:21px; font-weight:700; line-height:1.15; display:block; }}
.ce.mv {{ background:#3A2A22; }}
.prop {{ display:flex; align-items:center; gap:16px; padding:22px; border-radius:22px; background:{ACC_SOFT}; border:1px solid rgba(217,119,87,.4); }}
.prop b {{ font-size:28px; }} .prop span:not(.btn) {{ flex:1; font-size:24px; color:#E4DED6; }}
.pc {{ display:grid; gap:6px; padding:24px 26px; border-radius:22px; background:{PANEL2}; }}
.pc b {{ font-size:34px; font-weight:700; line-height:1.2; }} .pc span {{ font-size:24px; color:{MUTED}; }}
.pc .st {{ {MONO} font-size:18px; letter-spacing:.1em; color:{ACC}; }}

.board {{ position:absolute; left:60px; right:60px; top:330px; display:grid; gap:30px; }}
.bh {{ font-family:"Fraunces", serif; font-size:72px; font-weight:500; letter-spacing:-.02em; line-height:1.05; }}
.bh em {{ font-style:italic; color:{ACC}; }}
.tiles {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.tile {{ display:grid; gap:10px; padding:30px 28px; border-radius:30px; background:{PANEL}; border:1px solid {LINE}; }}
.tile span {{ {MONO} font-size:20px; letter-spacing:.14em; color:{MUTED}; }} .tile b {{ font-size:40px; font-weight:700; line-height:1.15; }}
.tile i {{ font-style:normal; font-size:22px; font-weight:700; color:{ACC}; }}
.you {{ font-size:36px; color:#D8D2CA; }}

.shift {{ position:absolute; left:60px; right:60px; top:300px; display:grid; gap:22px; }}
.col {{ padding:30px 32px; border-radius:36px; background:{PANEL}; border:1px solid {LINE}; display:grid; gap:16px; }}
.ck {{ {MONO} font-size:21px; letter-spacing:.16em; color:{MUTED}; }}
.col.now {{ border-color:rgba(217,119,87,.45); }} .col.now .ck {{ color:{ACC}; }}
.bq {{ justify-self:end; max-width:80%; font-size:32px; padding:18px 24px; border-radius:26px 26px 6px 26px; background:#2A2622; }}
.ba {{ max-width:84%; font-size:32px; padding:18px 24px; border-radius:26px 26px 26px 6px; background:{PANEL2}; }}
.ce2 {{ font-size:26px; color:{DIM}; }}
.arrow {{ justify-self:center; width:4px; height:60px; background:linear-gradient({MUTED}, {ACC}); transform-origin:top; border-radius:2px; }}
.job b {{ display:block; font-size:38px; font-weight:700; margin-bottom:12px; }}
.stp {{ display:flex; align-items:center; gap:16px; font-size:32px; padding:12px 0; color:#E4DED6; }}
.stp i {{ width:30px; height:30px; border-radius:50%; flex:none; }}
.stp i.d {{ background:{OK}; box-shadow:inset 0 0 0 8px {PANEL}; border:2px solid {OK}; }}
.stp i.w {{ border:3px solid {ACC}; }}

.sys {{ position:absolute; left:0; right:0; top:520px; padding:0 70px; display:grid; gap:40px; transform-origin:50% 0; }}
.sys h2 {{ font-family:"Inter", sans-serif; font-weight:800; font-size:128px; line-height:.96; letter-spacing:-.045em; text-transform:uppercase; }}
.sys h2.a {{ color:{ACC}; }}
.flow {{ position:absolute; left:0; top:-120px; width:1080px; height:700px; opacity:.5; }}
.flow path {{ fill:none; stroke:{ACC}; stroke-width:3; stroke-dasharray:1400; stroke-dashoffset:1400; }}
.endc {{ position:absolute; left:70px; right:70px; top:1050px; display:grid; gap:34px; }}
.lock {{ display:flex; align-items:center; gap:22px; opacity:0; }}
.lock .tile {{ width:96px; height:96px; border-radius:24px; background:#201E1D; border:1px solid {LINE}; display:flex; align-items:center; justify-content:center; padding:0; }}
.lock .tile img {{ width:62px; }}
.lock b {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:52px; letter-spacing:.12em; }}
.q2 {{ font-family:"Fraunces", serif; font-size:44px; line-height:1.25; color:#D8D2CA; opacity:0; }}
.fine {{ font-size:22px; line-height:1.45; color:{DIM}; opacity:0; max-width:880px; }}

#camw {{ position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; z-index:15; opacity:0; background:#000; }}
#cam {{ position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; filter:contrast(1.05) saturate(.9) brightness(.97); }}
.cg-top {{ position:absolute; left:0; right:0; top:0; height:640px; background:linear-gradient(180deg, rgba(8,7,6,.82), rgba(8,7,6,0)); }}
.cg-bot {{ position:absolute; left:0; right:0; bottom:0; height:560px; background:linear-gradient(0deg, rgba(8,7,6,.85), rgba(8,7,6,0)); }}
.seam {{ position:absolute; left:0; right:0; bottom:0; height:5px; background:{ACC}; opacity:0; }}
.cap {{ position:absolute; left:60px; right:60px; top:1380px; text-align:center; }}
.cap .cl {{ display:inline; font-family:"Inter", sans-serif; font-weight:800; font-size:70px; line-height:1.08; letter-spacing:-.025em; text-transform:uppercase;
            color:{INK}; text-shadow:0 4px 30px rgba(0,0,0,.85), 0 2px 6px rgba(0,0,0,.6); }}
.cap.split {{ top:978px; }} .cap.split .cl {{ font-size:60px; }} .cap.face {{ top:1520px; }} .cap.face .cl {{ font-size:64px; }}
.cap .cw {{ display:inline-block; }} .cap .cw.a {{ color:{ACC}; }}
"""])

if __name__ == "__main__":
    h = c.page(CSS, "Claude Duet for small business · JT Builds Co", script=True).replace('<script src="assets/gsap.min.js">', '<script src="assets/vendor/gsap.min.js">')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    m, f = mixdown()
    print(f"index.html: {D}s; {len(c.cues)} sounds; with voice {m['lufs']} LUFS / {m['true_peak']} dBTP; no voice {f['lufs']} LUFS")
