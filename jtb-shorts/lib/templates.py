"""The four video templates. Each one has:

    SEGMENTS(spec) -> [(name, seconds), ...]   body scenes after the hook (CTA not included)
    build(c, spec, niche, T)                     T = {name: start time}, plus T["cta"]

Times are snapped to the music's beat grid before build() sees them, so every
scene change lands on a beat. Copy comes from the spec; anything left out falls
back to the defaults below, which are written to be accurate (no ranking or
results promises).
"""
from comp import o, R
from scenes import (hook, head, chip, ring, wipe_in, scroll, brandbar, cta, type_into, typing)
from mocks import (phone, browser, site_mobile, site_desktop, site_old, screen_slow, screen_wall, serp, gbp, dashboard,
                   domain, PHONE, BROWSER)

HOOK = 2.3          # hook length before snapping
CTA_LEN = 3.4

# ----------------------------------------------------------------- device motion
SIDE_LEFT = 470     # phone beside a chip column (phone scaled SIDE_SCALE)
SIDE_SCALE = 0.86
CHIP_X = 60
CHIP_Y = (640, 795, 950)

def device_in(c, sel, t_land, scale=1.0, push_until=None):
    """Rises under the hook from frame 0, then lands as the first body scene starts, then a slow push-in."""
    c.ft(sel, o(y=1180, rotationX=26, transformPerspective=1800, scale=scale, opacity=1),
         o(y=780, rotationX=22, duration=t_land - 0.32, ease="power2.out"), 0.0)
    c.to(sel, o(y=0, rotationX=0, duration=0.95, ease="expo.out"), t_land - 0.3)
    if push_until:
        c.to(sel, o(scale=scale * 1.025, duration=push_until - t_land - 0.65, ease="none"), t_land + 0.65)

def device_clip(c, cid, t1, inner):
    c.clip(cid, 0, t1, inner, cls="layer", style="z-index:10")

def lead_in_riser(c, t):
    c.cue("riser-m", t, -4.0)

# ================================================================= 1. website redesign
def redesign_segments(s):
    seg = [("before", 3.9), ("after", 4.8)]
    if s.get("dashboard"): seg.append(("dash", 3.4))
    return seg

def redesign(c, s, n, T):
    b, a, d, z = T["before"], T["after"], T.get("dash"), T["cta"]
    phone_out = d or z
    screens = [("s-old", site_old(n, "mobile"), ""), ("s-new", site_mobile(n, px="n-"), "wipe")]
    device_clip(c, "dev", phone_out + 0.6, phone("ph", screens, f"left:{SIDE_LEFT}px"))
    device_in(c, "#ph", b, SIDE_SCALE, phone_out)
    hook(c, s["hook"], b)
    brandbar(c, b, z)
    lead_in_riser(c, b)

    B = s["before"]
    head(c, "hb", b, a, B.get("eyebrow", "Before"), B["head"], "bad")
    c.to("#s-old-scr", o(scale=2.1, transformOrigin="16% 20%", duration=1.0, ease="power3.inOut"), b + 0.8)
    c.to("#s-old-scr", o(scale=1, duration=0.8, ease="power3.inOut"), b + 2.6)
    for i, p in enumerate(B["problems"][:3]):
        chip(c, f"cb{i}", b + 0.85 + 0.55 * i, a - 0.2, p, "bad", x=CHIP_X, y=CHIP_Y[i])

    A = s["after"]
    head(c, "ha", a, d or z, A.get("eyebrow", "After"), A["head"], "good")
    wipe_in(c, "s-new", a - 0.15)
    rings = ["n-ring-h1", "n-ring-btns", "n-ring-rev"]
    slots = [a + 0.75, a + 1.35, a + 3.2]
    for i, f in enumerate(A["fixes"][:3]):
        text, rid = (f["text"], "n-ring-" + f["ring"]) if isinstance(f, dict) else (f, rings[i])
        t_end = (d or z) - 0.2
        chip(c, f"ca{i}", slots[i], t_end, text, "good", x=CHIP_X, y=CHIP_Y[i])
        ring(c, rid, slots[i] + 0.05, slots[i + 1] - 0.1 if i < 2 else t_end)
    scroll(c, "s-new", a + 2.0, -370, 1.3)

    if d:
        D_ = s["dashboard"]
        c.to("#ph", o(x=420, opacity=0, scale=0.7, duration=0.55, ease="power3.in"), d - 0.45)
        head(c, "hd", d, z, D_.get("eyebrow", "After launch"), D_["head"], "")
        c.clip("dash", d - 0.4, z + 0.3, browser("br", "dashboard." + domain(n), [("b-dash", dashboard(n), "")]), cls="layer", style="z-index:12")
        c.ft("#br", o(opacity=0, y=200, rotationX=18, transformPerspective=1800), o(opacity=1, y=0, rotationX=0, duration=0.9, ease="expo.out"), d - 0.2)
        c.cue("riser-s", d - 0.05, -4.0); c.cue("whoosh", d - 0.25, -6.0)
        for i, v in enumerate(D_.get("values", [48, 31, 22])):
            t = d + 0.45 + 0.18 * i
            c.line(f'(() => {{ const el = document.getElementById("db-v{i}"); const p = {{ v: 0 }}; '
                   f'tl.to(p, {{ v: {int(v)}, duration: 1.2, ease: "power2.out", onUpdate: () => {{ el.textContent = Math.round(p.v); }} }}, {t:.3f}); }})();')
            c.cue("bubble", t, -8.0)
        c.clip("dash-note", d + 0.3, z, '<div class="note" id="dash-note" style="left:70px;width:auto;right:70px;top:1310px;text-align:center">Example dashboard. Illustrative numbers, not real client results.</div>', cls="layer", style="z-index:35")
        c.ft("#dash-note", o(opacity=0), o(opacity=1, duration=0.4), d + 0.6)
        c.ft("#db-line", o(strokeDashoffset=1), o(strokeDashoffset=0, duration=1.5, ease="power2.inOut"), d + 0.5)
        c.to("#br", o(scale=1.02, duration=z - d, ease="none"), d + 0.7)
    cta(c, z, s["cta"])

# ================================================================= 2. local SEO tips
FACTORS = [("Relevance", "Do you match the search?", "search"), ("Distance", "How close you are", "pin"),
           ("Prominence", "Reviews, links, reputation", "star")]

def local_seo_segments(s):
    tips = len(s["profile"]["tips"][:3])
    return [("search", 5.7), ("profile", 1.4 + 1.1 * tips)]

def local_seo(c, s, n, T):
    q, p, z = T["search"], T["profile"], T["cta"]
    query = s.get("query", n["query"])
    spans, _, _ = typing(query, 0)
    sp = serp(n).replace('<span id="sp-q"></span>', f'<span id="sp-q">{spans}</span>')
    screens = [("s-serp", sp, ""), ("s-gbp", gbp(n), "wipe")]
    device_clip(c, "dev", z + 0.4, phone("ph", screens, f"left:{SIDE_LEFT}px"))
    device_in(c, "#ph", q, SIDE_SCALE, z)
    hook(c, s["hook"], q)
    brandbar(c, q, z)
    lead_in_riser(c, q)

    S = s["search"]
    head(c, "hs", q, p, S.get("eyebrow", "Local SEO"), S["head"])
    c.ft("#sp-caret", o(opacity=1), o(opacity=0, duration=0.22, ease="steps(1)", repeat=3, yoyo=True), q - 0.4)
    te = type_into(c, query, q + 0.45)
    c.ft("#sp-map", o(opacity=0, y=14), o(opacity=1, y=0, duration=0.45, ease="power2.out"), te + 0.12)
    c.ft("#s-serp .pinw", o(opacity=0, y=-26), o(opacity=1, y=0, duration=0.45, ease="back.out(2)", stagger=0.12), te + 0.3)
    for i in range(3): c.cue("bubble", te + 0.3 + 0.12 * i, -4.0)
    c.ft("#s-serp .sp-row", o(opacity=0, y=16), o(opacity=1, y=0, duration=0.4, ease="power2.out", stagger=0.1), te + 0.22)
    c.ft("#s-serp .sp-org", o(opacity=0), o(opacity=1, duration=0.4), te + 0.5)
    c.ft("#sp-caret", o(opacity=1), o(opacity=0, duration=0.15), te + 0.1)
    ring(c, "ring-sp-mine", te + 0.75, p - 0.2)
    factors = S.get("factors", FACTORS)
    for i, (t, sub, ic) in enumerate(factors[:3]):
        chip(c, f"cf{i}", te + 0.95 + 0.42 * i, p - 0.2, t, "acc", x=CHIP_X, y=CHIP_Y[i], sub=sub, ic=ic)
    if S.get("note"):
        c.clip("note", te + 1.9, p + 0.2, f'<div class="note" id="note">{S["note"]}</div>', cls="layer", style="z-index:35")
        c.ft("#note", o(opacity=0), o(opacity=1, duration=0.4), te + 2.0)
        c.to("#note", o(opacity=0, duration=0.2), p - 0.2)

    P = s["profile"]
    head(c, "hp", p, z, P.get("eyebrow", "What you control"), P["head"], "good")
    wipe_in(c, "s-gbp", p - 0.15)
    tips = P["tips"][:3]
    for i, tip in enumerate(tips):
        t0 = p + 0.8 + 1.1 * i
        chip(c, f"ct{i}", t0, z - 0.2, tip["text"], "good", x=CHIP_X, y=CHIP_Y[i], sub=tip.get("sub"))
        ring(c, "ring-gb-" + tip["section"], t0 + 0.05, (p + 0.8 + 1.1 * (i + 1) - 0.1) if i < len(tips) - 1 else z - 0.2)
        if tip["section"] in ("reviews", "posts"): scroll(c, "s-gbp", t0 - 0.35, -70, 0.7)
    cta(c, z, s["cta"])

# ================================================================= 3. website mistakes (conversions)
def _sm(**kw): return lambda n, px: site_mobile(n, px=px, **kw)
MISTAKES = {
    "hidden-phone":    dict(bad=_sm(buttons=False, callbar=False), good=_sm(), ring="ring-bar", scroll_bad=-420,
                            mistake="Your phone number is *buried*.", fix="Tap-to-call on *every* screen."),
    "no-cta":          dict(bad=_sm(buttons=False, callbar=False), good=_sm(), ring="ring-btns", scroll_bad=-160,
                            mistake="No clear *next step*.", fix="One obvious button: *Get a quote*."),
    "slow":            dict(bad=lambda n, px: screen_slow(px), good=_sm(), ring="ring-h1", slow=True,
                            mistake="It takes *forever* to load.", fix="Compress images. *Cut the bloat.*"),
    "not-mobile":      dict(bad=lambda n, px: site_old(n, "mobile"), good=_sm(), ring="ring-h1", pinch=True,
                            mistake="Not built for *phones*.", fix="Design for the *thumb* first."),
    "no-reviews":      dict(bad=_sm(reviews=False), good=_sm(), ring="ring-rev", scroll_bad=-360, scroll_good=-360,
                            mistake="No *proof* you're any good.", fix="Put real *reviews* up front."),
    "generic-heading": dict(bad=_sm(hero_title="Welcome to our website!"), good=_sm(), ring="ring-h1", bad_ring="ring-h1",
                            mistake="“Welcome to our *website*.”", fix="Say *what* you do and *where*."),
    "wall-of-text":    dict(bad=lambda n, px: screen_wall(n), good=_sm(), ring="ring-h1", scroll_bad=-240,
                            mistake="A wall of *text*.", fix="Short lines. *Clear sections.*"),
}

def mistakes_segments(s):
    return [(f"m{k}", 3.95) for k in range(len(s["items"][:3]))]

def mistakes(c, s, n, T):
    items = s["items"][:3]; z = T["cta"]; K = len(items)
    screens = []
    for k, it in enumerate(items):
        M = MISTAKES[it["type"]]
        screens.append((f"s{k}b", M["bad"](n, f"b{k}-"), "bad" + (" wipe" if k else "")))
        screens.append((f"s{k}g", M["good"](n, f"g{k}-"), "wipe"))
    device_clip(c, "dev", z + 0.4, phone("ph", screens))
    first = T["m0"]
    device_in(c, "#ph", first, 1.0, z)
    hook(c, s["hook"], first)
    brandbar(c, first, z)
    lead_in_riser(c, first)
    for k, it in enumerate(items):
        M = MISTAKES[it["type"]]
        a = T[f"m{k}"]; nxt = T[f"m{k + 1}"] if k + 1 < K else z
        f = a + (nxt - a) * 0.46
        if k: wipe_in(c, f"s{k}b", a - 0.15)
        head(c, f"hb{k}", a, f, it.get("eyebrow", f"Mistake {k + 1} of {K}"), it.get("mistake", M["mistake"]), "bad")
        head(c, f"hg{k}", f, nxt, "The fix", it.get("fix", M["fix"]), "good")
        if M.get("scroll_bad"): scroll(c, f"s{k}b", a + 0.3, M["scroll_bad"], f - a - 0.4, "power1.inOut")
        if M.get("slow"):
            c.ft(f"#b{k}-ss-fill", o(width="5%"), o(width="36%", duration=f - a, ease="power1.out"), a)
            c.ft(f"#b{k}-ss-spin", o(rotation=0), o(rotation=360 * 3, duration=f - a + 0.3, ease="none"), a)
        if M.get("pinch"):
            c.to(f"#s{k}b-scr", o(scale=2.1, transformOrigin="16% 20%", duration=0.9, ease="power3.inOut"), a + 0.4)
        if M.get("bad_ring"): ring(c, f"b{k}-{M['bad_ring']}", a + 0.5, f - 0.1)
        if M.get("scroll_good"): c.set(f"#s{k}g-scr", o(y=M["scroll_good"]), a)
        wipe_in(c, f"s{k}g", f - 0.12)
        c.cue("popup", f + 0.5, -6.0)
        ring(c, f"g{k}-{M['ring']}", f + 0.5, nxt - 0.25)
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
    device_in(c, "#br", rv, 1.0, z)
    hook(c, s["hook"], rv)
    brandbar(c, rv, z)
    lead_in_riser(c, rv)

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
.note {{ position:absolute; left:{CHIP_X}px; width:420px; top:1110px; font-size:23px; line-height:1.4; color:#8A8580; opacity:0; }}
.bad .ring {{ border-color:#FF6161; box-shadow:0 0 0 7px rgba(255,97,97,.2), 0 0 34px rgba(255,97,97,.3); }}
"""

TEMPLATES = {
    "redesign":     (redesign_segments, redesign),
    "local-seo":    (local_seo_segments, local_seo),
    "mistakes":     (mistakes_segments, mistakes),
    "before-after": (before_after_segments, before_after),
}
