"""Cut the pauses out of the talking head and remap the transcript to the tightened timeline.
    python3 tools/tighten.py <original.mp4>
Every silence >= 0.20 s is shortened to ~0.09 s (cut from inside it, so no speech is touched).
Writes base.mp4, tools/words.json (retimed) and tools/cuts.json (join points on the new timeline).
"""
import json, subprocess, sys
src = sys.argv[1]
sil = json.load(open("tools/silences.json"))
words = json.load(open("tools/words_raw.json"))
KEEP = 0.045
removed = [(a + KEEP, b - KEEP) for a, b in sil if b - a >= 0.20]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
segs, t = [], 0.0
for a, b in removed: segs.append((t, a)); t = b
segs.append((t, dur))
def newt(x):
    off = 0.0
    for a, b in removed:
        if x >= b: off += b - a
        elif x > a: return a - off
    return x - off
for w in words: w["s"] = round(newt(w["s"]), 3); w["e"] = round(newt(w["e"]), 3)
json.dump(words, open("tools/words.json", "w"))
cuts, acc = [], 0.0
for a, b in segs[:-1]: acc += b - a; cuts.append(round(acc, 3))
json.dump(cuts, open("tools/cuts.json", "w"))
fc = "".join(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(segs))
fc += "".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a];"
fc += "[v]scale=1080:1920:flags=lanczos:in_range=full:out_range=tv,format=yuv420p,fps=30[vo]"
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[vo]", "-map", "[a]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
    "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "base.mp4"])
print("segments", len(segs), "removed", round(sum(b - a for a, b in removed), 2), "s; new length", round(newt(dur), 2))
