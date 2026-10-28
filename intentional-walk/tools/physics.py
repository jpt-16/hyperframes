"""The pitches and the grand slam for "Intentional walk: smart strategy or big mistake?".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. For a pitch, t = 0 is when it reaches the catcher's glove.

Pitches (right-handed pitcher, 6.5 ft extension): gravity + drag + spin lift (Magnus), 0.5 ms steps, aimed by iteration
at a spot as the ball crosses the front of the plate. The hitter is right-handed (third-base side), so "away" is +x.

    slam    the 2024 NLCS Game 2 pitch, as reported: a 95 mph four-seam fastball from a right-hander (Landon Knack) to a
            right-handed hitter (Mark Vientos). The location here is illustrative (out over the plate, middle-away).
    final   the closing freeze (the pitcher is frozen before he lets go; the path is only used for timing).

The intentional walk (play time 0 = the manager's signal; feet and seconds), written to play.json "ibb":
    the batter drops the bat at 0.8 s and jogs (10 ft/s) from the box, across the front of the plate, up the line to
    first; the next hitter leaves the on-deck circle 1.5 s after the batter reaches first and walks (5 ft/s) to the box; the pitcher's next pitch.

The home run (from the contact point, gravity + drag + backspin): hit the other way, over the right-center wall
(22 deg toward right field, 375 ft fence), with the exit speed solved so it would carry 391 ft to field level, the
Statcast projected distance MLB.com reported. The exit speed and angle were not published with it, so they are a
plausible pair, not the real ones, and the video shows neither. The ball stops where it meets the outfield seats.
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

def seats(r, phi):                           # the outfield seats: 3 ft behind the wall, rising 0.5 ft per ft
    r0 = fence(np.degrees(phi)) + 3
    return 8.5 + 0.5 * (r - r0) if r >= r0 else None

if __name__ == "__main__":
    Z = {"half_w": round((17 / 2 + 1.45) / 12, 3), "bot": 1.6, "top": 3.4, "z": PLATE_FRONT}
    out = {"fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "zone": Z, "pitches": {}, "seats": {"gap": 3, "y0": 8.5, "rise": 0.5, "depth": 110}}
    FB = dict(mph=95, rpm=2300, eff=0.9, push=(-0.2, 1, 0))
    for name, (sp, tx, ty, cz) in {"slam": (FB, 0.45, 2.55, -0.9), "final": (FB, 0.15, 2.5, -2.0)}.items():
        T, P, _ = pitch(sp["mph"], sp["rpm"], sp["eff"], sp["push"], (tx, ty))
        tf, pf = at_z(T, P, PLATE_FRONT); tc, pc = at_z(T, P, cz)
        strike = abs(pf[0]) <= Z["half_w"] and Z["bot"] <= pf[1] <= Z["top"]
        out["pitches"][name] = dict(mph=sp["mph"], at_plate=pf.round(3).tolist(), strike=bool(strike), flight=round(float(T[-1]), 3),
                                    t_contact=round(float(tc - T[-1]), 4), contact=pc.round(3).tolist(), path=samples(T, P, -float(T[-1])))
        print(f"{name:6s} {sp['mph']} mph  crosses x {pf[0]:+.2f} y {pf[1]:.2f}  {'STRIKE' if strike else 'ball'}  contact {tc - T[-1]:+.3f} s")
    C = np.array(out["pitches"]["slam"]["contact"]); phi, th = np.radians(22), np.radians(27)
    dv = np.array([np.sin(phi) * np.cos(th), np.sin(th), -np.cos(phi) * np.cos(th)])
    def carry(ev):                           # where it would come down at field level
        T, P, _ = fly(C, dv * ev * MPH / FT, 2300, 1.0, (0, 1, 0), lambda p, v, t: p[1] <= 0 and v[1] < 0, cd=0.36)
        return float(np.hypot(P[-1, 0], P[-1, 2])), T, P
    lo, hi = 85.0, 120.0
    for _ in range(40):
        ev = (lo + hi) / 2; d, _, _ = carry(ev); lo, hi = (ev, hi) if d < 391 else (lo, ev)
    d, T, P = carry(ev)
    r = np.hypot(P[:, 0], P[:, 2]); fr = fence(22)
    k = int(np.argmax(r >= fr)); y_wall = float(P[k, 1])
    hit = [i for i in range(len(r)) if (s_ := seats(r[i], phi)) is not None and P[i, 1] <= s_]
    j = hit[0]; T, P = T[: j + 1], P[: j + 1]
    out["hits"] = {"slam": dict(ev=round(ev, 1), la=27, spray=22, path=samples(T, P, 0.0), land=P[-1].round(2).tolist(), t_land=round(float(T[-1]), 3),
                                t_wall=round(float(T[k]), 3), carry=round(d, 1))}
    print(f"slam: {ev:.1f} mph at 27 deg -> carries {d:.0f} ft; {y_wall:.1f} ft high at the {fr:.0f} ft wall (t {T[k]:.2f} s); lands in the seats {np.hypot(P[-1,0],P[-1,2]):.0f} ft out, {P[-1,1]:.1f} ft up at {T[-1]:.2f} s")
    def poly(pts):
        pts = np.array(pts, float); return pts.round(2).tolist(), float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
    walkR, LR = poly([[-3.0, 0, -0.9], [2.4, 0, -3.2], [63.0, 0, -63.0]])            # a right-handed hitter's box to the bag
    walkL, LL = poly([[3.0, 0, -0.9], [3.6, 0, -3.6], [63.0, 0, -63.0]])             # a left-handed hitter's
    OD = [33.0, 0, 5.0]; toBox, LB = poly([OD, [6.0, 0, 1.0], [-3.0, 0, -0.9]])
    T_WALK, JOG, NB = 1.0, 10.0, 5.0
    T_NB = round(T_WALK + LR / JOG + 1.5, 3)                                       # he leaves the circle once the walk is done
    T_BOX = T_NB + LB / NB
    out["ibb"] = dict(T_DROP=0.8, T_WALK=T_WALK, jog=JOG, walkR=walkR, walkL=walkL, T_ARR=round(T_WALK + LR / JOG, 3), T_ARR_L=round(T_WALK + LL / JOG, 3),
                      OD=OD, toBox=toBox, T_NB=T_NB, nb=NB, T_BOX=round(T_BOX, 3), T_PG=round(T_BOX + 3.0, 3))
    print("ibb:", {k: v for k, v in out["ibb"].items() if k.startswith("T")})
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
