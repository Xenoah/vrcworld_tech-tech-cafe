"""Generate the experience layout (sky deck, DATA STREAM ride, KOMO route).

Writes Unity/Assets/TheCommons/Data/experience_layout.json (Unity X / Y up / Z,
metres) for CommonsExperienceBuilder and Documentation/experience_validation.json.
The ride is a closed centripetal Catmull-Rom spline; the checks below use the
same evaluation the Unity builder bakes (16 samples per control segment).

    python3 Blender/build_experience_layout.py
"""
from pathlib import Path
import json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
pts = []; spd = []; cue = []
def add(x, y, z, s, c=''):
    pts.append((x, y, z)); spd.append(s); cue.append(c)

# Deck dock (deck centre 14,120,9; floor top 120)
add(26.0,120.08,3.0,0.8,'dock')
add(26.0,120.1,6.0,2.6)
add(26.0,120.16,9.0,4.0,'launch')
# pre-show lap around the holo planet, centre (14,*,9) r 11.5, 35deg -> 395deg
n=11
for i in range(n):
    a=math.radians(20.0+360.0*i/(n-1))
    add(14.0+11.5*math.cos(a),122.4+3.0*i/(n-1),9.0+11.5*math.sin(a),5.5 if i==0 else 6.0)
add(23.6,125.4,22.5,7.0)
add(15.0,124.6,31.5,8.0)
add(4.0,121.6,30.5,8.5)
add(-7.0,116.4,28.4,9.0,'dive')
# descending helix centre (-18,*,12) r16, counter-clockwise in x-z, 70deg -> 270deg+360
cx,cz,r=-18.0,12.0,16.0
a0=90.0; a1=270.0+720.0; n=31
for i in range(n):
    a=math.radians(a0+(a1-a0)*i/(n-1))
    y=111.0-(111.0-25.0)*i/(n-1)
    add(cx+r*math.cos(a),y,cz+r*math.sin(a),9.5+2.0*math.sin(math.pi*i/(n-1)))
add(-8.5,21.0,-4.5,9.5)
add(0.0,16.0,-6.8,9.0)
add(7.0,12.0,-6.0,8.0)
add(12.4,9.2,-3.4,7.0,'phase')
add(13.6,7.9,0.6,6.0)
add(14.1,7.3,4.2,5.0)
# one rising lap of the atrium, ellipse centre (14.3,*,8.5) rx 3.0 rz 2.3, -45deg -> 315deg
n=13
for i in range(n):
    a=math.radians(-45.0+360.0*i/(n-1))
    add(14.3+2.8*math.cos(a),6.95+0.65*i/(n-1),8.4+2.5*math.sin(a),4.5,'scan' if i==1 else '')
add(18.5,8.3,9.3,5.4,'roof')
add(21.0,9.8,11.2,6.0)
add(24.2,12.2,12.6,6.8)
add(28.6,15.2,13.2,7.5)
add(33.8,18.4,12.8,8.0,'skyline')
add(39.6,21.2,12.5,8.0)
add(44.6,23.6,13.6,7.5)
add(47.2,25.4,18.0,6.8)
add(48.2,26.8,22.6,6.5)
add(51.2,27.8,25.0,6.5)
add(56.0,28.8,25.0,7.0)
add(60.0,29.7,24.8,6.5)
add(62.6,30.6,22.2,6.5)
add(63.4,31.6,17.5,7.5)
add(63.3,33.0,10.0,7.5)
add(63.5,34.0,5.0,6.5)
add(64.6,34.8,1.2,6.5)
add(67.2,35.6,-0.9,7.0)
add(71.0,36.4,-1.3,7.5)
add(75.0,37.5,-1.0,8.5)
add(81.0,40.0,-1.5,9.0)
# climbing helix centre (95,*,10) r14, counter-clockwise, 250deg -> 90deg+360
cx,cz,r=95.0,10.0,14.0
a0=250.0; a1=450.0+360.0; n=19
for i in range(n):
    a=math.radians(a0+(a1-a0)*i/(n-1))
    y=43.0+(100.0-43.0)*i/(n-1)
    add(cx+r*math.cos(a),y,cz+r*math.sin(a),8.0-1.2*math.sin(math.pi*i/(n-1)),'stars' if i==9 else '')
add(81.0,103.5,23.5,7.5)
add(67.0,107.5,17.0,7.5)
add(55.0,111.5,7.0,7.5)
add(45.0,115.0,-3.5,7.0,'approach')
add(35.5,118.2,-10.5,6.0)
add(28.6,120.3,-8.5,4.5)
add(26.2,120.12,-3.0,2.5)

pts = np.array(pts); spd = np.array(spd); N = len(pts)
def cr(t):
    # Centripetal Catmull-Rom (alpha .5), closed loop. Mirrors CommonsExperienceBuilder.Centripetal.
    i=int(math.floor(t))%N;u=t-math.floor(t)
    p0,p1,p2,p3=pts[(i-1)%N],pts[i],pts[(i+1)%N],pts[(i+2)%N]
    def kn(a,b): return max(np.linalg.norm(b-a)**.5,1e-4)
    t0=0.0;t1=t0+kn(p0,p1);t2=t1+kn(p1,p2);t3=t2+kn(p2,p3)
    tt=t1+(t2-t1)*u
    a1=(t1-tt)/(t1-t0)*p0+(tt-t0)/(t1-t0)*p1
    a2=(t2-tt)/(t2-t1)*p1+(tt-t1)/(t2-t1)*p2
    a3=(t3-tt)/(t3-t2)*p2+(tt-t2)/(t3-t2)*p3
    b1=(t2-tt)/(t2-t0)*a1+(tt-t0)/(t2-t0)*a2
    b2=(t3-tt)/(t3-t1)*a2+(tt-t1)/(t3-t1)*a3
    return (t2-tt)/(t2-t1)*b1+(tt-t1)/(t2-t1)*b2
def speed(t):
    i=int(math.floor(t))%N;u=t-math.floor(t);u=u*u*(3-2*u)
    return spd[i]*(1-u)+spd[(i+1)%N]*u

S = 16
DECK = {
    'center': [14.0, 120.0, 9.0], 'floor_radius': 18.0, 'field_radius': 18.3, 'field_height': 28.0, 'well_radius': 7.0,
    'arrival': [14.0, 120.1, -3.0], 'arrival_yaw': 0.0,
    'return_portal': [14.0, 121.25, -6.6], 'return_portal_yaw': 180.0,
    'return_destination': [20.0, 0.12, 2.0], 'return_destination_yaw': 0.0,
    'settings_panel': [9.2, 121.9, -6.0], 'settings_yaw': 180.0,
    'size_lab': [3.0, 121.5, 9.0], 'size_lab_yaw': -90.0,
    'planet': [14.0, 129.0, 9.0], 'planet_radius': 2.2,
    'dock_exit': [23.2, 120.1, 3.0], 'dock_exit_yaw': -60.0,
    'dock_board': [23.0, 123.3, 8.6], 'board_yaw': 90.0,
    'dock_rail_x': 24.75, 'dock_gate': [0.3, 6.2],
}
LIFT = {'portal': [20.0, 1.3, 3.45], 'yaw': 0.0, 'frame_width': 2.2,
        'destination': DECK['arrival'], 'destination_yaw': DECK['arrival_yaw']}
# Cue map: view-jack channel (0 warp, 1 glitch, 2 scan, 3 stars, 4 data rain, 7 dream), seconds, SFX id.
CUES = {'launch': (0, 1.6, 0), 'dive': (4, 9.0, 0), 'phase': (0, .8, -1), 'scan': (2, 8.0, -1),
        'roof': (0, .8, -1), 'skyline': (7, 5.0, -1), 'stars': (3, 14.0, -1), 'approach': (2, 3.0, 2)}
# KOMO activities: 0 greeter, 1 barista, 2 dj, 3 dancer, 4 stargazer, 5 reader, 6 lounger, 7 gallery.
KOMO = {
    'hub': [14.3, 3.4, 8.5], 'ride_every': 4, 'travel_speed': 1.6,
    'spots': [
        {'name': 'Greeter', 'activity': 0, 'position': [14.0, 1.4, 4.8], 'yaw': 180.0, 'door': [14.1, 2.4, 6.5]},
        {'name': 'Barista', 'activity': 1, 'position': [0.85, 1.45, 10.0], 'yaw': 90.0, 'door': [3.8, 2.8, 9.6]},
        {'name': 'Reader', 'activity': 5, 'position': [6.0, 6.3, 9.4], 'yaw': -90.0, 'door': [8.4, 6.6, 9.0]},
        {'name': 'DJ', 'activity': 2, 'position': [14.0, 6.3, 14.4], 'yaw': 180.0, 'door': [17.8, 6.8, 13.0]},
        {'name': 'Dancer', 'activity': 3, 'position': [14.0, 1.6, 12.6], 'yaw': 180.0, 'door': [14.0, 2.8, 10.4]},
        {'name': 'Gallery', 'activity': 7, 'position': [25.4, 1.5, 11.5], 'yaw': 90.0, 'door': [22.4, 3.0, 9.0]},
        {'name': 'Stargazer', 'activity': 4, 'position': [22.6, 6.4, 12.5], 'yaw': 90.0, 'door': [20.4, 7.0, 10.0]},
        {'name': 'Lounger', 'activity': 6, 'position': [14.0, 6.2, 3.9], 'yaw': 0.0, 'door': [14.0, 5.8, 6.2]},
    ]}

def speed(t):
    i = int(math.floor(t)) % N; u = t - math.floor(t); u = u * u * (3 - 2 * u)
    return spd[i] * (1 - u) + spd[(i + 1) % N] * u

def towers():
    out = []
    for row, (x, zs, hs) in enumerate([(40, [-20, -7, 6, 19, 32, 45], [25, 32, 39, 28, 35, 24]),
                                       (55, [-24, -10, 4, 18, 32, 46], [36, 44, 55, 40, 49, 34]),
                                       (72, [-22, -8, 6, 20, 34, 48], [43, 52, 62, 46, 57, 39])]):
        for j, (z, h) in enumerate(zip(zs, hs)):
            spire = 5.5 if (row + j) % 3 == 1 else 2.0      # crown fins / spire beacon from build_city.py
            out.append((x, z, 7.4 + row * .8, 8.0, -8 + h + spire))
    for j, (x, z, h) in enumerate([(2, -13, 22), (14, -13, 29), (26, -13, 24), (-2, -28, 34), (13, -28, 42), (28, -30, 37)]):
        out.append((x, z, 7.5, 7.5, -8 + h + (5.5 if j % 3 == 1 else 2.0)))
    return out

def main():
    ts = np.arange(N * S + 1) / S
    pos = np.array([cr(t) for t in ts])
    ds = np.linalg.norm(np.diff(pos, axis=0), axis=1)
    v = np.array([speed(t) for t in ts])
    T = np.concatenate([[0], np.cumsum(ds / np.maximum(.3, (v[:-1] + v[1:]) / 2))])
    tw = towers()
    def boxdist(p, b):
        x, z, w, d, top = b
        dx = max(abs(p[0] - x) - w / 2, 0); dz = max(abs(p[2] - z) - d / 2, 0); dy = max(p[1] - top, 0)
        return (dx * dx + dy * dy + dz * dz) ** .5
    clearance = min(boxdist(p, b) for p in pos for b in tw)
    inside = [(i, p) for i, p in enumerate(pos) if 0 < p[0] < 28 and 0 < p[2] < 18 and p[1] < 9.8]
    cafe_issues = []
    for i, p in inside:
        in_void = 8.8 < p[0] < 20 and 5.0 < p[2] < 12.6
        over_bridge = p[2] < 5.1 and p[1] > 7.0
        if not (in_void or over_bridge or p[1] > 8.6): cafe_issues.append([round(float(c), 2) for c in p])
        if p[2] > 11.6 and p[1] < 8.6: cafe_issues.append([round(float(c), 2) for c in p])
        if p[1] < 6.5: cafe_issues.append([round(float(c), 2) for c in p])
    tn = np.gradient(pos, axis=0); tn /= np.linalg.norm(tn, axis=1)[:, None]
    k = np.linalg.norm(np.gradient(tn, axis=0), axis=1) / np.maximum(np.r_[ds, ds[-1]], 1e-4)
    slope = np.degrees(np.arcsin(np.clip(tn[:, 1], -1, 1)))
    deck_c = np.array(DECK['center'])
    over_deck = [p for p in pos if np.hypot(p[0] - deck_c[0], p[2] - deck_c[2]) < DECK['floor_radius'] and abs(p[1] - deck_c[1]) < 8]
    lowest_over_deck = [round(float(p[1] - deck_c[1]), 2) for p in over_deck if not (DECK['dock_rail_x'] < p[0] < 27.6 and -8 < p[2] < 13.5)]
    report = {
        'ride': {'control_points': N, 'length_m': round(float(ds.sum()), 1), 'ride_seconds': round(float(T[-1]), 1),
                 'min_tower_clearance_m': round(float(clearance), 2), 'note_clearance': 'car centre to tower/podium box; car half width 0.95 m',
                 'cafe_samples': len(inside), 'cafe_seconds': round(float(sum(T[i + 1] - T[i] for i, _ in inside if i + 1 < len(T))), 1),
                 'cafe_issues': cafe_issues[:20], 'max_lateral_mps2': round(float((v * v * k).max()), 1),
                 'max_climb_deg': round(float(slope.max()), 1), 'max_dive_deg': round(float(slope.min()), 1),
                 'min_height_over_deck_outside_dock_m': min(lowest_over_deck) if lowest_over_deck else None,
                 'min_car_height_vs_deck_floor_m': round(float(min(p[1] for p in over_deck) - deck_c[1]), 3) if over_deck else None},
        'checks': {}, 'note': 'Geometry checks only. Unity/Udon compilation and VRChat runtime are not validated here.'}
    c = report['checks']
    c['tower_clearance_ge_1_8m'] = bool(clearance >= 1.8)
    c['cafe_path_inside_void_or_above_bridge'] = not cafe_issues
    c['lateral_le_20mps2'] = bool(report['ride']['max_lateral_mps2'] <= 20)
    c['slope_within_40deg'] = bool(abs(report['ride']['max_climb_deg']) <= 40 and abs(report['ride']['max_dive_deg']) <= 40)
    c['car_never_below_deck_floor'] = bool(report['ride']['min_car_height_vs_deck_floor_m'] is None or report['ride']['min_car_height_vs_deck_floor_m'] >= 0)
    c['ride_clears_deck_heads'] = bool(report['ride']['min_height_over_deck_outside_dock_m'] is None or report['ride']['min_height_over_deck_outside_dock_m'] >= 2.2)
    layout = {
        'version': '0.10.0-dev', 'coordinates': 'Unity X / Y up / Z, metres',
        'deck': DECK, 'lift': LIFT, 'cafe_settings_panel': [19.95, 1.92, 1.40],
        'ride': {'points': [round(float(x), 4) for p in pts for x in p], 'speeds': [round(float(s), 3) for s in spd],
                 'cues': cue, 'cue_map': [{'name': n, 'channel': ch, 'seconds': s, 'sfx': fx} for n, (ch, s, fx) in CUES.items()],
                 'samples_per_segment': S, 'cars': 2, 'boarding': 30.0, 'unload': 4.0, 'roll_factor': .55, 'roll_limit': 28.0},
        'komo': KOMO,
    }
    (ROOT / 'Unity/Assets/TheCommons/Data/experience_layout.json').write_text(json.dumps(layout, indent=1) + '\n')
    (ROOT / 'Documentation/experience_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    assert all(c.values()), c

if __name__ == '__main__':
    main()
