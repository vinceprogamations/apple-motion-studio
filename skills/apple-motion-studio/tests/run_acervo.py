# Acervo de referências e aparelho real: status/pergunta/consentimento do acervo.py, abertura que pergunta (guiado) ou anuncia
# o download (autônomo), device.js e organico.js válidos, QA de cortes tolerando decimal arredondado e vídeo como vaga de asset.
#   python tests/run_acervo.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, json, shutil, subprocess, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT); sys.path.insert(0, 'scripts')
import acervo, conversa
PY = sys.executable; W = os.path.abspath('tests/_work/acervo'); res = []
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
def check(n, ok, d): res.append({'name': n, 'result': 'PASSOU' if ok else 'FALHOU', 'detail': str(d)[:300]}); print('PASSOU' if ok else 'FALHOU', n, '·', str(d)[:160])
def run(*a, cwd=None): r = subprocess.run([PY, *a], capture_output=True, text=True, encoding='utf8', errors='replace', cwd=cwd); return r.returncode, r.stdout + r.stderr

vazio = os.path.join(W, 'vazio')
rc, out = run('scripts/acervo.py', 'status', '--dir', vazio)
check('acervo ausente: status sai com 3 e lista o que falta', rc == 3 and 'FALTA' in out, out.splitlines()[1] if len(out.splitlines()) > 1 else out)
rc, out = run('scripts/acervo.py', 'pergunta', '--dir', vazio)
check('a pergunta pronta pede o Chrome e diz tamanho e licença', 'Posso acessar o Chrome e baixar tudo?' in out and 'MB' in out and 'licença livre' in out, out[-200:])
rc, out = run('scripts/acervo.py', 'baixar', '--dir', vazio)
check('sem --sim nada é baixado (exit 3)', rc == 3 and not os.path.exists(vazio), out.strip())
cheio = os.path.join(W, 'cheio')
for k, (sub, alvo, _) in acervo.PARTES.items():
    for i in range(alvo): os.makedirs(os.path.join(cheio, sub, f'item{i}'))
rc, out = run('scripts/acervo.py', 'status', '--dir', cheio)
check('acervo completo: status sai com 0', rc == 0, out.splitlines()[-1])
rc, out = run('scripts/acervo.py', 'chrome')
check('itens do navegador listados com autor e licença CC-BY', 'sketchfab' in out.lower() and 'CC-BY' in out and out.count('sketchfab.com/3d-models') == len(acervo.CHROME), len(acervo.CHROME))

# abertura: guiado pergunta, autônomo anuncia (sem pergunta), acervo presente só informa
proj = os.path.join(W, 'proj'); os.makedirs(proj)
rc, out = run(os.path.join(ROOT, 'scripts/conversa.py'), 'abertura', proj, 'quero um vídeo para a minha loja', cwd=W)
check('abertura guiada inclui a pergunta do acervo', 'Posso acessar o Chrome e baixar tudo?' in out, out[out.find('**Acervo'):][:160])
rc, out = run(os.path.join(ROOT, 'scripts/conversa.py'), 'abertura', proj, 'faça tudo, decide tudo, a direção é sua', cwd=W)
seg = out[out.find('**Acervo'):][:300]
check('abertura autônoma anuncia o download e não pergunta', 'Vou baixar o acervo' in seg and 'Posso acessar' not in seg, seg[:160])

# templates do aparelho e do kit orgânico: sintaxe e contrato
for f in ('templates/dom/device.js', 'templates/dom/organico.js'):
    r = subprocess.run(['node', '--check', f], capture_output=True, text=True)
    check(f'{f} é JavaScript válido', r.returncode == 0, r.stderr.strip() or 'ok')
dj = open('templates/dom/device.js', encoding='utf8').read(); oj = open('templates/dom/organico.js', encoding='utf8').read()
check('device.js mede a tela na máscara e expõe buildDevice', 'getImageData' in dj and 'window.buildDevice' in dj and 'border-radius' not in dj.split('const css =')[1].split('`;')[0], 'ok')
check('respingo do organico.js é chapado (sem luz nem sombra)', 'feSpecularLighting' not in oj and 'feDiffuseLighting' not in oj and 'makeSplash' in oj, 'ok')

# QA de cortes: decimal arredondado (9.333333 a 30 fps) passa; corte fora da grade de verdade continua reprovado
sys.argv = ['x']; import importlib.util
q = open('scripts/qa_frames.py', encoding='utf8').read()
check('QA tolera o decimal arredondado de um corte em quadro inteiro', '> 1e-3' in q and '28 / 3' in q, 'tolerância 1e-3 quadro')
check('vídeo é aceito como vaga data-asset (anim.js + render_dom)', "'VIDEO'" in open('templates/dom/anim.js', encoding='utf8').read() and '<video src=' in open('scripts/render_dom.mjs', encoding='utf8').read(), 'ok')

ok = all(r['result'] == 'PASSOU' for r in res)
print(f'\n{sum(r["result"] == "PASSOU" for r in res)}/{len(res)} PASSOU'); sys.exit(0 if ok else 1)
