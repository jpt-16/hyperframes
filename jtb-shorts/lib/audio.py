"""Original audio for JT Builds Co shorts (synthesised here, so it is ours to publish).

make_bed() writes a music bed sized to one video: its own BPM grid, a drop
right before the CTA, the CTA landing on a downbeat chord, and a tail that
rings out to silence by the last frame. make_whoosh() makes the transition
swish. Everything is deterministic (fixed seeds), so a rebuild is identical.
"""
import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
T = lambda d: np.arange(int(round(d * SR))) / SR
def _f(x, kind, f, order=2): return sosfilt(butter(order, f, btype=kind, fs=SR, output="sos"), x, axis=0)
def hz(note):
    names = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    return 440 * 2 ** ((names[note[:-1]] + 12 * (int(note[-1]) + 1) - 69) / 12)

def write(path, st, peak_db=-1.0):
    st = st / (np.max(np.abs(st)) + 1e-12) * 10 ** (peak_db / 20)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

def _reverb(x, rng, secs=1.8, damp=6000, mix=0.25):
    n = int(secs * SR); t = np.arange(n) / SR; out = np.zeros_like(x)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / secs); ir = _f(ir, "low", damp); ir[: int(0.012 * SR)] = 0
        out[:, c] = fftconvolve(x[:, c], ir / np.sqrt((ir ** 2).sum()))[: len(x)]
    return x * (1 - mix) + out * mix * 1.6

def _place(buf, x, t, g=1.0, pan=0.0):
    i = int(round(t * SR)); j = min(len(buf), i + len(x))
    if j <= i or i < 0: return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:j, 0] += x[: j - i] * g * l * 1.414; buf[i:j, 1] += x[: j - i] * g * r * 1.414

STYLES = {   # bpm, chord loop (one chord per bar), resolve chord, arp on/off
    "drive": dict(bpm=118, chords=[["A2", "E3", "A3", "C4"], ["F2", "C3", "F3", "A3"], ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3"]],
                  resolve=["A2", "E3", "A3", "C4", "E4"], arp=True),
    "glow":  dict(bpm=100, chords=[["D3", "A3", "D4", "F4"], ["Bb2", "F3", "Bb3", "D4"], ["F2", "C3", "F3", "A3"], ["C3", "G3", "C4", "E4"]],
                  resolve=["D3", "A3", "D4", "F4", "E4"], arp=False),
    "pulse": dict(bpm=124, chords=[["E3", "B3", "E4", "G4"], ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3"], ["D3", "A3", "D4", "F#4"]],
                  resolve=["E3", "B3", "E4", "G4", "F#4"], arp=True),
}

def make_bed(path, duration, cta_t, style="drive", seed=7):
    """A bed that starts at 0, drops for one beat before cta_t, lands a chord on cta_t, and fades out by duration."""
    S = STYLES[style]; rng = np.random.default_rng(seed)
    beat = 60 / S["bpm"]; bar = 4 * beat
    L = int(duration * SR); pad = np.zeros((L, 2)); hits = np.zeros((L, 2)); low = np.zeros((L, 2)); arp = np.zeros((L, 2))
    saw = lambda f, t, det: 2 * ((f * 2 ** (det / 1200) * t + rng.random()) % 1) - 1
    def kick():
        t = T(0.3); f = 46 + 95 * np.exp(-t / 0.032)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.1)
    def hat(open_=False):
        t = T(0.22 if open_ else 0.05); return _f(rng.standard_normal(len(t)), "high", 8000) * np.exp(-t / (0.05 if open_ else 0.01))
    def clap():
        t = T(0.3); n = _f(rng.standard_normal(len(t)), "band", [900, 3400])
        return n * (np.exp(-t / 0.008) + 0.5 * np.exp(-np.clip(t - 0.012, 0, None) / 0.01) * (t > 0.012) + 0.5 * np.exp(-t / 0.08))
    def pluck(f):
        t = T(0.35); x = saw(f, t, 0) * 0.7 + np.sign(np.sin(2 * np.pi * f * t)) * 0.2
        return _f(x, "low", 2600) * np.exp(-t / 0.12)
    # where the CTA lands on the grid: snap to the nearest beat so the chord is musical
    cta_b = round(cta_t / beat); cta_g = cta_b * beat
    drop_from = cta_g - beat
    nb = int(np.ceil(cta_g / bar)) + 1
    for b in range(nb):
        t0 = b * bar
        if t0 >= cta_g: break
        notes = S["chords"][b % len(S["chords"])]
        dur = min(bar, cta_g - t0) + 0.25
        tt = T(dur)
        env = np.minimum(1, tt / 0.25) * np.minimum(1, (dur - tt) / 0.2)
        for n in notes:
            v = sum(saw(hz(n), tt, d) for d in (-8, 0, 8)) / 3
            _place(pad, _f(v, "low", 1100) * env, t0, 0.09, rng.uniform(-0.5, 0.5))
        root = hz(notes[0]) / 2 if hz(notes[0]) > 90 else hz(notes[0])
        for k in range(8):                                   # pumping eighth-note sub bass
            ts = t0 + k * beat / 2
            if ts >= drop_from: break
            td = T(beat / 2); v = np.sin(2 * np.pi * root * td) + 0.2 * np.sin(4 * np.pi * root * td)
            v *= np.minimum(1, td / 0.01) * (1 - 0.6 * np.exp(-td / 0.08)); v[-int(0.015 * SR):] *= np.linspace(1, 0, int(0.015 * SR)) ** 2
            _place(low, v, ts, 0.22)
        for k in range(16):                                  # drums
            ts = t0 + k * beat / 4
            if ts >= drop_from or ts < bar * 0.5: continue   # half a bar of air at the top for the hook hit
            if k % 4 == 0: _place(hits, kick(), ts, 0.55)
            if k in (4, 12): _place(hits, clap(), ts, 0.2, 0.05)
            _place(hits, hat(k % 4 == 2), ts, 0.06 * [1, .35, .6, .35][k % 4], 0.3)
            if S["arp"] and b >= 1 and k % 2 == 0:
                tones = [hz(n) * 2 for n in notes[1:4]]
                _place(arp, pluck(tones[(k // 2) % 3]), ts, 0.04, -0.35 if k % 4 else 0.35)
    # swell into the CTA, then the landing chord + kick + low boom, ringing out
    sw = _f(rng.standard_normal(int(beat * SR)), "band", [2500, 9000]) * np.linspace(0, 1, int(beat * SR)) ** 3
    _place(hits, sw, drop_from, 0.09)
    tail = max(duration - cta_g, 0.5); tt = T(tail)
    for n in S["resolve"]:
        v = sum(saw(hz(n), tt, d) for d in (-7, 0, 7)) / 3
        _place(pad, _f(v, "low", 1600) * np.exp(-tt / (tail * 0.45)) * np.minimum(1, tt / 0.01), cta_g, 0.10, rng.uniform(-0.6, 0.6))
    _place(hits, kick(), cta_g, 0.5)
    bt = T(min(2.2, tail)); _place(low, np.sin(2 * np.pi * np.cumsum(36 + 30 * np.exp(-bt / 0.05)) / SR) * np.exp(-bt / 0.6), cta_g, 0.3)
    d = int(0.75 * beat * SR); ad = arp.copy()
    for k, g in enumerate([0.45, 0.2], 1): ad[d * k:] += arp[: -d * k] * g
    mix = _reverb(pad + ad, rng, 2.4, 5000, 0.33) + low + _reverb(hits, rng, 0.8, 7000, 0.1)
    t = np.arange(L) / SR
    mix *= np.clip((duration - 0.05 - t) / 0.9, 0, 1)[:, None] ** 1.6             # silent by the last frame
    mix *= np.minimum(1, t / 0.02)[:, None]
    write(path, _f(mix, "high", 30), -1.0)
    return cta_g

def make_whoosh(path, d=0.55, seed=3):
    rng = np.random.default_rng(seed); t = T(d); u = t / d
    n = np.stack([rng.standard_normal(len(t)) for _ in range(2)], 1)
    out = np.zeros_like(n); blk = 256
    for c in range(2):
        zi = None
        for i in range(0, len(t), blk):
            fc = 5500 * (500 / 5500) ** u[i]                  # sweeps down as it passes
            sos = butter(2, [fc / 1.6, min(fc * 1.6, 20000)], btype="band", fs=SR, output="sos")
            if zi is None: zi = np.zeros((sos.shape[0], 2))
            out[i:i + blk, c], zi = sosfilt(sos, n[i:i + blk, c], zi=zi)
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.5 * (1 - 0.3 * u)
    out *= env[:, None]; out[:, 1] = np.roll(out[:, 1], int(0.006 * SR))
    write(path, out, -3.0)

if __name__ == "__main__":
    import sys
    make_whoosh(sys.argv[1] if len(sys.argv) > 1 else "whoosh.wav")
