"""Lay the voiceover lines on one track with designed pauses -> assets/vo/vo.wav + assets/vo/timing.json
(line start/end and every word's start/end on the video's clock)."""
import json, os, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, "..", "assets", "vo")
SR = 48000
GAP_AFTER = {"h1": 0.5, "d1": 0.45, "d2": 0.6, "r1": 0.35, "r2": 0.45, "a1": 0.5, "a2": 0.45, "a3": 0.6, "l1": 0.4, "l2": 0.5, "e1": 0.3, "e2": 1.2}
AT = {"d1": 6.0, "r1": 15.0, "a1": 25.0, "l1": 38.0, "e1": 47.0}   # scene starts from the brief: each scene's first line starts no earlier than its time
START = 0.2

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

lines = json.load(open(os.path.join(VO, "lines.json")))
t, clips, timing = START, [], []
for ln in lines:
    gap = GAP_AFTER[ln["id"]]
    t = max(t, AT.get(ln["id"], 0.0))
    x = load(os.path.join(VO, f"{ln['i']:02d}.wav"))
    nz = np.where(np.abs(x) > 0.004)[0]                      # trim the model's leading/trailing silence
    a = max(0, nz[0] - int(0.02 * SR))
    x = x[a: nz[-1] + int(0.06 * SR)]
    words = [{"w": w["w"], "t0": round(t + w["start"] - a / SR, 3), "t1": round(t + w["end"] - a / SR, 3)} for w in ln.get("words", [])]
    clips.append((t, x)); timing.append({"i": ln["i"], "id": ln["id"], "text": ln["text"], "spoken": ln.get("spoken", ln["text"]), "t0": round(t, 3), "t1": round(t + len(x) / SR, 3), "words": words})
    t += len(x) / SR + gap
D = round(t, 2)
buf = np.zeros(int(D * SR) + SR)
for t0, x in clips:
    i = int(t0 * SR); buf[i:i + len(x)] += x
buf = buf[: int(D * SR)]
buf *= 10 ** (-3 / 20) / np.max(np.abs(buf))
w = wave.open(os.path.join(VO, "vo.wav"), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((buf * 32767).astype(np.int16).tobytes()); w.close()
json.dump({"duration": D, "lines": timing}, open(os.path.join(VO, "timing.json"), "w"), indent=1)
for x in timing: print(f"{x['t0']:6.2f}-{x['t1']:6.2f}  {x['text']}")
print("duration", D)
