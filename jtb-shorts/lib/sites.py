"""Example business pages shown inside the phone: the modern mobile site, a booking
sheet, a local results page and a Business Profile. Authored at 390 px (real
phone width) and scaled by the frame.

Design rules so they read as real sites, not drawings:
  - a photo-style hero (art.py) with the headline over it, never an icon in a blob
  - real microcopy: rating + review count, hours, what each service includes
  - one primary action, one secondary, a sticky call bar
Every id is prefixed with px so a page can appear on several screens of one video.
Ids the templates aim the camera at are listed in each docstring.
"""
from brand import icon, C
from mocks import niche_vars, FIXED, RING, esc
from art import scene

STAR = lambda s=15: icon("star", s, "#F5B301")

def _initial(n): return esc(n["short"][0])

# ----------------------------------------------------------------- the modern mobile site
def site_mobile(n, px="", hero_title=None, buttons=True, callbar=True, reviews=True, booking=False):
    """Camera / ring ids: {px}h1, {px}sm-btns, {px}sm-cta, {px}sm-rev, {px}sm-bar, {px}sm-svc.
    Rings: {px}ring-h1, {px}ring-btns, {px}ring-rev, {px}ring-bar."""
    k = n["_key"]
    rate = (f'<span class="sm-rate">{STAR(14)} {n["rating"]} · {n["reviews"]} Google reviews</span>') if reviews else \
           f'<span class="sm-rate">{esc(n["city"])} · {esc(n["label"])}</span>'
    btns = (f'<div class="sm-btns hl" id="{px}sm-btns">{RING.format(px + "ring-btns")}'
            f'<span class="sm-cta" id="{px}sm-cta">{esc(n["cta_label"])} {icon("arrow", 18, "#fff", 2.6)}</span>'
            f'<span class="sm-call">{icon("phone", 17, "var(--p)", 2.4)} {esc(n["phone"])}</span></div>') if buttons else ""
    trust = "".join(f'<span>{icon("check", 13, "var(--p)", 3)} {esc(b)}</span>' for b in n["badges"])
    svc = "".join(f'<div class="sm-svc"><span class="ic">{icon(n["icon"], 20, "var(--p)")}</span>'
                  f'<span class="tx"><b>{esc(s)}</b><small>{esc(note)}</small></span><em>›</em></div>'
                  for s, note in zip(n["services"], n["service_notes"]))
    rev = (f'<div class="sm-rev hl" id="{px}sm-rev">{RING.format(px + "ring-rev")}<div class="top"><span class="av">D</span>'
           f'<span><b>Dana K.</b><small>2 weeks ago</small></span><span class="st">{STAR(14) * 5}</span></div>'
           f'<p>“Booked online in a minute and they were right on time. Easy.”</p>'
           f'<small class="all">See all {n["reviews"]} reviews ›</small></div>') if reviews else ""
    navcall = f'<span class="sm-navcall">{icon("phone", 15, "#fff", 2.4)} Call</span>' if callbar else f'{icon("menu", 24, "var(--ink)")}'
    bar = (f'<div class="sm-bar hl" id="{px}sm-bar" style="{niche_vars(n)}">{RING.format(px + "ring-bar")}'
           f'{icon("phone", 20, "#fff", 2.4)} Call {esc(n["phone"])}</div>') if callbar else ""
    sheet = booking_sheet(n, px) if booking else ""
    return f"""<div class="sm" style="{niche_vars(n)}">
  <div class="sm-nav"><span class="sm-logo"><i>{_initial(n)}</i>{esc(n["short"])}</span>{navcall}</div>
  <div class="sm-hero"><div class="sm-photo">{scene(k, px + "hero")}</div><div class="sm-shade"></div>
    <div class="sm-htext">{rate}<h1 class="hl" id="{px}h1">{RING.format(px + "ring-h1")}{esc(hero_title or n["headline"])}</h1><p>{esc(n["sub"])}</p></div></div>
  {btns}
  <div class="sm-trust">{trust}</div>
  <div class="sm-sec" id="{px}sm-svc"><h3>Services</h3>{svc}</div>
  {rev}
  <div class="sm-foot">{esc(n["business"])} · {esc(n["city"])} · {esc(n["hours"])}</div>
</div>{FIXED}{bar}{sheet}<span class="tap" id="{px}tap"></span>"""

def booking_sheet(n, px=""):
    """Bottom sheet: ids {px}bk (sheet), {px}bk-d{0..4} days, {px}bk-s{0..5} slots, {px}bk-go, {px}bk-done."""
    days = [("Mon", "14"), ("Tue", "15"), ("Wed", "16"), ("Thu", "17"), ("Fri", "18")]
    slots = ["8:30 AM", "9:15 AM", "10:00 AM", "11:30 AM", "1:45 PM", "3:30 PM"]
    d = "".join(f'<span class="bk-day{" on" if i == 1 else ""}" id="{px}bk-d{i}"><small>{a}</small><b>{b}</b></span>' for i, (a, b) in enumerate(days))
    s = "".join(f'<span class="bk-slot" id="{px}bk-s{i}">{t}</span>' for i, t in enumerate(slots))
    return f"""<div class="bk" id="{px}bk" style="{niche_vars(n)}"><i class="bk-grab"></i>
  <div class="bk-h"><b>{esc(n["cta_label"])}</b><small>{esc(n["business"])}</small></div>
  <div class="bk-seg"><b>New patient</b><span>Returning</span></div>
  <div class="bk-lbl">October</div><div class="bk-days">{d}</div>
  <div class="bk-lbl">Available times</div><div class="bk-slots" id="{px}bk-slots">{s}</div>
  <div class="bk-go" id="{px}bk-go">Confirm Tue 10:00 AM</div>
  <div class="bk-done" id="{px}bk-done"><span class="ok">{icon("check", 44, "#fff", 3.2)}</span><b>You're booked</b>
    <span class="when">Tue, Oct 15 · 10:00 AM</span><small>Confirmation sent by text</small></div>
</div>"""

# ----------------------------------------------------------------- local results page (generic layout, no logos)
def serp(n, query_html=""):
    """ids: sp-q, sp-caret, sp-map, sp-you, sp-ring0..2, sp-p0..2 (pins), sp-dl0..2 (distance tags),
    sp-r0..2 (rows), sp-cat1 / sp-svc1 (marker targets on your row), sp-rate0..2, ring-sp-mine, sp-places."""
    names = [n["competitors"][0], n["business"], n["competitors"][1]]
    dist = ["0.8 mi", "2.6 mi", "1.4 mi"]
    rates = [("4.7", 86), (n["rating"], n["reviews"]), ("4.6", 41)]
    rows = ""
    for i, nm in enumerate(names):
        mine = i == 1
        svc = " · ".join(n["services"][:2])
        mk = '<i class="mk"></i>' if mine else ""        # only your listing gets the "matches the search" marker
        rows += (f'<div class="sp-row{" mine hl" if mine else ""}" id="sp-r{i}">{RING.format("ring-sp-mine") if mine else ""}'
                 f'<div class="sp-main"><b>{esc(nm)}</b>'
                 f'<div class="sp-rt" id="sp-rate{i}"><em>{rates[i][0]}</em>{STAR(14) * 5}<span>({rates[i][1]})</span></div>'
                 f'<small><span class="hlt" id="sp-cat{i}">{mk}{esc(n["category"])}</span> · <span id="sp-dist{i}">{dist[i]}</span> · {esc(n["hours"].replace("Open · ", "Open · "))}</small>'
                 f'<small class="svc"><span class="hlt" id="sp-svc{i}">{mk}{esc(svc)}</span></small></div>'
                 f'<div class="sp-acts"><span>{icon("globe", 18, "#1A73E8")}</span><span>{icon("dir", 18, "#1A73E8")}</span></div></div>')
    pins = "".join(f'<span class="pinw p{i + 1}" id="sp-p{i}"><span class="pin{" mine" if i == 1 else ""}">{icon("pin", 22, "#fff", 2.2)}</span>'
                   f'<span class="dtag" id="sp-dl{i}">{dist[i]}</span></span>' for i in range(3))
    rings = "".join(f'<circle id="sp-ring{i}" cx="118" cy="150" r="{36 + 52 * i}" fill="none" stroke="#1A73E8" stroke-width="2" stroke-dasharray="5 6" opacity="0"/>' for i in range(3))
    return f"""<div class="sp">
  <div class="sp-search" id="sp-bar">{icon("search", 22, "#5F6368")}<span id="sp-q">{query_html}</span><i id="sp-caret"></i></div>
  <div class="sp-tabs"><b>All</b><span>Maps</span><span>Images</span><span>Reviews</span></div>
  <div class="sp-map" id="sp-map"><svg viewBox="0 0 390 230" preserveAspectRatio="none">
      <rect width="390" height="230" fill="#E8EEE3"/><path d="M0 150 C90 130 150 170 240 128 S340 90 390 104" stroke="#fff" stroke-width="12" fill="none"/>
      <path d="M128 0 C138 80 108 140 160 230" stroke="#fff" stroke-width="8" fill="none"/><path d="M310 0 L280 230" stroke="#FCE8B2" stroke-width="10" fill="none"/>
      <rect x="200" y="20" width="70" height="44" rx="6" fill="#D5E6CB"/><rect x="30" y="176" width="80" height="40" rx="6" fill="#D5E6CB"/>{rings}</svg>
    <span class="you" id="sp-you"><i></i></span>{pins}</div>
  <div class="sp-places" id="sp-places"><b>Places</b><span>Rating</span><span>Open now</span></div>
  <div class="sp-list">{rows}</div>
</div>"""

# ----------------------------------------------------------------- Business Profile (generic layout)
def gbp(n, reply_html=""):
    """ids: gb-head, gb-photos (section), gb-ph0..3 (tiles), gb-reviews (section), gb-reply, gb-rq (typed reply text),
    gb-info (section), gb-hrs-old / gb-hrs-new, gb-hol (holiday row), gb-upd (updated badge)."""
    k = n["_key"]
    tiles = "".join(f'<span class="gb-ph" id="gb-ph{i}">{scene(k, f"gbp{i}", v)}<em>{lbl}</em></span>'
                    for i, (v, lbl) in enumerate([(1, "Patio · this week"), (2, "Garden bed"), (0, "Lawn renovation"), (3, "Stone path")]))
    info = [("pin", f"210 Main St, {esc(n['city'])}"), ("phone", esc(n["phone"])), ("globe", "fieldstone.com" if k == "landscaping" else esc(n["short"].lower()) + ".com")]
    rows = "".join(f'<div class="gb-row">{icon(ic, 20, "#5F6368")}<span>{t}</span></div>' for ic, t in info)
    return f"""<div class="gb" style="{niche_vars(n)}">
  <div class="gb-cover">{scene(k, "gbcover", 0)}</div>
  <div class="gb-head" id="gb-head"><h3>{esc(n['business'])}</h3>
    <div class="gb-rt"><b>{n["rating"]}</b>{STAR(15) * 5}<span>({n["reviews"]})</span></div>
    <small>{esc(n['category'])} in {esc(n['city'])}</small></div>
  <div class="gb-acts"><span>{icon("phone", 22, "#1A73E8")}<em>Call</em></span><span>{icon("dir", 22, "#1A73E8")}<em>Directions</em></span>
    <span>{icon("globe", 22, "#1A73E8")}<em>Website</em></span><span>{icon("star", 22, "#1A73E8")}<em>Review</em></span></div>
  <div class="gb-tabs"><b>Overview</b><span>Reviews</span><span>Photos</span><span>Updates</span></div>
  <div class="gb-sec" id="gb-photos"><h4>Photos <small>Recent work</small></h4><div class="gb-grid">{tiles}</div></div>
  <div class="gb-sec" id="gb-reviews"><h4>Reviews</h4>
    <div class="gb-rev"><div class="top"><span class="av">D</span><span><b>Dana K.</b><small>2 days ago</small></span></div>
      <div class="st">{STAR(15) * 5}</div><p>Our backyard looks incredible. On time, tidy and a fair price.</p>
      <div class="gb-reply" id="gb-reply"><b>Response from the owner</b><p id="gb-rq">{reply_html}</p></div></div></div>
  <div class="gb-sec" id="gb-info"><h4>About <span class="upd" id="gb-upd">{icon("check", 14, "#188038", 3)} Updated today</span></h4>
    <div class="gb-row">{icon("clock", 20, "#5F6368")}<span class="hrs"><span class="old" id="gb-hrs-old">Closes 5 PM<i class="strike" id="gb-strike"></i></span><b id="gb-hrs-new">Mon–Sat · 7 AM – 6 PM</b></span></div>
    <div class="gb-row hol" id="gb-hol">{icon("spark", 20, "#5F6368")}<span>Holiday hours added</span></div>{rows}
    <div class="gb-row">{icon("dir", 20, "#5F6368")}<span>Serves {esc(n['city'])} + 15 mi</span></div></div>
  <div class="gb-sec" id="gb-posts"><h4>Updates <small>from the owner</small></h4>
    <div class="gb-post"><span class="ph">{scene(k, "gbpost", 2)}</span><span><b>Fall cleanups are booking now</b>
      <small>Leaf removal, bed cutbacks and a final mow. Free estimates this month.</small><em>Book online ›</em></span></div></div>
</div>"""

SITES_CSS = f"""
/* modern mobile site (v2) */
.sm {{ font-family:"Inter", sans-serif; color:var(--ink); background:#fff; padding-bottom:96px; }}
.sm-nav {{ height:96px; padding:44px 16px 0; display:flex; align-items:center; justify-content:space-between; }}
.sm-logo {{ display:flex; align-items:center; gap:9px; font-family:"Montserrat", sans-serif; font-weight:800; font-size:19px; letter-spacing:-.01em; }}
.sm-logo i {{ width:32px; height:32px; border-radius:10px; background:var(--p); color:#fff; font-style:normal; font-size:17px;
              display:flex; align-items:center; justify-content:center; }}
.sm-navcall {{ display:flex; align-items:center; gap:6px; height:34px; padding:0 14px; border-radius:17px; background:var(--p); color:#fff; font-weight:700; font-size:14px; }}
.sm-hero {{ position:relative; margin:0 12px; height:372px; border-radius:24px; overflow:hidden; }}
.sm-photo {{ position:absolute; inset:0; }}
.sm-shade {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(0,0,0,0) 38%, rgba(6,10,14,.5) 62%, rgba(6,10,14,.84) 100%); }}
.sm-htext {{ position:absolute; left:20px; right:20px; bottom:22px; color:#fff; }}
.sm-rate {{ display:inline-flex; align-items:center; gap:5px; padding:6px 11px; border-radius:999px; background:rgba(255,255,255,.94); color:#1F2328;
            font-size:12.5px; font-weight:700; }}
.sm-htext h1 {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:33px; line-height:1.06; letter-spacing:-.022em; margin:12px 0 8px; }}
.sm-htext p {{ font-size:15px; line-height:1.4; color:rgba(255,255,255,.88); }}
.sm-btns {{ display:flex; flex-direction:column; gap:10px; margin:16px 16px 0; }}
.sm-cta {{ height:56px; border-radius:16px; background:var(--p); color:#fff; font-weight:700; font-size:17.5px; display:flex; align-items:center; justify-content:center; gap:8px;
           box-shadow:0 8px 20px color-mix(in srgb, var(--p) 35%, transparent); }}
.sm-call {{ height:50px; border-radius:16px; border:1.5px solid #D9DEE4; color:var(--ink); font-weight:700; font-size:16px; display:flex; align-items:center; justify-content:center; gap:8px; }}
.sm-trust {{ display:flex; justify-content:center; gap:16px; margin:14px 16px 4px; font-size:12.5px; font-weight:600; color:#4B5563; }}
.sm-trust span {{ display:flex; align-items:center; gap:5px; }}
.sm-sec {{ padding:14px 16px 2px; }}
.sm-sec h3 {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:21px; margin-bottom:6px; }}
.sm-svc {{ display:flex; align-items:center; gap:12px; padding:11px 0; border-bottom:1px solid #EEF0F3; }}
.sm-svc .ic {{ width:42px; height:42px; border-radius:12px; background:color-mix(in srgb, var(--p) 10%, #fff); display:flex; align-items:center; justify-content:center; flex:none; }}
.sm-svc .tx {{ flex:1; display:flex; flex-direction:column; }} .sm-svc b {{ font-size:15.5px; }} .sm-svc small {{ font-size:12.5px; color:#6B7280; margin-top:2px; }}
.sm-svc em {{ font-style:normal; color:#9CA3AF; font-size:22px; }}
.sm-rev {{ margin:16px 16px 0; padding:16px; border-radius:18px; background:#F6F7F8; }}
.sm-rev .top {{ display:flex; align-items:center; gap:10px; }} .sm-rev .top > span:nth-child(2) {{ display:flex; flex-direction:column; flex:1; }}
.sm-rev .av {{ width:34px; height:34px; border-radius:50%; background:#F4C7A1; color:#7A3E12; font-weight:800; display:flex; align-items:center; justify-content:center; }}
.sm-rev b {{ font-size:14px; }} .sm-rev small {{ font-size:12px; color:#6B7280; }}
.sm-rev .st {{ display:flex; gap:1px; }} .sm-rev p {{ font-size:15px; line-height:1.42; margin:10px 0 8px; }}
.sm-rev .all {{ color:var(--p); font-weight:700; }}
.sm-foot {{ padding:18px 16px; font-size:11.5px; color:#9CA3AF; }}
.sm-bar, .sm-bar.hl {{ position:absolute; left:12px; right:12px; top:{int(1012 / (492 / 390)) - 72}px; height:58px; border-radius:18px; background:var(--p);
           color:#fff; font-weight:700; font-size:17px; display:flex; align-items:center; justify-content:center; gap:10px; box-shadow:0 10px 30px rgba(0,0,0,.25); }}
.tap {{ position:absolute; left:0; top:0; width:54px; height:54px; margin:-27px 0 0 -27px; border-radius:50%; background:rgba(255,255,255,.55);
        box-shadow:0 0 0 2px rgba(17,24,39,.35), 0 6px 18px rgba(0,0,0,.25); opacity:0; z-index:9; }}

/* booking sheet */
.bk {{ position:absolute; left:0; right:0; top:236px; height:{int(1012 / (492 / 390)) - 236 + 40}px; background:#fff; border-radius:26px 26px 0 0; z-index:8;
       box-shadow:0 -20px 50px rgba(0,0,0,.28); padding:12px 18px 0; font-family:"Inter", sans-serif; color:var(--ink); }}
.bk-grab {{ display:block; width:44px; height:5px; border-radius:3px; background:#D7DBE0; margin:0 auto 14px; }}
.bk-h {{ display:flex; flex-direction:column; }} .bk-h b {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:23px; }}
.bk-h small {{ color:#6B7280; font-size:13px; margin-top:2px; }}
.bk-seg {{ display:flex; margin:14px 0 4px; padding:4px; border-radius:12px; background:#F1F3F5; font-size:14px; font-weight:700; }}
.bk-seg b, .bk-seg span {{ flex:1; height:36px; display:flex; align-items:center; justify-content:center; border-radius:9px; }}
.bk-seg b {{ background:#fff; box-shadow:0 1px 3px rgba(0,0,0,.12); }} .bk-seg span {{ color:#6B7280; }}
.bk-lbl {{ font-size:13px; font-weight:700; color:#6B7280; margin:14px 0 8px; text-transform:uppercase; letter-spacing:.06em; }}
.bk-days {{ display:flex; gap:8px; }}
.bk-day {{ flex:1; height:64px; border-radius:14px; border:1.5px solid #E3E7EB; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.bk-day small {{ font-size:12px; color:#6B7280; font-weight:600; }} .bk-day b {{ font-size:20px; }}
.bk-day.on {{ background:var(--p); border-color:var(--p); color:#fff; }} .bk-day.on small {{ color:rgba(255,255,255,.85); }}
.bk-slots {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; }}
.bk-slot {{ height:48px; border-radius:12px; border:1.5px solid #E3E7EB; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:15px; }}
.bk-go {{ margin-top:18px; height:56px; border-radius:16px; background:var(--p); color:#fff; font-weight:700; font-size:17px; display:flex; align-items:center; justify-content:center; }}
.bk-done {{ position:absolute; inset:0; border-radius:26px 26px 0 0; background:#fff; display:flex; flex-direction:column; align-items:center; padding-top:84px; opacity:0; }}
.bk-done .ok {{ width:96px; height:96px; border-radius:50%; background:#16A34A; display:flex; align-items:center; justify-content:center;
                box-shadow:0 12px 30px rgba(22,163,74,.35); }}
.bk-done b {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:30px; margin-top:22px; }}
.bk-done .when {{ font-size:18px; font-weight:700; margin-top:8px; }} .bk-done small {{ font-size:14px; color:#6B7280; margin-top:6px; }}

/* local results page (v2) */
.sp {{ font-family:"Inter", sans-serif; background:#fff; color:#202124; padding-top:54px; }}
.sp-search {{ margin:0 14px; height:52px; border-radius:26px; box-shadow:0 1px 6px rgba(32,33,36,.28); display:flex; align-items:center; gap:12px; padding:0 18px; font-size:18px; }}
#sp-caret {{ width:2px; height:22px; background:#1A73E8; margin-left:-10px; }}
.sp-tabs {{ display:flex; gap:22px; padding:14px 20px 0; font-size:14px; color:#5F6368; border-bottom:1px solid #EBEBEB; }}
.sp-tabs b {{ color:#1A73E8; padding-bottom:10px; border-bottom:3px solid #1A73E8; font-weight:600; }}
.sp-map {{ position:relative; height:230px; margin:12px 14px 4px; border-radius:16px; overflow:hidden; }}
.sp-map svg {{ position:absolute; inset:0; width:100%; height:100%; }}
.sp-map .you {{ position:absolute; left:{118 - 11}px; top:{150 - 11}px; width:22px; height:22px; border-radius:50%; background:rgba(26,115,232,.25); }}
.sp-map .you i {{ position:absolute; inset:5px; border-radius:50%; background:#1A73E8; box-shadow:0 0 0 2px #fff; }}
.sp-map .pinw {{ position:absolute; width:34px; height:34px; }}
.sp-map .pin {{ position:absolute; inset:0; border-radius:50% 50% 50% 0; transform:rotate(-45deg); background:#EA4335;
                display:flex; align-items:center; justify-content:center; box-shadow:0 4px 10px rgba(0,0,0,.25); }}
.sp-map .pin svg {{ transform:rotate(45deg); }}
.sp-map .pin.mine {{ background:#C5221F; }}
.sp-map .p1 {{ left:168px; top:96px; }} .sp-map .p2 {{ left:318px; top:46px; }} .sp-map .p3 {{ left:44px; top:44px; }}
.sp-map .dtag {{ position:absolute; left:40px; top:4px; white-space:nowrap; padding:3px 8px; border-radius:8px; background:#fff; font-size:13px; font-weight:700;
                 color:#1A73E8; box-shadow:0 2px 6px rgba(0,0,0,.2); opacity:0; }}
.sp-map .p2 .dtag {{ left:-70px; top:34px; }}
.sp-places {{ display:flex; align-items:center; gap:8px; padding:12px 18px 6px; }}
.sp-places b {{ font-size:19px; font-weight:600; flex:1; }}
.sp-places span {{ font-size:13px; padding:6px 12px; border:1px solid #DADCE0; border-radius:16px; color:#3C4043; }}
.sp-row {{ position:relative; display:flex; justify-content:space-between; padding:13px 18px; border-bottom:1px solid #EFEFEF; }}
.sp-row b {{ font-size:18px; color:#1A0DAB; font-weight:600; }}
.sp-row.mine {{ background:#FFF8EC; }}
.sp-rt {{ display:inline-flex; align-items:center; gap:1px; margin:5px 0 3px; padding:1px 2px; border-radius:6px; position:relative; }}
.sp-rt em {{ font-style:normal; font-size:14px; color:#3C4043; margin-right:4px; font-weight:600; }} .sp-rt span {{ font-size:14px; color:#70757A; margin-left:4px; }}
.sp-row small {{ display:block; font-size:14px; color:#70757A; line-height:1.5; }}
.sp-row small.svc {{ color:#3C4043; }}
.hlt {{ position:relative; display:inline-block; }}
.hlt .mk {{ position:absolute; left:-3px; right:-3px; top:1px; bottom:1px; border-radius:4px; background:rgba(255,181,71,.6); mix-blend-mode:multiply; transform-origin:0 50%; }}
.sp-main {{ position:relative; z-index:0; }}
.sp-acts {{ display:flex; flex-direction:column; gap:10px; }}
.sp-acts span {{ width:40px; height:40px; border-radius:50%; border:1px solid #DADCE0; display:flex; align-items:center; justify-content:center; }}

/* Business Profile (v2) */
.gb {{ font-family:"Inter", sans-serif; background:#fff; color:#202124; padding-top:44px; padding-bottom:40px; }}
.gb-cover {{ height:150px; overflow:hidden; }}
.gb-head {{ padding:14px 18px 10px; }} .gb-head h3 {{ font-size:23px; font-weight:600; }}
.gb-rt {{ display:flex; align-items:center; gap:2px; margin:5px 0; font-size:15px; }} .gb-rt b {{ margin-right:4px; }} .gb-rt span {{ color:#70757A; margin-left:4px; }}
.gb-head small {{ font-size:14px; color:#70757A; }}
.gb-acts {{ display:flex; justify-content:space-around; padding:10px 8px; }}
.gb-acts span {{ display:flex; flex-direction:column; align-items:center; gap:4px; }}
.gb-acts em {{ font-style:normal; font-size:12px; color:#1A73E8; font-weight:600; }}
.gb-tabs {{ display:flex; gap:20px; padding:10px 18px 0; border-bottom:1px solid #EBEBEB; font-size:14px; color:#5F6368; }}
.gb-tabs b {{ color:#1A73E8; padding-bottom:9px; border-bottom:3px solid #1A73E8; font-weight:600; }}
.gb-sec {{ padding:16px 18px 14px; border-bottom:8px solid #F1F3F4; }}
.gb-sec h4 {{ display:flex; align-items:center; gap:8px; font-size:18px; font-weight:600; margin-bottom:12px; }}
.gb-sec h4 small {{ font-size:13px; color:#70757A; font-weight:500; }}
.gb-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
.gb-ph {{ position:relative; height:128px; border-radius:12px; overflow:hidden; background:#E8EAED; }}
.gb-ph em {{ position:absolute; left:8px; bottom:8px; padding:4px 8px; border-radius:8px; background:rgba(0,0,0,.6); color:#fff; font-style:normal; font-size:11.5px; font-weight:600; }}
.gb-rev .top {{ display:flex; align-items:center; gap:10px; }} .gb-rev .top > span:nth-child(2) {{ display:flex; flex-direction:column; }}
.gb-rev .av {{ width:36px; height:36px; border-radius:50%; background:#C7E3B8; color:#2D5A1E; font-weight:800; display:flex; align-items:center; justify-content:center; }}
.gb-rev b {{ font-size:15px; }} .gb-rev small {{ font-size:12.5px; color:#70757A; }}
.gb-rev .st {{ display:flex; gap:1px; margin:8px 0 4px; }} .gb-rev p {{ font-size:15.5px; line-height:1.42; }}
.gb-reply {{ margin-top:12px; padding:12px 14px; border-radius:12px; background:#F1F3F4; min-height:92px; }}
.gb-reply b {{ font-size:13px; color:#5F6368; }} .gb-reply p {{ font-size:15.5px; line-height:1.42; margin-top:4px; white-space:pre-wrap; }}
#gb-rq .ch {{ display:none; }}
.gb-row {{ display:flex; align-items:center; gap:14px; padding:9px 0; font-size:15.5px; }}
.gb-row .hrs {{ display:flex; flex-direction:column; }} .gb-row .hrs .old {{ position:relative; align-self:flex-start; color:#5F6368; font-size:14px; }}
.gb-row .hrs .strike {{ position:absolute; left:-2px; right:-2px; top:52%; height:2px; background:#D93025; transform-origin:0 50%; }} .gb-row .hrs b {{ font-weight:600; color:#188038; }}
.gb-row.hol span {{ font-weight:600; }}
.gb-post {{ display:flex; gap:12px; }} .gb-post .ph {{ width:110px; height:110px; border-radius:12px; overflow:hidden; flex:none; }}
.gb-post > span:last-child {{ display:flex; flex-direction:column; gap:4px; }} .gb-post b {{ font-size:15.5px; }}
.gb-post small {{ font-size:13.5px; color:#5F6368; line-height:1.35; }} .gb-post em {{ font-style:normal; font-size:14px; font-weight:700; color:#1A73E8; }}
.upd {{ display:inline-flex; align-items:center; gap:4px; margin-left:auto; padding:4px 10px; border-radius:999px; background:#E6F4EA; color:#188038; font-size:12.5px; font-weight:700; }}
"""
