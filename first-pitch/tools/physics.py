"""The pitches and batted balls for "Take the first pitch, or swing?".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. For a pitch, t = 0 is when it reaches the catcher's glove.

Pitches (right-handed pitcher, 6.5 ft extension): gravity + drag + spin lift (Magnus), 0.5 ms steps, aimed by iteration
at a spot as the ball crosses the front of the plate. The hitter is right-handed (third-base side), so "away" is +x.
Strike or ball is decided by where the ball crosses the front of the plate: the zone shown is the 17 in plate plus the
ball's radius on each side (|x| <= 0.83 ft) and 1.6-3.4 ft high (a typical hitter's zone). Every label in the video
comes from that test, so a ball is never drawn as a strike.

Batted balls (from the contact point out front, gravity + drag + spin, bounces that keep half their vertical speed):
    drive   103 mph at 14 deg into the left-center gap (a hard line drive; it lands and rolls, no home run)
    weak     62 mph at -14 deg, rolled over toward second base (topped: weak contact on a pitch off the edge)
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
    out = {"fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "zone": Z, "pitches": {}}
    FB = dict(mph=94, rpm=2300, eff=0.9, push=(-0.2, 1, 0)); SL = dict(mph=86, rpm=2500, eff=0.45, push=(1.0, -0.5, 0))
    CH = dict(mph=86, rpm=1750, eff=0.85, push=(-1.0, 0.45, 0)); CU = dict(mph=79, rpm=2600, eff=0.75, push=(0.35, -1, 0))
    specs = {   # name: (pitch, target x, target y)
        "hook": (FB, 0.15, 2.5), "final": (FB, 0.15, 2.5),
        "d1": (FB, 0.0, 2.6), "d2": (SL, 1.25, 0.95), "d3": (FB, -0.55, 3.2), "d4": (CH, -0.3, 1.25), "d5": (CU, 0.72, 1.75),
        "d6": (FB, 1.2, 2.5), "d7": (FB, 0.3, 1.95), "d8": (SL, 0.78, 2.15), "d9": (CH, -0.95, 1.9), "d10": (FB, -0.2, 3.0),
        "take": (FB, -0.42, 2.3), "chase": (SL, 1.3, 0.9), "mid": (FB, 0.05, 2.55), "edge": (FB, 0.8, 1.75), "off": (FB, 1.02, 1.7),
    }
    for name, (sp, tx, ty) in specs.items():
        T, P, _ = pitch(sp["mph"], sp["rpm"], sp["eff"], sp["push"], (tx, ty))
        tf, pf = at_z(T, P, PLATE_FRONT); tc, pc = at_z(T, P, -2.0)
        strike = abs(pf[0]) <= Z["half_w"] and Z["bot"] <= pf[1] <= Z["top"]
        out["pitches"][name] = dict(mph=sp["mph"], at_plate=pf.round(3).tolist(), strike=bool(strike), flight=round(float(T[-1]), 3),
                                    t_contact=round(float(tc - T[-1]), 4), contact=pc.round(3).tolist(), path=samples(T, P, -float(T[-1])))
        print(f"{name:6s} {sp['mph']} mph  crosses x {pf[0]:+.2f} y {pf[1]:.2f}  {'STRIKE' if strike else 'ball'}")
    d = [k for k in out["pitches"] if k.startswith("d")]
    print(f"first-pitch sample: {sum(out['pitches'][k]['strike'] for k in d)} strikes of {len(d)}")
    out["hits"] = {}
    for name, (pk, ev, la, spray, rpm) in {"drive": ("mid", 103, 14, -15, 2000), "weak": ("edge", 62, -14, 12, 1200)}.items():
        C = np.array(out["pitches"][pk]["contact"]); phi, th = np.radians(spray), np.radians(la)
        dv = np.array([np.sin(phi) * np.cos(th), np.sin(th), -np.cos(phi) * np.cos(th)])
        T, P, B = fly(C, dv * ev * MPH / FT, rpm, 1.0 if la > 0 else -0.6, (0, 1, 0), lambda p, v, t: t > 6.0 or (np.linalg.norm(v[[0, 2]]) < 4 and p[1] < 0.3), cd=0.40, bounce=(0.5, 0.75))
        out["hits"][name] = dict(ev=ev, la=la, spray=spray, path=samples(T, P, 0.0), land=(B[0][1] if B else P[-1].round(2).tolist()))
        print(f"{name}: {ev} mph at {la} deg -> first bounce {np.hypot(B[0][1][0], B[0][1][2]):.0f} ft from the plate at {B[0][0]:.2f} s" if B else name)
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
