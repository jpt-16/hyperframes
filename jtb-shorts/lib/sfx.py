"""Original sound effects for JT Builds Co shorts (all synthesised; no samples).

    python3 lib/sfx.py          # rewrites brand/sfx/*.wav

Risers end exactly at their file end (the mixer places them so the top lands on
the cue). Every file is peak-normalised after all shaping, fixed seeds.
key_click() is called by the mixer once per typed character.
"""
import os, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from audio import SR, T, write, make_whoosh

rng = np.random.default_rng(1519)

def _bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)

def tv_bandpass(x, f_lo, f_hi, q=1.2, block=256):
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

def riser(d, f0=500, f1=7500, tone=(160, 640)):
    t = T(d); u = t / d
    air = np.stack([tv_bandpass(rng.standard_normal(len(t)), f0, f1) for _ in range(2)], 1)
    ph = 2 * np.pi * np.cumsum(tone[0] * (tone[1] / tone[0]) ** u) / SR
    body = (np.sin(ph) + 0.5 * np.sin(ph * 1.007 * 2) + 0.25 * np.sin(ph * 3.01)) * 0.35
    env = u ** 2.6
    x = air * env[:, None] + (body * env ** 1.3)[:, None]
    x[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))[:, None]
    return space(x, 0.6, 0.18)

def bubble(f0=980, f1=360, tau=0.03, d=0.18):
    t = T(d); f = f1 + (f0 - f1) * np.exp(-t / 0.013)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau) * np.minimum(1, t / 0.0007)
    return space(np.stack([x, x], 1), 0.35, 0.12)

def land(f0=58):
    t = T(0.8); f = f0 * (1 + 1.4 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    click = _bp(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t / 0.003) * 0.12
    return space(np.stack([x + click, x + click], 1), 1.0, 0.16)

def popup():
    """UI pop: falling body + a bright 2-6.5 kHz snap on the attack so it reads over music."""
    t = T(0.22); f = 520 + (1700 - 520) * np.exp(-t / 0.010)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035) * np.minimum(1, t / 0.0006)
    snap = _bp(rng.standard_normal(len(t)), 2000, 6500) * np.exp(-t / 0.006) * 0.55
    return space(np.stack([body + snap, body + snap], 1), 0.4, 0.14)

def key_click(seed):
    """One soft laptop key: a short plastic tick + a little low thock. Varies per seed. Peak ~ -6 dBFS."""
    g = np.random.default_rng(seed); t = T(0.06)
    tick = _bp(g.standard_normal(len(t)), 2200 + 900 * g.random(), 7500) * np.exp(-t / (0.0028 + 0.0012 * g.random()))
    f = 170 + 60 * g.random()
    thock = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012) * (0.35 + 0.2 * g.random())
    x = tick + thock; x *= np.minimum(1, t / 0.0004)
    x /= np.max(np.abs(x)) + 1e-12
    pan = g.uniform(-0.25, 0.25)
    return np.stack([x * (1 - pan), x * (1 + pan)], 1) * 0.5

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "brand", "sfx")
    write(f"{out}/popup.wav", popup(), -3.0)
    write(f"{out}/riser-s.wav", riser(0.45, 700, 7000, (220, 660)), -3.0)
    write(f"{out}/riser-m.wav", riser(0.75, 500, 8000, (170, 680)), -3.0)
    write(f"{out}/riser-l.wav", riser(1.25, 350, 9000, (110, 660)), -3.0)
    write(f"{out}/bubble.wav", bubble(), -3.0)
    write(f"{out}/land.wav", land(), -3.0)
    make_whoosh(f"{out}/whoosh.wav")
    print("brand/sfx rebuilt")
