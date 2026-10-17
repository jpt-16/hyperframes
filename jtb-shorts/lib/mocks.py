"""HTML mockups used inside the shorts: device frames, example business sites,
a simulated local search page, a business profile, a dashboard.

Sites are authored at real device widths (mobile 390 px, desktop 1200 px, an
old fixed-width site at 1000 px) and scaled into the frames, so they read like
real pages rather than drawings. All businesses are fictional (niches.json).
No search-engine logos are reproduced; the search page is a generic layout.
"""
import html
from brand import icon, C
from art import scene

esc = html.escape
PHONE = dict(x=280, y=500, w=520, h=1040, pad=14)          # outer frame in the 1080x1920 canvas
SCREEN_W = PHONE["w"] - 2 * PHONE["pad"]                    # 492
MOBILE_SCALE = SCREEN_W / 390
BROWSER = dict(x=60, y=640, w=960, h=640, bar=54)
DESK_SCALE = BROWSER["w"] / 1200

def niche_vars(n):
    c = n["colors"]; return f'--p:{c["primary"]};--a:{c["accent"]};--ink:{c["ink"]};'

FIXED = "<!--FIXED-->"     # site html after this marker stays put while the page scrolls (sticky call bars)

def _screen(kind, sid, h, cls):
    body, _, fixed = h.partition(FIXED)
    vp = "m" if kind == "pscreen" else "d"
    # the page inside a device is set dressing (judged visually), so layout/contrast audits skip it
    return (f'<div class="{kind} {cls}" id="{sid}"><div class="vp {vp}" data-layout-ignore><div class="scr" id="{sid}-scr">{body}</div>{fixed}</div>'
            f'<i class="sweep" id="{sid}-sweep"></i></div>')

def phone(pid, screens, style=""):
    """screens: list of (screen_id, inner_html, extra_class). Each gets #{sid}-scr (scroll) and #{sid}-sweep (light pass)."""
    inner = "".join(_screen("pscreen", sid, h, cls) for sid, h, cls in screens)
    return (f'<div class="phone" id="{pid}" data-layout-allow-overflow style="left:{PHONE["x"]}px;top:{PHONE["y"]}px;width:{PHONE["w"]}px;height:{PHONE["h"]}px;{style}">'
            f'<div class="pglass">{inner}</div><div class="notch"></div></div>')

def browser(bid, url, screens, style=""):
    inner = "".join(_screen("bscreen", sid, h, cls) for sid, h, cls in screens)
    return (f'<div class="browser" id="{bid}" style="left:{BROWSER["x"]}px;top:{BROWSER["y"]}px;width:{BROWSER["w"]}px;height:{BROWSER["h"]}px;{style}">'
            f'<div class="bbar"><i></i><i></i><i></i><span>{icon("globe", 18, "#9AA0A6")} {esc(url)}</span></div>'
            f'<div class="bbody">{inner}</div></div>')

def domain(n): return n["short"].lower().replace(" ", "") + ".com"

# ----------------------------------------------------------------- example sites
# px prefixes every id so the same site can appear on several screens of one video.
RING = '<i class="ring" id="{}"></i>'

def site_desktop(n):
    svc = "".join(f'<div class="sd-card"><span>{icon(n["icon"], 30, "var(--p)")}</span><b>{esc(s)}</b><p>Clear scope, clear quote, on your schedule.</p></div>' for s in n["services"])
    return f"""<div class="sd" style="{niche_vars(n)}">
  <div class="sd-nav"><span class="sd-logo"><i>{icon(n["icon"], 22, "#fff")}</i>{esc(n["business"])}</span>
    <span class="sd-links"><span>Services</span><span>Reviews</span><span>Areas</span></span><span class="sd-cta">Get a free quote</span></div>
  <div class="sd-hero"><div class="sd-l"><div class="sd-kick">{esc(n["city"])} · {esc(n["label"])}</div><h1>{esc(n["headline"])}</h1><p>{esc(n["sub"])}</p>
    <div class="sd-btns"><span class="sd-b1">Get a free quote {icon("arrow", 22, "#fff", 2.6)}</span><span class="sd-b2">{icon("phone", 22, "var(--p)", 2.4)} {esc(n["phone"])}</span></div>
    <div class="sd-trust">{icon("star", 20, "#F5B301") * 5}<span>4.9 from local customers</span></div></div>
    <div class="sd-r"><div class="sd-photo">{scene(n["_key"], "desk")}</div>
      <div class="sd-float f1">{icon("check", 20, "var(--p)", 3)} {esc(n["badges"][0])}</div><div class="sd-float f2">{icon("check", 20, "var(--p)", 3)} {esc(n["badges"][1])}</div></div></div>
  <div class="sd-svc">{svc}</div>
</div>"""

def site_old(n, fit=None):
    """A dated fixed-width (1000 px) site. fit="mobile" shrinks it the way a phone would; "desktop" centres it in a wide window."""
    para = (f"Welcome to {esc(n['business'])}! We are a family owned business providing quality {esc(n['label'])} services for all of your needs. "
            "We have many years of experience and we take pride in our work. Please browse our website to learn more about our company, "
            "our history and the many services we offer. Feel free to contact us with any questions you may have. ")
    page = f"""<div class="so">
  <div class="so-top"><span class="so-logo">{esc(n['business'])}</span><span class="so-nav"><u>Home</u> | <u>About Us</u> | <u>Services</u> | <u>Gallery</u> | <u>Links</u> | <u>Contact Us</u></span></div>
  <div class="so-banner"><span>Welcome to Our Website!</span></div>
  <div class="so-cols"><div><h4>About Us</h4><p>{para}{para}</p></div><div><h4>Our Services</h4><p>{para}</p><p><u>Click here</u> for more information.</p></div></div>
  <div class="so-foot">Copyright 2011 {esc(n['business'])}. All rights reserved. Phone: {esc(n['phone'])} · Best viewed in Internet Explorer</div>
</div>"""
    if fit == "mobile": return f'<div class="som"><div class="so-fit">{page}</div></div>'
    if fit == "desktop": return f'<div class="sod">{page}</div>'
    return page

def screen_slow(px=""):
    return f"""<div class="ss"><div class="ss-spin" id="{px}ss-spin"></div><div class="ss-bar"><i id="{px}ss-fill"></i></div><div class="ss-t">Loading…</div></div>"""

def screen_wall(n):
    t = (f"At {esc(n['business'])} we believe that every customer deserves the very best {esc(n['label'])} experience possible, which is why "
         "we have spent many years refining our processes, training our team and investing in the equipment needed to deliver results that "
         "we are proud of. Whether you are a new customer or have worked with us before, we are committed to providing service that exceeds "
         "expectations each and every time. If you would like to learn more about what we do, please continue reading below. ")
    return f'<div class="sw" style="{niche_vars(n)}"><div class="sm-nav"><span class="sm-logo"><i>{icon(n["icon"], 18, "#fff")}</i>{esc(n["short"])}</span>{icon("menu", 24, "var(--ink)")}</div><h2>About our company</h2><p>{t}</p><p>{t}</p></div>'

def dashboard(n):
    """Leads dashboard. Always labelled as illustrative. ids: db-v0..2 (numbers), db-line (pathLength=1)."""
    return f"""<div class="db" style="{niche_vars(n)}">
  <div class="db-side"><span class="db-logo"><i>{icon(n["icon"], 20, "#fff")}</i></span><i class="on"></i><i></i><i></i><i></i></div>
  <div class="db-main"><div class="db-top"><h3>Leads overview</h3><span class="db-tag">Example dashboard · illustrative data</span></div>
    <div class="db-tiles">
      <div class="db-tile"><small>{icon("phone", 20, "var(--p)")} Calls</small><b id="db-v0">0</b></div>
      <div class="db-tile"><small>{icon("msg", 20, "var(--p)")} Form fills</small><b id="db-v1">0</b></div>
      <div class="db-tile"><small>{icon("dir", 20, "var(--p)")} Direction requests</small><b id="db-v2">0</b></div></div>
    <div class="db-chart"><svg viewBox="0 0 1000 300" preserveAspectRatio="none"><path class="grid" d="M0 75H1000M0 150H1000M0 225H1000"/>
      <path id="db-line" d="M0 250 C120 240 180 210 260 215 S400 170 480 160 S640 120 720 110 S880 70 1000 60" pathLength="1"/></svg></div></div>
</div>"""

MOCK_CSS = f"""
.phone {{ position:absolute; border-radius:74px; background:#0B0B0C; padding:{PHONE['pad']}px; z-index:10;
          box-shadow:0 0 0 2px #2A2826, 0 0 0 9px #161514, 0 50px 120px rgba(0,0,0,.6), 0 0 120px rgba(255,181,71,.07); }}
.pglass {{ position:relative; width:100%; height:100%; border-radius:60px; overflow:hidden; background:#fff; }}
.notch {{ position:absolute; left:50%; top:30px; width:130px; height:36px; margin-left:-65px; border-radius:20px; background:#0B0B0C; z-index:5; }}
.pscreen, .bscreen {{ position:absolute; inset:0; overflow:hidden; background:#fff; }}
.vp {{ position:absolute; left:0; top:0; transform-origin:0 0; }}
.vp.m {{ width:390px; transform:scale({MOBILE_SCALE:.5f}); }}
.vp.d {{ width:1200px; transform:scale({DESK_SCALE:.5f}); }}
.browser {{ position:absolute; border-radius:22px; overflow:hidden; background:#fff; z-index:10;
            box-shadow:0 0 0 1px rgba(255,255,255,.12), 0 50px 120px rgba(0,0,0,.6); }}
.bbar {{ height:{BROWSER['bar']}px; background:#ECEBE8; display:flex; align-items:center; gap:10px; padding:0 20px; }}
.bbar i {{ width:14px; height:14px; border-radius:50%; background:#D0CDC8; }}
.bbar span {{ margin-left:20px; flex:1; height:32px; border-radius:16px; background:#fff; display:flex; align-items:center; gap:8px; padding:0 16px;
              font-size:17px; color:#5F6368; }}
.bbody {{ position:absolute; left:0; right:0; top:{BROWSER['bar']}px; bottom:0; }}
.blob {{ position:absolute; border-radius:50%; filter:blur(2px); }}
.scr {{ position:relative; }}
.wipe {{ clip-path:inset(0% 0% 100% 0%); }}
.sweep {{ position:absolute; top:0; bottom:0; left:0; width:100%; z-index:6; pointer-events:none; opacity:0;
          background:linear-gradient(105deg, rgba(255,255,255,0) 30%, rgba(255,255,255,.75) 50%, rgba(255,255,255,0) 70%); }}
.hl {{ position:relative; }}
.ring {{ position:absolute; left:-8px; right:-8px; top:-8px; bottom:-8px; border-radius:18px; border:3px solid {C['accent']}; z-index:3;
         box-shadow:0 0 0 7px rgba(255,181,71,.22), 0 0 34px rgba(255,181,71,.35); opacity:0; pointer-events:none; }}

/* modern desktop site */
.sd {{ font-family:"Inter", sans-serif; color:var(--ink); background:#fff; height:{int((BROWSER['h'] - BROWSER['bar']) / DESK_SCALE)}px; overflow:hidden; }}
.sd-nav {{ height:84px; padding:0 56px; display:flex; align-items:center; gap:40px; border-bottom:1px solid #F0F1F3; }}
.sd-logo {{ display:flex; align-items:center; gap:12px; font-weight:800; font-size:22px; }}
.sd-logo i {{ width:40px; height:40px; border-radius:11px; background:var(--p); display:flex; align-items:center; justify-content:center; }}
.sd-links {{ display:flex; gap:28px; font-size:17px; color:#4B5563; margin-left:auto; }}
.sd-cta {{ padding:13px 22px; border-radius:12px; background:var(--p); color:#fff; font-weight:700; font-size:17px; }}
.sd-hero {{ display:flex; gap:40px; padding:46px 56px 0; }}
.sd-l {{ flex:1; }}
.sd-kick {{ display:inline-block; font-size:14px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--p);
            background:color-mix(in srgb, var(--p) 10%, #fff); padding:8px 13px; border-radius:999px; }}
.sd-l h1 {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:62px; line-height:1.02; letter-spacing:-.025em; margin:20px 0 16px; }}
.sd-l p {{ font-size:20px; line-height:1.5; color:#4B5563; max-width:520px; }}
.sd-btns {{ display:flex; gap:14px; margin-top:28px; }}
.sd-b1 {{ padding:18px 28px; border-radius:14px; background:var(--p); color:#fff; font-weight:700; font-size:19px; display:flex; align-items:center; gap:10px; }}
.sd-b2 {{ padding:16px 24px; border-radius:14px; border:2px solid color-mix(in srgb, var(--p) 30%, #fff); color:var(--p); font-weight:700; font-size:19px; display:flex; align-items:center; gap:10px; }}
.sd-trust {{ display:flex; align-items:center; gap:3px; margin-top:24px; font-size:16px; color:#4B5563; }} .sd-trust span {{ margin-left:10px; }}
.sd-r {{ position:relative; width:480px; height:420px; border-radius:30px; overflow:hidden; background:linear-gradient(135deg, var(--p), color-mix(in srgb, var(--p) 55%, var(--a))); }}
.sd-r .b1 {{ width:320px; height:320px; right:-80px; top:-90px; background:color-mix(in srgb, var(--a) 70%, transparent); opacity:.6; }}
.sd-r .b2 {{ width:220px; height:220px; left:-60px; bottom:-80px; background:rgba(255,255,255,.18); }}
.sd-photo {{ position:absolute; inset:0; }}
.sd-float {{ position:absolute; display:flex; align-items:center; gap:8px; background:#fff; border-radius:14px; padding:12px 16px; font-weight:700; font-size:16px;
             box-shadow:0 12px 30px rgba(0,0,0,.18); }}
.sd-float.f1 {{ left:24px; bottom:30px; }} .sd-float.f2 {{ right:24px; top:28px; }}
.sd-svc {{ display:flex; gap:20px; padding:40px 56px; }}
.sd-card {{ flex:1; padding:24px; border-radius:18px; border:1px solid #EEF0F3; }}
.sd-card span {{ width:52px; height:52px; border-radius:14px; background:color-mix(in srgb, var(--p) 10%, #fff); display:flex; align-items:center; justify-content:center; }}
.sd-card b {{ display:block; font-size:20px; margin:14px 0 6px; }} .sd-card p {{ font-size:15px; color:#6B7280; }}

/* the old site: fixed 1000 px, beige, tiny low-contrast text, no button */
.so {{ width:1000px; font-family:"Fraunces", serif; background:#F4EBD6; color:#6B5E4A; height:2200px; }}
.so-top {{ display:flex; align-items:center; justify-content:space-between; padding:18px 24px; background:#E8DBBE; border-bottom:3px double #B49B6C; }}
.so-logo {{ font-size:24px; font-style:italic; color:#7A4E1F; font-weight:600; }}
.so-nav {{ font-family:"Inter", sans-serif; font-size:13px; color:#1F3FAF; }}
.so-banner {{ height:190px; margin:16px 24px; border:2px solid #B49B6C; display:flex; align-items:center; justify-content:center;
              background:linear-gradient(180deg, #7FA6D9, #3E6FB3 60%, #2E5A99); }}
.so-banner span {{ font-family:"Fraunces", serif; font-style:italic; font-size:40px; color:#FFF6C9; text-shadow:2px 2px 0 #1E3B6E; }}
.so-cols {{ display:flex; gap:24px; padding:0 24px; }}
.so-cols div {{ flex:1; }}
.so-cols h4 {{ font-size:20px; color:#7A4E1F; margin:8px 0; text-decoration:underline; }}
.so-cols p {{ font-family:"Inter", sans-serif; font-size:13px; line-height:1.5; color:#9A8E79; margin-bottom:10px; }}
.so-cols u {{ color:#1F3FAF; }}
.som {{ width:390px; height:{int(1012 / MOBILE_SCALE)}px; overflow:hidden; background:#F4EBD6; }}
.so-fit {{ width:1000px; transform:scale(.39); transform-origin:0 0; }}
.sod {{ width:1200px; height:{int((BROWSER['h'] - BROWSER['bar']) / DESK_SCALE)}px; overflow:hidden; background:#D9CFB8; }}
.sod .so {{ margin:0 auto; }}
.so-foot {{ margin:20px 24px; font-family:"Inter", sans-serif; font-size:11px; color:#B5AA95; text-align:center; }}

/* slow page + wall of text */
.ss {{ width:390px; height:{int(1012 / MOBILE_SCALE)}px; background:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:22px; }}
.ss-spin {{ width:54px; height:54px; border-radius:50%; border:5px solid #E5E7EB; border-top-color:#9CA3AF; }}
.ss-bar {{ width:220px; height:6px; border-radius:3px; background:#E5E7EB; overflow:hidden; }}
.ss-bar i {{ display:block; height:100%; width:5%; background:#9CA3AF; }}
.ss-t {{ font-size:15px; color:#9CA3AF; }}
.sw .sm-nav {{ height:96px; padding:44px 16px 0; display:flex; align-items:center; justify-content:space-between; }}
.sw .sm-logo {{ display:flex; align-items:center; gap:9px; font-weight:700; font-size:19px; }}
.sw .sm-logo i {{ width:32px; height:32px; border-radius:9px; background:var(--p); display:flex; align-items:center; justify-content:center; }}
.sw {{ font-family:"Inter", sans-serif; color:#4B5563; background:#fff; }}
.sw h2 {{ font-size:20px; color:#111827; padding:16px 22px 6px; }}
.sw p {{ font-size:13px; line-height:1.55; padding:6px 22px; color:#6B7280; }}

/* dashboard */
.db {{ display:flex; font-family:"Inter", sans-serif; background:#F7F7F8; color:#111827; height:{int((BROWSER['h'] - BROWSER['bar']) / DESK_SCALE)}px; }}
.db-side {{ width:84px; background:#fff; border-right:1px solid #ECECEE; display:flex; flex-direction:column; align-items:center; gap:22px; padding-top:24px; }}
.db-logo {{ width:44px; height:44px; border-radius:12px; background:var(--p); display:flex; align-items:center; justify-content:center; }}
.db-side i {{ width:36px; height:8px; border-radius:4px; background:#E5E7EB; }} .db-side i.on {{ background:var(--p); }}
.db-main {{ flex:1; padding:32px 40px; }}
.db-top {{ display:flex; align-items:center; justify-content:space-between; }} .db-top h3 {{ font-size:30px; font-weight:700; }}
.db-tag {{ font-size:15px; color:#6B7280; background:#fff; border:1px solid #E5E7EB; padding:8px 14px; border-radius:999px; }}
.db-tiles {{ display:flex; gap:20px; margin-top:26px; }}
.db-tile {{ flex:1; background:#fff; border:1px solid #ECECEE; border-radius:18px; padding:22px 24px; }}
.db-tile small {{ display:flex; align-items:center; gap:8px; font-size:17px; color:#6B7280; font-weight:600; }}
.db-tile b {{ display:block; font-size:56px; font-weight:800; margin-top:10px; font-variant-numeric:tabular-nums; }}
.db-chart {{ margin-top:22px; height:340px; background:#fff; border:1px solid #ECECEE; border-radius:18px; padding:20px; }}
.db-chart svg {{ width:100%; height:100%; }} .db-chart .grid {{ stroke:#F0F0F2; stroke-width:2; fill:none; }}
#db-line {{ stroke:var(--p); stroke-width:6; fill:none; stroke-linecap:round; stroke-dasharray:1; stroke-dashoffset:1; }}
"""
