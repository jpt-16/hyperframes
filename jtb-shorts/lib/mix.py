"""Mix and master one video's audio offline, so what we measure is what ships.

mix():    music bed + every sound cue (+ a synthesised click per typed character)
master(): gain to the loudness target, then a 4x-oversampled peak limiter.
          With music off, the gain is still worked out on the full mix (bed + sounds),
          then applied to the sounds alone: the effects keep exactly the level they
          were designed to sit at under a -14 LUFS track, so a song added later in an
          editor at normal loudness lands in the right balance.
          loudnorm is only ever used to MEASURE. The limiter's workload is
          reported so a hot mix is visible instead of silently squashed.
"""
import json, os, subprocess, wave, numpy as np
from scipy.signal import resample_poly, butter, sosfilt
from audio import SR, write
from sfx import key_click

# where a cue's time sits inside each file: risers top out on the cue, whooshes peak on it
ANCHOR = {"riser-s": "end", "riser-m": "end", "riser-l": "end", "whoosh": "peak"}
LEVEL_DB = {"tap": -10.0, "popup": -7.0, "bubble": -9.0, "land": -3.0, "riser-s": -9.0, "riser-m": -8.0, "riser-l": -9.0, "whoosh": -8.0}
BED_DB = -2.0
KEY_DB = -12.0
TARGET_LUFS = -14.0
AAC_MAX_TP = -1.3       # the renderer turns the WHOLE track down 1.5 dB if its AAC encode passes -1 dBTP
CEILING = 0.78          # limiter ceiling (linear), about -2.2 dBFS: AAC encoding adds overshoot and the renderer
                        # pulls the whole track down 1.5 dB if the encoded file passes -1 dBTP

def read(path):
    w = wave.open(path); n = w.getnframes(); ch = w.getnchannels(); sw = w.getsampwidth()
    raw = w.readframes(n); w.close()
    x = np.frombuffer(raw, np.int16 if sw == 2 else np.int32).astype(np.float64) / (32768.0 if sw == 2 else 2 ** 31)
    x = x.reshape(-1, ch)
    return np.repeat(x, 2, 1) if ch == 1 else x

def db(g): return 10 ** (g / 20)

def _raw_write(path, st):
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

def mix(out_path, D, bed_path, cues, keys, sfx_dir, fx_path=None):
    L = int(round(D * SR))
    bed = read(bed_path)[:L]
    buf = np.zeros((L, 2)); buf[: len(bed)] = bed * db(BED_DB)
    fx = np.zeros((L, 2))
    cache, report = {}, []
    for name, t, gdb in cues:
        if name not in cache: cache[name] = read(f"{sfx_dir}/{name}.wav")
        x = cache[name]
        a = ANCHOR.get(name)
        if a == "end": start = t - len(x) / SR
        elif a == "peak": start = t - np.argmax(np.abs(x).sum(1)) / SR
        else: start = t
        i = int(round(start * SR)); j = min(L, i + len(x))
        if i < 0: x = x[-i:]; i = 0
        if j <= i: continue
        fx[i:j] += x[: j - i] * db(LEVEL_DB.get(name, -8.0) + gdb)
        report.append((name, round(t, 2), i, j))
    for t, gdb in keys:
        x = key_click(int(t * 1000)); i = int(round(t * SR)); j = min(L, i + len(x))
        if j > i: fx[i:j] += x[: j - i] * db(KEY_DB + gdb)
    out = buf + fx
    k = db(-1.0) / (np.max(np.abs(out)) + 1e-12)          # one scale for both files keeps them comparable
    _raw_write(out_path, out * k)
    if fx_path: _raw_write(fx_path, fx * k)
    return audibility(buf, fx, report)

def audibility(bed, fx, report):
    """Sound-to-music ratio inside each cue's own window, measured in the 1.5-8 kHz band where pops and air live."""
    sos = butter(2, [1500, 8000], btype="band", fs=SR, output="sos")
    bb, ff = sosfilt(sos, bed.mean(1)), sosfilt(sos, fx.mean(1))
    rows = []
    for name, t, i, j in report:
        e_f = np.sqrt(np.mean(ff[i:j] ** 2) + 1e-12); e_b = np.sqrt(np.mean(bb[i:j] ** 2) + 1e-12)
        rows.append((name, t, round(float(20 * np.log10(e_f / e_b)), 1)))
    return rows

def measure(path, pre=""):
    af = (pre + "," if pre else "") + "loudnorm=print_format=json"
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", af, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j = json.loads(err[err.rindex("{"): err.rindex("}") + 1])
    return float(j["input_i"]), float(j["input_tp"])

def master(pre_path, out_path, target=TARGET_LUFS, fx_path=None):
    """fx_path: master the full mix to find the gain, then ship the sounds-only file at that same gain."""
    full_out = out_path + ".full.wav" if fx_path else out_path
    out_path, final = full_out, out_path
    I0, _ = measure(pre_path)
    g = target - I0
    for _ in range(4):
        af = f"volume={g:.2f}dB,aresample=192000,alimiter=limit={CEILING}:attack=4:release=80:level=disabled,aresample=48000"
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", pre_path, "-af", af, "-ac", "2", "-ar", "48000",
                        "-c:a", "pcm_s16le", out_path], check=True)
        I, tp = measure(out_path)
        if abs(I - target) <= 0.3: break
        g += target - I
    fx_stats = None
    if fx_path:
        af = f"volume={g:.2f}dB,aresample=192000,alimiter=limit={CEILING}:attack=4:release=80:level=disabled,aresample=48000"
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", fx_path, "-af", af, "-ac", "2", "-ar", "48000",
                        "-c:a", "pcm_s16le", final], check=True)
        os.remove(out_path); out_path = final
        fx_stats = measure(final)
    fixes = codec_safe(out_path)
    # limiter workload: how much of the programme sits above the ceiling before limiting (4x oversampled)
    x = read(pre_path).mean(1) * db(g)
    up = np.abs(resample_poly(x, 4, 1))
    blk = int(0.01 * SR * 4); nb = len(up) // blk
    peaks = up[: nb * blk].reshape(nb, blk).max(1)
    over = peaks > CEILING
    if fx_stats: I, tp = fx_stats
    return dict(lufs=round(I, 1), true_peak=round(tp, 1), aac_dips=fixes, gain_db=round(g, 1), music=fx_path is None,
                limited_pct=round(100 * over.mean(), 1),
                max_reduction_db=round(max(0.0, 20 * np.log10(peaks.max() / CEILING)), 1))

def _decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)

def codec_safe(path, rounds=4):
    """AAC can overshoot a sharp transient by 2-3 dB in a single frame. Encode a test AAC, find any 10 ms window
    over AAC_MAX_TP, and dip just that spot (20 ms ramps) by the overshoot, so the renderer never turns the whole track down.
    Returns [(time, dB), ...] of the dips made."""
    dips = []
    for _ in range(rounds):
        tmp = path + ".test.m4a"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-c:a", "aac", "-b:a", "192k", tmp], check=True)
        y = _decode(tmp); os.remove(tmp)
        x = read(path); n = min(len(x), len(y))
        up = np.abs(resample_poly(y[:n], 4, 1, axis=0)).max(1)
        blk = int(0.01 * SR); nb = n // blk
        pk = up[: nb * blk * 4].reshape(nb, blk * 4).max(1)
        over = np.where(20 * np.log10(pk + 1e-12) > AAC_MAX_TP)[0]
        if not len(over): break
        g = np.ones(len(x)); ramp = int(0.02 * SR)
        for k in over:
            cut = AAC_MAX_TP - 20 * np.log10(pk[k]) - 0.3
            a, b = k * blk, (k + 1) * blk
            env = np.ones(len(x))
            env[a:b] = db(cut)
            lo = max(0, a - ramp); env[lo:a] = np.linspace(1, db(cut), a - lo)
            hi = min(len(x), b + ramp); env[b:hi] = np.linspace(db(cut), 1, hi - b)
            g = np.minimum(g, env)
            dips.append((round(k * 0.01, 2), round(cut, 1)))
        st = x * g[:, None]
        w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    return dips
