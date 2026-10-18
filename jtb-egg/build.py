"""JT Builds Co: "the egg" pattern-interrupt reel, v2 (1080x1920, 9 s, sound effects only).

    python3 build.py
    npx --yes hyperframes@0.8.154 check .
    npx --yes hyperframes@0.8.154 render . -o renders/jtb-egg-reel-v2.mp4 -q delivery

Real footage, hard cuts, one noise hit per cut (the format of the reference reel):
0.00-1.87  the real egg clip (assets/media/egg.mp4): it rolls off the table and breaks on the tile
1.87-2.33  "need a website?"
2.33-2.97  outdated.   a generic 2011-style site for a made-up shop, in a browser
2.97-3.60  modern.     cloverdownsdetailing.com, desktop (screenshot)
3.60-4.40  mobile.     the same site on a phone, scrolling (frame-by-frame capture)
4.40-5.30  bookable.   its quote form being filled in (captured; never submitted)
5.30-6.40  findable.   its Beverly / Salem / Danvers town pages, hard cuts
6.40-7.00  clean. / fast.
7.00-9.00  "Your next customer is looking online." / JT Builds Co | DM 'SITE'

assets/media/ is user footage and is not committed (see .gitignore): egg.mp4 / egg-bg.mp4 /
egg-audio.wav come from the egg clip; clover-*.png / clover-*.mp4 are captures of cloverdownsdetailing.com
(tools/capture-site.js).
"""
import importlib.util, json, os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "jtb-shorts", "lib")
sys.path.insert(0, LIB)
from comp import Comp, o, R, esc
from brand import C, icon, BASE_CSS
from mocks import phone, browser, PHONE, MOCK_CSS, site_old
from mix import read, codec_safe, measure
from sfx import key_click
from audio import SR
spec = importlib.util.spec_from_file_location("eggsfx", os.path.join(HERE, "tools", "sfx.py"))
eggsfx = importlib.util.module_from_spec(spec); spec.loader.exec_module(eggsfx)

D, FPS = 9.0, 30
A, CREAM, INK, DARK = C["accent"], "#F2EADC", "#1A1206", "#121110"
NICHES = {k: dict(v, _key=k) for k, v in json.load(open(os.path.join(HERE, "..", "jtb-shorts", "niches.json"))).items() if not k.startswith("_")}
OLD = dict(NICHES["auto-detailing"], business="Main Street Auto Detailing", phone="(978) 555-0110")

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
# The "outdated" site is a generic 2011-style page for a made-up shop, not a past version of Clover Downs.
BTOP = 520
c.clip("b-old", T["old"], END("old"), f'<div class="stage" id="st-old">{browser("br-old", "Not secure  |  mainstreetautodetail.net/index.htm", [("s-old", site_old(OLD, "desktop"), "")], f"top:{BTOP}px")}</div>',
       cls="layer", style="z-index:10")
word("old", "outdated", 1300); push("#st-old", "old")
site_img = f'<div class="shot"><img id="cd-img" src="{med("clover-hero.jpg")}" alt="Clover Downs Detailing website"></div>'
c.clip("b-new", T["modern"], END("modern"), f'<div class="stage" id="st-new">{browser("br-new", "cloverdownsdetailing.com", [("s-new", site_img, "")], f"top:{BTOP}px")}</div>',
       cls="layer", style="z-index:10")
word("modern", "modern", 1300)
c.ft("#cd-img", o(scale=1, transformOrigin="18% 42%"), o(scale=1.14, duration=END("modern") - T["modern"], ease="power1.inOut"), T["modern"])

SBAR = ('<div class="sb"><b>9:41</b><span><i class="sig"><i></i><i></i><i></i><i></i></i><i class="bat"><i></i></i></span></div>')

# ----------------------------------------------------------------- mobile. the real site on a phone, scrolled (frame-by-frame capture)
PH_TOP = 196
c.clip("p-mob", T["mobile"], END("mobile"), f'<div class="stage pstage" id="st-mob">{phone("ph-mob", [("s-mob", "", "")], f"top:{PH_TOP}px")}</div>',
       cls="layer", style="z-index:10")
# the capture plays over the phone's glass (a timed video can't sit inside a timed layer)
c.raw(f'<video id="mob-v" class="clip" src="{med("clover-mobile.mp4")}" muted playsinline data-start="{T["mobile"]}" '
      f'data-duration="{round(END("mobile") - T["mobile"], 4)}" data-track-index="21" data-layout-ignore></video>')
c.clip("mob-notch", T["mobile"], END("mobile"), f'<div class="sbo">{SBAR}</div><i class="notch2"></i>', cls="layer", style="z-index:13")
word("mobile", "mobile")

# ----------------------------------------------------------------- bookable. the real quote form being filled in (frame-by-frame capture, never submitted)
c.clip("b-book", T["book"], END("book"), f'<div class="stage" id="st-book">{browser("br-book", "cloverdownsdetailing.com/#quote", [("s-book", "", "")], f"top:{BTOP}px")}</div>',
       cls="layer", style="z-index:10")
c.raw(f'<video id="form-v" class="clip" src="{med("clover-form.mp4")}" muted playsinline data-start="{T["book"]}" data-duration="{round(END("book") - T["book"], 4)}" '
      f'data-track-index="20" data-layout-ignore></video>')
word("book", "bookable", 1300)
for k in range(3, 23):      # the typing, timed to the capture (frames 2-22 of 27)
    if k % 2: c.key(T["book"] + k / FPS, -2.0)

# ----------------------------------------------------------------- findable. the real town pages, one per area served
TOWNS = ["beverly", "salem", "danvers"]
c.clip("p-find", T["find"], END("find"), f'<div class="stage pstage" id="st-find">' + phone("ph-find", [
    (f"s-{t}", SBAR + f'<img class="pg" src="{med(f"clover-{t}.png")}" alt="Clover Downs Detailing, {t.title()} page">', "") for t in TOWNS], f"top:{PH_TOP}px") + "</div>",
       cls="layer", style="z-index:10")
word("find", "findable")
TOWN_T = [T["find"], F(171), F(183)]
for i, t in enumerate(TOWNS):
    if i: c.set(f"#s-{t}", o(opacity=0), T["find"]); c.set(f"#s-{t}", o(opacity=1), TOWN_T[i])
push("#st-find", "find", 1.03, "540px 700px")

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
HITS = [T[k] for k in ORDER[1:]] + TOWN_T[1:] + [T_E2, T_LOCK]
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
        g = -9.0 if t in [T_E2] + TOWN_T[1:] else -3.0
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
CSS = "\n".join([BASE_CSS, FONTS, MOCK_CSS, f"""
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
.shot {{ width:1200px; height:{int(586 / 0.8)}px; overflow:hidden; background:#0C0C0C; }}
#cd-img {{ display:block; width:1200px; height:auto; }}
#form-v {{ position:absolute; left:60px; top:{BTOP + 54}px; width:960px; height:586px; z-index:12; }}

.pg {{ display:block; width:390px; height:802px; }}
#ph-mob .pglass, #s-mob, #ph-find .pglass, #ph-find .pscreen {{ background:#0C0C0C; }}
.sb {{ height:42px; background:#0C0C0C; display:flex; align-items:center; justify-content:space-between; padding:6px 30px 0 34px; color:#fff; font-family:"Inter", sans-serif; }}
.sb b {{ font-size:15px; font-weight:600; }} .sb span {{ display:flex; align-items:center; gap:6px; }}
.sig {{ display:flex; align-items:flex-end; gap:2px; height:11px; }} .sig i {{ width:3px; background:#fff; border-radius:1px; }}
.sig i:nth-child(1) {{ height:4px; }} .sig i:nth-child(2) {{ height:6px; }} .sig i:nth-child(3) {{ height:8px; }} .sig i:nth-child(4) {{ height:11px; }}
.bat {{ width:24px; height:12px; border:1.5px solid rgba(255,255,255,.55); border-radius:4px; padding:1.5px; display:block; }} .bat i {{ display:block; width:75%; height:100%; background:#fff; border-radius:1.5px; }}
.sbo {{ position:absolute; left:269.4px; top:211.4px; width:390px; transform:scale(1.38769); transform-origin:0 0; border-radius:48px 48px 0 0; overflow:hidden; }}
#mob-v {{ position:absolute; left:269.4px; top:269.7px; width:541.2px; height:1054.9px; border-radius:0 0 66px 66px; z-index:12; object-fit:cover; object-position:50% 0; }}
.notch2 {{ position:absolute; left:468.5px; top:229.0px; width:143.0px; height:39.6px; border-radius:22px; background:#0B0B0C; }}
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
