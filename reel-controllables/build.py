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
      /* Understated captions: sentence case, warm off-white, a soft plate only
         as strong as legibility needs. */
      .cue {{ position:absolute; left:90px; right:90px; bottom:320px; z-index:20;
        display:flex; justify-content:center; }}
      .cue > span {{ background:rgba(12,12,14,.5); border-radius:12px; padding:10px 20px;
        color:#f4f1ea; font-weight:600; font-size:44px; line-height:1.22; letter-spacing:-.2px;
        text-align:center; text-wrap:balance; }}
      #title {{ position:absolute; inset:0; z-index:20; }}
      #title-in {{ position:absolute; left:90px; right:90px; bottom:320px; text-align:center; }}
      #title-in span {{ display:inline-block; background:rgba(12,12,14,.5); border-radius:12px;
        padding:14px 26px; color:#f4f1ea; font-weight:600; font-size:58px; letter-spacing:-.6px; }}
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
      <audio id="a-roll-audio" src="base.mp4" data-start="0" data-duration="{END}" data-track-index="2" data-volume="1"></audio>

      <div id="title" class="clip" data-start="{TITLE[0]}" data-duration="{TITLE[1]}" data-track-index="3">
        <div id="title-in"><span>Control the controllables.</span></div>
      </div>

{cue_html}

      <!-- Three accents for three structural shifts, nothing else. All
           synthesised for this piece; none come from a stock library. -->
      <audio id="sx-open" src="assets/sfx/boom.wav" data-start="0.2" data-duration="3.4" data-track-index="10" data-volume="0.5"></audio>
      <audio id="sx-swell" src="assets/sfx/crackle.wav" data-start="{round(CUT18-2.62,3)}" data-duration="2.62" data-track-index="11" data-volume="0.4"></audio>
      <audio id="sx-turn" src="assets/sfx/thud.wav" data-start="{CUT18}" data-duration="1.6" data-track-index="12" data-volume="0.45"></audio>
      <audio id="sx-close" src="assets/sfx/boom.wav" data-start="{CUT26}" data-duration="{round(END-CUT26,3)}" data-track-index="10" data-volume="0.32"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.set("#cam", {{ scale:1 }}, 0);
      /* Title settles in rather than popping. */
      tl.fromTo("#title-in", {{ opacity:0, y:14 }}, {{ opacity:1, y:0, duration:.55, ease:"power2.out" }}, 0.22);
      /* The only camera move: a slow push across the confession, reset by the cut. */
      tl.to("#cam", {{ scale:1.05, duration:{round(CUT20-CUT18,3)}, ease:"sine.inOut" }}, {CUT18});
      tl.set("#cam", {{ scale:1 }}, {CUT20});
      /* Let the closing boom fade with the picture instead of being cut off. */
      tl.fromTo("#sx-close", {{ volume:0.32 }}, {{ volume:0, duration:.55, ease:"power1.in" }}, {round(END-0.6,3)});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open("index.html","w").write(html)
json.dump(cues,open("cues.json","w"),indent=1)
print(f"{len(cues)} caption cues; avg {sum(c['dur'] for c in cues)/len(cues):.2f}s, range {min(c['dur'] for c in cues):.2f}-{max(c['dur'] for c in cues):.2f}s")
