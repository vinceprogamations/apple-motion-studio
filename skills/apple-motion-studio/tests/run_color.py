# Color management test (spec § 40): known sRGB patches -> render_dom (JPEG and PNG intermediates) -> H.264 BT.709 ->
# decoded back to RGB with the BT.709 limited-range matrix -> error per patch (0..255) + tags. Also checks the ramp is monotonic
# (no banding inversion) and that decoding with the WRONG matrix (BT.601) would show a measurable shift (the tags matter).
#   python tests/run_color.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, subprocess, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib.tools import find_tool
FF, FP = find_tool('ffmpeg'), find_tool('ffprobe'); EV = 'tests/evidence/09-cor'; os.makedirs(EV, exist_ok=True)
P = [[0,0,0],[16,16,16],[64,64,64],[128,128,128],[192,192,192],[235,235,235],[255,255,255],[255,0,0],[0,255,0],[0,0,255],[255,255,0],[0,255,255],
     [255,0,255],[224,172,140],[61,217,193],[255,138,91],[77,163,255],[20,22,31],[107,79,224],[142,142,147]]
def decode(mp4, matrix):
    raw = subprocess.run([FF, '-v', 'error', '-i', mp4, '-frames:v', '1', '-vf', f'scale=in_color_matrix={matrix}:in_range=tv:out_range=pc,format=rgb24', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(int)
res = {}
for mode, extra in (('jpeg', []), ('png', ['--png'])):
    out = f'{EV}/patches-{mode}.mp4'
    if os.path.exists(out): os.remove(out)
    r = subprocess.run(['node', 'scripts/render_dom.mjs', 'video', 'tests/fixtures/color/patches.html', out, '--fps', '30', '--root', '.', *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    tags = json.loads(subprocess.run([FP, '-v', 'error', '-show_entries', 'stream=color_space,color_transfer,color_primaries,color_range,pix_fmt', '-of', 'json', out], capture_output=True, text=True).stdout)['streams'][0]
    img = decode(out, 'bt709'); wrong = decode(out, 'bt601')
    errs, errs_wrong = [], []
    for i, c in enumerate(P):
        y, x = (i // 4) * 270 + 135, (i % 4) * 270 + 135
        got = img[y - 40:y + 40, x - 40:x + 40].reshape(-1, 3).mean(0); bad = wrong[y - 40:y + 40, x - 40:x + 40].reshape(-1, 3).mean(0)
        errs.append(float(np.abs(got - c).max())); errs_wrong.append(float(np.abs(bad - c).max()))
    # ramp (y 1350–1650): average 240 rows and smooth 16 px (codec noise is ±1–2 levels per pixel); an inversion is a real step backwards of > 1 level,
    # and the deviation from the ideal linear sRGB ramp measures banding / range errors
    ramp = img[1380:1620, 0:1080, :].mean((0, 2)); sm = np.convolve(ramp, np.ones(16) / 16, mode='valid'); mono = int((np.diff(sm[::8]) < -1.0).sum())
    ideal = np.linspace(0, 255, 1080)[8:8 + len(sm)]; ramp_dev = float(np.abs(sm - ideal).max())
    res[mode] = {'tags': tags, 'max_err_bt709': round(max(errs), 2), 'mean_err_bt709': round(float(np.mean(errs)), 2), 'worst_patch': P[int(np.argmax(errs))],
                 'max_err_if_decoded_as_bt601': round(max(errs_wrong), 2), 'ramp_inversions': mono, 'ramp_max_dev_from_linear': round(ramp_dev, 2)}
ok = all(v['tags'].get('color_primaries') == 'bt709' and v['tags'].get('color_transfer') == 'bt709' and v['tags'].get('color_space') == 'bt709'
         and v['tags'].get('color_range') == 'tv' and v['max_err_bt709'] <= 4 and v['ramp_inversions'] == 0 and v['ramp_max_dev_from_linear'] <= 4 and v['max_err_if_decoded_as_bt601'] > v['max_err_bt709'] + 5
         for v in res.values())
res['criterio'] = 'tags bt709/tv; erro máx ≤ 4 níveis em patches chapados de 80×80 px (h264 4:2:0 crf 15); rampa (média de 240 linhas (y 1380–1620, dentro da rampa), suavizada 16 px) sem passo para trás > 1 nível e desvio ≤ 4 níveis da rampa linear; decodificar como BT.601 erraria visivelmente'
res['result'] = 'PASSOU' if ok else 'FALHOU'
json.dump(res, open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit(0 if ok else 1)
