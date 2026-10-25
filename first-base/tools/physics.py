"""The play for the dive-or-run-through video: a ground ball in the hole, the throw to first, and one batter-runner
going down the line two ways (running through the bag, or a head-first dive).

    python3 tools/physics.py        # writes assets/play.json (read by build.py and assets/field.js)

Field frame (same as the other baseball videos): home plate's back point at the origin, +x toward the first-base
side, -z toward center field, y up, feet and seconds. t = 0 is the runner's first step out of the box.

THIS IS A MODEL, NOT A MEASUREMENT. It shows the trade-off; it does not settle which is faster.
  Sprint (both runners, identical): v(t) = VMAX (1 - exp(-t / TAU)), VMAX = 27 ft/s (MLB average Statcast sprint
    speed), TAU = 0.8 s. Same start point, same line, same throw.
  Running through: the bag is touched when the foot lands on it, FOOT ft ahead of the hips; full speed is kept
    through the bag, then he eases up past it and veers into foul ground.
  Head-first dive: one setup stride (STRIDE s) lowers him and costs speed (KEEP of his speed is left at takeoff);
    then he is in the air (gravity only) until his chest lands, his arms reaching out in front, then he slides on
    the dirt (friction MU). "Well timed": he leaves the ground exactly where his hand reaches the bag as his chest
    lands (no time lost sliding). The hand ends REACH ft ahead of the hips; FOOT and REACH are measured on the
    3D figure, so the animation and the model touch the bag at the same moment.
  How much speed the setup stride really costs is not known precisely, and it decides the result: with no loss the
  model dive wins by the reach, with more loss it loses. KEEP is an assumption; the video only says the two are too
  close to call in the model, and quotes the measured study for which is faster.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
G = 32.17
HZ = 240
VMAX, TAU = 27.0, 0.8
FOOT = 1.38            # foot ahead of the hips when it lands (3D figure, runPose at foot strike)
REACH0 = 1.3           # hand ahead of the hips while running (arms pumping)
REACH = 3.51           # hand ahead of the hips, body flat, reaching arm straight out (3D figure)
KEEP = 0.85            # share of his speed left after the setup stride (assumption; see the sensitivity printout)
STRIDE = 0.24          # the setup stride before takeoff (one step at ~4.2 steps/s)
HIP_RUN, HIP_TAKEOFF, HIP_FLAT = 3.0, 2.55, 0.55   # hip height: running, at takeoff, lying flat
VY0 = 2.0              # small upward push at takeoff (ft/s)
MU = 0.5               # sliding friction, uniform on dirt
T_END = 7.5

B1 = np.array([63.64, 0, -63.64])
LINE = B1 / np.linalg.norm(B1)
FOUL = np.array([1, 0, 1]) / np.sqrt(2)                      # perpendicular to the line, toward foul ground
START = np.array([-2.4, 0, -0.7])                            # first step out of the right-handed batter's box
AIM = B1 + 0.3 * FOUL                                        # the foul-side half of the bag
DIR = (AIM - START) / np.linalg.norm(AIM - START)
S_BAG = float(np.linalg.norm(AIM - START) - 0.625)           # the near edge of the bag (15 in square), along his path

t = np.arange(0, T_END + 1e-9, 1 / HZ)
def sprint_v(t): return VMAX * (1 - np.exp(-np.maximum(t, 0) / TAU))
def sprint_s(t): t = np.maximum(t, 0); return VMAX * (t - TAU * (1 - np.exp(-t / TAU)))
def cross(s, target):
    if s[-1] < target: return np.inf
    i = int(np.argmax(s >= target)); f = (target - s[i - 1]) / (s[i] - s[i - 1]); return float(t[i - 1] + f / HZ)

# ---------------------------------------------------------------- running through
s_run, v_run = sprint_s(t), sprint_v(t)
T_RUN = cross(s_run + FOOT, S_BAG)
s_r = np.zeros_like(t); v_r = np.zeros_like(t)
for i in range(1, len(t)):
    vv = v_run[i] if s_r[i - 1] < S_BAG + 6 else max(0.0, v_r[i - 1] - 11.0 / HZ)
    v_r[i] = vv; s_r[i] = s_r[i - 1] + vv / HZ
lat_r = 7.0 * np.clip((s_r - S_BAG - 4) / 34, 0, 1) ** 2 * (3 - 2 * np.clip((s_r - S_BAG - 4) / 34, 0, 1))   # veers into foul ground
T_RUN = cross(s_r + FOOT, S_BAG)

# gait: cycle length (two steps) grows with speed; feet land at phase 0.27 (left) and 0.77 (right)
def phase(v):
    L = 4.0 + 8.5 * v / VMAX
    return np.cumsum(v / L) / HZ
ph_r = phase(v_r)
k = int(round(T_RUN * HZ)); OFF = (0.77 - ph_r[k]) % 1.0   # a foot lands on the bag at the touch
ph_r = ph_r + OFF

# ---------------------------------------------------------------- head-first dive
def dive(t_plant, keep=None):
    keep = KEEP if keep is None else keep
    s = np.zeros_like(t); v = np.zeros_like(t); y = np.full_like(t, HIP_RUN)
    t0, vy, land = t_plant - STRIDE, VY0, None
    for i in range(1, len(t)):
        ti = t[i]
        if ti <= t0: vv = sprint_v(ti)
        elif ti <= t_plant:                                  # the setup stride: lower the hips, lose some speed
            u = (ti - t0) / STRIDE; vv = sprint_v(t0) * (1 - (1 - keep) * u); y[i] = HIP_RUN + (HIP_TAKEOFF - HIP_RUN) * u
        elif land is None:                                   # in the air: gravity only
            vv = v[i - 1]; vy -= G / HZ; y[i] = y[i - 1] + vy / HZ
            if y[i] <= HIP_FLAT: y[i] = HIP_FLAT; land = ti
        else:                                                # sliding on the dirt
            vv = max(0.0, v[i - 1] - MU * G / HZ); y[i] = HIP_FLAT
        v[i] = vv; s[i] = s[i - 1] + vv / HZ
    u = np.clip((t - t_plant) / ((land or t_plant + 0.4) - t_plant), 0, 1)
    reach = REACH0 + (REACH - REACH0) * u * u * (3 - 2 * u)  # arms reach out through the flight
    return s, v, y, reach, land
def touch(s, reach): return cross(s + reach, S_BAG)
def well_timed(keep=None):                                   # the hand reaches the bag just as the chest lands
    lo, hi = 2.5, T_RUN + 0.3
    for _ in range(50):
        mid = (lo + hi) / 2; s_, v_, y_, r_, land = dive(mid, keep)
        if touch(s_, r_) > land: lo = mid                    # landed short and slid: he left too early
        else: hi = mid                                       # hand there while still in the air: leave earlier
    return (lo + hi) / 2
T_PLANT = well_timed()
s_d, v_d, y_d, r_d, T_LAND = dive(T_PLANT)
T_DIVE = touch(s_d, r_d)
T_STOP = float(t[np.argmax((t > T_LAND) & (v_d <= 0))])
ph_d = np.where(t <= T_PLANT, phase(np.where(t <= T_PLANT, v_d, 0)) + OFF, np.nan)
ph_d = np.where(np.isnan(ph_d), ph_d[int(T_PLANT * HZ)], ph_d)

def steps(ph, until):
    out = []
    for i in range(1, len(t)):
        if t[i] > until: break
        for f in (0.27, 0.77):
            if np.floor(ph[i - 1] - f) != np.floor(ph[i] - f): out.append(round(float(t[i]), 3))
    return out

# ---------------------------------------------------------------- the ground ball and the throw (same for both runners)
RHO, R_BALL, M_BALL, CD = 1.19, 0.0366, 0.145, 0.35
KD = 0.5 * RHO * np.pi * R_BALL ** 2 / M_BALL
CONTACT_T = -0.28                                            # bat on ball, just before his first step
CONTACT = np.array([0.4, 2.6, -1.6])
FIELD = np.array([-37.0, 0.0, -127.0])                       # the shortstop backhands it deep in the hole
SS0 = np.array([-31.0, 0.0, -116.0])
EXCH = 0.78                                                  # glove -> release (plant and throw)
GLOVE = np.array([59.66, 2.2, -65.2])                         # the first baseman's glove at full stretch (measured on the 3D figure)
THROW_MPH = 84.0
MARGIN = 0.03                                                # the throw arrives a hair after the run-through touch

def fly(p0, v0, dt=0.0005):
    p, v, T, P = p0 * 0.3048, v0 * 0.3048, [0.0], [p0.copy()]
    while True:
        sp = np.linalg.norm(v); a = -KD * CD * sp * v + np.array([0, -9.80665, 0])
        v = v + a * dt; p = p + v * dt; T.append(T[-1] + dt); P.append(p / 0.3048)
        if np.dot(p / 0.3048 - GLOVE, (GLOVE - p0) * np.array([1, 0, 1])) >= 0 or T[-1] > 3: return np.array(T), np.array(P)
REL = FIELD + np.array([3.0, 5.9, 1.8])
def throw(ang):
    d = (GLOVE - REL) * np.array([1, 0, 1]); d /= np.linalg.norm(d)
    v0 = (d * np.cos(ang) + np.array([0, np.sin(ang), 0])) * THROW_MPH * 1.4667
    return fly(REL, v0)
lo_a, hi_a = -0.1, 0.3
for _ in range(50):
    m = (lo_a + hi_a) / 2; T_, P_ = throw(m)
    if P_[-1][1] < GLOVE[1]: lo_a = m
    else: hi_a = m
T_TH, P_TH = throw((lo_a + hi_a) / 2)
FLIGHT = float(T_TH[-1])
T_ARRIVE = T_RUN + MARGIN                                    # bang-bang: the ball pops the glove a hair after his foot
T_RELEASE = T_ARRIVE - FLIGHT
T_FIELD = T_RELEASE - EXCH
# ground ball: four hops, slowing, from the bat to the shortstop's glove
def grounder(n=None):
    tt = np.arange(CONTACT_T, T_FIELD + 1e-9, 1 / 120)
    u = (tt - CONTACT_T) / (T_FIELD - CONTACT_T)
    k_ = 1.6; d = (1 - np.exp(-k_ * u)) / (1 - np.exp(-k_))  # it slows down along the ground
    xy = CONTACT * (1 - d)[:, None] + (FIELD + np.array([0, 0.6, 0])) * d[:, None]
    hops = [(0.0, 0.16, 5.5), (0.16, 0.42, 3.2), (0.42, 0.68, 1.6), (0.68, 1.0, 0.7)]
    y = np.zeros_like(u)
    for a, b, h in hops:
        m = (u >= a) & (u <= b); w = (u[m] - a) / (b - a); y[m] = 4 * h * w * (1 - w)
    y[u < 0.16] = CONTACT[1] * (1 - u[u < 0.16] / 0.16) + y[u < 0.16]
    xy[:, 1] = np.maximum(y, 0) + 0.12 + 0.5 * d
    return tt, xy
TG, PG = grounder()
# the throw that gets away (risk scene): off the end of the glove, skipping into foul ground behind the bag
def away():
    d = (P_TH[-1] - P_TH[-20]) * np.array([1, 0, 1]); d /= np.linalg.norm(d)
    d = d * 0.85 + FOUL * 0.55; d /= np.linalg.norm(d)
    tt = np.arange(0, 2.4, 1 / 120); dist = 55 * (1 - np.exp(-tt / 0.9)) * 1.0
    y = np.abs(np.sin(np.minimum(tt, 1.6) * 6.0)) * 1.4 * np.exp(-tt * 1.8) + 0.12
    y[:6] = np.linspace(GLOVE[1], y[6], 6)
    return tt, GLOVE * np.array([1, 0, 1]) + d[None, :] * dist[:, None] + np.outer(y, [0, 1, 0])
TA, PA = away()

def samples(T, P, t0, hz=120):
    tt = np.arange(0, T[-1] + 1e-9, 1 / hz)
    pts = np.stack([np.interp(tt, T, P[:, i]) for i in range(3)], 1)
    return {"t0": round(float(t0), 4), "hz": hz, "dur": round(float(T[-1]), 4), "p": [[round(x, 3) for x in q] for q in pts.tolist()]}
R3 = lambda a: [round(float(x), 3) for x in a]
rnd = lambda a, n=3: [round(float(x), n) for x in a]

if __name__ == "__main__":
    i_r, i_d = int(round(T_RUN * HZ)), int(round(T_DIVE * HZ))
    out = {
        "assume": dict(vmax=VMAX, tau=TAU, foot=FOOT, reach=REACH, reach0=REACH0, keep=KEEP, stride=STRIDE, mu=MU, throw_mph=THROW_MPH, hip_flat=HIP_FLAT),
        "start": R3(START), "dir": R3(DIR), "foul": R3(FOUL), "s_bag": round(S_BAG, 3), "b1": R3(B1),
        "t_run": round(T_RUN, 4), "t_dive": round(T_DIVE, 4), "t_plant": round(T_PLANT, 4), "t_land": round(T_LAND, 4), "t_stop": round(T_STOP, 4),
        "v_touch_run": round(float(v_r[i_r]), 1), "v_touch_dive": round(float(v_d[i_d]), 1), "v_plant": round(float(v_d[int(T_PLANT * HZ)]), 1),
        "plant_dist": round(S_BAG - float(s_d[int(T_PLANT * HZ)]), 2), "reach_gain": round(REACH - FOOT, 2),
        "hz": HZ, "run": {"s": rnd(s_r), "v": rnd(v_r, 2), "ph": rnd(ph_r, 4), "lat": rnd(lat_r)},
        "dive": {"s": rnd(s_d), "v": rnd(v_d, 2), "ph": rnd(ph_d, 4), "y": rnd(y_d), "reach": rnd(r_d)},
        "steps_run": steps(ph_r, T_RUN + 1.6), "steps_dive": steps(ph_d, T_PLANT + 0.01),
        "contact_t": CONTACT_T, "t_field": round(T_FIELD, 4), "t_release": round(T_RELEASE, 4), "t_arrive": round(T_ARRIVE, 4),
        "field": R3(FIELD), "ss0": R3(SS0), "release": R3(REL), "glove": R3(GLOVE),
        "path": {"grounder": samples(TG - CONTACT_T, PG, CONTACT_T), "throw": samples(T_TH, P_TH, T_RELEASE), "away": samples(TA, PA, T_ARRIVE)},
    }
    json.dump(out, open(os.path.join(HERE, "..", "assets", "play.json"), "w"))
    show = {k: v for k, v in out.items() if k not in ("run", "dive", "path")}
    print(json.dumps(show, indent=1))
    # how much the outcome hinges on the setup stride
    print("sensitivity (speed kept after the setup stride -> dive minus run, s):")
    for kp in (1.0, 0.95, 0.9, 0.85, 0.8):
        tp = well_timed(kp); sd, vd, yd, rd, ld = dive(tp, kp); print(f"  {kp:.2f}: {touch(sd, rd) - T_RUN:+.3f}")
