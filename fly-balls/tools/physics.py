"""Fly balls and outfielder routes for the "reading fly balls" video.

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds; t = 0 is contact. Spray angle phi: 0 = straightaway center,
positive toward right field; the foul lines are at +/-45 deg. Fences: 330 ft at the lines, 375 in the alleys, 400 in
center (a typical modern park).

BALL FLIGHT: gravity + drag (Cd 0.40, which reproduces typical Statcast carry for fly balls) + Magnus lift from spin,
1 ms steps. Lift CL = 1.5 S (S < 0.1) else 0.09 + 0.6 S, S = r w / v, acting along (spin axis) x (velocity).
Pure backspin lifts the ball; tilting the spin axis adds a sideways push. Opposite-field fly balls tend to slice
toward the foul line and pulled ones hook toward it; most of the time the drift is modest. Here a 25 deg axis tilt
moves the landing point about a dozen feet over a ~330 ft fly: real, but no video-game curve. Wind isn't modeled.

THE FIELDERS (a model): ready until a 0.30 s reaction, then they accelerate toward their target with
v -> 28 ft/s (time constant 0.75 s; outfielders' top sprint speeds run ~27-30 ft/s), easing in to arrive.
Their read of the landing point starts from where the ball first looks like it's going (the same launch without
sidespin) and settles on the real landing point by ~2 s. A "wrong first step" fielder starts the wrong way for
0.45 s (in when it's going over his head, or back when it's in front of him), then has to stop and turn around.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
G, RHO, R_BALL, M_BALL, CD = 9.80665, 1.19, 0.0366, 0.145, 0.40
K = 0.5 * RHO * np.pi * R_BALL ** 2 / M_BALL
CONTACT = np.array([-0.6, 3.1, -2.2])      # bat on ball, in front of the plate
GLOVE_Y = 6.4                               # ball caught at about this height (arm up, on the run)
VMAX, TAU, REACT, WRONG_T = 28.0, 0.75, 0.30, 0.45
DECEL = 22.0                                # ft/s^2 a fielder can brake at (easing in, or stopping a wrong step)
HZ = 120

def fence(phi):                             # fence distance (ft) at spray angle phi (deg)
    a = abs(phi)
    return 400 - 25 * (a / 22.5) ** 1.3 if a <= 22.5 else 375 - 45 * ((a - 22.5) / 22.5) ** 1.15

def cl(v, rpm):
    s = R_BALL * rpm * 2 * np.pi / 60 / max(v, 1e-6)
    return 1.5 * s if s < 0.1 else 0.09 + 0.6 * s

def sprdir(phi):
    r = np.radians(phi); return np.array([np.sin(r), 0, -np.cos(r)])

def fly(ev, la, phi, rpm, tilt, dt=0.001):
    """tilt: spin-axis tilt (deg); + pushes the ball to the right of its path (toward the right-field line on a ball
    to right), - to the left."""
    d = sprdir(phi); la_ = np.radians(la)
    v = (d * np.cos(la_) + np.array([0, np.sin(la_), 0])) * ev * MPH
    back = np.cross(d, [0, 1, 0]); back /= np.linalg.norm(back)          # backspin axis: lifts the ball
    w = np.cos(np.radians(tilt)) * back + np.sin(np.radians(tilt)) * np.array([0, -1.0, 0])   # tilt toward vertical
    w /= np.linalg.norm(w)
    p, T, P = CONTACT * FT, [0.0], [CONTACT.copy()]
    while True:
        sp = np.linalg.norm(v); f = np.cross(w, v / sp); f /= max(np.linalg.norm(f), 1e-9)
        a = -K * CD * sp * v + K * cl(sp, rpm) * sp * sp * f + np.array([0, -G, 0])
        v = v + a * dt; p = p + v * dt; T.append(T[-1] + dt); P.append(p / FT)
        if p[1] <= 0: break
    T, P = np.array(T), np.array(P)
    return T, P, w

def descend_to(T, P, y):
    i = len(P) - 1
    while P[i - 1][1] < y: i -= 1
    f = (y - P[i - 1][1]) / (P[i][1] - P[i - 1][1]); return float(T[i - 1] + f * (T[i] - T[i - 1])), P[i - 1] + f * (P[i] - P[i - 1])

def at(T, P, t):
    return np.array([np.interp(t, T, P[:, k]) for k in range(3)])

def field_pos(phi, r): return sprdir(phi) * r

def route(start, catch_pt, naive_pt, t_catch, wrong=False, t_end=7.0, judge=None):
    """Fielder positions on the ground over time. Returns arrays (t, x, z, speed) and how far short he was at t_catch."""
    tt = np.arange(0, t_end + 1e-9, 1 / HZ)
    p = start[[0, 2]].astype(float).copy(); v = np.zeros(2); out = []
    goal_dir = (catch_pt - start)[[0, 2]]; goal_dir /= np.linalg.norm(goal_dir)
    caught = False; short = None
    for t in tt:
        if t >= REACT:
            if wrong and t < REACT + WRONG_T:
                tgt = p - goal_dir * 30                          # commits the wrong way
            else:
                w = np.clip((t - 0.5) / 1.6, 0, 1); w = w * w * (3 - 2 * w)
                tgt = (naive_pt * (1 - w) + catch_pt * w)[[0, 2]]
            dvec = tgt - p; dist = np.linalg.norm(dvec)
            vdes = dvec / max(dist, 1e-6) * min(VMAX, np.sqrt(2 * DECEL * max(dist - 0.5, 0)))
            dv = vdes - v
            if np.dot(vdes, v) < 0 or np.linalg.norm(vdes) < np.linalg.norm(v):    # braking / turning around
                step = min(np.linalg.norm(dv), DECEL / HZ); v = v + dv / max(np.linalg.norm(dv), 1e-9) * step
            else:
                v = v + dv * min(1.0, 1 / (TAU * HZ))
            p = p + v / HZ
        if short is None and t >= t_catch:
            short = float(np.linalg.norm(p - (catch_pt if judge is None else judge)[[0, 2]]))
        out.append((t, p[0], p[1], np.linalg.norm(v)))
    o = np.array(out)
    return o, short

def gait(o):                                                     # running phase: one cycle (two steps) per ~12 ft at speed
    sp = o[:, 3]; L = 4.0 + 8.0 * np.clip(sp / VMAX, 0, 1)
    return np.cumsum(sp / L) / HZ

def samples(T, P, hz=HZ):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    pts = np.stack([np.interp(tt, T, P[:, k]) for k in range(3)], 1)
    return {"hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(x, 2) for x in q] for q in pts.tolist()]}

START = {"CF": field_pos(1.0, 318), "LF": field_pos(-25.0, 292), "RF": field_pos(24.0, 292)}
#        name: exit mph, launch deg, spray deg, backspin rpm, axis tilt deg, who fields it, others who move
BALLS = {
    "deep":    dict(ev=102.0, la=22.0, phi=3.0, rpm=2100, tilt=0, f="CF", label="Over his head"),
    "shallow": dict(ev=71.0, la=35.0, phi=-4.0, rpm=2400, tilt=0, f="CF", label="In front of him"),
    "gap":     dict(ev=90.0, la=27.0, phi=16.0, rpm=2200, tilt=0, f="CF", help="RF", label="Right-center gap"),
    "lfline":  dict(ev=88.0, la=28.0, phi=-30.0, rpm=2300, tilt=-8, f="LF", label="Hooking toward the line"),
    "rfslice": dict(ev=88.0, la=29.0, phi=26.0, rpm=2400, tilt=8, f="RF", label="Slicing toward the line"),
}

if __name__ == "__main__":
    out = {"assume": dict(cd=CD, vmax=VMAX, tau=TAU, react=REACT, wrong_t=WRONG_T, decel=DECEL, glove_y=GLOVE_Y),
           "contact": CONTACT.tolist(), "start": {k: [round(x, 2) for x in v] for k, v in START.items()},
           "fence": [[round(float(np.radians(a)), 4), round(fence(a), 1)] for a in range(-45, 46)], "balls": {}}
    for name, b in BALLS.items():
        T, P, w = fly(b["ev"], b["la"], b["phi"], b["rpm"], b["tilt"])
        T0, P0, _ = fly(b["ev"], b["la"], b["phi"], b["rpm"], 0)     # the same launch without sidespin: where it first looks like it's going
        tc, pc = descend_to(T, P, GLOVE_Y); land = P[-1]; naive = descend_to(T0, P0, GLOVE_Y)[1]
        st = START[b["f"]]
        r_ok, s_ok = route(st, pc, naive, tc)
        r_bad, s_bad = route(st, pc, naive, tc, wrong=True)
        # a fielder who runs straight to where it first looks like it's going and never adjusts
        r_naive, s_naive = route(st, naive, naive, tc, judge=pc)
        rec = dict(label=b["label"], ev=b["ev"], la=b["la"], phi=b["phi"], rpm=b["rpm"], tilt=b["tilt"], fielder=b["f"],
                   t_catch=round(tc, 3), catch=[round(x, 2) for x in pc], land=[round(x, 2) for x in land], t_land=round(float(T[-1]), 3),
                   naive=[round(x, 2) for x in naive], drift_ft=round(float(np.linalg.norm((pc - naive)[[0, 2]])), 1),
                   dist=round(float(np.linalg.norm(land[[0, 2]])), 1), apex=round(float(P[:, 1].max()), 1),
                   spin_axis=[round(x, 3) for x in w], path=samples(T, P), path_straight=samples(T0, P0) if b["tilt"] else None,
                   run_ft=round(float(np.linalg.norm((pc - st)[[0, 2]])), 1),
                   short_ok=round(s_ok, 1), short_bad=round(s_bad, 1), short_naive=round(s_naive, 1),
                   routes={k: {"x": [round(x, 2) for x in r[:, 1]], "z": [round(x, 2) for x in r[:, 2]], "v": [round(x, 2) for x in r[:, 3]],
                               "ph": [round(x, 3) for x in gait(r)]} for k, r in (("ok", r_ok), ("bad", r_bad), ("naive", r_naive))})
        # when does the correct-read fielder get there, and where is the wrong-step fielder at the catch?
        d_ok = np.hypot(r_ok[:, 1] - pc[0], r_ok[:, 2] - pc[2]); rec["t_arrive"] = round(float(r_ok[np.argmax(d_ok < 1.5), 0]), 2)
        d_bad = np.hypot(r_bad[:, 1] - pc[0], r_bad[:, 2] - pc[2]); hit = d_bad < 1.5
        rec["t_arrive_bad"] = round(float(r_bad[np.argmax(hit), 0]), 2) if hit.any() else None
        if b.get("help"):
            h = START[b["help"]]; r_h, s_h = route(h, pc + (h - pc) * 0.25, pc + (h - pc) * 0.25, tc)   # converges, then backs him up
            rec["helper"] = b["help"]; rec["routes"]["help"] = {"x": [round(x, 2) for x in r_h[:, 1]], "z": [round(x, 2) for x in r_h[:, 2]], "v": [round(x, 2) for x in r_h[:, 3]], "ph": [round(x, 3) for x in gait(r_h)]}
        out["balls"][name] = rec
        print(f"{name:8s} {b['label']:26s} {rec['dist']:5.0f} ft (fence {fence(np.degrees(np.arctan2(land[0], -land[2]))):.0f})  apex {rec['apex']:4.0f}  "
              f"hang {rec['t_land']:.2f}s  catch {tc:.2f}s at {np.linalg.norm(pc[[0,2]]):.0f} ft  run {rec['run_ft']:.0f} ft  "
              f"drift {rec['drift_ft']:.1f} ft  ok short {s_ok:.1f} (there at {rec['t_arrive']:.2f}s)  wrong-step short {s_bad:.1f}  never-adjust short {s_naive:.1f}")
    out["hz"] = HZ
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
