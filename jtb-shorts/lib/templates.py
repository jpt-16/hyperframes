"""The video templates. Each one has:

    SEGMENTS(spec) -> [(name, seconds), ...]   body scenes after the hook (CTA not included)
    build(c, spec, niche, T)                     T = {name: start time}, plus T["cta"]

Scene starts are snapped to a grid (the beat with music, quarter seconds without).
Copy comes from the spec; anything left out falls back to the defaults below,
which are written to be accurate (no ranking or results promises).

Pacing rules these follow: one idea per beat, one callout on screen at a time,
the camera punches in on the part of the phone that the beat is about (sized to
read on a phone), and nothing sits still for more than about a second.
"""
from comp import o, R
from scenes import (hook, head, chip, ring, wipe_in, scroll, brandbar, cta, type_into, typing,
                    cam_to, cam_home, scroll_to, tap, callout, numeral)
from mocks import phone, browser, site_desktop, site_old, screen_slow, screen_wall, dashboard, domain, PHONE, BROWSER
from sites import site_mobile, serp, gbp

HOOK = 2.0          # hook length before snapping
CTA_LEN = 3.0

# ----------------------------------------------------------------- the stage: device inside the camera, scrim over it
def stage(c, t1, device_html, z=10):
    c.clip("dev", 0, t1, f'<div id="cam">{device_html}</div>', cls="layer", style=f"z-index:{z}")
    c.clip("scrim-l", 1.0, t1, '<div class="scrim"></div>', cls="layer", style="z-index:25")

def device_in(c, sel, t_land, scale=1.0):
    """Rises under the hook from frame 0, then lands as the first body scene starts."""
    c.ft(sel, o(y=1180, rotationX=26, transformPerspective=1800, scale=scale, opacity=1),
         o(y=780, rotationX=22, duration=t_land - 0.32, ease="power2.out"), 0.0)
    c.to(sel, o(y=0, rotationX=0, duration=0.85, ease="expo.out"), t_land - 0.3)

def device_clip(c, cid, t1, inner):
    c.clip(cid, 0, t1, inner, cls="layer", style="z-index:10")

def opening(c, s, t_land, z):
    hook(c, s["hook"], t_land)
    brandbar(c, t_land, z)
    c.cue("riser-m", t_land, -4.0)

# ================================================================= 1. website redesign (before -> after -> booking)
def redesign_segments(s):
    seg = [("before", 3.0), ("after", 3.2 if s.get("booking") else 4.2)]
    if s.get("booking"): seg.append(("book", 3.6))
    return seg

def redesign(c, s, n, T):
    b, a, k, z = T["before"], T["after"], T.get("book"), T["cta"]
    screens = [("s-old", site_old(n, "mobile"), ""), ("s-new", site_mobile(n, px="n-", booking=bool(s.get("booking"))), "wipe")]
    stage(c, z + 0.3, phone("ph", screens))
    device_in(c, "#ph", b)
    opening(c, s, b, z)

    B = s["before"]
    head(c, "hb", b, a, B.get("eyebrow", "Before"), B["head"], "bad")
    c.to("#s-old-scr", o(scale=2.2, transformOrigin="14% 18%", duration=0.8, ease="power3.inOut"), b + 0.35)
    c.to("#s-old-scr", o(scale=1, duration=0.6, ease="power3.inOut"), a - 0.75)
    probs = B["problems"][:2]
    for i, p in enumerate(probs):
        t0 = b + 0.6 + i * 1.15
        callout(c, f"cb{i}", t0, (t0 + 1.05) if i < len(probs) - 1 else a - 0.12, p, "bad")

    A = s["after"]; end_after = k or z
    head(c, "ha", a, end_after, A.get("eyebrow", "After"), A["head"], "good")
    wipe_in(c, "s-new", a - 0.15)
    fixes = [f if isinstance(f, dict) else {"text": f} for f in A["fixes"]]
    # fix 1: what you do, up top
    cam_to(c, a + 0.35, 0.6, "n-h1", 1.3, cy=950)
    ring(c, "n-ring-h1", a + 0.5, a + 1.45)
    callout(c, "ca0", a + 0.5, a + 1.45, fixes[0]["text"], "good", fixes[0].get("sub"))
    # fix 2: the primary action
    cam_to(c, a + 1.45, 0.55, "n-sm-btns", 1.45, cy=930)
    ring(c, "n-ring-btns", a + 1.6, end_after - 0.1)
    callout(c, "ca1", a + 1.6, (a + 2.8) if not k else end_after - 0.1, fixes[1]["text"], "good", fixes[1].get("sub"))
    if not k and len(fixes) > 2:      # no booking beat: show the reviews instead
        sy = scroll_to(c, a + 2.7, 0.7, "s-new", "n-sm-rev", top=330)
        cam_to(c, a + 2.7, 0.7, "n-sm-rev", 1.35, cy=930, scroll=sy)
        ring(c, "n-ring-rev", a + 3.2, z - 0.15)
        callout(c, "ca2", a + 3.2, z - 0.15, fixes[2]["text"], "good", fixes[2].get("sub"))

    if k:   # booking: tap the button, the sheet comes up, pick a time, confirmed
        K = s["booking"]
        head(c, "hk2", k, z, K.get("eyebrow", "Booking"), K["head"], "good")
        tap(c, "n-", k + 0.15, "n-sm-cta")
        c.ft("#n-bk", o(yPercent=104), o(yPercent=0, duration=0.55, ease="power3.out"), k + 0.3)
        c.cue("whoosh", k + 0.45, -9.0)
        cam_to(c, k + 0.3, 0.7, "n-bk-slots", 1.42, cy=930)
        tap(c, "n-", k + 1.05, "n-bk-s2")
        c.to("#n-bk-s2", o(backgroundColor=n["colors"]["primary"], color="#ffffff", borderColor=n["colors"]["primary"], duration=0.12), k + 1.05)
        tap(c, "n-", k + 1.6, "n-bk-go")
        c.ft("#n-bk-done", o(opacity=0), o(opacity=1, duration=0.3, ease="power2.out"), k + 1.72)
        c.ft("#n-bk-done .ok", o(scale=0.4), o(scale=1, duration=0.5, ease="back.out(2.2)"), k + 1.72)
        c.cue("bubble", k + 1.72, -3.0); c.cue("popup", k + 1.8, -5.0)
        callout(c, "cbk", k + 2.0, z - 0.12, K["callout"], "good", K.get("sub"), ic="cal", sfx=False)
    cta(c, z, s["cta"])

# ================================================================= 2. local SEO: the three local factors
FACTORS = [
    dict(name="Relevance", head="*Relevance*: do you match the search?", callout="Match your category + services", sub="List exactly what you do"),
    dict(name="Distance", head="*Distance*: how close you are.", callout="You can't control this one", sub="It depends on where they're searching", kind="mute", ic="lock"),
    dict(name="Prominence", head="*Prominence*: how well-known you are.", callout="Reviews, links, mentions", sub="Built over time, not bought", ic="star"),
]

def local_seo_segments(s):
    return [("search", 2.6), ("f0", 2.5), ("f1", 2.5), ("f2", 2.6)]

def local_seo(c, s, n, T):
    q, z = T["search"], T["cta"]
    query = s.get("query", n["query"])
    spans, _, _ = typing(query, 0)
    stage(c, z + 0.3, phone("ph", [("s-serp", serp(n, spans), "")]))
    device_in(c, "#ph", q)
    opening(c, s, q, z)

    S = s["search"]
    head(c, "hs", q, T["f0"], S.get("eyebrow", "Local SEO"), S["head"])
    c.ft("#sp-caret", o(opacity=1), o(opacity=0, duration=0.18, ease="steps(1)", repeat=3, yoyo=True), q - 0.4)
    cam_to(c, q + 0.05, 0.55, "sp-bar", 1.45, cy=820)
    te = type_into(c, query, q + 0.35, cps=24)
    cam_home(c, te + 0.05, 0.6)
    c.ft("#sp-map", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.45, ease="power2.out"), te + 0.1)
    c.ft("#s-serp .pinw", o(opacity=0, y=-26), o(opacity=1, y=0, duration=0.45, ease="back.out(2)", stagger=0.1), te + 0.25)
    for i in range(3): c.cue("bubble", te + 0.25 + 0.1 * i, -4.0)
    c.ft("#sp-you", o(opacity=0, scale=0.3), o(opacity=1, scale=1, duration=0.4, ease="back.out(2)"), te + 0.5)
    c.ft("#s-serp .sp-row", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.4, ease="power2.out", stagger=0.08), te + 0.2)
    c.ft("#sp-places", o(opacity=0), o(opacity=1, duration=0.35), te + 0.15)
    c.to("#sp-caret", o(opacity=0, duration=0.15), te + 0.1)

    F = [dict(d, **u) for d, u in zip(FACTORS, s.get("factors", [{}, {}, {}]))]
    keys = ["f0", "f1", "f2"]
    for i, f in enumerate(F):
        t0 = T[keys[i]]; t1 = T[keys[i + 1]] if i < 2 else z
        numeral(c, f"nm{i}", t0, t1 - 0.1, i + 1)
        head(c, f"hf{i}", t0, t1, f.get("eyebrow", f"Factor {i + 1} of 3"), f["head"], "")
        callout(c, f"cf{i}", t0 + 0.85, t1 - 0.12, f["callout"], f.get("kind", "acc"), f.get("sub"), ic=f.get("ic"))
    # relevance: your listing, with the words that match the search marked
    t0 = T["f0"]
    cam_to(c, t0 - 0.05, 0.65, "sp-r1", 1.6, cy=960)
    ring(c, "ring-sp-mine", t0 + 0.35, T["f1"] - 0.2)
    c.ft("#sp-cat1 .mk", o(scaleX=0), o(scaleX=1, duration=0.35, ease="power2.out"), t0 + 0.5)
    c.ft("#sp-svc1 .mk", o(scaleX=0), o(scaleX=1, duration=0.45, ease="power2.out"), t0 + 0.7)
    c.cue("popup", t0 + 0.5, -10.0)
    # distance: the map, rings out from the searcher, the miles on each pin
    t0 = T["f1"]
    cam_to(c, t0 - 0.05, 0.65, "sp-map", 1.5, cy=930)
    for i in range(3):
        c.ft(f"#sp-ring{i}", o(opacity=0, attr=R("{ r: 0 }")), o(opacity=0.9, attr=R(f"{{ r: {36 + 52 * i} }}"), duration=0.7, ease="power2.out"), t0 + 0.35 + 0.12 * i)
    c.ft("#s-serp .dtag", o(opacity=0, y=6), o(opacity=1, y=0, duration=0.3, ease="back.out(2)", stagger=0.15), t0 + 0.6)
    for i in range(3): c.cue("bubble", t0 + 0.6 + 0.15 * i, -6.0)
    # prominence: the ratings and review counts, side by side
    t0 = T["f2"]
    cam_to(c, t0 - 0.05, 0.65, "sp-r1", 1.5, cy=930)
    c.to("#s-serp .sp-rt", o(backgroundColor="rgba(255,181,71,0.55)", boxShadow="0 0 0 2px rgba(232,140,20,0.9)", duration=0.3, stagger=0.14), t0 + 0.45)
    c.cue("popup", t0 + 0.45, -10.0)
    cta(c, z, s["cta"])

# ================================================================= 3. Business Profile tips
TIPS = [
    dict(eyebrow="Tip 1 of 3", head="Post *real* project photos.", callout="Your work, not stock photos", sub="Recent jobs, with a short caption", ic="camera"),
    dict(eyebrow="Tip 2 of 3", head="*Reply* to every review.", callout="The good ones and the bad ones", sub="Short, specific, by name", ic="reply",
         reply="Thanks Dana! The new patio turned out great. Enjoy it!"),
    dict(eyebrow="Tip 3 of 3", head="Keep your info *up to date*.", callout="Hours, holidays, service area", sub="Update it when anything changes", ic="clock"),
]

def gbp_tips_segments(s):
    return [("t0", 3.1), ("t1", 3.5), ("t2", 3.1)]

def gbp_tips(c, s, n, T):
    z = T["cta"]
    P = [dict(d, **u) for d, u in zip(TIPS, s.get("tips", [{}, {}, {}]))]
    reply = P[1]["reply"]
    spans, _, _ = typing(reply, 0, pid="rq")
    stage(c, z + 0.3, phone("ph", [("s-gbp", gbp(n, spans), "")]))
    device_in(c, "#ph", T["t0"])
    opening(c, s, T["t0"], z)
    keys = ["t0", "t1", "t2"]
    for i, p in enumerate(P):
        t0 = T[keys[i]]; t1 = T[keys[i + 1]] if i < 2 else z
        numeral(c, f"nm{i}", t0, t1 - 0.1, i + 1)
        head(c, f"ht{i}", t0, t1, p["eyebrow"], p["head"], "good")
        callout(c, f"ct{i}", t0 + (1.25 if i else 1.2), t1 - 0.12, p["callout"], "good", p.get("sub"), ic=p.get("ic"))
    # 1. photos: real jobs land in the grid one by one
    t0 = T["t0"]
    sy = scroll_to(c, t0 - 0.1, 0.6, "s-gbp", "gb-photos", top=96)
    cam_to(c, t0 - 0.05, 0.65, "gb-photos", 1.5, cy=900, scroll=sy)
    c.ft("#s-gbp .gb-ph", o(opacity=0, scale=0.7), o(opacity=1, scale=1, duration=0.42, ease="back.out(1.8)", stagger=0.16), t0 + 0.45)
    for i in range(4): c.cue("bubble", t0 + 0.45 + 0.16 * i, -6.0)
    # 2. reviews: the owner's reply types itself out
    t0 = T["t1"]
    sy = scroll_to(c, t0 - 0.1, 0.6, "s-gbp", "gb-reviews", top=96)
    cam_to(c, t0 - 0.05, 0.65, "gb-reviews", 1.6, cy=880, scroll=sy)
    c.ft("#gb-reply", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.35, ease="power2.out"), t0 + 0.4)
    type_into(c, reply, t0 + 0.6, cps=30, pid="rq")
    # 3. info: hours corrected, holiday hours added, marked updated
    t0 = T["t2"]
    sy = scroll_to(c, t0 - 0.1, 0.6, "s-gbp", "gb-info", top=96)
    cam_to(c, t0 - 0.05, 0.65, "gb-info", 1.6, cy=880, scroll=sy)
    c.ft("#gb-strike", o(scaleX=0), o(scaleX=1, duration=0.3, ease="power2.out"), t0 + 0.5)
    c.ft("#gb-hrs-new", o(opacity=0, y=8), o(opacity=1, y=0, duration=0.35, ease="power2.out"), t0 + 0.7)
    c.ft("#gb-hol", o(opacity=0, x=-10), o(opacity=1, x=0, duration=0.35, ease="power2.out"), t0 + 0.95)
    c.ft("#gb-upd", o(opacity=0, scale=0.6), o(opacity=1, scale=1, duration=0.4, ease="back.out(2)"), t0 + 1.15)
    c.cue("popup", t0 + 0.7, -9.0); c.cue("bubble", t0 + 1.15, -4.0)
    cta(c, z, s["cta"])

# ================================================================= 4. website mistakes (conversions)
def _sm(**kw): return lambda n, px: site_mobile(n, px=px, **kw)
MISTAKES = {
    "hidden-phone":    dict(bad=_sm(buttons=False, callbar=False), good=_sm(), target="sm-bar", ring="ring-bar", scroll_bad=-420, cy=1060,
                            mistake="Your phone number is *buried*.", fix="Tap-to-call on *every* screen.", why="A call button always in reach"),
    "no-cta":          dict(bad=_sm(buttons=False, callbar=False), good=_sm(), target="sm-btns", ring="ring-btns", scroll_bad=-160,
                            mistake="No clear *next step*.", fix="One obvious button up top.", why="Tell them exactly what to do"),
    "slow":            dict(bad=lambda n, px: screen_slow(px), good=_sm(), target="h1", ring="ring-h1", slow=True, bad_len=1.0,
                            mistake="It takes *forever* to load.", fix="Compress images. *Cut the bloat.*", why="Light pages load faster"),
    "not-mobile":      dict(bad=lambda n, px: site_old(n, "mobile"), good=_sm(), target="h1", ring="ring-h1", pinch=True,
                            mistake="Not built for *phones*.", fix="Design for the *thumb* first.", why="Readable without zooming"),
    "no-reviews":      dict(bad=_sm(reviews=False), good=_sm(), target="sm-rev", ring="ring-rev", scroll_bad=-300, scroll_good=True,
                            mistake="No *proof* you're any good.", fix="Put real *reviews* up front.", why="Proof right where they decide"),
    "generic-heading": dict(bad=_sm(hero_title="Welcome to our website!"), good=_sm(), target="h1", ring="ring-h1", bad_ring="ring-h1",
                            mistake="“Welcome to our *website*.”", fix="Say *what* you do and *where*.", why="Clear in three seconds"),
    "wall-of-text":    dict(bad=lambda n, px: screen_wall(n), good=_sm(), target="h1", ring="ring-h1", scroll_bad=-240,
                            mistake="A wall of *text*.", fix="Short lines. *Clear sections.*", why="Easy to scan on a phone"),
}

def mistakes_segments(s):
    return [(f"m{k}", 1.95 + MISTAKES[it["type"]].get("bad_len", 1.3)) for k, it in enumerate(s["items"][:3])]

def mistakes(c, s, n, T):
    items = s["items"][:3]; z = T["cta"]; K = len(items)
    screens = []
    for k, it in enumerate(items):
        M = MISTAKES[it["type"]]
        screens.append((f"s{k}b", M["bad"](n, f"b{k}-"), "bad" + (" wipe" if k else "")))
        screens.append((f"s{k}g", M["good"](n, f"g{k}-"), "wipe"))
    stage(c, z + 0.3, phone("ph", screens))
    first = T["m0"]
    device_in(c, "#ph", first)
    opening(c, s, first, z)
    for k, it in enumerate(items):
        M = MISTAKES[it["type"]]
        a = T[f"m{k}"]; nxt = T[f"m{k + 1}"] if k + 1 < K else z
        f = a + M.get("bad_len", 1.3)
        numeral(c, f"nm{k}", a, nxt - 0.1, k + 1)
        if k:
            cam_home(c, a - 0.4, 0.45)
            wipe_in(c, f"s{k}b", a - 0.15)
        head(c, f"hb{k}", a, f, it.get("eyebrow", f"Mistake {k + 1} of {K}"), it.get("mistake", M["mistake"]), "bad")
        head(c, f"hg{k}", f, nxt, it.get("fix_eyebrow", f"Fix {k + 1}"), it.get("fix", M["fix"]), "good")
        if M.get("scroll_bad"): scroll(c, f"s{k}b", a + 0.2, M["scroll_bad"], f - a - 0.25, "power1.inOut")
        if M.get("slow"):
            c.ft(f"#b{k}-ss-fill", o(width="5%"), o(width="38%", duration=f - a, ease="power1.out"), a)
            c.ft(f"#b{k}-ss-spin", o(rotation=0), o(rotation=360 * 2, duration=f - a + 0.2, ease="none"), a)
        if M.get("pinch"):
            c.to(f"#s{k}b-scr", o(scale=2.1, transformOrigin="16% 20%", duration=0.7, ease="power3.inOut"), a + 0.25)
        if M.get("bad_ring"): ring(c, f"b{k}-{M['bad_ring']}", a + 0.35, f - 0.1)
        sy = 0
        if M.get("scroll_good"):
            sy = lambda Mm, el=f"g{k}-{M['target']}": min(0.0, -(Mm[el]["y"] - 300))
            c.need(f"g{k}-{M['target']}")
            c.later(lambda Mm, k=k, sy=sy: c.set(f"#s{k}g-scr", o(y=sy(Mm)), f - 0.15))
        wipe_in(c, f"s{k}g", f - 0.12)
        cam_to(c, f + 0.3, 0.6, f"g{k}-{M['target']}", 1.45, cy=M.get("cy", 960), scroll=sy)
        ring(c, f"g{k}-{M['ring']}", f + 0.55, nxt - 0.2)
        callout(c, f"cw{k}", f + 0.6, nxt - 0.15, it.get("why", M["why"]), "good")
    cta(c, z, s["cta"])

# ================================================================= 4. before / after transformation
BA_TOP = 560

def before_after_segments(s):
    return [("reveal", 3.9), ("changes", 1.6 + 0.6 * len(s["changes"][:3]))]

def before_after(c, s, n, T):
    rv, ch, z = T["reveal"], T["changes"], T["cta"]
    screens = [("b-old", site_old(n, "desktop"), ""), ("b-new", site_desktop(n), "")]
    bh = BROWSER["h"] - BROWSER["bar"]
    device_clip(c, "dev", z + 0.4, browser("br", domain(n), screens, f"top:{BA_TOP}px") + f"""
        <div id="ba-h" style="left:{BROWSER['x'] - 2}px;top:{BA_TOP + BROWSER['bar']}px;height:{bh}px"><i></i><span>{"‹ ›"}</span></div>
        <div class="ba-tag old" id="tag-old" style="right:{1080 - BROWSER['x'] - BROWSER['w'] + 24}px;top:{BA_TOP + BROWSER['h'] - 76}px">BEFORE</div>
        <div class="ba-tag new" id="tag-new" style="left:{BROWSER['x'] + 24}px;top:{BA_TOP + BROWSER['h'] - 76}px">AFTER</div>""")
    device_in(c, "#br", rv)
    hook(c, s["hook"], rv)
    brandbar(c, rv, z)
    c.cue("riser-m", rv, -4.0)

    sw0, sw1 = rv + 1.35, rv + 2.85
    head(c, "hb", rv, sw1 + 0.05, s.get("before_eyebrow", "Before"), s["before_head"], "bad")
    head(c, "ha", sw1 + 0.05, z, s.get("after_eyebrow", "After"), s["after_head"], "good")
    c.ft("#tag-old", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.35, ease="power2.out"), rv + 0.35)
    c.ft("#b-new", o(clipPath="inset(0% 100% 0% 0%)"), o(clipPath="inset(0% 0% 0% 0%)", duration=sw1 - sw0, ease="power3.inOut"), sw0)
    c.ft("#ba-h", o(x=0, opacity=0), o(x=BROWSER["w"], opacity=1, duration=sw1 - sw0, ease="power3.inOut", immediateRender=False), sw0)
    c.to("#ba-h", o(opacity=0, duration=0.25), sw1 + 0.05)
    c.ft("#ba-h", o(opacity=0), o(opacity=1, duration=0.2), sw0 - 0.2)
    c.ft("#tag-new", o(opacity=0, y=10), o(opacity=1, y=0, duration=0.35, ease="power2.out", immediateRender=False), sw0 + 0.45)
    c.to("#tag-old", o(opacity=0, duration=0.2), sw0 + (sw1 - sw0) * 0.72)
    c.cue("riser-m", sw0 + 0.1, -3.0); c.cue("whoosh", sw0 + (sw1 - sw0) * 0.5, -3.0); c.cue("popup", sw1, -5.0)

    mini = phone("mph", [("m-new", site_mobile(n, px="m-"), "")], "left:700px;top:830px")
    c.clip("mini", ch - 0.2, z + 0.4, mini, cls="layer", style="z-index:14")
    c.ft("#mph", o(opacity=0, y=260, scale=0.46, transformOrigin="0% 0%"),
         o(opacity=1, y=0, scale=0.46, duration=0.75, ease="expo.out"), ch - 0.15)
    c.cue("riser-s", ch - 0.05, -4.0); c.cue("whoosh", ch - 0.2, -7.0)
    scroll(c, "m-new", ch + 0.9, -300, 2.2)
    c.to("#br", o(y=-20, duration=0.8, ease="power2.inOut"), ch - 0.2)
    for i, t in enumerate(s["changes"][:3]):
        chip(c, f"cc{i}", ch + 0.45 + 0.6 * i, z - 0.2, t, "good", x=70, y=1250 + 100 * i)
    cta(c, z, s["cta"])

BA_CSS = f"""
#ba-h {{ position:absolute; width:4px; z-index:12; opacity:0; }}
#ba-h i {{ position:absolute; inset:0; background:#fff; box-shadow:0 0 18px rgba(0,0,0,.35); }}
#ba-h span {{ position:absolute; left:50%; top:50%; width:72px; height:72px; margin:-36px 0 0 -36px; border-radius:50%; background:#fff;
              color:#1C1A19; font:800 26px/72px "Montserrat", sans-serif; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,.35); }}
.ba-tag {{ position:absolute; z-index:13; padding:10px 18px; border-radius:12px; font:800 22px/1 "Montserrat", sans-serif; letter-spacing:.18em;
           opacity:0; box-shadow:0 10px 24px rgba(0,0,0,.3); }}
.ba-tag.old {{ background:#1C1A19; color:#FF8A8A; }}
.ba-tag.new {{ background:#1C1A19; color:#7BE7B0; }}
.note {{ position:absolute; left:60px; width:420px; top:1110px; font-size:23px; line-height:1.4; color:#8A8580; opacity:0; }}
.bad .ring {{ border-color:#FF6161; box-shadow:0 0 0 7px rgba(255,97,97,.2), 0 0 34px rgba(255,97,97,.3); }}
"""

TEMPLATES = {
    "redesign":     (redesign_segments, redesign),
    "local-seo":    (local_seo_segments, local_seo),
    "mistakes":     (mistakes_segments, mistakes),
    "before-after": (before_after_segments, before_after),
    "gbp-tips":     (gbp_tips_segments, gbp_tips),
}
