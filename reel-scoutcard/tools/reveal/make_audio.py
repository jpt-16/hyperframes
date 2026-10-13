"""Original audio for reveal.html: opening rumble, two text thumps, and the music bed.

    python3 tools/reveal/make_audio.py

Everything here is synthesised from scratch (numpy + scipy, fixed seeds), so it is
ours to use. Replace assets/reveal/music/bed.wav with a licensed track at any time;
the composition only needs the file to start on the reveal impact (t = 3.0 s).

Bed: 120 BPM, D minor, one bar = 2.0 s, bar 1 starts at the impact, so every
bar line lands on a scene change (5, 7, 9, 11, 13, 15) and the brand reveal at
17.0 is the downbeat of bar 8. Drums drop out for the last bar before it.
"""
import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng = np.random.default_rng(2026)
BPM = 120; BEAT = 60 / BPM; BAR = 4 * BEAT
BED_LEN = 17.0                                  # 3.0 -> 20.0 in composition time
T = lambda d: np.arange(int(round(d * SR))) / SR

def sos(kind, f, order=2):
    return butter(order, f, btype=kind, fs=SR, output="sos")
def filt(x, kind, f, order=2): return sosfilt(sos(kind, f, order), x)
def hz(note):                                  # "D2" -> Hz
    names = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    n, o = note[:-1], int(note[-1]); return 440 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)
def saw(f, t, detune=0.0):
    ph = (f * 2 ** (detune / 1200)) * t + rng.random()
    return 2 * (ph % 1) - 1
def env_adsr(n, a, d, s, r, sustain_len):
    A, D, R = int(a * SR), int(d * SR), int(r * SR); S = max(sustain_len - A - D, 0)
    e = np.concatenate([np.linspace(0, 1, A, False), np.linspace(1, s, D, False), np.full(S, s), np.linspace(s, 0, R)])
    out = np.zeros(n); out[:min(n, len(e))] = e[:n]; return out
def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(round(t * SR)); j = min(len(buf), i + len(x))
    if j <= i: return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:j, 0] += x[:j - i] * gain * l * 1.414; buf[i:j, 1] += x[:j - i] * gain * r * 1.414
def reverb(x, secs=1.8, damp=6000, mix=0.25, seed=7):
    g = np.random.default_rng(seed); n = int(secs * SR); t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = g.standard_normal(n) * np.exp(-t * 6.9 / secs); ir = filt(ir, "low", damp); ir[: int(0.012 * SR)] = 0
        ir /= np.sqrt((ir ** 2).sum())
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x * (1 - mix) + out * mix * 1.6
def write(path, x, peak_db=-3.0):
    x = x / (np.max(np.abs(x)) + 1e-12) * 10 ** (peak_db / 20)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

# ---------------------------------------------------------------- opening rumble
def rumble(d=3.3):
    t = T(d); n = len(t)
    brown = np.cumsum(rng.standard_normal(n)); brown -= filt(brown, "low", 4)     # drift-free brown noise
    body = filt(brown, "low", 70, 4) / 60
    drone = np.sin(2 * np.pi * hz("D1") * t) * 0.6 + np.sin(2 * np.pi * hz("A1") * t + 1.3) * 0.3
    drone *= 1 + 0.18 * np.sin(2 * np.pi * 0.9 * t)                              # slow beating, not a wobble
    swell = np.clip(t / 2.9, 0, 1) ** 1.6 * np.where(t > 3.0, np.exp(-(t - 3.0) / 0.08), 1.0)
    x = (body + drone) * swell
    st = np.stack([x, x], 1); st[:, 1] = np.roll(st[:, 1], int(0.011 * SR))         # a little width
    return reverb(st, 1.2, 400, 0.2)

# ------------------------------------------------- text thumps (beat 1, beat 2)
def thump(f0, sharp):
    t = T(0.9)
    f = f0 * (1 + 1.6 * np.exp(-t / 0.018))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.22 if not sharp else 0.16))
    click = filt(rng.standard_normal(len(t)), "band", [1800, 6000]) * np.exp(-t / 0.004) * (0.25 if sharp else 0.08)
    x = body + click
    return reverb(np.stack([x, x], 1), 1.4, 1800, 0.18)

# -------------------------------------------------------------------- music bed
CHORDS = [  # one per bar from the impact: bar k spans comp 3+2k .. 5+2k
    ("D", ["D3", "F3", "A3", "D4"]), ("Bb", ["Bb2", "D3", "F3", "Bb3"]), ("F", ["F2", "A3", "C4", "F4"]),
    ("C", ["C3", "E3", "G3", "C4"]), ("D", ["D3", "F3", "A3", "E4"]), ("Bb", ["Bb2", "D3", "F3", "A3"]),
    ("A", ["A2", "C#4", "E4", "A4"]),                                  # bar 6, comp 15-17: dominant, drums drop at 16
    ("D", ["D3", "A3", "D4", "F4", "E4"])]                             # bar 7, comp 17.0: the reveal chord, rings out
BASS = {"D": "D2", "Bb": "Bb1", "F": "F2", "C": "C2", "G": "G1", "A": "A1"}

def kick():
    t = T(0.32); f = 46 + 90 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11) + filt(rng.standard_normal(len(t)), "high", 3000) * np.exp(-t / 0.003) * 0.15
def clap():
    t = T(0.35); n = filt(rng.standard_normal(len(t)), "band", [900, 3200])
    e = sum(np.exp(-np.clip(t - k, 0, None) / 0.008) * (t >= k) for k in (0, 0.011, 0.022)) + np.exp(-t / 0.09) * 0.6
    return n * e * 0.6
def hat(open_=False):
    t = T(0.25 if open_ else 0.06); n = filt(rng.standard_normal(len(t)), "high", 7500)
    return n * np.exp(-t / (0.06 if open_ else 0.012))
def pluck(f):
    t = T(0.45); x = saw(f, t) * 0.6 + np.sign(np.sin(2 * np.pi * f * t)) * 0.25
    cut = 600 + 4200 * np.exp(-t / 0.05)
    y = np.zeros_like(x); s = 0.0                                    # one-pole with a falling cutoff
    a = 1 - np.exp(-2 * np.pi * cut / SR)
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y * np.exp(-t / 0.16)

def bed():
    L = int(BED_LEN * SR); out = np.zeros((L, 2)); pad = np.zeros((L, 2)); drums = np.zeros((L, 2)); arp = np.zeros((L, 2))
    for b, (root, notes) in enumerate(CHORDS):
        t0 = b * BAR
        if t0 >= BED_LEN: break
        final = b == len(CHORDS) - 1
        dur = (BED_LEN - t0) if final else BAR
        # pad: three detuned saws per note, soft attack, dark
        tt = T(dur + (0 if final else 0.3))
        for nn in notes:
            v = sum(saw(hz(nn), tt, d) for d in (-7, 0, 7)) / 3
            v = filt(v, "low", 900 if not final else 1500, 2) * env_adsr(len(tt), 0.35 if b else 0.05, 0.4, 0.8, 0.3 if not final else 2.6, int((dur - 0.2) * SR) if not final else int(0.4 * SR))
            place(pad, v, t0, 0.10, rng.uniform(-0.5, 0.5))
        # sub bass: eighth-note pulses with a pumping envelope
        if b >= 0:
            fb = hz(BASS[root])
            steps = 1 if final else 8
            for k in range(steps):
                ts = t0 + k * BEAT / 2
                td = T(2.8 if final else BEAT / 2)
                v = np.sin(2 * np.pi * fb * td) + 0.25 * np.sin(2 * np.pi * 2 * fb * td)
                v *= np.minimum(1, td / 0.012) * (np.exp(-td / 1.2) if final else (1 - 0.65 * np.exp(-td / 0.09)) * np.exp(-td / 0.5))
                rel = int(0.018 * SR); v[-rel:] *= np.linspace(1, 0, rel) ** 2       # no click at the pulse end
                place(out, v, ts, 0.21 if b else 0.13 + 0.015 * k)
        # drums: enter bar 1 (comp 5.0); clap from bar 2; drop out for the second half of bar 6 (comp 16-17)
        for k in range(16):
            ts = t0 + k * BEAT / 4
            if final or b == 0: continue
            if b == 6 and k >= 8: continue                           # stillness before the reveal (comp 16.0-17.0)
            if k % 4 == 0: place(drums, kick(), ts, 0.55)
            if b >= 2 and k in (4, 12): place(drums, clap(), ts, 0.22, 0.05)
            vel = [1, .35, .6, .35][k % 4]
            place(drums, hat(open_=(k % 4 == 2 and b >= 3)), ts, 0.07 * vel, 0.3)
        # arp: sixteenths of chord tones an octave up, from bar 2
        if 2 <= b <= 6:                                              # half a bar in bar 6, then silence
            tones = [hz(n) * 2 for n in notes[1:4]]
            pattern = [0, 1, 2, 1, 2, 0, 1, 2]
            for k in range(16 if b < 6 else 8):
                place(arp, pluck(tones[pattern[k % 8]]), t0 + k * BEAT / 4, 0.045, -0.4 if k % 2 else 0.4)
    # final hit on the reveal downbeat (bed time 14.0 = comp 17.0): kick + low boom under the last chord
    place(drums, kick(), 14.0, 0.75)
    boom_t = T(2.6); boom = np.sin(2 * np.pi * np.cumsum(38 + 30 * np.exp(-boom_t / 0.05)) / SR) * np.exp(-boom_t / 0.7)
    place(out, boom, 14.0, 0.35)
    # swell into the reveal: filtered noise rising through the dropout (comp 16.0-17.0)
    sw_t = T(1.0); sw = filt(rng.standard_normal(len(sw_t)), "band", [2500, 9000]) * (sw_t / 1.0) ** 3
    place(out, sw, 13.0, 0.10)
    # delay on the arp (dotted eighth), reverb on everything tonal
    d = int(0.75 * BEAT * SR); arp_d = arp.copy()
    for k, g in enumerate([0.45, 0.22, 0.1], 1):
        arp_d[d * k:] += arp[: -d * k] * g * (np.array([1, 0.6]) if k % 2 else np.array([0.6, 1]))
    mix = reverb(pad + arp_d, 2.6, 5000, 0.35) + out + reverb(drums, 0.9, 7000, 0.12)
    # final tail: everything fades to silence by the last frame (bed 16.9 = comp 19.9)
    tt = np.arange(L) / SR
    mix *= np.clip((16.9 - tt) / 1.6, 0, 1)[:, None] ** 1.5
    mix = filt(mix.T, "high", 28).T
    return mix

if __name__ == "__main__":
    write("assets/reveal/sfx/rumble.wav", rumble())
    write("assets/reveal/sfx/thump-1.wav", thump(52, False))
    write("assets/reveal/sfx/thump-2.wav", thump(58, True))
    write("assets/reveal/music/bed.wav", bed(), -1.0)
    print("wrote rumble, thump-1, thump-2, bed")
