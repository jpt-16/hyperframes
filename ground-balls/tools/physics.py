"""Ground balls to the shortstop, and how he plays them, for the "work through the ball" video.

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds; t = 0 is contact. Every ball goes toward the shortstop,
17 deg to the third-base side of straightaway; he starts 146 ft from the plate.

BALL: gravity + air drag (Cd 0.35) in flight. Bounces off the infield: the vertical speed reverses and keeps e of
its size (0.50-0.55, the restitution of a firm infield) and the speed along the ground keeps 88%; low skips under
2 ft/s become a roll that slows ~3 ft/s^2. The four balls are ordinary ground balls hit down into the dirt in front
of the plate; the hop pattern near the shortstop comes out of the bounces, not a hand-drawn curve:
    awkward   93 mph, -16 deg   a long hop that lands 7 ft in front of his spot: wait for it and it's rising at
                                his belt as it reaches him (an in-between hop); move and you can take the end of
                                the big hop out in front
    routine   66 mph, -28 deg   a readable 2 ft hop: attack it and field it in stride
    short     69 mph, -24 deg   bounces right where he meets it: field the short hop, glove down and out front
    high      63 mph, -36 deg   a high chopper: near chest high where he'd naturally charge it, so he backs up
                                a couple of steps and takes it as it comes down

THE SHORTSTOP (choreography, not a measurement): ready, then a 0.25 s first move. Where he fields each ball is
chosen from the ball's flight: a spot he can reach under control where the ball is at a playable height.
The times from glove to release are illustrative values for each technique (a gather-and-reset after fielding it
flat-footed takes more steps than fielding it on the move); the video never puts numbers on them.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
K = 0.5 * 1.19 * np.pi * 0.0366 ** 2 / 0.145
R_BALL = 0.12
CONTACT = np.array([-0.6, 2.6, -2.2])
PHI = -17.0
D = np.array([np.sin(np.radians(PHI)), 0, -np.cos(np.radians(PHI))])     # home -> shortstop
SIDE = np.array([-D[2], 0, D[0]]) * -1                                     # perpendicular, toward the first-base side
SIDE = np.array([np.cos(np.radians(PHI)), 0, np.sin(np.radians(PHI))])
SS_R = 146.0
B1 = np.array([63.64, 0, -63.64])
GLOVE_1B = np.array([61.3, 4.0, -66.6])                                    # first baseman's stretch toward the shortstop
THROW_MPH = 82.0
HZ = 120

def ground_ball(ev, la, e, mu=0.88, dt=0.0005, tmax=4.5):
    v = (D * np.cos(np.radians(la)) + np.array([0, np.sin(np.radians(la)), 0])) * ev * MPH / FT
    p = CONTACT.copy(); t = 0.0; T, P, B = [0.0], [p.copy()], []
    while t < tmax:
        sp = np.linalg.norm(v) * FT
        a = -K * 0.35 * sp * v + np.array([0, -32.17, 0])
        if p[1] <= R_BALL + 1e-6 and v[1] == 0: a = np.zeros(3)
        v = v + a * dt; p = p + v * dt; t += dt
        if p[1] <= R_BALL and v[1] <= 0:
            p[1] = R_BALL
            if abs(v[1]) > 2.0: B.append((round(t, 4), [round(x, 2) for x in p])); v[1] = -e * v[1]; v[[0, 2]] *= mu
            else:
                v[1] = 0; h = np.hypot(v[0], v[2])
                if h > 0: v[[0, 2]] *= max(0.0, h - 3.0 * dt) / h
        T.append(t); P.append(p.copy())
    return np.array(T), np.array(P), B

def along(P): return P @ D                                                  # distance along the line to the shortstop

def at_r(T, P, r):
    s = along(P); i = int(np.argmax(s >= r)); f = (r - s[i - 1]) / (s[i] - s[i - 1])
    return float(T[i - 1] + f * (T[i] - T[i - 1])), P[i - 1] + f * (P[i] - P[i - 1])

def pt(r, lat=0.0): return D * r + SIDE * lat

def throw_from(rel):
    """Release point -> first baseman's glove: a near-flat 82 mph throw with drag (solve the launch angle)."""
    d = (GLOVE_1B - rel) * np.array([1, 0, 1]); d /= np.linalg.norm(d)
    def fly(ang):
        v = (d * np.cos(ang) + np.array([0, np.sin(ang), 0])) * THROW_MPH * MPH / FT; p = rel.copy(); T, P = [0.0], [p.copy()]
        while np.dot(p - GLOVE_1B, d) < 0 and T[-1] < 3:
            sp = np.linalg.norm(v) * FT; v = v + (-K * 0.35 * sp * v + np.array([0, -32.17, 0])) * 0.0005; p = p + v * 0.0005; T.append(T[-1] + 0.0005); P.append(p.copy())
        return np.array(T), np.array(P)
    lo, hi = -0.1, 0.25
    for _ in range(40):
        m = (lo + hi) / 2; T, P = fly(m)
        if P[-1][1] < GLOVE_1B[1]: lo = m
        else: hi = m
    return fly((lo + hi) / 2)

def spline(keys, hz=HZ):
    """keys: [(t, r, lat)] -> positions on a smooth (Catmull-Rom in time) path, sampled from t=0."""
    ts = np.array([k[0] for k in keys]); ps = np.array([pt(k[1], k[2]) for k in keys])
    tt = np.arange(0, ts[-1] + 1e-9, 1 / hz); out = []
    for t in tt:
        if t <= ts[0]: out.append(ps[0]); continue
        i = min(np.searchsorted(ts, t) - 1, len(ts) - 2)
        p0, p1, p2, p3 = ps[max(i - 1, 0)], ps[i], ps[i + 1], ps[min(i + 2, len(ps) - 1)]
        t0, t1, t2, t3 = ts[max(i - 1, 0)], ts[i], ts[i + 1], ts[min(i + 2, len(ts) - 1)]
        u = (t - t1) / (t2 - t1)
        m1 = (p2 - p0) / max(t2 - t0, 1e-6) * (t2 - t1); m2 = (p3 - p1) / max(t3 - t1, 1e-6) * (t2 - t1)
        if i == 0: m1 = np.zeros(3)
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        out.append(h00 * p1 + h10 * m1 + h01 * p2 + h11 * m2)
    return np.array(out)

def fence(phi):                             # fence distance (ft) at spray angle phi (deg): 330 lines, 375 alleys, 400 center
    a = abs(phi)
    return 400 - 25 * (a / 22.5) ** 1.3 if a <= 22.5 else 375 - 45 * ((a - 22.5) / 22.5) ** 1.15

BALLS = {"awkward": (93, -16, 0.55), "routine": (66, -28, 0.50), "short": (69, -24, 0.50), "high": (63, -36, 0.55)}

if __name__ == "__main__":
    out = {"hz": HZ, "dir": D.round(4).tolist(), "side": SIDE.round(4).tolist(), "ss_r": SS_R, "glove_1b": GLOVE_1B.tolist(), "balls": {}, "plays": {},
           "fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)]}
    sims = {}
    for name, (ev, la, e) in BALLS.items():
        T, P, B = ground_ball(ev, la, e); sims[name] = (T, P, B)
        tt = np.arange(0, T[-1], 1 / HZ)
        out["balls"][name] = {"ev": ev, "la": la, "e": e, "bounces": B, "hz": HZ,
                              "p": [[round(float(np.interp(x, T, P[:, k])), 3) for k in range(3)] for x in tt]}
    # where each technique fields the ball (distance from home, glove height there, time)
    def field_at(name, r):
        T, P, _ = sims[name]; t, p = at_r(T, P, r); return t, p
    plays = {
        # name: ball, kind, fielding distance (along the line), body offset behind the glove, glove->release
        "stand":   dict(ball="awkward", kind="stand", r=144.6, behind=0.9, exch=0.95, label="Waits on it, fields it at his body"),
        "through": dict(ball="awkward", kind="through", r=134.0, behind=2.0, exch=0.60, label="Works through it"),
        "routine": dict(ball="routine", kind="through", r=132.0, behind=2.0, exch=0.60, label="Routine hop: attack it"),
        "short":   dict(ball="short", kind="short", r=139.2, behind=2.1, exch=0.68, label="Short hop: stay down, stay balanced"),
        "high":    dict(ball="high", kind="back", r=151.5, behind=2.0, exch=0.68, label="High hop: create space"),
    }
    for name, pl in plays.items():
        T, P, B = sims[pl["ball"]]
        tf, gp = field_at(pl["ball"], pl["r"])
        rb = pl["r"] + pl["behind"]                                           # where his body is when the ball hits the glove
        kind = pl["kind"]
        to1b = B1 - pt(rb); to1b /= np.linalg.norm(to1b)
        r1b = float(to1b @ D); l1b = float(to1b @ SIDE)                       # direction to first, in (along, side)
        if kind == "stand":       # flat-footed: a small creep, fields it at his body, two gather shuffles toward first, then throws
            keys = [(0, SS_R, 0), (0.3, SS_R - 0.4, 0), (tf, rb, 0), (tf + 0.25, rb, 0.05), (tf + 0.5, rb + r1b * 1.2, l1b * 1.2),
                    (tf + 0.72, rb + r1b * 2.4, l1b * 2.4), (tf + pl["exch"], rb + r1b * 3.0, l1b * 3.0), (tf + pl["exch"] + 0.5, rb + r1b * 4.0, l1b * 4.0)]
            steps = [tf + 0.36, tf + 0.6, tf + 0.8]
        elif kind == "back":      # reads it, a quick drop step back to let it come down, fields it, steps through
            keys = [(0, SS_R, 0), (0.25, SS_R, 0), (0.7, SS_R - 1.5, -0.6), (tf - 0.35, rb - 0.5, -0.6), (tf, rb, -0.3),
                    (tf + 0.3, rb + r1b * 2.2, -0.3 + l1b * 2.2), (tf + pl["exch"], rb + r1b * 4.2, -0.3 + l1b * 4.2), (tf + pl["exch"] + 0.5, rb + r1b * 6.5, -0.3 + l1b * 6.5)]
            steps = [tf + 0.2, tf + pl["exch"] - 0.1]
        else:                     # through / short: an angled, controlled approach, glove out front, momentum carries toward first
            lat0 = -1.8                                                        # starts a step to the third-base side: comes through on an angle
            v_f = 7.0 if kind == "through" else 3.5
            keys = [(0, SS_R, lat0), (0.25, SS_R, lat0), (tf - 0.35, rb + v_f * 0.35 * 0.9, lat0 * 0.35), (tf, rb, 0),
                    (tf + 0.25, rb + r1b * 2.3, l1b * 2.3), (tf + pl["exch"], rb + r1b * 4.6, l1b * 4.6), (tf + pl["exch"] + 0.5, rb + r1b * 6.8, l1b * 6.8)]
            steps = [tf + 0.18, tf + pl["exch"] - 0.08]
        path = spline(keys)
        rel_t = tf + pl["exch"]
        i_rel = min(int(rel_t * HZ), len(path) - 1)
        rel = path[i_rel] + np.array([0, 6.0, 0]) + to1b * 0.8
        TT, PT = throw_from(rel)
        sp = np.r_[0, np.linalg.norm(np.diff(path, axis=0), axis=1)] * HZ
        L = 3.2 + 7.0 * np.clip(sp / 25, 0, 1); ph = np.cumsum(sp / L) / HZ        # running gait phase
        foot = [[round(float(x), 2) for x in (path[min(int(s * HZ), len(path) - 1)] + SIDE * (0.45 if k % 2 else -0.45))] for k, s in enumerate(steps)]
        out["plays"][name] = dict(pl, t_field=round(tf, 3), glove_pt=[round(x, 2) for x in gp], glove_h=round(float(gp[1]), 2), t_release=round(rel_t, 3),
                                  t_arrive=round(rel_t + float(TT[-1]), 3), release=[round(x, 2) for x in rel], steps=[round(s, 3) for s in steps], footprints=foot,
                                  pos={"x": [round(float(q[0]), 3) for q in path], "z": [round(float(q[2]), 3) for q in path], "ph": [round(float(x), 3) for x in ph]},
                                  throw={"t0": round(rel_t, 4), "hz": HZ, "dur": round(float(TT[-1]), 4),
                                         "p": [[round(float(np.interp(x, TT, PT[:, k])), 3) for k in range(3)] for x in np.arange(0, TT[-1] + 1e-9, 1 / HZ)]})
        T_, P_, _ = sims[pl["ball"]]
        _, p146 = at_r(T_, P_, SS_R - 1.0)
        print(f"{name:8s} {pl['ball']:8s} fields at {pl['r']:.1f} ft, t {tf:.2f}s, glove height {gp[1]:.2f} ft"
              f" (ball at his start spot: {p146[1]:.2f} ft)  release {rel_t:.2f}s  ball at first {rel_t + TT[-1]:.2f}s  run {np.linalg.norm(path[int(tf*HZ)] - path[0]):.1f} ft")
    for name, (T, P, B) in sims.items():
        print(name, "bounces:", " ".join(f"{float(np.hypot(b[1][0], b[1][2])):.0f}ft@{b[0]:.2f}" for b in B[:6]))
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
