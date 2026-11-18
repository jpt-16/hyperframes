"""The pitches and batted balls for "What if an MLB hitter stopped swinging for 3 months?".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Each pitch path starts at release (t = 0).

Three throwers, one hitter:
- the game pitcher, from the mound (released 6.0 ft high, 54 ft from the plate): 96 and 98 mph fastballs, and a 94 mph
  fastball that gets hit for a home run;
- a pitcher throwing live in the batting cage (flat floor, so released 5.2 ft high): a 93 mph fastball and an 85 mph slider;
- a coach throwing batting practice from behind an L-screen 44 ft away: a 60 mph fastball, a 50 mph curve and a 52 mph
  change.
Gravity, drag (Cd 0.35) and spin lift (Magnus), aimed by iteration at a spot as the ball crosses the front of the plate.
Each pitch also has a contact point (where it is at the hitter's contact depth); the swing in field.js is placed so the
bat would meet it there. In the cage, a pitch nobody hits carries on into the back net.

Batted balls leave the contact point at an exit speed (mph), launch angle and spray angle (0 = straight to center,
positive toward right field) with backspin lift and drag (Cd 0.40). In the cage they hit the nets: a net takes almost all
of the ball's speed, and the ball drops, bounces on the turf and rolls.
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

def fly(p0, v0, rpm, eff, push, stop, cd=0.35, dt=0.0005, bounce=False):
    p, v, t = np.array(p0, float) * FT, np.array(v0, float) * FT, 0.0
    push = np.array(push, float); push /= np.linalg.norm(push)
    T, P = [0.0], [p / FT]
    rolling = False
    while True:
        sp = np.linalg.norm(v); vh = v / max(sp, 1e-9)
        if rolling:
            a = -vh * 0.35 * 9.80665; a[1] = 0
        else:
            d = push - vh * np.dot(push, vh); n = np.linalg.norm(d); d = d / n if n > 1e-9 else d
            a = -K * cd * sp * v + K * cl(sp, rpm) * eff * sp * sp * d + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        if bounce and p[1] < 0.121 * FT and v[1] < 0:
            p[1] = 0.121 * FT
            if abs(v[1]) < 1.2: v[1] = 0; rolling = True
            else: v[1] = -v[1] * 0.45; v[0] *= 0.75; v[2] *= 0.75; rpm *= 0.3
        T.append(t); P.append(p / FT)
        if stop(p / FT, v / FT, t): return np.array(T), np.array(P)

def at_z(T, P, z):
    i = int(np.argmax(P[:, 2] >= z)); f = (z - P[i - 1, 2]) / (P[i, 2] - P[i - 1, 2])
    return float(T[i - 1] + f * (T[i] - T[i - 1])), P[i - 1] + f * (P[i] - P[i - 1])

def pitch(mph, rpm, eff, push, target, rel=RELEASE, endz=GLOVE_Z):
    tx, ty = target; rel = np.array(rel, float)
    yaw, pit = np.arctan2(tx - rel[0], -rel[2]), 0.0
    for _ in range(40):
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P = fly(rel, d * mph * MPH / FT, rpm, eff, push, lambda p, v, t: p[2] >= endz or p[1] < 0.15 or t > 2.0)
        _, p = at_z(T, P, PLATE_FRONT)
        yaw += (tx - p[0]) / 55 * 0.9; pit += (ty - p[1]) / 55 * 0.9
    return T, P, d

def batted(p0, ev, la, spray, dur, rpm=2000):
    la, sp = np.radians(la), np.radians(spray)
    d = np.array([np.sin(sp) * np.cos(la), np.sin(la), -np.cos(sp) * np.cos(la)])
    side = np.cross(d, [0, 1, 0]); side /= np.linalg.norm(side)
    lift = np.cross(side, d)                            # backspin lifts the ball (topspin on a grounder pushes it down)
    if la < 0: lift = -lift
    return fly(p0, d * ev * MPH / FT, rpm, 0.6, lift, lambda p, v, t: t > dur, cd=0.40, bounce=True)

def fence(phi):                             # 330 ft lines, 375 alleys, 400 center
    a = abs(phi)
    return 400 - 25 * (a / 22.5) ** 1.3 if a <= 22.5 else 375 - 45 * ((a - 22.5) / 22.5) ** 1.15

def samples(T, P, hz=HZ):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    return {"t0": 0.0, "hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(float(np.interp(x, T, P[:, k])), 3) for k in range(3)] for x in tt]}

CAGE = dict(x0=-8.5, x1=7.5, y1=13.0, z0=-72.0, z1=9.0)              # the tunnel's nets (floor at y = 0)
def cage_fly(p0, v0, rpm, push, dur, cd=0.40, dt=0.0005):
    """A ball in the cage: flight, then nets that soak up its speed, then the turf (bounce and roll)."""
    p, v, t = np.array(p0, float) * FT, np.array(v0, float) * FT, 0.0
    push = np.array(push, float); push /= np.linalg.norm(push); T, P = [0.0], [p / FT]; rolling = False
    while t < dur:
        sp = np.linalg.norm(v); vh = v / max(sp, 1e-9)
        if rolling: a = -vh * 0.5 * 9.80665; a[1] = 0
        else:
            d = push - vh * np.dot(push, vh); n = np.linalg.norm(d); d = d / n if n > 1e-9 else d
            a = -K * cd * sp * v + K * cl(sp, rpm) * 0.5 * sp * sp * d + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        q = p / FT
        for ax, lo, hi in [(0, CAGE["x0"] + 0.15, CAGE["x1"] - 0.15), (2, CAGE["z0"] + 0.15, CAGE["z1"] - 0.15)]:
            if q[ax] < lo or q[ax] > hi:
                q[ax] = min(max(q[ax], lo), hi); v[ax] = -v[ax] * 0.08; v[[i for i in range(3) if i != ax]] *= 0.25; rpm *= 0.2
        if q[1] > CAGE["y1"] - 0.15: q[1] = CAGE["y1"] - 0.15; v[1] = -abs(v[1]) * 0.08; v[0] *= 0.3; v[2] *= 0.3
        if q[1] < 0.121 and v[1] < 0:
            q[1] = 0.121
            if abs(v[1]) < 1.0: v[1] = 0; rolling = True
            else: v[1] = -v[1] * 0.4; v[0] *= 0.7; v[2] *= 0.7
        p = q * FT; T.append(t); P.append(q.copy())
    return np.array(T), np.array(P)

def batted_dir(ev, la, spray):
    la, sp = np.radians(la), np.radians(spray)
    d = np.array([np.sin(sp) * np.cos(la), np.sin(la), -np.cos(sp) * np.cos(la)])
    side = np.cross(d, [0, 1, 0]); side /= np.linalg.norm(side)
    return d * ev * MPH / FT, np.cross(side, d) * (1 if la >= 0 else -1)

R_GAME, R_CAGE, R_BP = RELEASE, np.array([-1.9, 5.2, -54.0]), np.array([-1.1, 5.6, -42.0])
PITCHES = {   # mph, rpm, spin efficiency, lift direction, target (x, y) at the front of the plate, release, contact depth z, in the cage?
    "g96": (96, 2350, 0.9, (-0.2, 1, 0), (0.45, 2.75), R_GAME, PLATE_FRONT - 1.2, False),     # the hook: taken for a strike
    "g98": (98, 2450, 0.9, (-0.2, 1, 0), (0.15, 2.6), R_GAME, PLATE_FRONT - 1.2, False),      # the first game back
    "ghr": (94, 2300, 0.9, (-0.2, 1, 0), (-0.05, 2.55), R_GAME, PLATE_FRONT - 1.3, False),    # the swing that gets it back
    "cfb": (93, 2300, 0.9, (-0.2, 1, 0), (0.25, 2.65), R_CAGE, PLATE_FRONT - 1.2, True),      # live in the cage: a fastball he watches
    "csl": (85, 2500, 0.45, (0.95, 0.25, 0), (0.95, 1.55), R_CAGE, PLATE_FRONT - 1.2, True),  # ... and a slider down and away
    "bfb": (60, 1500, 0.8, (-0.2, 1, 0), (0.1, 2.55), R_BP, PLATE_FRONT - 1.2, True),         # batting practice: fastball
    "bcb": (50, 1900, 0.85, (0.15, -1, 0), (0.25, 1.75), R_BP, PLATE_FRONT - 1.2, True),       # curve: drops
    "bch": (52, 1100, 0.6, (-0.6, 0.6, 0), (0.2, 2.15), R_BP, PLATE_FRONT - 1.2, True),       # change: slower, fades a little
}
HITS = {   # pitch, exit mph, launch angle, spray angle, seconds to keep, in the cage?
    "k1": ("bfb", 94, 11, 4, 1.6, True), "k2": ("bfb", 96, 15, -12, 1.6, True),            # week 1: line drives into the net
    "kf": ("bfb", 58, 32, 172, 1.5, True),                                                 # a month: late, fouled back into the net
    "kp": ("bch", 72, 6, -55, 1.6, True),                                                  # out in front of the change: pulled foul

    "k3": ("bfb", 90, 14, 20, 1.6, True), "k4": ("bfb", 97, 13, -3, 1.6, True),             # back in the cage: getting it back
    "hr": ("ghr", 110, 29, -17, 5.6, False),                                               # the swing that's on time
}
OFF = {"kf": 0.012, "kp": -0.035}                                                          # contact this much late (+) or early (-): the ball is met further back or further out front
if __name__ == "__main__":
    out = {"pitches": {}, "hits": {}, "release": RELEASE.tolist(), "plate_front": PLATE_FRONT, "cage": CAGE,
           "fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "seats": {"gap": 3, "y0": 8.5, "rise": 0.5, "depth": 110}}
    for k, (mph, rpm, eff, push, tgt, rel, cz, cage) in PITCHES.items():
        T, P, d = pitch(mph, rpm, eff, push, tgt, rel)
        tf, pf = at_z(T, P, PLATE_FRONT); tc, pc = at_z(T, P, cz)
        if cage:                                                       # nobody catches it: on into the back net
            vend = (P[-1] - P[-2]) / (T[-1] - T[-2])
            T2, P2 = cage_fly(P[-1], vend, rpm * 0.8, push, 1.2)
            T = np.concatenate([T, T[-1] + T2[1:]]); P = np.concatenate([P, P2[1:]])
        pu = np.array(push, float); pu /= np.linalg.norm(pu); axis = np.cross(d, pu); axis /= np.linalg.norm(axis)
        out["pitches"][k] = dict(mph=mph, rpm=rpm, flight=round(float(T[-1]), 3), front=round(tf, 3), cross=[round(float(x), 2) for x in pf],
                                 t_contact=round(tc, 4), contact=[round(float(x), 3) for x in pc], spin=[round(float(x), 4) for x in axis],
                                 release=[round(float(x), 2) for x in rel], path=samples(T, P))
        print(f"{k}: {mph} mph: crosses ({pf[0]:+.2f}, {pf[1]:.2f}) at {tf:.3f} s; contact {pc.round(2)} at {tc:.3f} s")
    for k, (pk, ev, la, spray, dur, cage) in HITS.items():
        pp = out["pitches"][pk]; off = OFF.get(k, 0.0); tq = pp["t_contact"] + off
        pts = np.array(pp["path"]["p"]); i = tq * pp["path"]["hz"]; i0 = int(i); p0 = pts[i0] + (pts[i0 + 1] - pts[i0]) * (i - i0)
        v0, lift = batted_dir(ev, la, spray)
        if cage: T, P = cage_fly(p0, v0, 2000, lift, dur)
        else: T, P = fly(p0, v0, 2000, 0.6, lift, lambda p, v, t: t > dur, cd=0.40, bounce=True)
        out["hits"][k] = dict(pitch=pk, ev=ev, la=la, spray=spray, off=off, p0=[round(float(x), 3) for x in p0], path=samples(T, P, 120))
        print(f"  {k}: {ev} mph at {la} deg, spray {spray}: after {T[-1]:.1f} s at {P[-1].round(1)}; max height {P[:, 1].max():.0f}")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
