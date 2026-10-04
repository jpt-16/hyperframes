import json
W=json.load(open("transcript.json")); C=json.load(open("clip_starts.json"))
END=C["_end"]; TITLE=(0.0,2.25)
# Captions: phrase-sized chunks that follow the speech (break on punctuation or
# a real pause), so they change with his rhythm instead of a fixed word count.
cues=[]; cur=[]; prev=None
def flush():
    global cur
    if cur:
        cues.append({"text":" ".join(x["text"] for x in cur),"start":cur[0]["start"],"end":cur[-1]["end"]}); cur=[]
for w in W:
    if w["start"]<TITLE[1]: continue
    if prev is not None and w["start"]-prev>0.35: flush()
    cur.append(w); j=" ".join(x["text"] for x in cur)
    if w["text"][-1] in ".?!," and len(j)>=12: flush()
    elif len(j)>=34 or len(cur)>=7: flush()
    prev=w["end"]
flush()
# never strand a lone sentence-ending word ("be | great.") on its own card
i=0
while i < len(cues)-1:
    nx=cues[i+1]
    if len(nx["text"].split())==1 and nx["text"][-1] in ".?!" and len(cues[i]["text"])+len(nx["text"])<=46:
        cues[i]["text"]+=" "+nx["text"]; cues[i]["end"]=nx["end"]; cues.pop(i+1)
    else: i+=1
for i,c in enumerate(cues):
    nxt=cues[i+1]["start"] if i+1<len(cues) else END
    c["dur"]=round(min(max(c["end"]-c["start"]+0.25,0.6), nxt-c["start"]-0.04),3)
cue_html="\n".join(f'      <div id="cue-{i+1}" class="cue clip" data-start="{c["start"]}" data-duration="{c["dur"]}" data-track-index="1"><span>{c["text"]}</span></div>' for i,c in enumerate(cues))
CUT18, CUT20, CUT26 = C["IMG_1818"], C["IMG_1820"], C["IMG_1826"]
HWCSS=open("hw-helpers.css").read()
def CALLOUT(i,x,y,w,h):
    return (f'<div class="hw-callout" id="{i}" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px">'
            f'<div class="hw-co-boil"><div class="hw-co-deform"><svg viewBox="0 0 {w} {h}">'
            f'<path class="hw-co-scribble"></path><path class="hw-co-outline"></path></svg></div>'
            f'<svg class="hw-co-conn-layer" viewBox="0 0 {w} {h}"><path class="hw-co-connector"></path></svg>'
            f'<div class="hw-co-pop"><div class="hw-co-label" data-layout-allow-overflow></div></div></div></div>')
ITEMS=[("find leads",27.76),("convert clients",28.72),("build a better brand",31.84),("more content",34.64)]
ROWS="\n".join(f'          <div class="lrow" id="row{i}"><div class="lbox hw-mark" id="box{i}"><svg viewBox="0 0 52 52"><path></path></svg></div>'
                + (f'<div class="lcheck hw-mark" id="chk{i}"><svg viewBox="0 0 70 66"><path></path></svg></div>' if i==3 else "")
                + f'<div class="ltxt hand" id="txt{i}">{t}</div></div>' for i,(t,_) in enumerate(ITEMS))
VID=next(w["start"] for w in W if w["text"].lower().startswith("videos"))
BR_IN, BR_OUT = round(187/30,4), round(372/30,4)
TAPS="\n".join(f'      <audio id="pn-tap{i}" src="assets/sfx/pen/tap{i}.wav" data-start="{round(t-0.05,3)}" data-duration="0.22" data-track-index="15" data-volume="0.6"></audio>' for i,(_,t) in enumerate(ITEMS))
CC=next(w["start"] for w in W if w["text"].lower().startswith("creation"))
html=f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Control the Controllables</title>
    <script src="vendor/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ margin:0; width:1080px; height:1920px; overflow:hidden; background:#000; }}
      body {{ font-family: Inter, "Liberation Sans", sans-serif; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }}
      #cam {{ position:absolute; inset:0; overflow:hidden; transform-origin:50% 36%; }}
      #broll {{ position:absolute; inset:0; overflow:hidden; z-index:5; background:#111; }}
      #batter {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
                 object-position:46% 50%; transform-origin:52% 34%; }}
      /* Understated captions: sentence case, warm off-white, a soft plate only
         as strong as legibility needs. */
      .cue {{ position:absolute; left:90px; right:90px; bottom:320px; z-index:20;
        display:flex; justify-content:center; }}
      .cue > span {{ background:rgba(12,12,14,.5); border-radius:12px; padding:10px 20px;
        color:#f4f1ea; font-weight:600; font-size:44px; line-height:1.22; letter-spacing:-.2px;
        text-align:center; text-wrap:balance; }}
      @font-face {{ font-family:"Caveat"; src:url("assets/fonts/Caveat-700-latin.woff2") format("woff2");
        font-weight:700; font-display:block; }}
      {HWCSS}
      /* Hand-drawn layer: Caveat + wobbled strokes, warm off-white ink; one
         marker-orange accent, reserved for the single check that pays off. */
      .hand {{ font-family:"Caveat", cursive; font-weight:700; color:#f4f2ec;
        text-shadow:0 2px 3px rgba(0,0,0,.85), 0 0 16px rgba(0,0,0,.6); }}
      #title {{ position:absolute; inset:0; z-index:20; }}
      #title-in {{ position:absolute; left:60px; right:60px; bottom:300px; text-align:center; font-size:92px; line-height:1; }}
      #title-in .w {{ position:relative; display:inline-block; }}
      #title-mark {{ position:absolute; left:-6px; right:-6px; bottom:-20px; height:34px; }}
      .ovl {{ position:absolute; inset:0; z-index:15; pointer-events:none; }}
      .colabel {{ position:absolute; text-align:center; white-space:nowrap; }}
      /* The face sits low in these clips, so the hand-drawn layer lives in the
         clear band above the eyes (wall / ceiling / hair), on a feathered dark
         patch so off-white ink reads over a bright wall. Feathered, not a card. */
      .band {{ position:absolute; left:20px; right:20px; top:150px; height:470px; }}
      .patch {{ position:absolute; left:-60px; right:-60px; top:-70px; bottom:-70px;
        background:radial-gradient(ellipse at 50% 50%, rgba(14,12,10,.5) 0%, rgba(14,12,10,.36) 40%, rgba(14,12,10,.12) 64%, rgba(14,12,10,0) 82%);
        filter:blur(26px); }}
      #rows {{ position:absolute; left:230px; top:60px; width:640px; }}
      .lrow {{ position:relative; height:80px; }}
      .lbox {{ position:absolute; left:0; top:12px; width:52px; height:52px; }}
      .lbox svg, .lcheck svg {{ width:100%; height:100%; overflow:visible; }}
      .lbox path, .lcheck path {{ fill:none; stroke-linecap:round; stroke-linejoin:round; }}
      .lbox path {{ stroke:#f4f2ec; stroke-width:5; }}
      .lcheck {{ position:absolute; left:-4px; top:0; width:70px; height:66px; }}
      .lcheck path {{ stroke:#ffb020; stroke-width:9; }}
      /* padding keeps Caveat's overhanging strokes inside the write-on mask */
      .ltxt {{ position:absolute; left:74px; top:0; font-size:56px; line-height:76px; white-space:nowrap; padding:0 18px 0 4px; }}
      .colabel {{ padding:0 14px; }}
      #title-mark path {{ stroke:#f4f2ec !important; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1080" data-height="1920">
      <!-- Six clips, tone-mapped, joined with their natural pauses intact: only
           one pause over 0.9s existed and it was shortened, not removed. Video
           and audio were cut on identical frame boundaries. Voice: declip,
           75 Hz highpass, gentle 2:1, plain gain, one oversampled limiter that
           is idle 99.9% of the time. -16 LUFS. -->
      <div id="cam">
        <video id="a-roll" class="clip" src="base.mp4" muted playsinline data-start="0" data-duration="{END}"
          data-track-index="0" style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>
      </div>
      <!-- Real b-roll, his own photo: hard cut in on "playing sports", out
           on "and you put your best effort", so the effort line lands on his face. -->
      <div id="broll" class="clip" data-start="{BR_IN}" data-duration="{round(BR_OUT-BR_IN,4)}" data-track-index="6">
        <img id="batter" data-layout-allow-overflow src="assets/broll/batter.jpg" alt="">
      </div>
      <audio id="a-roll-audio" src="base.mp4" data-start="0" data-duration="{END}" data-track-index="2" data-volume="1"></audio>

      <div id="title" class="clip" data-start="{TITLE[0]}" data-duration="{TITLE[1]}" data-track-index="3">
        <div id="title-in" class="hand">Control the <span class="w">controllables.<span class="hw-mark" id="title-mark"><svg viewBox="0 0 420 34" preserveAspectRatio="none"><path vector-effect="non-scaling-stroke"></path></svg></span></span></div>
      </div>

      <!-- Circle of control, drawn as he describes it. -->
      <div id="circle" class="ovl clip" data-start="13.5" data-duration="10.45" data-track-index="4">
        <div class="band"><div class="patch"></div></div>
        {CALLOUT("co-in", 375, 335, 330, 170)}
        <div class="colabel hand" id="co-in-txt" style="left:375px; top:378px; width:330px; font-size:54px;">your effort</div>
        {CALLOUT("co-out", 170, 200, 740, 420)}
        <div class="colabel hand" id="co-out-txt" style="left:170px; top:598px; width:740px; font-size:48px;">out of your control</div>
      </div>

      <!-- What he admits he could be doing: boxes stay empty until the payoff. -->
      <div id="listwrap" class="ovl clip" data-start="27.5" data-duration="38.4" data-track-index="5">
        <div id="list" class="band"><div class="patch"></div>
          <div id="rows">
{ROWS}
          </div>
        </div>
      </div>

{cue_html}

      <!-- Three accents for three structural shifts, nothing else. All
           synthesised for this piece; none come from a stock library. -->
      <audio id="sx-open" src="assets/sfx/boom.wav" data-start="0.2" data-duration="3.4" data-track-index="10" data-volume="0.13"></audio>
      <audio id="sx-swell" src="assets/sfx/crackle.wav" data-start="{round(CUT18-2.62,3)}" data-duration="2.62" data-track-index="11" data-volume="0.3"></audio>
      <audio id="sx-turn" src="assets/sfx/thud.wav" data-start="{CUT18}" data-duration="1.6" data-track-index="12" data-volume="0.35"></audio>
      <!-- Hand-drawn layer foley: pen-on-paper, synthesised (assets/sfx/pen/gen.py).
           Each stroke is exactly as long as its line's draw and its loudness
           follows the draw's own velocity curve. Levels verified offline. -->
      <audio id="pn-underline" src="assets/sfx/pen/stroke_06.wav" data-start="1.25" data-duration="0.68" data-track-index="13" data-volume="0.4"></audio>
      <audio id="pn-circle-in" src="assets/sfx/pen/stroke_07.wav" data-start="13.6" data-duration="0.78" data-track-index="13" data-volume="0.4"></audio>
      <audio id="pn-write-in" src="assets/sfx/pen/write_05.wav" data-start="13.85" data-duration="0.5" data-track-index="14" data-volume="0.25"></audio>
      <audio id="pn-circle-out" src="assets/sfx/pen/stroke_07.wav" data-start="20.4" data-duration="0.78" data-track-index="13" data-volume="0.4"></audio>
      <audio id="pn-write-out" src="assets/sfx/pen/write_06.wav" data-start="20.7" data-duration="0.6" data-track-index="14" data-volume="0.25"></audio>
{TAPS}
      <audio id="pn-rustle" src="assets/sfx/pen/rustle.wav" data-start="{round(CC-0.35,3)}" data-duration="0.55" data-track-index="16" data-volume="0.3"></audio>
      <audio id="pn-check" src="assets/sfx/pen/check.wav" data-start="{round(VID,3)}" data-duration="0.45" data-track-index="17" data-volume="0.55"></audio>
      <audio id="sx-close" src="assets/sfx/boom.wav" data-start="{CUT26}" data-duration="{round(END-CUT26,3)}" data-track-index="10" data-volume="0.085"></audio>
    </div>
    <script src="hw-helpers.js"></script>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.set("#cam", {{ scale:1 }}, 0);
      /* B-roll still: one slow push toward his hands and helmet, no fades. */
      tl.fromTo("#batter", {{ scale:1.0 }}, {{ scale:1.07, duration:{round(BR_OUT-BR_IN,4)}, ease:"none" }}, {BR_IN});
      const wob = (n, seed, a) => window.hwHash(n, seed) * a;
      /* Title: handwritten, settles in; the underline draws itself under
         "controllables" as he lands the word. */
      document.querySelector("#title-mark path").setAttribute("d", window.hwMarkPath(420, 34, "underline", 3));
      tl.fromTo("#title-in", {{ opacity:0, y:12 }}, {{ opacity:1, y:0, duration:.55, ease:"power2.out" }}, 0.22);
      window.hwMarkOn(tl, "#title-mark", 1.25, 0.6);
      window.hwBoil(tl, "#title-in", {{ amp:1.2, rot:0.35, frameDrop:3, seed:3 }});

      /* Circle of control */
      ["#co-in", "#co-out"].forEach((id, k) => window.hwCalloutBuild(id, {{ scribble:false, connector:false,
        seed:5 + k, label:"", labelAt:"below", strokeType:"soft", boil:"calm" }}));
      window.hwCalloutOn(tl, "#co-in", 13.6);
      tl.fromTo("#co-in-txt", {{ opacity:0, clipPath:"inset(0 100% 0 0)" }}, {{ opacity:1, clipPath:"inset(0 0% 0 0)", duration:.5, ease:"power1.inOut" }}, 13.85);
      window.hwCalloutOn(tl, "#co-out", 20.4);
      tl.fromTo("#co-out-txt", {{ opacity:0, clipPath:"inset(0 100% 0 0)" }}, {{ opacity:1, clipPath:"inset(0 0% 0 0)", duration:.6, ease:"power1.inOut" }}, 20.7);
      tl.to("#circle", {{ opacity:0, duration:.4, ease:"power2.in" }}, 23.45);

      /* The list: each box is drawn, then its words are written, on the word. */
      const boxPath = (seed) => {{
        const p = [[4,5],[48,3],[50,47],[3,49]].map((q, i) => [q[0] + wob(i*3+1, seed, 2.2), q[1] + wob(i*3+2, seed, 2.2)]);
        return "M" + p[0] + " L" + p[1] + " L" + p[2] + " L" + p[3] + " Z";
      }};
      [{",".join(f"{t:.2f}" for _,t in ITEMS)}].forEach((t, i) => {{
        document.querySelector("#box" + i + " path").setAttribute("d", boxPath(11 + i));
        tl.set("#row" + i, {{ opacity:0 }}, 0);
        tl.set("#row" + i, {{ opacity:1 }}, t - 0.05);
        window.hwMarkOn(tl, "#box" + i, t - 0.05, 0.35);
        tl.fromTo("#txt" + i, {{ clipPath:"inset(0 100% 0 0)" }}, {{ clipPath:"inset(0 0% 0 0)", duration:.55, ease:"power1.inOut" }}, t + 0.15);
      }});
      document.querySelector("#chk3 path").setAttribute("d",
        "M" + [8 + wob(1,9,2), 34 + wob(2,9,2)] + " Q" + [20, 52] + " " + [27 + wob(3,9,2), 58] + " Q" + [40, 30] + " " + [66 + wob(4,9,2), 4 + wob(5,9,2)]);
      tl.set("#chk3", {{ opacity:0 }}, 0);
      window.hwBoil(tl, "#rows", {{ amp:1.1, rot:0.3, frameDrop:3, seed:7 }});
      tl.set("#list", {{ opacity:1 }}, 0);
      tl.to("#list", {{ opacity:0, duration:.35, ease:"power2.in" }}, {round(CUT20-0.45,3)});
      /* Payoff: the list comes back on "content creation" and the content box
         finally gets its check on "videos". */
      tl.fromTo("#list", {{ opacity:0 }}, {{ opacity:1, duration:.45, ease:"power2.out", immediateRender:false }}, {round(CC-0.35,3)});
      tl.set("#chk3", {{ opacity:1 }}, {round(VID,3)});
      window.hwMarkOn(tl, "#chk3", {round(VID,3)}, 0.45);
      tl.to("#list", {{ opacity:0, duration:.45, ease:"power2.in" }}, {round(VID+3.0,3)});
      /* The only camera move: a slow push across the confession, reset by the cut. */
      tl.to("#cam", {{ scale:1.05, duration:{round(CUT20-CUT18,3)}, ease:"sine.inOut" }}, {CUT18});
      tl.set("#cam", {{ scale:1 }}, {CUT20});
      /* Let the closing boom fade with the picture instead of being cut off. */
      tl.fromTo("#sx-close", {{ volume:0.085 }}, {{ volume:0, duration:.55, ease:"power1.in" }}, {round(END-0.6,3)});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open("index.html","w").write(html)
json.dump(cues,open("cues.json","w"),indent=1)
print(f"{len(cues)} caption cues; avg {sum(c['dur'] for c in cues)/len(cues):.2f}s, range {min(c['dur'] for c in cues):.2f}-{max(c['dur'] for c in cues):.2f}s")
