"""An original, synthesised beat for the Chase reel (no samples, so it is ours to publish).

    python3 tools/beat.py        # writes assets/beat.wav

120 BPM in F minor, so one beat = 0.5 s and every picture cut lands on the grid:
0-2     in hot: kick, 808, clap, hats from the first frame
2-4     the push-in: drums filtered down, 16th hats, a snare roll that speeds up, a breath of silence at 3.875
4-9     the drop: full kit, 808 line, minor stabs
9-11    the end card: the same groove, then one last hit that rings out by 11.5
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "jtb-shorts", "lib"))
from audio import SR, T, hz, write, _f, _reverb, _place

BPM = 120; B = 60 / BPM; D = 11.5
rng = np.random.default_rng(1)

def kick():
    t = T(0.45)
    body = np.sin(2 * np.pi * np.cumsum(46 + 120 * np.exp(-t / 0.028)) / SR) * np.exp(-t / 0.22)
    click = _f(rng.standard_normal(len(t)), "high", 2500) * np.exp(-t / 0.002) * 0.35
    return np.tanh(1.6 * (body + click))

def bass808(f, d):
    t = T(d)
    f_t = f * (1 + 0.9 * np.exp(-t / 0.018))
    x = np.sin(2 * np.pi * np.cumsum(f_t) / SR) * np.exp(-t / 0.9) * np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(2.2 * x) * 0.8

def clap():
    t = T(0.35); x = np.zeros(len(t))
    for k, dt in enumerate([0, 0.009, 0.019]):
        i = int(dt * SR); n = _f(rng.standard_normal(len(t) - i), "band", [900, 3200])
        x[i:] += n * np.exp(-t[: len(t) - i] / (0.006 if k < 2 else 0.11))
    return x * 0.9

def hat(open_=False):
    t = T(0.25 if open_ else 0.06)
    return _f(rng.standard_normal(len(t)), "high", 7500) * np.exp(-t / (0.09 if open_ else 0.014)) * 0.5

def snare():
    t = T(0.2)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04) * 0.5
    return (tone + _f(rng.standard_normal(len(t)), "band", [1500, 7000]) * np.exp(-t / 0.06)) * 0.7

def stab(notes, d=0.32):
    t = T(d); x = np.zeros(len(t))
    for n in notes:
        for det in (-0.08, 0.08):
            ph = (hz(n) * (1 + det / 100) * t) % 1.0
            x += (2 * ph - 1)
    x = _f(x * np.exp(-t / 0.12), "low", 2600)
    return x / len(notes) * 0.45

def build():
    L = int(D * SR); drums = np.zeros((L, 2)); low = np.zeros((L, 2)); music = np.zeros((L, 2))
    K, C, H, HO, S = kick(), clap(), hat(), hat(True), snare()
    BASS = ["F1", None, None, "F1", None, None, "Ab1", "C2"]          # one bar of eighths
    for bar in range(6):
        t0 = bar * 4 * B
        build_bar = 2.0 <= t0 < 4.0
        for e in range(8):                                             # eighth-note grid
            t = t0 + e * B / 2
            if t >= 11.0: break
            if build_bar:
                continue
            if e in (0, 3) or (e == 5 and bar % 2): _place(drums, K, t, 1.0)
            if e in (2, 6): _place(drums, C, t, 0.8, 0.0)
            _place(drums, H if e % 2 else HO if e == 7 else H, t, 0.55 if e % 2 else 0.4, 0.35)
            if BASS[e] and t < 11.0: _place(low, bass808(hz(BASS[e]), 0.48 if e == 7 else 0.7), t, 0.9)
            if t >= 4.0 and e in (0, 3):                               # minor stabs only after the drop
                _place(music, stab(["F3", "Ab3", "C4"] if e == 0 else ["Eb3", "G3", "Bb3"]), t, 0.8, -0.25)
    # 2-4: the build. filtered kick on the beat, 16th hats, a roll that doubles up, then a 1/8 breath before the drop
    for k in range(4):
        _place(drums, K, 2.0 + k * B, 0.55)
    for k in range(16):
        _place(drums, H, 2.0 + k * B / 4, 0.25 + 0.25 * k / 16, 0.35)
    t, step = 3.0, B / 2
    while t < 3.875 - 1e-6:
        _place(drums, S, t, 0.35 + 0.5 * (t - 3.0) / 0.875, 0.1)
        if t >= 3.5: step = B / 8
        elif t >= 3.25: step = B / 4
        t += step
    # the final hit at 11.0: kick + 808 + stab, left to ring out
    _place(drums, K, 11.0, 1.1); _place(low, bass808(hz("F1"), 0.5), 11.0, 0.9); _place(music, stab(["F3", "Ab3", "C4", "F4"], 0.5), 11.0, 0.9)
    # the 2-4 section sits under a low-pass that opens as it builds
    seg = slice(int(2.0 * SR), int(3.875 * SR))
    drums[seg] = _f(drums[seg], "low", 3800)
    drums[int(3.875 * SR): int(4.0 * SR)] *= 0.0
    low[int(3.875 * SR): int(4.0 * SR)] *= 0.0
    music = _reverb(music, rng, 1.4, 5000, 0.3)
    mix = drums * 0.9 + low * 0.85 + music * 0.6
    fade = np.clip((D - np.arange(L) / SR) / 0.12, 0, 1)
    return mix * fade[:, None]

if __name__ == "__main__":
    write(os.path.join(HERE, "..", "assets", "beat.wav"), build(), -3.0)
    print("assets/beat.wav written")
