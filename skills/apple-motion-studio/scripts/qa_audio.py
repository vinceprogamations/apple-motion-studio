# Audio QA of the file that will actually be played (decodes the MP4/WAV), plus checks that need stems.
#   python qa_audio.py deliver <final.mp4> [--profile web|ebu-r128-s1] [--timeline <render>.timeline.json] [--json out.json]
#        duration, channels, integrated loudness, true peak, max short-term loudness; mono-fold cancellation per 50 ms
#        window (stereo has sound, L+R loses > 9 dB = phase cancelling); intentional silences from the timeline are respected.
#   python qa_audio.py masking --voice <voz.wav> --bed <musica+efeitos.wav> --word <a-b> [--word ...] [--min-snr 6]
#        speech-band (300 Hz–4 kHz) level of the voice over the bed inside each key word; a global LUFS figure cannot show this.
#   python qa_audio.py onset <a.mp4|wav> <b.mp4|wav> --at <s> [--win 0.25]
#        onset of the transient near <s> in both files (decoded), and their difference — proves a cue did / did not move.
# Evidence words: "medido" (this script), "ouvido" (a person or an agent with audio perception listened), "simulado",
#   "testado em aparelho físico". This script only ever produces "medido".
import sys, os, json, re, subprocess, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.tools import find_tool
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
FF = find_tool('ffmpeg'); SR = 48000
PROFILES = {'web': {'I': -14.0, 'I_tol': 1.0, 'TP': -1.0, 'S_max': None},
            'ebu-r128-s1': {'I': -23.0, 'I_tol': 0.5, 'TP': -1.0, 'S_max': -18.0}}   # EBU R 128 s1 (commercials): I −23, max short-term −18, TP −1

def decode(p, ch=2):
    raw = subprocess.run([FF, '-v', 'error', '-i', p, '-map', '0:a:0', '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch)

def loudness(p):
    r = subprocess.run([FF, '-v', 'verbose', '-nostats', '-i', p, '-map', '0:a:0', '-af', 'ebur128=peak=true:framelog=verbose', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf8', errors='replace').stderr
    S = [float(x) for x in re.findall(r' S:\s*(-?[\d.]+)', r) if float(x) > -70]
    I = float(re.findall(r'I:\s*(-?[\d.]+) LUFS', r)[-1]); TP = float(re.findall(r'Peak:\s*(-?[\d.]+) dBFS', r)[-1])
    return I, TP, (max(S) if S else None)

def win_db(x, w):
    n = len(x) // w; y = x[:n * w].reshape(n, w, -1); return 10 * np.log10((y ** 2).mean(axis=(1, 2)) + 1e-12)

def deliver(a):
    st = decode(a.file, 2); dur = len(st) / SR; I, TP, S = loudness(a.file); P = PROFILES[a.profile]; probs, notes = [], []
    intents = json.load(open(a.timeline, encoding='utf8')).get('intentional', []) if a.timeline else []
    silent_ok = [(i['from'], i['to']) for i in intents if i.get('type') == 'silence']
    if abs(I - P['I']) > P['I_tol']: probs.append(f'loudness integrada {I:.1f} LUFS fora do perfil {a.profile} ({P["I"]} ± {P["I_tol"]})')
    if TP > P['TP']: probs.append(f'true peak {TP:.1f} dBTP acima de {P["TP"]}')
    if P['S_max'] is not None and S is not None and S > P['S_max']: probs.append(f'curto prazo máx {S:.1f} LUFS acima de {P["S_max"]}')
    w = int(0.05 * SR); L, R = st[:, 0:1], st[:, 1:2]; mono = (L + R) / 2
    e_st, e_mono = win_db(st, w), win_db(mono, w)
    bad = np.where((e_st > -45) & (e_st - e_mono > 9))[0]
    runs = []
    for i in bad:
        if runs and i - runs[-1][1] <= 2: runs[-1][1] = i
        else: runs.append([i, i])
    for r0, r1 in runs:
        t0, t1 = r0 * 0.05, (r1 + 1) * 0.05
        if t1 - t0 >= 0.1: probs.append(f'cancelamento em mono {t0:.2f}–{t1:.2f} s (estéreo {e_st[r0:r1 + 1].mean():.0f} dB, mono perde {np.mean(e_st[r0:r1 + 1] - e_mono[r0:r1 + 1]):.0f} dB)')
    sil = np.where(e_st < -60)[0]
    sruns = []
    for i in sil:
        if sruns and i - sruns[-1][1] <= 1: sruns[-1][1] = i
        else: sruns.append([i, i])
    for r0, r1 in sruns:
        t0, t1 = r0 * 0.05, (r1 + 1) * 0.05
        if t1 - t0 < 0.3 or t0 < 0.05 or t1 > dur - 0.6: continue
        if any(s0 - 0.1 <= t0 and t1 <= s1 + 0.1 for s0, s1 in silent_ok): notes.append(f'silêncio intencional {t0:.2f}–{t1:.2f} s (declarado)')
        else: probs.append(f'silêncio não declarado {t0:.2f}–{t1:.2f} s')
    res = {'file': a.file, 'evidence': 'medido', 'profile': a.profile, 'duration_s': round(dur, 3), 'channels': 2, 'integrated_lufs': I, 'true_peak_dbtp': TP,
           'max_short_term_lufs': S, 'mono_windows': len(e_st), 'problems': probs, 'notes': notes, 'result': 'OK' if not probs else 'PROBLEMA'}
    return res

def masking(a):
    from scipy.signal import butter, sosfilt
    sos = butter(4, [300 / (SR / 2), 4000 / (SR / 2)], 'band', output='sos')
    v = sosfilt(sos, decode(a.voice, 1)[:, 0]); b = sosfilt(sos, decode(a.bed, 1)[:, 0]); out = []
    for wd in a.word:
        t0, t1 = map(float, wd.split('-')); i0, i1 = int(t0 * SR), int(t1 * SR)
        lv = 10 * np.log10((v[i0:i1] ** 2).mean() + 1e-12); lb = 10 * np.log10((b[i0:i1] ** 2).mean() + 1e-12); snr = lv - lb
        out.append({'word': wd, 'voice_db': round(float(lv), 1), 'bed_db': round(float(lb), 1), 'snr_db': round(float(snr), 1), 'ok': bool(snr >= a.min_snr)})
    return {'evidence': 'medido', 'min_snr_db': a.min_snr, 'words': out, 'result': 'OK' if all(o['ok'] for o in out) else 'PROBLEMA'}

def onset_near(p, at, win):
    x = np.abs(decode(p, 1)[:, 0]); i0, i1 = int(max(0, at - win) * SR), int((at + win) * SR); seg = x[i0:i1]
    e = np.convolve(seg, np.ones(48) / 48, 'same'); base = np.median(e[: max(1, int(0.02 * SR))]) if len(e) else 0
    k = int(np.argmax(e > base + (e.max() - base) * 0.3)); return (i0 + k) / SR

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('deliver'); d.add_argument('file'); d.add_argument('--profile', default='web', choices=list(PROFILES)); d.add_argument('--timeline'); d.add_argument('--json')
    m = sub.add_parser('masking'); m.add_argument('--voice', required=True); m.add_argument('--bed', required=True); m.add_argument('--word', action='append', required=True); m.add_argument('--min-snr', type=float, default=6); m.add_argument('--json')
    o = sub.add_parser('onset'); o.add_argument('a'); o.add_argument('b'); o.add_argument('--at', type=float, required=True); o.add_argument('--win', type=float, default=0.25); o.add_argument('--json')
    a = ap.parse_args()
    if a.cmd == 'deliver': res = deliver(a)
    elif a.cmd == 'masking': res = masking(a)
    else:
        ta, tb = onset_near(a.a, a.at, a.win), onset_near(a.b, a.at, a.win); res = {'evidence': 'medido', 'a': round(ta, 4), 'b': round(tb, 4), 'delta_ms': round((tb - ta) * 1000, 2), 'result': 'OK'}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.json: json.dump(res, open(a.json, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    sys.exit(0 if res['result'] == 'OK' else 1)
