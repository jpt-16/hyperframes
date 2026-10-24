"""The simulated play: a deep fly ball, a runner tagging at third, and two throws home.

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Every number in the video comes from here. Units: feet and seconds; t = 0 is the catch.
Field frame (same as assets/field.js): home plate at the origin, +x toward the first-base side,
-z toward center field, y up.

The ball flies under gravity, air drag and backspin lift (Magnus), integrated in 1 ms steps:
    drag  = 1/2 rho Cd A v^2                    rho = 1.19 kg/m^3 (about 75 F at sea level), Cd = 0.35 for throws
                                                (pitch-tracking range), 0.40 for the batted fly ball
    lift  = 1/2 rho CL A v^2, CL from spin      CL = 1.5 S (S < 0.1) else 0.09 + 0.6 S, S = r w / v (Sawicki et al. 2003)
A throw is aimed by solving for the launch angle (or speed) that puts the ball in the catcher's glove.

The runner covers the 89 ft from third base to the near corner of the plate:
    reacts 0.10 s after the catch, then v(t) = v_max (1 - e^(-t/tau)), v_max = 27 ft/s, tau = 0.65 s,
    and slides the last 9 ft, slowing at 16 ft/s^2 (sliding friction, mu about 0.5).
27 ft/s is the MLB average Statcast sprint speed on competitive runs (Baseball Savant). Everything else is
a stated assumption of this simulation, not tracking data.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
G, RHO, R_BALL, M_BALL, CD = 9.80665, 1.19, 0.0366, 0.145, 0.35
K = 0.5 * RHO * np.pi * R_BALL ** 2 / M_BALL           # per metre, multiplies v^2

# ------------------------------------------------------------------ assumptions (all in feet / seconds)
CATCH_DIST = 300.0                  # catch point, from home plate
CATCH_ANGLE = 20.0                  # degrees toward right field from the center-field line
CATCH_H = 6.4                       # glove height at the catch
CROW_HOP = 7.0                      # feet the fielder travels toward home between catch and release
RELEASE_H = 6.3                     # release height
EXCHANGE = 0.80                     # catch -> release (crow hop and throw)
TAG = 0.20                          # catcher: ball in the glove -> tag applied
GLOVE = np.array([-0.9, 2.4, -3.4]) # where the catcher receives the throw (in front of the plate, third-base side)
THROW_RPM = 1500                    # backspin on a four-seam throw
DIRECT_MPH = 95.0                   # the direct throw: flattest path that reaches the glove in the air at this speed
LOOP_ANGLE = 25.0                   # the looping throw: launched at 25 degrees, speed solved to reach the same glove
R_REACT, R_VMAX, R_TAU = 0.10, 27.0, 0.65
R_DIST, SLIDE_AT, SLIDE_DECEL = 89.0, 80.0, 16.0
B3 = np.array([-63.64, 0.0, -63.64])
FLY_CD = 0.40                       # batted balls: Cd 0.40 reproduces typical Statcast carry (about 370 ft at 95 mph / 30 deg)
FLY_LA, FLY_RPM = 30.0, 1800        # the fly ball: launch angle and backspin; exit speed solved to land in the glove
CONTACT = np.array([-0.4, 3.0, -1.2])

U = np.array([np.sin(np.radians(CATCH_ANGLE)), 0, -np.cos(np.radians(CATCH_ANGLE))])
C = CATCH_DIST * U
C[1] = CATCH_H

def cl(v, rpm):
    if rpm <= 0: return 0.0
    s = R_BALL * rpm * 2 * np.pi / 60 / max(v, 1e-6)
    return 1.5 * s if s < 0.1 else 0.09 + 0.6 * s

def fly(p0, v0, rpm, stop, dt=0.001, cd=CD):
    """Integrate a ball (positions in feet, velocity in ft/s). Returns arrays t, pos, vel."""
    p = np.array(p0, float) * FT; v = np.array(v0, float) * FT; t = 0.0
    T, P, V = [0.0], [p / FT], [v / FT]
    while True:
        sp = np.linalg.norm(v)
        up = np.array([0.0, 1.0, 0.0]) - (v / sp) * (v[1] / sp); up /= np.linalg.norm(up)
        a = -K * cd * sp * v + K * cl(sp, rpm) * sp * sp * up + np.array([0, -G, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        T.append(t); P.append(p / FT); V.append(v / FT)
        if stop(p / FT, v / FT, t): return np.array(T), np.array(P), np.array(V)

def throw_to(src, dst, mph, ang):
    """Launch from src toward dst (horizontal heading) at speed/angle; stop when it reaches dst's horizontal distance."""
    h = dst - src; h[1] = 0; dist = np.linalg.norm(h); hd = h / dist
    a = np.radians(ang); v0 = mph * MPH / FT * (hd * np.cos(a) + np.array([0, np.sin(a), 0]))
    return fly(src, v0, THROW_RPM, lambda p, v, t: np.dot(p - src, hd) >= dist or p[1] < 0 or t > 8)

def height_at_glove(src, mph, ang):
    T, P, V = throw_to(src, GLOVE, mph, ang)
    h = GLOVE - src; h[1] = 0
    return P[-1][1] if np.dot(P[-1] - src, h / np.linalg.norm(h)) >= np.linalg.norm(h) - 0.01 else -99.0

def solve_angle(src, mph, lo=0.0, hi=20.0):
    """Lowest launch angle at this speed that arrives at glove height (the flattest path)."""
    for _ in range(50):
        m = (lo + hi) / 2
        if height_at_glove(src, mph, m) < GLOVE[1]: lo = m
        else: hi = m
    return (lo + hi) / 2

def solve_speed(src, ang, lo=50.0, hi=110.0):
    for _ in range(50):
        m = (lo + hi) / 2
        if height_at_glove(src, m, ang) < GLOVE[1]: lo = m
        else: hi = m
    return (lo + hi) / 2

def runner(t):
    """Distance from third base (ft) and speed at time t after the catch."""
    dt, s, v, ts, out = 0.001, 0.0, 0.0, 0.0, None
    S, Vv = [], []
    for k in range(int(t / dt) + 1):
        tt = k * dt
        if tt > R_REACT:
            if s < SLIDE_AT: v = R_VMAX * (1 - np.exp(-(tt - R_REACT) / R_TAU))
            else: v = max(0.0, v - SLIDE_DECEL * dt)
            s += v * dt
        S.append(s); Vv.append(v)
    return np.array(S), np.array(Vv)

RUN_S, RUN_V = runner(7.0)
RUN_T = np.arange(len(RUN_S)) * 0.001
def run_at(t): return float(np.interp(t, RUN_T, RUN_S))
SCORE_T = float(RUN_T[np.argmax(RUN_S >= R_DIST)])

def play(src, mph, ang, exchange=EXCHANGE):
    T, P, V = throw_to(src, GLOVE, mph, ang)
    glove_t = exchange + T[-1]; tag_t = glove_t + TAG
    return dict(T=T, P=P, V=V, flight=float(T[-1]), glove_t=glove_t, tag_t=tag_t,
                runner_at_tag=run_at(tag_t), margin=SCORE_T - tag_t,
                apex=float(P[:, 1].max()), arrive_mph=float(np.linalg.norm(V[-1]) / (MPH / FT)))

def release_point(cdist=CATCH_DIST):
    c = cdist * U
    r = c + CROW_HOP * (-U); r[1] = RELEASE_H
    return r

REL = release_point()
DIRECT_ANG = solve_angle(REL, DIRECT_MPH)
LOOP_MPH = solve_speed(REL, LOOP_ANGLE)
DIRECT = play(REL, DIRECT_MPH, DIRECT_ANG)
LOOP = play(REL, LOOP_MPH, LOOP_ANGLE)
THROW_DIST = float(np.linalg.norm((GLOVE - REL) * np.array([1, 0, 1])))

# the fly ball: solve exit speed so it comes down into the fielder's glove
def fly_ball(ev):
    h = C - CONTACT; h[1] = 0; dist = np.linalg.norm(h); hd = h / dist
    a = np.radians(FLY_LA); v0 = ev * MPH / FT * (hd * np.cos(a) + np.array([0, np.sin(a), 0]))
    return fly(CONTACT, v0, FLY_RPM, lambda p, v, t: (v[1] < 0 and p[1] <= C[1]) or t > 9, cd=FLY_CD)
lo, hi = 70.0, 120.0
for _ in range(50):
    ev = (lo + hi) / 2; T, P, V = fly_ball(ev)
    if np.linalg.norm((P[-1] - CONTACT) * [1, 0, 1]) < np.linalg.norm((C - CONTACT) * [1, 0, 1]): lo = ev
    else: hi = ev
FLY_EV = (lo + hi) / 2
FT_, FP_, FV_ = fly_ball(FLY_EV)
HANG = float(FT_[-1])

# what would flip the result: one variable at a time, everything else held
def flips():
    out = {}
    # runner speed that scores
    global R_VMAX
    base = R_VMAX
    for v in np.arange(base, 33, 0.05):
        R_VMAX = v; s, _ = runner(7.0); st = RUN_T[np.argmax(s >= R_DIST)]
        if st < DIRECT["tag_t"]: out["runner_fps"] = round(float(v), 1); break
    R_VMAX = base
    # exchange time that lets him score
    out["exchange"] = round(EXCHANGE + DIRECT["margin"], 2)          # margin > 0 means out by that much
    # catch depth that lets him score (same arm, same exchange, flattest throw)
    for d in np.arange(CATCH_DIST, CATCH_DIST + 60, 1.0):
        src = release_point(d); a = solve_angle(src, DIRECT_MPH, 0, 30)
        p = play(src, DIRECT_MPH, a)
        if p["margin"] < 0: out["catch_dist"] = round(float(d)); break
    # arm speed below which he scores (flattest throw each time)
    for m in np.arange(DIRECT_MPH, 70, -0.5):
        a = solve_angle(REL, m, 0, 30); p = play(REL, m, a)
        if p["margin"] < 0: out["arm_mph"] = round(float(m), 1); break
    return out

def samples(T, P, t0, hz=120):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    pts = np.stack([np.interp(tt, T, P[:, i]) for i in range(3)], 1)
    pts[-1] = P[-1]
    return {"t0": round(t0, 4), "hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(x, 3) for x in q] for q in pts.tolist()]}

if __name__ == "__main__":
    F = flips()
    out = {
        "assume": dict(catch_dist=CATCH_DIST, catch_angle=CATCH_ANGLE, crow_hop=CROW_HOP, exchange=EXCHANGE, tag=TAG,
                       throw_rpm=THROW_RPM, cd=CD, rho=RHO, r_react=R_REACT, r_vmax=R_VMAX, r_tau=R_TAU, r_dist=R_DIST,
                       slide_at=SLIDE_AT, slide_decel=SLIDE_DECEL, fly_la=FLY_LA, fly_rpm=FLY_RPM),
        "catch": [round(x, 3) for x in C.tolist()], "release": [round(x, 3) for x in REL.tolist()], "glove": GLOVE.tolist(),
        "throw_dist": round(THROW_DIST, 1), "score_t": round(SCORE_T, 3), "hang": round(HANG, 3), "fly_ev": round(FLY_EV, 1),
        "direct": dict(mph=DIRECT_MPH, ang=round(DIRECT_ANG, 2), flight=round(DIRECT["flight"], 3), glove_t=round(DIRECT["glove_t"], 3),
                       tag_t=round(DIRECT["tag_t"], 3), runner_at_tag=round(DIRECT["runner_at_tag"], 2), margin=round(DIRECT["margin"], 3),
                       apex=round(DIRECT["apex"], 1), arrive_mph=round(DIRECT["arrive_mph"], 1)),
        "loop": dict(mph=round(LOOP_MPH, 1), ang=LOOP_ANGLE, flight=round(LOOP["flight"], 3), glove_t=round(LOOP["glove_t"], 3),
                     tag_t=round(LOOP["tag_t"], 3), runner_at_tag=round(LOOP["runner_at_tag"], 2), margin=round(LOOP["margin"], 3),
                     apex=round(LOOP["apex"], 1), arrive_mph=round(LOOP["arrive_mph"], 1)),
        "flips": F,
        "path": {"fly": samples(FT_, FP_, -HANG), "direct": samples(DIRECT["T"], DIRECT["P"], EXCHANGE), "loop": samples(LOOP["T"], LOOP["P"], EXCHANGE)},
        "runner": {"hz": 120, "s": [round(run_at(k / 120), 3) for k in range(0, 7 * 120)]},
    }
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
    show = {k: v for k, v in out.items() if k not in ("path", "runner")}
    print(json.dumps(show, indent=1))
