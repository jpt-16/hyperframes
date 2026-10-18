"""Original sound for the egg reel (synthesised, no samples, no music).

    python3 tools/sfx.py        # writes assets/sfx/*.wav

roll    - an egg rolling on stone: a granular shell-on-stone texture whose grain rate and
          level follow the egg's speed and its distance to camera, with the slow
          once-per-turn swell of an uneven shell. Timed to the 3D shot (assets/egg.js).
edge    - the little knock as it leaves the edge
crack   - the impact at the match cut: a cluster of sharp shell cracks, a wet splat, a thud
shards  - pieces skittering away as the old site breaks
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "jtb-shorts", "lib"))
from audio import SR, T, write
from sfx import space, _bp

rng = np.random.default_rng(907)

# must match assets/egg.js
T_EDGE, V0, ACC, R = 1.5, 2.2, 1.0, 0.7463

def click(dur=0.004, lo=1500, hi=7000):
    t = T(dur * 6)
    return _bp(rng.standard_normal(len(t)), lo, hi) * np.exp(-t / dur)

def place(buf, x, t, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if 0 <= i < j: buf[i:j] += x[: j - i] * g

def roll():
    L = int(T_EDGE * SR) + int(0.05 * SR); buf = np.zeros(L); body = np.zeros(L)
    t = 0.0
    while t < T_EDGE:
        v = V0 + ACC * t
        rate = 70 * v / V0                                   # grains per second rise with speed
        d = V0 * t + 0.5 * ACC * t * t
        turn = 0.6 + 0.4 * np.sin(d / R) ** 2                # uneven shell: louder once per half turn
        near = 0.45 + 0.55 * (t / T_EDGE) ** 1.5             # egg comes toward the camera
        place(buf, click(0.0015 + 0.002 * rng.random(), 1200, 6500), t, (0.25 + 0.75 * rng.random()) * turn * near)
        t += rng.exponential(1 / rate)
    tt = np.arange(L) / SR
    v = V0 + ACC * np.minimum(tt, T_EDGE)
    d = V0 * tt + 0.5 * ACC * tt ** 2
    rumble = _bp(rng.standard_normal(L), 90, 420) * (0.35 + 0.65 * np.sin(d / R) ** 2) * (v / (V0 + ACC * T_EDGE)) * (0.45 + 0.55 * (tt / T_EDGE) ** 1.5)
    x = buf * 0.9 + rumble * 0.5
    x *= np.minimum(1, tt / 0.05) * np.clip((T_EDGE + 0.02 - tt) / 0.03, 0, 1)
    return space(np.stack([x, x * 0.96], 1), 0.25, 0.08)

def edge():
    t = T(0.25)
    knock = np.sin(2 * np.pi * np.cumsum(420 + 600 * np.exp(-t / 0.004)) / SR) * np.exp(-t / 0.02)
    x = knock * 0.6
    tk = click(0.002, 1500, 6000); x[: len(tk)] += tk * 0.7
    return space(np.stack([x, x], 1), 0.3, 0.1)

def crack():
    t = T(0.9); x = np.zeros(len(t))
    for k in range(9):                                        # the shell giving way: a tight cluster of cracks
        place(x, click(0.0012 + 0.0015 * rng.random(), 1800, 9500), 0.002 + 0.004 * k + 0.003 * rng.random(), 0.6 + 0.6 * rng.random())
    crackle = _bp(rng.standard_normal(len(t)), 2200, 8000) * np.exp(-t / 0.05) * (rng.random(len(t)) > 0.85) * 0.8
    splat = _bp(rng.standard_normal(len(t)), 180, 1400) * np.exp(-np.clip(t - 0.01, 0, None) / 0.07) * (t > 0.01) * 0.55
    thud = np.sin(2 * np.pi * np.cumsum(70 + 90 * np.exp(-t / 0.015)) / SR) * np.exp(-t / 0.09) * 0.7
    x += crackle + splat + thud
    return space(np.stack([x, x], 1), 0.6, 0.16)

def shards(d=0.7):
    t = T(d); x = np.zeros(len(t))
    for k in range(26):
        tk = (k / 26) ** 1.3 * (d - 0.1) + 0.01 * rng.random()
        place(x, click(0.001 + 0.002 * rng.random(), 2500, 10000), tk, (0.2 + 0.6 * rng.random()) * (1 - tk / d))
    return space(np.stack([x, np.roll(x, 90)], 1), 0.4, 0.14)

if __name__ == "__main__":
    out = os.path.join(HERE, "..", "assets", "sfx"); os.makedirs(out, exist_ok=True)
    write(f"{out}/roll.wav", roll(), -3.0)
    write(f"{out}/edge.wav", edge(), -3.0)
    write(f"{out}/crack.wav", crack(), -1.0)
    write(f"{out}/shards.wav", shards(), -3.0)
    print("assets/sfx written")
