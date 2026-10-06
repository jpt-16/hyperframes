import subprocess, json, re, os
F=30; SR=48000
fr=lambda t: int(round(t*F))                       # snap seconds to a frame index
# (clip, in, out) in seconds; ins/outs snapped to frames so picture and sound cut on the same boundary
PLAN=[("IMG_1842",0.00,4.31),
      ("IMG_1863",0.04,8.30),("IMG_1863",8.95,12.87),          # 1.10s hesitation -> ~0.45s
      ("IMG_1853",0.24,10.27),
      ("IMG_1866",0.00,5.40),("IMG_1866",5.85,16.90),          # 0.95s pause -> ~0.5s
      ("IMG_1861",0.08,20.84)]
SEG=[(k,fr(a),fr(b)) for k,a,b in PLAN]
os.makedirs("proc",exist_ok=True)
def lufs(path,af):
    o=subprocess.run(["ffmpeg","-hide_banner","-i",path,"-af",af+",loudnorm=print_format=json","-f","null","-"],capture_output=True,text=True).stderr
    j=json.loads(o[o.rindex("{"):o.rindex("}")+1]); return float(j["input_i"])
PRE="adeclip,highpass=f=75,pan=mono|c0=.5*c0+.5*c1"
for k in sorted({s[0] for s in SEG}):
    I=lufs(f"prep/{k}.mov",PRE); g=-20-I
    subprocess.run(["ffmpeg","-v","error","-y","-i",f"prep/{k}.mov","-vn","-af",
        f"{PRE},volume={g:.2f}dB,acompressor=ratio=2:threshold=-26dB:attack=8:release=160,acompressor=ratio=4:threshold=-16dB:attack=1:release=50:knee=6",
        "-ar","48000","-c:a","pcm_f32le",f"proc/{k}.wav"],check=True)
    print(k,f"in {I:.1f} LUFS gain {g:+.1f}")
clips=sorted({s[0] for s in SEG}); idx={k:i for i,k in enumerate(clips)}
inp=[]
for k in clips: inp+=["-i",f"prep/{k}.mov"]
for k in clips: inp+=["-i",f"proc/{k}.wav"]
fc=[]; n=len(clips)
for i,(k,a,b) in enumerate(SEG):
    d=(b-a)/F
    fc.append(f"[{idx[k]}:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[{n+idx[k]}:a]atrim=start_sample={a*1600}:end_sample={b*1600},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.006,afade=t=out:st={d-0.006:.4f}:d=0.006[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(len(SEG)))+f"concat=n={len(SEG)}:v=1:a=1[v][am]")
fc.append("[am]pan=stereo|c0=c0|c1=c0[a]")
subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[v]","-map","[a]",
    "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p","-c:a","pcm_f32le","-ar","48000","cut.mov"],check=True)
I=lufs("cut.mov","anull"); g=-16-I
subprocess.run(["ffmpeg","-v","error","-y","-i","cut.mov","-c:v","copy","-af",
    f"volume={g:.2f}dB,aresample=192000,alimiter=limit=0.84:attack=4:release=80:level=disabled,aresample=48000",
    "-c:a","aac","-b:a","256k","-ar","48000","-movflags","+faststart","base.mp4"],check=True)
starts=[]; t=0
for k,a,b in SEG: starts.append({"clip":k,"src_in":a/F,"src_out":b/F,"start":round(t,4)}); t+=(b-a)/F
json.dump({"segments":starts,"end":round(t,4)},open("plan.json","w"),indent=1)
print(f"cut {I:.1f} LUFS -> gain {g:+.2f}; total {t:.3f}s")
