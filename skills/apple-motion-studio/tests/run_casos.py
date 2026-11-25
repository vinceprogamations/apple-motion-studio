# Catálogo de estudos de caso: descoberta, no máximo duas sugestões com motivo e risco, as quatro saídas, a preferência "sem cases"
# respeitada (também numa revisão), escolha registrada com o estado certo, e a apresentação montada pelo motor de slides.
#   python tests/run_casos.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, json, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib import delegation as D
import casos as C
PY = sys.executable; W = 'tests/_work/casos'; EV = 'tests/evidence/14-casos'; shutil.rmtree(W, ignore_errors=True); os.makedirs(W); os.makedirs(EV, exist_ok=True)
res = []
def check(n, ok, d): res.append({'name': n, 'result': 'PASSOU' if ok else 'FALHOU', 'detail': d}); print('PASSOU' if ok else 'FALHOU', n, '·', d)
def run(*a): r = subprocess.run([PY, *a], capture_output=True, text=True, encoding='utf8', errors='replace'); return r.returncode, r.stdout + r.stderr
BRIEF = 'Faça uma apresentação comercial da Lumen, minha software house, para uma rede de clínicas.'
idx = C.indice(); fichas = [f for f in os.listdir('references/casos') if f.endswith('.md') and f != 'README.md']
check('catálogo: 14 fichas, todas no índice, todas com as 4 seções', len(fichas) == 14 and {c['id'] for c in idx} == {f[:-3] for f in fichas}
      and all(C.secao(c['id'], s) for c in idx for s in ('Quando consultar', 'Aplicação proposta', 'Quando pode atrapalhar', 'Teste na peça')), f'{len(fichas)} fichas')
sug = C.sugerir(BRIEF)
check('briefing software house: até duas sugestões, a institucional primeiro', 1 <= len(sug) <= 2 and sug[0]['id'] == 'thoughtworks-etsy', [s['id'] for s in sug])
c, out = run('scripts/casos.py', 'sugerir', BRIEF); open(f'{EV}/primeira-resposta-bloco.md', 'w', encoding='utf8').write(out)
check('o bloco diz por que combina, quando pode piorar e dá as 4 saídas', all(k in out for k in ('Por que combina', 'Quando pode piorar', 'Decida você', 'Escolho eu', 'Ver o catálogo', 'Sem cases'))
      and 'apresentação comercial' in out, 'texto em ' + f'{EV}/primeira-resposta-bloco.md')
check('pedido sem relação com o catálogo: nenhuma sugestão forçada', C.sugerir('Faça um logo animado de 3 segundos.') == [], 'logo animado → nenhuma')
st = D.init(f'{W}/sem', BRIEF + ' Sem cases.'); c, out = run('scripts/casos.py', 'sugerir', 'Troque o texto do slide 2.', '--projeto', f'{W}/sem')
check('"sem cases": preferência gravada e nada sugerido, nem numa revisão', st['constraints'].get('casos') is False and 'sem cases' in out and 'Por que combina' not in out, out.strip())
st = D.init(f'{W}/aut', 'Faz tudo aí. ' + BRIEF); c, out = run('scripts/casos.py', 'usar', f'{W}/aut', 'thoughtworks-etsy', 'figma-config', '--por', 'agente')
st = D.load(f'{W}/aut'); r = st['decisions'].get('referencias', {})
check('"faz tudo aí": modo autônomo, escolha do agente registrada como delegada', st['mode'] == 'autonomo' and r.get('status') == 'delegado-agente' and r.get('choice') == 'thoughtworks-etsy, figma-config', r)
D.init(f'{W}/gui', BRIEF); c, out = run('scripts/casos.py', 'usar', f'{W}/gui', 'figma-config'); r = D.load(f'{W}/gui')['decisions']['referencias']
check('"escolho eu": escolha do usuário registrada como aprovada por ele', r['status'] == 'aprovado-usuario' and r['choice'] == 'figma-config', r)
c, out = run('scripts/casos.py', 'listar'); check('"ver o catálogo": índice completo', out.count('.md)') == 14, f'{out.count(".md)")} linhas de referência')
c, out = run('scripts/apresentacao.py', 'init', f'{W}/apres')
ok = all(os.path.exists(f'{W}/apres/{f}') for f in ('page.html', 'slides.js', 'asset-manifest.json'))
check('apresentacao.py init cria página, dados e manifesto', ok, out.strip()[:120])
json.dump(res, open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(f"\n{sum(r['result'] == 'PASSOU' for r in res)}/{len(res)} passaram"); sys.exit(0 if all(r['result'] == 'PASSOU' for r in res) else 1)
