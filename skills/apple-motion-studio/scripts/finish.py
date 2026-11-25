# Finish a film's sound: cut the music so its drop lands on the film's reveal, mix it under the SFX stem, normalise in
# two passes (-14 LUFS / -1 dBTP), print the loudness around the drop, and mux onto the video with BT.709 tags.
#
#   python finish.py --video "out/Film - 1080p.mp4" --sfx "sound/Film - SFX.wav" --out "out/Film - FINAL 1080p.mp4" \
#       [--music track.mp3 --music-drop 17.60 --film-drop 9.00] [--bpm 110 --repeat 1 3] \
#       [--sfx-db 9 --music-db -8] [--fade-in 0.4 --fade-out 1.1] [--len 15] [--lufs -14 --tp -1]
#
# --music-drop  seconds INTO THE TRACK where its drop hits (find it by ear or with the RMS print of --probe)
# --film-drop   seconds INTO THE FILM where the reveal happens (a beat from window.EVENTS)
# --bpm + --repeat A B  extend the track by repeating bars A..B after the drop (bar = 4 beats), with 15 ms crossfades,
#               when the film needs more energy after the drop than the track gives. Edits stay on bar lines.
# --probe       just print the track's RMS every 0.05 s from --probe-from for 4 s, to find the drop, then exit.
# Writes "<out stem> - Music.wav" and "<out stem> - Mix.wav" next to the SFX stem. Needs ffmpeg/ffprobe, numpy.
import argparse, json, os, re, subprocess, sys
import numpy as np
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); from lib.tools import find_tool
FFMPEG, FFPROBE = find_tool('ffmpeg'), find_tool('ffprobe', required=False)

SR = 48000
def run(cmd, **kw): return subprocess.run(cmd, check=True, **kw)
def decode(path, sr=SR, ch=2):
    raw = run([FFMPEG, '-v', 'error', '-i', path, '-ac', str(ch), '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)
def write(path, y): run([FFMPEG, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', path], input=y.astype(np.float32).tobytes())
def db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9) if len(x) else -120
def duration(path): return float(run([FFPROBE, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())
S = lambda t: int(round(t * SR))

def xjoin(a, b, n=S(0.015)):
    w = np.linspace(0, 1, n)[:, None]
    return np.concatenate([a[:-n], a[-n:] * (1 - w) + b[:n] * w, b[n:]])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video'); ap.add_argument('--sfx'); ap.add_argument('--out')
    ap.add_argument('--music'); ap.add_argument('--music-drop', type=float); ap.add_argument('--film-drop', type=float)
    ap.add_argument('--bpm', type=float); ap.add_argument('--repeat', type=float, nargs=2)
    ap.add_argument('--sfx-db', type=float, default=9); ap.add_argument('--music-db', type=float, default=-8)
    ap.add_argument('--fade-in', type=float, default=0.4); ap.add_argument('--fade-out', type=float, default=1.1)
    ap.add_argument('--len', type=float); ap.add_argument('--lufs', type=float, default=-14); ap.add_argument('--tp', type=float, default=-1)
    ap.add_argument('--probe', action='store_true'); ap.add_argument('--probe-from', type=float, default=0)
    a = ap.parse_args()

    if a.probe:
        m = decode(a.music, 22050, 1)[:, 0]; h = int(22050 * 0.05)
        print(' '.join(f'{t:.2f}:{db(m[int(t*22050):int(t*22050)+h]):.0f}' for t in np.arange(a.probe_from, a.probe_from + 4, 0.05))); return
    if not (a.video and a.sfx and a.out): sys.exit('need --video, --sfx and --out')

    L = a.len or duration(a.video)
    sfx = decode(a.sfx); sfx = np.pad(sfx, ((0, max(0, S(L) - len(sfx))), (0, 0)))[:S(L)]
    stem = os.path.join(os.path.dirname(os.path.abspath(a.sfx)), re.sub(r'\s*-\s*(FINAL\s*)?(4K|1080p|720p).*$', '', os.path.splitext(os.path.basename(a.out))[0]))
    mix = sfx * 10 ** (a.sfx_db / 20)

    if a.music:
        if a.music_drop is None or a.film_drop is None: sys.exit('--music needs --music-drop and --film-drop')
        x = decode(a.music)
        if a.repeat:
            if not a.bpm: sys.exit('--repeat needs --bpm')
            bar = 60 / a.bpm * 4; r0, r1 = a.music_drop + a.repeat[0] * bar, a.music_drop + a.repeat[1] * bar
            X = S(0.015); x = xjoin(xjoin(x[:S(r1) + X], x[S(r0):S(r1) + X]), x[S(r1):])
            print(f'extended: bars {a.repeat[0]:g}-{a.repeat[1]:g} after the drop repeated (+{r1 - r0:.2f} s, bar {bar:.4f} s)')
        off = a.music_drop - a.film_drop
        y = x[S(off):] if off >= 0 else np.concatenate([np.zeros((S(-off), 2)), x])
        y = np.pad(y, ((0, max(0, S(L) - len(y))), (0, 0)))[:S(L)]
        t = np.arange(len(y)) / SR
        g = np.clip(t / max(a.fade_in, 1e-3), 0, 1) * np.clip((L - t) / max(a.fade_out, 1e-3), 0, 1)
        y = y * g[:, None]; write(stem + ' - Music.wav', y)
        print(f'music: track {off:+.2f} s -> its drop ({a.music_drop:.2f}) lands at film {a.film_drop:.2f} s')
        mix = mix + y * 10 ** (a.music_db / 20)

    pk = np.abs(mix).max(); print(f'premix peak {20*np.log10(pk+1e-9):.1f} dBFS (float, no clipping yet)')
    pre = stem + ' - premix.wav'; write(pre, mix)
    out1 = run([FFMPEG, '-hide_banner', '-i', pre, '-af', f'loudnorm=I={a.lufs}:TP={a.tp}:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(out1[out1.rindex('{'):out1.rindex('}') + 1])
    af = (f"loudnorm=I={a.lufs}:TP={a.tp}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample={SR}")
    final = stem + ' - Mix.wav'; run([FFMPEG, '-v', 'error', '-y', '-i', pre, '-af', af, '-c:a', 'pcm_s24le', final]); os.remove(pre)
    chk = run([FFMPEG, '-hide_banner', '-i', final, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    k = json.loads(chk[chk.rindex('{'):chk.rindex('}') + 1]); print(f"mix: {k['input_i']} LUFS, true peak {k['input_tp']} dBTP -> {final}")

    if a.film_drop is not None:
        m = decode(final, 22050, 1)[:, 0]; h = int(22050 * 0.05)
        print('RMS around the drop:', ' '.join(f'{t:.2f}:{db(m[int(t*22050):int(t*22050)+h]):.0f}' for t in np.arange(max(0, a.film_drop - 0.6), a.film_drop + 0.6, 0.05)))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    def mux(src):
        run([FFMPEG, '-v', 'error', '-y', '-i', a.video, '-i', src, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
             '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
             '-c:a', 'aac', '-b:a', '320k', '-t', f'{L:.3f}', '-movflags', '+faststart', a.out])
    def tp_of(path):   # true peak of the DECODED delivery (AAC adds inter-sample overs to a -1 dBTP WAV)
        e = run([FFMPEG, '-v', 'info', '-nostats', '-i', path, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf8', errors='replace').stderr
        return float(re.findall(r'Peak:\s*(-?[\d.]+) dBFS', e)[-1])
    mux(final); tp = tp_of(a.out)
    if tp > a.tp:   # trim the excess (+0.3 dB margin) and mux again; the WAV master keeps its loudness target
        g = a.tp - tp - 0.3; trimmed = stem + ' - Mix (aac-safe).wav'
        run([FFMPEG, '-v', 'error', '-y', '-i', final, '-af', f'volume={g:.2f}dB', '-c:a', 'pcm_s24le', trimmed]); mux(trimmed); tp2 = tp_of(a.out)
        print(f'true peak do MP4 decodificado {tp:.2f} dBTP > {a.tp}: ganho {g:.2f} dB e novo mux -> {tp2:.2f} dBTP')
    else: print(f'true peak do MP4 decodificado {tp:.2f} dBTP (alvo ≤ {a.tp})')
    info = run([FFPROBE, '-v', 'error', '-show_entries', 'stream=codec_type,width,height,color_space,color_primaries,color_transfer:format=duration', '-of', 'compact', a.out], capture_output=True, text=True).stdout
    print('SAVED', a.out); print(info.strip())

if __name__ == '__main__': main()
