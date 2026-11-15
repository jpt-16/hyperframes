"""The pitch and the pop-ups for "Why catchers struggle with pop-ups".

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Each path starts at t = 0 (release, or contact for a pop-up).

The pitch: a 95 mph fastball (gravity, drag, spin lift), as in the other videos.
Pop-ups: gravity, drag (Cd 0.35) and the Magnus force from a fixed spin axis (a_M ~ Cl(S) v^2 along w x v), stepped
every 0.5 ms. A pop-up off a pitched ball leaves the bat with heavy backspin (here 3,500-4,200 rpm, spin axis
horizontal and across the ball's path). Going up, that spin pushes the ball back toward the field; coming down it pushes
it the other way, so the path bends instead of making a plain parabola, and the ball drifts while the catcher looks
for it. Fungo pop-ups in practice are hit off a tossed ball and carry far less spin (here 800 rpm): their paths are
close to plain parabolas. Each pop-up's launch is solved (launch angle and direction) so it comes down to the catch
height at a chosen spot.
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

def flyw(p0, v0, rpm, axis, stop, cd=0.35, dt=0.0005, decay=20.0):
    """Gravity, drag and a true Magnus force (w x v, w fixed in direction, decaying with time constant `decay` s)."""
    p, v, t = np.array(p0, float) * FT, np.array(v0, float) * FT, 0.0
    w = np.array(axis, float); w /= np.linalg.norm(w)
    T, P = [0.0], [p / FT]
    while True:
        sp = np.linalg.norm(v); r = rpm * np.exp(-t / decay)
        m = np.cross(w, v / max(sp, 1e-9))
        a = -K * cd * sp * v + K * cl(sp, r) * sp * sp * m + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        T.append(t); P.append(p / FT)
        if stop(p / FT, v / FT, t): return np.array(T), np.array(P)

CATCH_Y = 6.0
def launch(p0, ev, la, az, rpm, spin_sign=1.0, dur=9.0):
    """az: horizontal direction in degrees, 0 = toward the backstop (+z), 90 = toward first base (+x)."""
    la_, az_ = np.radians(la), np.radians(az)
    h = np.array([np.sin(az_), 0, np.cos(az_)]); d = h * np.cos(la_) + np.array([0, 1, 0]) * np.sin(la_)
    axis = np.cross(h, [0, 1, 0]) * spin_sign                  # backspin for the launch direction
    return flyw(p0, d * ev * MPH / FT, rpm, axis, lambda p, v, t: (p[1] < 0.12 and v[1] < 0) or t > dur)

def down_at(T, P, y):
    i = len(P) - 1
    while i > 0 and P[i, 1] < y: i -= 1
    f = (y - P[i + 1, 1]) / (P[i, 1] - P[i + 1, 1]) if i + 1 < len(P) else 0
    return float(T[i + 1] - f * (T[i + 1] - T[i])), P[i + 1] + f * (P[i] - P[i + 1])

def solve(p0, ev, rpm, target, la0=80.0, az0=None):
    """Launch angle and direction so the ball comes down through CATCH_Y at target (x, z)."""
    tx, tz = target
    la = la0; az = np.degrees(np.arctan2(tx - p0[0], tz - p0[2])) if az0 is None else az0
    def land(la, az):
        T, P = launch(p0, ev, la, az, rpm); _, q = down_at(T, P, CATCH_Y); return np.array([q[0], q[2]])
    for _ in range(30):
        q = land(la, az); e = np.array([tx, tz]) - q
        if np.hypot(*e) < 0.15: break
        J = np.zeros((2, 2)); h = 0.05
        J[:, 0] = (land(la + h, az) - q) / h; J[:, 1] = (land(la, az + h) - q) / h
        step = np.linalg.lstsq(J, e, rcond=None)[0]; step = np.clip(step, -4, 4)
        la = float(np.clip(la + step[0], 55, 89.5)); az = float(az + step[1])
    return la, az

PITCHES = {"fb": (95, 2400, 0.9, (-0.2, 1, 0), (0.3, 2.35), PLATE_FRONT - 1.2)}
CONTACT = None
# pop-ups: id -> (exit mph, rpm, catch spot (x, z), note). Game pop-ups start at the contact point; practice ones at the coach's bat.
POPS = {
    "pa": (78, 3800, (7.0, 16.0), "the opener: up behind the plate, a little toward first"),
    "pd": (80, 3600, (-46.0, 4.0), "drifts toward the third-base dugout"),
    "pb": (82, 4000, (-3.0, 42.0), "carries back toward the backstop"),
    "pm": (76, 4200, (4.0, -22.0), "goes up, then curls back toward the mound"),
    "pf": (84, 4000, (11.0, 47.0), "the payoff: back toward the backstop, near the wall"),
}
COACH_BAT = (-2.5, 3.2, -5.0)
FUNGO = {   # practice: a coach's fungo pop-ups (little spin), all over the place
    "f1": (64, 800, (-26.0, 18.0)), "f2": (70, 800, (24.0, 36.0)), "f3": (62, 800, (30.0, -8.0)),
    "f4": (66, 800, (-14.0, -30.0)), "f5": (60, 800, (6.0, 8.0)), "f6": (68, 800, (-38.0, -6.0)),
    "f7": (72, 800, (-3.0, 42.0)),    # the same spot as the game pop-up "pb", for the side-by-side
}
if __name__ == "__main__":
    out = {"pitches": {}, "pops": {}, "release": RELEASE.tolist(), "plate_front": PLATE_FRONT, "catch_y": CATCH_Y, "coach_bat": list(COACH_BAT),
           "fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "seats": {"gap": 3, "y0": 8.5, "rise": 0.5, "depth": 110}}
    for k, (mph, rpm, eff, push, tgt, cz) in PITCHES.items():
        T, P, d = pitch(mph, rpm, eff, push, tgt)
        tf, pf = at_z(T, P, PLATE_FRONT); tc, pc = at_z(T, P, cz)
        pu = np.array(push, float); pu /= np.linalg.norm(pu); axis = np.cross(d, pu); axis /= np.linalg.norm(axis)
        out["pitches"][k] = dict(mph=mph, rpm=rpm, flight=round(float(T[-1]), 3), front=round(tf, 3), cross=[round(float(x), 2) for x in pf],
                                 t_contact=round(tc, 4), contact=[round(float(x), 3) for x in pc], spin=[round(float(x), 4) for x in axis], path=samples(T, P))
        print(f"{k}: {mph} mph: crosses ({pf[0]:+.2f}, {pf[1]:.2f}) at {tf:.3f} s; contact {pc.round(2)} at {tc:.3f} s")
    cp = np.array(out["pitches"]["fb"]["contact"])
    def add(k, p0, ev, rpm, tgt, note=""):
        la, az = solve(p0, ev, rpm, tgt)
        T, P = launch(p0, ev, la, az, rpm); tcat, q = down_at(T, P, CATCH_Y)
        ap = int(np.argmax(P[:, 1]))
        out["pops"][k] = dict(ev=ev, rpm=rpm, la=round(la, 2), az=round(az, 2), t_catch=round(tcat, 3), catch=[round(float(x), 2) for x in q],
                              apex=[round(float(x), 1) for x in P[ap]], t_apex=round(float(T[ap]), 2), path=samples(T, P, 120), p0=[round(float(x), 3) for x in p0])
        print(f"{k}: {ev} mph, {rpm} rpm, la {la:.1f}, az {az:.1f}: apex {P[ap, 1]:.0f} ft at {T[ap]:.2f} s over ({P[ap, 0]:.0f}, {P[ap, 2]:.0f}); "
              f"down to {CATCH_Y} ft at ({q[0]:.1f}, {q[2]:.1f}) after {tcat:.2f} s  {note}")
    for k, (ev, rpm, tgt, note) in POPS.items(): add(k, cp, ev, rpm, tgt, note)
    for k, (ev, rpm, tgt) in FUNGO.items(): add(k, np.array(COACH_BAT), ev, rpm, tgt, "(fungo)")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
