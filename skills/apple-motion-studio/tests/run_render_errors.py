# Render-time failure fixtures for render_dom.mjs (spec §§ 65, 85): each defect must stop the export with a useful message.
#   python tests/run_render_errors.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, shutil, subprocess, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
FIX = 'tests/fixtures/studio-lume'; EV = 'tests/evidence/05-render-errors'; os.makedirs(EV, exist_ok=True)
def case(name, mutate):
    w = f'tests/_work/{name}'; shutil.rmtree(w, ignore_errors=True); shutil.copytree(FIX, w); mutate(w); return w
def edit(path, a, b):
    s = open(path, encoding='utf8').read(); assert a in s, (path, a); open(path, 'w', encoding='utf8').write(s.replace(a, b))
CASES = [
    ('erro-js-no-meio', lambda w: edit(f'{w}/s1.html', "titles(lt, 2.5, 0.2);", "titles(lt, 2.5, 0.2); if (lt > 1.2) throw new Error('falha proposital no quadro');"),
     ['--fps', '30'], r'erro na página no quadro|falha proposital'),
    ('cena-sem-contrato', lambda w: edit(f'{w}/s1.html', 'window.anim = lt => {', 'window.animX = lt => {'), ['--fps', '30'], r'não cumpre o contrato de cena'),
    ('kit-404', lambda w: edit(f'{w}/s1.html', '../../../templates/dom/anim.js', '../../../templates/dom/anim-que-nao-existe.js'), ['--fps', '30'], r'HTTP 404: .*anim-que-nao-existe\.js|não cumpre o contrato'),
    ('ready-nunca-resolve', lambda w: edit(f'{w}/s1.html', '<script src="../../../templates/dom/anim.js"></script>',
       '<script src="../../../templates/dom/anim.js"></script><script>window.ready = new Promise(() => {});</script>'), ['--fps', '30', '--ready-timeout', '4'], r'não resolveu em 4 s'),
]
res = []
for name, mut, args, pat in CASES:
    w = case(name, mut); out = f'{EV}/{name}.mp4'
    r = subprocess.run(['node', 'scripts/render_dom.mjs', 'video', f'{w}/sequence.html', out, '--root', '.', *args], capture_output=True, text=True, encoding='utf8', errors='replace')
    log = r.stdout + r.stderr; open(f'{EV}/{name}.log', 'w', encoding='utf8').write(log)
    ok = r.returncode == 1 and bool(re.search(pat, log)) and not os.path.exists(out) and not os.path.exists(out.replace('.mp4', '.tmp.mp4'))
    res.append((name, 'PASSOU' if ok else 'FALHOU', r.returncode, next((l for l in log.splitlines() if 'FAILED' in l), '')[:150]))
for n, s, c, m in res: print(f'{n:22s} {s}  exit={c}  {m}')
json.dump([dict(case=n, result=s, exit=c, message=m) for n, s, c, m in res], open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
sys.exit(0 if all(s == 'PASSOU' for _, s, _, _ in res) else 1)
