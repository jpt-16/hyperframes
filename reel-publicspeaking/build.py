"""Generate index.html for the public-speaking reel from transcript.json + clip_plan.json."""
import json, re, html

W = json.load(open("transcript.json"))
PLAN = json.load(open("clip_plan.json"))
END = PLAN["end"]

def at(word, n=1):
    """Cut-timeline start of the n-th occurrence of a word (punctuation ignored)."""
    hits = [w for w in W if re.sub(r"[^\w']", "", w["text"]).lower() == word]
    return hits[n - 1]["start"]

# Structural beats, all read off the transcript
SPOT1_ON = round(at("spotlight") - 0.03, 3)          # "under the spotlight"
SPOT1_OFF = PLAN["segments"][3]["start"]              # the cut to "Public speaking teaches"
CONF = at("confidence", 3)                            # "...it's having confidence."
CONF_OUT = PLAN["segments"][6]["start"]               # cut to "I still get nervous"
SPOT2_ON = round(at("spotlight", 2) - 0.03, 3)        # "get in the spotlight"

# ---- caption chunking: short phrases, broken on pauses and punctuation ----
def clean(t):
    return t.rstrip(".,:;")   # creator style: no trailing commas/periods; keep "?" and inner apostrophes

WEAK = {"a","an","the","to","of","on","in","and","or","but","that","i","i'm","is","are","my","your","you",
        "for","with","be","it's","have","some","any","when","which","so","because","going","not"}
OPENERS = {"and","but","because","so","when","which","why"}
bare = lambda t: re.sub(r"[^\w']", "", t).lower()

def cost(ws, last_in_run):
    t = " ".join(x["text"] for x in ws); n = len(t)
    c = (n - 16) ** 2 / 14
    if n > 25 or len(ws) > 5: c += 400
    if len(ws) == 1 and not last_in_run: c += 30
    if bare(ws[-1]["text"]) in WEAK and not last_in_run: c += 45
    if ws[-1]["text"].endswith(","): c -= 12
    if ws[-1]["end"] - ws[0]["start"] < 0.45 and not last_in_run: c += 35   # too quick to read
    return c

def split_run(run):
    """Optimal phrase breaks inside one run of speech (no pauses, no sentence ends)."""
    best = [0.0] + [1e9] * len(run); prev = [0] * (len(run) + 1)
    for j in range(1, len(run) + 1):
        for i in range(max(0, j - 6), j):
            c = best[i] + cost(run[i:j], j == len(run))
            if j < len(run) and bare(run[j]["text"]) in OPENERS: c -= 10
            if c < best[j]: best[j], prev[j] = c, i
    out, j = [], len(run)
    while j > 0: out.append(run[prev[j]:j]); j = prev[j]
    return out[::-1]

runs, cur = [], []
for i, w in enumerate(W):
    if CONF - 0.01 <= w["start"] < CONF_OUT:     # the thesis word gets its own moment
        continue
    cur.append(w)
    nxt = W[i + 1] if i + 1 < len(W) else None
    if (nxt is None or CONF - 0.01 <= nxt["start"] < CONF_OUT or nxt["start"] - w["start"] > 0.62
            or re.search(r"[.?!:]$", w["text"])):
        runs.append(cur); cur = []
chunks = [c for r in runs for c in split_run(r)]

cues = []
for i, c in enumerate(chunks):
    s = round(c[0]["start"] - 0.04, 3)
    nxt = chunks[i + 1][0]["start"] - 0.04 if i + 1 < len(chunks) else END
    e = min(c[-1]["end"] + 0.22, nxt - 0.001)
    if c[-1]["start"] < CONF and nxt > CONF - 0.06:
        e = min(e, CONF - 0.02)
    cues.append({"start": s, "dur": round(max(e - s, 0.3), 3), "words": c})

cap_html, cap_js = [], []
for i, q in enumerate(cues):
    spans = []
    for j, w in enumerate(q["words"]):
        t = clean(w["text"])
        if i == 0 and j == 0:
            t = t[:1].upper() + t[1:]
        spans.append(f'<span class="w" id="c{i}w{j}">{html.escape(t)}</span>')
    cap_html.append(f'      <div id="cap-{i}" class="cap clip" data-start="{q["start"]}" data-duration="{q["dur"]}" '
                    f'data-track-index="1"><span class="line">{" ".join(spans)}</span></div>')
    gap_before = i == 0 or q["start"] - (cues[i - 1]["start"] + cues[i - 1]["dur"]) > 0.25
    if gap_before:
        cap_js.append(f'tl.fromTo("#cap-{i} .line", {{y:16, opacity:0}}, {{y:0, opacity:1, duration:0.16, ease:"power2.out"}}, {q["start"]});')
    else:
        cap_js.append(f'tl.fromTo("#cap-{i} .line", {{y:6}}, {{y:0, duration:0.12, ease:"power2.out"}}, {q["start"]});')
    ws = q["words"]
    for j, w in enumerate(ws):
        on = max(w["start"], q["start"])
        cap_js.append(f'hi("#c{i}w{j}", {on}{"" if j + 1 == len(ws) else ", " + str(ws[j + 1]["start"])});')

CAPS = "\n".join(cap_html)
CAPJS = "\n      ".join(cap_js)

page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family:"Bricolage"; src:url("assets/fonts/BricolageGrotesque-var-latin.woff2") format("woff2");
                   font-weight:200 800; font-display:block; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }}

      /* Captions: one short phrase at a time on the shirt, under the chin.
         Bold grotesk in sentence case; the word being spoken gets a warm
         marker block, so the line reads at a glance on a light grey shirt. */
      .cap {{ position:absolute; left:64px; right:64px; bottom:500px; z-index:30; text-align:center;
              font-family:"Bricolage", sans-serif; font-weight:760; font-size:70px; line-height:1.16;
              letter-spacing:-0.015em; color:#fffaf1; font-optical-sizing:auto; }}
      .cap .line {{ display:inline-block; }}
      .w {{ display:inline-block; padding:0.02em 0.11em 0.07em; margin:0 -0.05em; border-radius:0.22em;
            -webkit-text-stroke:9px rgba(18,14,10,.92); paint-order:stroke fill;
            text-shadow:0 6px 22px rgba(0,0,0,.4); }}

      /* The thesis word, set once and only once. */
      #conf {{ position:absolute; left:0; right:0; top:1290px; z-index:31; text-align:center;
               font-family:"Bricolage", sans-serif; font-weight:800; font-size:150px; letter-spacing:-0.035em;
               color:#ffd447; text-shadow:0 4px 6px rgba(0,0,0,.35), 0 14px 46px rgba(0,0,0,.5); }}

      /* Stage light: the room drops away around him, warm-dark, soft-edged. */
      .spot {{ position:absolute; inset:0; z-index:20; pointer-events:none; }}
      .spot .dark {{ position:absolute; inset:0;
        background:radial-gradient(ellipse 560px 700px at 50% 42%, rgba(6,5,4,0) 0%, rgba(6,5,4,0) 46%,
                   rgba(6,5,4,.55) 74%, rgba(6,5,4,.86) 100%); }}
      #spot2 .dark {{ background:radial-gradient(ellipse 600px 760px at 50% 42%, rgba(8,6,4,0) 0%, rgba(8,6,4,0) 50%,
                   rgba(8,6,4,.45) 76%, rgba(8,6,4,.78) 100%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1080" data-height="1920">
      <!-- Five takes in story order (1842 hook, 1863 fear, 1853 confidence,
           1866 the stakes, 1861 the turn + recommendation). 1856 was a rougher
           take of the 1866 point and is left out. Only two pauses were
           shortened (1.10s -> 0.45s, 0.95s -> 0.5s); every other breath stays.
           Picture and sound cut on identical frame boundaries. Voice: declip,
           75 Hz highpass, 2:1 compressor, a fast 4:1 peak stage, one
           oversampled limiter. -16 LUFS. -->
      <video id="a-roll" class="clip" src="base.mp4" muted playsinline data-start="0" data-duration="{END}"
        data-track-index="0" style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>
      <audio id="a-roll-audio" src="base.mp4" data-start="0" data-duration="{END}" data-track-index="2" data-volume="1"></audio>

      <div id="spot1" class="spot clip" data-start="{SPOT1_ON}" data-duration="{round(SPOT1_OFF - SPOT1_ON, 3)}" data-track-index="3">
        <div class="dark"></div>
      </div>
      <div id="spot2" class="spot clip" data-start="{SPOT2_ON}" data-duration="{round(END - SPOT2_ON, 3)}" data-track-index="3">
        <div class="dark"></div>
      </div>

{CAPS}

      <div id="conf" class="clip" data-start="{round(CONF - 0.03, 3)}" data-duration="{round(CONF_OUT - CONF + 0.03, 3)}" data-track-index="4">confidence.</div>

      <!-- Sound: two stage-light throws and one soft pop. Nothing else. -->
      <audio id="sx-light1" src="assets/sfx/stagelight.wav" data-start="{SPOT1_ON}" data-duration="1.1" data-track-index="10" data-volume="0.32"></audio>
      <audio id="sx-pop" src="assets/sfx/pop_in.wav" data-start="{round(CONF - 0.03, 3)}" data-duration="0.16" data-track-index="11" data-volume="0.45"></audio>
      <audio id="sx-light2" src="assets/sfx/stagelight.wav" data-start="{SPOT2_ON}" data-duration="1.1" data-track-index="10" data-volume="0.32"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      const SHADOW = "0 6px 22px rgba(0,0,0,.4)", STROKE = "9px rgba(18,14,10,.92)";
      /* Active word: marker block on, tiny settle; off when the next word starts. */
      function hi(sel, on, off) {{
        tl.set(sel, {{ backgroundColor:"rgba(255,212,71,1)", color:"#17130d", textShadow:"none", webkitTextStroke:"0px rgba(18,14,10,0)" }}, on);
        tl.fromTo(sel, {{ scale:1.06 }}, {{ scale:1, duration:0.14, ease:"power2.out" }}, on);
        if (off !== undefined) tl.set(sel, {{ backgroundColor:"rgba(255,212,71,0)", color:"#fffaf1", textShadow:SHADOW, webkitTextStroke:STROKE }}, off);
      }}
      {CAPJS}

      /* Stage light: a quick filament stutter, then it holds. Off on the cut. */
      function light(id, t) {{
        tl.set(id, {{ opacity:0 }}, 0);
        tl.to(id, {{ opacity:0.6, duration:0.04, ease:"none" }}, t);
        tl.to(id, {{ opacity:0.25, duration:0.05, ease:"none" }}, t + 0.05);
        tl.to(id, {{ opacity:1, duration:0.32, ease:"power2.out" }}, t + 0.11);
      }}
      light("#spot1", {SPOT1_ON});
      light("#spot2", {SPOT2_ON});

      tl.fromTo("#conf", {{ scale:0.86, opacity:0 }}, {{ scale:1, opacity:1, duration:0.24, ease:"back.out(1.7)" }}, {round(CONF - 0.03, 3)});
      tl.to("#conf", {{ opacity:0, duration:0.1, ease:"none" }}, {round(CONF_OUT - 0.1, 3)});

      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open("index.html", "w").write(page)
json.dump([{"start": q["start"], "dur": q["dur"], "text": " ".join(w["text"] for w in q["words"])} for q in cues],
          open("cues.json", "w"), indent=0)
print(f"{len(cues)} caption cues; spot1 {SPOT1_ON}-{SPOT1_OFF}, confidence {CONF}, spot2 {SPOT2_ON}-{END}")
