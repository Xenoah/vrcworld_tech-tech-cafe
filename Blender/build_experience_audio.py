"""Render THE COMMONS adaptive music stems and experience SFX.

Original material, synthesised from code (no samples, no third-party audio).
Seven stems share tempo (96 BPM), key (D major) and length (16 bars, 40 s),
so CommonsAdaptiveMusic can cross-fade any combination in sync. Every stem is
rendered over two loops and the second loop is kept, so reverb and delay tails
wrap seamlessly. Output: Unity/Assets/TheCommons/Audio/Experience/*.ogg
(libvorbis via ffmpeg) plus optional preview mixes.

    python3 Blender/build_experience_audio.py [--preview OUT_DIR]
"""
from pathlib import Path
import argparse, json, subprocess, tempfile, wave
import numpy as np
from scipy.signal import butter, lfilter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Unity/Assets/TheCommons/Audio/Experience'
SR = 44100
BPM = 96.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 16
LOOP = BAR * BARS                      # 40.0 s
N = int(round(LOOP * SR))              # 1,764,000 samples
TAIL = 6.0
rng = np.random.default_rng(20261010)

def midi(n): return 440.0 * 2 ** ((n - 69) / 12.0)

# Chords: (bass root, pad voicing) per bar. D major, lo-fi / city-pop colours.
CH = {
    'Dmaj9': (38, [54, 57, 61, 64]), 'Bm9': (35, [54, 57, 61, 62]), 'Gmaj9': (43, [54, 57, 59, 62]),
    'A69': (33, [52, 54, 59, 61]), 'F#m7': (42, [52, 57, 61, 64]), 'A13': (33, [55, 59, 61, 66]),
    'Em9': (40, [54, 55, 59, 62]), 'A7sus': (33, [52, 55, 57, 62]),
}
PROG = ['Dmaj9', 'Bm9', 'Gmaj9', 'A69', 'Dmaj9', 'F#m7', 'Gmaj9', 'A13',
        'Bm9', 'Gmaj9', 'Em9', 'A69', 'Gmaj9', 'F#m7', 'Em9', 'A7sus']
PENTA = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83]   # D major pentatonic, D4..B5

def buf(seconds=None):
    return np.zeros((2, int((2 * LOOP + TAIL) * SR) if seconds is None else int(seconds * SR)))

def place(dst, sig, start, pan=0.0, gain=1.0):
    """Mix a mono or stereo signal into dst at time start (s), both loops."""
    if sig.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
        sig = np.vstack([sig * l * 1.414, sig * r * 1.414])
    for loop in (0, 1):
        i = int(round((start + loop * LOOP) * SR))
        part = sig
        if i < 0: part = sig[:, -i:]; i = 0          # only loop two is kept, loop one may start early
        j = min(dst.shape[1], i + part.shape[1])
        if i < dst.shape[1] and j > i: dst[:, i:j] += part[:, :j - i] * gain

def env_adsr(n, a, d, s, r_len, sustain_n):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r_len * SR)
    e = np.zeros(n)
    k = np.arange(n)
    e[:a_n] = k[:a_n] / max(1, a_n)
    dd = np.arange(min(d_n, n - a_n))
    e[a_n:a_n + len(dd)] = 1 - (1 - s) * dd / max(1, d_n)
    e[a_n + d_n:sustain_n] = s
    rel = np.arange(max(0, n - sustain_n))
    level = e[sustain_n - 1] if sustain_n > 0 else s
    e[sustain_n:] = level * np.exp(-rel / max(1, r_n) * 4)
    return e

def polyblep_saw(freq, n, phase0=0.0):
    dt = freq / SR
    ph = (phase0 + dt * np.arange(n)) % 1.0
    y = 2 * ph - 1
    m = ph < dt; t = ph[m] / dt; y[m] -= t + t - t * t - 1
    m = ph > 1 - dt; t = (ph[m] - 1) / dt; y[m] -= t * t + t + t + 1
    return y

def lp(x, cutoff, order=2):
    sos = butter(order, cutoff / (SR / 2), 'low', output='sos'); return sosfilt(sos, x, axis=-1)

def hp(x, cutoff, order=2):
    sos = butter(order, cutoff / (SR / 2), 'high', output='sos'); return sosfilt(sos, x, axis=-1)

def bp(x, lo, hi, order=2):
    sos = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band', output='sos'); return sosfilt(sos, x, axis=-1)

def comb(x, delay, g):
    """y[n] = x[n] + g*y[n-d], evaluated block-wise (blocks of d samples)."""
    d = max(1, int(delay * SR)); y = np.array(x, dtype=float, copy=True)
    for k in range(d, len(y), d):
        e = min(len(y), k + d); y[k:e] += g * y[k - d:e - d]
    return y

def allpass(x, delay, g):
    """Schroeder all-pass y[n] = -g*x[n] + x[n-d] + g*y[n-d], block-wise."""
    d = max(1, int(delay * SR)); x = np.asarray(x, dtype=float); y = -g * x
    y[d:] += x[:-d]
    for k in range(d, len(y), d):
        e = min(len(y), k + d); y[k:e] += g * y[k - d:e - d]
    return y

def reverb(st, wet=0.25, size=1.0, damp=5500):
    out = np.zeros_like(st)
    for ch, spread in ((0, 0.0), (1, 0.0023)):
        x = lp(st[ch], damp, 1)
        y = sum(comb(x, (d + spread) * size, g) for d, g in ((0.0297, .80), (0.0371, .79), (0.0411, .78), (0.0437, .77)))
        y = allpass(allpass(y, 0.005, .7), 0.0017, .7)
        out[ch] = y * 0.22
    return st * (1 - wet * .5) + out * wet

def pingpong(st, delay, fb=0.35, mix=0.3):
    d = int(delay * SR); out = st.copy(); mono = st.mean(axis=0)
    tap = np.zeros_like(mono); tap[d:] = mono[:-d]
    l = comb(tap, delay * 2, fb); r = np.zeros_like(l); r[d:] = l[:-d]
    out[0] += l * mix; out[1] += r * mix
    return out

def steady(st):
    """Keep the second loop: tails from loop one wrap into its start."""
    return st[:, int(LOOP * SR):int(LOOP * SR) + N]

def tape(st, drive=1.2):
    return np.tanh(st * drive) / np.tanh(drive)

# ---------------------------------------------------------------- stems
def stem_pad():
    out = buf()
    for bar, name in enumerate(PROG):
        _, notes = CH[name]
        dur = BAR + 1.6
        n = int(dur * SR)
        e = env_adsr(n, .7, .6, .8, 1.4, int(BAR * SR))
        for k, note in enumerate(notes):
            f = midi(note)
            for det, pan in ((-.11, -.6), (0.0, 0.0), (.09, .6)):
                ff = f * 2 ** (det / 12)
                s = polyblep_saw(ff, n, rng.random()) * .5 + np.sin(2 * np.pi * ff / 2 * np.arange(n) / SR) * .25
                place(out, s * e * .09, bar * BAR, pan)
    out = lp(out, 1500, 2)
    # Slow filter breathing: a gentle tremolo of the upper band that loops in 40 s.
    t = np.arange(out.shape[1]) / SR
    shimmer = hp(out, 900) * (0.35 + 0.25 * np.sin(2 * np.pi * t / 10.0))
    out = lp(out, 900) + shimmer
    return reverb(out, .35, 1.3)

def epiano(f, n, vel):
    t = np.arange(n) / SR
    idx = 1.9 * np.exp(-t / .35) + .25
    mod = np.sin(2 * np.pi * f * t) * idx
    tone = np.sin(2 * np.pi * f * t + mod)
    tine = np.sin(2 * np.pi * f * 14.0 * t) * np.exp(-t / .03) * .12
    amp = np.exp(-t / 1.4) * (1 - np.exp(-t / .004))
    return (tone + tine) * amp * vel

def stem_keys():
    out = buf()
    pattern = [(0, 1.0, 5), (6, .7, 3), (10, .85, 4), (14, .55, 2)]
    for bar, name in enumerate(PROG):
        _, notes = CH[name]
        voicing = [x + 12 for x in notes[1:]]
        for step, vel, length in pattern:
            if bar % 4 == 3 and step == 14: continue
            jitter = rng.normal(0, .006)
            n = int((length * BEAT / 4 + 1.6) * SR)
            for i, note in enumerate(voicing):
                v = vel * (0.85 + 0.15 * rng.random())
                place(out, epiano(midi(note), n, v) * .12, bar * BAR + step * BEAT / 4 + jitter + i * .012, -.25 + .25 * i)
        if bar % 4 == 3:
            # Little right-hand fill on every fourth bar.
            phrase = [PENTA[i] for i in rng.choice(len(PENTA), 4, replace=False)]
            phrase.sort(reverse=bar % 8 == 7)
            for i, note in enumerate(phrase):
                place(out, epiano(midi(note), int(1.4 * SR), .7) * .11, bar * BAR + (8 + i * 2) * BEAT / 4, .3)
    t = np.arange(out.shape[1]) / SR
    pan = 0.18 * np.sin(2 * np.pi * t / 4.0)       # 10 cycles per loop: seamless auto-pan
    out[0] *= 1 - pan; out[1] *= 1 + pan
    return reverb(lp(out, 7000), .25, 1.1)

def stem_bass():
    out = buf()
    pattern = [(0, 0, 5), (7, 0, 2), (10, 7, 2), (14, 12, 2)]
    for bar, name in enumerate(PROG):
        root, _ = CH[name]
        for step, interval, length in pattern:
            f = midi(root + interval)
            n = int((length * BEAT / 4 + .25) * SR)
            t = np.arange(n) / SR
            s = np.sin(2 * np.pi * f * t) + .28 * np.sin(4 * np.pi * f * t) + .1 * np.sin(6 * np.pi * f * t)
            e = env_adsr(n, .006, .12, .7, .12, int(length * BEAT / 4 * SR))
            place(out, np.tanh(s * 1.4) * e * .32, bar * BAR + step * BEAT / 4, 0)
    return lp(out, 650, 2)

def kick(n_s=.45, punch=1.0, f0=48):
    n = int(n_s * SR); t = np.arange(n) / SR
    f = f0 + 95 * np.exp(-t / .035) * punch
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / .16) * (1 - np.exp(-t / .002))

def noise_hit(n_s, lo, hi, decay):
    n = int(n_s * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), lo, hi) * np.exp(-t / decay)

def stem_beat_soft():
    out = buf()
    swing = .58
    for bar in range(BARS):
        b0 = bar * BAR
        for step in (0, 7, 10):
            if step == 7 and bar % 2 == 1: continue
            place(out, kick(.4, .8, 50) * (.9 if step == 0 else .6), b0 + step * BEAT / 4, 0, .55)
        for step in (4, 12):
            rim = noise_hit(.18, 800, 4200, .045) * .9 + np.sin(2 * np.pi * 330 * np.arange(int(.18 * SR)) / SR) * np.exp(-np.arange(int(.18 * SR)) / SR / .02) * .4
            place(out, rim, b0 + step * BEAT / 4 + .01, .1, .35)
        for e8 in range(8):
            delay = (swing - .5) * BEAT if e8 % 2 else 0
            place(out, noise_hit(.08, 6000, 12000, .018), b0 + e8 * BEAT / 2 + delay, .25, .16 * (1.0 if e8 % 2 == 0 else .7) * (0.8 + 0.4 * rng.random()))
    crackle = np.zeros(out.shape[1])
    pops = rng.integers(0, out.shape[1], 2600)
    crackle[pops] = rng.normal(0, 1, len(pops))
    crackle = lp(hp(crackle, 1500, 1), 6000, 1) * .08 + lp(rng.standard_normal(out.shape[1]), 900, 1) * .004
    out += np.vstack([crackle, np.roll(crackle, 37)])
    return reverb(tape(lp(out, 9000), 1.4), .12, .8)

def stem_beat_dance():
    out = buf()
    for bar in range(BARS):
        b0 = bar * BAR
        for beat in range(4):
            place(out, kick(.38, 1.2, 47), b0 + beat * BEAT, 0, .62)
            place(out, noise_hit(.22, 7000, 15000, .07), b0 + (beat + .5) * BEAT, -.15, .17)
        for beat in (1, 3):
            clap = sum(np.pad(noise_hit(.2, 900, 5000, .05), (int(k * .011 * SR), 0))[:int(.2 * SR)] for k in range(3))
            place(out, clap, b0 + beat * BEAT, .05, .28)
        for s16 in range(16):
            place(out, noise_hit(.04, 8000, 14000, .01), b0 + s16 * BEAT / 4, .3, .06 * (1.0 if s16 % 4 == 2 else .55))
    return reverb(tape(out, 1.15), .1, .7)

def pluck(f, n, bright=1.0):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 13):
        if f * k > 9000: break
        s += np.sin(2 * np.pi * f * k * t) / k * np.exp(-t * (3 + k * 2.2 / bright))
    return s * (1 - np.exp(-t / .002))

def stem_arp():
    out = buf()
    for bar, name in enumerate(PROG):
        _, notes = CH[name]
        seq = [x + 12 for x in notes] + [notes[1] + 24, notes[2] + 24]
        order = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 3, 2, 1] if bar % 2 == 0 else [0, 2, 1, 3, 2, 4, 3, 5, 4, 2, 3, 1, 2, 0, 1, 2]
        for s16, idx in enumerate(order):
            vel = .9 if s16 % 4 == 0 else .55 + .2 * rng.random()
            place(out, pluck(midi(seq[idx]), int(.35 * SR), .8 + .4 * vel) * vel * .14, bar * BAR + s16 * BEAT / 4, -.2 if s16 % 2 else .2)
    out = pingpong(hp(out, 250), BEAT * .75, .38, .35)
    return reverb(out, .22, 1.0)

def bell(f, n):
    t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 3.5 * t) * (2.2 * np.exp(-t / .6))
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 1.6) * (1 - np.exp(-t / .002))

def stem_sparkle():
    out = buf()
    for bar in range(BARS):
        count = 1 + (bar % 3 == 0) + (bar % 4 == 3)
        for _ in range(count):
            step = int(rng.integers(0, 8)) * 2
            note = PENTA[int(rng.integers(3, len(PENTA)))] + 12 * (rng.random() < .3)
            place(out, bell(midi(note), int(3.2 * SR)) * .11, bar * BAR + step * BEAT / 4, float(rng.uniform(-.8, .8)))
    return reverb(pingpong(out, BEAT * 1.5, .3, .25), .5, 1.6, 7000)

STEMS = [('stem_0_pad', stem_pad), ('stem_1_keys', stem_keys), ('stem_2_bass', stem_bass),
         ('stem_3_beat_soft', stem_beat_soft), ('stem_4_beat_dance', stem_beat_dance),
         ('stem_5_arp', stem_arp), ('stem_6_sparkle', stem_sparkle)]

# ------------------------------------------------------------------ sfx
def sweep_noise(n_s, f_from, f_to, q=4.0, gain=1.0):
    n = int(n_s * SR); x = rng.standard_normal(n); y = np.zeros(n)
    f = np.geomspace(f_from, f_to, n); y1 = y2 = 0.0; x1 = x2 = 0.0
    for i in range(n):   # time-varying band-pass (RBJ biquad)
        w = 2 * np.pi * f[i] / SR; alpha = np.sin(w) / (2 * q); c = np.cos(w); a0 = 1 + alpha
        yi = (alpha * x[i] - alpha * x2 - (-2 * c) * y1 - (1 - alpha) * y2) / a0
        x2, x1 = x1, x[i]; y2, y1 = y1, yi; y[i] = yi
    t = np.arange(n) / SR
    return y * np.sin(np.pi * t / n_s) ** 1.5 * gain

def sfx_whoosh():
    s = sweep_noise(1.6, 300, 4200, 2.5, 1.0) + sweep_noise(1.6, 120, 900, 3, .6)
    return reverb(np.vstack([s, np.roll(s, 200)]) * .5, .3, 1.0)

def sfx_glitch():
    out = np.zeros(int(.55 * SR))
    pos = 0
    while pos < len(out) - 800:
        seg = int(rng.integers(600, 1800)); f = float(rng.choice([220, 330, 440, 660, 880, 1320]))
        t = np.arange(seg) / SR
        tone = np.sign(np.sin(2 * np.pi * f * t)) * .4 + rng.standard_normal(seg) * .25 * (rng.random() < .5)
        out[pos:pos + seg] += np.round(tone * 6) / 6 * np.hanning(seg) ** .3
        pos += seg + int(rng.integers(0, 600))
    out = lp(out, 7000) * np.exp(-np.arange(len(out)) / SR / .35)
    return np.vstack([out, np.roll(out, 90)]) * .5

def sfx_chime():
    out = buf(2.4)
    for i, note in enumerate([74, 78, 81, 86]):
        place_once(out, bell(midi(note), int(1.8 * SR)) * .3, i * .09, -.3 + .2 * i)
    return reverb(out, .4, 1.2)

def place_once(dst, sig, start, pan=0.0):
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    i = int(start * SR); j = min(dst.shape[1], i + len(sig))
    dst[0, i:j] += sig[:j - i] * l * 1.414; dst[1, i:j] += sig[:j - i] * r * 1.414

def tone_sweep(n_s, f0, f1, shape=1.0):
    n = int(n_s * SR); t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** ((t / n_s) ** shape)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def sfx_grow():
    n_s = .9; s = tone_sweep(n_s, 260, 1040, .8) * np.sin(np.pi * np.arange(int(n_s * SR)) / SR / n_s) * .35
    out = buf(1.6); place_once(out, s, 0); place_once(out, bell(midi(86), int(1.2 * SR)) * .2, .55, .3)
    return reverb(out, .3, 1.0)

def sfx_shrink():
    n_s = .8; t = np.arange(int(n_s * SR)) / SR
    s = tone_sweep(n_s, 900, 180, .7) * np.exp(-t / .5) * .4
    s += np.sin(2 * np.pi * 1600 * t) * np.exp(-t / .05) * .15
    out = buf(1.4); place_once(out, s, 0)
    return reverb(out, .25, .9)

def sfx_click():
    n = int(.09 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 1800 * t) * np.exp(-t / .012) * .4 + np.sin(2 * np.pi * 900 * t) * np.exp(-t / .02) * .2
    return np.vstack([s, s])

def sfx_lift():
    n_s = 2.2; n = int(n_s * SR); t = np.arange(n) / SR
    rise = tone_sweep(n_s, 110, 880, 1.6) * .18 * np.sin(np.pi * t / n_s)
    air = sweep_noise(n_s, 200, 6000, 2.0, .5)
    out = buf(3.2); place_once(out, rise + air, 0)
    for i, note in enumerate([62, 66, 69, 74]): place_once(out, bell(midi(note + 12), int(1.4 * SR)) * .12, 1.5 + i * .06, -.4 + .25 * i)
    return reverb(out, .35, 1.2)

def sfx_car_loop():
    seconds = 4.0; n = int(seconds * SR); t = np.arange(2 * n) / SR
    drone = np.sin(2 * np.pi * 55 * t) * .3 + np.sin(2 * np.pi * 110.0 * t) * .12 + np.sin(2 * np.pi * 165 * t) * .05
    wob = 1 + .15 * np.sin(2 * np.pi * t / 2.0)
    base = rng.standard_normal(n)
    air = lp(hp(np.tile(base, 2), 300), 2500) * .12      # filtered periodic noise
    s = drone * wob + air
    st = np.vstack([s, np.roll(s, 311)])
    return st[:, n:2 * n] * .8                         # second period: filters settled, seamless 4 s loop

def sfx_chirp(variant):
    notes = [[76, 83, 88], [81, 79, 86], [72, 79, 84, 91]][variant]
    out = buf(.9); pos = 0.0
    for i, note in enumerate(notes):
        n_s = .07 + .03 * (i == len(notes) - 1); n = int(n_s * SR); t = np.arange(n) / SR
        f = midi(note) * (1 + .06 * np.sin(2 * np.pi * 18 * t))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR + 1.2 * np.sin(2 * np.pi * np.cumsum(f) * 2 / SR) * np.exp(-t / .03))
        place_once(out, s * np.sin(np.pi * t / n_s) * .3, pos, 0); pos += n_s * .9
    return reverb(out, .2, .7)

SFX = [('sfx_0_whoosh', sfx_whoosh), ('sfx_1_glitch', sfx_glitch), ('sfx_2_chime', sfx_chime), ('sfx_3_grow', sfx_grow),
       ('sfx_4_shrink', sfx_shrink), ('sfx_5_click', sfx_click), ('sfx_6_lift', sfx_lift),
       ('ride_hum_loop', sfx_car_loop), ('komo_chirp_0', lambda: sfx_chirp(0)), ('komo_chirp_1', lambda: sfx_chirp(1)),
       ('komo_chirp_2', lambda: sfx_chirp(2))]

# ---------------------------------------------------------------- output
def normalise(st, rms_db=-21.0, peak_db=-1.0):
    rms = np.sqrt(np.mean(st ** 2)) + 1e-9
    st = st * (10 ** (rms_db / 20) / rms)
    peak = np.max(np.abs(st)); limit = 10 ** (peak_db / 20)
    if peak > limit: st = np.tanh(st / limit * .9) / np.tanh(.9) * limit
    return st

def write_wav(path, st):
    data = (np.clip(st.T, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())

def write_ogg(path, st, quality=5):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'x.wav'; write_wav(wav, st)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-c:a', 'libvorbis', '-q:a', str(quality), str(path)], check=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--preview'); args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'bpm': BPM, 'key': 'D major', 'bars': BARS, 'loop_seconds': LOOP, 'sample_rate': SR, 'stems': [], 'sfx': [],
              'note': 'Original audio synthesised by this script. No samples or third-party recordings.'}
    stems = {}
    for name, fn in STEMS:
        st = normalise(steady(fn()), -20.0 if 'beat' in name or 'bass' in name else -22.0)
        assert st.shape[1] == N
        stems[name] = st; write_ogg(OUT / (name + '.ogg'), st)
        report['stems'].append({'file': name + '.ogg', 'samples': N, 'rms_dbfs': round(float(20 * np.log10(np.sqrt(np.mean(st ** 2)))), 2),
                                'peak_dbfs': round(float(20 * np.log10(np.max(np.abs(st)))), 2),
                                'loop_seam_jump': round(float(np.max(np.abs(st[:, 0] - st[:, -1]))), 4)})
        print('stem', name, report['stems'][-1])
    for name, fn in SFX:
        st = fn()
        st = normalise(st, -18.0 if name != 'ride_hum_loop' else -20.0, -1.0)
        write_ogg(OUT / (name + '.ogg'), st)
        report['sfx'].append({'file': name + '.ogg', 'seconds': round(st.shape[1] / SR, 3)})
        print('sfx', name, round(st.shape[1] / SR, 2), 's')
    (ROOT / 'Documentation/experience_audio_report.json').write_text(json.dumps(report, indent=2) + '\n')
    if args.preview:
        out = Path(args.preview); out.mkdir(parents=True, exist_ok=True)
        trims = [.8, .7, .75, .65, .7, .55, .6]
        names = [n for n, _ in STEMS]
        scenes = {'lounge_warm': [.6, .75, .55, .5, 0, 0, .15], 'cyber': [.6, .45, .55, .5, 0, .5, .15],
                  'dj_disco': [.35, 0, .85, 0, .9, .6, 0], 'sky_deck': [.75, .3, .3, 0, 0, .35, .75],
                  'ride': [.55, .2, .9, 0, .95, .75, .25]}
        for scene, mix in scenes.items():
            st = sum(stems[n] * m * t for n, m, t in zip(names, mix, trims))
            st = st / max(1e-6, np.max(np.abs(st))) * .89
            write_ogg(out / ('preview_' + scene + '.ogg'), np.hstack([st, st[:, :int(SR * 10)]]))
            print('preview', scene)

if __name__ == '__main__':
    main()
