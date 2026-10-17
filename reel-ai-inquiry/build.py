"""Generate index.html: captions, motion graphics and B-roll over the AI-inquiry talking head.

    tools/prep_media.sh <talking-head> <demo>   # once: media/ (gitignored)
    python3 build.py && npx hyperframes@0.8.154 check

Every beat is pinned to a word in tools/words.json via W("word", n). Copy, crops,
timing and sound levels all live here. Visual language follows his demo app
(navy + green), captions use Montserrat (his logo's face).

Drop a real detailing clip at media/broll-detailing.mp4 and rebuild: it replaces
the "owner is busy" card as a full-screen cutaway on "working on a car".
"""
import json, html, re, os

WORDS = json.load(open("tools/words.json"))
END = 43.14
r = lambda x: round(x, 3)
esc = html.escape

def W(word, n=1):
    hits = [w for w in WORDS if re.sub(r"[^\w'-]", "", w["text"]).lower() == word.lower()]
    return hits[n - 1]["start"]

# ------------------------------------------------------------------ palette (from the demo app)
NAVY, NAVY2, CARD = "#0A1120", "#0E1A2E", "#111C2E"
INK, MUTED, GREEN, GOLD, RED = "#E8EEF6", "#8CA0B8", "#34D399", "#F5B544", "#F87171"
LINE = "rgba(255,255,255,.08)"

def icon(name, size=28, color="currentColor", sw=2.2):
    p = {
        "bell":  '<path d="M6 9a6 6 0 1 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 15 6 9Z"/><path d="M10 20a2.2 2.2 0 0 0 4 0"/>',
        "wrench":'<path d="M14.7 6.3a4 4 0 0 0 5 5l-8.4 8.4a2.1 2.1 0 0 1-3-3l8.4-8.4a4 4 0 0 0-2-2Z"/><path d="M14.7 6.3 17 4"/>',
        "chat":  '<path d="M5 5h14v10H9l-4 4Z"/>',
        "form":  '<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',
        "db":    '<ellipse cx="12" cy="6" rx="7" ry="2.6"/><path d="M5 6v12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6V6"/><path d="M5 12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6"/>',
        "check": '<path d="M5 12.5l4.2 4.2L19 7"/>',
        "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
        "send":  '<path d="M4 12l16-8-6 16-2.6-6.4Z"/><path d="M11.4 13.6 20 4"/>',
        "user":  '<circle cx="12" cy="8.5" r="3.6"/><path d="M5 20a7 7 0 0 1 14 0"/>',
        "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/>',
        "bolt":  '<path d="M13 3 5 13.5h6L10.5 21 19 10.5h-6Z"/>',
    }[name]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>')

# ------------------------------------------------------------------ beats
SPLIT0, SPLIT1 = 23.867, 37.233            # his own split-screen demo section (measured)
T = dict(
    note=W("customer"), unread=W("read"), note_out=W("message") + 0.35,
    inbox=W("too") - 0.05, lose=W("lose"), respond=W("respond"), fast=W("fast"), inbox_out=9.40,
    busy=W("example"), car=W("car"), req=W("requests"), site=W("quote"),
    sys=W("so") - 0.02, ai=W("ai"), s1=W("responds"), s2=W("collects"), s3=W("organizes"), auto=W("automatically"),
    sys_out=21.85, how=W("here's"), how_out=SPLIT0,
    submit=W("submits"), vehicle=W("vehicle"), service=W("service"), ai2=W("ai", 2), gen=W("generates"),
    whole=W("whole"), autom2=W("automatically", 2), manual=W("enter"),
    comment=W("comment"), typed=W("system", 2), reach=W("reach"),
)
assert T["note"] < 1 and abs(T["typed"] - 39.12) < 0.01, T

# ------------------------------------------------------------------ captions (2-4 word phrases)
WEAK = {"a", "an", "the", "to", "of", "on", "in", "and", "or", "that", "their", "your", "for", "with", "be", "you", "i",
        "i'll", "is", "they", "this", "we", "can", "could", "might", "how", "into", "about", "when", "through", "out", "before", "even", "because", "many", "get"}
POWER = {"lost", "customers", "fast", "detailing", "quote", "ai", "system", "responds", "collects", "organizes",
         "automatically", "personalized", "manually", "comment", "business"}
bare = lambda t: re.sub(r"[^\w'-]", "", t).lower()
def cost(ws, last):
    n = len(" ".join(w["text"] for w in ws)); c = (n - 13) ** 2 / 10
    if n > 19 or len(ws) > 4: c += 500
    if len(ws) == 1 and not last: c += 25
    if bare(ws[-1]["text"]) in WEAK and not last: c += 40
    return c
def split(run):
    best = [0.0] + [1e9] * len(run); prev = [0] * (len(run) + 1)
    for j in range(1, len(run) + 1):
        for i in range(max(0, j - 5), j):
            c = best[i] + cost(run[i:j], j == len(run))
            if c < best[j]: best[j], prev[j] = c, i
    out, j = [], len(run)
    while j > 0: out.append(run[prev[j]:j]); j = prev[j]
    return out[::-1]
runs, cur = [], []
for i, w in enumerate(WORDS):
    if T["how"] - 0.05 <= w["start"] < T["how_out"]:     # the title card says it
        continue
    cur.append(w); nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    if nxt is None or nxt["start"] - w["start"] > 0.7 or re.search(r"[.?!,]$", w["text"]) or (T["how"] - 0.05 <= nxt["start"] < T["how_out"]):
        runs.append(cur); cur = []
chunks = [c for rn in runs for c in split(rn)]
cues = []
for i, c in enumerate(chunks):
    s = c[0]["start"] - 0.05; nxt = chunks[i + 1][0]["start"] - 0.05 if i + 1 < len(chunks) else END
    e = min(c[-1]["end"] + 0.25, nxt - 0.001)
    cues.append((r(s), r(max(e - s, 0.25)), c))
cap_html, cap_js = [], []
for i, (s, d, c) in enumerate(cues):
    spans = " ".join(f'<span class="w{" pw" if bare(w["text"]) in POWER else ""}" id="c{i}w{j}">{esc(re.sub(r"[.,]$", "", w["text"]).upper())}</span>'
                     for j, w in enumerate(c))
    cap_html.append(f'      <div id="cap{i}" class="cap clip" data-start="{s}" data-duration="{d}" data-track-index="20"><div class="ln">{spans}</div></div>')
    cap_js.append(f'tl.fromTo("#cap{i} .ln", {{ y:22, scale:0.92, opacity:0 }}, {{ y:0, scale:1, opacity:1, duration:0.18, ease:"back.out(2)" }}, {s});')
    for j, w in enumerate(c):
        on = max(w["start"], s); off = c[j + 1]["start"] if j + 1 < len(c) else None
        cap_js.append(f'hi("#c{i}w{j}", {r(on)}{"" if off is None else ", " + str(r(off))});')

# ------------------------------------------------------------------ demo crops (source px of the 2160x1218 demo)
PANEL_W, PANEL_H = 1080, 624
def view(rx, ry, rw):
    s = PANEL_W / rw
    return dict(x=r(-rx * s), y=r(-ry * s), scale=r(s))
DEMO = [  # id, file, start, end, [(t_rel, view)]
    ("dA", "demo-form", SPLIT0, T["ai2"] - 0.16, [(0, view(20, 525, 1120)), (T["vehicle"] - SPLIT0 - 0.15, view(40, 700, 800))]),
    ("dB", "demo-ai", T["ai2"] - 0.16, T["whole"] - 0.02, [(0, view(1170, 140, 980)), (T["gen"] - (T["ai2"] - 0.16), view(1170, 372, 980))]),
    ("dC", "demo-saved", T["whole"] - 0.02, SPLIT1, [(0, view(0, 180, 1300)), (T["autom2"] - T["whole"], view(1180, 640, 1000)),
                                                    (2.32, view(0, 82, 1400)), (T["manual"] - T["whole"], view(1200, 440, 960))]),
]
STEPS = [(T["submit"], "1", "Request submitted"), (T["ai2"], "2", "AI writes a personal reply"), (T["whole"], "3", "Saved for follow-up")]

BROLL = os.path.exists("media/broll-detailing.mp4")

# ------------------------------------------------------------------ markup
inbox_rows = [("Jordan M.", "Full detail · 2022 F-150", "2m"), ("Ashley R.", "Interior · Model Y", "18m"),
              ("Chris P.", "Ceramic coat · Civic", "1h"), ("Dana K.", "Exterior · Tahoe", "3h"), ("Sam L.", "Full detail · RAV4", "6h")]
rows_html = "\n".join(
    f'<div class="irow" id="ir{i}"><span class="dot"></span><div class="who"><b>{esc(n)}</b><small>{esc(w)}</small></div>'
    f'<span class="ago">{esc(a)} ago</span><span class="lost">No reply</span></div>' for i, (n, w, a) in enumerate(inbox_rows))
demo_html = "\n".join(
    f'<video id="{i}" class="dv" src="media/{f}.mp4" muted playsinline data-layout-allow-overflow data-start="{r(a)}" '
    f'data-duration="{r(b - a)}" data-media-start="0"></video>' for i, f, a, b, _ in DEMO)
steps_html = "\n".join(f'<div class="step" id="st{n}"><i></i>Step {n} · {esc(t)}</div>' for _, n, t in STEPS)
sys_rows = [("chat", "Responds instantly", "Every inquiry gets a personal reply", "s1"),
            ("form", "Collects their info", "Vehicle, service, preferred date", "s2"),
            ("db", "Organizes the lead", "Saved and ready for follow-up", "s3")]
sys_html = "\n".join(
    f'<div class="srow" id="sr{k}"><span class="snum">{k + 1}</span><span class="sic">{icon(ic, 34, GREEN)}</span>'
    f'<div><b>{esc(a)}</b><small>{esc(b)}</small></div></div>' for k, (ic, a, b, _) in enumerate(sys_rows))

css = f"""
      @font-face {{ font-family:"Inter"; font-weight:400; font-display:block; src:url("assets/fonts/Inter-400-latin.woff2") format("woff2"); }}
      @font-face {{ font-family:"Inter"; font-weight:600; font-display:block; src:url("assets/fonts/Inter-600-latin.woff2") format("woff2"); }}
      @font-face {{ font-family:"Inter"; font-weight:700; font-display:block; src:url("assets/fonts/Inter-700-latin.woff2") format("woff2"); }}
      @font-face {{ font-family:"Montserrat"; font-weight:100 900; font-display:block; src:url("assets/fonts/Montserrat-var-latin.woff2") format("woff2"); }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; font-family:"Inter", sans-serif; color:{INK};
               -webkit-font-smoothing:antialiased; }}
      .full {{ position:absolute; inset:0; overflow:hidden; opacity:0; background:radial-gradient(ellipse 120% 70% at 50% 30%, {NAVY2}, {NAVY} 70%); }}
      .layer {{ position:absolute; inset:0; pointer-events:none; }}
      .eyebrow {{ font-weight:700; font-size:24px; letter-spacing:.24em; color:{GREEN}; }}

      /* captions: Montserrat (his logo's face), the spoken word lights up green */
      .cap {{ position:absolute; left:40px; right:40px; top:1468px; z-index:40; text-align:center; font-family:"Montserrat", sans-serif;
              font-weight:800; font-size:68px; line-height:1.08; letter-spacing:.005em; }}
      .cap .ln {{ display:inline-block; }}
      .w {{ display:inline-block; color:#fff; -webkit-text-stroke:11px rgba(6,10,18,.92); paint-order:stroke fill;
            text-shadow:0 8px 24px rgba(0,0,0,.45); margin:0 .16em; }}
      .w.pw {{ font-size:1.12em; }}

      /* hook: an unread message */
      #nt {{ position:absolute; left:60px; right:60px; top:150px; height:150px; border-radius:34px; background:rgba(18,26,40,.92);
             border:1px solid {LINE}; box-shadow:0 24px 60px rgba(0,0,0,.45); display:flex; align-items:center; gap:22px; padding:0 28px; opacity:0; }}
      #nt .app {{ width:84px; height:84px; border-radius:22px; background:#fff; color:{NAVY}; display:flex; align-items:center; justify-content:center;
                  font-weight:800; font-size:44px; flex:none; }}
      #nt .tx {{ flex:1; min-width:0; }}
      #nt .tx b {{ display:block; font-size:28px; }}
      #nt .tx span {{ display:block; font-size:27px; color:#C9D4E2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
      #nt .tm {{ align-self:flex-start; margin-top:30px; font-size:22px; color:{MUTED}; }}
      #nt-unread {{ position:absolute; right:84px; top:322px; padding:10px 20px; border-radius:999px; background:rgba(248,113,113,.16);
                    color:{RED}; font-weight:700; font-size:24px; display:flex; gap:10px; align-items:center; opacity:0; }}

      /* inbox cutaway */
      #ib-head {{ position:absolute; left:80px; right:80px; top:250px; }}
      #ib-head h2 {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:76px; letter-spacing:-.01em; margin-top:14px; }}
      #ib-count {{ display:inline-flex; margin-top:18px; padding:10px 20px; border-radius:999px; background:rgba(245,181,68,.14); color:{GOLD};
                   font-weight:700; font-size:26px; }}
      #ib-list {{ position:absolute; left:80px; right:80px; top:560px; }}
      .irow {{ position:relative; height:130px; margin-bottom:18px; border-radius:26px; background:{CARD}; border:1px solid {LINE};
               display:flex; align-items:center; gap:22px; padding:0 30px; opacity:0; }}
      .irow .dot {{ width:16px; height:16px; border-radius:50%; background:#5B8DEF; flex:none; }}
      .irow .who b {{ display:block; font-size:32px; }}
      .irow .who small {{ display:block; font-size:24px; color:{MUTED}; margin-top:4px; }}
      .irow .ago {{ margin-left:auto; font-size:24px; color:{MUTED}; }}
      .irow .lost {{ position:absolute; right:30px; top:50%; margin-top:-22px; height:44px; padding:0 18px; border-radius:999px; display:flex;
                     align-items:center; background:rgba(248,113,113,.16); color:{RED}; font-weight:700; font-size:22px; opacity:0; }}
      #ib-clock {{ position:absolute; left:0; right:0; top:1290px; display:flex; justify-content:center; opacity:0; }}
      #ib-clock span {{ display:flex; align-items:center; gap:14px; padding:18px 30px; border-radius:22px; background:{CARD}; border:1px solid {LINE};
                        font-weight:700; font-size:32px; color:{GOLD}; }}

      /* busy owner + the website (top band, his face stays visible) */
      .glass {{ position:absolute; left:60px; right:60px; top:140px; border-radius:32px; background:rgba(12,20,34,.93); border:1px solid {LINE};
                box-shadow:0 30px 80px rgba(0,0,0,.45); overflow:hidden; opacity:0; }}
      #busy {{ height:300px; padding:34px 38px; }}
      #busy .row {{ display:flex; align-items:center; gap:18px; }}
      #busy .row b {{ font-size:34px; }}
      #busy .st {{ margin-left:auto; padding:8px 18px; border-radius:999px; background:rgba(245,181,68,.14); color:{GOLD}; font-weight:700; font-size:22px; }}
      #busy .job {{ margin-top:26px; font-size:28px; color:#C9D4E2; }}
      #busy .bar {{ margin-top:22px; height:14px; border-radius:7px; background:rgba(255,255,255,.08); overflow:hidden; }}
      #busy .bar i {{ display:block; height:100%; width:100%; background:{GOLD}; transform-origin:0 50%; }}
      #ping {{ position:absolute; left:90px; right:90px; top:470px; height:120px; border-radius:28px; background:rgba(18,26,40,.96); border:1px solid {LINE};
               display:flex; align-items:center; gap:20px; padding:0 26px; box-shadow:0 20px 50px rgba(0,0,0,.45); opacity:0; }}
      #ping .app {{ width:66px; height:66px; border-radius:18px; background:#fff; color:{NAVY}; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:34px; }}
      #ping b {{ display:block; font-size:26px; }} #ping span {{ font-size:24px; color:#C9D4E2; }}
      #site {{ height:520px; }}
      #site .bar {{ height:52px; display:flex; align-items:center; gap:10px; padding:0 22px; background:rgba(255,255,255,.04); border-bottom:1px solid {LINE}; }}
      #site .bar i {{ width:13px; height:13px; border-radius:50%; background:rgba(255,255,255,.18); }}
      #site .bar span {{ margin-left:18px; font-size:20px; color:{MUTED}; }}
      #site .vp {{ position:absolute; left:0; right:0; top:52px; bottom:0; overflow:hidden; }}
      #site .vp img {{ position:absolute; left:0; top:0; width:2160px; transform-origin:0 0; }}

      /* AI system cutaway */
      #sy-head {{ position:absolute; left:80px; right:80px; top:250px; }}
      #sy-head h2 {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:92px; line-height:1; letter-spacing:-.015em; margin-top:16px; }}
      #sy-head h2 em {{ font-style:normal; color:{GREEN}; }}
      #sy-list {{ position:absolute; left:80px; right:80px; top:560px; }}
      .srow {{ position:relative; display:flex; align-items:center; gap:24px; height:170px; margin-bottom:22px; padding:0 32px; border-radius:28px;
               background:{CARD}; border:1px solid {LINE}; opacity:0.28; }}
      .snum {{ width:54px; height:54px; border-radius:50%; border:2px solid rgba(255,255,255,.25); display:flex; align-items:center; justify-content:center;
               font-weight:700; font-size:26px; color:{MUTED}; flex:none; }}
      .sic {{ width:70px; height:70px; border-radius:20px; background:rgba(52,211,153,.12); display:flex; align-items:center; justify-content:center; flex:none; }}
      .srow b {{ display:block; font-size:38px; }} .srow small {{ display:block; font-size:25px; color:{MUTED}; margin-top:6px; }}
      #sy-auto {{ position:absolute; left:0; right:0; top:1222px; display:flex; justify-content:center; opacity:0; }}
      #sy-auto span {{ display:flex; align-items:center; gap:14px; padding:20px 34px; border-radius:999px; background:{GREEN}; color:#052016;
                       font-family:"Montserrat", sans-serif; font-weight:800; font-size:36px; letter-spacing:.06em; }}

      /* title card */
      #how .t {{ position:absolute; left:0; right:0; top:760px; text-align:center; font-family:"Montserrat", sans-serif; font-weight:900;
                 font-size:118px; line-height:.98; letter-spacing:-.01em; }}
      #how .t span {{ display:block; }}
      #how .t .g {{ color:{GREEN}; }}

      /* demo panel: covers his own low-res strip (y 0-620) with sharp crops of the demo */
      #dp {{ position:absolute; left:0; top:0; width:{PANEL_W}px; height:{PANEL_H}px; overflow:hidden; background:{NAVY}; clip-path:inset(0% 0% 100% 0%);
             box-shadow:0 6px 0 rgba(52,211,153,.0); }}
      #dp::after {{ content:""; position:absolute; left:0; right:0; bottom:0; height:4px; background:{GREEN}; opacity:.85; }}
      .dv {{ position:absolute; left:0; top:0; width:2160px; height:1218px; transform-origin:0 0; }}
      .step {{ position:absolute; left:28px; top:{PANEL_H + 18}px; z-index:12; height:52px; display:flex; align-items:center; gap:12px; padding:0 20px; border-radius:999px;
               background:rgba(10,17,32,.9); border:1px solid rgba(52,211,153,.35); font-weight:700; font-size:24px; color:{INK}; opacity:0; }}
      .step i {{ width:12px; height:12px; border-radius:50%; background:{GREEN}; }}

      /* CTA */
      #cm {{ position:absolute; left:80px; right:80px; top:200px; height:118px; border-radius:59px; background:rgba(12,20,34,.94); border:1px solid {LINE};
             display:flex; align-items:center; gap:18px; padding:0 18px 0 22px; box-shadow:0 24px 60px rgba(0,0,0,.45); opacity:0; }}
      .av {{ width:72px; height:72px; border-radius:50%; background:rgba(255,255,255,.1); display:flex; align-items:center; justify-content:center; flex:none; }}
      #cm-f {{ flex:1; position:relative; height:60px; font-family:"Montserrat", sans-serif; font-weight:800; font-size:42px; letter-spacing:.06em; }}
      #cm-ph {{ position:absolute; left:0; top:8px; font-family:"Inter", sans-serif; font-weight:400; font-size:32px; letter-spacing:0; color:#71809A; }}
      #cm-in {{ position:absolute; left:0; top:4px; }}
      .ch {{ display:none; }}
      .caret {{ display:inline-block; width:4px; height:40px; margin-left:3px; vertical-align:-4px; background:{GREEN}; opacity:0; }}
      #cm-go {{ width:80px; height:80px; border-radius:50%; background:{GREEN}; display:flex; align-items:center; justify-content:center; flex:none; }}
      #lk {{ position:absolute; left:250px; top:150px; width:580px; height:440px; border-radius:36px; background:rgba(32,30,29,.97);
             box-shadow:0 30px 80px rgba(0,0,0,.45); opacity:0; }}
      #lk .k {{ position:absolute; left:0; right:0; top:36px; text-align:center; font-family:"Montserrat", sans-serif; font-weight:700; font-size:22px;
                letter-spacing:.3em; color:#A09D9B; }}
      #lk .mk {{ position:absolute; left:50%; top:80px; width:236px; height:199px; margin-left:-118px; }}
      #lk .mk img {{ width:100%; height:100%; display:block; }}
      #lk .wd {{ position:absolute; left:0; right:0; top:304px; text-align:center; font-family:"Montserrat", sans-serif; font-weight:800; font-size:56px;
                 letter-spacing:.035em; white-space:nowrap; }}
      #lk .wd b {{ color:#fff; font-weight:800; }} #lk .wd span {{ color:#A09D9B; margin-left:.28em; }}
      #lk .rt {{ position:absolute; left:0; right:0; top:384px; text-align:center; font-size:24px; font-weight:600; color:#D4D4D8; }}
"""

def typed(id_, text):
    return (f'<span id="{id_}">' + "".join(f'<span class="ch" id="{id_}-{i}">{esc(c)}</span>' for i, c in enumerate(text))
            + f'<span class="caret" id="{id_}-caret"></span></span>')

body = f"""
      <video id="a-roll" class="clip" src="media/base.mp4" muted playsinline data-start="0" data-duration="{END}" data-track-index="0"
             style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>
      <audio id="a-roll-audio" src="media/base.mp4" data-start="0" data-duration="{END}" data-track-index="1" data-volume="1"></audio>

      <!-- 1 hook: a message nobody reads -->
      <div id="hook" class="layer clip" data-start="{r(T['note'] - 0.1)}" data-duration="{r(T['note_out'] - T['note'] + 0.5)}" data-track-index="2">
        <div id="nt"><span class="app">G</span><div class="tx"><b>New quote request</b><span>"Hey! How much for a full detail on my truck?"</span></div><span class="tm">now</span></div>
        <div id="nt-unread">{icon("clock", 24, RED)} Unread</div>
      </div>

      <!-- 2 cutaway: an inbox nobody answers -->
      <div id="inbox" class="full clip" data-start="{r(T['inbox'])}" data-duration="{r(T['inbox_out'] - T['inbox'])}" data-track-index="3">
        <div id="ib-head"><div class="eyebrow">QUOTE REQUESTS</div><h2>Waiting on a reply</h2><div id="ib-count">5 unanswered</div></div>
        <div id="ib-list">{rows_html}</div>
        <div id="ib-clock"><span>{icon("clock", 34, GOLD)} Every hour, they shop around</span></div>
      </div>

      <!-- 3 the owner is busy; a request comes in through the website -->
      <div id="busyl" class="layer clip" data-start="{r(T['busy'] - 0.1)}" data-duration="{r(T['sys'] - T['busy'] + 0.1)}" data-track-index="4">
        <div id="busy" class="glass"><div class="row">{icon("wrench", 36, GOLD)}<b>Owner · in the bay</b><span class="st">Busy</span></div>
          <div class="job">Working on: full interior + exterior detail</div><div class="bar"><i id="bar"></i></div></div>
        <div id="ping"><span class="app">G</span><div><b>New quote request</b><span>via your website · just now</span></div></div>
        <div id="site" class="glass"><div class="bar"><i></i><i></i><i></i><span>gleamdetail.co/quote</span></div>
          <div class="vp"><img id="site-img" src="media/demo-site.png" alt="The detailing website's quote form" data-layout-allow-overflow></div></div>
      </div>
{f'''      <video id="broll" class="clip" src="media/broll-detailing.mp4" muted playsinline data-start="{r(T['busy'] - 0.05)}" data-duration="{r(T['req'] - T['busy'])}"
             data-track-index="5" style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>''' if BROLL else ''}

      <!-- 4 cutaway: the AI system, in the demo's own visual language -->
      <div id="sys" class="full clip" data-start="{r(T['sys'])}" data-duration="{r(T['sys_out'] - T['sys'])}" data-track-index="6">
        <div id="sy-head"><div class="eyebrow">AI LEAD RESPONSE</div><h2>One <em>AI system</em><br>for every inquiry</h2></div>
        <div id="sy-list">{sys_html}</div>
        <div id="sy-auto" data-layout-allow-overflow><span>{icon("bolt", 34, "#052016", 2.4)} AUTOMATIC</span></div>
      </div>

      <!-- 5 title -->
      <div id="how" class="full clip" data-start="{r(T['how'] - 0.08)}" data-duration="{r(T['how_out'] - T['how'] + 0.08)}" data-track-index="7">
        <div class="t"><span>HERE'S HOW</span><span class="g">IT WORKS</span></div>
      </div>

      <!-- 6 the real demo, sharp, over his split-screen strip -->
      <div id="dp">
{demo_html}
      </div>
      <div id="steps">
{steps_html}
      </div>

      <!-- 7 CTA + his logo -->
      <div id="ctal" class="layer clip" data-start="{r(T['comment'] - 0.1)}" data-duration="{r(END - T['comment'] + 0.1)}" data-track-index="9">
        <div id="cm"><span class="av">{icon("user", 36, MUTED)}</span><div id="cm-f"><span id="cm-ph">Add a comment…</span><span id="cm-in">{typed("cin", "SYSTEM")}</span></div>
          <span id="cm-go">{icon("send", 36, "#052016", 2.4)}</span></div>
        <div id="lk"><div class="k">AI SYSTEMS BY</div><div class="mk"><img src="assets/brand/jt-mark.png" alt="JT Builds Co."></div>
          <div class="wd"><b>BUILDS</b><span>CO.</span></div><div class="rt">Comment "SYSTEM" · I'll reach out</div></div>
      </div>

{chr(10).join(cap_html)}
__AUDIO__"""

# ------------------------------------------------------------------ timeline
js = []; a = js.append
a('function hi(sel, on, off) {')
a(f'  tl.set(sel, {{ color:"{GREEN}" }}, on); tl.fromTo(sel, {{ scale:1.06 }}, {{ scale:1, duration:0.16, ease:"power2.out" }}, on);')
a('  if (off !== undefined) tl.set(sel, { color:"#ffffff" }, off);')
a('}')
js += cap_js

# 1 hook
n0 = T["note"]
a(f'tl.fromTo("#nt", {{ opacity:0, y:-60, scale:0.96 }}, {{ opacity:1, y:0, scale:1, duration:0.45, ease:"back.out(1.6)" }}, {r(n0)});')
a(f'tl.fromTo("#nt-unread", {{ opacity:0, scale:0.8 }}, {{ opacity:1, scale:1, duration:0.3, ease:"back.out(2)" }}, {r(T["unread"])});')
a(f'tl.to("#nt .tx span", {{ color:"#9AA6B6", duration:0.5 }}, {r(T["unread"])});')
a(f'tl.to("#nt .app", {{ opacity:0.55, duration:0.5 }}, {r(T["unread"])});')
a(f'tl.to(["#nt", "#nt-unread"], {{ opacity:0, y:-50, duration:0.28, ease:"power2.in" }}, {r(T["note_out"] - 0.28)});')

# 2 inbox cutaway
ib = T["inbox"]
a(f'tl.fromTo("#inbox", {{ opacity:0, scale:1.06 }}, {{ opacity:1, scale:1, duration:0.32, ease:"power3.out" }}, {r(ib)});')
a(f'tl.fromTo("#ib-head > *", {{ opacity:0, y:24 }}, {{ opacity:1, y:0, duration:0.4, ease:"power3.out", stagger:0.07 }}, {r(ib + 0.08)});')
a(f'tl.fromTo(".irow", {{ opacity:0, y:40 }}, {{ opacity:1, y:0, duration:0.38, ease:"back.out(1.4)", stagger:0.14 }}, {r(ib + 0.3)});')
for i in range(len(inbox_rows)):
    t = T["lose"] + 0.18 * i
    a(f'tl.to("#ir{i} .ago", {{ opacity:0, duration:0.12 }}, {r(t - 0.1)});')
    a(f'tl.to("#ir{i} .lost", {{ opacity:1, duration:0.2 }}, {r(t + 0.04)});')
    a(f'tl.to("#ir{i}", {{ opacity:0.38, duration:0.5 }}, {r(t + 0.45)});')
a(f'tl.fromTo("#ib-clock", {{ opacity:0, y:20 }}, {{ opacity:1, y:0, duration:0.4, ease:"back.out(1.6)" }}, {r(T["respond"])});')
a(f'tl.to("#inbox", {{ opacity:0, scale:0.97, duration:0.18, ease:"power2.in" }}, {r(T["inbox_out"] - 0.18)});')

# 3 busy owner -> request -> website
b0 = T["busy"]
if not BROLL:
    a(f'tl.fromTo("#busy", {{ opacity:0, y:-30 }}, {{ opacity:1, y:0, duration:0.45, ease:"back.out(1.5)" }}, {r(b0)});')
    a(f'tl.fromTo("#bar", {{ scaleX:0.2 }}, {{ scaleX:0.68, duration:{r(T["req"] - b0)}, ease:"none" }}, {r(b0)});')
a(f'tl.fromTo("#ping", {{ opacity:0, y:-24, scale:0.95 }}, {{ opacity:1, y:0, scale:1, duration:0.4, ease:"back.out(1.8)" }}, {r(T["req"])});')
a(f'tl.to(["#busy", "#ping"], {{ opacity:0, y:-20, duration:0.22, ease:"power2.in" }}, {r(T["site"] - 0.22)});')
SITE_V = view(0, 150, 1150); SITE_V2 = view(0, 430, 1150)
a(f'tl.fromTo("#site", {{ opacity:0, y:40, scale:0.96 }}, {{ opacity:1, y:0, scale:1, duration:0.45, ease:"back.out(1.4)" }}, {r(T["site"])});')
a(f'tl.fromTo("#site-img", {{ x:{SITE_V["x"] * 960 / 1080:.1f}, y:{SITE_V["y"] * 960 / 1080:.1f}, scale:{SITE_V["scale"] * 960 / 1080:.4f} }}, '
  f'{{ x:{SITE_V2["x"] * 960 / 1080:.1f}, y:{SITE_V2["y"] * 960 / 1080:.1f}, scale:{SITE_V2["scale"] * 960 / 1080:.4f}, duration:{r(T["sys"] - T["site"] - 0.7)}, ease:"sine.inOut", immediateRender:false }}, {r(T["site"] + 0.6)});')

# 4 system cutaway
sy = T["sys"]
a(f'tl.fromTo("#sys", {{ opacity:0, scale:1.06 }}, {{ opacity:1, scale:1, duration:0.32, ease:"power3.out" }}, {r(sy)});')
a(f'tl.fromTo("#sy-head > *", {{ opacity:0, y:26 }}, {{ opacity:1, y:0, duration:0.45, ease:"power3.out", stagger:0.1 }}, {r(T["ai"] - 0.3)});')
a(f'tl.fromTo(".srow", {{ y:30 }}, {{ y:0, duration:0.4, ease:"power3.out", stagger:0.06 }}, {r(sy + 0.1)});')
for k, (_, _, _, key) in enumerate(sys_rows):
    t = T[key]
    a(f'tl.to("#sr{k}", {{ opacity:1, borderColor:"rgba(52,211,153,.55)", duration:0.25 }}, {r(t)});')
    a(f'tl.fromTo("#sr{k}", {{ scale:1.04 }}, {{ scale:1, duration:0.35, ease:"back.out(2)" }}, {r(t)});')
    a(f'tl.to("#sr{k} .snum", {{ backgroundColor:"{GREEN}", borderColor:"{GREEN}", color:"#052016", duration:0.2 }}, {r(t)});')
a(f'tl.fromTo("#sy-auto", {{ opacity:0, scale:0.7 }}, {{ opacity:1, scale:1, duration:0.42, ease:"back.out(2.2)" }}, {r(T["auto"])});')
a(f'tl.to("#sys", {{ opacity:0, duration:0.18, ease:"power2.in" }}, {r(T["sys_out"] - 0.18)});')

# 5 title
hw = T["how"]
a(f'tl.fromTo("#how", {{ opacity:0 }}, {{ opacity:1, duration:0.12 }}, {r(hw - 0.08)});')
a(f'tl.fromTo("#how .t span", {{ opacity:0, scale:1.6, filter:"blur(14px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.4, ease:"expo.out", stagger:0.16 }}, {r(hw)});')
a(f'tl.to("#how .t", {{ scale:1.08, duration:{r(T["how_out"] - hw - 0.4)}, ease:"none" }}, {r(hw + 0.4)});')

# 6 demo panel
a(f'tl.fromTo("#dp", {{ clipPath:"inset(0% 0% 100% 0%)" }}, {{ clipPath:"inset(0% 0% 0% 0%)", duration:0.38, ease:"power3.out" }}, {SPLIT0});')
for i, f, s0, s1, views in DEMO:
    v0 = views[0][1]
    a(f'tl.set("#{i}", {{ x:{v0["x"]}, y:{v0["y"]}, scale:{v0["scale"]} }}, 0);')
    if i != "dA":
        a(f'tl.fromTo("#{i}", {{ opacity:0 }}, {{ opacity:1, duration:0.22, ease:"none" }}, {r(s0)});')
    for (t0, va), (t1, vb) in zip(views, views[1:]):
        a(f'tl.to("#{i}", {{ x:{vb["x"]}, y:{vb["y"]}, scale:{vb["scale"]}, duration:0.6, ease:"power3.inOut" }}, {r(s0 + t1)});')
for k, (t, n, _) in enumerate(STEPS):
    a(f'tl.fromTo("#st{n}", {{ opacity:0, x:-24 }}, {{ opacity:1, x:0, duration:0.32, ease:"back.out(1.8)" }}, {r(t)});')
    if k + 1 < len(STEPS):
        a(f'tl.to("#st{n}", {{ opacity:0, duration:0.15 }}, {r(STEPS[k + 1][0] - 0.12)});')
a(f'tl.to("#dp", {{ clipPath:"inset(0% 0% 100% 0%)", duration:0.3, ease:"power3.in" }}, {r(SPLIT1 - 0.3)});')
a(f'tl.to("#st{STEPS[-1][1]}", {{ opacity:0, x:-24, duration:0.2, ease:"power2.in" }}, {r(SPLIT1 - 0.3)});')

# 7 CTA
cm = T["comment"]
a(f'tl.fromTo("#cm", {{ opacity:0, y:-30, scale:0.95 }}, {{ opacity:1, y:0, scale:1, duration:0.42, ease:"back.out(1.6)" }}, {r(cm)});')
a(f'tl.set("#cm-ph", {{ opacity:0 }}, {r(T["typed"] - 0.02)});')
a(f'tl.set("#cin-caret", {{ opacity:1 }}, {r(T["typed"] - 0.05)});')
for i in range(6):
    a(f'tl.set("#cin-{i}", {{ display:"inline" }}, {r(T["typed"] + i * 0.07)});')
post = T["typed"] + 0.62
a(f'tl.set("#cin-caret", {{ opacity:0 }}, {r(post)});')
a(f'tl.to("#cm-go", {{ scale:0.86, duration:0.08 }}, {r(post - 0.04)}); tl.to("#cm-go", {{ scale:1, duration:0.25, ease:"back.out(2)" }}, {r(post + 0.04)});')
a(f'tl.to("#cm", {{ opacity:0, y:-24, duration:0.25, ease:"power2.in" }}, {r(T["reach"] - 0.05)});')
a(f'tl.fromTo("#lk", {{ opacity:0, scale:0.9, filter:"blur(10px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.55, ease:"expo.out" }}, {r(T["reach"] + 0.12)});')
a(f'tl.fromTo("#lk .mk img", {{ clipPath:"inset(100% 0% 0% 0%)", y:16 }}, {{ clipPath:"inset(0% 0% 0% 0%)", y:0, duration:0.5, ease:"power3.out" }}, {r(T["reach"] + 0.22)});')

# ------------------------------------------------------------------ sound
VOL = {"riser-s": 0.85, "riser-m": 0.85, "riser-l": 0.75, "popup": 0.6, "bubble": 0.5, "bubble-in": 0.45, "keys": 0.85,
       "click": 0.6, "notification": 0.42, "land": 0.5}
ONSET = {"notification.mp3": 0.06}
RS, RM, RL = 0.45, 0.75, 1.25
S = []
def add(i, f, t, d, v=None):
    kind = f.rsplit(".", 1)[0]
    S.append((i, f, r(max(t, 0)), r(d), VOL[kind] if v is None else v, ONSET.get(f, 0.0)))
add("n-hook", "notification.mp3", n0, 1.1, 0.62);       add("p-hook", "popup.wav", n0, 0.22)
add("r-inbox", "riser-m.wav", ib - RM, RM);            add("l-inbox", "land.wav", ib, 0.8)
for i in range(len(inbox_rows)):
    add(f"b-ir{i}", "bubble.wav", ib + 0.3 + 0.14 * i, 0.18, 0.38)
add("p-clock", "popup.wav", T["respond"], 0.22, 0.5)
add("r-busy", "riser-s.wav", b0 - RS, RS);             add("p-busy", "popup.wav", b0, 0.22)
add("n-ping", "notification.mp3", T["req"], 1.1, 0.4)
add("r-site", "riser-s.wav", T["site"] - RS, RS);      add("p-site", "popup.wav", T["site"], 0.22)
add("r-sys", "riser-m.wav", sy - RM, RM);              add("l-sys", "land.wav", sy, 0.8)
for k, (_, _, _, key) in enumerate(sys_rows):
    add(f"p-s{k}", "popup.wav", T[key], 0.22)
add("l-auto", "land.wav", T["auto"], 0.8, 0.45);       add("p-auto", "popup.wav", T["auto"], 0.22)
add("r-how", "riser-l.wav", hw - RL, RL);              add("l-how", "land.wav", hw, 0.8, 0.55)
add("r-demo", "riser-s.wav", SPLIT0 - RS, RS);         add("p-demo", "popup.wav", SPLIT0, 0.22)
add("k-form", "keys.wav", SPLIT0 + 0.3, 1.05, 0.6)
for t, n, _ in STEPS:
    add(f"b-st{n}", "bubble.wav", t, 0.18)
add("r-cm", "riser-s.wav", cm - RS, RS);               add("p-cm", "popup.wav", cm, 0.22)
add("k-cin", "keys.wav", T["typed"], 0.5);              add("c-cin", "click.mp3", post - 0.04, 0.3)
add("r-lk", "riser-m.wav", T["reach"] + 0.12 - RM, RM); add("l-lk", "land.wav", T["reach"] + 0.12, 0.8, 0.45)
audio = "\n".join(f'      <audio id="{i}" src="assets/sfx/{f}" data-start="{t}" data-duration="{d}" data-media-start="{ms}" data-track-index="{30 + n}" data-volume="{v}"></audio>'
                  for n, (i, f, t, d, v, ms) in enumerate(S))

page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="vendor/gsap.min.js"></script>
    <style>{css}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1080" data-height="1920">
{body.replace("__AUDIO__", audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join("      " + l for l in js)}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open("index.html", "w").write(page)
print(f"index.html: {len(cues)} caption cues, {len(S)} sounds; broll={'yes' if BROLL else 'no (card)'}")
for s, d, c in cues: print(f"  {s:6.2f} {d:4.2f}  {' '.join(w['text'] for w in c)}")
