# Sound design mixer: places sound effects from a local library on the animation's beats and writes one WAV, then checks
# that every hit really lands on its beat.
#   python3 mix.py cues.json "<out SFX.wav>" --lib "<library folder>" [--lib "<another>"] [--events events.json] [--len 20.2]
#                  [--gain dB] [--quant 12] [--stems <dir>]
# --stems <dir>: also writes one WAV per group (cue/bed field "stem": "musica" | "foley" | "ui" | "ambiencia" | "voz"; default
#   "musica" for beds, "efeitos" for cues), scaled exactly like the mix (they sum to it) — a revision of one cue can then be
#   proven to leave the other stems bit-identical.
# events.json: the page's window.EVENTS ([{name, t}], from `node render.mjs events page.html events.json`), so cues are placed
#   by name ("event": "card.open") and stay in sync when the animation is re-timed.  --quant 12: snap events up to the
#   12-poses-a-second grid of a posterised animation (the frame where the change is first visible).
# A cue:  {"event": "card.open" | "at": 3.15, "offset": 0.0, "file": "part of a file name", "db": -14,
#          "align": "peak|start|end", "pitch": 1.0, "lp": 6000, "hp": 200, "dur": 2.0, "pan": 0, "pick": 0}
# A bed:  {"type": "bed", "file": ..., "event"/"at": start, "to_event"/"to": end, "db": -26, "from": 0 (seconds into the file),
#          "fade_in": 1.0, "fade_out": 1.5, "lp", "hp", "env": [["event or seconds", dB relative], ...]}   (loops if short)
import json, sys, os, subprocess, argparse, numpy as np
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
from scipy.signal import butter, sosfilt
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); from lib.tools import find_tool
FFMPEG, FFPROBE = find_tool('ffmpeg'), find_tool('ffprobe', required=False)
SR = 48000
FILES = []
def find(name, pick=0):
    exact = [f for f in FILES if os.path.splitext(os.path.basename(f))[0].lower() == name.lower()]   # an exact name wins over a partial one
    hits = exact or [f for f in FILES if name.lower() in os.path.basename(f).lower()]
    if not hits: sys.exit(f'no sound matches "{name}"')
    return hits[min(pick, len(hits) - 1)]
def load(path):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
def filt(x, f, kind): return sosfilt(butter(2, f / (SR / 2), kind, output='sos'), x, axis=0)
def repitch(x, k):
    if abs(k - 1) < 1e-3: return x
    n = int(len(x) / k); idx = np.arange(n) * k; i0 = np.floor(idx).astype(int); fr = (idx - i0)[:, None]; i1 = np.minimum(i0 + 1, len(x) - 1)
    return x[i0] * (1 - fr) + x[i1] * fr
def env(x): e = np.abs(x).max(1); w = int(0.01 * SR); return np.convolve(e, np.ones(w) / w, 'same')
def onset(x): e = env(x); return int(np.argmax(e > e.max() * 0.08))
def tail_end(x): e = env(x); idx = np.where(e > e.max() * 0.05)[0]; return int(idx[-1]) if len(idx) else len(x)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cues'); ap.add_argument('out'); ap.add_argument('--lib', action='append', required=True)
    ap.add_argument('--events'); ap.add_argument('--len', type=float, default=None); ap.add_argument('--gain', type=float, default=0); ap.add_argument('--quant', type=float, default=0); ap.add_argument('--stems')
    a = ap.parse_args()
    for lib in a.lib: FILES.extend(sorted(os.path.join(d, f) for d, _, fs in os.walk(lib) for f in fs if f.lower().endswith(('.wav', '.aif', '.aiff', '.mp3', '.flac')) and not f.startswith('._')))
    EV = {e['name']: e['t'] for e in json.load(open(a.events))} if a.events else {}
    q = (lambda t: np.ceil(t * a.quant - 1e-6) / a.quant) if a.quant else (lambda t: t)
    def when(c, key='event', fallback='at'):
        if key in c:
            if c[key] not in EV: sys.exit(f'unknown event "{c[key]}"')
            return q(EV[c[key]]) + c.get('offset', 0)
        return c[fallback] + c.get('offset', 0)
    def tval(v): return q(EV[v]) if isinstance(v, str) else v
    L = a.len or EV.get('end') or 20; N = int(L * SR); mix = np.zeros((N + SR * 4, 2)); cache = {}; placed = []; late = []; stems = {}
    def put(name, st, sig):
        if name not in stems: stems[name] = np.zeros_like(mix)
        stems[name][st:st + len(sig)] += sig
    for c in json.load(open(a.cues)):
        f = find(c['file'], c.get('pick', 0))
        if f not in cache: s0 = load(f); cache[f] = s0 / (np.abs(s0).max() + 1e-9)
        s = repitch(cache[f], c.get('pitch', 1.0))
        if c.get('lp'): s = filt(s, c['lp'], 'low')
        if c.get('hp'): s = filt(s, c['hp'], 'high')
        if c.get('type') == 'bed':   # a long ambient layer: looped to length, faded, automated
            t0 = when(c); t1 = tval(c['to_event']) if 'to_event' in c else c.get('to', L); n = int((t1 - t0) * SR); off = int(c.get('from', 0) * SR)
            src = s[off:] if off < len(s) else s; reps = int(np.ceil(n / max(1, len(src)))) + 1; body = np.concatenate([src] * reps)[:n].copy()
            g = np.full(n, 10 ** (c['db'] / 20)); tt = np.arange(n) / SR + t0
            if c.get('env'): pts = sorted((tval(p[0]), p[1]) for p in c['env']); g *= 10 ** (np.interp(tt, [p[0] for p in pts], [p[1] for p in pts]) / 20)
            fi, fo = int(c.get('fade_in', 0.5) * SR), int(c.get('fade_out', 1.0) * SR)
            if fi: g[:fi] *= np.linspace(0, 1, fi) ** 2
            if fo: g[-fo:] *= np.linspace(1, 0, fo) ** 2
            st = int(t0 * SR); mix[st:st + n] += body * g[:, None]; put(c.get('stem', 'musica'), st, body * g[:, None]); print(f"BED {t0:6.2f}-{t1:5.2f}  {c['db']:+5.1f} dB  {os.path.basename(f)[:64]}"); continue
        if c.get('dur'): n = int(c['dur'] * SR); s = s[:n].copy(); fade = min(n, int(0.08 * SR)); s[-fade:] *= np.linspace(1, 0, fade)[:, None]
        pan = c.get('pan', 0); s = s * 10 ** (c['db'] / 20) * np.array([np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)]) * 1.41
        al = c.get('align', 'peak'); ref = {'peak': int(np.argmax(env(s))), 'start': onset(s), 'end': tail_end(s)}[al]
        if al == 'start':   # golpe com ataque lento (booms de trailer, whooshes): alinhar pelo início deixa o PICO atrasado na imagem
            lag = (int(np.argmax(env(s))) - onset(s)) / SR
            if lag > 0.08: late.append((when(c), c.get('event', ''), os.path.basename(f), lag))
        t = when(c); st = int(t * SR) - ref
        if st < 0: s = s[-st:]; ref += st; st = 0   # starts before 0: trim the head, the aligned point stays on the beat
        nn = min(len(s), len(mix) - st); mix[st:st + nn] += s[:nn]; put(c.get('stem', 'efeitos'), st, s[:nn]); placed.append((t, al, c.get('event', ''), os.path.basename(f), (st + ref) / SR))
    fo = int(0.6 * SR); fade = np.ones(N); fade[-fo:] = np.linspace(1, 0, fo)
    mix = mix[:N] * 10 ** (a.gain / 20) * fade[:, None]
    pk = np.abs(mix).max(); k = (10 ** (-1.0 / 20) / pk) if pk > 10 ** (-1.0 / 20) else 1; mix *= k
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        for name, y in stems.items():
            y = y[:N] * 10 ** (a.gain / 20) * fade[:, None] * k
            subprocess.run([FFMPEG, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_f32le', os.path.join(a.stems, f'{name}.wav')], input=y.astype(np.float32).tobytes(), check=True)
        print(f"stems: {', '.join(sorted(stems))} -> {a.stems}")
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', a.out], input=mix.astype(np.float32).tobytes(), check=True)
    # sync check: where does each cue's aligned point actually sit (its own placement), and how far from the beat?
    worst = 0
    for t, ev, name, lag in late:
        print(f"AVISO: {ev or t:} '{name[:48]}' alinhado pelo início, mas o pico chega {lag * 1000:.0f} ms depois — o golpe vai soar ATRASADO na imagem. Use \"align\": \"peak\" (ou confira se o atraso é intencional).")
    for t, al, ev, name, actual in sorted(placed):
        err = (actual - t) * 1000; worst = max(worst, abs(err)); print(f"{t:6.3f}s  {ev[:14]:14s} {al:5s}  {err:+6.1f} ms  {name[:58]}")
    print(f"sync: {len(placed)} cues, worst offset {worst:.1f} ms (1 frame at 24 fps = 41.7 ms)   peak {20 * np.log10(np.abs(mix).max() + 1e-9):.1f} dBFS")
main()
