"""JT Builds Co: "the egg" pattern-interrupt reel, v2 (1080x1920, 9 s, sound effects only).

    python3 build.py
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/jtb-egg-reel-v2.mp4 -q delivery

Real footage, hard cuts, one noise hit per cut (the format of the reference reel):
0.00-1.87  the real egg clip (assets/media/egg.mp4): it rolls off the table and breaks on the tile
1.87-2.33  "need a website?"
2.33-2.97  outdated.   a 2011-style version of the site in a browser
2.97-3.60  modern.     the real Gleam Detail Co. site (screenshot)
3.60-4.40  mobile.     the same site laid out for a phone, scrolled to the quote button
4.40-5.30  bookable.   the real quote form filling in (screen recording)
5.30-6.40  findable.   a local search; the listing sits among the results (no ranking claim)
6.40-7.00  clean. / fast.
7.00-9.00  "Your next customer is looking online." / JT Builds Co | DM 'SITE'

assets/media/ is user footage and is not committed (see .gitignore): egg.mp4 / egg-bg.mp4 /
egg-audio.wav come from the egg clip, gleam-site-clean.png and form-clean.mp4 from the Gleam demo.
"""
import importlib.util, json, os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "jtb-shorts", "lib")
sys.path.insert(0, LIB)
from comp import Comp, o, R, esc
from brand import C, icon, BASE_CSS
from mocks import phone, browser, PHONE, MOCK_CSS, site_old
from sites import serp, SITES_CSS
from scenes import typing, type_into, ring, TYPING_CSS
from mix import read, codec_safe, measure
from sfx import key_click
from audio import SR
spec = importlib.util.spec_from_file_location("eggsfx", os.path.join(HERE, "tools", "sfx.py"))
eggsfx = importlib.util.module_from_spec(spec); spec.loader.exec_module(eggsfx)

D, FPS = 9.0, 30
A, CREAM, INK, DARK = C["accent"], "#F2EADC", "#1A1206", "#121110"
NICHES = {k: dict(v, _key=k) for k, v in json.load(open(os.path.join(HERE, "..", "jtb-shorts", "niches.json"))).items() if not k.startswith("_")}
n = dict(NICHES["auto-detailing"], business="Gleam Detail Co.", short="Gleam", cta_label="Request my quote")
QUERY = n["query"]

# every cut sits on a frame boundary
F = lambda f: round(f / FPS, 4)
T = dict(egg=0.0, need=F(56), old=F(70), modern=F(89), mobile=F(108), book=F(132), find=F(159), clean=F(192), fast=F(201), end=F(210))
ORDER = list(T)
END = lambda k: T[ORDER[ORDER.index(k) + 1]] if k != "end" else D

c = Comp(D, FPS)
med = lambda f: f"assets/media/{f}"

# ----------------------------------------------------------------- 0-1.87 s: the egg, as filmed
c.raw(f'<video id="egg-bg" class="clip" src="{med("egg-bg.mp4")}" muted playsinline data-start="0" data-duration="{T["need"]}" '
      f'data-track-index="1" data-layout-ignore></video>')
c.raw(f'<video id="egg-v" class="clip" src="{med("egg.mp4")}" muted playsinline data-start="0" data-duration="{T["need"]}" '
      f'data-track-index="2" data-layout-ignore></video>')
c.clip("egg-cr", 0, T["need"], '<div class="credit">video: @nikso2893</div>', cls="layer", style="z-index:5")

# ----------------------------------------------------------------- text cards (hard cuts)
def card(k, html, bg, fg, size):
    c.clip(f"k-{k}", T[k], END(k), f'<div class="card" style="background:{bg};color:{fg}"><div class="kt" id="kt-{k}" style="font-size:{size}px">{html}</div></div>',
           cls="layer", style="z-index:30")
    c.ft(f"#kt-{k}", o(scale=1.06), o(scale=1, duration=END(k) - T[k], ease="power2.out"), T[k])
card("need", 'need a<br>website<b>?</b>', DARK, CREAM, 196)
card("clean", 'clean<b>.</b>', CREAM, INK, 290)
card("fast", 'fast<b>.</b>', A, INK, 290)

def word(k, txt, top=1372):
    """The big lowercase word under each visual beat."""
    c.clip(f"w-{k}", T[k], END(k), f'<div class="word" style="top:{top}px">{txt}<b>.</b></div>', cls="layer", style="z-index:40")

def push(sel, k, s=1.045, origin="50% 40%"):
    """A slow push-in across the beat so no shot sits dead still."""
    c.ft(sel, o(scale=1, transformOrigin=origin), o(scale=s, duration=END(k) - T[k], ease="none"), T[k])

# ----------------------------------------------------------------- outdated. / modern. (same browser, same spot: a straight before/after)
BTOP = 520
c.clip("b-old", T["old"], END("old"), f'<div class="stage" id="st-old">{browser("br-old", "Not secure  |  gleamdetailco.com/index.htm", [("s-old", site_old(n, "desktop"), "")], f"top:{BTOP}px")}</div>',
       cls="layer", style="z-index:10")
word("old", "outdated", 1300); push("#st-old", "old")
site_img = f'<div class="shot"><img id="gl-img" src="{med("gleam-site-clean.png")}" alt="Gleam Detail Co. website"></div>'
c.clip("b-new", T["modern"], END("modern"), f'<div class="stage" id="st-new">{browser("br-new", "gleamdetail.co", [("s-new", site_img, "")], f"top:{BTOP}px")}</div>',
       cls="layer", style="z-index:10")
word("modern", "modern", 1300)
c.ft("#gl-img", o(scale=1, transformOrigin="22% 38%"), o(scale=1.16, duration=END("modern") - T["modern"], ease="power1.inOut"), T["modern"])

# ----------------------------------------------------------------- mobile. the same site on a phone
FIELDS = [("Full name", "Jane Smith"), ("Email", "jane@example.com"), ("Phone", "(555) 123-4567"), ("Vehicle", "2022 Audi Q5, silver"),
          ("Service", "Select a service…"), ("Preferred date", "mm/dd/yyyy")]
gm = f"""<div class="gm">
  <div class="gm-nav"><span class="gm-logo"><i>G</i>Gleam Detail Co.</span><span class="gm-menu"><i></i><i></i></span></div>
  <div class="gm-eye">AI LEAD RESPONSE</div>
  <h1>Get a detailing quote. We reply in seconds.</h1>
  <p>Tell us about your vehicle. You'll get a personal acknowledgement right away, and a real person follows up with pricing and availability.</p>
  <div class="gm-card">{"".join(f'<label>{esc(a)}</label><div class="gm-in{" sel" if a == "Service" else ""}">{esc(b)}</div>' for a, b in FIELDS)}
    <div class="gm-btn" id="gm-btn">Request my quote</div></div>
</div>"""
PH_TOP = 196
c.clip("p-mob", T["mobile"], END("mobile"), f'<div class="stage pstage" id="st-mob">{phone("ph-mob", [("s-mob", gm, "")], f"top:{PH_TOP}px")}</div>',
       cls="layer", style="z-index:10")
word("mobile", "mobile")
c.to("#s-mob-scr", o(y=-262, duration=0.42, ease="power3.inOut"), T["mobile"] + 0.16)
c.to("#gm-btn", o(scale=0.95, duration=0.08, yoyo=True, repeat=1, ease="power1.inOut"), T["mobile"] + 0.62)

# ----------------------------------------------------------------- bookable. the real form filling in
c.clip("b-book", T["book"], END("book"), f'<div class="stage" id="st-book">{browser("br-book", "gleamdetail.co/quote", [("s-book", "", "")], f"top:{BTOP + 20}px;height:{54 + 601}px")}</div>',
       cls="layer", style="z-index:10")
c.raw(f'<video id="form-v" class="clip" src="{med("form-clean.mp4")}" muted playsinline data-start="{T["book"]}" data-duration="{round(END("book") - T["book"], 4)}" '
      f'data-track-index="20" data-layout-ignore></video>')
word("book", "bookable", 1300)

# ----------------------------------------------------------------- findable. a local search, the listing among the results
c.clip("p-find", T["find"], END("find"), f'<div class="stage pstage" id="st-find">{phone("ph-find", [("s-serp", serp(n, typing(QUERY, 0)[0]), "")], f"top:{PH_TOP}px")}</div>',
       cls="layer", style="z-index:10")
word("find", "findable")
te = type_into(c, QUERY, T["find"] + 0.04, cps=44)
for sel, d in [("#sp-map", 0.0), ("#sp-places", 0.02), ("#s-serp .sp-row", 0.04)]:
    c.ft(sel, o(opacity=0), o(opacity=1, duration=0.08, immediateRender=False), te + d)
c.set("#sp-map, #sp-places, #s-serp .sp-row", o(opacity=0), T["find"])
c.to("#sp-caret", o(opacity=0, duration=0.05), te)
ring(c, "ring-sp-mine", te + 0.22, END("find") + 0.1)

# ----------------------------------------------------------------- 7-9 s: the line, then the brand
c.clip("end", T["end"], D, f"""<div class="end">
  <div class="end-t"><div id="e1">Your next customer</div><div id="e2">is <em>looking online.</em></div></div>
  <div class="lockup" id="lock"><span class="tile"><img src="assets/jt-mark.png" alt="JT Builds Co"></span><b>JT BUILDS CO</b><i class="sep"></i><span class="dm">DM ‘SITE’</span></div></div>""",
       cls="layer", style="z-index:50")
T_E2, T_LOCK = F(219), F(237)
c.set("#e2", o(opacity=0), T["end"]); c.set("#e2", o(opacity=1), T_E2)
c.set("#lock", o(opacity=0), T["end"]); c.set("#lock", o(opacity=1), T_LOCK)
c.ft(".end-t", o(scale=1.05), o(scale=1, duration=0.5, ease="power2.out"), T["end"])
c.ft("#lock", o(scale=1.06), o(scale=1, duration=0.35, ease="power2.out", immediateRender=False), T_LOCK)

# ----------------------------------------------------------------- sound: the filmed egg, then a noise hit on every cut
HITS = [T[k] for k in ORDER[1:]] + [T_E2, T_LOCK]
HITS.sort()

def mixdown(path):
    L = int(round(D * SR)); buf = np.zeros((L, 2))
    egg = read(os.path.join(HERE, "assets", "media", "egg-audio.wav"))[: int(T["need"] * SR)]
    egg *= np.clip((T["need"] * SR - np.arange(len(egg)))[:, None] / (0.01 * SR), 0, 1)   # hard stop at the cut, no click
    buf[: len(egg)] += egg * 10 ** (-3.0 / 20)
    for k, t in enumerate(HITS):
        nxt = HITS[k + 1] if k + 1 < len(HITS) else D
        x = eggsfx.noise_hit(min(0.66, nxt - t - 0.08 if k + 1 < len(HITS) else 0.66), seed=11 + k)
        x /= np.max(np.abs(x))
        g = -9.0 if t in (T_E2,) else -3.0
        i = int(round(t * SR)); j = min(L, i + len(x)); buf[i:j] += x[: j - i] * 10 ** (g / 20)
    for t, gdb in c.keys:
        x = key_click(int(t * 1000)); i = int(t * SR); j = min(L, i + len(x))
        if j > i: buf[i:j] += x[: j - i] * 10 ** ((-16 + gdb) / 20)
    buf *= 10 ** (-2.5 / 20) / (np.max(np.abs(buf)) + 1e-12)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    return measure(path), codec_safe(path)

# ----------------------------------------------------------------- CSS
FONTS = "".join(f'@font-face {{ font-family:"Inter"; font-weight:{w}; font-display:block; src:url("assets/fonts/Inter-{w}-latin.woff2") format("woff2"); }}\n'
                for w in (800, 900))
CSS = "\n".join([BASE_CSS, FONTS, MOCK_CSS, SITES_CSS, TYPING_CSS, f"""
#grid, #glow, #vignette {{ display:none; }}
#root {{ background:{DARK}; }}
.layer {{ position:absolute; inset:0; pointer-events:none; }}
#egg-bg {{ position:absolute; left:0; top:0; width:1080px; height:1920px; object-fit:cover; }}
#egg-v {{ position:absolute; left:0; top:303px; width:1080px; height:1314px; z-index:2; }}
.credit {{ position:absolute; left:0; right:0; top:1648px; text-align:center; font-size:28px; font-weight:600; color:rgba(255,255,255,.82); }}

.card {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }}
.kt {{ font-family:"Inter", sans-serif; font-weight:900; line-height:.92; letter-spacing:-.06em; text-align:center; padding-bottom:.06em; }}
.kt b, .word b {{ color:{A}; font-weight:900; }}
#k-clean .kt b, #k-fast .kt b {{ color:{INK}; }}
#k-need .kt {{ margin-top:-60px; }}
.word {{ position:absolute; left:40px; right:40px; top:1372px; text-align:center; font-family:"Inter", sans-serif; font-weight:900; font-size:196px;
         line-height:1; letter-spacing:-.06em; color:{CREAM}; }}

.stage {{ position:absolute; inset:0; }}
.browser {{ box-shadow:0 0 0 1px rgba(255,255,255,.10), 0 30px 70px rgba(0,0,0,.55); }}
.phone {{ box-shadow:0 0 0 2px #2A2826, 0 0 0 9px #161514, 0 30px 70px rgba(0,0,0,.55); }}
.pstage {{ transform:scale(1.1); transform-origin:540px {PH_TOP}px; }}
#br-old .bbar span {{ color:#C5221F; }}
.shot {{ width:1200px; height:{int(586 / 0.8)}px; overflow:hidden; background:#0A0F1D; }}
#gl-img {{ display:block; width:1200px; height:auto; }}
#form-v {{ position:absolute; left:60px; top:{BTOP + 20 + 54}px; width:960px; height:601px; z-index:12; }}

/* the Gleam site, mobile layout (matches the live desktop design) */
.gm {{ font-family:"Inter", sans-serif; background:linear-gradient(180deg, #0B1220 0%, #0A0F1D 100%); color:#E8EAF0; padding:58px 18px 40px; min-height:1300px; }}
.gm-nav {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:30px; }}
.gm-logo {{ display:flex; align-items:center; gap:10px; font-weight:700; font-size:17px; }}
.gm-logo i {{ width:30px; height:30px; border-radius:8px; background:#E8EAF0; color:#0B1220; font-style:normal; font-weight:800; font-size:16px;
              display:flex; align-items:center; justify-content:center; }}
.gm-menu {{ display:flex; flex-direction:column; gap:6px; }} .gm-menu i {{ width:22px; height:2px; background:#C9CEDA; border-radius:2px; }}
.gm-eye {{ font-size:12px; font-weight:700; letter-spacing:.14em; color:#4FD1C5; margin-bottom:12px; }}
.gm h1 {{ font-size:36px; line-height:1.06; letter-spacing:-.03em; font-weight:700; margin-bottom:14px; }}
.gm p {{ font-size:15px; line-height:1.5; color:#A3ABBB; margin-bottom:22px; }}
.gm-card {{ background:#fff; border-radius:16px; padding:18px 16px 18px; color:#111827; }}
.gm-card label {{ display:block; font-size:13px; font-weight:600; margin:0 0 6px; }}
.gm-in {{ height:42px; border:1px solid #D6D9E2; border-radius:10px; padding:0 12px; display:flex; align-items:center; font-size:14px; color:#7B8190; margin-bottom:12px; }}
.gm-in.sel {{ justify-content:space-between; }}
.gm-btn {{ height:48px; border-radius:10px; background:#0B1220; color:#fff; font-weight:700; font-size:15px; display:flex; align-items:center; justify-content:center; margin-top:6px; }}

.end {{ position:absolute; inset:0; background:{DARK}; }}
.end-t {{ position:absolute; left:50px; right:50px; top:640px; text-align:center; font-family:"Inter", sans-serif; font-weight:900;
          font-size:100px; line-height:1.02; letter-spacing:-.05em; color:{CREAM}; }}
.end-t em {{ font-style:normal; color:{A}; }}
.lockup {{ position:absolute; left:0; right:0; top:1060px; display:flex; align-items:center; justify-content:center; gap:22px;
           font-family:"Montserrat", sans-serif; }}
.lockup .tile {{ width:92px; height:92px; border-radius:22px; background:{C['tile']}; display:flex; align-items:center; justify-content:center;
                 box-shadow:0 0 0 1px rgba(255,255,255,.10); }}
.lockup .tile img {{ width:58px; height:49px; }}
.lockup b {{ font-weight:800; font-size:46px; letter-spacing:.06em; color:{C['white']}; }}
.lockup .sep {{ width:3px; height:56px; background:rgba(255,255,255,.35); }}
.lockup .dm {{ display:inline-block; padding:18px 30px; border-radius:999px; background:{A}; color:{INK}; font-weight:800; font-size:44px; }}
"""])

if __name__ == "__main__":
    h = c.page(CSS, "JT Builds Co · the egg", script=True).replace('<script src="assets/gsap.min.js">', '<script src="assets/vendor/gsap.min.js">')
    open(os.path.join(HERE, "index.html"), "w").write(h)
    (I, tp), dips = mixdown(os.path.join(HERE, "assets", "mix.wav"))
    print(f"index.html: {D}s, cuts {[T[k] for k in ORDER]}, {len(HITS)} noise hits + {len(c.keys)} key clicks; "
          f"effects track {I} LUFS, {tp} dBTP, AAC dips {dips}")
