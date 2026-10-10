"""Neo-Tokyo neon dressing for APEX / NEON SWITCHYARD (v0.11): placement + checks.

Reads the kart centreline from Unity/Assets/TheCommons/Data/world_manifest.json
(all three road levels) and places visual-only décor where it can never touch a
deck, a barrier, the pit apron or visitor deck, the tyre bundles or the hall
walls, and where overhead decks leave headroom for gates. The kart geometry and
its sources are not modified.

Writes Unity/Assets/TheCommons/Data/kart_neon_layout.json (Unity X / Y up / Z)
and Documentation/kart_neon_validation.json.

    python3 Blender/build_kart_neon_layout.py
"""
from pathlib import Path
import json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / 'Unity/Assets/TheCommons/Data/world_manifest.json').read_text())
K = M['kart']
P = np.array(K['centerline'])            # Blender (x, y plan, z height)
S = np.array(K['stations']); N = len(P)
HALF = K['deck_half_width']; ORIGIN = np.array(K['origin']); SIZE = np.array(K['size'])
XY = P[:, :2]; Z = P[:, 2]
MARGIN = .8                              # free air beyond the deck edge
WALL = (ORIGIN[0] + .3, ORIGIN[0] + SIZE[0] - .3, ORIGIN[1] + .3, ORIGIN[1] + SIZE[1] - .3)
PASS = (564.0, 1070.0)                   # T18 pass entry .. T26 (the seven hairpins T19-T25)
rng = np.random.default_rng(1101)

def U(p, height=None):
    """Blender plan point -> Unity [x, y, z]."""
    return [round(float(p[0]), 3), round(float(p[2] if height is None else height), 3), round(float(p[1]), 3)]

# Pit apron, walkways, visitor deck, canopy and grandstand (from build_kart_circuit.py),
# as an axis-aligned keep-out box with a generous margin.
PIT = (222.0, 281.0, 2.5, 31.2)
def in_pit(q, r=0.): return PIT[0] - r < q[0] < PIT[1] + r and PIT[2] - r < q[1] < PIT[3] + r

def tyres():
    out = []
    for t in K['turn_markers']:
        a = np.array(t['apex']); i = int(np.argmin(np.linalg.norm(XY - a[:2], axis=1)))
        if abs(Z[i] - K['levels'][0]) > 1e-3: continue
        out.append(XY[i])
    return np.array(out)
TYRES = tyres()

def deck_distance(q):
    return float(np.min(np.linalg.norm(XY - q, axis=1))) - HALF
def free(q, r):
    """Floor point q (plan) is free for a footprint of radius r."""
    if not (WALL[0] + r + 1.2 < q[0] < WALL[1] - r - 1.2 and WALL[2] + r + 1.2 < q[1] < WALL[3] - r - 1.2): return False
    if in_pit(q, r + .5): return False
    if deck_distance(q) < MARGIN + r: return False
    if len(TYRES) and np.min(np.linalg.norm(TYRES - q, axis=1)) < 5.5 + r: return False
    return True

def tangent(i):
    d = XY[(i + 2) % N] - XY[(i - 2) % N]; return d / np.linalg.norm(d)
def curvature(i):
    a, b = tangent(i - 3), tangent(i + 3); ds = abs(S[(i + 3) % N] - S[(i - 3) % N]) or 1.
    return float(np.linalg.norm(b - a) / ds)

def overhead_clear(i, top, half_span):
    """No other deck above the gate span at sample i up to height `top` (+0.4 deck)."""
    q = XY[i]; t = tangent(i); n = np.array([-t[1], t[0]])
    for k in np.linspace(-half_span, half_span, 9):
        p = q + n * k
        near = np.linalg.norm(XY - p, axis=1) < HALF + .6
        far = np.abs(S - S[i]) > 40
        above = Z > Z[i] + .5
        if np.any(near & far & above & (Z - K['deck_thickness'] < top + .3)): return False
    return True

def gate_posts_free(i, offset):
    t = tangent(i); n = np.array([-t[1], t[0]]); posts = []
    for side in (-1, 1):
        p = XY[i] + n * side * offset
        others = np.abs(S - S[i]) > 30
        if np.any((np.linalg.norm(XY - p, axis=1) < HALF + .35) & others): return None
        if in_pit(p, .4) or not (WALL[0] + 1 < p[0] < WALL[1] - 1 and WALL[2] + 1 < p[1] < WALL[3] - 1): return None
        posts.append(p)
    return posts

# ---------------------------------------------------------------- gates
def torii_run(count=6, spacing=6.5, rise=5.0, offset=HALF + .35):
    """Longest run of valid gate stations on a straight; prefer the lower level (seen from the stand)."""
    best = None
    for start in range(N):
        run = []; s0 = S[start]
        for k in range(count):
            target = s0 + k * spacing; i = int(np.argmin(np.abs(S - target)))
            if abs(S[i] - target) > .5 or curvature(i) > .012 or not overhead_clear(i, Z[i] + rise, offset + .3): break
            if gate_posts_free(i, offset) is None: break
            if PASS[0] - 10 < S[i] < PASS[1] + 10: break
            run.append(i)
        if len(run) == count:
            score = -Z[run[0]] * 2 - abs(XY[run[0]][1] - 34) * .02
            if best is None or score > best[0]: best = (score, run)
    out = []
    for i in (best[1] if best else []):
        t = tangent(i); yaw = math.degrees(math.atan2(t[0], t[1]))      # Unity yaw: +Z forward = plan +y
        out.append({'position': U(XY[i], 0.0), 'road_y': round(float(Z[i]), 3), 'yaw': round(yaw, 2),
                    'post_offset': round(offset, 3), 'rise': rise, 'station': round(float(S[i]), 1)})
    return out

def pass_arch(rise=4.6, offset=HALF + .35, banner_h=1.75):
    for i in np.argsort(np.abs(S - (PASS[0] + 14))):
        if not (PASS[0] + 4 < S[i] < PASS[0] + 60): continue
        # Structure top: board (rise .. rise + banner) plus the upper beam (+0.31).
        if curvature(i) > .02 or not overhead_clear(i, Z[i] + rise + banner_h + .31, offset + .3) or gate_posts_free(i, offset) is None: continue
        t = tangent(i); yaw = math.degrees(math.atan2(t[0], t[1]))
        return {'position': U(XY[i], 0.0), 'road_y': round(float(Z[i]), 3), 'yaw': round(yaw, 2), 'post_offset': round(offset, 3),
                'rise': rise, 'station': round(float(S[i]), 1), 'texture': 'neon_pass_banner', 'banner': [5.6, banner_h]}
    return None

# ---------------------------------------------------------------- forest
def hairpin_centres():
    out = []
    for t in K['turn_markers']:
        if not t['id'] in ('T19', 'T20', 'T21', 'T22', 'T23', 'T24', 'T25'): continue
        a = np.array(t['apex'])[:2]; i = int(np.argmin(np.linalg.norm(XY - a, axis=1)))
        t0, t1 = tangent(i - 6), tangent(i + 6); turn = np.sign(t0[0] * t1[1] - t0[1] * t1[0])
        n = np.array([-tangent(i)[1], tangent(i)[0]]) * turn
        out.append((t['id'], XY[i] + n * t['radius_m'], t['radius_m']))
    return out

def forest(limit=54):
    pass_mask = (S >= PASS[0]) & (S <= PASS[1]); pxy = XY[pass_mask]
    trees = []
    kinds = ['momiji', 'momiji', 'cedar', 'sakura', 'momiji', 'cedar']
    for name, c, radius in hairpin_centres():           # a feature tree in every hairpin it fits
        for r in (2.0, 1.6, 1.3, 1.0):
            if free(c, r):
                trees.append({'type': 'sakura' if name in ('T19', 'T22', 'T25') else 'momiji', 'plan': c, 'radius': r, 'height': round(3.6 + r * 1.3, 2), 'hairpin': name}); break
    lo = pxy.min(axis=0) - 10; hi = pxy.max(axis=0) + 10
    candidates = [np.array([x, y]) for x in np.arange(lo[0], hi[0], 1.0) for y in np.arange(lo[1], hi[1], 1.0)]
    rng.shuffle(candidates)
    for q in candidates:
        if len(trees) >= limit: break
        r = float(rng.choice([1.0, 1.3, 1.6]))
        d_pass = float(np.min(np.linalg.norm(pxy - q, axis=1))) - HALF
        if d_pass > 8.5 or not free(q, r): continue
        if any(np.linalg.norm(q - t['plan']) < t['radius'] + r + 1.1 for t in trees): continue
        trees.append({'type': kinds[len(trees) % len(kinds)], 'plan': q, 'radius': r, 'height': round(3.2 + r * 1.6 + float(rng.uniform(0, 1.2)), 2), 'hairpin': None})
    for t in trees:
        t['position'] = U(t.pop('plan'), 0.0); t['yaw'] = round(float(rng.uniform(0, 360)), 1); t['radius'] = round(t['radius'], 2)
    return trees

def lantern_strings(trees, want=4):
    pts = [np.array([t['position'][0], t['position'][2]]) for t in trees]
    out = []; tried = 0
    pairs = [(a, b) for a in range(len(pts)) for b in range(a + 1, len(pts)) if 8 < np.linalg.norm(pts[a] - pts[b]) < 13]
    rng.shuffle(pairs)
    for a, b in pairs:
        if len(out) >= want: break
        pa, pb = pts[a], pts[b]; d = (pb - pa) / np.linalg.norm(pb - pa); n = np.array([-d[1], d[0]])
        pa = pa + n * 1.9; pb = pb + n * 1.9                 # poles beside the trees, not inside them
        if not all(free(pa + (pb - pa) * k, .45) for k in np.linspace(0, 1, 25)): continue
        if any(np.linalg.norm(np.cross(np.r_[pb - pa, 0], np.r_[t_[[0, 2]] - pa, 0])[2]) / np.linalg.norm(pb - pa) < 1.0 for t_ in [np.array(t['position']) for t in trees]
               if 0 < np.dot(np.array([t_[0], t_[2]]) - pa, pb - pa) < np.dot(pb - pa, pb - pa)): continue
        if any(np.linalg.norm((pa + pb) / 2 - np.array([o['from'][0] + o['to'][0], o['from'][2] + o['to'][2]]) / 2) < 6 for o in out): continue
        out.append({'from': U(pa, 0.0), 'to': U(pb, 0.0), 'pole_height': 3.4, 'lanterns': int(np.linalg.norm(pb - pa) / 1.4)})
    return out

def tower():
    best = None
    for x in np.arange(WALL[0] + 6, WALL[1] - 6, 1.0):
        for y in np.arange(WALL[2] + 6, WALL[3] - 6, 1.0):
            q = np.array([x, y])
            pass_d = float(np.min(np.linalg.norm(XY[(S >= PASS[0]) & (S <= PASS[1])] - q, axis=1)))
            if pass_d < 14 or not free(q, 3.4): continue
            d = deck_distance(q)
            if best is None or d > best[0]: best = (d, q)
    return {'position': U(best[1], 0.0), 'height': 12.4, 'base': 4.6, 'clearance_m': round(best[0], 2)} if best else None

def hanging(trees, tower_rec):
    centre = np.mean([[t['position'][0], t['position'][2]] for t in trees], axis=0)
    spots = [(centre, 'neon_apex_h', 0.0), (np.array([ORIGIN[0] + SIZE[0] * .5, ORIGIN[1] + SIZE[1] * .78]), 'neon_neotokyo_h', 90.0)]
    if tower_rec: spots.append((np.array([tower_rec['position'][0], tower_rec['position'][2]]) + np.array([0, 7.0]), 'neon_switchyard_h', 0.0))
    return [{'position': U(q, 12.75), 'yaw': yaw, 'texture': tex, 'size': [4.2, 1.31]} for q, tex, yaw in spots]

def wall_signs():
    x0, x1, y0, y1 = WALL
    v, h = [2.0, 6.0], [9.6, 3.0]
    raw = [  # texture, plan point on the wall, Unity yaw (readable side faces the hall), size, centre height
        ('neon_tokyo_v', (x0, 42), -90, v, 8.2), ('neon_dennou_v', (x0, 118), -90, v, 8.2), ('neon_neotokyo_h', (x0, 80), -90, h, 11.6),
        ('neon_kasoku_v', (x1, 58), 90, v, 8.2), ('neon_yasou_v', (x1, 128), 90, v, 8.2), ('neon_anzen_h', (x1, 93), 90, h, 11.6),
        ('neon_switchyard_h', (296, y0), 180, h, 10.8), ('neon_mirai_v', (198, y0), 180, v, 8.2),
        ('neon_touge_v', (204, y1), 0, [2.4, 7.2], 8.6), ('neon_mirai_v', (312, y1), 0, v, 8.2),
    ]
    out = []
    for tex, (px, py), yaw, size, height in raw:
        inward = {-90: (1, 0), 90: (-1, 0), 180: (0, 1), 0: (0, -1)}[yaw]
        q = np.array([px + inward[0] * .32, py + inward[1] * .32])
        out.append({'texture': tex, 'position': U(q, height), 'yaw': yaw, 'size': size})
    return out

def vending():
    return [{'position': U(np.array([233.0 + k * 1.15, 1.05]), 0.0), 'yaw': 0.0, 'variant': k % 2} for k in range(4)]

def main():
    gates = torii_run(); arch = pass_arch(); trees = forest(); strings = lantern_strings(trees)
    tw = tower(); hangs = hanging(trees, tw); signs = wall_signs(); vend = vending()
    # ---- validation (independent re-checks of everything placed on the floor)
    issues = []
    def plan(p): return np.array([p[0], p[2]])
    for t in trees:
        if not free(plan(t['position']), t['radius']): issues.append(('tree', t['position']))
    for g in gates + ([arch] if arch else []):
        i = int(np.argmin(np.linalg.norm(XY - plan(g['position']), axis=1)))
        if gate_posts_free(i, g['post_offset']) is None: issues.append(('gate posts', g['position']))
        if not overhead_clear(i, g['road_y'] + g['rise'] + (1.9 if g is arch else 0), g['post_offset'] + .3): issues.append(('gate headroom', g['position']))
    for s_ in strings:
        a, b = plan(s_['from']), plan(s_['to'])
        if not all(free(a + (b - a) * k, .45) for k in np.linspace(0, 1, 25)): issues.append(('lantern string', s_['from']))
    if tw and not free(plan(tw['position']), 3.4): issues.append(('tower', tw['position']))
    for h_ in hangs:
        if h_['position'][1] - h_['size'][1] / 2 < max(K['levels']) + 3.0: issues.append(('hanging sign headroom', h_['position']))
    for v_ in vend:
        if in_pit(plan(v_['position'])): issues.append(('vending in pit', v_['position']))
    min_tree = min(deck_distance(plan(t['position'])) - t['radius'] for t in trees)
    report = {
        'version': '0.11.0', 'trees': len(trees), 'hairpin_feature_trees': sorted(t['hairpin'] for t in trees if t['hairpin']),
        'tree_types': {k: sum(t['type'] == k for t in trees) for k in ('momiji', 'sakura', 'cedar')},
        'torii': len(gates), 'torii_stations_m': [g['station'] for g in gates], 'pass_arch_station_m': arch['station'] if arch else None,
        'lantern_strings': len(strings), 'tower_deck_clearance_m': tw['clearance_m'] if tw else None,
        'min_tree_canopy_to_deck_edge_m': round(min_tree, 2), 'wall_signs': len(signs), 'hanging_signs': len(hangs), 'vending_machines': len(vend),
        'checks': {'no_floor_object_inside_deck_pit_tyre_or_wall_clearance': not issues, 'gates_found': len(gates) == 6 and arch is not None,
                   'hanging_signs_clear_top_level_by_3m': all(h_['position'][1] - h_['size'][1] / 2 >= max(K['levels']) + 3.0 for h_ in hangs),
                   'trees_in_every_fitting_hairpin': len([t for t in trees if t['hairpin']]) >= 5},
        'issues': [list(map(str, i)) for i in issues],
        'note': 'Visual-only décor without colliders except the vending machines (south wall walkway). Geometry checks only; Unity/CVS2 runtime not validated.'}
    layout = {'version': '0.11.0', 'coordinates': 'Unity X / Y up / Z, metres', 'trees': trees, 'torii': gates, 'pass_arch': arch,
              'lanterns': strings, 'tower': tw, 'hanging_signs': hangs, 'wall_signs': signs, 'vending': vend}
    (ROOT / 'Unity/Assets/TheCommons/Data/kart_neon_layout.json').write_text(json.dumps(layout, indent=1) + '\n')
    (ROOT / 'Documentation/kart_neon_validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    assert all(report['checks'].values()), report['checks']

if __name__ == '__main__':
    main()
