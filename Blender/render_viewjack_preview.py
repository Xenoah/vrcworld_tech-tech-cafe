"""View-jack design preview: the overlay math of Shaders/CommonsViewJack.shader
ported to numpy and composited over the v0.10.0 Blender renders.

Each quadrant uses that render's camera lens to rebuild per-pixel view
directions, then applies one channel at a representative strength and a fixed
time (motion ON). This is a design check, not a Unity/VRChat capture.

    python3 Blender/render_viewjack_preview.py    (after render_experience_views.py)
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'Preview'
CYAN = np.array([.05, .78, 1.0]); VIOLET = np.array([.82, .25, 1.0])

def frac(x): return x - np.floor(x)
def hash11(p):
    p = frac(p * .1031); p = p * (p + 33.33); p = p * (p + p); return frac(p)
def hash21(x, y):
    q = frac(np.stack([x, y, x], -1) * .1031); q = q + (q * (q[..., [1, 2, 0]] + 33.33)).sum(-1, keepdims=True)
    return frac((q[..., 0] + q[..., 1]) * q[..., 2])
def hash31(c):
    p = frac(c * .1031); p = p + (p * (p[..., [2, 1, 0]] + 31.32)).sum(-1, keepdims=True)
    return frac((p[..., 0] + p[..., 1]) * p[..., 2])

def directions(w, h, lens):
    """Camera-space view directions (x right, y up, z forward) for a 36 mm sensor."""
    half = 18.0 / lens
    x = ((np.arange(w) + .5) / w * 2 - 1) * half
    y = -((np.arange(h) + .5) / h * 2 - 1) * half * h / w
    X, Y = np.meshgrid(x, y); d = np.stack([X, Y, np.ones_like(X)], -1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)

def over(acc, color, a):
    a = np.clip(a, 0, 1)[..., None]
    rgb = color * a + acc[..., :3] * (1 - a); alpha = a[..., 0] + acc[..., 3] * (1 - a[..., 0])
    return np.concatenate([rgb, alpha[..., None]], -1)

def effect(d, kind, strength, t=7.3, world=None):
    r = np.arccos(np.clip(d[..., 2], -1, 1)) / 1.5708
    p = d[..., :2] / np.maximum(d[..., 2:3], .12)
    phi = np.arctan2(d[..., 1], d[..., 0]) / 6.28318 + .5
    acc = np.zeros(d.shape[:2] + (4,)); add = np.zeros(d.shape[:2] + (3,))
    s = strength
    if kind == 'warp':
        lanes = 96; lane = np.floor(phi * lanes); h = hash11(lane + 7.3)
        flow = frac(r * 2.4 - t * (1.1 + h * 1.7) + h * 9.1)
        streak = np.clip(flow / .06, 0, 1) * (1 - np.clip((flow - .06) / .44, 0, 1))
        streak *= np.clip((1 - np.abs(frac(phi * lanes) - .5) * 2 - .15) / .7, 0, 1) * (h >= .52) * np.clip((r - .12) / .68, 0, 1)
        acc = over(acc, np.array([.004, .012, .035]), np.clip((r - .22) / .56, 0, 1) * .6 * s)
        add += (CYAN * (1 - h[..., None]) + VIOLET * h[..., None]) * (streak * 1.7 * s)[..., None]
        add += CYAN * (np.exp(-r * r * 36) * .45 * s)[..., None]
    if kind == 'glitch':
        slot = np.floor(t * 2.0); band = np.floor(d[..., 1] * 14 + slot * 3.7); hb = hash11(band + slot * 13.1)
        g = np.where((hb > .88)[..., None], VIOLET, CYAN); on = (hb >= .74).astype(float)
        acc = over(acc, g * .55, on * .28 * s)
        add += g * (on * (.5 + .5 * np.sin(d[..., 1] * 900)) ** 4 * .22 * s)[..., None]
        hk = hash21(np.floor(p[..., 0] * 18 + slot), np.floor(p[..., 1] * 10 + slot))
        add += np.array([.6, .9, 1]) * ((hk >= .968) * .45 * s)[..., None]
        acc = over(acc, np.zeros(3), np.clip((r - .45) / .4, 0, 1) * .35 * s)
    if kind == 'rain':
        qx = p[..., 0] * 26; qy = p[..., 1] * 14; col = np.floor(qx); hc = hash11(col * 1.7 + .3)
        y = qy * .16 + t * (.7 + hc * 1.5) + hc * 10; trail = (1 - frac(y)) ** 5
        glyph = (hash21(col, np.floor(qy * 1.6)) >= .42); thin = np.clip(1 - np.abs(frac(qx) - .5) / .36, 0, 1)
        add += np.array([.25, 1, .72]) * (trail * thin * glyph * (hc >= .38) * np.clip((r - .14) / .41, 0, 1) * .55 * s)[..., None]
    if kind == 'stars':
        sw = world * 150; cell = np.floor(sw); hs = hash31(cell)
        off = np.stack([hash31(cell + 1.7), hash31(cell + 3.1), hash31(cell + 5.3)], -1) - .5
        star = (hs >= .982) * np.clip(1 - np.linalg.norm(frac(sw) - .5 - off * .4, axis=-1) / .3, 0, 1)
        mask = np.clip((r - .2) / .42, 0, 1)
        acc = over(acc, np.array([0, .008, .03]), mask * .55 * s)
        add += np.array([.82, .9, 1]) * (star * mask * 1.2 * s)[..., None]
    acc[..., :3] += add * (1 - acc[..., 3:4] * .5)
    return acc

def composite(name, lens, kind, strength):
    img = Image.open(PREVIEW / f'{name}.png').convert('RGB')
    w, h = img.size; base = (np.asarray(img).astype(np.float32) / 255) ** 2.2
    d = directions(w, h, lens)
    world = d @ np.array([[1, 0, 0], [0, .94, .34], [0, -.34, .94]])   # stars stay put in the world, not in the visor
    acc = effect(d, kind, strength, world=world)
    out = acc[..., :3] + base * (1 - acc[..., 3:4])
    return Image.fromarray((np.clip(out, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8))

def main():
    tiles = [('39_Orbit_Lift', 17, 'warp', .9, 'WARP  -  portal / lift'), ('36_DataStream_Atrium', 20, 'glitch', .9, 'GLITCH  -  phasing through glass'),
             ('37_DataStream_Skyline', 14, 'rain', 1.0, 'DATA RAIN  -  helix dive'), ('35_Orbit_Deck', 22, 'stars', .8, 'STARS  -  orbit deck')]
    W, H = 1440, 900; sheet = Image.new('RGB', (W, H))
    try: font = ImageFont.truetype(str(ROOT / 'Blender/Fonts/DejaVuSans-Bold.ttf'), 22)
    except OSError: font = ImageFont.load_default()
    for i, (name, lens, kind, strength, label) in enumerate(tiles):
        tile = composite(name, lens, kind, strength).resize((W // 2, H // 2), Image.LANCZOS)
        draw = ImageDraw.Draw(tile); draw.rectangle((0, H // 2 - 40, W // 2, H // 2), fill=(8, 12, 20)); draw.text((16, H // 2 - 33), label, fill=(210, 230, 255), font=font)
        sheet.paste(tile, ((i % 2) * W // 2, (i // 2) * H // 2))
    sheet.save(PREVIEW / '40_ViewJack_Effects.png', optimize=True)
    print('COMPLETE 40_ViewJack_Effects')

if __name__ == '__main__':
    main()
