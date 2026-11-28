# Captions + composition QA by sampling (prompt 2 § 6, § 8):
#   1 import an existing SRT tied to an audio version; 2 a headline/caption collision that exists only MID-transition is found
#   by instant; 3 the corrected page passes; 4 zero samples = insufficient coverage (not "zero errors"); 5 a re-recorded line
#   gets new timing, earlier lines kept, later lines moved, the boundary has neither overlap nor a blank frame — checked in the
#   final vertical MP4; 6 same frame by direct seek and by sequential playback; 7 an export interrupted mid-way leaves the
#   valid master's sha256 unchanged.
#   python tests/run_legenda_qa.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, json, shutil, subprocess, hashlib, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib.tools import find_tool
FF = find_tool('ffmpeg'); PY = sys.executable; FIX = 'tests/fixtures/legenda'; EV = 'tests/evidence/13-legenda-qa'; os.makedirs(EV, exist_ok=True)
res = []
def check(name, ok, detail): res.append({'name': name, 'result': 'PASSOU' if ok else 'FALHOU', 'detail': detail}); print('PASSOU' if ok else 'FALHOU', name, '·', detail)
def run(*a, timeout=600): r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf8', errors='replace', timeout=timeout); return r.returncode, r.stdout + r.stderr
def case(name, exit_mode='down', empty=False):
    w = f'tests/_work/{name}'; shutil.rmtree(w, ignore_errors=True); shutil.copytree(FIX, w)
    if exit_mode != 'down': p = f'{w}/page.html'; s = open(p, encoding='utf8').read().replace("const EXIT = 'down';", f"const EXIT = '{exit_mode}';"); open(p, 'w', encoding='utf8').write(s)
    if empty:
        p = f'{w}/page.html'; s = open(p, encoding='utf8').read().replace("transitions: [{ from: B.transition[0], to: B.transition[1] }], ", ''); open(p, 'w', encoding='utf8').write(s)
    return w
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

# 1 import
w_bad = case('legenda-colisao'); c, o = run(PY, 'scripts/captions.py', 'import', f'{FIX}/legenda.srt', f'{w_bad}/captions.json', '--audio', 'voz-v1')
doc = json.load(open(f'{w_bad}/captions.json', encoding='utf8'))
check('importa legenda existente ligada à versão do áudio', c == 0 and len(doc['lines']) == 3 and doc['audio'] == 'voz-v1' and doc['lines'][0]['text'] == 'Sua agenda inteira\nnum só lugar.',
      f"{len(doc['lines'])} linhas, quebra editorial preservada, confiança {doc['lines'][0]['confidence']}")
# 2 collision mid-transition
c, o = run('node', 'scripts/render_dom.mjs', 'layout', f'{w_bad}/page.html', f'{EV}/colisao', '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30')
lay = json.load(open(f'{EV}/colisao/layout.json', encoding='utf8')); hits = [x for x in lay['collisions'] if {x['a'], x['b']} == {'headline', 'legenda'}]
mid_only = hits and all(1.0 < x['t'] < 2.0 for x in hits) and not any(abs(x['t'] - 1.0) < 1e-6 or x['t'] >= 1.96 for x in hits)
check('colisão só no meio da transição é achada pelo instante', c == 1 and bool(mid_only), f"{lay['samples']} amostras; colisões headline×legenda em t = {[x['t'] for x in hits]}")
# 3 corrected version
w_ok = case('legenda-corrigida', 'up'); shutil.copy(f'{w_bad}/captions.json', f'{w_ok}/captions.json')
c, o = run('node', 'scripts/render_dom.mjs', 'layout', f'{w_ok}/page.html', f'{EV}/corrigida', '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30')
lay2 = json.load(open(f'{EV}/corrigida/layout.json', encoding='utf8'))
check('versão corrigida passa nas mesmas amostras', c == 0 and not lay2['collisions'] and lay2['samples'] == lay['samples'], f"{lay2['samples']} amostras, 0 colisões")
# 6 seek vs sequential (from the corrected run)
sv = lay2['seek_vs_sequential']; check('mesmo quadro por salto direto e por sequência', sv and all(x['identical_bytes'] for x in sv), f"{len(sv)} instantes comparados, bytes idênticos (tolerância 0)")
# 4 zero samples
w0 = case('legenda-sem-amostras', 'up', empty=True); json.dump({'fps': 30, 'audio': 'voz-v1', 'lines': []}, open(f'{w0}/captions.json', 'w'))
c, o = run('node', 'scripts/render_dom.mjs', 'layout', f'{w0}/page.html', f'{EV}/sem-amostras', '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30')
check('zero amostras = cobertura insuficiente (falha, não "zero erros")', c == 1 and 'cobertura insuficiente' in o, o.strip().splitlines()[-1][:160])
# 5 re-recorded line → captions revised → final vertical MP4
c, o = run(PY, 'scripts/captions.py', 'revise', f'{w_ok}/captions.json', '--id', 'c2', '--dur', '1.6', '--audio', 'voz-v2', '--text', 'Marque em dois toques,\nsem trocar de app.')
rv = json.loads(o.strip().splitlines()[-1]); doc2 = json.load(open(f'{w_ok}/captions.json', encoding='utf8')); L = {x['id']: x for x in doc2['lines']}
check('frase regravada: anteriores preservadas, posteriores recalculadas, fronteira sem sobreposição nem buraco',
      c == 0 and rv['kept'] == ['c1'] and rv['moved'] == ['c3'] and abs(rv['delta_s'] - 0.4) < 1e-6 and round(L['c2']['end'] * 30) == round(L['c3']['start'] * 30) and L['c1'] == doc['lines'][0],
      f"Δ {rv['delta_s']} s; c2 {L['c2']['start']}–{L['c2']['end']} s; c3 {L['c3']['start']}–{L['c3']['end']} s; áudio {doc2['audio']}")
run(PY, 'scripts/captions.py', 'export', f'{w_ok}/captions.json', f'{EV}/legenda-v2.srt')
mp4 = f'{EV}/vertical corrigido.mp4'
c, o = run('node', 'scripts/render_dom.mjs', 'video', f'{w_ok}/page.html', mp4, '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30', '--replace', timeout=900)
raw = subprocess.run([FF, '-v', 'error', '-i', mp4, '-vf', 'crop=900:240:90:1490,scale=225:60', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 60, 225).astype(float); bnd = round(L['c3']['start'] * 30)
ink = [round(float((fr[f] > 128).mean()) * 100, 2) for f in range(bnd - 2, bnd + 3)]   # % of bright (text) pixels in the caption band
d = lambda i, j: float(np.abs(fr[i] - fr[j]).mean())
c3s = round(L['c3']['start'] * 30)
check('no MP4 vertical final: legenda presente em todos os quadros da fronteira e troca exatamente no quadro previsto',
      c == 0 and min(ink) > 1 and d(bnd, bnd - 1) > 2 and d(bnd - 1, bnd - 2) < 1 and d(bnd + 1, bnd) < 1,
      f'quadros {bnd - 2}…{bnd + 2}: % de texto na faixa {ink}; diferença na troca {d(bnd, bnd - 1):.1f} (vizinhos {d(bnd - 1, bnd - 2):.2f}, {d(bnd + 1, bnd):.2f}); troca no quadro {c3s} (t={c3s / 30:.3f} s)')
subprocess.run([FF, '-v', 'error', '-y', '-ss', '1.5', '-i', mp4, '-frames:v', '1', f'{EV}/vertical corrigido - 1.5 s (meio da transição).jpg'])
# 7 interrupted export keeps the master
master = f'{EV}/master.mp4'; shutil.copy(mp4, master); h0 = sha(master)
p = subprocess.Popen(['node', 'scripts/render_dom.mjs', 'video', f'{w_ok}/page.html', master, '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30', '--replace'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(9); p.kill(); p.wait(); time.sleep(1)
if os.name == 'nt': subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)], capture_output=True)
check('exportação interrompida preserva o hash do master válido', sha(master) == h0, f'sha256 {h0[:16]}… antes e depois; .tmp deixado: {os.path.exists(master.replace(".mp4", ".tmp.mp4"))}')
json.dump(res, open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(f"\n{sum(r['result'] == 'PASSOU' for r in res)}/{len(res)} passaram"); sys.exit(0 if all(r['result'] == 'PASSOU' for r in res) else 1)
