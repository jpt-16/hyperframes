"""Shared scene pieces: the hook, section headings, pop-up chips, highlight rings,
screen wipes, typing, the brand bar and the CTA end card. Templates compose these.

Every piece takes absolute times (seconds) and writes into a Comp. Sounds are
cued here too, so a graphic and its sound can never drift apart:
  hook lands on a low hit · chips pop · screens swap with a riser into the
  light sweep · section changes whoosh · the CTA lands on the music's chord.
"""
from brand import C, icon
from comp import o, R, rich, plain, esc

# ----------------------------------------------------------------- layout
SAFE = dict(left=70, right=1010, top=220, bottom=1560)    # keep text clear of Reels / TikTok UI

SCENE_CSS = f"""
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#vignette {{ position:absolute; inset:0; pointer-events:none; z-index:60;
             background:radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.42) 100%); }}
.mask {{ display:block; overflow:hidden; padding-bottom:.12em; margin-bottom:-.12em; }}
.mask > .in {{ display:block; }}

/* hook */
#hook {{ opacity:1; z-index:40; }}
.hk {{ position:absolute; left:{SAFE['left']}px; right:{1080 - SAFE['right'] + 0}px; }}
.hk h1 {{ font-family:"Montserrat", sans-serif; font-weight:800; line-height:1.0; letter-spacing:-.032em; margin-top:26px; color:{C['white']}; }}
.hk .w {{ position:relative; display:inline-block; }}
.hk .acc .w {{ color:{C['accent']}; }}
.hk .u {{ position:absolute; left:0; right:0; bottom:.02em; height:.085em; border-radius:.05em; background:{C['accent']}; }}
.hk .eyebrow {{ font-size:28px; }}

/* section headings */
.head {{ z-index:30; }}
.head h2 {{ margin-top:18px; }}

/* chips */
.chip .tx {{ display:flex; flex-direction:column; line-height:1.12; }}
.chip .tx small {{ font-weight:600; font-size:25px; color:{C['grey']}; margin-top:6px; white-space:nowrap; }}

/* brand bar */
#brandbar {{ opacity:0; }}

/* cta end card */
#cta {{ z-index:50; }}
.cta-bg {{ position:absolute; inset:0; background:radial-gradient(ellipse 110% 60% at 50% 40%, {C['bg2']} 0%, {C['bg']} 70%); }}
.lk {{ position:absolute; left:340px; top:380px; width:400px; height:330px; border-radius:34px; background:{C['tile']};
       box-shadow:0 0 0 1px rgba(255,255,255,.06), 0 30px 80px rgba(0,0,0,.5); opacity:0; }}
.lk-mark {{ position:absolute; left:50%; top:46px; width:170px; height:143px; margin-left:-85px; }}
.lk-mark img {{ width:100%; height:100%; display:block; }}
.lk-word {{ position:absolute; left:0; right:0; top:222px; text-align:center; font-family:"Montserrat", sans-serif; font-weight:800;
            font-size:44px; line-height:1; letter-spacing:.035em; white-space:nowrap; }}
.lk-word .m {{ display:inline-block; overflow:hidden; vertical-align:top; padding-bottom:.06em; }}
.lk-word .lt {{ display:inline-block; color:#FFFFFF; }}
.lk-word .co {{ display:inline-block; color:{C['grey']}; margin-left:.28em; opacity:0; }}
.cta-h {{ position:absolute; left:{SAFE['left']}px; right:{SAFE['left']}px; top:790px; text-align:center; font-family:"Montserrat", sans-serif;
          font-weight:800; line-height:1.06; letter-spacing:-.018em; color:{C['white']}; text-wrap:balance; }}
.cta-h em {{ font-style:normal; color:{C['accent']}; }}
.cta-row {{ position:absolute; left:0; right:0; display:flex; justify-content:center; }}
.cta-pill {{ display:inline-flex; align-items:center; gap:16px; padding:28px 46px; border-radius:999px; background:{C['accent']}; color:{C['accent_ink']};
             font-family:"Montserrat", sans-serif; font-weight:800; font-size:40px; letter-spacing:-.005em; white-space:nowrap; opacity:0;
             box-shadow:0 20px 60px rgba(255,181,71,.25); }}
.cta-sub {{ position:absolute; left:110px; right:110px; text-align:center; font-size:29px; line-height:1.4; font-weight:600; color:{C['grey']}; opacity:0; text-wrap:balance; }}
"""

def fit(text, sizes):
    """Pick a font size from [(max_chars, px), ...] by the visible character count."""
    n = len(plain(text))
    for mx, px in sizes:
        if n <= mx: return px
    return sizes[-1][1]

def lines_html(lines, accent=()):
    out = []
    for i, ln in enumerate(lines):
        acc = i in accent
        u = '<i class="u"></i>' if acc else ""
        out.append(f'<span class="mask{" acc" if acc else ""}"><span class="in"><span class="w">{rich(ln)}{u}</span></span></span>')
    return "".join(out)

# ----------------------------------------------------------------- hook (0 - ~2.3 s)
def hook(c, h, t1):
    """h = {eyebrow, lines[], accent:[i]}. Readable by 0.4 s; the eyebrow is on frame 0."""
    lines = h["lines"]; accent = h.get("accent", [len(lines) - 1])
    longest = max(len(plain(l)) for l in lines)
    size = min(128, int(950 / (0.64 * longest)))
    block = 28 + 26 + len(lines) * size * 1.0
    top = int(850 - block / 2)
    c.clip("hook", 0, t1 + 0.4, f"""<div class="hk" id="hk" style="top:{top}px">
        <div class="eyebrow" id="hk-eb"><i></i>{esc(h.get("eyebrow", "WEBSITE TIP").upper())}</div>
        <h1 style="font-size:{size}px">{lines_html(lines, accent)}</h1></div>""")
    c.ft("#hk h1 .in", o(yPercent=112), o(yPercent=0, duration=0.55, ease="power4.out", stagger=0.1), 0.0)
    c.ft("#hk .u", o(scaleX=0, transformOrigin="0% 50%"), o(scaleX=1, duration=0.5, ease="power3.inOut"), 0.42 + 0.1 * accent[0])
    c.ft("#hk", o(scale=1), o(scale=1.035, duration=t1, ease="none"), 0.0)
    c.to("#hk h1 .in", o(yPercent=-112, duration=0.32, ease="power3.in", stagger=0.04), t1 - 0.3)
    c.to("#hk-eb", o(opacity=0, duration=0.2, ease="power1.in"), t1 - 0.3)
    c.cue("land", 0.0, -1.0)
    c.cue("popup", 0.42 + 0.1 * accent[0], -5.0)
    c.cue("whoosh", t1 - 0.05, -3.0)

# ----------------------------------------------------------------- section heading
def head(c, hid, t0, t1, eyebrow, text, kind="", last=False):
    size = fit(text, [(38, 70), (50, 62), (64, 56), (999, 50)])
    c.clip(hid, t0 - 0.05, t1 + 0.35, f"""<div class="head"><div class="eyebrow {kind}" id="{hid}-eb"><i></i>{esc(eyebrow.upper())}</div>
        <h2 style="font-size:{size}px"><span class="mask"><span class="in" id="{hid}-h">{rich(text)}</span></span></h2></div>""", cls="layer head-l")
    c.ft(f"#{hid}-eb", o(opacity=0, x=-18), o(opacity=1, x=0, duration=0.4, ease="power3.out"), t0)
    c.ft(f"#{hid}-h", o(yPercent=105), o(yPercent=0, duration=0.6, ease="power4.out"), t0 + 0.05)
    if not last:
        c.to(f"#{hid}-eb", o(opacity=0, duration=0.22, ease="power2.in"), t1 - 0.22)
        c.to(f"#{hid}-h", o(yPercent=-105, duration=0.3, ease="power3.in"), t1 - 0.25)

# ----------------------------------------------------------------- chips + rings
CHIP_IC = {"good": ("check", C["good"]), "bad": ("x", C["bad"]), "acc": ("spark", C["accent"])}

def chip(c, cid, t0, t1, text, kind="good", x=None, right=None, y=800, sub=None, ic=None, sfx=True):
    name, col = CHIP_IC[kind]
    if ic: name = ic
    pos = f"left:{x}px;" if x is not None else f"right:{right}px;"
    subh = f"<small>{esc(sub)}</small>" if sub else ""
    c.clip(cid + "-l", t0 - 0.05, t1 + 0.3, f"""<div class="chip {kind}" id="{cid}" style="{pos}top:{y}px">
        <span class="ic">{icon(name, 28, col, 2.8)}</span><span class="tx"><b>{rich(text)}</b>{subh}</span></div>""", cls="layer", style="z-index:35")
    c.ft(f"#{cid}", o(opacity=0, y=30, scale=0.88), o(opacity=1, y=0, scale=1, duration=0.5, ease="back.out(1.7)", immediateRender=False), t0)
    c.set(f"#{cid}", o(opacity=0), 0)
    c.to(f"#{cid}", o(opacity=0, y=-14, scale=0.97, duration=0.25, ease="power2.in"), t1)
    if sfx: c.cue("popup", t0, -6.0)

def ring(c, rid, t0, t1):
    c.ft(f"#{rid}", o(opacity=0, scale=1.12), o(opacity=1, scale=1, duration=0.42, ease="power3.out", immediateRender=False), t0)
    c.to(f"#{rid}", o(opacity=0, duration=0.3, ease="power1.in"), t1)

# ----------------------------------------------------------------- screens
WIPE_FROM = "inset(0% 0% 100% 0%)"
WIPE_TO = "inset(0% 0% 0% 0%)"

def wipe_in(c, sid, t, dur=0.75, sound=True):
    """Reveal a stacked screen top-down with a light pass across the glass. Screen html needs cls 'wipe'."""
    c.ft(f"#{sid}", o(clipPath=WIPE_FROM), o(clipPath=WIPE_TO, duration=dur, ease="power3.inOut"), t)
    c.ft(f"#{sid}-sweep", o(xPercent=-110, opacity=1), o(xPercent=110, duration=dur + 0.25, ease="power2.inOut", immediateRender=False), t + 0.05)
    c.set(f"#{sid}-sweep", o(opacity=0), 0)
    c.to(f"#{sid}-sweep", o(opacity=0, duration=0.01), t + dur + 0.3)
    if sound:
        c.cue("riser-s", t + dur * 0.55, -4.0)
        c.cue("whoosh", t + dur * 0.5, -6.0)

def scroll(c, sid, t, y, dur=1.6, ease="power2.inOut"):
    c.to(f"#{sid}-scr", o(y=y, duration=dur, ease=ease), t)

def typing(text, t0, cps=19):
    """-> (html spans, end time, char times). Characters show one by one; c.key() clicks are added by the caller."""
    times = [t0 + i / cps for i in range(len(text))]
    spans = "".join(f'<span class="ch" id="q{i}">{esc(ch)}</span>' for i, ch in enumerate(text))
    return spans, (times[-1] if times else t0) + 1 / cps, times

def type_into(c, text, t0, cps=19):
    _, end, times = typing(text, t0, cps)
    for i, t in enumerate(times):
        c.set(f"#q{i}", o(display="inline"), t)
        if text[i] != " ": c.key(t, -1.5 if i % 3 else 0.0)
        else: c.key(t, -6.0)
    return end

TYPING_CSS = "#sp-q { white-space:pre; } .ch { display:none; }"

# ----------------------------------------------------------------- brand bar + CTA
def brandbar(c, t0, t1):
    c.clip("bb", t0, t1, f'<div id="brandbar"><img src="assets/jt-mark.png" alt=""><span><b>JT</b> BUILDS CO.</span></div>', cls="layer", style="z-index:30")
    c.ft("#brandbar", o(opacity=0, y=-8), o(opacity=1, y=0, duration=0.5, ease="power2.out"), t0 + 0.1)
    c.to("#brandbar", o(opacity=0, duration=0.25), t1 - 0.3)

def cta(c, t0, spec):
    """End card: the JT Builds Co. lockup, the ask, an action pill, a short sub line (disclaimers go here)."""
    h = spec["headline"]; size = fit(h, [(30, 76), (44, 68), (999, 60)])
    sub = spec.get("sub", "")
    pill_top = 790 + int(size * 1.06 * (1 if len(plain(h)) <= 24 else 2)) + 70
    letters = "".join(f'<span class="lt">{ch}</span>' for ch in "BUILDS")
    c.clip("cta", t0 - 0.12, c.D, f"""<div class="cta-bg" id="cta-bg"></div>
        <div class="lk" id="lk"><div class="lk-mark" id="lk-mark"><img src="assets/jt-mark.png" alt="JT Builds Co. mark"></div>
          <div class="lk-word"><span class="m">{letters}</span><span class="co" id="lk-co">CO.</span></div></div>
        <h2 class="cta-h" style="font-size:{size}px"><span class="mask"><span class="in" id="cta-h">{rich(h)}</span></span></h2>
        <div class="cta-row" style="top:{pill_top}px"><div class="cta-pill" id="cta-pill">{rich(spec["action"])} {icon("arrow", 36, C["accent_ink"], 3)}</div></div>
        <div class="cta-sub" id="cta-sub" style="top:{pill_top + 150}px">{rich(sub)}</div>""")
    c.ft("#cta", o(opacity=0), o(opacity=1, duration=0.3, ease="power1.out"), t0 - 0.12)
    c.ft("#lk", o(opacity=0, scale=0.9, filter="blur(10px)"), o(opacity=1, scale=1, filter="blur(0px)", duration=0.6, ease="expo.out"), t0)
    c.ft("#lk-mark img", o(clipPath="inset(100% 0% 0% 0%)", y=14), o(clipPath="inset(0% 0% 0% 0%)", y=0, duration=0.55, ease="power3.out"), t0 + 0.08)
    c.ft("#lk .lt", o(yPercent=105), o(yPercent=0, duration=0.5, ease="power4.out", stagger=0.04), t0 + 0.2)
    c.ft("#lk-co", o(opacity=0, x=-12), o(opacity=1, x=0, duration=0.4, ease="power3.out"), t0 + 0.5)
    c.ft("#cta-h", o(yPercent=105), o(yPercent=0, duration=0.6, ease="power4.out"), t0 + 0.32)
    c.ft("#cta-pill", o(opacity=0, y=26, scale=0.9), o(opacity=1, y=0, scale=1, duration=0.55, ease="back.out(1.6)"), t0 + 0.7)
    c.ft("#cta-sub", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.5, ease="power2.out"), t0 + 0.95)
    c.to("#cta-pill", o(scale=1.045, duration=0.32, ease="sine.inOut", yoyo=True, repeat=1), t0 + 1.7)
    c.cue("riser-m", t0, -2.5)
    c.cue("land", t0, -6.0)            # the bed already lands a kick + boom here
    c.cue("popup", t0 + 0.7, -4.0)
