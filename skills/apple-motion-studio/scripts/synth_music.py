# Original electronic cue generated from code (no samples, no AI, deterministic): intro pad + plucked arp, a build that opens
# the filter with a snare roll and a riser, a breath of silence, the DROP exactly on the film's reveal (kick, sub bass,
# chords), then a held ending. Being authored here, it can ship with a public demo (CC0 by the skill's authors).
#   python synth_music.py <out.wav> --len 21 --drop 14.0 [--bpm 120] [--key A] [--breath 0.5] [--seed 1] [--mood bright|dark]
#   [--voice-gap a-b[:dB],...]   duck the music in these film seconds (room for a voice line; default 10 dB, 120 ms ramps)
import numpy as np, argparse, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.tools import find_tool
SR = 48000
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def env_adsr(n, a, d, s, r, sus_len):
    A, D, R = int(a * SR), int(d * SR), int(r * SR); S = max(0, n - A - D - R)
    e = np.concatenate([np.linspace(0, 1, A, endpoint=False), np.linspace(1, s, D, endpoint=False), np.full(S, s), np.linspace(s, 0, R)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]
def saw(f, n, ph=0.0): t = np.arange(n) / SR; return 2 * ((f * t + ph) % 1) - 1
def lp(x, fc):   # one-pole low-pass with a time-varying cutoff (array) or a constant
    fc = np.broadcast_to(np.asarray(fc, float), x.shape); a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - a[i]) * x[i] + a[i] * acc; y[i] = acc
    return y
def lp_fast(x, fc):   # constant cutoff, vectorised via scipy if present
    try:
        from scipy.signal import butter, sosfilt; return sosfilt(butter(2, min(fc, SR / 2 - 100) / (SR / 2), 'low', output='sos'), x)
    except Exception: return lp(x, fc)
def hp_fast(x, fc):
    from scipy.signal import butter, sosfilt; return sosfilt(butter(2, fc / (SR / 2), 'high', output='sos'), x)

def render(L, drop, bpm, key, breath, seed, mood, gaps):
    rng = np.random.default_rng(seed); N = int(L * SR); out = np.zeros((N, 2)); beat = 60 / bpm; root = 45 + NOTE[key]   # A2 = 45
    prog = [[0, 7, 12, 16], [-4, 3, 8, 12], [-7, 0, 5, 9], [-2, 5, 10, 14]] if mood == 'bright' else [[0, 7, 12, 15], [-4, 3, 8, 12], [-5, 2, 7, 10], [-2, 5, 10, 14]]
    bar = 4 * beat
    def add(sig, t0, pan=0.0, g=1.0):
        i = int(t0 * SR)
        if i >= N or i + len(sig) <= 0: return
        if i < 0: sig = sig[-i:]; i = 0
        n = min(len(sig), N - i); l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2); out[i:i + n, 0] += sig[:n] * g * l * 1.41; out[i:i + n, 1] += sig[:n] * g * r * 1.41
    b0 = drop - breath                                  # breath = silence right before the drop
    build0 = max(0.0, drop - 4 * bar)                   # 4 bars of build
    # pad: whole film except the breath, chords every bar, aligned so a bar line falls on the drop
    first = drop - np.ceil(drop / bar) * bar
    t = first; k = 0
    while t < L:
        ch = prog[k % 4]; n = int(bar * SR) + int(0.4 * SR); seg = np.zeros(n)
        for iv in ch:
            f = hz(root + 12 + iv); seg += sum(saw(f * (1 + d), n, rng.random()) for d in (-0.004, 0.0, 0.0045)) / 3
        cut = 900 if t + bar <= build0 else (900 + 5000 * np.clip((t - build0) / (drop - build0 + 1e-9), 0, 1) if t < drop else 3800)
        seg = lp_fast(seg, cut) * env_adsr(n, 0.25 if t < drop else 0.02, 0.3, 0.75, 0.4, 0) * (0.16 if t < drop else 0.2)
        add(seg, t, pan=-0.25, g=1); add(seg, t + 0.011, pan=0.25, g=1); t += bar; k += 1
    # pluck arp (8ths), from the start, brighter in the build
    t = first; i = 0
    while t < L:
        ch = prog[int((t - first) // bar) % 4]; f = hz(root + 24 + ch[[0, 1, 2, 3, 2, 1, 3, 2][i % 8]]); n = int(0.25 * SR)
        s = (saw(f, n) * 0.6 + np.sin(2 * np.pi * f * np.arange(n) / SR) * 0.4) * np.exp(-np.arange(n) / SR * 14)
        s = lp_fast(s, 2500 if t < build0 else 6000) * 0.09; add(s, t, pan=0.35 if i % 2 else -0.35); t += beat / 2; i += 1
    # build: snare roll accelerating + noise riser
    n_r = int((b0 - build0) * SR)
    if n_r > 0:
        noise = rng.standard_normal(n_r); ramp = np.linspace(0, 1, n_r) ** 2
        add(hp_fast(noise, 2000) * ramp * 0.12, build0)
        t = build0; step = beat
        while t < b0 - 0.02:
            n = int(0.12 * SR); s = hp_fast(rng.standard_normal(n), 1200) * np.exp(-np.arange(n) / SR * 30) * (0.05 + 0.2 * (t - build0) / (b0 - build0))
            add(s, t); step = beat if t < build0 + 2 * bar else (beat / 2 if t < build0 + 3 * bar else beat / 4); t += step
    # drop: kick on the beat, sub bass, hats on offbeats
    t = drop
    while t < L - 0.05:
        n = int(0.45 * SR); tt = np.arange(n) / SR; f = 45 + 110 * np.exp(-tt * 28); kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7)
        kick[: int(0.003 * SR)] += rng.standard_normal(int(0.003 * SR)) * 0.3; add(kick * 0.85, t)
        ch = prog[int((t - first) // bar) % 4]; fb = hz(root + ch[0]); nb = int(beat * SR); bass = np.sin(2 * np.pi * fb * np.arange(nb) / SR) + 0.25 * saw(fb, nb)
        bass = lp_fast(bass, 400) * env_adsr(nb, 0.03, 0.1, 0.8, 0.08, 0) * 0.42
        # sidechain feel: bass enters after the kick
        bass[: int(0.06 * SR)] *= np.linspace(0, 1, int(0.06 * SR)); add(bass, t)
        nh = int(0.06 * SR); hat = hp_fast(rng.standard_normal(nh), 7000) * np.exp(-np.arange(nh) / SR * 60) * 0.08; add(hat, t + beat / 2, pan=0.2)
        t += beat
    # breath: true silence before the drop (fade the tails)
    i0, i1 = int(b0 * SR), int(drop * SR); fade = int(0.04 * SR)
    out[i0 - fade:i0] *= np.linspace(1, 0, fade)[:, None]; out[i0:i1] = 0
    # voice gaps: duck the music by <dB> inside the line, 120 ms ramps — automation in that interval, not a global level change
    for g0, g1, depth in gaps:
        a, b = int(g0 * SR), int(g1 * SR); r = int(0.12 * SR); gain = np.ones(N); lo = 10 ** (-depth / 20)
        gain[a:b] = lo; gain[max(0, a - r):a] = np.linspace(1, lo, a - max(0, a - r)); gain[b:b + r] = np.linspace(lo, 1, len(gain[b:b + r])); out *= gain[:, None]
    # ending: last 1.2 s fade
    fo = int(1.2 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    pk = np.abs(out).max(); return out * (0.89 / pk if pk > 0 else 1)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--len', type=float, required=True); ap.add_argument('--drop', type=float, required=True)
    ap.add_argument('--bpm', type=float, default=120); ap.add_argument('--key', default='A'); ap.add_argument('--breath', type=float, default=0.5); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--mood', default='bright', choices=['bright', 'dark']); ap.add_argument('--voice-gap', default='')
    a = ap.parse_args(); gaps = [(*map(float, g.split(':')[0].split('-')), float(g.split(':')[1]) if ':' in g else 10.0) for g in a.voice_gap.split(',') if g]
    y = render(a.len, a.drop, a.bpm, a.key, a.breath, a.seed, a.mood, gaps)
    subprocess.run([find_tool('ffmpeg'), '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', a.out], input=y.astype(np.float32).tobytes(), check=True)
    print(f'{a.out}: {a.len:g} s, drop em {a.drop:g} s (respiro {a.breath:g} s), {a.bpm:g} bpm, {a.key} {a.mood}')
