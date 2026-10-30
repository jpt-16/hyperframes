"""The pitch, the ground ball and the throws for "The hit-and-run".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Play time t = 0 is when the pitch reaches the plate area (the
catcher's glove on a miss); contact is a hair earlier.

The pitch: a right-hander's 92 mph fastball, middle-away to a right-handed hitter (gravity + drag + spin lift, aimed by
iteration). The ground ball: from the contact point, 92 mph at -4 deg, 15 deg toward right field (to the right side,
behind the runner), gravity + drag + topspin, bouncing (it keeps 45% of its vertical speed and 85% of its speed along
the ground each hop). It passes through where the second baseman stood before he left to cover second.
The right fielder reacts 0.3 s after contact, runs 26 ft/s to the first point he can reach, and throws it in to second.
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
    Z = {"half_w": round((17 / 2 + 1.45) / 12, 3), "bot": 1.6, "top": 3.4, "z": PLATE_FRONT}
    out = {"fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "zone": Z, "pitches": {},
           "seats": {"gap": 3, "y0": 8.5, "rise": 0.5, "depth": 110}}
    FB = dict(mph=92, rpm=2300, eff=0.9, push=(-0.2, 1, 0))
    T, P, _ = pitch(FB["mph"], FB["rpm"], FB["eff"], FB["push"], (0.45, 2.45))
    tc, pc = at_z(T, P, -1.7)
    out["pitches"]["fb"] = dict(mph=92, flight=round(float(T[-1]), 3), t_contact=round(float(tc - T[-1]), 4), contact=pc.round(3).tolist(), path=samples(T, P, -float(T[-1])))
    print(f"pitch: flight {T[-1]:.3f} s, contact {tc - T[-1]:+.3f} s at {pc.round(2)}")
    def grounder(p0, v0, rpm=1800, dt=0.0005, tmax=6.0):
        """Flight with drag + topspin, hops off the dirt (45% of the vertical speed, 85% along the ground), then a roll
        on the grass once the hops die out (6 ft/s^2 of rolling resistance plus drag)."""
        p, v, t = np.array(p0, float) * FT, np.array(v0, float) * FT, 0.0
        TT, PP, BB, rolling = [0.0], [p / FT], [], False
        while t < tmax:
            sp = np.linalg.norm(v)
            if rolling:
                h = v.copy(); h[1] = 0; hs = np.linalg.norm(h)
                if hs < 3 * FT: break
                a = -h / hs * (6 * FT + K * 0.36 * hs * hs); v = v + a * dt; v[1] = 0; p = p + v * dt; p[1] = 0.12 * FT
            else:
                vh = v / sp; d = np.array([0, 1, 0]) - vh * vh[1]; n = np.linalg.norm(d); d = d / n if n > 1e-9 else d
                a = -K * 0.36 * sp * v - K * cl(sp, rpm) * 0.5 * sp * sp * d + np.array([0, -9.80665, 0])
                v = v + a * dt; p = p + v * dt
                if p[1] / FT <= 0.12 and v[1] < 0:
                    v[1] = -0.45 * v[1]; v[[0, 2]] *= 0.85; p[1] = 0.12 * FT; BB.append((round(t, 4), (p / FT).round(2).tolist()))
                    if v[1] < 3 * FT: rolling = True; v[1] = 0
            t += dt; TT.append(t); PP.append(p / FT)
        return np.array(TT), np.array(PP), BB
    phi, th = np.radians(15), np.radians(-4)
    dv = np.array([np.sin(phi) * np.cos(th), np.sin(th), -np.cos(phi) * np.cos(th)])
    T2, P2, B = grounder(pc, dv * 92 * MPH / FT)
    RF0 = np.array([118.0, -262.0]); SPD = 26.0
    ti = None
    for i, t in enumerate(T2):
        q = P2[i]
        if t > 0.6 and np.hypot(q[0] - RF0[0], q[2] - RF0[1]) / SPD + 0.3 <= t and q[1] < 3.5: ti = i; break
    t_f = float(T2[ti]); pf = P2[ti]
    out["gb"] = dict(path=samples(T2[: ti + 1], P2[: ti + 1], 0.0), t_field=round(t_f, 3), field=pf.round(2).tolist(),
                     bounces=[[b[0], b[1]] for b in B if b[0] <= t_f])
    r = lambda x, z: float(np.hypot(x, z))
    k2b = int(np.argmax(np.hypot(P2[:, 0], P2[:, 2]) >= 116))
    print(f"ground ball: {len(B)} hops; passes 116 ft out at x {P2[k2b, 0]:.1f}, z {P2[k2b, 2]:.1f} (2B's spot was 26, -116) at {T2[k2b]:.2f} s; RF fields it at {t_f:.2f} s at ({pf[0]:.0f}, {pf[2]:.0f}), {r(pf[0], pf[2]):.0f} ft out")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
