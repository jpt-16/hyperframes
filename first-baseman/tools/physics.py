"""The home run for "First base is harder than it looks".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. t = 0 is contact.

The home run: the first baseman (a right-handed hitter) pulls a line drive to left-center, 106 mph off the bat at
24 degrees with backspin, flown with gravity + drag + spin lift (Magnus) in 0.5 ms steps (Cd 0.40, the same carry
model as the fly-ball video). It clears the 8 ft wall and lands in the seats. The throws to first base are worked
out in assets/field.js from the fielders' and the first baseman's 3D figures (gravity only, ~80-85 mph).
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
           "zone": {"half_w": round((17 / 2 + 1.45) / 12, 3), "bot": 1.6, "top": 3.4, "z": PLATE_FRONT}}
    CONTACT = np.array([0.6, 3.0, -2.0])
    phi, la, ev = np.radians(-19), np.radians(24), 106
    dv = np.array([np.sin(phi) * np.cos(la), np.sin(la), -np.cos(phi) * np.cos(la)])
    T, P, _ = fly(CONTACT, dv * ev * MPH / FT, 2200, 1.0, (0, 1, 0), lambda p, v, t: t > 7.0 or p[1] < 0 or np.hypot(p[0], p[2]) > 470, cd=0.40)
    r = np.hypot(P[:, 0], P[:, 2]); wall = fence(np.degrees(phi)); k = int(np.argmax(r >= wall))
    out["hr"] = dict(ev=ev, la=24, spray=-19, contact=CONTACT.tolist(), path=samples(T, P, 0.0), t_wall=round(float(T[k]), 3),
                     h_wall=round(float(P[k, 1]), 1), wall=round(float(wall), 1), dist=round(float(r[-1]), 1), apex=round(float(P[:, 1].max()), 1))
    print(f"home run: {ev} mph at 24 deg; passes the {wall:.0f} ft wall {P[k,1]:.0f} ft up at {T[k]:.2f} s; apex {P[:,1].max():.0f} ft; "
          f"reaches {r[-1]:.0f} ft (seats) at {T[-1]:.2f} s")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
