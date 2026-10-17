"""Original risers, pops and a landing thump for the AI-quote reel.

    python3 tools/make_sfx.py

Synthesised (numpy + scipy, fixed seed); every file is peak-normalised AFTER
all shaping. A riser ends exactly at its file end, so placing it at
(arrival - riser length) lands its top on the arrival frame.
"""
import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng = np.random.default_rng(1519)
T = lambda d: np.arange(int(round(d * SR))) / SR
def write(path, st, peak_db=-3.0):
    st = st / (np.max(np.abs(st)) + 1e-12) * 10 ** (peak_db / 20)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
def tv_bandpass(x, f_lo, f_hi, q=1.2, block=256):
    """Band-pass whose centre glides f_lo -> f_hi (exponential), block-wise."""
    out = np.zeros_like(x); n = len(x); zi = None
    for i in range(0, n, block):
        u = i / max(n - 1, 1); fc = f_lo * (f_hi / f_lo) ** u
        lo, hi = fc / (1 + 1 / (2 * q)), min(fc * (1 + 1 / (2 * q)), SR / 2 - 100)
        sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
        if zi is None: zi = np.zeros((sos.shape[0], 2))
        out[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return out
def space(st, secs=0.9, mix=0.22):
    n = int(secs * SR); t = np.arange(n) / SR; out = np.zeros_like(st)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / secs); ir[: int(0.01 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum())
        out[:, c] = fftconvolve(st[:, c], ir)[: len(st)]
    return st * (1 - mix) + out * mix * 1.5

def riser(d, f0=500, f1=7500, tone=(160, 640), brightness=1.0):
    t = T(d); u = t / d
    air = np.stack([tv_bandpass(rng.standard_normal(len(t)), f0, f1 * brightness) for _ in range(2)], 1)
    glide = tone[0] * (tone[1] / tone[0]) ** u
    ph = 2 * np.pi * np.cumsum(glide) / SR
    body = (np.sin(ph) + 0.5 * np.sin(ph * 1.007 * 2) + 0.25 * np.sin(ph * 3.01)) * 0.35
    env = u ** 2.6
    x = air * env[:, None] + (body * env ** 1.3)[:, None]
    x[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))[:, None]   # clean stop at the top
    return space(x, 0.6, 0.18)

def bubble(f0=980, f1=360, tau=0.03, d=0.18):
    t = T(d); f = f1 + (f0 - f1) * np.exp(-t / 0.013)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau) * np.minimum(1, t / 0.0007)
    return space(np.stack([x, x], 1), 0.35, 0.12)

def land(f0=58):
    t = T(0.8); f = f0 * (1 + 1.4 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    click = sosfilt(butter(2, [1500, 6000], btype="band", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t / 0.003) * 0.12
    return space(np.stack([x + click, x + click], 1), 1.0, 0.16)

def popup():
    """A UI pop that reads over speech: falling body + a bright 2-6 kHz snap on the attack."""
    t = T(0.22); f = 520 + (1700 - 520) * np.exp(-t / 0.010)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035) * np.minimum(1, t / 0.0006)
    snap = sosfilt(butter(2, [2000, 6500], btype="band", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t / 0.006) * 0.55
    return space(np.stack([body + snap, body + snap], 1), 0.4, 0.14)

def keys():
    """Pixabay typing (bundled, licensed): skip its 0.42 s of silence, peak-normalise."""
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.42", "-i", "assets/sfx/typing.mp3", "-ac", "2", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)

if __name__ == "__main__":
    write("assets/sfx/popup.wav", popup())
    write("assets/sfx/keys.wav", keys(), -1.0)
    write("assets/sfx/riser-s.wav", riser(0.45, 700, 7000, (220, 660)))
    write("assets/sfx/riser-m.wav", riser(0.75, 500, 8000, (170, 680)))
    write("assets/sfx/riser-l.wav", riser(1.25, 350, 9000, (110, 660)))
    write("assets/sfx/bubble.wav", bubble())
    write("assets/sfx/bubble-in.wav", bubble(760, 300, 0.035))      # the customer's reply: a touch lower
    write("assets/sfx/land.wav", land())
    print("wrote riser-s/m/l, bubble, bubble-in, land")
