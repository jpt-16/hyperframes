"""Generate index.html: motion graphics over the AI-quote talking head.

    python3 build.py && npx hyperframes@0.8.154 check

The footage (base.mp4, with his own burned-in captions) plays untouched; every
graphic lives in the band above his eyes (y 150-650) on a soft dark fade, so his
face and captions (y 1390-1475) stay clear. Every beat is pinned to a word in
tools/words.json via W("word", n). Timings, copy and levels are all in this file.
"""
import json, html, re

WORDS = json.load(open("tools/words.json"))
END = 39.6

def W(word, n=1):
    hits = [w for w in WORDS if re.sub(r"[^\w']", "", w["text"]).lower() == word.lower()]
    return hits[n - 1]["start"]
r = lambda x: round(x, 3)
esc = html.escape

# ----------------------------------------------------------------- palette
PINK = "#FF0065"        # his caption highlight
GREEN = "#2BD47D"
INK = "#F5F5F7"; MUTED = "#A1A1AA"; LINE = "rgba(255,255,255,.09)"

# ----------------------------------------------------------------- icons (inline SVG, 24px grid)
def icon(name, size=28, color="currentColor", sw=2.2):
    p = {
        "bell":  '<path d="M6 9a6 6 0 1 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 15 6 9Z"/><path d="M10 20a2.2 2.2 0 0 0 4 0"/>',
        "wrench":'<path d="M14.7 6.3a4 4 0 0 0 5 5l-8.4 8.4a2.1 2.1 0 0 1-3-3l8.4-8.4a4 4 0 0 0-2-2Z"/><path d="M14.7 6.3 17 4"/>',
        "spark": '<path d="M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8Z"/><path d="M18.5 16.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7Z"/>',
        "check": '<path d="M5 12.5l4.2 4.2L19 7"/>',
        "moon":  '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
        "send":  '<path d="M4 12l16-8-6 16-2.6-6.4Z"/><path d="M11.4 13.6 20 4"/>',
        "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/>',
        "user":  '<circle cx="12" cy="8.5" r="3.6"/><path d="M5 20a7 7 0 0 1 14 0"/>',
        "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
        "inbox": '<path d="M4 13l2.5-7h11L20 13v5H4Z"/><path d="M4 13h4.5l1 2h5l1-2H20"/>',
    }[name]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>')

# ----------------------------------------------------------------- beats (all from the transcript)
T = dict(
    hook=W("systems"), hook_pill=W("best"), hook_out=3.70,
    panel_in=W("customer"), name=W("fills") + 0.02, phone=W("form") - 0.05, msg=W("business"), submit=W("quote"),
    wait=W("owner"), busy=W("working"), hours0=W("sitting"), hours1=W("hours") + 0.30,
    ai=W("ai", 2), ai_hi=W("respond"), replied=W("immediately"),
    q_vehicle=W("what"), a_vehicle=W("have") + 0.0, q_service=W("what", 2), a_service=W("need"),
    q_when=W("when"), a_when=W("available") + 0.12,
    lead=W("organize"), sent=W("owner", 2), follow=W("follow"),
    inbox=W("inquiry"), busy2=W("busy", 2), closed=W("business", 2), late=W("business", 2) + 0.24,
    panel_out=W("that's") - 0.12,
    kicker=W("system", 2), brand=W("jt"), tag1=W("real"), tag2=W("real", 2), brand_out=33.25,
    ask=W("systems", 2), comment=W("comment"), typed=W("system", 3), post=W("below"), dm=W("dm"),
)
print({k: r(v) for k, v in T.items()})

# chat script: (time, who, text)
CHAT = [
    (T["ai_hi"] - 0.02, "ai", "Hey Jordan, thanks for reaching out!"),
    (T["q_vehicle"],    "ai", "What vehicle do you have?"),
    (T["a_vehicle"],    "me", "2021 Ford F-150"),
    (T["q_service"],    "ai", "Which service do you need?"),
    (T["a_service"],    "me", "Full interior + exterior"),
    (T["q_when"],       "ai", "When works best for you?"),
    (T["a_when"],       "me", "Saturday morning"),
]
BUB_H, BUB_GAP, CHAT_AREA = 70, 14, 300

# ----------------------------------------------------------------- markup
def typed(id_, text, cls=""):
    chars = "".join(f'<span class="ch" id="{id_}-{i}">{esc(c) if c != " " else "&nbsp;"}</span>' for i, c in enumerate(text))
    return f'<span class="typed {cls}" id="{id_}">{chars}<span class="caret" id="{id_}-caret"></span></span>'
FORM = [("Name", "f-name", "Jordan M.", T["name"]), ("Phone", "f-phone", "(555) 214-0193", T["phone"]),
        ("Message", "f-msg", "How much for a full detail?", T["msg"])]
form_rows = "\n".join(f'''          <div class="field"><div class="flabel">{esc(l)}</div><div class="finput">{typed(i, v)}</div></div>'''
                      for l, i, v, _ in FORM)

bubbles = []
for k, (t, who, text) in enumerate(CHAT):
    y = k * (BUB_H + BUB_GAP)
    bubbles.append(f'<div class="bub {who}" id="b{k}" style="top:{y}px">{esc(text)}</div>')

LEAD = [("user", "Customer", "Jordan M. · (555) 214-0193"), ("spark", "Vehicle", "2021 Ford F-150"),
        ("check", "Service", "Full interior + exterior"), ("clock", "Availability", "Saturday morning")]
lead_rows = "\n".join(f'<div class="lrow" id="l{i}"><span class="lic">{icon(ic, 26, PINK)}</span><span class="lk">{esc(k)}</span><span class="lv">{esc(v)}</span></div>'
                      for i, (ic, k, v) in enumerate(LEAD))

INBOX = [("Jordan M.", "F-150 · full detail", "4s"), ("Ashley R.", "Model Y · interior", "6s"), ("Marcus T.", "Tahoe · ceramic", "5s")]
LATE = ("Dana K.", "Civic · exterior", "5s")
def irow(id_, name, what, secs, y, extra=""):
    return (f'<div class="irow" id="{id_}" style="top:{y}px"><span class="iav">{esc(name[0])}</span>'
            f'<span class="iname">{esc(name)}<small>{esc(what)}</small></span>'
            f'<span class="ibadge">{icon("check", 22, GREEN, 2.6)} Replied in {secs}{extra}</span></div>')
ROW_H = 78
inbox_rows = "\n".join(irow(f"i{i}", n, w, s, i * ROW_H) for i, (n, w, s) in enumerate(INBOX))
inbox_rows += "\n" + irow("i-late", *LATE, 0)

PANEL_TOP, PANEL_H = 168, 470
html_out = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family:"Inter"; font-weight:400; font-display:block; src:url("assets/fonts/Inter-400-latin.woff2") format("woff2"); }}
      @font-face {{ font-family:"Inter"; font-weight:600; font-display:block; src:url("assets/fonts/Inter-600-latin.woff2") format("woff2"); }}
      @font-face {{ font-family:"Inter"; font-weight:700; font-display:block; src:url("assets/fonts/Inter-700-latin.woff2") format("woff2"); }}
      @font-face {{ font-family:"Fraunces"; font-weight:400 900; font-display:block; src:url("assets/fonts/Fraunces-var-latin.woff2") format("woff2"); }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000;
               font-family:"Inter", sans-serif; color:{INK}; -webkit-font-smoothing:antialiased; }}
      #scrim {{ position:absolute; inset:0; z-index:5; pointer-events:none; opacity:0;
                background:linear-gradient(180deg, rgba(7,7,9,.80) 0%, rgba(7,7,9,.62) 18%, rgba(7,7,9,.28) 32%, rgba(7,7,9,0) 42%); }}
      .layer {{ position:absolute; inset:0; z-index:10; }}

      /* hook */
      #hook-word {{ position:absolute; left:0; right:0; top:236px; text-align:center; font-family:"Fraunces", serif;
                    font-weight:800; font-size:150px; line-height:1; letter-spacing:-.02em; font-variation-settings:"opsz" 144; }}
      #hook-word .w {{ display:inline-block; }}
      #hook-line {{ position:absolute; left:50%; top:404px; width:360px; height:7px; margin-left:-180px; border-radius:4px; background:{PINK}; }}
      #hook-pill {{ position:absolute; left:0; right:0; top:448px; display:flex; justify-content:center; opacity:0; }}
      #hook-pill span {{ white-space:nowrap; font-weight:600; font-size:32px; padding:12px 26px; border-radius:999px;
                         background:rgba(255,255,255,.1); border:1px solid {LINE}; }}

      /* the panel: one card that carries the whole system demo */
      #panel {{ position:absolute; left:70px; top:{PANEL_TOP}px; width:940px; height:{PANEL_H}px; border-radius:30px; overflow:hidden;
                background:rgba(16,16,20,.90); border:1px solid {LINE};
                box-shadow:0 30px 80px rgba(0,0,0,.45), 0 2px 0 rgba(255,255,255,.04) inset; opacity:0; }}
      .scr {{ position:absolute; inset:0; padding:30px 36px; opacity:0; }}
      .hd {{ display:flex; align-items:center; gap:16px; height:56px; }}
      .hd .ttl {{ font-weight:700; font-size:34px; letter-spacing:-.01em; }}
      .hd .sub {{ font-weight:400; font-size:24px; color:{MUTED}; margin-left:auto; }}
      .ico {{ width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center; background:rgba(255,0,101,.14); color:{PINK}; }}

      /* form */
      .field {{ display:flex; align-items:center; height:76px; border-bottom:1px solid {LINE}; }}
      .flabel {{ width:170px; font-size:26px; font-weight:600; color:{MUTED}; }}
      .finput {{ flex:1; font-size:30px; font-weight:600; white-space:nowrap; }}
      .ch {{ display:none; }}
      .caret {{ display:inline-block; width:3px; height:32px; margin-left:2px; vertical-align:-5px; background:{PINK}; opacity:0; }}
      #btn {{ position:absolute; left:36px; right:36px; bottom:30px; height:82px; border-radius:20px; background:{PINK};
              display:flex; align-items:center; justify-content:center; gap:12px; font-weight:700; font-size:32px; color:#fff; }}
      #btn .done {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:12px; opacity:0; background:{GREEN}; border-radius:20px; color:#06140C; }}

      /* waiting */
      #w-from {{ margin:22px 0 0 68px; font-size:28px; color:{MUTED}; }}
      #w-from b {{ color:{INK}; font-weight:600; }}
      #w-busy {{ display:inline-flex; align-items:center; gap:12px; margin:22px 0 0 0; padding:12px 20px; border-radius:14px;
                 background:rgba(255,255,255,.06); border:1px solid {LINE}; font-size:26px; font-weight:600; color:#E4E4E7; opacity:0; }}
      #w-timer {{ position:absolute; left:36px; right:36px; bottom:30px; height:120px; border-radius:22px; background:rgba(255,255,255,.04);
                  border:1px solid {LINE}; display:flex; align-items:center; padding:0 30px; gap:18px; }}
      #w-timer .lab {{ font-size:26px; font-weight:600; color:{MUTED}; }}
      #w-count {{ margin-left:auto; font-weight:700; font-size:58px; letter-spacing:-.01em; font-variant-numeric:tabular-nums; }}
      #w-dot {{ width:14px; height:14px; border-radius:50%; background:#F2B33D; }}

      /* chat */
      .ai-av {{ width:52px; height:52px; border-radius:50%; display:flex; align-items:center; justify-content:center;
                background:linear-gradient(135deg, {PINK}, #FF5E9C); color:#fff; }}
      .online {{ display:inline-flex; align-items:center; gap:8px; font-size:22px; font-weight:600; color:{GREEN}; margin-left:6px; }}
      .online i {{ width:10px; height:10px; border-radius:50%; background:{GREEN}; }}
      #replied {{ margin-left:auto; display:inline-flex; align-items:center; gap:8px; padding:8px 16px; border-radius:999px;
                  background:rgba(43,212,125,.12); color:{GREEN}; font-weight:700; font-size:22px; opacity:0; }}
      #chat {{ position:absolute; left:36px; right:36px; top:120px; height:{CHAT_AREA + 20}px; overflow:hidden; }}
      #track {{ position:absolute; left:0; right:0; top:0; }}
      .bub {{ position:absolute; height:{BUB_H}px; display:flex; align-items:center; padding:0 26px; border-radius:24px;
              font-size:28px; font-weight:600; white-space:nowrap; opacity:0; }}
      .bub.ai {{ left:0; background:rgba(255,255,255,.08); border-bottom-left-radius:8px; transform-origin:0% 100%; }}
      .bub.me {{ right:0; background:{PINK}; color:#fff; border-bottom-right-radius:8px; transform-origin:100% 100%; }}
      #typing {{ position:absolute; left:0; top:0; height:{BUB_H}px; padding:0 24px; display:flex; align-items:center; gap:8px;
                 border-radius:24px; background:rgba(255,255,255,.08); opacity:0; }}
      #typing i {{ width:11px; height:11px; border-radius:50%; background:{MUTED}; }}

      /* lead */
      .lrow {{ display:flex; align-items:center; height:70px; border-bottom:1px solid {LINE}; opacity:0; }}
      .lic {{ width:44px; }}
      .lk {{ width:200px; font-size:25px; font-weight:600; color:{MUTED}; }}
      .lv {{ font-size:29px; font-weight:600; }}
      #l-rows {{ margin-top:14px; }}
      #l-status {{ position:absolute; left:36px; bottom:28px; display:flex; gap:14px; }}
      .pill {{ display:inline-flex; align-items:center; gap:10px; padding:12px 20px; border-radius:999px; font-size:24px; font-weight:700; opacity:0; }}
      .pill.g {{ background:rgba(43,212,125,.13); color:{GREEN}; }}
      .pill.w {{ background:rgba(255,255,255,.08); color:{INK}; }}

      /* inbox */
      #ibox {{ position:absolute; left:36px; right:36px; top:118px; height:330px; overflow:hidden; }}
      .irow {{ position:absolute; left:0; right:0; height:{ROW_H - 10}px; display:flex; align-items:center; gap:18px; padding:0 18px;
               border-radius:18px; background:rgba(255,255,255,.045); opacity:0; }}
      .iav {{ width:46px; height:46px; border-radius:50%; background:rgba(255,255,255,.12); display:flex; align-items:center; justify-content:center;
              font-weight:700; font-size:22px; }}
      .iname {{ font-size:27px; font-weight:700; display:flex; flex-direction:column; line-height:1.2; }}
      .iname small {{ font-size:21px; font-weight:400; color:{MUTED}; }}
      .ibadge {{ margin-left:auto; display:inline-flex; align-items:center; gap:6px; font-size:22px; font-weight:700; color:{GREEN}; }}
      #i-state {{ margin-left:auto; display:inline-flex; align-items:center; gap:10px; padding:9px 18px; border-radius:999px; font-size:22px; font-weight:700;
                  background:rgba(255,255,255,.08); color:#E4E4E7; position:relative; min-width:262px; justify-content:center; white-space:nowrap; }}
      #i-state .s2 {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:10px; border-radius:999px;
                      background:#1E1B3A; color:#C9C2FF; opacity:0; white-space:nowrap; }}

      /* brand */
      #b-kick {{ position:absolute; left:0; right:0; top:214px; text-align:center; font-size:25px; font-weight:600; letter-spacing:.32em; color:{MUTED}; opacity:0; }}
      #b-word {{ position:absolute; left:0; right:0; top:262px; text-align:center; font-family:"Fraunces", serif; font-weight:800; font-size:132px;
                 line-height:1; letter-spacing:-.02em; font-variation-settings:"opsz" 144; }}
      #b-word .lt {{ display:inline-block; opacity:0; }}
      #b-word .dot {{ color:{PINK}; }}
      #b-tag {{ position:absolute; left:0; right:0; top:432px; text-align:center; font-size:38px; font-weight:600; color:#E4E4E7; }}
      #b-tag span {{ display:inline-block; opacity:0; }}

      /* cta */
      #c-ask {{ position:absolute; left:0; right:0; top:182px; text-align:center; font-family:"Fraunces", serif; font-weight:800; font-size:96px;
                line-height:1; letter-spacing:-.02em; opacity:0; }}
      #c-box {{ position:absolute; left:90px; right:90px; top:320px; height:112px; border-radius:56px; background:rgba(16,16,20,.92);
                border:1px solid {LINE}; display:flex; align-items:center; padding:0 18px 0 22px; gap:18px; opacity:0;
                box-shadow:0 24px 60px rgba(0,0,0,.4); }}
      .c-av {{ width:68px; height:68px; border-radius:50%; background:rgba(255,255,255,.1); display:flex; align-items:center; justify-content:center; color:{MUTED}; }}
      #c-field {{ flex:1; font-size:40px; font-weight:700; letter-spacing:.04em; position:relative; height:56px; }}
      #c-ph {{ position:absolute; left:0; top:6px; font-size:32px; font-weight:400; letter-spacing:0; color:#71717A; }}
      #c-in {{ position:absolute; left:0; top:2px; }}
      #c-send {{ width:76px; height:76px; border-radius:50%; background:{PINK}; display:flex; align-items:center; justify-content:center; color:#fff; }}
      #c-posted {{ position:absolute; left:90px; right:90px; top:320px; height:112px; display:flex; align-items:center; gap:18px; padding:0 22px;
                   border-radius:28px; background:rgba(16,16,20,.92); border:1px solid {LINE}; opacity:0; }}
      #c-posted .who {{ font-size:24px; color:{MUTED}; font-weight:600; }}
      #c-posted .txt {{ font-size:40px; font-weight:700; letter-spacing:.04em; }}
      #c-posted .h {{ margin-left:auto; color:{PINK}; }}
      #c-dm {{ position:absolute; left:0; right:0; top:458px; display:flex; justify-content:center; opacity:0; }}
      #c-dm span {{ white-space:nowrap; display:flex; align-items:center; gap:14px; padding:18px 28px; border-radius:22px;
                    background:{INK}; color:#111114; font-size:30px; font-weight:700; box-shadow:0 18px 50px rgba(0,0,0,.35); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1080" data-height="1920">
      <!-- His footage with his own captions, untouched. -->
      <video id="a-roll" class="clip" src="base.mp4" muted playsinline data-start="0" data-duration="{END}" data-track-index="0"
             style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>
      <audio id="a-roll-audio" src="base.mp4" data-start="0" data-duration="{END}" data-track-index="1" data-volume="1"></audio>
      <div id="scrim" class="clip" data-start="0" data-duration="{END}" data-track-index="2"></div>

      <div id="hook" class="layer clip" data-start="0" data-duration="{r(T['hook_out'] + 0.3)}" data-track-index="3">
        <div id="hook-word"><span class="w">AI</span> <span class="w">systems</span></div>
        <div id="hook-line"></div>
        <div id="hook-pill"><span>The best thing to sell right now</span></div>
      </div>

      <div id="demo" class="layer clip" data-start="{r(T['panel_in'] - 0.2)}" data-duration="{r(T['panel_out'] - T['panel_in'] + 0.6)}" data-track-index="4">
        <div id="panel">
          <div class="scr" id="s-form">
            <div class="hd"><span class="ico">{icon("inbox", 28, PINK)}</span><span class="ttl">Request a quote</span><span class="sub">Auto detailing</span></div>
            <div style="margin-top:14px">
{form_rows}
            </div>
            <div id="btn">Get my quote<div class="done">{icon("check", 30, "#06140C", 3)} Request sent</div></div>
          </div>
          <div class="scr" id="s-wait">
            <div class="hd"><span class="ico">{icon("bell", 28, PINK)}</span><span class="ttl">New quote request</span><span class="sub">Unread</span></div>
            <div id="w-from">from <b>Jordan M.</b> · "How much for a full detail?"</div>
            <div id="w-busy">{icon("wrench", 26, "#E4E4E7")} Owner is busy working on a car</div>
            <div id="w-timer"><span id="w-dot"></span><span class="lab">Waiting for a reply</span><span id="w-count">0m</span></div>
          </div>
          <div class="scr" id="s-chat">
            <div class="hd"><span class="ai-av">{icon("spark", 28, "#fff")}</span><span class="ttl">AI Assistant</span>
              <span class="online"><i></i>Online</span><span id="replied">{icon("check", 20, GREEN, 3)} Replied in 4 sec</span></div>
            <div id="chat"><div id="track">
              <div id="typing"><i></i><i></i><i></i></div>
              {"".join(bubbles)}
            </div></div>
          </div>
          <div class="scr" id="s-lead">
            <div class="hd"><span class="ico">{icon("check", 28, PINK, 2.8)}</span><span class="ttl">New lead, organized</span><span class="sub">by AI</span></div>
            <div id="l-rows">{lead_rows}</div>
            <div id="l-status"><span class="pill g" id="p-sent">{icon("send", 22, GREEN)} Sent to owner</span><span class="pill w" id="p-follow">Ready for follow-up</span></div>
          </div>
          <div class="scr" id="s-inbox">
            <div class="hd"><span class="ico">{icon("inbox", 28, PINK)}</span><span class="ttl">Inquiries</span>
              <span id="i-state">{icon("wrench", 22, "#E4E4E7")} Owner busy<span class="s2">{icon("moon", 22, "#C9C2FF")} Closed · 11:47 PM</span></span></div>
            <div id="ibox">{inbox_rows}</div>
          </div>
        </div>
      </div>

      <div id="brand" class="layer clip" data-start="{r(T['kicker'] - 0.1)}" data-duration="{r(T['brand_out'] - T['kicker'] + 0.5)}" data-track-index="5">
        <div id="b-kick">AI SYSTEMS BY</div>
        <div id="b-word">{"".join(f'<span class="lt">{esc(c) if c != " " else "&nbsp;"}</span>' for c in "JT Builds Co")}<span class="lt dot">.</span></div>
        <div id="b-tag"><span id="t1">Real problems.</span> <span id="t2">Real businesses.</span></div>
      </div>

      <div id="cta" class="layer clip" data-start="{r(T['ask'] - 0.1)}" data-duration="{r(END - T['ask'] + 0.1)}" data-track-index="6">
        <div id="c-ask">Own a business?</div>
        <div id="c-box"><span class="c-av">{icon("user", 34, MUTED)}</span>
          <div id="c-field"><span id="c-ph">Add a comment…</span><span id="c-in">{typed("cin", "SYSTEM")}</span></div>
          <span id="c-send">{icon("send", 34, "#fff", 2.4)}</span></div>
        <div id="c-posted"><span class="c-av">{icon("user", 34, MUTED)}</span><div><div class="who">you · just now</div><div class="txt">SYSTEM</div></div>
          <span class="h">{icon("heart", 34, PINK, 2.4)}</span></div>
        <div id="c-dm"><span>{icon("send", 30, "#111114", 2.4)} I'll DM you to get started</span></div>
      </div>
__AUDIO__
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
__JS__
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

# ----------------------------------------------------------------- timeline
js = []
a = js.append
def type_in(id_, text, t, cps=16):
    """Reveal characters one by one from t; caret shows while typing."""
    a(f'tl.set("#{id_}-caret", {{ opacity:1 }}, {r(t - 0.05)});')
    for i, _ in enumerate(text):
        a(f'tl.set("#{id_}-{i}", {{ display:"inline" }}, {r(t + i / cps)});')
    a(f'tl.set("#{id_}-caret", {{ opacity:0 }}, {r(t + len(text) / cps + 0.25)});')
    return t + len(text) / cps

# scrim follows the graphics
a(f'tl.fromTo("#scrim", {{ opacity:0 }}, {{ opacity:1, duration:0.4, ease:"power2.out" }}, {r(T["hook"] - 0.3)});')
for t0, t1 in [(T["panel_out"] + 0.2, T["kicker"] - 0.15), (T["brand_out"], T["ask"] - 0.15)]:
    a(f'tl.to("#scrim", {{ opacity:0.35, duration:0.35, ease:"power2.inOut" }}, {r(t0)});')
    a(f'tl.to("#scrim", {{ opacity:1, duration:0.35, ease:"power2.inOut" }}, {r(t1)});')

# hook
h = T["hook"]
a(f'tl.fromTo("#hook-word .w", {{ yPercent:60, opacity:0, filter:"blur(10px)" }}, {{ yPercent:0, opacity:1, filter:"blur(0px)", duration:0.55, ease:"expo.out", stagger:0.09 }}, {r(h - 0.02)});')
a(f'tl.fromTo("#hook-line", {{ scaleX:0 }}, {{ scaleX:1, duration:0.5, ease:"power3.inOut" }}, {r(h + 0.3)});')
a(f'tl.fromTo("#hook-pill", {{ opacity:0, y:16, scale:0.92 }}, {{ opacity:1, y:0, scale:1, duration:0.4, ease:"back.out(1.8)" }}, {r(T["hook_pill"])});')
a(f'tl.to("#hook", {{ opacity:0, y:-24, filter:"blur(8px)", duration:0.3, ease:"power2.in" }}, {r(T["hook_out"])});')

# panel in + form
p = T["panel_in"]
a(f'tl.fromTo("#panel", {{ opacity:0, y:40, scale:0.9, filter:"blur(10px)" }}, {{ opacity:1, y:0, scale:1, filter:"blur(0px)", duration:0.6, ease:"back.out(1.3)" }}, {r(p)});')
a(f'tl.set("#s-form", {{ opacity:1 }}, {r(p)});')
a(f'tl.fromTo("#s-form .field", {{ opacity:0, y:14 }}, {{ opacity:1, y:0, duration:0.35, ease:"power2.out", stagger:0.06 }}, {r(p + 0.15)});')
typing_spans = []
for lab, id_, val, t in FORM:
    end = type_in(id_, val, t, {"f-name": 20, "f-phone": 28, "f-msg": 26}[id_])
    typing_spans.append((t, end))
s = T["submit"]
a(f'tl.to("#btn", {{ scale:0.95, duration:0.08, ease:"power2.in" }}, {r(s - 0.06)});')
a(f'tl.to("#btn", {{ scale:1, duration:0.3, ease:"back.out(2)" }}, {r(s + 0.02)});')
a(f'tl.to("#btn .done", {{ opacity:1, duration:0.18, ease:"none" }}, {r(s + 0.04)});')

def swap(out_id, in_id, t, dist=140):
    a(f'tl.to("#{out_id}", {{ x:-{dist}, opacity:0, duration:0.24, ease:"power3.in" }}, {r(t - 0.24)});')
    a(f'tl.fromTo("#{in_id}", {{ x:{dist}, opacity:0 }}, {{ x:0, opacity:1, duration:0.4, ease:"power3.out" }}, {r(t)});')

# waiting
w = T["wait"]; swap("s-form", "s-wait", w)
a(f'tl.fromTo("#w-from", {{ opacity:0 }}, {{ opacity:1, duration:0.3 }}, {r(w + 0.2)});')
a(f'tl.fromTo("#w-busy", {{ opacity:0, y:12, scale:0.95 }}, {{ opacity:1, y:0, scale:1, duration:0.36, ease:"back.out(1.8)" }}, {r(T["busy"])});')
# counter: minutes race to hours while he says "sitting there for hours"
js.append(f'''const wc = document.getElementById("w-count"), clock = {{ m: 1 }};
      const fmt = m => m < 60 ? Math.floor(m) + "m" : Math.floor(m / 60) + "h " + String(Math.floor(m % 60)).padStart(2, "0") + "m";
      tl.fromTo(clock, {{ m: 1 }}, {{ m: 2, duration: {r(T["hours0"] - w - 0.3)}, ease: "none", onUpdate: () => wc.textContent = fmt(clock.m) }}, {r(w + 0.3)});
      tl.fromTo(clock, {{ m: 2 }}, {{ m: 192, duration: {r(T["hours1"] - T["hours0"])}, ease: "power3.in", immediateRender: false, onUpdate: () => wc.textContent = fmt(clock.m) }}, {r(T["hours0"])});''')
a(f'tl.to("#w-dot", {{ backgroundColor:"#F0524F", duration:0.3 }}, {r(T["hours0"] + 0.4)});')
a(f'tl.to(["#w-from", "#w-busy"], {{ opacity:0.45, duration:0.6 }}, {r(T["hours0"])});')

# AI takes over: the biggest swap
ai = T["ai"]
a(f'tl.to("#s-wait", {{ scale:0.94, opacity:0, filter:"blur(6px)", duration:0.22, ease:"power3.in" }}, {r(ai - 0.22)});')
a(f'tl.fromTo("#s-chat", {{ opacity:0, scale:1.06, filter:"blur(8px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.45, ease:"expo.out" }}, {r(ai)});')
a(f'tl.fromTo("#panel", {{ boxShadow:"0 30px 80px rgba(0,0,0,.45), 0 0 0 0 rgba(255,0,101,0)" }}, {{ boxShadow:"0 30px 80px rgba(0,0,0,.45), 0 0 0 3px rgba(255,0,101,.55)", duration:0.18, ease:"power2.out", immediateRender:false }}, {r(ai)});')
a(f'tl.to("#panel", {{ boxShadow:"0 30px 80px rgba(0,0,0,.45), 0 0 0 0 rgba(255,0,101,0)", duration:0.8, ease:"power2.out" }}, {r(ai + 0.18)});')
a(f'tl.fromTo("#typing", {{ opacity:0, scale:0.8 }}, {{ opacity:1, scale:1, duration:0.2, ease:"back.out(2)" }}, {r(ai + 0.18)});')
a(f'tl.fromTo("#typing i", {{ y:0 }}, {{ y:-6, duration:0.16, ease:"sine.inOut", stagger:{{ each:0.08, repeat:1, yoyo:true }} }}, {r(ai + 0.3)});')
a(f'tl.to("#typing", {{ opacity:0, duration:0.1 }}, {r(CHAT[0][0] - 0.06)});')
a(f'tl.fromTo("#replied", {{ opacity:0, x:12 }}, {{ opacity:1, x:0, duration:0.35, ease:"back.out(1.8)" }}, {r(T["replied"])});')
for k, (t, who, text) in enumerate(CHAT):
    a(f'tl.fromTo("#b{k}", {{ opacity:0, scale:0.82, y:10 }}, {{ opacity:1, scale:1, y:0, duration:0.32, ease:"back.out(1.6)" }}, {r(t)});')
    bottom = (k + 1) * BUB_H + k * BUB_GAP
    if bottom > CHAT_AREA:
        a(f'tl.to("#track", {{ y:-{bottom - CHAT_AREA}, duration:0.34, ease:"power3.out" }}, {r(t - 0.04)});')

# lead summary
l = T["lead"]; swap("s-chat", "s-lead", l)
a(f'tl.fromTo(".lrow", {{ opacity:0, x:40 }}, {{ opacity:1, x:0, duration:0.38, ease:"power3.out", stagger:0.12 }}, {r(l + 0.18)});')
a(f'tl.fromTo("#p-sent", {{ opacity:0, scale:0.85 }}, {{ opacity:1, scale:1, duration:0.34, ease:"back.out(2)" }}, {r(T["sent"])});')
a(f'tl.fromTo("#p-follow", {{ opacity:0, scale:0.85 }}, {{ opacity:1, scale:1, duration:0.34, ease:"back.out(2)" }}, {r(T["follow"])});')

# inbox: every inquiry handled, even after hours
ib = T["inbox"]; swap("s-lead", "s-inbox", ib)
a(f'tl.fromTo("#i0, #i1, #i2", {{ opacity:0, y:24 }}, {{ opacity:1, y:0, duration:0.4, ease:"power3.out", stagger:0.13 }}, {r(ib + 0.15)});')
a(f'tl.fromTo("#i-state", {{ scale:0.9 }}, {{ scale:1, duration:0.3, ease:"back.out(2)" }}, {r(T["busy2"])});')
a(f'tl.to("#i-state .s2", {{ opacity:1, duration:0.12, ease:"none" }}, {r(T["closed"])});')
a(f'tl.to("#i0, #i1, #i2", {{ y:{ROW_H}, duration:0.36, ease:"power3.inOut" }}, {r(T["late"] - 0.06)});')
a(f'tl.fromTo("#i-late", {{ opacity:0, scale:0.9, y:-10 }}, {{ opacity:1, scale:1, y:0, duration:0.38, ease:"back.out(1.6)" }}, {r(T["late"] + 0.08)});')
a(f'tl.to("#panel", {{ opacity:0, scale:0.93, y:-24, filter:"blur(8px)", duration:0.32, ease:"power2.in" }}, {r(T["panel_out"])});')

# brand
k = T["kicker"]; b = T["brand"]
a(f'tl.fromTo("#b-kick", {{ opacity:0, y:10 }}, {{ opacity:1, y:0, duration:0.4, ease:"power2.out" }}, {r(k)});')
a(f'tl.fromTo("#b-word .lt", {{ opacity:0, yPercent:40, filter:"blur(8px)" }}, {{ opacity:1, yPercent:0, filter:"blur(0px)", duration:0.5, ease:"expo.out", stagger:0.035 }}, {r(b)});')
a(f'tl.fromTo("#t1", {{ opacity:0, y:12 }}, {{ opacity:1, y:0, duration:0.4, ease:"power2.out" }}, {r(T["tag1"])});')
a(f'tl.fromTo("#t2", {{ opacity:0, y:12 }}, {{ opacity:1, y:0, duration:0.4, ease:"power2.out" }}, {r(T["tag2"])});')
a(f'tl.to("#brand", {{ opacity:0, y:-20, filter:"blur(8px)", duration:0.3, ease:"power2.in" }}, {r(T["brand_out"])});')

# cta
a(f'tl.fromTo("#c-ask", {{ opacity:0, y:24, filter:"blur(8px)" }}, {{ opacity:1, y:0, filter:"blur(0px)", duration:0.5, ease:"expo.out" }}, {r(T["ask"])});')
a(f'tl.fromTo("#c-box", {{ opacity:0, y:24, scale:0.94 }}, {{ opacity:1, y:0, scale:1, duration:0.45, ease:"back.out(1.5)" }}, {r(T["comment"])});')
a(f'tl.set("#c-ph", {{ opacity:0 }}, {r(T["typed"] - 0.02)});')
cin_end = type_in("cin", "SYSTEM", T["typed"], 14)
a(f'tl.to("#c-send", {{ scale:0.86, duration:0.08, ease:"power2.in" }}, {r(T["post"] - 0.06)});')
a(f'tl.to("#c-send", {{ scale:1, duration:0.25, ease:"back.out(2)" }}, {r(T["post"] + 0.02)});')
a(f'tl.to("#c-box", {{ opacity:0, scale:0.97, duration:0.1, ease:"power2.in" }}, {r(T["post"] + 0.06)});')
a(f'tl.fromTo("#c-posted", {{ opacity:0, y:10 }}, {{ opacity:1, y:0, duration:0.3, ease:"power2.out" }}, {r(T["post"] + 0.17)});')
a(f'tl.fromTo("#c-posted .h", {{ scale:0.4 }}, {{ scale:1, duration:0.4, ease:"back.out(3)" }}, {r(T["post"] + 0.3)});')
a(f'tl.fromTo("#c-dm", {{ opacity:0, y:-14, scale:0.92 }}, {{ opacity:1, y:0, scale:1, duration:0.42, ease:"back.out(1.7)" }}, {r(T["dm"] - 0.04)});')

# ----------------------------------------------------------------- sound
# (id, file, start, duration, volume). A riser starts (len) before its arrival so it tops out on it.
RS, RM, RL = 0.45, 0.75, 1.25
# Levels by kind (0..1), and where each bundled file's sound actually starts (its own lead-in is skipped).
VOL = {"riser-s": 0.85, "riser-m": 0.85, "riser-l": 0.75, "pop": 0.60, "bubble": 0.55, "bubble-in": 0.50,
       "typing": 0.75, "keys": 0.70, "popup": 0.55, "click": 0.60, "notification": 0.40, "land": 0.45}
ONSET = {"pop.mp3": 0.09, "typing.mp3": 0.42, "notification.mp3": 0.06}
S = []
def add(i, f, t, d, v=None, ms=0.0):
    kind = f.rsplit(".", 1)[0]
    S.append((i, f, r(t), r(d), VOL[kind] if v is None else v, r(ONSET.get(f, 0.0) + ms)))
add("r-hook", "riser-s.wav", T["hook"] - RS, RS);  add("p-hook", "popup.wav", T["hook"], 0.45, 0.9)
add("p-pill", "bubble.wav", T["hook_pill"], 0.18)
add("r-panel", "riser-m.wav", p - RM, RM);         add("p-panel", "popup.wav", p, 0.45)
for n, (t0, t1) in enumerate(typing_spans):
    add(f"k-type{n}", "keys.wav", t0, min(t1 - t0 + 0.05, 1.05), 0.95 if n == 2 else None, ms=0.2 * n)
add("k-submit", "click.mp3", s - 0.04, 0.3)
add("n-request", "notification.mp3", w, 1.2)
add("p-busy", "bubble-in.wav", T["busy"], 0.18)
add("r-ai", "riser-l.wav", ai - RL, RL);           add("l-ai", "land.wav", ai, 0.8); add("p-ai", "popup.wav", ai, 0.45)
for k, (t, who, _) in enumerate(CHAT):
    add(f"b{k}-snd", "bubble.wav" if who == "ai" else "bubble-in.wav", t, 0.18)
add("r-lead", "riser-s.wav", l - RS, RS);          add("p-lead", "popup.wav", l, 0.45)
add("p-sent", "bubble.wav", T["sent"], 0.18)
add("r-inbox", "riser-s.wav", ib - RS, RS);        add("p-inbox", "popup.wav", ib, 0.45)
add("p-closed", "bubble-in.wav", T["closed"], 0.18); add("p-late", "bubble.wav", T["late"] + 0.08, 0.18)
add("r-brand", "riser-m.wav", b - RM, RM);         add("l-brand", "land.wav", b, 0.8, 0.40); add("p-brand", "popup.wav", b, 0.45)
add("r-ask", "riser-s.wav", T["ask"] - RS, RS);    add("p-ask", "popup.wav", T["ask"], 0.45, 0.9)
add("p-box", "popup.wav", T["comment"], 0.45, 0.75)
add("k-cin", "keys.wav", T["typed"], r(cin_end - T["typed"] + 0.05), 1.0, ms=0.35)
add("k-post", "click.mp3", T["post"] - 0.04, 0.3)
add("n-dm", "notification.mp3", T["dm"] - 0.02, 1.2, 0.32)
audio = "\n".join(f'      <audio id="{i}" src="assets/sfx/{f}" data-start="{t}" data-duration="{d}" data-media-start="{ms}" '
                  f'data-track-index="{10 + n}" data-volume="{v}"></audio>' for n, (i, f, t, d, v, ms) in enumerate(S))

out = html_out.replace("__AUDIO__", "      <!-- sound: risers top out on each arrival; nothing else is under his voice -->\n" + audio)
out = out.replace("__JS__", "\n".join("      " + l for l in js))
open("index.html", "w").write(out)
print(f"index.html: {len(S)} sounds, {len(js)} timeline lines")
