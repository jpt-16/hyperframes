"""The pitch, the swing timing and the batted ball for the 100 mph video.

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. t = 0 is the release.

Ball flight: gravity + drag + backspin lift (Magnus), 1 ms steps. rho = 1.19 kg/m^3, Cd 0.35 for the pitch
(pitch-tracking range), 0.40 for the batted ball; lift CL = 1.5 S (S < 0.1) else 0.09 + 0.6 S, S = r w / v.

The pitch: 100 mph out of the hand, four-seam backspin 2,300 rpm, released 6.5 ft in front of the rubber
(so 54 ft from the back of the plate), 6.0 ft high, 1.9 ft to the arm side, aimed so it crosses the front of
the plate belt-high over the middle. At a constant 100 mph, 60 ft 6 in takes 60.5 / 146.67 = 0.41 s.

The swing: a typical pro swing takes about 0.15 s from start to contact (reported 0.10-0.20 s), so it has to
start about 0.15 s before the ball reaches the contact point, out in front of the plate.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FT, MPH = 0.3048, 0.44704
G, RHO, R_BALL, M_BALL = 9.80665, 1.19, 0.0366, 0.145
K = 0.5 * RHO * np.pi * R_BALL ** 2 / M_BALL

V0_MPH = 100.0
RPM = 2300
RUBBER = 60.5
EXTENSION = 6.5
RELEASE = np.array([-1.9, 6.0, -(RUBBER - EXTENSION)])
PLATE_FRONT = -17 / 12                      # the plate is 17 in deep; its front edge faces the pitcher
TARGET = np.array([0.0, 2.6, PLATE_FRONT])  # belt-high, middle of the plate, at the front edge
CONTACT_Z = PLATE_FRONT - 1.3               # contact out in front of the plate
GLOVE_Z = 2.1                               # the catcher's glove, behind the plate (pitches that are taken)
SWING = 0.15                                # start of the swing -> contact
RECOGNIZE = 0.10                            # roughly the first stretch of flight: picking the ball up out of the hand
EV_MPH, LA, SPRAY, BAT_RPM = 104.0, 17.0, -9.0, 1900   # the line drive off the bat (spray: degrees toward left field)

def cl(v, rpm):
    s = R_BALL * rpm * 2 * np.pi / 60 / max(v, 1e-6)
    return 1.5 * s if s < 0.1 else 0.09 + 0.6 * s

def fly(p0, v0, rpm, cd, stop, dt=0.0005):
    p = np.array(p0, float) * FT; v = np.array(v0, float) * FT; t = 0.0
    T, P, V = [0.0], [p / FT], [v / FT]
    while True:
        sp = np.linalg.norm(v)
        up = np.array([0.0, 1.0, 0.0]) - (v / sp) * (v[1] / sp); up /= np.linalg.norm(up)
        a = -K * cd * sp * v + K * cl(sp, rpm) * sp * sp * up + np.array([0, -G, 0])
        v = v + a * dt; p = p + v * dt; t += dt
        T.append(t); P.append(p / FT); V.append(v / FT)
        if stop(p / FT, v / FT, t): return np.array(T), np.array(P), np.array(V)

def pitch(yaw, pit):
    d = np.array([np.sin(yaw) * np.cos(pit), np.sin(pit), np.cos(yaw) * np.cos(pit)])
    return fly(RELEASE, d * V0_MPH * MPH / FT, RPM, 0.35, lambda p, v, t: p[2] >= GLOVE_Z or t > 1)

def at_z(T, P, V, z):
    i = np.argmax(P[:, 2] >= z); f = (z - P[i - 1, 2]) / (P[i, 2] - P[i - 1, 2])
    return T[i - 1] + f * (T[i] - T[i - 1]), P[i - 1] + f * (P[i] - P[i - 1]), V[i - 1] + f * (V[i] - V[i - 1])

# aim: solve yaw and pitch angle so the ball crosses the front of the plate at TARGET
yaw, pit = np.arctan2(-RELEASE[0], -RELEASE[2]), -0.03
for _ in range(30):
    T, P, V = pitch(yaw, pit)
    _, p, _ = at_z(T, P, V, PLATE_FRONT)
    yaw += (TARGET[0] - p[0]) / 55 * 0.9; pit += (TARGET[1] - p[1]) / 55 * 0.9
T, P, V = pitch(yaw, pit)
t_front, p_front, v_front = at_z(T, P, V, PLATE_FRONT)
t_contact, p_contact, v_contact = at_z(T, P, V, CONTACT_Z)
mph = lambda v: float(np.linalg.norm(v) * FT / MPH)

# the batted ball
sp = np.radians(SPRAY); la = np.radians(LA)
d = np.array([np.sin(sp) * np.cos(la), np.sin(la), -np.cos(sp) * np.cos(la)])
BT, BP, BV = fly(p_contact, d * EV_MPH * MPH / FT, BAT_RPM, 0.40, lambda p, v, t: p[1] <= 0 or t > 6)

def samples(T, P, hz=240):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    pts = np.stack([np.interp(tt, T, P[:, i]) for i in range(3)], 1)
    return {"hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(x, 3) for x in q] for q in pts.tolist()]}

if __name__ == "__main__":
    inch_per_ms = float(np.linalg.norm(v_contact)) * 12 / 1000
    out = {
        "v0_mph": V0_MPH, "fps": round(V0_MPH * MPH / FT, 1), "rubber": RUBBER, "extension": EXTENSION,
        "const_time": round(RUBBER / (V0_MPH * MPH / FT), 3),
        "release": RELEASE.tolist(), "plate_front": PLATE_FRONT, "release_dist": round(-RELEASE[2] + PLATE_FRONT, 1),
        "t_front": round(t_front, 3), "t_glove": round(float(T[-1]), 3), "glove": [round(x, 3) for x in P[-1].tolist()], "t_contact": round(t_contact, 3), "contact": [round(x, 3) for x in p_contact.tolist()],
        "mph_front": round(mph(v_front), 1), "mph_contact": round(mph(v_contact), 1),
        "swing": SWING, "t_swing": round(t_contact - SWING, 3), "z_swing": round(float(np.interp(t_contact - SWING, T, P[:, 2])), 2), "recognize": RECOGNIZE,
        "inch_per_ms": round(inch_per_ms, 2), "drop_ft": round(float(RELEASE[1] - p_front[1]), 2),
        "ev_mph": EV_MPH, "la": LA, "spray": SPRAY,
        "path": {"pitch": samples(T, P), "hit": samples(BT, BP, 120)},
    }
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
    print(json.dumps({k: v for k, v in out.items() if k != "path"}, indent=1))
