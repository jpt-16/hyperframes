"""Offline mix check: base voice + every SFX at its data-volume, band-limited lift per cue.
    python3 tools/sfx_levels.py [scale-overrides as id=vol ...]"""
import subprocess, numpy as np, re, sys
SR = 48000
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
base = load("base.mp4"); mix = base.copy()
rows = re.findall(r'<audio id="([^"]+)" src="assets/sfx/([^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)" data-media-start="([\d.]+)"[^>]*data-volume="([\d.]+)"', open("index.html").read())
cache = {}
for i, f, t, d, ms, v in rows:
    x = cache.setdefault(f, load(f"assets/sfx/{f}"))
    a = int(float(ms) * SR); seg = x[a:a + int(float(d) * SR)] * float(v)
    s = int(float(t) * SR); mix[s:s + len(seg)] += seg[: len(mix) - s]
def band(x, lo, hi):
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); X[(fr < lo) | (fr > hi)] = 0; return np.fft.irfft(X, len(x))
db = lambda x: 10 * np.log10(np.mean(x ** 2) + 1e-15)
BANDS = {"riser": (3500, 11000), "popup": (2000, 6500), "keys": (1000, 6000), "typing": (2500, 9000), "click": (2000, 8000), "bubble": (250, 1500), "pop": (200, 2500),
         "notification": (1000, 6000), "land": (35, 160)}
print(f"{'id':10s} {'t':>6s} {'band':>11s}  lift")
for i, f, t, d, ms, v in rows:
    k = next(b for b in BANDS if f.startswith(b)); lo, hi = BANDS[k]
    t, d = float(t), float(d); a = t + d - 0.18 if k == "riser" else t
    win = 0.18 if k in ("riser", "land", "notification") else 0.04          # transients are heard over ~40 ms
    s = slice(int(a * SR), int((a + win) * SR))
    print(f"{i:10s} {t:6.2f} {lo:>5}-{hi:<5}  {db(band(mix[s], lo, hi)) - db(band(base[s], lo, hi)):+5.1f} dB")
