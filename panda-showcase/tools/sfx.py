"""Original sound design for the Panda Sports showcase (synthesised, no samples).

    python3 tools/sfx.py        # writes assets/sfx/*.wav

impact  - a heavy cinematic hit: sub drop, body thump, a crack on top, long tail
hit     - a shorter punch for text slams and name cards
riser-s / riser-m / riser-l, whoosh - shared with the JT shorts kit
Music is left out on purpose: the owner lays their own track over this in CapCut.
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "jtb-shorts", "lib"))
from audio import SR, T, write, make_whoosh
from sfx import riser, space, _bp

rng = np.random.default_rng(2026)

def impact(d=2.2, f0=95, f1=34):
    t = T(d)
    f = f1 + (f0 - f1) * np.exp(-t / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    thump = np.sin(2 * np.pi * np.cumsum(70 + 120 * np.exp(-t / 0.012)) / SR) * np.exp(-t / 0.08) * 0.8
    crack = _bp(rng.standard_normal(len(t)), 350, 5200) * np.exp(-t / 0.035) * 0.55
    air = _bp(rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t / 0.25) * 0.12
    x = (sub + thump + crack + air) * np.minimum(1, t / 0.0008)
    st = np.stack([x, x], 1)
    st[:, 1] = np.roll(st[:, 1], int(0.004 * SR))
    return space(st, 1.8, 0.28)

def hit(d=0.7):
    t = T(d)
    body = np.sin(2 * np.pi * np.cumsum(58 + 140 * np.exp(-t / 0.018)) / SR) * np.exp(-t / 0.14)
    snap = _bp(rng.standard_normal(len(t)), 900, 6500) * np.exp(-t / 0.018) * 0.6
    x = (body + snap) * np.minimum(1, t / 0.0006)
    return space(np.stack([x, x], 1), 0.7, 0.2)

def tick():
    """A crisp camera-like click for close-up cuts."""
    t = T(0.12)
    x = _bp(rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t / 0.006) + np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.01) * 0.3
    return space(np.stack([x, x], 1), 0.3, 0.1)

if __name__ == "__main__":
    out = os.path.join(HERE, "..", "assets", "sfx"); os.makedirs(out, exist_ok=True)
    write(f"{out}/impact.wav", impact(), -1.0)
    write(f"{out}/hit.wav", hit(), -1.0)
    write(f"{out}/tick.wav", tick(), -3.0)
    write(f"{out}/riser-s.wav", riser(0.45, 700, 7000, (220, 660)), -3.0)
    write(f"{out}/riser-m.wav", riser(0.75, 500, 8000, (170, 680)), -3.0)
    write(f"{out}/riser-l.wav", riser(1.4, 300, 9500, (90, 640)), -3.0)
    make_whoosh(f"{out}/whoosh.wav")
    print("assets/sfx written")
