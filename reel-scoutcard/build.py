import json, math
W=json.load(open("transcript.json")); A=json.load(open("anchors.json"))
END=94.5; OR="#f47b2c"
# ---------------- captions ----------------
HOOK=(3.45,5.32)
cues=[]; cur=[]; prev=None
def flush():
    global cur
    if cur:
        cues.append({"text":" ".join(x["text"] for x in cur),"start":cur[0]["start"],
                     "dur":round(max(cur[-1]["end"]-cur[0]["start"],0.35)-0.05,3)}); cur=[]
for w in W:
    if HOOK[0]<=w["start"]<HOOK[1]: flush(); prev=None; continue
    if prev is not None and w["start"]-prev>0.42: flush()
    cur.append(w); j=" ".join(x["text"] for x in cur)
    if cur[-1]["text"].endswith((".",",","!","?")) or len(j)>=20 or len(cur)>=4: flush()
    prev=w["end"]
flush()
for i in range(len(cues)-1):
    cues[i]["dur"]=round(min(cues[i]["dur"], cues[i+1]["start"]-cues[i]["start"]-0.04),3)
json.dump(cues,open("cues.json","w"),indent=1)
cue_html="\n".join(f'      <div id="cue-{i+1}" class="cue clip" data-start="{c["start"]}" data-duration="{c["dur"]}" data-track-index="1"><span>{c["text"]}</span></div>' for i,c in enumerate(cues))

# ---------------- founder curve geometry ----------------
pts=[(30,190),(150,160),(270,125),(390,65),(500,90),(610,170),(700,282),(810,160),(910,68)]
labels=["","IDEA","VALUE","$$$","START","PROBLEMS","THE HOLE","CLIMB OUT","PERSEVERANCE"]
times=[5.6,8.32,9.68,12.16,13.44,15.36,18.4,20.2,23.28]
seg=[math.dist(pts[i-1],pts[i]) for i in range(1,len(pts))]
total=sum(seg); cum=[0]
for s in seg: cum.append(cum[-1]+s)
poly=" ".join(f"{x},{y}" for x,y in pts)
nodes=""; lbl=""
for i,((x,y),L) in enumerate(zip(pts,labels)):
    if i==0: continue
    col = "#ff4d2e" if L=="THE HOLE" else (OR if L=="PERSEVERANCE" else "#fff")
    nodes+=f'<circle id="nd-{i}" cx="{x}" cy="{y}" r="11" fill="{col}" stroke="#0b0d11" stroke-width="4"/>'
    ly = y+12 if L=="THE HOLE" else y-26
    anchor = "end" if L in ("PERSEVERANCE","THE HOLE") else "middle"
    lx = x+12 if L=="PERSEVERANCE" else (x-24 if L=="THE HOLE" else x)
    lbl+=f'<text id="lb-{i}" x="{lx}" y="{ly}" text-anchor="{anchor}" fill="{col}" class="clabel">{L}</text>'
draw_js=[]
for i in range(1,len(pts)):
    t_end=times[i]; t0=max(times[i-1], t_end-0.6)
    if labels[i]=="THE HOLE": t0=t_end-0.3
    if labels[i]=="CLIMB OUT": t0=19.28
    draw_js.append(f'tl.to("#curve",{{strokeDashoffset:{total-cum[i]:.1f},duration:{t_end-t0:.2f},ease:"power1.inOut"}},{t0:.2f});')
    draw_js.append(f'tl.fromTo("#nd-{i}",{{scale:0}},{{scale:1,duration:.22,ease:"back.out(3)",svgOrigin:"{pts[i][0]} {pts[i][1]}"}},{t_end:.2f});')
    draw_js.append(f'tl.fromTo("#lb-{i}",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.2,ease:"power2.out"}},{t_end:.2f});')

def chiprows(prefix, items):
    return "\n".join(f'          <div class="row" id="{prefix}-{i+1}"><span class="dot"></span><span class="rtxt">{t}</span></div>' for i,t in enumerate(items))

html=f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>ScoutCard AI Reel</title>
    <script src="vendor/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ margin:0; width:1080px; height:1920px; overflow:hidden; background:#000; }}
      body {{ font-family: Inter, "Liberation Sans", sans-serif; }}
      #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }}
      #cam, #broll-wrap {{ position:absolute; inset:0; overflow:hidden; transform-origin:50% 38%; }}
      #broll-wrap {{ z-index:5; }}
      .overlay {{ position:absolute; inset:0; z-index:10; pointer-events:none; }}

      /* Captions sit on a backing plate so contrast never depends on the frame. */
      .cue {{ position:absolute; left:60px; right:60px; bottom:300px; z-index:30;
        display:flex; justify-content:center; }}
      .cue > span {{ background:rgba(9,11,15,.82); border-radius:18px; padding:16px 26px;
        color:#fff; font-weight:900; text-transform:uppercase; text-align:center; text-wrap:balance;
        font-size:60px; line-height:1.05; letter-spacing:-1.2px; }}

      /* House card: ScoutCard's own dark + orange. */
      .card {{ position:absolute; left:64px; right:64px; bottom:560px;
        background:rgba(11,13,17,.9); border:3px solid rgba(255,255,255,.14);
        border-radius:30px; padding:30px 34px; }}
      .kicker {{ color:{OR}; font-weight:900; font-size:28px; letter-spacing:5px; text-transform:uppercase; }}

      #hook-in {{ position:absolute; left:50px; right:50px; bottom:560px; text-align:center;
        color:#fff; font-weight:900; text-transform:uppercase; font-size:118px; line-height:.94;
        letter-spacing:-3px; text-wrap:balance;
        text-shadow:-5px -5px 0 #000,5px -5px 0 #000,-5px 5px 0 #000,5px 5px 0 #000,0 -6px 0 #000,0 6px 0 #000,-6px 0 0 #000,6px 0 0 #000,0 14px 40px rgba(0,0,0,.8); }}
      #hook-in .o {{ color:{OR}; }}

      #curve-card svg {{ display:block; width:100%; height:auto; margin-top:10px; }}
      .clabel {{ font: 900 32px Inter, sans-serif; letter-spacing:.5px; }}

      .row {{ height:0; overflow:hidden; display:flex; align-items:center; gap:22px; }}
      .row .dot {{ flex:0 0 22px; width:22px; height:22px; border-radius:50%; background:{OR}; }}
      .row .rtxt {{ color:#fff; font-weight:800; font-size:44px; letter-spacing:-.6px; text-transform:uppercase; }}

      #logo-in {{ position:absolute; left:50%; top:820px; width:780px; margin-left:-390px; }}
      #logo-in img {{ display:block; width:780px; border-radius:24px; box-shadow:0 30px 80px rgba(0,0,0,.8); }}

      /* Dropped-features card */
      .chip {{ position:relative; display:inline-block; margin:14px 14px 0 0; padding:14px 26px;
        border-radius:16px; background:#1b1f27; border:3px solid #39404d; color:#fff;
        font-weight:900; font-size:40px; letter-spacing:.5px; }}
      .strike {{ position:absolute; left:-8px; right:-8px; top:50%; height:7px; margin-top:-3px;
        background:#ff3b30; border-radius:4px; transform-origin:0 50%; }}
      .note {{ color:#aab3c2; font-weight:700; font-size:30px; margin-top:12px; }}
      #field {{ display:block; width:100%; height:auto; margin-top:16px; border-radius:16px; }}
      #verdict {{ color:#ff3b30; font-weight:900; font-size:52px; margin-top:12px; letter-spacing:1px; }}

      #stamp-in {{ position:absolute; left:50%; bottom:600px; margin-left:-410px; width:820px;
        padding:34px 20px; border:10px solid {OR}; border-radius:26px; background:rgba(11,13,17,.92);
        text-align:center; color:#fff; font-weight:900; font-size:104px; line-height:.95;
        letter-spacing:-3px; text-transform:uppercase; }}
      #stamp-in .k {{ display:block; color:{OR}; font-size:36px; letter-spacing:6px; margin-bottom:12px; }}

      #end-in {{ position:absolute; left:64px; right:64px; top:300px; text-align:center;
        background:rgba(11,13,17,.93); border:4px solid {OR}; border-radius:34px; padding:44px 36px; }}
      #end-in img {{ display:block; width:100%; border-radius:16px; }}
      #end-in .tag {{ color:#d6dae2; font-weight:700; font-size:38px; margin-top:26px; }}
      #end-in .cta {{ color:{OR}; font-weight:900; font-size:72px; letter-spacing:-1px; margin-top:16px; text-transform:uppercase; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1080" data-height="1920">
      <!-- Base: six clips normalised to -14 LUFS, tone-mapped from HLG,
           concatenated in narrative order, 3.85s of pauses cut, re-normalised.
           Every cue below is a word onset from transcript.json. #cam is a plain
           wrapper so punch-ins scale the picture, never the timed clip. -->
      <div id="cam">
        <video id="a-roll" class="clip" src="base_tight.mp4" muted playsinline data-start="0" data-duration="{END}"
          data-track-index="0" style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>
      </div>
      <audio id="a-roll-audio" src="base_tight.mp4" data-start="0" data-duration="{END}" data-track-index="2" data-volume="1"></audio>

      <!-- Real ScoutCard AI screen recording: status bar cropped, slowed
           10.35s -> 17.0s so the headlines are readable. -->
      <div id="broll-wrap">
        <video id="broll" class="clip" src="assets/scoutcard-broll.mp4" muted playsinline data-start="29.2" data-duration="17.0"
          data-track-index="3" style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover"></video>
      </div>

      <div id="hook" class="overlay clip" data-start="3.5" data-duration="1.8" data-track-index="4">
        <div id="hook-in">Not everything is <span class="o">as it seems</span></div>
      </div>

      <div id="curve-wrap" class="overlay clip" data-start="5.36" data-duration="22.1" data-track-index="5">
        <div id="curve-card" class="card">
          <div class="kicker">Every founder&rsquo;s curve</div>
          <svg viewBox="0 0 940 330" aria-hidden="true">
            <line x1="0" y1="190" x2="940" y2="190" stroke="#2a2f39" stroke-width="3" stroke-dasharray="8 10"/>
            <polyline id="curve" points="{poly}" fill="none" stroke="{OR}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"
              stroke-dasharray="{total:.1f}" stroke-dashoffset="{total:.1f}"/>
            {nodes}
            {lbl}
          </svg>
        </div>
      </div>

      <div id="logo" class="overlay clip" data-start="28.4" data-duration="0.85" data-track-index="6">
        <div id="logo-in"><img src="assets/scoutcard-logo.png" alt="ScoutCard AI" /></div>
      </div>

      <div id="flow" class="overlay clip" data-start="37.3" data-duration="8.85" data-track-index="7">
        <div id="flow-card" class="card">
          <div class="kicker">How it works</div>
{chiprows("fr",["Hudl export in","Scout cards. Instantly.","AI checks every card"])}
        </div>
      </div>

      <div id="drop" class="overlay clip" data-start="47.4" data-duration="20.0" data-track-index="8">
        <div id="drop-card" class="card">
          <div class="kicker">What I almost built</div>
          <div>
            <span class="chip" id="chip-film">AI FILM<span class="strike" id="st-1"></span></span>
            <span class="chip" id="chip-cv">CV TRACKING<span class="strike" id="st-2"></span></span>
          </div>
          <div class="note" id="note-hudl">Hudl may already have this.</div>
          <div id="field-wrap" style="height:0; overflow:hidden">
          <svg id="field" viewBox="0 0 940 260" aria-hidden="true">
            <rect width="940" height="260" fill="#1d5a2c"/>
            {"".join(f'<line x1="{x}" y1="0" x2="{x}" y2="260" stroke="#ffffff" stroke-opacity=".35" stroke-width="3"/>' for x in range(70,940,100))}
            {"".join(f'<g id="pl-{k}"><rect x="-26" y="-26" width="52" height="52" fill="none" stroke="#7cf" stroke-width="3"/><circle r="11" fill="#fff"/><text y="-36" text-anchor="middle" fill="#7cf" style="font:800 20px Inter,sans-serif">x,y</text></g>' for k in range(1,5))}
          </svg>
          </div>
          <div id="verdict-wrap" style="height:0; overflow:hidden"><div id="verdict">UNREALISTIC. UNNECESSARY.</div></div>
        </div>
      </div>

      <div id="stamp" class="overlay clip" data-start="{A['one_product']}" data-duration="2.0" data-track-index="9">
        <div id="stamp-in"><span class="k">So I&rsquo;m focusing on</span>One product.</div>
      </div>

      <div id="sum" class="overlay clip" data-start="69.7" data-duration="7.6" data-track-index="10">
        <div id="sum-card" class="card">
          <div class="kicker">To sum it up</div>
{chiprows("sr",["A real problem","That adds value","For HS football coaches"])}
        </div>
      </div>

      <div id="next" class="overlay clip" data-start="{A['more_videos']}" data-duration="11.8" data-track-index="11">
        <div id="next-card" class="card">
          <div class="kicker">Coming next</div>
{chiprows("nx",["More ScoutCard AI videos","Stay tuned","+ A players version"])}
        </div>
      </div>

      <div id="end" class="overlay clip" data-start="89.44" data-duration="{round(END-89.44,2)}" data-track-index="12">
        <div id="end-in">
          <img src="assets/scoutcard-logo-end.png" alt="ScoutCard AI" />
          <div class="tag">Built for high school football staffs.</div>
          <div class="cta">Stay tuned</div>
        </div>
      </div>

      <!-- Captions -->
{cue_html}

      <!-- SFX: bundled media-use library. Overlapping hits sit on separate
           lanes so the deliberate layering never reads as a collision. -->
      <audio id="sx-riser-hook" src=".media/audio/sfx/riser-short.mp3" data-start="2.32" data-duration="1.4" data-track-index="20" data-volume="0.45"></audio>
      <audio id="sx-hook" src=".media/audio/sfx/sfx_001.mp3" data-start="3.52" data-duration="2.11" data-track-index="21" data-volume="0.55"></audio>
      <audio id="sx-n1" src=".media/audio/sfx/tick-1.mp3" data-start="8.32" data-duration="0.8" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-n2" src=".media/audio/sfx/tick-2.mp3" data-start="9.68" data-duration="0.7" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-n3" src=".media/audio/sfx/tick-3.mp3" data-start="12.16" data-duration="0.6" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-hole" src=".media/audio/sfx/sfx_002.mp3" data-start="18.4" data-duration="2.0" data-track-index="21" data-volume="0.5"></audio>
      <audio id="sx-climb" src=".media/audio/sfx/sfx_004.mp3" data-start="19.28" data-duration="0.6" data-track-index="22" data-volume="0.5"></audio>
      <audio id="sx-pers" src=".media/audio/sfx/tick-3.mp3" data-start="23.28" data-duration="0.6" data-track-index="23" data-volume="0.4"></audio>
      <audio id="sx-logo" src=".media/audio/sfx/sfx_004.mp3" data-start="28.4" data-duration="0.6" data-track-index="22" data-volume="0.45"></audio>
      <audio id="sx-broll" src=".media/audio/sfx/sfx_003.mp3" data-start="29.2" data-media-start="2.1" data-duration="1.6" data-track-index="21" data-volume="0.5"></audio>
      <audio id="sx-f1" src=".media/audio/sfx/tick-1.mp3" data-start="37.44" data-duration="0.8" data-track-index="22" data-volume="0.4"></audio>
      <audio id="sx-f2" src=".media/audio/sfx/tick-2.mp3" data-start="40.72" data-duration="0.7" data-track-index="22" data-volume="0.4"></audio>
      <audio id="sx-f3" src=".media/audio/sfx/tick-3.mp3" data-start="43.6" data-duration="0.6" data-track-index="22" data-volume="0.4"></audio>
      <audio id="sx-back" src=".media/audio/sfx/sfx_001.mp3" data-start="46.2" data-duration="2.0" data-track-index="21" data-volume="0.4"></audio>
      <audio id="sx-c1" src=".media/audio/sfx/tick-1.mp3" data-start="{A['ai_film']}" data-duration="0.8" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-c2" src=".media/audio/sfx/tick-2.mp3" data-start="{A['cv']}" data-duration="0.7" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-strike" src=".media/audio/sfx/sfx_005.mp3" data-start="{A['unrealistic']}" data-duration="0.9" data-track-index="23" data-volume="0.4"></audio>
      <audio id="sx-stamp" src=".media/audio/sfx/sfx_001.mp3" data-start="{A['one_product']}" data-duration="2.0" data-track-index="21" data-volume="0.55"></audio>
      <audio id="sx-s1" src=".media/audio/sfx/tick-1.mp3" data-start="{A['problem2']}" data-duration="0.8" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-s2" src=".media/audio/sfx/tick-2.mp3" data-start="71.36" data-duration="0.7" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-s3" src=".media/audio/sfx/tick-3.mp3" data-start="{A['coaches2']}" data-duration="0.6" data-track-index="22" data-volume="0.35"></audio>
      <audio id="sx-next" src=".media/audio/sfx/sfx_004.mp3" data-start="{A['more_videos']}" data-duration="0.6" data-track-index="22" data-volume="0.45"></audio>
      <audio id="sx-epic" src=".media/audio/sfx/sfx_002.mp3" data-start="{A['epic']}" data-duration="2.0" data-track-index="21" data-volume="0.45"></audio>
      <audio id="sx-riser-end" src=".media/audio/sfx/riser-short.mp3" data-start="88.24" data-duration="1.4" data-track-index="20" data-volume="0.4"></audio>
      <audio id="sx-end" src=".media/audio/sfx/sfx_001.mp3" data-start="89.44" data-duration="2.11" data-track-index="21" data-volume="0.5"></audio>
    </div>

    <script>
      const tl = gsap.timeline({{ paused: true }});
      const card = (sel, t0, t1) => {{
        tl.fromTo(sel, {{ opacity:0, y:40 }}, {{ opacity:1, y:0, duration:.28, ease:"power3.out" }}, t0);
      }};
      const rows = (pre, times) => times.forEach((t, i) =>
        tl.fromTo("#" + pre + "-" + (i + 1), {{ height:0, opacity:0 }},
          {{ height:72, opacity:1, duration:.24, ease:"power3.out" }}, t));
      const punch = (t, hold) => {{
        tl.to("#cam", {{ scale:1.12, duration:.16, ease:"power3.out" }}, t);
        tl.to("#cam", {{ scale:1, duration:.25, ease:"power2.inOut" }}, t + hold);
      }};

      tl.set("#cam", {{ scale:1 }}, 0);

      /* Hook: slam + punch-in on "not everything is as it seems". */
      tl.fromTo("#hook-in", {{ opacity:0, scale:1.35 }}, {{ opacity:1, scale:1, duration:.16, ease:"power4.out" }}, 3.52);
      punch(3.52, 1.6);

      /* Founder curve: draws itself as he narrates, dives on "hole". */
      card("#curve-card", 5.36, 27.46);
      {chr(10).join("      "+j for j in draw_js).strip()}

      /* Logo sting, then the real product. */
      tl.fromTo("#logo-in", {{ opacity:0, scale:.8 }}, {{ opacity:1, scale:1, duration:.2, ease:"back.out(2)" }}, 28.4);
      tl.fromTo("#broll-wrap", {{ scale:1.14 }}, {{ scale:1, duration:.35, ease:"power3.out" }}, 29.2);
      tl.to("#broll-wrap", {{ scale:1.05, duration:16.5, ease:"none" }}, 29.55);
      card("#flow-card", 37.3, 46.15);
      rows("fr", [37.44, 40.72, 43.6]);

      /* Dropped features: tracking dots move, then get struck out. */
      card("#drop-card", 47.4, 67.4);
      tl.fromTo("#chip-film", {{ opacity:0, scale:.8 }}, {{ opacity:1, scale:1, duration:.2, ease:"back.out(2.5)" }}, {A['ai_film']});
      tl.fromTo("#note-hudl", {{ opacity:0 }}, {{ opacity:1, duration:.2 }}, {A['similar'] if 'similar' in A else 52.4});
      tl.fromTo("#chip-cv", {{ opacity:0, scale:.8 }}, {{ opacity:1, scale:1, duration:.2, ease:"back.out(2.5)" }}, {A['cv']});
      tl.fromTo("#field-wrap", {{ height:0 }}, {{ height:262, duration:.32, ease:"power3.out" }}, {A['cv']});
      const P = [[120,55,560,60],[220,110,700,105],[90,165,780,160],[300,220,860,215]];  /* separate lanes: labels never cross */
      P.forEach((p, i) => tl.fromTo("#pl-" + (i + 1), {{ x:p[0], y:p[1] }},
        {{ x:p[2], y:p[3], duration:{A['unrealistic']-A['cv']-0.2:.2f}, ease:"sine.inOut" }}, {A['cv']}));
      tl.fromTo("#st-1", {{ scaleX:0 }}, {{ scaleX:1, duration:.18, ease:"power3.out" }}, {A['unrealistic']});
      tl.fromTo("#st-2", {{ scaleX:0 }}, {{ scaleX:1, duration:.18, ease:"power3.out" }}, {A['unrealistic']+0.12:.2f});
      tl.fromTo("#verdict-wrap", {{ height:0 }}, {{ height:76, duration:.18, ease:"power3.out" }}, {A['unrealistic']+0.1:.2f});
      tl.fromTo("#verdict", {{ opacity:0, scale:.9 }}, {{ opacity:1, scale:1, duration:.18, ease:"back.out(2)" }}, {A['unrealistic']+0.1:.2f});

      /* Decision stamp + punch-in. */
      tl.fromTo("#stamp-in", {{ opacity:0, scale:1.5, rotation:-12 }}, {{ opacity:1, scale:1, rotation:-4, duration:.22, ease:"back.out(1.8)" }}, {A['one_product']});
      punch({A['one_product']}, 1.0);

      card("#sum-card", 69.7, 77.3);
      rows("sr", [{A['problem2']}, 71.36, {A['coaches2']}]);

      card("#next-card", {A['more_videos']}, 89.24);
      rows("nx", [{A['more_videos']}, {A['stay_tuned']}, {A['players']}]);
      punch({A['epic']}, 0.9);

      tl.fromTo("#end-in", {{ opacity:0, scale:.9 }}, {{ opacity:1, scale:1, duration:.3, ease:"back.out(1.6)" }}, 89.44);

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open("index.html","w").write(html)
print(f"{len(cues)} caption cues; curve length {total:.0f}")
