"""Cut pauses/fillers out of his video -> media/base.mp4 (picture and sound on identical frame boundaries).
    python3 tools/cut_base.py <original talking-head upload>
Keeps the un-cut version as media/base_src.mp4 for reference."""
import json, subprocess, sys, os
src = sys.argv[1]; C = json.load(open("tools/cuts.json")); F = 30
keep, t = [], 0.0
for a, b in C["remove"]:
    keep.append((t, a)); t = b
keep.append((t, C["end"]))
fc = []
for i, (a, b) in enumerate(keep):
    fa, fb = round(a * F), round(b * F); d = (fb - fa) / F
    fc.append(f"[0:v]trim=start_frame={fa}:end_frame={fb},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[a48]atrim=start_sample={fa * 1600}:end_sample={fb * 1600},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.006,afade=t=out:st={d - 0.006:.4f}:d=0.006[a{i}]")
fc.insert(0, "[0:v]fps=30,setsar=1[vf];[0:a]aresample=48000,asplit=1[a48]")
fc = [x.replace("[0:v]trim", "[vs{0}]trim") for x in fc]
# split the fps-normalised video once per segment
n = len(keep)
fc[0] = f"[0:v]fps=30,setsar=1,split={n}" + "".join(f"[vs{i}]" for i in range(n)) + ";[0:a]aresample=48000,asplit=" + str(n) + "".join(f"[as{i}]" for i in range(n))
fc = [fc[0]] + [x.replace("[vs{0}]", f"[vs{k // 2}]").replace("[a48]", f"[as{k // 2}]") for k, x in enumerate(fc[1:])]
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-g", "15", "-keyint_min", "15", "-sc_threshold", "0",
                "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "media/base.mp4"], check=True)
total = sum(round(b * F) - round(a * F) for a, b in keep) / F
print(f"{n} segments kept, {C['end'] - total:.2f}s removed, new length {total:.3f}s")
