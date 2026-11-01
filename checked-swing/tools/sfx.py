"""Original sounds for the video (synthesised, no samples).
    python3 tools/sfx.py       # writes assets/sfx/{crowd,glove,tick}.wav
crowd - a distant ballpark murmur with slow swells (a low bed under the whole video)
glove - a ball smacking into a leather glove: a sharp snap and a short low thump
tick  - one stopwatch tick
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "jtb-shorts", "lib"))
from audio import SR, T, write, _f
from sfx import space, _bp
rng = np.random.default_rng(31)

def crowd(d=56.0):
    t = T(d); out = np.zeros((len(t), 2))
    for c in range(2):
        n = rng.standard_normal(len(t))
        babble = _bp(n, 250, 2600)
        swell = 0.6 + 0.4 * np.convolve(rng.standard_normal(len(t) // 4800 + 2), np.ones(6) / 6, "same")
        env = np.interp(t, np.linspace(0, d, len(swell)), swell)
        hiss = _bp(rng.standard_normal(len(t)), 3000, 7000) * 0.08
        out[:, c] = babble * env + hiss
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.5)
    return out * fade[:, None]

def glove():
    t = T(0.35)
    snap = _bp(rng.standard_normal(len(t)), 900, 5200) * np.exp(-t / 0.006)
    thump = np.sin(2 * np.pi * np.cumsum(140 + 260 * np.exp(-t / 0.01)) / SR) * np.exp(-t / 0.045) * 0.9
    x = snap * 1.1 + thump
    return space(np.stack([x, x], 1), 0.35, 0.12)

def tick():
    t = T(0.08)
    x = _bp(rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t / 0.004) + np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.008) * 0.4
    return np.stack([x, x], 1)

if __name__ == "__main__":
    out = os.path.join(HERE, "..", "assets", "sfx")
    write(f"{out}/crowd.wav", crowd(), -6.0)
    write(f"{out}/glove.wav", glove(), -1.0)
    write(f"{out}/tick.wav", tick(), -3.0)
    print("assets/sfx: crowd, glove, tick")
