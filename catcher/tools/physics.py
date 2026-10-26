"""The plays for the "complete catcher" video: pitches, a ball in the dirt, a steal of second, a gap double.

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. Each play has its own clock: t = 0 is when the pitch reaches
the catcher's glove (or, for the gap double, the moment of contact).

Pitches (right-handed pitcher, 6.5 ft extension): gravity + drag + spin lift (Magnus), 0.5 ms steps, aimed by
iteration at a spot as the ball crosses the front of the plate:
    slider     85 mph, glove-side break, low and away from the right-handed hitter, out of the zone (the chase)
    fastball   94 mph, ride, at the bottom edge of the zone (the borderline pitch for framing)
    curveball  79 mph, topspin, lands ~4 ft in front of the plate and bounces (the block)
    steal      93 mph fastball, a little up and away (the pitch the runner goes on)
Strike zone shown: 17 in wide plate plus the ball's radius each side; 1.6-3.4 ft high (a typical hitter's zone).

The steal: the runner leads 12 ft off first and goes on the pitcher's first move (1.3 s before the ball reaches the
plate), sprinting 27 ft/s top speed (a good base stealer: 28.5 ft/s top speed) and sliding the last 9 ft. The catcher's exchange and
footwork take 0.75 s from glove to release; the 82 mph throw (drag included) goes to the shortstop's tag at the bag.
These are illustrative values chosen to make a close play; no times are shown in the video.

The gap double: 99 mph, 16 deg off the bat to left-center; carries, bounces and rolls (drag, then bounces that keep
half their vertical speed and 75% of their speed along the ground) to the wall. The batter-runner (the catcher) runs from the
box at the same 27 ft/s top speed, rounds first on a curve, and heads for second.
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
    out = {"fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "zone": {"half_w": round((17 / 2 + 1.45) / 12, 3), "bot": 1.6, "top": 3.4, "z": PLATE_FRONT}, "pitches": {}}
    specs = {
        "slider":   dict(mph=85, rpm=2500, eff=0.45, push=(1.0, -0.5, 0), target=(1.25, 0.95)),
        "fastball": dict(mph=94, rpm=2300, eff=0.9, push=(-0.2, 1, 0), target=(0.66, 1.62)),
        "steal":    dict(mph=93, rpm=2300, eff=0.9, push=(-0.2, 1, 0), target=(0.35, 3.0)),
    }
    for name, sp in specs.items():
        T, P, _ = pitch(sp["mph"], sp["rpm"], sp["eff"], sp["push"], sp["target"])
        tf, pf = at_z(T, P, PLATE_FRONT)
        out["pitches"][name] = dict(mph=sp["mph"], at_plate=pf.round(3).tolist(), flight=round(float(T[-1]), 3), path=samples(T, P, -float(T[-1])))
        print(f"{name:9s} {sp['mph']} mph, crosses the front of the plate at x {pf[0]:+.2f} ft, y {pf[1]:.2f} ft; flight {T[-1]:.2f} s")
    # the curveball in the dirt: lands ~4 ft in front of the plate, one bounce, into the catcher's chest
    yaw = np.arctan2(0.2 - RELEASE[0], -RELEASE[2])
    for pit in np.linspace(-0.12, 0.0, 600):                        # from steep to flatter: the first that lands ~5 ft in front
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P, B = fly(RELEASE, d * 79 * MPH / FT, 2600, 0.7, (0.3, -1, 0), lambda p, v, t: p[2] >= 1.2 or t > 1.4, bounce=(0.45, 0.72))
        if B and B[0][1][2] >= -6.5: break
    out["pitches"]["curve_dirt"] = dict(mph=79, bounce=B[0], flight=round(float(T[-1]), 3), path=samples(T, P, -float(T[-1])), at_end=P[-1].round(2).tolist())
    print(f"curve     79 mph, bounces at z {B[0][1][2]:.1f} ft (x {B[0][1][0]:+.1f}), reaches the catcher's chest {T[-1]:.2f} s after release, height {P[-1][1]:.1f} ft")

    # ---- the steal of second: pitch reaches the glove at t = 0
    STEAL = out["pitches"]["steal"]
    LEAD, GO = 13.0, -1.30                                          # lead off first; goes on the pitcher's first move
    EXCH = 0.75                                                     # glove -> release: exchange, footwork, release
    REL_PT = np.array([0.4, 6.1, 0.2])                              # out of his crouch, stepping toward second
    TAG_PT = np.array([0.9, 1.4, -125.6])                           # the shortstop's glove at the bag, low, first-base side of it
    d = TAG_PT - REL_PT; dh = d * np.array([1, 0, 1]); dh /= np.linalg.norm(dh)
    def throw(ang):
        v0 = (dh * np.cos(ang) + np.array([0, np.sin(ang), 0])) * 82 * MPH / FT
        return fly(REL_PT, v0, 1500, 0.9, (0, 1, 0), lambda p, v, t: np.dot(p - TAG_PT, dh) >= 0 or t > 3)
    lo, hi = -0.1, 0.3
    for _ in range(40):
        m = (lo + hi) / 2; TT, PT, _ = throw(m)
        if PT[-1][1] < TAG_PT[1]: lo = m
        else: hi = m
    TT, PT, _ = throw((lo + hi) / 2)
    t_rel = EXCH; t_tag = t_rel + float(TT[-1])
    lead_pt = B1 + (B2 - B1) / np.linalg.norm(B2 - B1) * LEAD
    run_len = np.linalg.norm(B2 - lead_pt) - 0.6                     # to his foot on the bag
    # he reaches the bag a hair after the tag is down
    tt = np.arange(GO, 6, 1 / HZ); s = np.minimum(sprint(tt - GO, 28.5, 0.62), run_len + 2)    # a good base stealer
    t_bag = float(tt[np.argmax(s >= run_len)])
    out["steal"] = dict(go=GO, lead=lead_pt.round(2).tolist(), exch=EXCH, t_release=round(t_rel, 3), t_tag=round(t_tag, 3), t_bag=round(t_bag, 3),
                        release=REL_PT.tolist(), tag=TAG_PT.tolist(), throw=samples(TT, PT, t_rel), run_len=round(float(run_len), 2),
                        run={"t0": GO, "hz": HZ, "s": [round(float(x), 3) for x in s]})
    print(f"steal: release {t_rel:.2f}s after the catch, tag down {t_tag:.2f}s, runner's foot reaches the bag {t_bag:.2f}s")

    # ---- the gap double (t = 0 at contact)
    CONTACT = np.array([0.6, 3.0, -2.0])                            # a right-handed hitter's contact point out front
    phi = np.radians(-24); la = np.radians(16)
    dv = np.array([np.sin(phi) * np.cos(la), np.sin(la), -np.cos(phi) * np.cos(la)])
    T, P, B = fly(CONTACT, dv * 99 * MPH / FT, 1800, 1.0, (0, 1, 0), lambda p, v, t: t > 6.0 or np.hypot(p[0], p[2]) > 368 or (np.linalg.norm(v[[0, 2]]) < 6 and p[1] < 0.3), cd=0.40, bounce=(0.5, 0.75))
    land = B[0][1] if B else P[-1].tolist()
    out["double"] = dict(ev=99, la=16, contact=CONTACT.tolist(), land=land, t_land=B[0][0] if B else None, path=samples(T, P, 0.0),
                         dist=round(float(np.hypot(land[0], land[2])), 1))
    print(f"double: lands {np.hypot(land[0], land[2]):.0f} ft from the plate at {B[0][0]:.2f}s, rolls to {np.hypot(P[-1][0], P[-1][2]):.0f} ft by {T[-1]:.2f}s")
    # batter-runner: out of the box, down the line, a rounded turn at first, on toward second
    start = np.array([-2.4, 0, -0.7]); pts = [start]
    line = (B1 - start) / np.linalg.norm(B1 - start)
    for k in np.linspace(0, 1, 40)[1:]: pts.append(start + (B1 - start - line * 14 + np.array([5, 0, 5]) * 0) * k)   # straight, aiming a little wide of the bag
    c0 = pts[-1]
    to2 = (B2 - B1) / np.linalg.norm(B2 - B1)
    ctrl = B1 + np.array([4.5, 0, 4.5])                              # bows out into foul ground to hit the inside corner on the way to second
    for k in np.linspace(0, 1, 30)[1:]: pts.append((1 - k) ** 2 * c0 + 2 * (1 - k) * k * ctrl + k ** 2 * (B1 + to2 * 12))
    for k in np.linspace(0, 1, 40)[1:]: pts.append(B1 + to2 * (12 + (np.linalg.norm(B2 - B1) - 14) * k))
    pts = np.array(pts); seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    tt = np.arange(0, 9, 1 / HZ); s = sprint(tt - 0.25)
    s = np.minimum(s, seg[-1])
    path = np.stack([np.interp(s, seg, pts[:, k]) for k in range(3)], 1)
    out["runner"] = {"hz": HZ, "x": path[:, 0].round(3).tolist(), "z": path[:, 2].round(3).tolist(), "s": s.round(3).tolist(),
                     "t_first": round(float(tt[np.argmax(s >= seg[39])]), 3)}
    print(f"batter-runner: by first base at ~{out['runner']['t_first']:.2f}s after contact")
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
