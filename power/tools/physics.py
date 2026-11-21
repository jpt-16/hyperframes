"""The pitch and the two batted balls for "Why some hitters generate more power" (illustrative exit speeds; none are shown on screen).

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Each pitch path starts at release (t = 0).

A right-hander from the stretch, released 6.0 ft high, 1.9 ft to the arm side, 6.5 ft in front of the rubber.
Gravity, drag (Cd 0.35) and spin lift (Magnus), aimed by iteration at a spot as the ball crosses the front of the plate.
Each pitch also has a contact point: where the ball is when it reaches the hitter's contact depth (out in front of the
plate for a pitch inside, deeper for one away). The swing in field.js is placed so the bat meets the ball there.

Batted balls leave the contact point at a given exit speed (mph), launch angle and spray angle (0 = straight to center,
positive toward right field) with backspin lift and drag (Cd 0.40). Grounders bounce: each bounce keeps 45% of the
vertical speed and 75% of the horizontal speed, then the ball rolls with friction.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
K = 0.5 * 1.19 * np.pi * 0.0366 ** 2 / 0.145
RELEASE = np.array([-1.9, 6.0, -54.0])
_rel = os.path.join(HERE, "release.json")                  # where the rig's hand is at release (written from field.js)
if os.path.exists(_rel): RELEASE = np.array(json.load(open(_rel))["release"])
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

def pitch(mph, rpm, eff, push, target):
    tx, ty = target
    yaw, pit = np.arctan2(tx - RELEASE[0], -RELEASE[2]), 0.0
    for _ in range(40):
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P = fly(RELEASE, d * mph * MPH / FT, rpm, eff, push, lambda p, v, t: p[2] >= GLOVE_Z or t > 1.2)
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

PITCHES = {   # mph, rpm, spin efficiency, lift direction, target (x, y) at the front of the plate, contact depth z
    "fb": (92, 2300, 0.9, (-0.2, 1, 0), (0.15, 2.4), PLATE_FRONT - 1.2),              # the pitch the shortstop's grounders come off
    "cfb": (95, 2350, 0.92, (-0.2, 1, 0), (0.3, 2.6), PLATE_FRONT - 1.2),             # the fastball the catcher receives
    "cslide": (84, 2500, 0.5, (1.0, -0.45, 0), (1.05, 1.55), PLATE_FRONT - 1.2),      # the breaking ball: glove-side break, low and away from a right-hander
    "csteal": (93, 2300, 0.9, (-0.2, 1, 0), (0.3, 3.0), PLATE_FRONT - 1.2),           # up, so it's a clean catch to throw from
}
HITS = {   # pitch, exit mph, launch angle, spray angle, seconds of flight to keep
    "big": ("fb", 98, 19, -13, 5.2),           # the bigger hitter: a solid drive to left field
    "small": ("fb", 107, 22, -15, 5.8),        # the smaller hitter: the ball comes off the bat harder and carries to the wall
}
# ground balls: exit mph, launch (deg, down), spray (deg, + toward right field), how far from home he fields it (ft), bad hop (ft) or None
GROUNDERS = {
    "mid": (98, -8, -8, 141, None),       # up the middle: the dive to his glove side
    "hole": (92, -9, -24, 150, None),     # deep in the hole: the backhand
    "chop": (52, -38, -16, 112, None),    # a slow chopper toward the left side: he charges
    "routine": (82, -14, -14, 142, None), # right at him
    "bad": (90, -11, -12, 139, 127),      # a hard one that takes a bad hop off the lip
    "hole2": (90, -9, -26, 148, None),    # deep in the hole again: the jump throw
    "ss2": (80, -14, -9, 135, None),      # toward the bag: he fields and feeds the second baseman covering
    "b2": (80, -14, 14, 138, None),       # to the second baseman: the shortstop covers second
}
def grounder(p0, ev, la, spray, bad, dur=3.2):
    """Gravity and drag in the air; each bounce off the firm infield keeps 52% of the vertical speed and 88% along the ground,
    low skips turn into a roll. A bad hop (at the first bounce past `bad` ft from home) kicks up and to the side."""
    la, sp = np.radians(la), np.radians(spray)
    d = np.array([np.sin(sp) * np.cos(la), np.sin(la), -np.cos(sp) * np.cos(la)])
    p, v, t = np.array(p0, float) * FT, d * ev * MPH, 0.0
    T, P, B, dt, rolling, used = [0.0], [p / FT], [], 0.0005, False, False
    while t < dur:
        sp_ = np.linalg.norm(v)
        if rolling: a = -v / max(sp_, 1e-9) * 0.30 * 9.80665; a[1] = 0
        else: a = -K * 0.40 * sp_ * v + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        if not rolling and p[1] < 0.121 * FT and v[1] < 0:
            p[1] = 0.121 * FT; B.append(round(t, 4))
            dist = np.hypot(p[0], p[2]) / FT
            if bad and not used and dist > bad:
                used = True; v[1] = -v[1] * 0.95 + 1.2; ang = np.radians(-9); c_, s_ = np.cos(ang), np.sin(ang)
                v[0], v[2] = v[0] * c_ - v[2] * s_, v[0] * s_ + v[2] * c_
            elif abs(v[1]) < 0.9: v[1] = 0; rolling = True
            else: v[1] = -v[1] * 0.52; v[0] *= 0.88; v[2] *= 0.88
        T.append(t); P.append(p / FT)
    return np.array(T), np.array(P), B
if __name__ == "__main__":
    out = {"pitches": {}, "hits": {}, "release": RELEASE.tolist(), "plate_front": PLATE_FRONT,
           "fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "seats": {"gap": 3, "y0": 8.5, "rise": 0.5, "depth": 110}}
    for k, (mph, rpm, eff, push, tgt, cz) in PITCHES.items():
        T, P, d = pitch(mph, rpm, eff, push, tgt)
        tf, pf = at_z(T, P, PLATE_FRONT)
        tc, pc = at_z(T, P, cz)
        pu = np.array(push, float); pu /= np.linalg.norm(pu)
        axis = np.cross(d, pu); axis /= np.linalg.norm(axis)
        out["pitches"][k] = dict(mph=mph, rpm=rpm, flight=round(float(T[-1]), 3), front=round(tf, 3), cross=[round(float(x), 2) for x in pf],
                                 t_contact=round(tc, 4), contact=[round(float(x), 3) for x in pc],
                                 spin=[round(float(x), 4) for x in axis], path=samples(T, P))
        print(f"{k}: {mph} mph: crosses ({pf[0]:+.2f}, {pf[1]:.2f}) at {tf:.3f} s; contact {pc.round(2)} at {tc:.3f} s")
    # the curveball in the dirt: it bounces ~4.5 ft in front of the plate and climbs toward the catcher's chest
    best = None
    yaw = np.arctan2(0.15 - RELEASE[0], -RELEASE[2])
    for pit in np.linspace(-0.14, 0.0, 700):                        # steep to flat
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P = fly(RELEASE, d * 79 * MPH / FT, 2600, 0.7, (0.3, -1, 0), lambda p, v, t: p[2] >= 2.6 or t > 1.4, bounce=True)
        ib = int(np.argmax(P[:, 1] <= 0.1215))
        if P[ib, 1] > 0.1215 or P[ib, 2] > -2: continue
        zb = P[ib, 2]; tc, pc = at_z(T, P, 1.4)
        score = abs(zb + 4.6)
        if best is None or score < best[0]: best = (score, pit, T, P, ib, tc, pc)
    _, pit, T, P, ib, tc, pc = best
    tg, pg = at_z(T, P, GLOVE_Z)
    out["pitches"]["cdirt"] = dict(mph=79, rpm=2600, flight=round(float(tg), 3), bounce_t=round(float(T[ib]), 4), bounce=P[ib].round(2).tolist(), chest_t=round(tc, 4), chest=pc.round(2).tolist(),
                                   spin=[0.0, 0.0, -1.0], path=samples(T, P))
    print(f"cdirt: 79 mph: bounces at z {P[ib][2]:.1f} ft (x {P[ib][0]:+.2f}) at {T[ib]:.3f} s; at z 1.4 ft: y {pc[1]:.2f} at {tc:.3f} s; z 2.0 at {tg:.3f} s")
    for k, (ev, la, spray, R, bad) in GROUNDERS.items():
        p0 = np.array(out["pitches"]["fb"]["contact"])
        T, P, B = grounder(p0, ev, la, spray, bad)
        dist = np.hypot(P[:, 0], P[:, 2]); i = int(np.argmax(dist >= R)); tf = float(T[i])
        out["hits"][k] = dict(pitch="fb", ev=ev, la=la, spray=spray, tf=round(tf, 3), field=[round(float(x), 3) for x in P[i]], bounces=B, path=samples(T, P, 240))
        print(f"  {k}: {ev} mph {la} deg spray {spray}: reaches {R} ft at {tf:.2f} s, at {P[i].round(1)}; bounces {B[:6]}")
    for k, (pk, ev, la, spray, dur) in HITS.items():
        p0 = np.array(out["pitches"][pk]["contact"])
        T, P = batted(p0, ev, la, spray, dur)
        out["hits"][k] = dict(pitch=pk, ev=ev, la=la, spray=spray, path=samples(T, P, 120))
        land = np.argmax((P[1:, 1] <= 0.13) & (np.diff(P[:, 1]) < 0)) + 1
        print(f"  {k}: {ev} mph at {la} deg, spray {spray}: first lands {np.hypot(P[land, 0], P[land, 2]):.0f} ft at {T[land]:.2f} s; after {T[-1]:.1f} s at {P[-1].round(0)}")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
