"""The pitches for "Why every team wants a lefty".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. t = 0 is when the pitch reaches the catcher's glove.

A right-handed pitcher's pitches (6.5 ft extension, release 1.9 ft to the third-base side of the rubber's center),
flown with gravity + drag + spin lift (Magnus), 0.5 ms steps, aimed by iteration at a spot as the ball crosses the
front of the plate:
    fb_r   93 mph four-seam fastball, belt high over the middle
    sl_r   85 mph slider, glove-side break, low and away from a right-handed hitter (off the plate)
    ch_r   85 mph changeup, arm-side fade, down;  cu_r  79 mph curveball, topspin, down
           (the changeup and curve are only drawn as faint paths: "what hitters see most")
The left-hander's pitches are the same pitches mirrored across the plate-to-mound line (fb_l, sl_l): same speed,
same spin, same break, released from the first-base side. The video compares the ANGLE, never claims a lefty
throws harder or moves the ball more. The lefty's slider crosses low and away from a left-handed hitter, and at the
back foot of a right-handed hitter: one path, two very different looks.
Strike zone shown: 17 in wide plate plus the ball's radius each side; 1.6-3.4 ft high (a typical hitter's zone).
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
K = 0.5 * 1.19 * np.pi * 0.0366 ** 2 / 0.145
RELEASE = np.array([-1.9, 6.0, -54.0])
PLATE_FRONT = -17 / 12
GLOVE_Z = 2.0
HZ = 120

def cl(v, rpm):
    s = 0.0366 * rpm * 2 * np.pi / 60 / max(v, 1e-6)
    return 1.5 * s if s < 0.1 else 0.09 + 0.6 * s

def fly(p0, v0, rpm, eff, push, stop, cd=0.35, dt=0.0005, bounce=None):
    p, v, t = np.array(p0, float) * FT, np.array(v0, float) * FT, 0.0
    push = np.array(push, float); push /= np.linalg.norm(push)
    T, P, B = [0.0], [p / FT], []
    while True:
        sp = np.linalg.norm(v); vh = v / sp
        d = push - vh * np.dot(push, vh); n = np.linalg.norm(d); d = d / n if n > 1e-9 else d
        a = -K * cd * sp * v + K * cl(sp, rpm) * eff * sp * sp * d + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        if bounce and p[1] / FT <= 0.12 and v[1] < 0:
            e, mu = bounce; v[1] = -e * v[1]; v[[0, 2]] *= mu; p[1] = 0.12 * FT; B.append((round(t, 4), (p / FT).round(2).tolist())); rpm *= 0.4
        T.append(t); P.append(p / FT)
        if stop(p / FT, v / FT, t): return np.array(T), np.array(P), B

def at_z(T, P, z):
    i = int(np.argmax(P[:, 2] >= z)); f = (z - P[i - 1, 2]) / (P[i, 2] - P[i - 1, 2])
    return float(T[i - 1] + f * (T[i] - T[i - 1])), P[i - 1] + f * (P[i] - P[i - 1])

def pitch(mph, rpm, eff, push, target, end_z=GLOVE_Z, bounce=None):
    tx, ty = target
    yaw, pit = np.arctan2(tx - RELEASE[0], -RELEASE[2]), 0.0
    for _ in range(40):
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P, B = fly(RELEASE, d * mph * MPH / FT, rpm, eff, push, lambda p, v, t: p[2] >= end_z or t > 1.2, bounce=bounce)
        if bounce:   # aim where it first hits the dirt
            if not B: pit -= 0.01; continue
            bx, bz = B[0][1][0], B[0][1][2]; yaw += (tx - bx) / 55 * 0.9; pit += (ty - bz) / 55 * 0.3 * -0.06
            continue
        _, p = at_z(T, P, PLATE_FRONT)
        yaw += (tx - p[0]) / 55 * 0.9; pit += (ty - p[1]) / 55 * 0.9
    return T, P, B

def samples(T, P, t0, hz=HZ):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    return {"t0": round(float(t0), 4), "hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(float(np.interp(x, T, P[:, k])), 3) for k in range(3)] for x in tt]}

def sprint(t, vmax=27.0, tau=0.8):
    t = np.maximum(t, 0); return vmax * (t - tau * (1 - np.exp(-t / tau)))

B1, B2 = np.array([63.64, 0, -63.64]), np.array([0.0, 0, -127.28])
def fence(phi):                             # 330 ft lines, 375 alleys, 400 center
    a = abs(phi)
    return 400 - 25 * (a / 22.5) ** 1.3 if a <= 22.5 else 375 - 45 * ((a - 22.5) / 22.5) ** 1.15

if __name__ == "__main__":
    out = {"fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)],
           "zone": {"half_w": round((17 / 2 + 1.45) / 12, 3), "bot": 1.6, "top": 3.4, "z": PLATE_FRONT}, "pitches": {}}
    specs = {
        "fb_r": dict(mph=93, rpm=2300, eff=0.9, push=(-0.2, 1, 0), target=(0.25, 2.6)),
        "sl_r": dict(mph=85, rpm=2500, eff=0.45, push=(1.0, -0.5, 0), target=(1.25, 0.95)),
        "ch_r": dict(mph=85, rpm=1750, eff=0.85, push=(-1.0, 0.45, 0), target=(-0.55, 1.9)),
        "cu_r": dict(mph=79, rpm=2600, eff=0.75, push=(0.35, -1, 0), target=(0.45, 1.45)),
    }
    for name, sp in specs.items():
        T, P, _ = pitch(sp["mph"], sp["rpm"], sp["eff"], sp["push"], sp["target"])
        tf, pf = at_z(T, P, PLATE_FRONT)
        out["pitches"][name] = dict(mph=sp["mph"], at_plate=pf.round(3).tolist(), flight=round(float(T[-1]), 3), path=samples(T, P, -float(T[-1])))
        Pm = P * np.array([-1, 1, 1])                                   # the left-hander: the same pitch, mirrored
        out["pitches"][name[:-1] + "l"] = dict(mph=sp["mph"], at_plate=(pf * np.array([-1, 1, 1])).round(3).tolist(), flight=round(float(T[-1]), 3), path=samples(T, Pm, -float(T[-1])))
        print(f"{name}: {sp['mph']} mph, crosses the front of the plate at x {pf[0]:+.2f} ft, y {pf[1]:.2f} ft; flight {T[-1]:.2f} s  (mirrored for the lefty: x {-pf[0]:+.2f})")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
