"""Neon sign textures for the kart hall's Neo-Tokyo dressing (v0.11).

Original wording only (no brands, no real road names). Glyphs are drawn as
glowing neon-tube outlines on dark boards with Noto Sans CJK JP (SIL OFL 1.1;
the font itself is not redistributed). Output: Unity/Assets/TheCommons/Media/Neon/*.png

    python3 Blender/build_kart_neon_signs.py [--font PATH]
"""
from pathlib import Path
import argparse, json
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Unity/Assets/TheCommons/Media/Neon'
FONTS = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc']
PINK, CYAN, AMBER, VIOLET, GREEN, RED, WHITE = (255, 60, 170), (40, 220, 255), (255, 170, 40), (170, 90, 255), (60, 255, 150), (255, 70, 60), (235, 240, 255)

# name: (lines, orientation, colour, secondary colour)
SIGNS = {
    'neon_tokyo_v': (['東', '京'], 'v', PINK, CYAN),
    'neon_dennou_v': (['電', '脳'], 'v', CYAN, VIOLET),
    'neon_kasoku_v': (['加', '速'], 'v', AMBER, PINK),
    'neon_yasou_v': (['夜', '走'], 'v', VIOLET, CYAN),
    'neon_touge_v': (['峠'], 'v1', AMBER, RED),
    'neon_mirai_v': (['未', '来'], 'v', GREEN, CYAN),
    'neon_neotokyo_h': (['ネオ東京', 'NEO TOKYO'], 'h', PINK, CYAN),
    'neon_switchyard_h': (['ネオン操車場', 'NEON SWITCHYARD'], 'h', CYAN, VIOLET),
    'neon_anzen_h': (['安全運転', 'DRIVE SAFE'], 'h', GREEN, AMBER),
    'neon_pass_banner': (['七曲峠', 'NANAMAGARI PASS  ·  7 HAIRPINS'], 'h', AMBER, RED),
    'neon_apex_h': (['頂点', 'APEX'], 'h', VIOLET, PINK),
}

def font(path, size):
    return ImageFont.truetype(path, size)

def neon_layer(size, draw_fn, colour, tube=7, glow=26):
    """Tube outline + soft glow, additive on black."""
    line = Image.new('RGB', size); d = ImageDraw.Draw(line); draw_fn(d, colour, tube)
    core = Image.new('RGB', size); d = ImageDraw.Draw(core); draw_fn(d, tuple(int(c * .35 + 255 * .65) for c in colour), max(2, tube // 3))
    halo = line.filter(ImageFilter.GaussianBlur(glow)); halo = Image.eval(halo, lambda v: min(255, int(v * 1.6)))
    near = line.filter(ImageFilter.GaussianBlur(glow / 4))
    return ImageChops.add(ImageChops.add(ImageChops.add(halo, near), line), core)

def board(size, colour):
    img = Image.new('RGB', size, (5, 7, 14)); d = ImageDraw.Draw(img)
    w, h = size; m = int(min(w, h) * .05)
    frame = neon_layer(size, lambda dr, c, t: dr.rounded_rectangle((m, m, w - m, h - m), radius=m, outline=c, width=max(3, t // 2)), colour, 6, 14)
    return ImageChops.add(img, Image.eval(frame, lambda v: int(v * .7)))

def outline_text(d, xy, text, f, colour, tube, anchor):
    # Stroke in colour, then the glyph fill in black: only the "tube" stays lit.
    d.text(xy, text, font=f, fill=colour, stroke_width=tube, stroke_fill=colour, anchor=anchor)
    d.text(xy, text, font=f, fill=(0, 0, 0), anchor=anchor)

def make(name, lines, orient, colour, second, fpath):
    if orient in ('v', 'v1'):
        size = (384, 1152); img = board(size, second)
        n = len(lines); cell = size[1] * .86 / n; f = font(fpath, int(min(size[0] * .74, cell * .82)))
        def draw(d, c, t):
            for i, ch in enumerate(lines): outline_text(d, (size[0] / 2, size[1] * .07 + cell * (i + .5)), ch, f, c, t, 'mm')
        img = ImageChops.add(img, neon_layer(size, draw, colour))
    else:
        size = (1280, 400); img = board(size, second)
        big = font(fpath, 170 if len(lines[0]) <= 5 else 140); small = font(fpath, 50 if len(lines[1]) < 20 else 40)
        def draw_big(d, c, t): outline_text(d, (size[0] / 2, size[1] * .42), lines[0], big, c, t, 'mm')
        def draw_small(d, c, t): d.text((size[0] / 2, size[1] * .82), lines[1], font=small, fill=c, anchor='mm')
        img = ImageChops.add(img, neon_layer(size, draw_big, colour))
        img = ImageChops.add(img, neon_layer(size, draw_small, second, 3, 10))
    img.save(OUT / f'{name}.png', optimize=True)
    return {'file': f'{name}.png', 'size': list(img.size), 'text': lines}

def vending(name, body, accent):
    """Generic vending-machine front: rows of glowing bottles and cans, no brands."""
    w, h = 384, 704; img = Image.new('RGB', (w, h), tuple(int(c * .18) for c in body)); d = ImageDraw.Draw(img)
    d.rectangle((24, 24, w - 24, h * .62), fill=(12, 16, 26))
    palette = [CYAN, PINK, AMBER, GREEN, VIOLET, RED, WHITE]
    for row in range(4):
        y0 = 44 + row * 98
        for col in range(5):
            x0 = 40 + col * 62; c = palette[(row * 5 + col * 3) % len(palette)]
            d.rounded_rectangle((x0, y0, x0 + 40, y0 + 70), radius=10, fill=tuple(int(v * .8) for v in c))
            d.rectangle((x0 + 4, y0 + 76, x0 + 36, y0 + 84), fill=(255, 210, 90))
    d.rectangle((40, h * .66, w - 40, h * .72), fill=accent)
    d.rectangle((w - 110, h * .76, w - 40, h * .84), fill=(30, 30, 40)); d.rectangle((60, h * .86, w - 60, h * .95), fill=(8, 8, 12))
    glow = img.filter(ImageFilter.GaussianBlur(10)); img = ImageChops.add(img, Image.eval(glow, lambda v: int(v * .6)))
    img.save(OUT / f'{name}.png', optimize=True)
    return {'file': f'{name}.png', 'size': [w, h], 'text': []}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--font'); args = ap.parse_args()
    fpath = args.font or next(p for p in FONTS if Path(p).exists())
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'font': Path(fpath).name, 'font_license': 'SIL Open Font License 1.1 (glyphs rendered into textures; font not redistributed)', 'signs': []}
    for name, (lines, orient, colour, second) in SIGNS.items(): report['signs'].append(make(name, lines, orient, colour, second, fpath))
    report['signs'].append(vending('neon_vending_a', (40, 120, 255), PINK))
    report['signs'].append(vending('neon_vending_b', (255, 60, 120), CYAN))
    (ROOT / 'Documentation/kart_neon_signs.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(len(report['signs']), 'textures')

if __name__ == '__main__':
    main()
