"""Build the ScoutCard reveal reel (reveal.html + four scene sub-compositions).

    python3 tools/reveal/build_reveal.py
    npx hyperframes check                      (index.html, the founder reel)
    npx hyperframes render -c reveal.html ...  (this reel; see BRIEF-reveal.md)

Everything a person would want to adjust lives in CONFIG below: scene timing,
on-screen copy, colours, transition timing and every audio level. Edit, re-run,
re-render. The generated HTML is plain HyperFrames and can also be edited by
hand, but edits there are overwritten by the next build.
"""
import json, html, os

# ============================================================================ CONFIG
CONFIG = {
    "duration": 20.0,
    "colors": {
        "bg": "#060708", "charcoal": "#111317", "panel_edge": "rgba(255,255,255,.08)",
        "white": "#F4F5F7", "muted": "#9AA3AE",
        "blue": "#1E57E6",        # the line of scrimmage in the ScoutCard prototype
        "blue_text": "#5B8CFF",   # same hue, lifted so a blue glyph reads on black
    },
    # ---------------------------------------------------------------- scenes
    "s1": {"start": 0.0, "end": 3.0,
           "line1": ["WHAT IF FILM", "COULD…"], "line1_in": 0.30, "line1_out": 1.40,
           "line2": ["BUILD YOUR", "SCOUT CARDS?"], "line2_in": 1.52, "glitch": [2.84, 2.91]},
    "s2": {"start": 3.0, "end": 6.0, "headline": "MEET SCOUT CARD.", "headline_in": 3.28, "headline_out": 5.70},
    "s3": {"start": 6.0, "end": 14.0,
           "shots": {"film": [6.0, 8.45], "card": [8.45, 10.05], "list": [10.05, 12.55], "flip": [12.55, 14.0]},
           "labels": [("FOOTBALL FILM", 7.28, 8.40), ("SCOUTING CARDS", 8.52, 10.00), ("BUILT FOR COACHES", 10.12, 12.45)]},
    "s4": {"start": 14.0, "end": 20.0, "brand_in": 17.0,
           "wordmark": "SCOUT CARD", "status": "IN DEVELOPMENT"},
    "prototype_tag": "PROTOTYPE · DEMO DATA",
    # Panels (px, 1080x1920 frame). Film and card share a centre line so every
    # handoff is a match on position.
    "film_panel": {"w": 1080, "cy": 960},
    "card_panel": {"w": 1000, "cy": 960},
    "list_panel": {"w": 600, "cy": 985},
    "label_cy": 400, "subtitle_cy": 1468,
    "subtitles": True,
    # ---------------------------------------------------------------- audio (0..1 volumes)
    "vo": {"vo1": 3.40, "vo2": 6.10, "vo3": 14.35, "volume": 1.0},
    "music": {"start": 3.0, "volume": 0.50, "duck_to": 0.36, "duck_down": 0.15, "duck_up": 0.35, "breath": 0.62},
    "sfx": [  # (id, file, start, duration, volume, media_start)
        ("sx-rumble", "assets/reveal/sfx/rumble.wav",        0.00, 3.30, 0.85, 0),
        ("sx-riser",  "assets/reveal/sfx/riser.mp3",         0.30, 2.70, 0.22, 0),
        ("sx-thump1", "assets/reveal/sfx/thump-1.wav",       0.30, 0.90, 0.40, 0),
        ("sx-thump2", "assets/reveal/sfx/thump-2.wav",       1.52, 0.90, 0.55, 0),
        ("sx-impact", "assets/reveal/sfx/impact-bass-1.mp3", 3.00, 2.10, 0.60, 0),
        ("sx-swish1", "assets/reveal/sfx/whoosh-short.mp3",  8.36, 0.57, 0.22, 0),
        ("sx-swish2", "assets/reveal/sfx/whoosh-short.mp3",  9.97, 0.57, 0.18, 0),
        ("sx-swish3", "assets/reveal/sfx/whoosh-short.mp3", 12.47, 0.57, 0.15, 0),
    ],
}
# ==================================================================================

C = CONFIG; COL = C["colors"]; D = C["duration"]
VO = json.load(open("tools/reveal/vo_words.json"))
VO_TRIM = {"vo1": 0.00, "vo2": 0.00, "vo3": 0.08}            # must match prep_media.py TRIM starts
MEDIA_LEN = {"ui_card01": 1.7, "ui_list": 2.6, "ui_flip": 1.6, "film": 5.933}
VO_LEN = {}
for k in VO:
    import wave
    w = wave.open(f"assets/reveal/media/{k}.wav"); VO_LEN[k] = w.getnframes() / w.getframerate(); w.close()
def vo_word(k, i):                                          # composition time of word i of take k
    return round(C["vo"][k] + VO[k][i]["start"] - VO_TRIM[k], 3)

FONTS = """
      @font-face { font-family:"Barlow Condensed"; font-weight:700; font-display:block; src:url("assets/reveal/fonts/BarlowCondensed-700-latin.woff2") format("woff2"); }
      @font-face { font-family:"Barlow Condensed"; font-weight:800; font-display:block; src:url("assets/reveal/fonts/BarlowCondensed-800-latin.woff2") format("woff2"); }
      @font-face { font-family:"Inter"; font-weight:400; font-display:block; src:url("assets/reveal/fonts/Inter-400-latin.woff2") format("woff2"); }
      @font-face { font-family:"Inter"; font-weight:600; font-display:block; src:url("assets/reveal/fonts/Inter-600-latin.woff2") format("woff2"); }
      @font-face { font-family:"Inter"; font-weight:700; font-display:block; src:url("assets/reveal/fonts/Inter-700-latin.woff2") format("woff2"); }"""

def scene_file(cid, dur, css, body, js):
    """A templated sub-composition: styles, markup and script all inside <template>."""
    return f"""<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /><title>{cid}</title></head>
  <body>
    <template>
      <style>{FONTS}
      #root {{ position:absolute; inset:0; overflow:hidden; color:{COL['white']}; font-family:"Inter", sans-serif; }}
{css}
      </style>
      <div id="root" data-composition-id="{cid}" data-width="1080" data-height="1920" data-duration="{dur}">
{body}
      </div>
      <script>
        window.__timelines = window.__timelines || {{}};
        (function () {{
          const tl = gsap.timeline({{ paused: true }});
{js}
          window.__timelines["{cid}"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""
def r(x): return round(x, 3)

# ------------------------------------------------------------------ scene 1: hook
s1 = C["s1"]; S1 = s1["end"] - s1["start"]
def words(lines, cls):
    out = []
    for li, line in enumerate(lines):
        ws = " ".join(f'<span class="m"><span class="{cls}">{html.escape(w)}</span></span>' for w in line.split(" "))
        out.append(f'<div class="ln">{ws}</div>')
    return "\n".join(out)
l2 = [s1["line2"][0], s1["line2"][1].replace("?", "")]
s1_css = f"""
      #root {{ background:{COL['bg']}; }}
      .stack {{ position:absolute; left:80px; right:80px; top:0; bottom:0; display:flex; flex-direction:column; justify-content:center; text-align:center;
               font-family:"Barlow Condensed", sans-serif; font-weight:800; text-transform:uppercase; }}
      #s1-a {{ font-size:150px; line-height:.92; letter-spacing:.005em; }}
      #s1-b {{ font-size:168px; line-height:.9; letter-spacing:.005em; opacity:0; }}
      .ln {{ display:block; white-space:nowrap; }}
      .m {{ display:inline-block; overflow:hidden; vertical-align:top; padding:0 .04em .06em; margin:0 -.02em; }}
      .w, .w2 {{ display:inline-block; }}
      .q {{ color:{COL['blue_text']}; }}
      #s1-dots span {{ opacity:0; }}"""
line1_html = words([s1["line1"][0]], "w") + f'\n<div class="ln"><span class="m"><span class="w">COULD</span></span><span id="s1-dots"><span>.</span><span>.</span><span>.</span></span></div>'
line2_html = words(l2, "w2").replace("CARDS</span></span></div>", 'CARDS</span></span><span class="m"><span class="w2 q">?</span></span></div>')
s1_body = f"""        <div id="s1-a" class="stack">{line1_html}</div>
        <div id="s1-b" class="stack">{line2_html}</div>"""
a_in, a_out, b_in = s1["line1_in"], s1["line1_out"], s1["line2_in"]
g1, g2 = s1["glitch"]
s1_js = f"""
          // beat 1: words rise out of their masks, then the ellipsis types itself
          tl.fromTo("#s1-a .w", {{ yPercent:105 }}, {{ yPercent:0, duration:0.55, ease:"power4.out", stagger:0.08 }}, {a_in});
          tl.to("#s1-dots span", {{ opacity:1, duration:0.01, stagger:0.14 }}, {r(a_in+0.48)});
          tl.to("#s1-a", {{ y:-36, opacity:0, filter:"blur(10px)", duration:0.16, ease:"power2.in" }}, {r(a_out-0.16)});
          // beat 2: lands harder - out of focus and oversized, snapping into place
          tl.fromTo("#s1-b", {{ opacity:0, scale:1.32, filter:"blur(16px)" }},
                             {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.42, ease:"expo.out" }}, {b_in});
          tl.fromTo("#s1-b .w2", {{ yPercent:60 }}, {{ yPercent:0, duration:0.38, ease:"expo.out", stagger:0.04 }}, {b_in});
          // tension: a slow push that rides the riser
          tl.to("#s1-b", {{ scale:1.07, duration:{r(S1-b_in-0.42-0.09)}, ease:"power1.in" }}, {r(b_in+0.42)});
          // two restrained glitch frames just before the hit
          [{g1}, {g2}].forEach((t, i) => {{
            tl.set("#s1-b", {{ x: i ? -7 : 9, textShadow: i ? "6px 0 0 rgba(91,140,255,.55)" : "-8px 0 0 rgba(91,140,255,.55)" }}, t);
            tl.set("#s1-b", {{ x:0, textShadow:"none" }}, t + 1/30);
          }});
          tl.to("#s1-b", {{ scale:1.16, opacity:0, duration:0.08, ease:"power2.in" }}, {r(S1-0.08)});
"""
open("compositions/reveal/s1-hook.html", "w").write(scene_file("reveal-s1", S1, s1_css, s1_body, s1_js))

# ---------------------------------------------- shared panel geometry for s2-s4
FP, CP, LP = C["film_panel"], C["card_panel"], C["list_panel"]
film_h = round(FP["w"] * 744 / 1470); card_h = round(CP["w"] * 944 / 1194); list_h = round(LP["w"] * 850 / 690)
def box(w, h, cy): return f"left:{(1080-w)//2}px; top:{cy - h//2}px; width:{w}px; height:{h}px;"
PANEL_CSS = f"""
      .panel {{ position:absolute; overflow:hidden; border-radius:18px; background:#000;
                box-shadow:0 0 0 1px {COL['panel_edge']}, 0 40px 90px rgba(0,0,0,.55); }}
      .panel video, .panel img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
      .film {{ {box(FP['w'], film_h, FP['cy'])} border-radius:0; box-shadow:none; }}
      .film::after {{ content:""; position:absolute; inset:0; pointer-events:none;
                      background:linear-gradient(180deg, rgba(6,7,8,.55), rgba(6,7,8,0) 18%, rgba(6,7,8,0) 82%, rgba(6,7,8,.55)); }}
      .card {{ {box(CP['w'], card_h, CP['cy'])} }}
      .list {{ {box(LP['w'], list_h, LP['cy'])} }}
      .label {{ position:absolute; left:80px; right:80px; top:{C['label_cy'] - 66}px; text-align:center;
                font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:104px; line-height:1; letter-spacing:.01em; }}
      .label .rule {{ display:block; width:56px; height:4px; margin:22px auto 0; background:{COL['blue']}; transform-origin:50% 50%; }}
      .tag {{ position:absolute; font-family:"Inter", sans-serif; font-weight:600; font-size:22px; letter-spacing:.16em;
              color:{COL['muted']}; padding:9px 14px 8px; border:1px solid rgba(154,163,174,.35); border-radius:8px;
              background:rgba(6,7,8,.6); }}
      .tag i {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:{COL['blue']}; margin-right:10px; vertical-align:1px; }}"""
def tag_pos(w, h, cy): return f"left:{(1080-w)//2}px; top:{cy - h//2 - 62}px;"
TAG = lambda pid, w, h, cy: f'<div id="{pid}" class="tag" style="{tag_pos(w, h, cy)}"><i></i>{html.escape(C["prototype_tag"])}</div>'

# ------------------------------------------------------- scene 2: the reveal
s2 = C["s2"]; S2 = s2["end"] - s2["start"]
FILM_PUSH = (1.0, 1.035, 1.075)    # scale at s2 start, s2 end/s3 start, film end - continuous across the cut
s2_css = f"""
      #root {{ background:{COL['bg']}; }}{PANEL_CSS}
      #s2-head {{ font-size:118px; }}"""
s2_body = f"""        <div id="s2-film" class="panel film"><video id="s2-film-v" src="assets/reveal/media/film.mp4" muted playsinline data-layout-allow-overflow
             data-start="0" data-duration="{S2}" data-media-start="0"></video></div>
        <div id="s2-head" class="label">{html.escape(s2['headline'])}<span class="rule"></span></div>"""
hin, hout = r(s2["headline_in"] - s2["start"]), r(s2["headline_out"] - s2["start"])
s2_js = f"""
          // the impact: the film opens out of a single line of light
          tl.fromTo("#s2-film", {{ clipPath:"inset(49.6% 0% 49.6% 0%)", filter:"brightness(2.2)" }},
                                {{ clipPath:"inset(0% 0% 0% 0%)", filter:"brightness(1)", duration:0.5, ease:"power4.out" }}, 0);
          tl.fromTo("#s2-film-v", {{ scale:{FILM_PUSH[0]} }}, {{ scale:{FILM_PUSH[1]}, duration:{S2}, ease:"none" }}, 0);
          tl.fromTo("#s2-head", {{ opacity:0, y:34, filter:"blur(10px)" }}, {{ opacity:1, y:0, filter:"blur(0px)", duration:0.5, ease:"power3.out" }}, {hin});
          tl.fromTo("#s2-head .rule", {{ scaleX:0 }}, {{ scaleX:1, duration:0.45, ease:"power3.inOut" }}, {r(hin+0.2)});
          tl.to("#s2-head", {{ opacity:0, y:-26, filter:"blur(8px)", duration:0.24, ease:"power2.in" }}, {hout});"""
open("compositions/reveal/s2-meet.html", "w").write(scene_file("reveal-s2", S2, s2_css, s2_body, s2_js))

# ------------------------------------------------- scene 3: the product
s3 = C["s3"]; S3 = s3["end"] - s3["start"]; o = s3["start"]
sh = {k: (r(a - o), r(b - o)) for k, (a, b) in s3["shots"].items()}
s3_css = f"""
      #root {{ background:{COL['bg']}; }}{PANEL_CSS}
      #s3-card, #s3-list, #s3-flip, #s3-tag-c, #s3-tag-l, #s3-tag-f, .label {{ opacity:0; }}"""
lab_html = "\n".join(f'        <div id="s3-l{i}" class="label">{html.escape(t)}<span class="rule"></span></div>' for i, (t, _, _) in enumerate(s3["labels"]))
fa, fb = sh["film"]; ca, cb = sh["card"]; la, lb = sh["list"]; xa, xb = sh["flip"]
s3_body = f"""        <div id="s3-film" class="panel film"><video id="s3-film-v" src="assets/reveal/media/film.mp4" muted playsinline data-layout-allow-overflow
             data-start="{fa}" data-duration="{r(fb-fa+0.3)}" data-media-start="{S2}"></video></div>
        <div id="s3-card" class="panel card"><video id="s3-card-v" src="assets/reveal/media/ui_card01.mp4" muted playsinline data-layout-allow-overflow
             data-start="{r(ca-0.1)}" data-duration="{r(min(cb-ca+0.1, MEDIA_LEN['ui_card01']))}" data-media-start="0"></video></div>
        <div id="s3-list" class="panel list"><video id="s3-list-v" src="assets/reveal/media/ui_list.mp4" muted playsinline data-layout-allow-overflow
             data-start="{r(la-0.1)}" data-duration="{r(min(lb-la+0.1, MEDIA_LEN['ui_list']))}" data-media-start="0"></video></div>
        <div id="s3-flip" class="panel card"><video id="s3-flip-v" src="assets/reveal/media/ui_flip.mp4" muted playsinline data-layout-allow-overflow
             data-start="{r(xa-0.1)}" data-duration="{r(min(xb-xa+0.1, MEDIA_LEN['ui_flip']))}" data-media-start="0"></video></div>
        {TAG("s3-tag-c", CP['w'], card_h, CP['cy'])}
        {TAG("s3-tag-l", LP['w'], list_h, LP['cy'])}
        {TAG("s3-tag-f", CP['w'], card_h, CP['cy'])}
{lab_html}"""
lab_js = []
for i, (t, a, b) in enumerate(s3["labels"]):
    a, b = r(a - o), r(b - o)
    lab_js.append(f'tl.fromTo("#s3-l{i}", {{ opacity:0, y:30, filter:"blur(8px)" }}, {{ opacity:1, y:0, filter:"blur(0px)", duration:0.42, ease:"power3.out" }}, {a});')
    lab_js.append(f'tl.fromTo("#s3-l{i} .rule", {{ scaleX:0 }}, {{ scaleX:1, duration:0.4, ease:"power3.inOut" }}, {r(a+0.15)});')
    lab_js.append(f'tl.to("#s3-l{i}", {{ opacity:0, y:-22, filter:"blur(6px)", duration:0.2, ease:"power2.in" }}, {r(b-0.2)});')
s3_js = f"""
          // film keeps the push it had in the reveal, so the scene change is invisible
          tl.fromTo("#s3-film-v", {{ scale:{FILM_PUSH[1]} }}, {{ scale:{FILM_PUSH[2]}, duration:{r(fb-fa)}, ease:"none" }}, 0);
          // film -> card: rack-focus blur-cut on a shared centre line
          tl.to("#s3-film", {{ filter:"blur(18px)", scale:1.06, opacity:0, duration:0.26, ease:"power2.in" }}, {r(fb-0.2)});
          tl.fromTo("#s3-card", {{ opacity:0, scale:0.94, filter:"blur(18px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.42, ease:"power3.out" }}, {r(ca-0.06)});
          tl.fromTo("#s3-card-v", {{ scale:1.0 }}, {{ scale:1.06, duration:{r(cb-ca)}, ease:"none" }}, {ca});
          tl.fromTo("#s3-tag-c", {{ opacity:0, y:8 }}, {{ opacity:1, y:0, duration:0.3, ease:"power2.out" }}, {r(ca+0.25)});
          // card -> list: both travel up, velocity-matched (out on power4.in, in on power4.out)
          tl.to(["#s3-card", "#s3-tag-c"], {{ y:-230, opacity:0, duration:0.22, ease:"power4.in" }}, {r(la-0.22)});
          tl.fromTo("#s3-list", {{ opacity:0, y:230 }}, {{ opacity:1, y:0, duration:0.36, ease:"power4.out" }}, {la});
          tl.fromTo("#s3-tag-l", {{ opacity:0, y:230 }}, {{ opacity:1, y:0, duration:0.36, ease:"power4.out" }}, {r(la+0.04)});
          tl.fromTo("#s3-list-v", {{ scale:1.0, y:0 }}, {{ scale:1.05, y:-14, duration:{r(lb-la)}, ease:"none" }}, {la});
          // list -> live card taps: same direction of travel
          tl.to(["#s3-list", "#s3-tag-l"], {{ y:-230, opacity:0, duration:0.22, ease:"power4.in" }}, {r(xa-0.22)});
          tl.fromTo("#s3-flip", {{ opacity:0, y:230 }}, {{ opacity:1, y:0, duration:0.36, ease:"power4.out" }}, {xa});
          tl.fromTo("#s3-tag-f", {{ opacity:0, y:230 }}, {{ opacity:1, y:0, duration:0.36, ease:"power4.out" }}, {r(xa+0.04)});
          {chr(10).join('          ' + l for l in lab_js).strip()}"""
open("compositions/reveal/s3-product.html", "w").write(scene_file("reveal-s3", S3, s3_css, s3_body, s3_js))

# ------------------------------------------------- scene 4: close + brand
s4 = C["s4"]; S4 = s4["end"] - s4["start"]; bi = r(s4["brand_in"] - s4["start"])
s4_css = f"""
      #root {{ background:{COL['bg']}; }}{PANEL_CSS}
      #s4-brand {{ position:absolute; inset:0; opacity:0; }}
      #s4-brand::before {{ content:""; position:absolute; inset:0;
                           background:radial-gradient(ellipse 70% 45% at 50% 47%, {COL['charcoal']} 0%, {COL['bg']} 70%); }}
      #s4-mark {{ position:absolute; left:50%; top:700px; width:190px; height:190px; margin-left:-95px; }}
      #s4-word {{ position:absolute; left:60px; right:60px; top:948px; text-align:center;
                  font-family:"Barlow Condensed", sans-serif; font-weight:800; font-size:156px; line-height:1; letter-spacing:.02em; }}
      #s4-line {{ position:absolute; left:50%; top:1128px; width:420px; height:4px; margin-left:-210px; background:{COL['blue']}; }}
      #s4-status {{ position:absolute; left:60px; right:60px; top:1168px; text-align:center;
                    font-family:"Inter", sans-serif; font-weight:600; font-size:30px; letter-spacing:.34em; color:{COL['muted']}; }}
      #s4-status i {{ display:inline-block; width:10px; height:10px; border-radius:50%; background:{COL['blue']}; margin-right:16px; vertical-align:3px; }}"""
s4_body = f"""        <div id="s4-hero" class="panel card"><img id="s4-hero-img" data-layout-allow-overflow src="assets/reveal/media/card05.png" alt="Scout card: Pro Set, PA TE Leak"></div>
        {TAG("s4-tag", CP['w'], card_h, CP['cy'])}
        <div id="s4-brand">
          <img id="s4-mark" src="assets/reveal/brand/scoutcard-mark.png" alt="ScoutCard mark">
          <div id="s4-word">{html.escape(s4['wordmark'])}</div>
          <div id="s4-line"></div>
          <div id="s4-status"><i></i>{html.escape(s4['status'])}</div>
        </div>"""
s4_js = f"""
          // hero: the last card the coach tapped to, held and pushed in slowly
          tl.fromTo("#s4-hero-img", {{ scale:1.0 }}, {{ scale:1.12, duration:{bi}, ease:"sine.inOut" }}, 0);
          tl.to("#s4-hero", {{ y:-40, duration:{bi}, ease:"sine.inOut" }}, 0);
          // zoom-through into the brand: the card passes the camera, the brand arrives from just behind it
          tl.to("#s4-tag", {{ opacity:0, duration:0.12, ease:"none" }}, {r(bi-0.36)});
          tl.to("#s4-hero", {{ scale:1.55, opacity:0, filter:"blur(16px)", duration:0.34, ease:"power3.in" }}, {r(bi-0.3)});
          tl.set("#s4-brand", {{ opacity:1 }}, {r(bi-0.02)});
          tl.fromTo("#s4-mark", {{ opacity:0, scale:0.82, filter:"blur(10px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.6, ease:"expo.out" }}, {bi});
          tl.fromTo("#s4-word", {{ opacity:0, scale:0.9, filter:"blur(12px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:0.7, ease:"expo.out" }}, {r(bi+0.12)});
          tl.fromTo("#s4-line", {{ scaleX:0 }}, {{ scaleX:1, duration:0.6, ease:"power3.inOut" }}, {r(bi+0.42)});
          tl.fromTo("#s4-status", {{ opacity:0, y:12 }}, {{ opacity:1, y:0, duration:0.5, ease:"power2.out" }}, {r(bi+0.7)});"""
open("compositions/reveal/s4-close.html", "w").write(scene_file("reveal-s4", S4, s4_css, s4_body, s4_js))

# ------------------------------------------------------------- root: reveal.html
def hosts():
    out = []
    for i, (cid, f, sc) in enumerate([("reveal-s1", "s1-hook", "s1"), ("reveal-s2", "s2-meet", "s2"),
                                      ("reveal-s3", "s3-product", "s3"), ("reveal-s4", "s4-close", "s4")]):
        a, b = C[sc]["start"], C[sc]["end"]
        out.append(f'      <div id="{cid}" class="clip" data-composition-id="{cid}" data-composition-src="compositions/reveal/{f}.html"\n'
                   f'           data-start="{a}" data-duration="{r(b-a)}" data-track-index="{i % 2}" data-width="1080" data-height="1920"></div>')
    return "\n".join(out)

# Subtitles: what he actually says, in short phrases
SUB_SPLITS = {"vo1": [4], "vo2": [5, 9, 12, 15, 21], "vo3": [2, 7]}   # phrase ends (word index, exclusive) per take
subs = []
for k, breaks in SUB_SPLITS.items():
    ws = VO[k]; a = 0
    for b in breaks:
        grp = ws[a:b]
        if grp:
            st = vo_word(k, a); en = r(C["vo"][k] + min(grp[-1]["end"], VO_LEN[k] + VO_TRIM[k]) - VO_TRIM[k] + 0.12)
            subs.append((st, en, " ".join(w["text"] for w in grp)))
        a = b
for i in range(len(subs) - 1):                       # never overlap; join tight gaps
    s, e, t = subs[i]
    subs[i] = (s, min(e, subs[i + 1][0] - 0.02), t)
sub_html = "\n".join(
    f'      <div id="sub-{i}" class="sub clip" data-start="{s}" data-duration="{r(e-s)}" data-track-index="3">'
    f'<span>{html.escape(t)}</span></div>' for i, (s, e, t) in enumerate(subs)) if C["subtitles"] else ""

# Music duck: dip under each line of voiceover (t is seconds from the bed's own start)
m = C["music"]; ms = m["start"]
spans = sorted([(C["vo"][k], C["vo"][k] + VO_LEN[k]) for k in ("vo1", "vo2", "vo3")])
merged = [list(spans[0])]
for a_, b_ in spans[1:]:
    if a_ - merged[-1][1] < 0.9: merged[-1][1] = b_          # short gaps stay ducked (no pumping)
    else: merged.append([a_, b_])
pts = [{"t": 0, "v": 1}]
for n_, (a_, b_) in enumerate(merged):
    nxt_ = merged[n_ + 1][0] if n_ + 1 < len(merged) else None
    up = m["breath"] if nxt_ is not None and nxt_ - b_ < 2.0 else 1      # a breath between lines, not a swell
    pre = pts[-1]["v"]
    pts += [{"t": r(a_ - ms - m["duck_down"]), "v": pre}, {"t": r(a_ - ms), "v": m["duck_to"]},
            {"t": r(b_ - ms), "v": m["duck_to"]}, {"t": r(b_ - ms + m["duck_up"]), "v": up}]
# NB: a volume lane is absolute and replaces data-volume, so scale it by the track level here.
pts = [{**p_, "v": r(p_["v"] * m["volume"])} for p_ in pts]
auto = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": pts}]}).replace('"', "&quot;")

sfx_html = "\n".join(
    f'      <audio id="{i}" src="{f}" data-start="{s}" data-duration="{d}" data-media-start="{ms_}" data-track-index="{12 + n}" data-volume="{v}"></audio>'
    for n, (i, f, s, d, v, ms_) in enumerate(C["sfx"]))
SFX_VOL = {i: v for (i, f, s_, d, v, ms_) in C["sfx"]}
def lane(pid, pts_):   # absolute volume lane = shape x the track's CONFIG level
    return json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [{**p_, "v": r(p_["v"] * SFX_VOL[pid])} for p_ in pts_]}]}).replace('"', "&quot;")
riser_auto = lane("sx-riser", [{"t": 0, "v": 1}, {"t": 2.62, "v": 1}, {"t": 2.70, "v": 0}])
sfx_html = sfx_html.replace('id="sx-riser"', f'id="sx-riser" data-automation="{riser_auto}"')
# the bundled impact sustains for ~2 s; keep its hit, then get out of the voice's way
impact_auto = lane("sx-impact", [{"t": 0, "v": 1}, {"t": 0.18, "v": 0.7}, {"t": 0.42, "v": 0.16, "curve": -0.3}, {"t": 1.4, "v": 0.05}, {"t": 2.0, "v": 0}])
sfx_html = sfx_html.replace('id="sx-impact"', f'id="sx-impact" data-automation="{impact_auto}"')

root = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>ScoutCard reveal</title>
    <script src="vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family:"Inter"; font-weight:600; font-display:block; src:url("assets/reveal/fonts/Inter-600-latin.woff2") format("woff2"); }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:{COL['bg']}; }}
      #reveal {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:{COL['bg']}; }}
      .sub {{ position:absolute; left:110px; right:110px; top:{C['subtitle_cy']}px; transform:translateY(-50%); z-index:50;
              text-align:center; font-family:"Inter", sans-serif; font-weight:600; font-size:36px; line-height:1.3;
              color:rgba(244,245,247,.92); text-shadow:0 2px 12px rgba(0,0,0,.6); }}
    </style>
  </head>
  <body>
    <!-- ScoutCard reveal reel, 20 s. Generated by tools/reveal/build_reveal.py: edit CONFIG there and rebuild.
         Scenes: s1 hook (black + type) / s2 reveal (film) / s3 product (film -> prototype UI) / s4 close + brand.
         Voice: the founder's own three takes. Music: original bed (assets/reveal/music/bed.wav), swappable. -->
    <div id="reveal" data-composition-id="reveal" data-start="0" data-duration="{D}" data-width="1080" data-height="1920" data-fps="30">
{hosts()}

{sub_html}

      <!-- voiceover: the founder's own takes -->
      <audio id="vo1" src="assets/reveal/media/vo1.wav" data-start="{C['vo']['vo1']}" data-duration="{r(VO_LEN['vo1'])}" data-track-index="10" data-volume="{C['vo']['volume']}"></audio>
      <audio id="vo2" src="assets/reveal/media/vo2.wav" data-start="{C['vo']['vo2']}" data-duration="{r(VO_LEN['vo2'])}" data-track-index="10" data-volume="{C['vo']['volume']}"></audio>
      <audio id="vo3" src="assets/reveal/media/vo3.wav" data-start="{C['vo']['vo3']}" data-duration="{r(VO_LEN['vo3'])}" data-track-index="10" data-volume="{C['vo']['volume']}"></audio>
      <!-- music bed: starts on the impact, ducks under each line of voiceover -->
      <audio id="music-bed" src="assets/reveal/music/bed.wav" data-start="{ms}" data-duration="{r(D-ms)}" data-track-index="11" data-volume="{m['volume']}"
             data-automation="{auto}"></audio>
      <!-- sound design -->
{sfx_html}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(f'      tl.fromTo("#sub-{i} span", {{ opacity:0, y:6 }}, {{ opacity:1, y:0, duration:0.14, ease:"power2.out" }}, {s});' for i, (s, e, t) in enumerate(subs)) if C['subtitles'] else ''}
      window.__timelines["reveal"] = tl;
    </script>
  </body>
</html>
"""
open("reveal.html", "w").write(root)
print("built reveal.html + 4 scenes;", len(subs), "subtitle phrases")
for s, e, t in subs: print(f"  {s:6.2f}-{e:6.2f}  {t}")
print("music duck points:", pts)
