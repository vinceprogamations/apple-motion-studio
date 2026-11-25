# DOM 4K test (spec § 89): the same composition rendered at 1080x1920 (scale 1) and natively at 2160x3840 (scale 2).
# Proves: captured pixels are really 2160x3840 BEFORE encoding (PNG stills); framing is equivalent (4K downscaled ≈ 1080p);
# 4K carries real fine detail (Laplacian energy vs 1080p upscaled ×2); the 4K MP4 decodes at 2160x3840; render time.
#   python tests/run_dom_4k.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, subprocess, json, time
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib.tools import find_tool
FP = find_tool('ffprobe'); EV = 'tests/evidence/08-dom-4k'; os.makedirs(EV, exist_ok=True)
SEQ = 'tests/fixtures/studio-lume/sequence.html'; T = '1.50'; res = {}
for sc in (1, 2):
    t0 = time.time()
    r = subprocess.run(['node', 'scripts/render_dom.mjs', 'stills', SEQ, f'{EV}/stills-x{sc}', T, '--root', '.', '--scale', str(sc), '--png'], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    res[f'stills_x{sc}_s'] = round(time.time() - t0, 1)
a = cv2.imread(f'{EV}/stills-x1/{T}.png'); b = cv2.imread(f'{EV}/stills-x2/{T}.png')
res['pixels_1080'] = list(a.shape[1::-1]); res['pixels_4k'] = list(b.shape[1::-1])
down = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
res['framing_mean_abs_diff_0_255'] = round(float(np.abs(down.astype(int) - a.astype(int)).mean()), 3)
# detail: crop the avatar/text block, compare Laplacian variance of native 4K vs 1080p upscaled to 4K
y0, y1, x0, x1 = 760, 1060, 340, 760
c4 = b[y0 * 2:y1 * 2, x0 * 2:x1 * 2]; up = cv2.resize(a, (b.shape[1], b.shape[0]), interpolation=cv2.INTER_CUBIC)[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
lap = lambda im: float(cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
res['detail_laplacian_native4k'] = round(lap(c4), 1); res['detail_laplacian_1080_upscaled'] = round(lap(up), 1)
cv2.imwrite(f'{EV}/recorte 4K nativo.png', c4); cv2.imwrite(f'{EV}/recorte 1080 ampliado.png', up)
cv2.imwrite(f'{EV}/comparativo recortes.png', np.hstack([up, c4]))
# short 4K video through the normal command
out = f'{EV}/studio-lume 4K.mp4'
if os.path.exists(out): os.remove(out)
t0 = time.time(); r = subprocess.run(['node', 'scripts/render_dom.mjs', 'video', SEQ, out, '--fps', '30', '--root', '.', '--scale', '2', '--png'], capture_output=True, text=True)
res['video_4k_render_s'] = round(time.time() - t0, 1); res['video_4k_exit'] = r.returncode
pr = subprocess.run([FP, '-v', 'error', '-count_frames', '-show_entries', 'stream=width,height,nb_read_frames,color_space,color_transfer,color_primaries,color_range', '-of', 'json', out], capture_output=True, text=True).stdout
res['video_4k_probe'] = json.loads(pr)['streams'][0] if pr else None
ok = (res['pixels_4k'] == [2160, 3840] and res['pixels_1080'] == [1080, 1920] and res['framing_mean_abs_diff_0_255'] < 3
      # detail threshold 1.25x: measured 1.41x; the photos are 512 px sources, so the native gain comes from text and edges
      and res['detail_laplacian_native4k'] > 1.25 * res['detail_laplacian_1080_upscaled'] and res['video_4k_exit'] == 0
      and res['video_4k_probe'] and res['video_4k_probe']['width'] == 2160 and res['video_4k_probe']['height'] == 3840
      and res['video_4k_probe'].get('color_primaries') == 'bt709' and res['video_4k_probe'].get('color_transfer') == 'bt709')
res['result'] = 'PASSOU' if ok else 'FALHOU'
json.dump(res, open(f'{EV}/RESUMO.json', 'w'), indent=1); print(json.dumps(res, indent=1)); sys.exit(0 if ok else 1)
