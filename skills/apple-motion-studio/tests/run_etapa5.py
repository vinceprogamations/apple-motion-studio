# Etapa 5: briefing completo, estimativa de tempo com consentimento, motion blur no render DOM, aviso de pico atrasado no mix,
# medição de andamento e teste de celular com as áreas do Reels. Tudo com material sintético de resposta conhecida.
#   python tests/run_etapa5.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, json, shutil, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT); sys.path.insert(0, 'scripts')
from lib.tools import find_tool
import briefing
PY = sys.executable; FF = find_tool('ffmpeg'); W = os.path.abspath('tests/_work/etapa5'); EV = 'tests/evidence/16-etapa5'
shutil.rmtree(W, ignore_errors=True); os.makedirs(W); os.makedirs(EV, exist_ok=True); res = []
def check(n, ok, d): res.append({'name': n, 'result': 'PASSOU' if ok else 'FALHOU', 'detail': str(d)[:300]}); print('PASSOU' if ok else 'FALHOU', n, '·', str(d)[:150])
def run(*a, t=600): r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf8', errors='replace', timeout=t); return r.returncode, r.stdout + r.stderr

# 1. briefing: pedido vago → todas; pedido detalhado → só o que falta; blocos de até 4; registrar
r0 = briefing.perguntas('Faça um vídeo da minha empresa')
r1 = briefing.perguntas('Reels de 30 segundos para donos de academias, sem voz, faz tudo aí, com pessoas e música com drop')
check('briefing: pedido vago traz o questionário inteiro em blocos de até 4, com a permissão da estimativa no fim', r0['faltam'] == len(briefing.Q) + 1 and r0['blocos'][-1][-1]['id'] == 'estimativa' and all(len(b) <= 4 for b in r0['blocos']), r0['faltam'])
ra = briefing.perguntas('Faz tudo aí: vídeo de lançamento da minha cafeteria')
check('briefing: no modo autônomo só a permissão da estimativa é perguntada', [q['id'] for b in ra['blocos'] for q in b] == ['estimativa'], [q['id'] for b in ra['blocos'] for q in b])
check('briefing: o que o pedido já respondeu não é perguntado de novo', {'destino', 'duracao', 'publico', 'voz', 'modo', 'pessoas', 'musica'} <= set(r1['ja_respondidas']), r1['ja_respondidas'])
check('briefing: toda pergunta tem 2–4 opções e a recomendada vem primeiro quando há', all(2 <= len(q['options']) <= 4 for b in r0['blocos'] for q in b)
      and all(not any('Recommended' in o['label'] for o in q['options'][1:]) for b in r0['blocos'] for q in b), '')
briefing.registrar(f'{W}/proj', {'destino': 'Reels 9:16', 'mensagem': 'Visita vira aluna.'}); r2 = briefing.perguntas('vídeo', f'{W}/proj')
check('briefing: respostas registradas no estado não voltam como pergunta', 'destino' not in [q['id'] for b in r2['blocos'] for q in b], r2['ja_respondidas'])

# 2. estimativa: sem --sim recusa; estimar funciona e cresce com blur/formatos/Blender
c, out = run(PY, 'scripts/estimativa.py', 'ler'); check('estimativa: ler o PC sem consentimento é recusado e mostra a pergunta a fazer', c != 0 and 'Posso ler' in out, out.strip()[:120])
def est(*a): c, o = run(PY, 'scripts/estimativa.py', 'estimar', '--json', *a); return json.loads(o)
e1, e2, e3 = est('--dur', '30'), est('--dur', '30', '--blur', '6', '--formatos', '2'), est('--dur', '30', '--blender-quadros', '200', '--blender-tipo', 'produto')
def seg(s): p = s.split(); return int(p[0]) * 3600 + int(p[2]) * 60 if 'h' in p else (int(p[0]) * 60 if 'min' in p else int(p[0]))
check('estimativa: blur e formatos aumentam o render; Blender de produto aparece', seg(e2['maquina']['renders do filme']) > seg(e1['maquina']['renders do filme']) and 'Blender' in e3['maquina'], (e1['render_unico'], e2['render_unico'], e3['maquina'].get('Blender')))
json.dump([e1, e2, e3], open(f'{EV}/estimativas.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)

# 3. motion blur no render DOM: mesma contagem de quadros, imagem diferente num movimento rápido, corte não misturado
os.makedirs(f'{W}/blur'); open(f'{W}/blur/asset-manifest.json', 'w').write('{"assets": []}')
open(f'{W}/blur/p.html', 'w').write('''<!doctype html><html><body style="margin:0;width:640px;height:360px;background:#000;overflow:hidden">
<div id="q" style="position:absolute;top:130px;width:100px;height:100px;background:#fff"></div><script>
window.TOTAL=1; window.EVENTS=[]; window.TIMELINE={total:1,scenes:[{id:'a',start:0,end:0.5},{id:'b',start:0.5,end:1}],intentional:[]};
window.renderAt=t=>{ q.style.left=(t<0.5? 40+t*1600 : 40)+'px'; q.style.background=t<0.5?'#fff':'#f00'; };
window.ready=Promise.resolve(true);</script></body></html>''')
for b in ('1', '6'):
    run('node', 'scripts/render_dom.mjs', 'video', f'{W}/blur/p.html', f'{W}/blur/b{b}.mp4', '--root', f'{W}/blur', '--w', '640', '--h', '360', '--fps', '30', '--blur', b)
def frames(f): return np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', f, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout, np.uint8).reshape(-1, 360, 640, 3)
f1, f6 = frames(f'{W}/blur/b1.mp4'), frames(f'{W}/blur/b6.mp4')
row = lambda f: (f[180, :, 0].astype(int) > 40).sum()                        # largura do rastro branco/vermelho na linha central
check('blur: mesma quantidade de quadros e rastro mais largo no movimento', len(f1) == len(f6) == 30 and row(f6[7]) > row(f1[7]) + 20, (len(f1), len(f6), row(f1[7]), row(f6[7])))
check('blur: o quadro logo depois do corte não mistura o plano anterior (sem branco no plano vermelho)', int((f6[15][..., 1] > 120).sum()) < 50, int((f6[15][..., 1] > 120).sum()))

# 4. mix: aviso de pico atrasado
SR = 48000; os.makedirs(f'{W}/lib')
def wav(path, x): subprocess.run([FF, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', path], input=x.astype(np.float32).tobytes(), check=True)
t = np.arange(int(0.8 * SR)) / SR; boom = np.sin(2 * np.pi * 50 * t) * np.clip((t - 0.02) / 0.28, 0, 1) * np.exp(-np.clip(t - 0.3, 0, None) * 6)   # sobe 280 ms até o pico
wav(f'{W}/lib/boom_lento.wav', boom); wav(f'{W}/lib/clique.wav', np.sin(2 * np.pi * 2000 * t[:2400]) * np.exp(-t[:2400] * 300))
json.dump([{'at': 1.0, 'file': 'boom_lento', 'db': -6, 'align': 'start'}, {'at': 1.5, 'file': 'clique', 'db': -6, 'align': 'start'}], open(f'{W}/cues.json', 'w'))
c, out = run(PY, 'scripts/mix.py', f'{W}/cues.json', f'{W}/m.wav', '--lib', f'{W}/lib', '--len', '3')
check('mix: avisa o golpe com pico atrasado alinhado pelo início (e só ele)', 'boom_lento' in out and 'AVISO' in out and 'clique' not in out.split('AVISO')[-1].split('\n')[0], [l for l in out.splitlines() if 'AVISO' in l][:2])

# 5. batidas: trilha sintética a 126 BPM com bumbo sincopado + chimbal regular
P = 60 / 126; d = 70; y = np.zeros(int(d * SR))
for k in range(int(d / P)):
    i = int(k * P * SR); n = int(0.03 * SR); y[i:i + n] += np.random.default_rng(k).standard_normal(n) * np.exp(-np.arange(n) / (0.004 * SR)) * 0.3   # chimbal em toda batida
    if k % 4 in (0, 3):                                                                                                                    # bumbo sincopado (garage)
        j = int((k * P + (0.25 * P if k % 4 == 3 else 0)) * SR); m = int(0.2 * SR); y[j:j + m] += np.sin(2 * np.pi * 55 * np.arange(m) / SR) * np.exp(-np.arange(m) / (0.05 * SR))
wav(f'{W}/trilha.wav', y)
c, out = run(PY, 'scripts/batidas.py', f'{W}/trilha.wav', '--de', '2', '--ate', '68', '--grade', '0.4645', '--json'); r = json.loads(out[out.index('{'):])
check('batidas: acha o andamento real (126 BPM) e o atempo para a grade', abs(r['bpm'] - 126) < 0.3 and abs(r['atempo_para_grade'] - P / 0.4645) < 0.003, (r['bpm'], r['escolhida'], r.get('atempo_para_grade')))

# 6. celular: texto na base de um 9:16 é apontado; no meio, não
from PIL import Image, ImageDraw, ImageFont
def card(path, y):
    im = Image.new('RGB', (1080, 1920), (10, 10, 12)); dr = ImageDraw.Draw(im)
    for k in range(12): dr.rectangle([120 + k * 70, y, 160 + k * 70, y + 120], fill=(240, 240, 240))   # "letras" grandes
    im.save(path)
card(f'{W}/meio.png', 900); card(f'{W}/base.png', 1700)
for n in ('meio', 'base'): subprocess.run([FF, '-v', 'error', '-y', '-loop', '1', '-i', f'{W}/{n}.png', '-t', '3', '-r', '30', '-pix_fmt', 'yuv420p', f'{W}/{n}.mp4'], check=True)
c1, o1 = run(PY, 'scripts/qa_celular.py', f'{W}/meio.mp4', '--saida', f'{W}/qm'); c2, o2 = run(PY, 'scripts/qa_celular.py', f'{W}/base.mp4', '--saida', f'{W}/qb')
a1 = json.load(open(f'{W}/qm/celular.json'))['alertas_areas']; a2 = json.load(open(f'{W}/qb/celular.json'))['alertas_areas']
check('celular: conteúdo na base do 9:16 é apontado; no meio, não', not a1 and a2 and all(x['area'] == 'base' for x in a2), (len(a1), len(a2)))
for f in ('qb/celular_areas.jpg',): shutil.copy(f'{W}/{f}', f'{EV}/celular_areas_base.jpg')

# 7. SKILL.md liga tudo
sk = open('SKILL.md', encoding='utf8').read()
check('SKILL.md: questionário, estimativa com consentimento, crítica com nota e novas ferramentas', all(k in sk for k in ('briefing.py perguntas', 'estimativa.py ler --sim', 'critica.md', 'qa_celular.py', 'batidas.py', '--blur')), '')
json.dump(res, open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(f"\n{sum(r['result'] == 'PASSOU' for r in res)}/{len(res)} passaram"); sys.exit(0 if all(r['result'] == 'PASSOU' for r in res) else 1)
