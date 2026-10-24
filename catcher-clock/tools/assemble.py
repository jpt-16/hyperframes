"""Lay the voiceover lines on one track with designed pauses -> assets/vo/vo.wav + assets/vo/timing.json."""
import json, os, subprocess, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, "..", "assets", "vo")
SR = 48000
GAP_AFTER = [0.35, 0.6, 0.5, 0.35, 0.65, 0.3, 0.6, 0.3, 0.6, 0.35, 1.7]   # pause after each line
START = 0.35

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

lines = json.load(open(os.path.join(VO, "lines.json")))
t, clips, timing = START, [], []
for ln, gap in zip(lines, GAP_AFTER):
    x = load(os.path.join(VO, f"{ln['i']:02d}.wav"))
    nz = np.where(np.abs(x) > 0.004)[0]                      # trim the model's leading/trailing silence
    x = x[max(0, nz[0] - int(0.02 * SR)): nz[-1] + int(0.06 * SR)]
    clips.append((t, x)); timing.append({"i": ln["i"], "text": ln["text"], "t0": round(t, 3), "t1": round(t + len(x) / SR, 3)})
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
