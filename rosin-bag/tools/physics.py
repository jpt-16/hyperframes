"""The pitches for "Why pitchers use the rosin bag".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Each path starts at release (t = 0 at release here).

A right-hander from the stretch, released 6.0 ft high, 1.9 ft to the arm side, 6.5 ft in front of the rubber.
Gravity, drag (Cd 0.35) and spin lift (Magnus), aimed by iteration at a spot as the ball crosses the front of the plate.
  fb  four-seam fastball  94 mph, 2,300 rpm backspin
  cb  curveball           79 mph, 2,600 rpm topspin, a little glove side
  ch  changeup            85 mph, 1,750 rpm, arm-side fade
  end the last pitch      95 mph four-seamer
"spin" is the ball's spin axis (unit vector, right-hand rule) and rate, so the seams turn the right way on screen.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
K = 0.5 * 1.19 * np.pi * 0.0366 ** 2 / 0.145
RELEASE = np.array([-1.9, 6.0, -54.0])
PLATE_FRONT = -17 / 12
GLOVE_Z = 2.0
HZ = 240

def cl(v, rpm):
    s = 0.0366 * rpm * 2 * np.pi / 60 / max(v, 1e-6)
    return 1.5 * s if s < 0.1 else 0.09 + 0.6 * s

def fly(p0, v0, rpm, eff, push, stop, cd=0.35, dt=0.0005):
    p, v, t = np.array(p0, float) * FT, np.array(v0, float) * FT, 0.0
    push = np.array(push, float); push /= np.linalg.norm(push)
    T, P = [0.0], [p / FT]
    while True:
        sp = np.linalg.norm(v); vh = v / sp
        d = push - vh * np.dot(push, vh); n = np.linalg.norm(d); d = d / n if n > 1e-9 else d
        a = -K * cd * sp * v + K * cl(sp, rpm) * eff * sp * sp * d + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        T.append(t); P.append(p / FT)
        if stop(p / FT, v / FT, t): return np.array(T), np.array(P)

def at_z(T, P, z):
    i = int(np.argmax(P[:, 2] >= z)); f = (z - P[i - 1, 2]) / (P[i, 2] - P[i - 1, 2])
    return float(T[i - 1] + f * (T[i] - T[i - 1])), P[i - 1] + f * (P[i] - P[i - 1])

def pitch(mph, rpm, eff, push, target):
    tx, ty = target
    yaw, pit = np.arctan2(tx - RELEASE[0], -RELEASE[2]), 0.0
    for _ in range(40):
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P = fly(RELEASE, d * mph * MPH / FT, rpm, eff, push, lambda p, v, t: p[2] >= GLOVE_Z or t > 1.2)
        _, p = at_z(T, P, PLATE_FRONT)
        yaw += (tx - p[0]) / 55 * 0.9; pit += (ty - p[1]) / 55 * 0.9
    return T, P, d

def samples(T, P, hz=HZ):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    return {"t0": 0.0, "hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(float(np.interp(x, T, P[:, k])), 3) for k in range(3)] for x in tt]}

def fence(phi):                             # 330 ft lines, 375 alleys, 400 center
    a = abs(phi)
    return 400 - 25 * (a / 22.5) ** 1.3 if a <= 22.5 else 375 - 45 * ((a - 22.5) / 22.5) ** 1.15

PITCHES = {   # mph, rpm, spin efficiency, lift direction, target (x, y) at the front of the plate
    "fb": (94, 2300, 0.9, (-0.2, 1, 0), (0.25, 2.7)),
    "cb": (79, 2600, 0.85, (0.35, -1, 0), (0.15, 1.7)),
    "ch": (85, 1750, 0.85, (-0.75, 0.5, 0), (-0.35, 1.9)),
    "end": (95, 2350, 0.9, (-0.2, 1, 0), (0.4, 2.6)),
}
if __name__ == "__main__":
    out = {"fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "pitches": {},
           "seats": {"gap": 3, "y0": 8.5, "rise": 0.5, "depth": 110}, "release": RELEASE.tolist()}
    for k, (mph, rpm, eff, push, tgt) in PITCHES.items():
        T, P, d = pitch(mph, rpm, eff, push, tgt)
        tf, pf = at_z(T, P, PLATE_FRONT)
        pu = np.array(push, float); pu /= np.linalg.norm(pu)
        axis = np.cross(d, pu); axis /= np.linalg.norm(axis)
        out["pitches"][k] = dict(mph=mph, rpm=rpm, flight=round(float(T[-1]), 3), front=round(tf, 3), cross=[round(float(x), 2) for x in pf],
                                 spin=[round(float(x), 4) for x in axis], path=samples(T, P))
        print(f"{k}: {mph} mph, {rpm} rpm: crosses the plate at ({pf[0]:+.2f}, {pf[1]:.2f}) after {tf:.3f} s; glove at {T[-1]:.3f} s, {P[-1].round(2)}")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
