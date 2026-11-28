# Localized revision (user request: "atrase a notificação em seis quadros"): change ONE beat, re-render, prove only the
# affected window changed, the notification appears exactly 6 frames later, and only its sound event moved.
#   python tests/run_revisao_localizada.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, shutil, subprocess, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib.tools import find_tool
FF = find_tool('ffmpeg'); FIX = 'tests/fixtures/revisao'; EV = 'tests/evidence/10-revisao-localizada'; os.makedirs(EV, exist_ok=True)
FPS, DELAY_FRAMES = 30, 6
def prep(name, toast_local):
    w = f'tests/_work/{name}'; shutil.rmtree(w, ignore_errors=True); shutil.copytree(FIX, w)
    p = f'{w}/s2.html'; s = open(p, encoding='utf8').read(); a = 'const B = { toast: 1.2,'
    assert a in s; open(p, 'w', encoding='utf8').write(s.replace(a, f'const B = {{ toast: {toast_local},', 1)); return w
def render(w, out):
    if os.path.exists(out): os.remove(out)
    r = subprocess.run(['node', 'scripts/render_dom.mjs', 'video', f'{w}/sequence.html', out, '--fps', str(FPS), '--root', '.'], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr
    e = subprocess.run(['node', 'scripts/render_dom.mjs', 'events', f'{w}/sequence.html', out.replace('.mp4', '.events.json'), '--root', '.'], capture_output=True, text=True); assert e.returncode == 0, e.stdout + e.stderr
    return json.load(open(out.replace('.mp4', '.events.json')))
def frames(mp4, w=135, h=240):
    raw = subprocess.run([FF, '-v', 'error', '-i', mp4, '-vf', f'scale={w}:{h}', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
v1 = prep('revisao-v1', 1.2); v2 = prep('revisao-v2', round(1.2 + DELAY_FRAMES / FPS, 6))
e1 = render(v1, f'{EV}/v1 aprovada.mp4'); e2 = render(v2, f'{EV}/v2 notificação +6 quadros.mp4')
A, Bv = frames(f'{EV}/v1 aprovada.mp4'), frames(f'{EV}/v2 notificação +6 quadros.mp4')
d = np.abs(A - Bv).mean(axis=(1, 2)); changed = np.where(d > 0.3)[0]
# notification region (toast at x 70..1010, y 560..700 css px) -> on the 135x240 proxy: x 9..126, y 70..87
def first_visible(F):
    reg = F[:, 70:88, 9:126].mean(axis=(1, 2)); base = reg[75:100].mean()   # scene 2 before the toast
    return int(next(i for i in range(100, len(reg)) if reg[i] > base + 4))
# delay = the shift s that best aligns v1's toast entrance (frames where v1 and v2 differ) with v2 shifted by s
lo, hi = int(changed.min()), int(changed.min()) + 20
cost = {s: float(np.abs(A[lo:hi] - Bv[lo + s:hi + s]).mean()) for s in range(0, 13)}
f1 = lo; f2 = lo + min(cost, key=cost.get); res_cost = {k: round(v, 3) for k, v in cost.items()}
ev1 = {e['name']: e['t'] for e in e1}; ev2 = {e['name']: e['t'] for e in e2}
moved = {k: (ev1[k], ev2.get(k)) for k in ev1 if abs(ev1[k] - ev2.get(k, -1)) > 1e-6}
res = {'frames_total': int(len(A)), 'frames_changed': [int(changed.min()), int(changed.max())] if len(changed) else None, 'n_changed': int(len(changed)),
       'scene1_identical': bool(np.all(d[:75] <= 0.3)), 'after_window_identical': bool(len(changed) and np.all(d[changed.max() + 1:] <= 0.3)),
       'toast_entrance_frame_v1_v2': [f1, f2], 'delay_measured_frames': f2 - f1, 'alignment_cost_by_shift': res_cost, 'events_moved': moved}
ok = res['scene1_identical'] and res['delay_measured_frames'] == DELAY_FRAMES and list(moved) == ['s2.toast'] \
     and abs(moved['s2.toast'][1] - moved['s2.toast'][0] - DELAY_FRAMES / FPS) < 1e-6 and changed.min() >= 75 + int(1.2 * FPS) - 1
res['result'] = 'PASSOU' if ok else 'FALHOU'
# side-by-side evidence at the original appearance frame and 6 frames later
for k in (f1, f1 + 3, f2):
    subprocess.run([FF, '-v', 'error', '-y', '-i', f'{EV}/v1 aprovada.mp4', '-i', f'{EV}/v2 notificação +6 quadros.mp4', '-filter_complex',
                    f"[0:v]select=eq(n\\,{k}),scale=540:-1[a];[1:v]select=eq(n\\,{k}),scale=540:-1[b];[a][b]hstack", '-frames:v', '1', f'{EV}/comparativo quadro {k}.jpg'])
json.dump(res, open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1); print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit(0 if ok else 1)
