"""The pitch and the pop-up for "The infield fly rule".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Play time t = 0 is contact.

The pitch: a right-hander's 93 mph fastball, in on a right-handed hitter's hands (gravity + drag + spin, aimed by
iteration). The pop-up: from the contact point, gravity + drag + backspin, 0.5 ms steps; launch speed and angle are
solved so it comes down on the infield dirt in front of the shortstop (about 104 ft out, 13 deg toward third) after a
4.6 s hang time, an ordinary infield pop-up. It then takes a short hop off the dirt (it keeps 35% of its vertical speed).
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
    FB = dict(mph=93, rpm=2300, eff=0.9, push=(-0.2, 1, 0))
    T, P, _ = pitch(FB["mph"], FB["rpm"], FB["eff"], FB["push"], (-0.55, 2.9))
    tc, pc = at_z(T, P, -1.6)
    out["pitches"]["pop"] = dict(mph=93, flight=round(float(T[-1]), 3), t_contact=round(float(tc - T[-1]), 4), contact=pc.round(3).tolist(), path=samples(T, P, -float(T[-1])))
    C = pc; target = np.array([-23.5, -101.5]); spray = np.arctan2(target[0] - C[0], -(target[1] - C[2]))
    def popup(ev, la):
        th = np.radians(la); dv = np.array([np.sin(spray) * np.cos(th), np.sin(th), -np.cos(spray) * np.cos(th)])
        return fly(C, dv * ev * MPH / FT, 2600, 1.0, (0, 1, 0), lambda p, v, t: p[1] <= 0.12 and v[1] < 0, cd=0.36)
    best = None
    for la in np.arange(60, 80, 0.5):                                    # angle for the hang time, speed for the distance
        lo, hi = 30.0, 120.0
        for _ in range(30):
            ev = (lo + hi) / 2; T2, P2, _ = popup(ev, la); d = np.hypot(P2[-1, 0] - C[0], P2[-1, 2] - C[2])
            lo, hi = (ev, hi) if d < np.hypot(target[0] - C[0], target[1] - C[2]) else (lo, ev)
        if best is None or abs(T2[-1] - 4.6) < abs(best[2][-1] - 4.6): best = (ev, la, T2, P2)
    ev, la, T2, P2 = best
    land = P2[-1].copy(); vy = (P2[-1, 1] - P2[-2, 1]) / (T2[-1] - T2[-2]); vh = (P2[-1] - P2[-2]) / (T2[-1] - T2[-2])
    hop_v = np.array([vh[0] * 0.35, -vy * 0.35, vh[2] * 0.35])           # the short hop off the dirt
    tt = np.arange(0, 0.45, 1 / HZ); hop = [(land + hop_v * x + np.array([0, -16.1 * x * x, 0])).round(3).tolist() for x in tt]
    hop = [[q[0], max(q[1], 0.12), q[2]] for q in hop]
    out["pop"] = dict(ev=round(ev, 1), la=la, t_land=round(float(T2[-1]), 3), apex=round(float(P2[:, 1].max()), 1), t_apex=round(float(T2[np.argmax(P2[:, 1])]), 3),
                      land=land.round(2).tolist(), path=samples(T2, P2, 0.0), hop=hop)
    print(f"pitch: contact at {tc - T[-1]:+.3f} s, {pc.round(2)}")
    print(f"pop-up: {ev:.1f} mph at {la} deg -> apex {P2[:, 1].max():.0f} ft at {T2[np.argmax(P2[:, 1])]:.2f} s, lands {np.hypot(land[0], land[2]):.0f} ft out at ({land[0]:.1f}, {land[2]:.1f}) after {T2[-1]:.2f} s")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
