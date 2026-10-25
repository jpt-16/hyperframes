"""Three pitches for the pitch-sequencing video: a high fastball, a curveball, then a fastball the hitter isn't expecting.

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds; t = 0 is the release.

Ball flight: gravity + drag + spin lift (Magnus), 0.5 ms steps; rho 1.19 kg/m^3, Cd 0.35; lift CL = 1.5 S (S < 0.1)
else 0.09 + 0.6 S, S = r w / v, scaled by the spin efficiency, acting perpendicular to the velocity in the
direction the spin pushes (up for a four-seamer's backspin, down and to the glove side for a curveball's topspin).

All three come from the same right-handed release point (6.5 ft extension, 6.0 ft high, 1.9 ft to the arm side):
    high fastball   95 mph, 2,300 rpm backspin (efficiency 0.9), aimed at the top of the zone
    curveball       79 mph, 2,600 rpm topspin (efficiency 0.7, slightly to the glove side), aimed at the knees
    fastball        95 mph, same spin as the first, aimed belt-high on the inner third
A pro swing takes about 0.15 s from start to contact (reported 0.10-0.20 s), so the commit point is 0.15 s before
the ball reaches the contact point.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
G, RHO, R_BALL, M_BALL, CD = 9.80665, 1.19, 0.0366, 0.145, 0.35
K = 0.5 * RHO * np.pi * R_BALL ** 2 / M_BALL
RELEASE = np.array([-1.9, 6.0, -54.0])
PLATE_FRONT = -17 / 12
GLOVE_Z = 2.1
SWING = 0.15

PITCHES = {   # name: speed, rpm, spin efficiency, spin push direction, target at the front of the plate, contact depth
    "fb1": dict(mph=95.0, rpm=2300, eff=0.9, push=(-0.15, 1.0, 0.0), target=(-0.25, 3.4), contact=-1.3, label="High fastball"),
    "cb":  dict(mph=79.0, rpm=2600, eff=0.7, push=(0.35, -1.0, 0.0), target=(0.45, 1.75), contact=-0.5, label="Curveball"),
    "fb2": dict(mph=95.0, rpm=2300, eff=0.9, push=(-0.15, 1.0, 0.0), target=(-0.35, 2.75), contact=-1.3, label="Fastball"),
}

def cl(v, rpm):
    s = R_BALL * rpm * 2 * np.pi / 60 / max(v, 1e-6)
    return 1.5 * s if s < 0.1 else 0.09 + 0.6 * s

def fly(v0, pc, dt=0.0005):
    p = RELEASE * FT; v = np.array(v0, float) * FT; t = 0.0
    push = np.array(pc["push"], float); push /= np.linalg.norm(push)
    T, P, V = [0.0], [p / FT], [v / FT]
    while p[2] / FT < GLOVE_Z and t < 1.2:
        sp = np.linalg.norm(v); vh = v / sp
        d = push - vh * np.dot(push, vh); d /= np.linalg.norm(d)
        a = -K * CD * sp * v + K * cl(sp, pc["rpm"]) * pc["eff"] * sp * sp * d + np.array([0, -G, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        T.append(t); P.append(p / FT); V.append(v / FT)
    return np.array(T), np.array(P), np.array(V)

def at_z(T, P, V, z):
    i = np.argmax(P[:, 2] >= z); f = (z - P[i - 1, 2]) / (P[i, 2] - P[i - 1, 2])
    return T[i - 1] + f * (T[i] - T[i - 1]), P[i - 1] + f * (P[i] - P[i - 1]), V[i - 1] + f * (V[i] - V[i - 1])

def throw(pc):
    tx, ty = pc["target"]
    yaw, pit = np.arctan2(tx - RELEASE[0], -RELEASE[2]), 0.0
    for _ in range(40):
        d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
        T, P, V = fly(d * pc["mph"] * MPH / FT, pc)
        _, p, _ = at_z(T, P, V, PLATE_FRONT)
        yaw += (tx - p[0]) / 55 * 0.9; pit += (ty - p[1]) / 55 * 0.9
    return T, P, V, np.degrees(pit)

def samples(T, P, hz=240):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    pts = np.stack([np.interp(tt, T, P[:, i]) for i in range(3)], 1)
    return {"hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(x, 3) for x in q] for q in pts.tolist()]}

if __name__ == "__main__":
    out, raw = {"release": RELEASE.tolist(), "plate_front": PLATE_FRONT, "swing": SWING, "pitches": {}}, {}
    for name, pc in PITCHES.items():
        T, P, V, ang = throw(pc)
        tf, pf, vf = at_z(T, P, V, PLATE_FRONT)
        cz = PLATE_FRONT + pc["contact"]
        tc, pcon, _ = at_z(T, P, V, cz)
        ts = tc - SWING
        raw[name] = (T, P, V)
        out["pitches"][name] = dict(label=pc["label"], mph=pc["mph"], launch_deg=round(ang, 2), t_front=round(tf, 3), t_glove=round(float(T[-1]), 3),
                                    mph_front=round(float(np.linalg.norm(vf) * FT / MPH), 1), at_plate=[round(x, 2) for x in pf.tolist()],
                                    t_contact=round(tc, 3), contact=[round(x, 3) for x in pcon.tolist()], t_commit=round(ts, 3),
                                    z_commit=round(float(np.interp(ts, T, P[:, 2])), 2), path=samples(T, P))
    # how alike the fastball and the curveball look on the way in: the gap between them at the same distance from the plate
    Tf, Pf, Vf = raw["fb1"]; Tc, Pc, Vc = raw["cb"]
    def gap_at(z):
        _, a, _ = at_z(Tf, Pf, Vf, z); _, b, _ = at_z(Tc, Pc, Vc, z); return float(np.linalg.norm(a - b) * 12)
    zc = out["pitches"]["cb"]["z_commit"]
    out["gap"] = {"first_10ft_in": round(gap_at(RELEASE[2] + 10), 1), "half_in": round(gap_at((RELEASE[2] + PLATE_FRONT) / 2), 1),
                  "commit_in": round(gap_at(zc), 1), "plate_in": round(gap_at(PLATE_FRONT), 1),
                  "commit_dist_ft": round(PLATE_FRONT - zc, 1)}
    cb, f1, f2 = out["pitches"]["cb"], out["pitches"]["fb1"], out["pitches"]["fb2"]
    out["cb_later_s"] = round(cb["t_front"] - f1["t_front"], 3)
    out["cb_lower_in"] = round((f1["at_plate"][1] - cb["at_plate"][1]) * 12, 1)
    out["late_by_s"] = round(cb["t_contact"] - f2["t_contact"], 3)        # a swing timed for the curve, on the fastball
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
    show = {k: v for k, v in out.items() if k != "pitches"}
    show["pitches"] = {k: {kk: vv for kk, vv in v.items() if kk != "path"} for k, v in out["pitches"].items()}
    print(json.dumps(show, indent=1))
