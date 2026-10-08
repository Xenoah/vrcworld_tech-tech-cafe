"""Draw the current kart plan and long section from the exported manifest.

Python: numpy, Pillow. Output: Preview/Design/09_Kart_Plan_v07.png.
Deck outlines, heights, stations and turn positions come from model_manifest.json.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
K = json.loads((ROOT / 'Documentation/model_manifest.json').read_text())['kart']
P = np.array(K['centerline']); T = np.array(K['tangents']); D = np.array(K['stations'])
N = np.column_stack([-T[:, 1], T[:, 0]]); origin = np.array(K['origin']); levels = K['levels']
half = K['deck_half_width']; count = len(P); L = P.copy(); L[:, :2] -= origin[:2]
PAPER, INK, MUTED, RULE = '#F5F4EF', '#16263A', '#5C6B7B', '#CAD3D8'
LEVEL = [np.array(c) for c in [(35, 125, 224), (146, 97, 201), (19, 172, 181)]]
font = lambda size, bold=False: ImageFont.truetype(str(ROOT / 'Blender/Fonts' / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')), size)

def colour(z):
    t = np.clip((z - levels[0]) / (levels[1] - levels[0]), 0, 2)
    c = LEVEL[0] + (LEVEL[1] - LEVEL[0]) * min(t, 1) if t <= 1 else LEVEL[1] + (LEVEL[2] - LEVEL[1]) * (t - 1)
    return tuple(int(v) for v in c)

W, H, S, X0, Y0 = 2200, 1440, 7.6, 70, 1345
img = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(img)
f = lambda x, y: (X0 + x * S, Y0 - y * S)
d.text((70, 28), 'APEX / NEON SWITCHYARD  v%s' % K['version'], fill=INK, font=font(34, True))
d.text((70, 74), '%.2f m  /  %d turns  /  levels %.2f, %.2f, %.2f m  /  max grade %.2f%%  /  max bank %.0f deg' % (
    K['length_m'], K['turns'], *levels, max(abs(np.diff(P[:, 2])) / np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1)) * 100, K['maximum_bank_deg']), fill=MUTED, font=font(22))
# Hall outline, 10 m grid and the pit complex footprint.
for x in range(0, 149, 10): d.line([f(x, 0), f(x, 160)], fill=RULE if x % 50 else '#AEBAC2', width=1)
for y in range(0, 161, 10): d.line([f(0, y), f(148, y)], fill=RULE if y % 50 else '#AEBAC2', width=1)
d.rectangle([f(0, 160), f(148, 0)], outline=INK, width=3)
pits = K['pit_indices']; mid = L[pits[len(pits) // 2]]
d.rectangle([f(mid[0] - 24, mid[1] - 3.6), f(mid[0] + 24, mid[1] - 29.5)], outline=MUTED, width=2)
d.text(f(mid[0] - 22, mid[1] - 16), 'PIT APRON / GRANDSTAND', fill=MUTED, font=font(16))
# Deck quads drawn low to high so every crossing shows the upper deck on top.
for i in sorted(range(count), key=lambda k: (P[k, 2] + P[(k + 1) % count, 2]) / 2):
    j = (i + 1) % count; q = [L[i, :2] + N[i] * half, L[j, :2] + N[j] * half, L[j, :2] - N[j] * half, L[i, :2] - N[i] * half]
    d.polygon([f(*p) for p in q], fill=colour((P[i, 2] + P[j, 2]) / 2))
    for side in (1, -1): d.line([f(*(L[i, :2] + N[i] * half * side)), f(*(L[j, :2] + N[j] * half * side))], fill=PAPER, width=2)
for i in range(0, count, 18):
    a = L[i, :2] - T[i] * .9; b = L[i, :2] + T[i] * .9; d.line([f(*a), f(*b)], fill=PAPER, width=3)
s = pits[-1]; d.line([f(*(L[s, :2] + N[s] * half)), f(*(L[s, :2] - N[s] * half))], fill=INK, width=6)
d.text(f(L[s, 0] + 1.5, L[s, 1] - 4.5), 'START', fill=INK, font=font(16, True))
# Turn numbers beside each apex, at the candidate farthest from every deck and earlier label.
placed = []
for t in K['turn_markers']:
    a = np.array(t['apex'][:2]) - origin[:2]; k = int(np.argmin(np.linalg.norm(L[:, :2] - a, axis=1)))
    options = [a + N[k] * side * r for side in (1, -1) for r in (5.6, 7.2, 9.0)]
    score = lambda q: min([np.linalg.norm(L[:, :2] - q, axis=1).min() - half] + [np.linalg.norm(q - o) - 4.2 for o in placed]) - .05 * np.linalg.norm(q - a)
    p = max(options, key=score); placed.append(p); x, y = f(*p); label = t['id'][1:]
    d.ellipse([x - 15, y - 15, x + 15, y + 15], fill=INK); d.text((x, y), label, fill=PAPER, font=font(15, True), anchor='mm')
for x in (0, 50, 100, 148): d.text((f(x, 0)[0], Y0 + 12), '%d' % x, fill=MUTED, font=font(15), anchor='ma')
for y in (0, 50, 100, 160): d.text((X0 - 10, f(0, y)[1]), '%d' % y, fill=MUTED, font=font(15), anchor='rm')
d.text((X0 + 148 * S / 2, Y0 + 36), 'hall X (m), north up', fill=MUTED, font=font(15), anchor='ma')
# Legend and long section.
lx = X0 + 148 * S + 70; d.text((lx, 150), 'DECK HEIGHT', fill=INK, font=font(20, True))
for k, (name, z) in enumerate(zip(['LOWER  REACTOR', 'MIDDLE  CROSSFIRE', 'UPPER  SKYLINE'], levels)):
    d.rectangle([lx, 190 + k * 40, lx + 46, 214 + k * 40], fill=colour(z)); d.text((lx + 60, 202 + k * 40), '%s  +%.2f m' % (name, z), fill=INK, font=font(18), anchor='lm')
d.text((lx, 320), 'Dark circles: turn numbers (painted on the road before each turn).', fill=MUTED, font=font(16))
d.text((lx, 346), 'Upper decks are drawn above lower decks at crossings.', fill=MUTED, font=font(16))
px, py, pw, ph = lx, 470, W - lx - 70, 420
d.text((px, py - 50), 'LONG SECTION  (height x 10)', fill=INK, font=font(20, True))
d.rectangle([px, py, px + pw, py + ph], outline=RULE, width=2)
total = float(K['length_m']); g = lambda s_, z: (px + pw * s_ / total, py + ph - 30 - z * 10 * ph / 120)
for z in levels: d.line([g(0, z), g(total, z)], fill=RULE, width=1); d.text((px - 8, g(0, z)[1]), '%.2f' % z, fill=MUTED, font=font(14), anchor='rm')
for i in range(count - 1): d.line([g(D[i], P[i, 2]), g(D[i + 1], P[i + 1, 2])], fill=colour(P[i, 2]), width=5)
for t in K['turn_markers']:
    x, y = g(t['station_m'], t['apex'][2]); d.line([(x, y - 8), (x, y - 26)], fill=MUTED, width=1)
    d.text((x, y - 30), t['id'][1:], fill=INK, font=font(12), anchor='mb')
for s_ in range(0, int(total) + 1, 200): d.text(g(s_, 0)[0:1] + (py + ph + 8,), '%d m' % s_, fill=MUTED, font=font(14), anchor='ma')
out = ROOT / 'Preview/Design/09_Kart_Plan_v07.png'; img.save(out, optimize=True)
print('KART PLAN', out.relative_to(ROOT), img.size)
