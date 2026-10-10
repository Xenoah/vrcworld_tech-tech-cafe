"""v0.10.0 release previews: the actual model plus the experience layer.

Opens Blender/The_Commons_Compact.blend (the real cafe, city and lighting) and
adds the experience geometry that CommonsExperienceBuilder generates in Unity,
rebuilt here from Unity/Assets/TheCommons/Data/experience_layout.json with the
same dimensions: ORBIT DECK, DATA STREAM cars at baked ride poses, KOMO, the
ORBIT lift and the EXPERIENCE panel. Rendered with Cycles; when an Intel Open
Image Denoise CLI is given, the albedo/normal passes are used to denoise.

These are Blender previews, not Unity/VRChat runtime captures: Unity draws the
new objects with toon/holo shaders, light probes and its own post effects.

blender -b Blender/The_Commons_Compact.blend --python Blender/render_experience_views.py -- \
    [VIEW ...] [--samples N] [--oidn /path/to/oidnDenoise]
"""
from pathlib import Path
import bpy, math, sys, subprocess, tempfile, os
from mathutils import Vector, Quaternion, Euler
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Blender'))
import build_experience_layout as L   # same spline, cues, deck and KOMO data as the Unity bake

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default):
    if name in ARGS:
        i = ARGS.index(name); value = ARGS[i + 1]; del ARGS[i:i + 2]; return value
    return default
SAMPLES = int(option('--samples', '48'))
PERCENT = int(option('--percent', '100'))
OIDN = option('--oidn', '')
WARM = ((1, .49, .18), (1, .76, .40))           # CommonsLightingModes WARM palette (default mode)

def U(x, y, z): return Vector((x, z, y))        # Unity (X, Y up, Z) -> Blender (X, Y, Z up)
def UL(v): return Vector((v[0], v[2], v[1]))
def ueuler(x, y, z):                            # Unity Euler (ZXY, left-handed) -> Blender
    return Euler((math.radians(-x), math.radians(-z), math.radians(-y)), 'YXZ')

# ------------------------------------------------------------- ride bake
def bake():
    """Mirror of CommonsExperienceBuilder.Bake (positions, tangents, times, roll)."""
    S = L.S; n = L.N; count = n * S + 1
    pos = np.array([L.cr(k / S) for k in range(count)])
    v = np.array([max(.3, L.speed(k / S)) for k in range(count)])
    t = np.zeros(count)
    for k in range(1, count): t[k] = t[k - 1] + np.linalg.norm(pos[k] - pos[k - 1]) / max(.3, (v[k - 1] + v[k]) * .5)
    tan = np.zeros_like(pos)
    for k in range(count):
        a = pos[count - 2 if k == 0 else k - 1]; b = pos[1 if k == count - 1 else k + 1]
        d = b - a; tan[k] = d / max(1e-6, np.linalg.norm(d))
    raw = np.zeros(count)
    for k in range(count):
        ka = count - 2 if k == 0 else k - 1; kb = 1 if k == count - 1 else k + 1
        ds = max(.01, np.linalg.norm(pos[kb] - pos[ka])); curv = (tan[kb] - tan[ka]) / ds
        right = np.cross([0, 1, 0], tan[k]); right /= max(1e-6, np.linalg.norm(right))
        lateral = v[k] ** 2 * np.dot(curv, right)
        raw[k] = np.clip(-math.degrees(math.atan(lateral / 9.81)) * .55, -28, 28)
    roll = np.array([np.mean([raw[(k + d) % (count - 1)] for d in range(-8, 9)]) for k in range(count)])
    return pos, tan, t, roll
POS, TAN, TIME, ROLL = bake()
def pose_near(target):
    k = int(np.argmin(np.linalg.norm(POS - np.array(target), axis=1))); return k
def pose(k):
    p = POS[k]; d = TAN[k]
    q = UL(d).normalized().to_track_quat('Y', 'Z') @ Quaternion((0, 1, 0), math.radians(-ROLL[k]))
    return U(*p), q

# ------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    return m, nt, nt.nodes.new('ShaderNodeOutputMaterial')
def emission(name, color, strength):
    m, nt, out = node_mat(name); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength; nt.links.new(e.outputs[0], out.inputs[0]); return m
def toon(name, color, rough=.45, metal=0., glow=None, glow_strength=0.):
    """Principled stand-in for 'Experience Toon'; a small self-light mimics its minimum-light floor."""
    m, nt, out = node_mat(name); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    p.inputs['Emission Color'].default_value = (*(glow or color), 1)
    p.inputs['Emission Strength'].default_value = glow_strength if glow else .03
    nt.links.new(p.outputs[0], out.inputs[0]); return m
def glass(name, color=(.6, .8, .85)):
    m, nt, out = node_mat(name); g = nt.nodes.new('ShaderNodeBsdfGlass'); g.inputs[0].default_value = (*color, 1); g.inputs[1].default_value = .02
    t = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader'); mix.inputs[0].default_value = .35
    nt.links.new(t.outputs[0], mix.inputs[1]); nt.links.new(g.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0]); return m
def fading_emission(name, color, strength, z0, z1):
    """Emission that fades with height, like Holo Field's _FadeTop."""
    m, nt, out = node_mat(name); geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = z0; mr.inputs[2].default_value = z1; mr.inputs[3].default_value = strength; mr.inputs[4].default_value = 0
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1)
    t = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(geo.outputs['Position'], sep.inputs[0]); nt.links.new(sep.outputs[2], mr.inputs[0]); nt.links.new(mr.outputs[0], e.inputs[1])
    nt.links.new(e.outputs[0], add.inputs[0]); nt.links.new(t.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs[0]); return m
def image_emission(name, pixels, strength=1.4):
    h, w, _ = pixels.shape; img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels = np.flipud(pixels).astype(np.float32).ravel()
    m, nt, out = node_mat(name); tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[1].default_value = strength
    nt.links.new(tex.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], out.inputs[0]); return m

# ------------------------------------------------------------- geometry
COLL = None
def link(o):
    COLL.objects.link(o); return o
def mesh_object(name, verts, faces, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    if mat: me.materials.append(mat)
    return link(bpy.data.objects.new(name, me))
def cube(name, loc, dims, mat, parent=None, rot=None):
    h = Vector(dims) / 2; vs = [Vector((sx * h.x, sy * h.y, sz * h.z)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    o = mesh_object(name, vs, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], mat)
    o.parent = parent; o.location = loc
    if rot is not None: o.rotation_euler = rot
    return o
def cylinder(name, loc, radius, depth, mat, segments=64, caps=True, parent=None, rot=None):
    vs = []; fs = []
    for i in range(segments):
        a = 2 * math.pi * i / segments; vs += [Vector((radius * math.cos(a), radius * math.sin(a), -depth / 2)), Vector((radius * math.cos(a), radius * math.sin(a), depth / 2))]
    for i in range(segments):
        j = (i + 1) % segments; fs.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    if caps: fs += [tuple(2 * i for i in reversed(range(segments))), tuple(2 * i + 1 for i in range(segments))]
    o = mesh_object(name, vs, fs, mat); o.parent = parent; o.location = loc
    if rot is not None: o.rotation_euler = rot
    return o
def sphere(name, loc, dims, mat, parent=None, rings=16, segments=32):
    vs = [Vector((0, 0, -1))]; fs = []
    for r in range(1, rings):
        phi = math.pi * r / rings - math.pi / 2
        for s in range(segments):
            th = 2 * math.pi * s / segments; vs.append(Vector((math.cos(phi) * math.cos(th), math.cos(phi) * math.sin(th), math.sin(phi))))
    vs.append(Vector((0, 0, 1))); top = len(vs) - 1
    for s in range(segments): fs.append((0, 1 + (s + 1) % segments, 1 + s))
    for r in range(rings - 2):
        for s in range(segments):
            a = 1 + r * segments + s; b = 1 + r * segments + (s + 1) % segments; fs.append((a, b, b + segments, a + segments))
    base = 1 + (rings - 2) * segments
    for s in range(segments): fs.append((base + s, base + (s + 1) % segments, top))
    vs = [Vector((v.x * dims[0] / 2, v.y * dims[1] / 2, v.z * dims[2] / 2)) for v in vs]
    o = mesh_object(name, vs, fs, mat); o.parent = parent; o.location = loc
    for p in o.data.polygons: p.use_smooth = True
    return o
def torus(name, loc, major, minor, mat, segments=96, sides=8, parent=None, rot=None):
    vs = []; fs = []
    for i in range(segments):
        a = 2 * math.pi * i / segments; c = Vector((math.cos(a), math.sin(a), 0))
        for j in range(sides):
            b = 2 * math.pi * j / sides; vs.append(c * (major + minor * math.cos(b)) + Vector((0, 0, minor * math.sin(b))))
    for i in range(segments):
        for j in range(sides):
            a = i * sides + j; b = ((i + 1) % segments) * sides + j; c = ((i + 1) % segments) * sides + (j + 1) % sides; d = i * sides + (j + 1) % sides
            fs.append((a, b, c, d))
    o = mesh_object(name, vs, fs, mat); o.parent = parent; o.location = loc
    if rot is not None: o.rotation_euler = rot
    for p in o.data.polygons: p.use_smooth = True
    return o
def annulus(name, loc, inner, outer, mat, segments=128):
    vs = []; fs = []
    for i in range(segments):
        a = 2 * math.pi * i / segments; d = Vector((math.cos(a), math.sin(a), 0)); vs += [d * inner, d * outer]
    for i in range(segments):
        j = (i + 1) % segments; fs.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    o = mesh_object(name, vs, fs, mat); o.location = loc; return o
def wire(o, thickness):
    mod = o.modifiers.new('Wire', 'WIREFRAME'); mod.thickness = thickness; mod.use_replace = True; return o
FONT = None
def text(body, loc, size, yaw, mat, flat=False, parent=None):
    """TextMesh stand-in. Unity yaw faces the readable side like CommonsWorldBuilder.Label."""
    cu = bpy.data.curves.new('Text', 'FONT'); cu.body = body; cu.size = size; cu.font = FONT
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.space_line = 1.05
    o = link(bpy.data.objects.new('Text', cu)); o.data.materials.append(mat); o.parent = parent
    o.location = loc; o.rotation_euler = (0, 0, math.radians(-yaw)) if flat else (math.radians(90), 0, math.radians(-yaw))
    return o

# ------------------------------------------------------------- KOMO face
def face_pixels(expression, blush=0., w=256, h=192):
    """Numpy port of The Commons/Komo Face (neutral 0, happy 1, surprised 3)."""
    yy, xx = np.mgrid[0:h, 0:w]; p = np.stack([(xx + .5) / w - .5, .5 - (yy + .5) / h], -1)
    def box(q, b, r):
        d = np.abs(q) - np.array(b) + r
        return np.linalg.norm(np.maximum(d, 0), axis=-1) + np.minimum(np.maximum(d[..., 0], d[..., 1]), 0) - r
    def arc(q, rad, wd):
        ring = np.abs(np.linalg.norm(q, axis=-1) - rad) - wd
        ends = np.linalg.norm(np.stack([np.abs(q[..., 0]) - rad, q[..., 1]], -1), axis=-1) - wd
        return np.where(q[..., 1] < 0, ends, ring)
    def eye(q):
        if expression == 1: return arc(q + np.array([0, .03]), .075, .022)
        if expression == 3: return np.abs(np.linalg.norm(q, axis=-1) - .095) - .028
        return box(q, (.075, .11), .06)
    q = p - np.array([0, .05])
    d = np.minimum(eye(q - np.array([-.17, 0])), eye(q - np.array([.17, 0])))
    m = p - np.array([0, -.17]); mouth = np.abs(np.linalg.norm(m - np.array([0, .06]), axis=-1) - .075) - .012
    mouth = np.where(m[..., 1] > -.005, 1, mouth); d = np.minimum(d, mouth)
    edge = 1 - np.clip(d / .012, 0, 1); glow = np.exp(-np.maximum(d, 0) * 38) * .35
    vign = np.clip((.72 - np.linalg.norm(p * np.array([1, 1.15]), axis=-1)) / .37, 0, 1)
    c = np.array([.02, .035, .06]) * (.6 + .4 * vign)[..., None] + np.array([.35, .95, 1])[None, None] * (edge * 1.35 + glow)[..., None]
    for sx in (-.27, .27):
        b = np.exp(-(np.linalg.norm((p - np.array([sx, -.08])) * np.array([1, 1.6]), axis=-1) * 9) ** 2)
        c += np.array([1, .35, .45]) * (b * blush * .5)[..., None]
    return np.concatenate([np.clip(c, 0, 4), np.ones((h, w, 1))], -1)

def build_komo(root_loc, root_rot, expression, mats, held=None, bubble=None, camera_target=None):
    root = link(bpy.data.objects.new('NPC_KOMO', None)); root.location = root_loc
    root.rotation_mode = 'QUATERNION' if isinstance(root_rot, Quaternion) else 'XYZ'
    if isinstance(root_rot, Quaternion): root.rotation_quaternion = root_rot
    else: root.rotation_euler = root_rot
    face = image_emission('KomoFace_%d' % expression, face_pixels(expression, .8 if expression == 1 else 0.))
    sphere('Shell', UL((0, 0, 0)), UL((.46, .42, .42)), mats['shell'], root)
    plane = mesh_object('Face', [Vector((-.17, 0, -.125)), Vector((.17, 0, -.125)), Vector((.17, 0, .125)), Vector((-.17, 0, .125))], [(0, 1, 2, 3)], face)
    plane.data.uv_layers.new(); uv = plane.data.uv_layers[0].data
    for i, c in enumerate([(1, 0), (0, 0), (0, 1), (1, 1)]): uv[i].uv = c
    plane.parent = root; plane.location = UL((0, .02, .215))
    for side in (-1, 1):
        cylinder('Antenna', UL((side * .11, .25, -.02)), .01, .12, mats['dark'], 12, parent=root, rot=ueuler(0, 0, -side * 15))
        sphere('AntennaTip', UL((side * .13, .32, -.02)), (.055, .055, .055), mats['tip'], root, 8, 12)
    hands = {}
    for side, name in ((-1, 'L'), (1, 'R')):
        hands[name] = sphere('Hand' + name, UL((side * .3, -.05, .1)), (.1, .1, .1), mats['shell'], root, 8, 16)
    torus('OrbitRing', UL((0, -.02, 0)), .34, .016, mats['ring'], 64, 6, root, ueuler(14, 0, 8))
    cylinder('Thruster', UL((0, -.31, 0)), .1, .01, mats['ring'], 24, parent=root)
    if held == 'cup':
        hands['L'].location = UL((-.12, -.12, .3)); hands['R'].location = UL((.1, -.02, .3))
        cylinder('Mug', UL((-.12, -.03, .3)), .035, .09, mats['cup'], 24, parent=root)
        cylinder('Coffee', UL((-.12, .016, .3)), .03, .004, mats['coffee'], 24, parent=root)
    if held == 'cheer':
        hands['L'].location = UL((-.3, .45, 0)); hands['R'].location = UL((.3, .45, 0))
    if bubble and camera_target is not None:
        towards = camera_target - root_loc; towards.z = 0; towards.normalize()
        anchor = root_loc + Vector((0, 0, .62)) + towards * .4; back = cube('BubbleBack', anchor, (1.32, .01, .34), mats['bubble'])   # builder: local (0, .62, .4)
        direction = (camera_target - anchor); yaw = math.atan2(direction.x, -direction.y)
        back.rotation_euler = (0, 0, yaw)
        t = text(bubble, anchor + Vector((math.sin(yaw), -math.cos(yaw), 0)) * .02, .055, 0, mats['white'])
        t.rotation_euler = (math.radians(90), 0, yaw)
    return root

def build_car(name, k, mats, komo=None):
    loc, q = pose(k)
    car = link(bpy.data.objects.new(name, None)); car.location = loc; car.rotation_mode = 'QUATERNION'; car.rotation_quaternion = q
    cube('Chassis', UL((0, .16, 0)), UL((1.9, .32, 3.3)), mats['body'], car)
    sphere('Nose', UL((0, .3, 1.65)), UL((1.9, .55, 1.3)), mats['body'], car)
    cube('TailFin', UL((0, .55, -1.5)), UL((.08, .55, .7)), mats['accent'], car)
    for side in (-1, 1): cube('LightStrip', UL((side * .965, .26, 0)), UL((.03, .06, 3.0)), mats['strip'], car)
    for z in (.45, -.75):
        cube('LapBar', UL((0, .8, z + .3)), UL((1.5, .05, .05)), mats['steel'], car)
        for x in (-.45, .45):
            cube('Cushion', UL((x, .38, z)), UL((.52, .12, .5)), mats['seat'], car)
            cube('Back', UL((x, .72, z - .27)), UL((.52, .62, .08)), mats['seat'], car)
    letter = text(name[-1], UL((0, .55, -1.86)), .2, 0, mats['violet_text'], parent=car)
    if komo is not None:
        mount = loc + q @ UL((0, .82, 1.95)); build_komo(mount, q, komo, mats, 'cheer' if komo == 3 else None)
    return car

def unlink_baked_lamps(center, radius=4.0):
    """Unity bakes the cafe lamps; moving objects only see light probes. Exclude new
    experience objects from lamps (and emissive lamp meshes) within radius via light linking."""
    receivers = bpy.data.collections.new('EXP_ProbeLitOnly')
    for o in COLL.all_objects: receivers.objects.link(o)
    count = 0
    for o in bpy.data.objects:
        if o.name in receivers.objects or (o.users_collection and o.users_collection[0] == COLL): continue
        emissive = o.type == 'MESH' and any(sl.material and sl.material.use_nodes and any(
            n.type == 'BSDF_PRINCIPLED' and n.inputs['Emission Strength'].default_value > 0 for n in sl.material.node_tree.nodes) for sl in o.material_slots)
        if (o.type == 'LIGHT' or emissive) and (o.matrix_world.translation - center).length < radius + (max(o.dimensions) / 2 if o.type == 'MESH' else 0):
            o.light_linking.receiver_collection = receivers; count += 1
    for item in receivers.collection_objects: item.light_linking.link_state = 'EXCLUDE'
    print('light linking: excluded experience objects from', count, 'nearby baked lamps', flush=True)

# ------------------------------------------------------------- scene
def build_experience(s, camera_location):
    global COLL, FONT
    COLL = bpy.data.collections.new('EXP_Preview'); s.collection.children.link(COLL)
    FONT = bpy.data.fonts.load(str(ROOT / 'Blender/Fonts/DejaVuSans-Bold.ttf'))
    # RideBody is darker than Unity's pearl: Cycles lights it from the pendant lamps 1 m above; Unity uses probes.
    M = {
        'floor': toon('DeckFloor', (.12, .13, .16), .55), 'trim': toon('DeckTrim', (.72, .75, .8), .3, .6),
        'core': toon('DeckCore', (.05, .06, .09), .4, 0, (.02, .1, .25), 1.0),
        'cyan': emission('HoloCyan', (.05, .75, 1), 3.0), 'violet': emission('HoloViolet', (.62, .35, 1), 3.0),
        'amber': emission('HoloAmber', (1, .6, .25), 2.5), 'field': fading_emission('DeckField', (.1, .6, 1), 1.6, 120, 127),
        'glass': glass('DeckGlass'), 'planet_core': toon('PlanetCore', (.02, .05, .12), .3, 0, (.02, .12, .3), 2.0),
        'planet': emission('PlanetShell', (.15, .8, 1), 2.2), 'lane': emission('DockLane', (.05, .75, 1), .9),
        'body': toon('RideBody', (.40, .42, .46), .55), 'seat': toon('RideSeat', (.08, .09, .12), .6),
        'accent': toon('RideAccent', (.4, .25, .9), .3, 0, (.35, .18, .9), 2.5), 'strip': emission('RideStrip', (.05, .75, 1), 3.0),
        'shell': toon('KomoShell', (.78, .77, .74), .4), 'dark': toon('KomoDark', (.1, .11, .14), .5),
        'tip': toon('KomoTip', (1, .62, .25), .3, 0, (1, .5, .15), 4.0), 'ring': emission('KomoRing', (.1, .8, 1), 5.0),
        'cup': toon('KomoCup', (.96, .96, .94), .2), 'coffee': toon('KomoCoffee', (.25, .14, .07), .2),
        'bubble': emission('KomoBubble', (.02, .035, .07), 1.0), 'white': emission('TextWhite', (.95, .97, 1), 3.0),
        'label': emission('TextLabel', (.75, .88, 1), 1.6), 'violet_text': emission('TextViolet', (.78, .62, 1), 2.5),
        'steel': bpy.data.materials.get('MAT_Steel') or toon('Steel', (.5, .52, .55), .35, .8),
        'black': bpy.data.materials.get('MAT_Black') or toon('Black', (.02, .02, .02), .4),
        'frame': toon('LiftFrame', (.45, .3, .95), .3, 0, (.45, .25, 1), 3.0),
    }
    D = L.DECK; C = U(*D['center']); R = D['floor_radius']
    # Deck
    cylinder('Deck_Floor', C - Vector((0, 0, .3)), R, .6, M['floor'], 128)
    cylinder('Deck_Core', C - Vector((0, 0, 2)), R * .55, 2.8, M['core'], 96)
    annulus('Deck_WellRing', C + Vector((0, 0, .012)), D['well_radius'] - .12, D['well_radius'] + .12, M['violet'])
    annulus('Deck_MidRing', C + Vector((0, 0, .012)), 12, 12.12, M['cyan'])
    annulus('Deck_EdgeRing', C + Vector((0, 0, .012)), R - .35, R - .15, M['cyan'], 192)
    wire(cylinder('Deck_FieldGrid', C + Vector((0, 0, 3.5)), D['field_radius'], 7, M['field'], 96, caps=False), .025)
    cylinder('Deck_Parapet', C + Vector((0, 0, .55)), D['field_radius'] - .03, 1.1, M['glass'], 160, caps=False)
    torus('Deck_ParapetRail', C + Vector((0, 0, 1.1)), D['field_radius'] - .03, .03, M['trim'], 192, 6)
    text('GRAVITY WELL\nhold JUMP to float', C + Vector((0, -D['well_radius'] - .9, .03)), .16, 0, M['violet_text'], flat=True)
    planet = U(*D['planet']); pr = D['planet_radius']
    sphere('PlanetCore', planet, (pr * 1.84,) * 3, M['planet_core'])
    wire(sphere('PlanetShell', planet, (pr * 2,) * 3, M['planet'], None, 12, 24), .02)
    torus('PlanetRing', planet, pr * 1.6, .05, M['violet'], 96, 6, rot=ueuler(20, 0, 8))
    torus('Deck_Halo_A', C + Vector((0, 0, 9)), 14, .06, M['cyan'], 192, 6)
    torus('Deck_Halo_B', C + Vector((0, 0, 10.5)), 15.5, .05, M['amber'], 192, 6, rot=ueuler(6, 0, 0))
    lz0, lz1 = -6.0, 13.5
    cube('Deck_DockLane', U(26, D['center'][1] + .011, (lz0 + lz1) / 2), (1.9, lz1 - lz0, .002), M['lane'])
    rail_x = D['dock_rail_x']
    for x, a, b in ((rail_x, -4.0, D['dock_gate'][0]), (rail_x, D['dock_gate'][1], lz1), (27.6, lz0, lz1)):
        cube('Rail', U(x, 121.0, (a + b) / 2), (.06, b - a, .06), M['trim'])
        z = a
        while z <= b + .01: cube('RailPost', U(x, 120.5, z), (.05, .05, 1.0), M['trim']); z += 2
    text('DATA STREAM\nboard here', U(rail_x - .05, 122.35, sum(D['dock_gate']) / 2), .16, 90, M['label'])
    board = 'DATA STREAM\nCAR A  BOARDING  departs 0:18\nCAR B  ON THE STREAM  back 1:05\nSit to board. Leave any time: you return to this dock.'
    text(board, U(*D['dock_board']), .1, D['board_yaw'], M['label'])
    arrival = U(*D['arrival'])
    annulus('Deck_ArrivalPad', arrival + Vector((0, 0, .013)), .02, 1.0, M['violet'], 48)
    text('ORBIT DECK', arrival + U(0, 3.6, 6.5), .42, 0, M['violet_text'])
    text('GRAVITY WELL  /  DATA STREAM  /  SIZE LAB', arrival + U(0, 3.05, 6.5), .12, 0, M['label'])
    rp = D['return_portal']; portal(U(*rp), D['return_portal_yaw'], 'RETURN TO CAFE', 2.1, 2.4, M, M['violet'])
    lab = D['size_lab']; yaw = D['size_lab_yaw']
    panel(lab, yaw, 'SIZE LAB (LOCAL)\nNOW NORMAL\nGIANT works on this deck only', ['TINY x0.1', 'SMALL x0.5', 'NORMAL', 'GIANT x4'], .72, .2, .32, .27, .085, M)
    settings_panel(D['settings_panel'], D['settings_yaw'], M)
    # Cafe entrance: ORBIT lift and EXPERIENCE panel
    lift = L.LIFT; p = lift['portal']
    cube('Lift_Panel', U(*p), UL((1.9, .72, .12)), M['black'])
    text('GO TO ORBIT', U(p[0], p[1], p[2] - .072), .1, 0, M['white'])
    text('ORBIT', U(p[0], p[1] + 1.05, p[2] - .08), .3, 0, M['violet_text'])
    text('SKY DECK / DATA STREAM / SIZE LAB', U(p[0], p[1] + .72, p[2] - .08), .07, 0, M['label'])
    text('DATA STREAM\nCAR A  BOARDING  departs 0:18\nCAR B  ON THE STREAM  back 1:05', U(p[0], p[1] + 1.85, p[2] - .08), .05, 0, M['label'])
    frame(U(p[0], 0, p[2] + .06), lift['frame_width'], 2.9, 0, M['frame'])
    annulus('Lift_FloorPad', U(p[0], .02, p[2] - 1.2), .6, .85, M['violet'], 48)
    settings_panel([21.25, 1.92, 2.4], 90, M)          # experience_layout.json cafe_settings_panel / yaw
    return M

def frame(base, width, height, yaw, mat):
    r = math.radians(-yaw)
    for side in (-1, 1):
        off = Vector((side * width / 2 * math.cos(r), side * width / 2 * math.sin(r), height / 2))
        cube('FramePost', base + off, (.12, .16, height), mat, rot=(0, 0, r))
    cube('FrameTop', base + Vector((0, 0, height)), (width + .12, .16, .12), mat, rot=(0, 0, r))
def portal(center, yaw, title, width, frame_width, M, frame_mat):
    r = math.radians(-yaw); front = Vector((math.sin(r) * .072, -math.cos(r) * .072, 0))
    cube('Portal_' + title, center, (width, .12, .72), M['black'], rot=(0, 0, r))
    text(title, center + front, .11, yaw, M['white'])
    frame(center - Vector((0, 0, 1.3)) - front * .7, frame_width, 2.9, yaw, frame_mat)
def panel(p, yaw, label, titles, label_up, top, step, height, label_size, M):
    r = math.radians(-yaw); fwd = Vector((math.sin(r), -math.cos(r), 0)); right = Vector((math.cos(r), math.sin(r), 0))
    base = U(*p)
    text(label, base + Vector((0, 0, label_up)) + fwd * .05, label_size, yaw, M['label'])
    for i, t in enumerate(titles):
        c = base + right * ((i % 2 - .5) * 1.04) + Vector((0, 0, top - (i // 2) * step))
        cube('Button', c, (.98, .075, height), M['steel'], rot=(0, 0, r))
        text(t, c + fwd * .046, height * .35, yaw, M['white'])
def settings_panel(p, yaw, M):
    label = ('EXPERIENCE (LOCAL)\nVIEW FX SOFT / WARP ON / RIDE ON\nAMBIENT OFF / PULSE OFF / VIGNETTE ON\n'
             'MUSIC 4/5 / KOMO EN\nREDUCED MOTION: effects stay still')
    titles = ['VIEW FX OFF/SOFT/FULL', 'WARP ON / OFF', 'RIDE FX ON / OFF', 'AMBIENT FX', 'BEAT PULSE', 'RIDE VIGNETTE',
              'MUSIC -', 'MUSIC +', 'KOMO TALK / QUIET', 'KOMO EN / JP']
    panel(p, yaw, label, titles, .78, .3, .3, .25, .062, M)

VIEWS = {
    # name: (camera Unity position, target Unity position, lens mm)
    '35_Orbit_Deck': ((-6.0, 129.0, -12.0), (14.5, 119.5, 9.0), 22),
    '36_DataStream_Atrium': ((11.6, 6.35, 4.1), (15.0, 7.3, 10.6), 20),
    '37_DataStream_Skyline': (None, None, 14),
    '38_KOMO_Bar': ((3.3, 1.75, 10.7), (0.85, 1.75, 10.0), 32),
    '39_Orbit_Lift': ((18.4, 1.62, 0.55), (20.6, 1.75, 3.0), 17),
}

def warm_palette():
    clones = {}
    primary, secondary = WARM
    for o in bpy.data.objects:
        group = o.users_collection[0].name if o.users_collection else ''
        o.hide_render = group.startswith(('KART_', 'FPV_')) or group == 'MODE_Academic'
        if o.type == 'LIGHT' and not o.hide_render and 0 < o.location.x < 28:
            o.data.color = primary if sum(ord(c) for c in o.name) % 2 else secondary
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
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'Blender/The_Commons_Compact.blend')); s = bpy.context.scene
    warm_palette()
    cam_pos, target, lens = VIEWS[name]
    if name == '37_DataStream_Skyline':
        k = pose_near((56.0, 28.8, 25.0)); loc, q = pose(k)
        cam_loc = loc + q @ UL((-.45, 2.0, .1)); look = cam_loc + q @ UL((0, -.32, 1))
    else:
        cam_loc = U(*cam_pos); look = U(*target)
    M = build_experience(s, cam_loc)
    # Ride poses from the baked table: car A at the dock with KOMO (its ride slot),
    # or passing through the atrium; car B on the skyline for the rider view.
    if name == '35_Orbit_Deck': build_car('Car_A', 0, M, komo=1)
    if name == '36_DataStream_Atrium':
        k = pose_near((15.6, 7.25, 10.6)); build_car('Car_A', k, M, komo=3); unlink_baked_lamps(U(*POS[k]))
    if name == '37_DataStream_Skyline':
        build_car('Car_B', pose_near((56.0, 28.8, 25.0)), M)
    if name == '38_KOMO_Bar':
        spot = next(sp for sp in L.KOMO['spots'] if sp['name'] == 'Barista')
        build_komo(U(*spot['position']), ueuler(0, spot['yaw'], 0), 1, M, 'cup', 'Espresso, tea or soda -\nsame glass, same table.', cam_loc)
    if name == '39_Orbit_Lift':
        spot = next(sp for sp in L.KOMO['spots'] if sp['name'] == 'Greeter')
        build_komo(U(*spot['position']), ueuler(0, spot['yaw'], 0), 1, M)
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.clip_end = 900; cam.clip_start = .05
    camera = bpy.data.objects.new(name, cam); s.collection.objects.link(camera)
    camera.location = cam_loc; camera.rotation_euler = (look - cam_loc).to_track_quat('-Z', 'Y').to_euler(); s.camera = camera
    s.render.engine = 'CYCLES'; s.cycles.samples = SAMPLES; s.cycles.use_denoising = False
    s.cycles.sample_clamp_indirect = 6.0; s.render.threads_mode = 'FIXED'; s.render.threads = os.cpu_count() or 4
    s.render.resolution_x = 1440; s.render.resolution_y = 900; s.render.resolution_percentage = PERCENT
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
    target_png = ROOT / 'Preview' / f'{name}.png'
    out.save_render(filepath=str(target_png), scene=s)
    print('COMPLETE', name, 'denoised' if OIDN else 'raw', flush=True)

for view in ARGS or VIEWS:
    render(view)
