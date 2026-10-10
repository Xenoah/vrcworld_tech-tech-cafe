"""v0.11.0 release previews: the kart hall's Neo-Tokyo neon and the cafe's particle lasers.

Opens Blender/The_Commons_Compact.blend (the real cafe and kart hall) and adds what
the v0.11 builders generate in Unity, rebuilt at the same dimensions:
  * kart neon dressing from Unity/Assets/TheCommons/Data/kart_neon_layout.json, using
    the primitives, transforms and colours of Editor/CommonsKartNeonBuilder.cs
    (Unity cube/cylinder/sphere sizes, Holo Field grid shells, neon sign textures);
  * DISCO particle lasers: the particles alive at one moment of the built-in music,
    simulated like CommonsLightingModes does it (Emit() per frame at the music-driven
    rate, 26 m/s, 0.28 s lifetime, world space, the four bar figures and chord colours
    from Data/music_score.json), drawn as camera-facing stretched billboards with the
    Laser Particle shader's soft core.
Rendered with Cycles; an Intel Open Image Denoise CLI uses the albedo/normal passes.

These are Blender previews, not Unity/VRChat runtime captures: Unity lights the neon
with baked GI and probes and draws the particles itself.

blender -b --python Blender/render_neon_views.py -- [VIEW ...] [--samples N] [--percent P] [--oidn PATH]
"""
from pathlib import Path
import bpy, math, sys, os, json, subprocess, tempfile
from mathutils import Vector
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'Unity/Assets/TheCommons/Data'
NEON = ROOT / 'Unity/Assets/TheCommons/Media/Neon'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default):
    if name in ARGS:
        i = ARGS.index(name); value = ARGS[i + 1]; del ARGS[i:i + 2]; return value
    return default
SAMPLES = int(option('--samples', '40'))
PERCENT = int(option('--percent', '100'))
OIDN = option('--oidn', '')
VIEW_TRANSFORM = option('--view', 'Standard')   # kart views; the cafe keeps the file's AgX like 31-33
EXPOSURE = float(option('--exposure', '0'))
LAYOUT = json.loads((DATA / 'kart_neon_layout.json').read_text())
SCORE = json.loads((DATA / 'music_score.json').read_text())

# ------------------------------------------------------------ Unity space
def euler(x, y, z):
    """Quaternion.Euler(x, y, z) as a matrix (Unity applies Z, then X, then Y)."""
    cx, sx = math.cos(math.radians(x)), math.sin(math.radians(x))
    cy, sy = math.cos(math.radians(y)), math.sin(math.radians(y))
    cz, sz = math.cos(math.radians(z)), math.sin(math.radians(z))
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return ry @ rx @ rz
def trs(p=(0, 0, 0), r=None, s=(1, 1, 1)):
    m = np.eye(4); m[:3, :3] = (np.eye(3) if r is None else r) @ np.diag(s); m[:3, 3] = p; return m
def look(d):
    """Quaternion.LookRotation(d) (up = Y) as a matrix: local +Z along d."""
    f = np.array(d, float); f /= np.linalg.norm(f); up = np.array([0, 1., 0])
    if abs(f @ up) > .999: up = np.array([1., 0, 0])
    x = np.cross(up, f); x /= np.linalg.norm(x); y = np.cross(f, x)
    return np.stack([x, y, f], 1)
def B(v): return Vector((v[0], v[2], v[1]))   # Unity (X, Y up, Z) -> Blender (X, Y, Z up)

# Unity primitive meshes in local Unity coordinates: (vertices, faces, uvs or None)
def prim_cube():
    vs = [(sx * .5, sy * .5, sz * .5) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    return vs, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], None
def prim_cylinder(seg=24):                       # Unity cylinder: diameter 1, height 2 (y -1..1)
    vs = []; fs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; vs += [(.5 * math.cos(a), -1, .5 * math.sin(a)), (.5 * math.cos(a), 1, .5 * math.sin(a))]
    for i in range(seg):
        j = (i + 1) % seg; fs.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    fs += [tuple(2 * i for i in range(seg)), tuple(2 * i + 1 for i in reversed(range(seg)))]
    return vs, fs, None
def prim_sphere(rings=12, seg=24):               # Unity sphere: diameter 1, lat-long UVs
    vs = []; uv = []; fs = []
    for r in range(rings + 1):
        phi = math.pi * r / rings - math.pi / 2
        for s in range(seg + 1):
            th = 2 * math.pi * s / seg
            vs.append((.5 * math.cos(phi) * math.cos(th), .5 * math.sin(phi), .5 * math.cos(phi) * math.sin(th))); uv.append((s / seg, r / rings))
    for r in range(rings):
        for s in range(seg):
            a = r * (seg + 1) + s; fs.append((a, a + 1, a + seg + 2, a + seg + 1))
    return vs, fs, uv
def prim_cone(radius, height, seg):              # CommonsKartNeonBuilder.Cone (open base disc kept)
    vs = []; uv = []; fs = []
    for k in range(11):
        v = k / 10
        for i in range(seg + 1):
            a = 2 * math.pi * i / seg; vs.append((math.cos(a) * radius * (1 - v), height * v, math.sin(a) * radius * (1 - v))); uv.append((i / seg, v))
    for k in range(10):
        for i in range(seg):
            a = k * (seg + 1) + i; fs.append((a, a + seg + 1, a + seg + 2, a + 1))
    fs.append(tuple(range(seg)))
    return vs, fs, uv
def prim_torus(major, minor, seg, sides):        # XZ plane, like the builder's Torus
    vs = []; fs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; c = np.array([math.cos(a), 0, math.sin(a)])
        for j in range(sides):
            b = 2 * math.pi * j / sides; vs.append(tuple(c * (major + minor * math.cos(b)) + np.array([0, minor * math.sin(b), 0])))
    for i in range(seg):
        for j in range(sides):
            fs.append((i * sides + j, i * sides + (j + 1) % sides, ((i + 1) % seg) * sides + (j + 1) % sides, ((i + 1) % seg) * sides + j))
    return vs, fs, None
def prim_annulus(inner, outer, seg):
    vs = []; fs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; vs += [(math.cos(a) * inner, 0, math.sin(a) * inner), (math.cos(a) * outer, 0, math.sin(a) * outer)]
    for i in range(seg):
        j = (i + 1) % seg; fs.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    return vs, fs, None
def prim_quad(w, h):                             # CommonsWorldBuilder.Quad: XY plane, faces -Z
    return [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [(0, 1, 2, 3)], [(0, 0), (1, 0), (1, 1), (0, 1)]

COLL = None
def emit(name, mesh, m, mat, smooth=False):
    """Place a Unity-local mesh with Unity world matrix m into the Blender scene."""
    vs, fs, uv = mesh
    v = np.asarray(vs, float); w = (m[:3, :3] @ v.T).T + m[:3, 3]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in w[:, [0, 2, 1]]], [], [tuple(reversed(f)) for f in fs])
    if uv:
        layer = me.uv_layers.new()
        for poly in me.polygons:
            for li in poly.loop_indices: layer.data[li].uv = uv[me.loops[li].vertex_index]
    if smooth:
        for p in me.polygons: p.use_smooth = True
    me.materials.append(mat); o = bpy.data.objects.new(name, me); COLL.objects.link(o); return o

# --------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new('ShaderNodeOutputMaterial')
CACHE = {}
def neon(key, color, strength, albedo=.18):
    """The Commons/Surface with _Color = color * albedo and _EmissionColor = color * strength."""
    if key in CACHE: return CACHE[key]
    m, nt, out = node_mat('NEON_' + key); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (*(c * albedo for c in color), 1); p.inputs['Roughness'].default_value = .5
    p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = strength
    nt.links.new(p.outputs[0], out.inputs[0]); CACHE[key] = m; return m
def dark(key, color, rough=.65):
    if key in CACHE: return CACHE[key]
    m, nt, out = node_mat('NEON_' + key); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough
    nt.links.new(p.outputs[0], out.inputs[0]); CACHE[key] = m; return m
def math_node(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for k, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[k].default_value = x
        else: nt.links.new(x, n.inputs[k])
    return n.outputs[0]
def additive(nt, out, color, strength_socket):
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1); nt.links.new(strength_socket, e.inputs[1])
    t = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(e.outputs[0], add.inputs[0]); nt.links.new(t.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs[0])
def holo(key, color, intensity=.75, grid=(12, 6), line=.05):
    """The Commons/Holo Field (additive): (grid lines * .8 + .12 + fresnel^2) * intensity, no fade."""
    if 'holo' + key in CACHE: return CACHE['holo' + key]
    m, nt, out = node_mat('NEON_Holo' + key); uv = nt.nodes.new('ShaderNodeUVMap'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs[0], sep.inputs[0]); lines = []
    for axis, g in ((0, grid[0]), (1, grid[1])):
        f = math_node(nt, 'ABSOLUTE', math_node(nt, 'SUBTRACT', math_node(nt, 'FRACT', math_node(nt, 'MULTIPLY', sep.outputs[axis], g)), .5))
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
        mr.inputs[1].default_value = 0; mr.inputs[2].default_value = line; mr.inputs[3].default_value = 1; mr.inputs[4].default_value = 0
        nt.links.new(math_node(nt, 'SUBTRACT', .5, f), mr.inputs[0]); lines.append(mr.outputs[0])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); fres = math_node(nt, 'POWER', lw.outputs['Facing'], 2)
    s = math_node(nt, 'ADD', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', math_node(nt, 'MAXIMUM', *lines), .8), .12), fres)
    additive(nt, out, color, math_node(nt, 'MULTIPLY', s, intensity)); m.blend_method = 'BLEND'; CACHE['holo' + key] = m; return m
def sign(texture, brightness=1.15):
    """The Commons/Media: unlit texture * _Color (1.15)."""
    if texture in CACHE: return CACHE[texture]
    m, nt, out = node_mat('NEON_' + texture); tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(NEON / f'{texture}.png')); tex.interpolation = 'Smart'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[1].default_value = brightness
    nt.links.new(tex.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], out.inputs[0]); CACHE[texture] = m; return m

# ----------------------------------------------------------- neon dressing
CUBE, CYL, SPH = prim_cube(), prim_cylinder(), prim_sphere()
def P(a): return np.array(a, float)
def bar(a, b, thickness, mat):
    d = P(b) - P(a)
    if d @ d < 1e-12: return
    emit('Bar', CUBE, trs((P(a) + P(b)) / 2, look(d), (thickness, thickness, np.linalg.norm(d))), mat)

def tree(t):
    root = trs(P(t['position']), euler(0, t['yaw'], 0)); h, r = t['height'], t['radius']; kind = t['type']
    trunk = dark('Trunk', (.05, .05, .08))
    col = {'cedar': (.05, 1, .6), 'sakura': (1, .2, .6)}.get(kind, (1, .22, .04))
    edge = {'cedar': (.2, .7, 1), 'sakura': (1, .6, .85)}.get(kind, (1, .08, .06))
    core, ring, shell, ground = neon(kind + 'Core', col, .28, .07), neon(kind + 'Ring', edge, 3.2), holo(kind, col), neon(kind + 'Ground', col, 2.2)
    emit('Planter', prim_annulus(r * .55, r * .62, 40), trs(P(t['position']) + [0, .015, 0]), ground)
    if kind == 'cedar':
        emit('Trunk', CYL, root @ trs((0, h * .17, 0), None, (.3, h * .17, .3)), trunk)
        for y, rad, ht in zip((h * .25, h * .45, h * .65), (r, r * .75, r * .5), (h * .45, h * .4, h * .35)):
            cone = prim_cone(rad, ht, 12)
            emit('Canopy', cone, root @ trs((0, y, 0)), core)
            emit('Shell', prim_cone(rad, ht, 16), root @ trs((0, y - .02, 0), None, (1.06,) * 3), shell)
            emit('NeonRing', prim_torus(rad * 1.02, .04, 36, 5), root @ trs((0, y + .03, 0)), ring)
    else:
        emit('Trunk', CYL, root @ trs((0, h * .25, 0), None, (.26, h * .25, .26)), trunk)
        emit('Branch', CYL, root @ trs((r * .22, h * .52, 0), euler(0, 0, -35), (.12, h * .12, .12)), trunk)
        for p, size in zip(((0, h * .7, 0), (r * .55, h * .62, r * .2), (-r * .5, h * .6, -r * .25), (r * .1, h * .62, -r * .55)), (r * 1.5, r * 1.05, r, r * .95)):
            emit('Canopy', SPH, root @ trs(p, None, (size,) * 3), core, True)
            emit('Shell', SPH, root @ trs(p, None, (size * 1.07,) * 3), shell, True)
        emit('Halo', prim_torus(r * 1.05, .035, 48, 5), trs(P(t['position']) + [0, h * .66, 0], euler(0, t['yaw'], 0) @ euler(8, 0, 4)), ring)

def gate_frame(m, g, post, beam, cap, torii):
    top = g['road_y'] + g['rise']; half = g['post_offset']
    for side in (-1, 1): emit('Post', CYL, m @ trs((side * half, (top - .2) / 2, 0), None, (.36, (top - .2) / 2, .36)), post)
    if not torii: return
    emit('Kasagi', CUBE, m @ trs((0, top, 0), None, (half * 2 + 1.5, .32, .44)), beam)
    emit('KasagiCap', CUBE, m @ trs((0, top + .2, 0), None, (half * 2 + 1.7, .1, .5)), cap)
    emit('Nuki', CUBE, m @ trs((0, top - 1.05, 0), None, (half * 2 + .7, .24, .26)), beam)
    emit('Gakuzuka', CUBE, m @ trs((0, top - .52, 0), None, (.22, .8, .2)), beam)
def torii(g):
    vermilion = neon('Vermilion', (1, .14, .04), 1.35)
    gate_frame(trs(P(g['position']), euler(0, g['yaw'], 0)), g, vermilion, vermilion, dark('ToriiCap', (.03, .03, .04)), True)
def pass_arch(g):
    m = trs(P(g['position']), euler(0, g['yaw'], 0)); steel = dark('GateSteel', (.12, .13, .17), .45); amber = neon('Amber', (1, .62, .12), 3.2)
    gate_frame(m, g, steel, steel, steel, False)
    w, h = g.get('banner') or (5.6, 1.75); cy = g['road_y'] + g['rise'] + h / 2
    emit('Beam', CUBE, m @ trs((0, cy, 0), None, (g['post_offset'] * 2 + .4, .18, .2)), steel)
    emit('Board', CUBE, m @ trs((0, cy, 0), None, (w, h, .1)), dark('Board', (.02, .02, .03)))
    for face in (-1, 1): emit('Banner', prim_quad(w, h), m @ trs((0, cy, face * .056), euler(0, 0 if face < 0 else 180, 0)), sign(g['texture']))
    for y in (cy - h / 2 - .06, cy + h / 2 + .06): emit('Tube', CUBE, m @ trs((0, y, 0), None, (w + .1, .06, .14)), amber)

def lanterns(s):
    a, b = P(s['from']), P(s['to']); ph = s['pole_height']
    pole, wire = dark('Pole', (.08, .08, .1)), dark('Wire', (.02, .02, .02))
    red, white = neon('LanternRed', (1, .16, .1), 2.6), neon('LanternWhite', (1, .85, .65), 2.4)
    for p in (a, b): emit('Pole', CYL, trs(p + [0, ph / 2, 0], None, (.12, ph / 2, .12)), pole)
    n = max(3, s['lanterns']); prev = a + [0, ph, 0]
    for i in range(1, n + 2):
        u = i / (n + 1); p = a + (b - a) * u + [0, ph - .55 * 4 * u * (1 - u), 0]
        bar(prev, p, .02, wire); prev = p
        if i == n + 1: break
        emit('Chochin', SPH, trs(p - [0, .3, 0], None, (.34, .46, .34)), white if i % 3 == 0 else red, True)
        for dy in (-.24, .24): emit('Cap', CYL, trs(p - [0, .3, 0] + [0, dy, 0], None, (.2, .025, .2)), wire)

def corner(e, s, y):
    return [(-s, y, -s), (s, y, -s), (s, y, s), (-s, y, s)][e % 4]
def tower(w):
    o = P(w['position']); H, Bh, T = w['height'], w['base'] * .5, .5
    red, white, steel = neon('TowerRed', (1, .26, .08), 3.0), neon('TowerWhite', (.9, .95, 1), 2.6), dark('TowerSteel', (.1, .1, .13), .5)
    half = lambda y: Bh + (T - Bh) * (y / H) ** .8
    for sx in (-1, 1):
        for sz in (-1, 1): bar(o + [sx * Bh, 0, sz * Bh], o + [sx * T, H, sz * T], .22, steel)
    levels = (2.4, 4.8, 7.2, 9.4, 11.2)
    for k, y in enumerate(levels):
        s = half(y); m = red if k % 2 == 0 else white
        for e in range(4): bar(o + corner(e, s, y), o + corner(e + 1, s, y), .12, m)
        y0 = 0 if k == 0 else levels[k - 1]; s0 = half(y0)
        for e in range(4):   # X braces (PC only in Unity)
            bar(o + corner(e, s0, y0), o + corner(e + 1, s, y), .05, white if k % 2 == 0 else red)
            bar(o + corner(e + 1, s0, y0), o + corner(e, s, y), .05, white if k % 2 == 0 else red)
    ds = half(7.2) + .45
    emit('Observatory', CUBE, trs(o + [0, 7.65, 0], None, (ds * 2, .9, ds * 2)), steel)
    emit('ObservatoryBand', CUBE, trs(o + [0, 7.65, 0], None, (ds * 2 + .04, .16, ds * 2 + .04)), white)
    emit('Antenna', CYL, trs(o + [0, H + .7, 0], None, (.12, .7, .12)), red)

def wall_sign(s, hanging):
    m = trs(P(s['position']), euler(0, s['yaw'], 0)); w, h = s['size']
    emit('Backing', CUBE, m @ trs((0, 0, 0 if hanging else .07), None, (w + .16, h + .16, .06 if hanging else .1)), dark('Board', (.02, .02, .03)))
    for face in ((-1, 1) if hanging else (-1,)): emit('Sign', prim_quad(w, h), m @ trs((0, 0, face * .04), euler(0, 0 if face < 0 else 180, 0)), sign(s['texture']))
    if hanging:
        length = max(.2, 14.1 - (s['position'][1] + h / 2))
        for x in (-w * .4, w * .4): emit('Hanger', CYL, m @ trs((x, h / 2 + length / 2, 0), None, (.03, length / 2, .03)), dark('Wire', (.02, .02, .02)))
def vending(v):
    m = trs(P(v['position']), euler(0, v['yaw'], 0)); k = v['variant']
    emit('Body', CUBE, m @ trs((0, .93, 0), None, (1, 1.86, .78)), dark('Vend%d' % k, (.05, .18, .5) if k == 0 else (.5, .06, .18), .4))
    emit('Front', prim_quad(.92, 1.68), m @ trs((0, .95, .395), euler(0, 180, 0)), sign('neon_vending_a' if k == 0 else 'neon_vending_b'))
    emit('TopGlow', CUBE, m @ trs((0, 1.9, .2), None, (1, .06, .4)), neon('VendGlow%d' % k, (.3, .7, 1) if k == 0 else (1, .3, .6), 2.6))

def build_neon():
    for t in LAYOUT['trees']: tree(t)
    for g in LAYOUT['torii']: torii(g)
    pass_arch(LAYOUT['pass_arch'])
    for s in LAYOUT['lanterns']: lanterns(s)
    tower(LAYOUT['tower'])
    for s in LAYOUT['wall_signs']: wall_sign(s, False)
    for s in LAYOUT['hanging_signs']: wall_sign(s, True)
    for v in LAYOUT['vending']: vending(v)
    print('neon objects', len(COLL.objects), flush=True)

# ------------------------------------------------------------ particle lasers
BPM, STEPS, BARS = SCORE['bpm'], SCORE['steps_per_bar'], SCORE['bars']
CENTER, RADIUS = np.array([14, 2.8, 10.]), np.array([2.6, .7, 1.])
def chord(bar, secondary):
    t = np.array(SCORE['bar_secondary_rgb' if secondary else 'bar_primary_rgb']).reshape(-1, 3); return t[bar % len(t)]
def hit(track, step_pos, decay):
    """CommonsAdaptiveMusic.Hit: latest onset within the last 4 steps, exponential decay."""
    tr = SCORE[track]; step = math.floor(step_pos)
    for back in range(4):
        s = (step - back) % len(tr)
        if tr[s] > 0: return tr[s] * math.exp(-(step_pos - (step - back)) * 15 / BPM * decay)
    return 0.
def kick(step_pos, dance=.71, soft=.13):
    """KickPulse with DISCO stem levels (dance beat .8 x MUSIC 4/5 over the .9 headroom)."""
    return min(1., hit('kick_dance', step_pos, 7) * dance + hit('kick_soft', step_pos, 7) * soft)
def figure(f, i, count, beat):
    """CommonsLightingModes.Figure: fan, cross, tunnel, chase."""
    half = max(1, count // 2); side = -1 if i < half else 1; j = i % half
    s = j / (half - 1) * 2 - 1 if half > 1 else 0.; tau = 2 * math.pi; r = RADIUS
    if f == 0: return CENTER + [s * r[0], r[1] * math.sin(tau * beat / 2) * .6, side * r[2] * math.sin(tau * beat / 4)]
    if f == 1: return CENTER + [-side * r[0] * (.3 + .7 * abs(s)), r[1] * math.sin(tau * beat + j), r[2] * s]
    if f == 2:
        a = tau * beat / 4 + j * tau / half + (math.pi if side > 0 else 0)
        return CENTER + [r[0] * .65 * math.cos(a), r[1] * .5 * math.sin(a * 2), r[2] * math.sin(a)]
    lane = beat / 2 + j / half
    return CENTER + [-r[0] + 2 * r[0] * (lane - math.floor(lane)), -.3, side * r[2] * .6]
def beam_dir(i, origin, step_pos, count=12):
    bar = int(step_pos // STEPS) % BARS; beat = (step_pos % STEPS) / 4
    blend = (lambda x: x * x * (3 - 2 * x))(min(1., max(0., beat))); f = bar % 4; prev = (bar + 3) % 4
    target = figure(prev, i, count, beat + 4) * (1 - blend) + figure(f, i, count, beat) * blend
    d = target - origin; return d / np.linalg.norm(d)
def particle_mat(key, color):
    """The Commons/Laser Particle: colour * core(across) * along * intensity * 1.6, additive."""
    m, nt, out = node_mat('LaserParticle_' + key); uv = nt.nodes.new('ShaderNodeUVMap'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs[0], sep.inputs[0])
    across = math_node(nt, 'SUBTRACT', 1, math_node(nt, 'ABSOLUTE', math_node(nt, 'SUBTRACT', math_node(nt, 'MULTIPLY', sep.outputs[1], 2), 1)))
    core = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', across, across), math_node(nt, 'ADD', 1, math_node(nt, 'MULTIPLY', 2, math_node(nt, 'POWER', across, 8))))
    ramps = []
    for lo, hi in ((0, .2), (1, .6)):
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'; mr.clamp = True
        mr.inputs[1].default_value = lo; mr.inputs[2].default_value = hi; nt.links.new(sep.outputs[0], mr.inputs[0]); ramps.append(mr.outputs[0])
    strength = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', core, math_node(nt, 'MULTIPLY', *ramps)), 1.0)
    additive(nt, out, color, strength); m.blend_method = 'BLEND'; return m, strength.node
def build_lasers(step_pos, cam, count=12, fps=90., rate=70., speed=26., lifetime=.28, size=.045, velocity_scale=.018):
    """Particles alive at step_pos, emitted frame by frame like EmitParticles()."""
    bar = int(step_pos // STEPS) % BARS
    k_now = kick(step_pos); intensity = (.55 + .4 * k_now) * 1.6
    mats = []
    for idx in range(2):
        m, strength = particle_mat('AB'[idx], tuple(chord(bar, idx == 1))); strength.inputs[1].default_value = intensity; mats.append(m)
    sec_per_step = 15 / BPM; length = size + speed * velocity_scale; verts = []; faces = []; uvs = []; mat_idx = []
    for i in range(count):
        origin = np.array([10.2 if i < count // 2 else 17.8, 4.3, 5.3]); carry = 0.
        frames = int(round((lifetime + .05) * fps))
        for fr in range(frames, -1, -1):
            age = fr / fps; t_step = step_pos - age / sec_per_step
            carry += rate * (.45 + 1.8 * kick(t_step)) / fps; n = int(carry); carry -= n
            if n == 0 or age > lifetime: continue
            d = beam_dir(i, origin, t_step, count); head = origin + d * speed * age; tail = head - d * length
            view = head - cam; side = np.cross(d, view); side /= np.linalg.norm(side); side *= size / 2
            for _ in range(min(n, 12)):
                b = len(verts); verts += [tail - side, head - side, head + side, tail + side]; faces.append((b, b + 1, b + 2, b + 3))
                uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]; mat_idx.append(i % 2)
    me = bpy.data.meshes.new('LaserParticles'); me.from_pydata([tuple(B(v)) for v in verts], [], faces)
    layer = me.uv_layers.new()
    for poly in me.polygons:
        poly.material_index = mat_idx[poly.index]
        for li in poly.loop_indices: layer.data[li].uv = uvs[me.loops[li].vertex_index]
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new('LaserParticles', me); COLL.objects.link(o); o.visible_shadow = False
    print('laser particles', len(faces), 'kick %.2f' % k_now, 'bar', bar, SCORE['chords'][bar], flush=True)
    return chord(bar, False), chord(bar, True), k_now

# ------------------------------------------------------------------ scene
VIEWS = {
    # name: (kind, camera Blender position, target, lens)
    '41_Cafe_Particle_Lasers': ('cafe', (14, 2.4, 1.65), (14, 12, 3.7), 18),
    '42_Kart_Neon_Pass': ('kart', (272, 40, 13.0), (220, 94, 1.5), 24),
    '43_Kart_Torii_Tunnel': ('kart', (320.0, 36.5, 1.55), (320.0, 70.0, 3.2), 22),
    '44_Kart_Pass_Gate': ('kart', (285.1, 49.0, 5.9), (284.7, 64.0, 8.6), 22),
    '45_Kart_Neon_Overview': ('kart_cutaway', (393, -109, 178), (254, 84, 3.4), 43),
}
LASER_MOMENT = 4 * 16 + 9.0     # bar 5 of the loop (Dmaj9, fan figure), one 16th after the kick on beat 3

def cafe_palette(primary, secondary, k):
    """DISCO: room emission, accents and lamps follow the chord colours; accents swell on the kick."""
    clones = {}
    for o in bpy.data.objects:
        group = o.users_collection[0].name if o.users_collection else ''
        o.hide_render = group.startswith(('KART_', 'FPV_')) or group == 'MODE_Academic'
        if o.type == 'LIGHT' and not o.hide_render and 0 < o.location.x < 28:
            o.data.color = primary if sum(ord(c) for c in o.name) % 2 else secondary; o.data.energy *= .75 * (1 + .35 * k)
        if group.startswith(('ENV_', 'WAY_')) or o.type not in {'MESH', 'FONT'}: continue
        for slot in o.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes: continue
            if mat.name not in clones:
                copy = mat.copy(); clones[mat.name] = copy; pb = copy.node_tree.nodes.get('Principled BSDF')
                if pb and pb.inputs['Emission Strength'].default_value > 0:
                    pb.inputs['Emission Color'].default_value = (*(primary if len(clones) % 2 else secondary), 1)
            slot.material = clones[mat.name]

def write_pfm(path, rgb):
    h, w, _ = rgb.shape
    with open(path, 'wb') as f:
        f.write(b'PF\n%d %d\n-1.0\n' % (w, h)); f.write(np.ascontiguousarray(rgb, dtype='<f4').tobytes())
def read_pfm(path):
    with open(path, 'rb') as f:
        assert f.readline().strip() == b'PF'; w, h = map(int, f.readline().split()); scale = float(f.readline())
        data = np.frombuffer(f.read(), dtype='<f4' if scale < 0 else '>f4')
    return data.reshape(h, w, 3)
def load_exr(path):
    img = bpy.data.images.load(str(path)); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
    bpy.data.images.remove(img); return px
def blur(a, radius):
    for axis in (0, 1):
        for _ in range(3):
            c = np.cumsum(np.pad(a, [(radius + 1, radius) if i == axis else (0, 0) for i in range(3)], mode='edge'), axis=axis)
            a = (np.take(c, range(2 * radius + 1, c.shape[axis]), axis=axis) - np.take(c, range(0, c.shape[axis] - 2 * radius - 1), axis=axis)) / (2 * radius + 1)
    return a

def render(name):
    global COLL
    kind, cam_pos, target, lens = VIEWS[name]
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'Blender/The_Commons_Compact.blend')); s = bpy.context.scene
    CACHE.clear()   # materials do not survive reopening the file
    COLL = bpy.data.collections.new('NEON_Preview'); s.collection.children.link(COLL)
    cam_loc = Vector(cam_pos); look_at = Vector(target)
    if kind == 'cafe':
        primary, secondary, k = build_lasers(LASER_MOMENT, np.array([cam_loc.x, cam_loc.z, cam_loc.y]))
        cafe_palette(tuple(primary), tuple(secondary), k)
        res = (1440, 900)
    else:
        cutaway = kind == 'kart_cutaway'
        for o in bpy.data.objects:
            if o.type in {'MESH', 'FONT', 'LIGHT'}:
                group = o.users_collection[0].name if o.users_collection else ''
                o.hide_render = not group.startswith('KART_') or (cutaway and group in {'KART_Roof', 'KART_ShellSouth', 'KART_ShellEast', 'KART_Trusses'})
        build_neon()
        s.world.use_nodes = True; bg = s.world.node_tree.nodes.get('Background')
        if bg: bg.inputs[0].default_value = (.008, .012, .026, 1); bg.inputs[1].default_value = .15
        # Standard view transform: no tone mapping, as Unity draws the hall without a
        # tonemapper; AgX would desaturate the neon towards pastel.
        s.view_settings.view_transform = VIEW_TRANSFORM; s.view_settings.look = 'None'; s.view_settings.exposure = EXPOSURE
        s.cycles.max_bounces = 4
        res = (1600, 1000)
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.clip_end = 900; cam.clip_start = .05
    camera = bpy.data.objects.new(name, cam); s.collection.objects.link(camera)
    camera.location = cam_loc; camera.rotation_euler = (look_at - cam_loc).to_track_quat('-Z', 'Y').to_euler(); s.camera = camera
    s.render.engine = 'CYCLES'; s.cycles.samples = SAMPLES; s.cycles.use_denoising = False
    s.cycles.sample_clamp_indirect = 6.0; s.render.threads_mode = 'FIXED'; s.render.threads = os.cpu_count() or 4
    s.render.resolution_x, s.render.resolution_y = res; s.render.resolution_percentage = PERCENT
    vl = s.view_layers[0]; vl.cycles.denoising_store_passes = True
    tmp = Path(tempfile.mkdtemp())
    s.use_nodes = True; nt = s.node_tree; nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite'); nt.links.new(rl.outputs['Image'], comp.inputs['Image'])
    fo = nt.nodes.new('CompositorNodeOutputFile'); fo.base_path = str(tmp); fo.format.file_format = 'OPEN_EXR'; fo.format.color_depth = '32'
    fo.file_slots.clear()
    for slot, socket in (('color', 'Image'), ('albedo', 'Denoising Albedo'), ('normal', 'Denoising Normal')):
        fo.file_slots.new(slot); nt.links.new(rl.outputs[socket], fo.inputs[slot])
    s.render.filepath = str(tmp / 'noisy.png'); bpy.ops.render.render(write_still=True)
    frame_no = '%04d' % s.frame_current
    color = load_exr(tmp / f'color{frame_no}.exr')
    if OIDN:
        write_pfm(tmp / 'c.pfm', color); write_pfm(tmp / 'a.pfm', load_exr(tmp / f'albedo{frame_no}.exr')); write_pfm(tmp / 'n.pfm', load_exr(tmp / f'normal{frame_no}.exr'))
        env = dict(os.environ, LD_LIBRARY_PATH=str(Path(OIDN).resolve().parents[1] / 'lib'))
        subprocess.run([OIDN, '--hdr', str(tmp / 'c.pfm'), '--alb', str(tmp / 'a.pfm'), '--nrm', str(tmp / 'n.pfm'), '-o', str(tmp / 'o.pfm'), '-q', 'high'], check=True, env=env)
        color = read_pfm(tmp / 'o.pfm').copy()
    # Soft fog glow like the earlier release renders (Glare FOG_GLOW, threshold 1.1).
    color = color + .35 * blur(np.maximum(color - 1.1, 0), 18)
    h, w, _ = color.shape
    out = bpy.data.images.new(name, w, h, float_buffer=True)
    out.pixels = np.concatenate([color, np.ones((h, w, 1), np.float32)], -1).ravel()
    s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'; s.render.image_settings.color_depth = '8'
    out.save_render(filepath=str(ROOT / 'Preview' / f'{name}.png'), scene=s)
    print('COMPLETE', name, 'denoised' if OIDN else 'raw', flush=True)

for view in ARGS or VIEWS:
    render(view)
