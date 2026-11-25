# Frame integrity + timeline coverage for a rendered video (spec §§ 64, 67, 85).
#   python qa_frames.py <video.mp4> [--timeline timeline.json] [--fps 60] [--size 1080x1920] [--duration 40] [--audio] [--json report.json]
# Checks (each one actually measured):
#   container  : decodes without errors (ffmpeg -v error), fps, size, duration, frame count = duration*fps
#   black      : blackdetect (pixel <= 10 %, >= 0.1 s)          white : same on the negated picture
#   freeze     : freezedetect (noise -60 dB, >= 0.5 s)          dupes : exact duplicate-frame runs (mean |Δ| < 0.02 / 255 on 1/8 res)
#   timeline   : scenes contiguous (no gap / overlap), integer frames, last scene ends at the video end
#   audio      : present when --audio; peak (no clipping > -0.1 dBFS), silence runs (silencedetect -50 dB >= 0.5 s)
# timeline.json: {"fps": 60, "total": 40, "scenes": [{"id": "s1", "start": 0, "end": 4.0}, ...],
#                 "intentional": [{"type": "hold|black|white|static_logo|silence", "from": 36.5, "to": 40, "why": "..."}]}
# An alert inside a declared intentional range of the same kind is reported as "intencional" and does not fail.
# The detectors only LOCATE suspicious ranges; whether a range is wrong is decided by the storyboard + inspection.
import sys, os, re, json, argparse, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from lib.tools import find_tool
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
FF, FP = find_tool('ffmpeg'), find_tool('ffprobe')

def ff(args): return subprocess.run([FF, '-hide_banner', '-nostats', *args], capture_output=True, text=True, encoding='utf8', errors='replace').stderr
def ranges(log, kind):
    if kind in ('black', 'white'): return [(float(a), float(b)) for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', log)]
    if kind == 'freeze':
        st = [float(x) for x in re.findall(r'freeze_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'freeze_end: ([\d.]+)', log)]
        return [(s, en[i] if i < len(en) else None) for i, s in enumerate(st)]
    if kind == 'silence':
        st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
        return [(s, en[i] if i < len(en) else None) for i, s in enumerate(st)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--timeline'); ap.add_argument('--fps', type=float); ap.add_argument('--size'); ap.add_argument('--duration', type=float)
    ap.add_argument('--audio', action='store_true'); ap.add_argument('--json'); a = ap.parse_args()
    tl = json.load(open(a.timeline, encoding='utf8')) if a.timeline else {}
    fps_exp = a.fps or tl.get('fps'); dur_exp = a.duration or tl.get('total'); intents = tl.get('intentional', [])
    out = {'video': a.video, 'problems': [], 'intentional': [], 'measures': {}}
    def problem(kind, msg, t0=None, t1=None):
        for it in intents:
            same = it['type'] == kind or (it['type'] in ('hold', 'static_logo', 'black', 'white') and kind in ('freeze', 'dupes'))   # a declared black/white/hold range is also static
            if same and t0 is not None and t0 >= it['from'] - 0.05 and (t1 if t1 is not None else t0) <= it['to'] + 0.05:
                out['intentional'].append(f'{kind} {t0:.2f}–{(t1 if t1 is not None else t0):.2f}s (declarado: {it["type"]}, {it.get("why", "")})'); return
        out['problems'].append(f'{kind}: {msg}')
    # container
    pr = json.loads(subprocess.run([FP, '-v', 'error', '-count_frames', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,nb_read_frames:format=duration', '-of', 'json', a.video], capture_output=True, text=True).stdout or '{}')
    v = next((s for s in pr.get('streams', []) if s['codec_type'] == 'video'), None)
    if not v: print('FALHOU: sem stream de vídeo'); sys.exit(1)
    num, den = map(int, v['r_frame_rate'].split('/')); fps = num / den; dur = float(pr['format']['duration']); nfr = int(v.get('nb_read_frames', 0))
    out['measures'].update(fps=fps, size=f"{v['width']}x{v['height']}", duration=dur, frames=nfr, has_audio=any(s['codec_type'] == 'audio' for s in pr['streams']))
    dec = ff(['-v', 'error', '-i', a.video, '-f', 'null', '-']).strip()
    if dec: problem('decode', 'erros ao decodificar: ' + dec.splitlines()[0])
    if fps_exp and abs(fps - fps_exp) > 1e-3: problem('fps', f'{fps:.3f} fps, esperado {fps_exp}')
    if a.size and f"{v['width']}x{v['height']}" != a.size: problem('resolução', f"{v['width']}x{v['height']}, esperado {a.size}")
    if dur_exp and abs(dur - dur_exp) > 1.5 / fps: problem('duração', f'{dur:.3f} s, esperado {dur_exp}')
    if fps_exp and dur_exp and abs(nfr - round(dur_exp * fps_exp)) > 0: problem('quadros', f'{nfr} quadros, esperado {round(dur_exp * fps_exp)}')
    # black / white / freeze (ffmpeg detectors)
    for t0, t1 in ranges(ff(['-i', a.video, '-vf', 'blackdetect=d=0.1:pix_th=0.10:pic_th=0.98', '-an', '-f', 'null', '-']), 'black'): problem('black', f'quadro(s) preto(s) {t0:.2f}–{t1:.2f} s', t0, t1)
    for t0, t1 in ranges(ff(['-i', a.video, '-vf', 'negate,blackdetect=d=0.1:pix_th=0.10:pic_th=0.98', '-an', '-f', 'null', '-']), 'white'): problem('white', f'quadro(s) branco(s) {t0:.2f}–{t1:.2f} s', t0, t1)
    for t0, t1 in ranges(ff(['-i', a.video, '-vf', 'freezedetect=n=-60dB:d=0.5', '-an', '-f', 'null', '-']), 'freeze'):
        problem('freeze', f'imagem congelada {t0:.2f}–{(t1 if t1 is not None else dur):.2f} s', t0, t1 if t1 is not None else dur)
    # exact duplicate runs shorter than freezedetect's window (render glitch: the same frame captured twice)
    w, h = max(16, v['width'] // 8), max(16, v['height'] // 8)
    raw = subprocess.run([FF, '-v', 'error', '-i', a.video, '-vf', f'scale={w}:{h}', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16); diffs = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)) if len(fr) > 1 else np.array([])
    run = 0; runs = []
    for i, d in enumerate(diffs):
        if d < 0.02: run += 1
        else:
            if run: runs.append((i - run, i)); run = 0
    if run: runs.append((len(diffs) - run, len(diffs)))
    out['measures']['duplicate_runs'] = len(runs)
    for s, e in runs:
        if 1 <= e - s < (0.5 * fps) and 0 < s and e < len(diffs): problem('dupes', f'{e - s} quadro(s) repetido(s) a partir de {s / fps:.2f} s (possível falha de captura)', s / fps, e / fps)
    # timeline coverage
    if tl.get('scenes'):
        sc = sorted(tl['scenes'], key=lambda x: x['start']); tfps = tl.get('fps', fps)
        if abs(sc[0]['start']) > 1e-6: problem('timeline', f"primeira cena começa em {sc[0]['start']} s (lacuna no início)")
        for p, q in zip(sc, sc[1:]):
            if q['start'] > p['end'] + 1e-6: problem('timeline', f"lacuna {p['end']}–{q['start']} s entre {p['id']} e {q['id']}")
            if q['start'] < p['end'] - 1e-6: problem('timeline', f"sobreposição {q['start']}–{p['end']} s entre {p['id']} e {q['id']}")
        for s in sc:
            for k in ('start', 'end'):
                if abs(s[k] * tfps - round(s[k] * tfps)) > 1e-6: problem('timeline', f"{s['id']}.{k}={s[k]} s não cai em quadro inteiro a {tfps} fps")
        if tl.get('total') and abs(sc[-1]['end'] - tl['total']) > 1e-6: problem('timeline', f"última cena termina em {sc[-1]['end']} s, filme tem {tl['total']} s")
    # audio
    if a.audio or out['measures']['has_audio']:
        if not out['measures']['has_audio']: problem('audio', 'sem faixa de áudio')
        else:
            st = ff(['-i', a.video, '-af', 'astats=metadata=0:reset=0', '-vn', '-f', 'null', '-'])
            pk = [float(x) for x in re.findall(r'Peak level dB: ([-\d.inf]+)', st) if x not in ('-inf',)]
            out['measures']['audio_peak_dbfs'] = max(pk) if pk else None
            if pk and max(pk) > -0.1: problem('clipping', f'pico de áudio {max(pk):.2f} dBFS (clipping)')
            for t0, t1 in ranges(ff(['-i', a.video, '-af', 'silencedetect=n=-50dB:d=0.5', '-vn', '-f', 'null', '-']), 'silence'):
                problem('silence', f'silêncio {t0:.2f}–{(t1 if t1 is not None else dur):.2f} s', t0, t1 if t1 is not None else dur)
    m = out['measures']; print(f"{a.video}\n  {m['size']} · {m['fps']:.3f} fps · {m['duration']:.3f} s · {m['frames']} quadros · áudio {'sim' if m['has_audio'] else 'não'}")
    for x in out['intentional']: print('  intencional: ' + x)
    for x in out['problems']: print('  PROBLEMA: ' + x)
    print('  OK' if not out['problems'] else f"  {len(out['problems'])} problema(s)")
    if a.json: json.dump(out, open(a.json, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    sys.exit(1 if out['problems'] else 0)

if __name__ == '__main__': main()
