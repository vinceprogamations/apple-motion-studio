# Rank music tracks for a launch film without listening: punch (transients/s), low-end share, rough tempo, and the
# loudness map with the "drops" (a jump of >= 7 dB after a quieter stretch). Then use finish.py --probe on a candidate
# drop to get it to 50 ms, and finish.py --music-drop/--film-drop to land it on the reveal.
#   python music_scan.py <file or folder> [...]      (needs ffmpeg, numpy, scipy)
# Reading it: punch alone misleads (the approved future-garage track scored 1.7/s). Pads "de igreja" = low punch AND a flat
# loudness map with no drops; good picks have strong bass (> 0.8) and clear dips followed by drops you can land on a reveal.
# Tempo is a rough autocorrelation guess and may be half/double (86 vs 172 for ~130 BPM garage).
import sys, os, glob, subprocess
import numpy as np
from scipy.signal import butter, sosfilt
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); from lib.tools import find_tool
FFMPEG, FFPROBE = find_tool('ffmpeg'), find_tool('ffprobe', required=False)
SR = 11025
def load(f): return np.frombuffer(subprocess.run([FFMPEG, '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
def analyze(f):
    """Metrics of one track (None if shorter than 10 s): duration, punch (transients/s), bass share, rough bpm, drops (s), dB per 0.5 s."""
    x = load(f); dur = len(x) / SR
    if dur < 10: return None
    h = 256; e = np.array([np.sqrt((x[i:i + h] ** 2).mean()) for i in range(0, len(x) - h, h)])
    flux = np.maximum(0, np.diff(np.log(e + 1e-6))); punch = (flux > 0.35).mean() * SR / h
    lo = sosfilt(butter(4, 120 / (SR / 2), 'low', output='sos'), x); bass = np.sqrt((lo ** 2).mean()) / (np.sqrt((x ** 2).mean()) + 1e-9)
    ac = np.correlate(flux - flux.mean(), flux - flux.mean(), 'full')[len(flux) - 1:]; lag = np.arange(len(ac)) * h / SR
    m = (lag > 0.25) & (lag < 0.75); bpm = 60 / lag[m][np.argmax(ac[m])]
    hh = SR // 2; db = [20 * np.log10(np.sqrt((x[i:i + hh] ** 2).mean()) + 1e-9) for i in range(0, len(x) - hh, hh)]
    drops = [i / 2 for i in range(3, len(db)) if db[i] - min(db[i - 3:i]) > 7 and db[i] > -22]
    merged = [d for j, d in enumerate(drops) if j == 0 or d - drops[j - 1] > 2]
    return {'file': f, 'dur': dur, 'punch': float(punch), 'bass': float(bass), 'bpm': float(bpm), 'drops': merged, 'db': db}

if __name__ == '__main__':
    files = []
    for a in sys.argv[1:]: files += sorted(glob.glob(os.path.join(a, '**', '*.*'), recursive=True)) if os.path.isdir(a) else [a]
    files = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.flac', '.m4a', '.ogg'))]
    for f in files:
        r = analyze(f)
        if not r: continue
        print(f"{os.path.basename(f)[:60]:60s} {r['dur']:5.0f}s  punch {r['punch']:4.1f}/s  bass {r['bass']:.2f}  ~{r['bpm']:5.1f}bpm  drops {r['drops'][:10]}")
        print('    dB/s:', ' '.join(f'{d:.0f}' for d in r['db'][::2]))
