# Etapa 4 — relacionamento com o usuário: instalação só com sim registrado, ferramentas pagas identificadas e avisadas,
# navegador anunciado com licença, material fraco detectado com o pedido certo, combinado e entrega honestos.
#   python tests/run_relacionamento.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, json, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT); sys.path.insert(0, 'scripts')
import ambiente, material, conversa
from lib import delegation as D
from PIL import Image
PY = sys.executable; W = 'tests/_work/relacionamento'; EV = 'tests/evidence/15-relacionamento'
shutil.rmtree(W, ignore_errors=True); os.makedirs(W); os.makedirs(EV, exist_ok=True); res = []
def check(n, ok, d): res.append({'name': n, 'result': 'PASSOU' if ok else 'FALHOU', 'detail': str(d)[:300]}); print('PASSOU' if ok else 'FALHOU', n, '·', str(d)[:160])
def run(*a): r = subprocess.run([PY, *a], capture_output=True, text=True, encoding='utf8', errors='replace'); return r.returncode, r.stdout + r.stderr

# 1. instalação: sem sim não instala (exit 3, plano com tamanho e origem); com sim registra o consentimento (ensaio, nada roda)
fake = [{'id': 'blender', 'nome': 'Blender', 'perfil': '3d', 'por_que': 'x', 'mb': 400, 'custo': 'grátis', 'fonte': 'https://www.blender.org', 'ok': False, 'onde': '', 'comando': 'winget install -e --id BlenderFoundation.Blender'}]
ambiente.plano = lambda perfil=None: fake; ambiente.CONSENT = os.path.join(W, 'consent.json')
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf): rc = ambiente.instalar(['faltando'], None, None)
out = buf.getvalue(); open(f'{EV}/plano-sem-sim.txt', 'w', encoding='utf8').write(out)
check('sem o sim do usuário nada é instalado (exit 3) e o plano diz tamanho e origem', rc == 3 and '400 MB' in out and 'blender.org' in out and not os.path.exists(ambiente.CONSENT), out.splitlines()[1] if len(out.splitlines()) > 1 else out)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): rc = ambiente.instalar(['faltando'], 'sim, pode instalar', None, dry=True)
log = json.load(open(ambiente.CONSENT, encoding='utf8')) if os.path.exists(ambiente.CONSENT) else []
check('com o sim: consentimento gravado com as palavras do usuário e os itens', log and log[-1]['palavras_do_usuario'] == 'sim, pode instalar' and log[-1]['o_que'] == ['blender'], log)

# 2. MCPs: pagos reconhecidos por servidor, desconhecido tratado como pago, grátis separado
nomes = ['mcp__1c18__creative_generate_speech', 'mcp__1c18__account_get_usage', 'mcp__4c57__estimate_video_cost', 'mcp__4c57__generate_video',
         'mcp__6f2d__generate-design', 'mcp__claude-in-chrome__navigate', 'mcp__misterioso__fazer']
s, d = ambiente.mcp(nomes); ids = {x['id']: x['custo'] for x in s}; txt = ambiente.texto_mcp(s, d); open(f'{EV}/mcp.txt', 'w', encoding='utf8').write(txt)
check('ElevenLabs e Higgsfield marcados como PAGOS, Canva freemium, navegador grátis', ids.get('elevenlabs') == 'pago' and ids.get('higgsfield') == 'pago' and ids.get('canva') == 'freemium' and ids.get('navegador') == 'grátis', ids)
check('conector desconhecido é tratado como pago e o aviso promete estimativa antes', d == ['misterioso'] and 'trato como pagos' in txt and 'estimativa' in txt, d)
check('sem conectores pagos: o aviso diz que tudo é grátis', 'gratuito' in ambiente.texto_mcp(*ambiente.mcp(['mcp__claude-in-chrome__navigate'])) or 'GRÁTIS' in ambiente.texto_mcp(*ambiente.mcp(['mcp__claude-in-chrome__navigate'])), '')

# 3. navegador: site, licença, um por vez, sem senha/CAPTCHA
t = ambiente.texto_sites(['pixabay', 'freesound'])
check('aviso de navegador: licença por site, um arquivo por vez, sem senha nem CAPTCHA', all(k in t for k in ('Pixabay', 'Freesound', 'não comercial', 'confirmo', 'CAPTCHA', 'senha')), t.splitlines()[0])

# 4. delegação: "faz tudo" não autoriza instalar; "pode instalar" sim; verba 0 por padrão
a, b = D.classify('faz tudo aí'), D.classify('faz tudo aí, pode instalar o que precisar')
check('"faz tudo" não vira permissão de instalar; "pode instalar" vira; verba padrão 0', not a['constraints'].get('instalar') and b['constraints'].get('instalar') and a['constraints']['verba'] == 0, (a['constraints'], b['constraints']))

# 5. material: logo pequeno sem alfa → pedir vetor e transparência; foto grande ok; 4K exige mais
Image.new('RGB', (300, 300), 'white').save(f'{W}/logo.png'); Image.new('RGBA', (900, 900), (0, 0, 0, 0)).save(f'{W}/logo-grande.png')
Image.new('RGB', (2600, 1500), 'gray').save(f'{W}/foto.jpg')
r1, r2, r3, r4 = material.checar(f'{W}/logo.png'), material.checar(f'{W}/logo-grande.png'), material.checar(f'{W}/foto.jpg'), material.checar(f'{W}/foto.jpg', '4k')
open(f'{EV}/material.txt', 'w', encoding='utf8').write(material.texto([r1, r2, r3, r4], '1080'))
check('logo 300 px sem fundo transparente: pede SVG e transparência', r1['nivel'] != 'ok' and 'SVG' in r1['pedir'] and 'transparente' in r1['pedir'], r1['pedir'])
check('logo 900 px com alfa e foto 2600 px passam em 1080; a mesma foto é fraca em 4K', r2['nivel'] == 'ok' and r3['nivel'] == 'ok' and r4['nivel'] != 'ok', (r2['nivel'], r3['nivel'], r4['nivel']))

# 6. combinado: checkpoints do modo, custo, limites, formato de nota
ab = conversa.abertura('', 'Faça tudo, mas quero escolher a música', [f'{W}/logo.png'], ['mcp__1c18__creative_generate_speech'], '1080', ['pexels'])
open(f'{EV}/abertura.md', 'w', encoding='utf8').write(ab)
check('combinado: modo híbrido, material fraco, custo, navegador, "não assisto nem ouço" e formato de nota',
      'menos a música' in ab and 'SVG' in ab and 'PAGO' in ab and 'Pexels' in ab and 'não assisto nem ouço' in ab and 'aos 0:12,4' in ab, ab.splitlines()[1])

# 7. entrega: separa medido de não verificado, onde olhar, como pedir mudança (usa um MP4 sintético)
from lib.tools import find_tool
ff = find_tool('ffmpeg'); mp4 = f'{W}/out/Teste - MASTER.mp4'; os.makedirs(f'{W}/out')
subprocess.run([ff, '-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=640x360:d=3:r=30', '-f', 'lavfi', '-i', 'sine=f=440:d=3', '-shortest', '-c:v', 'libx264', '-c:a', 'aac', mp4], check=True)
json.dump({'qa': 'ok', 'timeline': f'{W}/out/Teste.timeline.json'}, open(f'{W}/out/Teste - MASTER.promote.json', 'w'))
json.dump({'fps': 30, 'total': 3, 'scenes': [{'id': 'abre', 'start': 0, 'end': 1.5}, {'id': 'fecho', 'start': 1.5, 'end': 3}]}, open(f'{W}/out/Teste.timeline.json', 'w'))
json.dump({'assets': [{'id': 'logo', 'file': 'logo.png'}]}, open(f'{W}/asset-manifest.json', 'w'))
en = conversa.entrega(mp4); open(f'{EV}/entrega.md', 'w', encoding='utf8').write(en)
check('entrega: QA medido, "não assisti nem ouvi", tempo → cena, logo fraco e como pedir mudança',
      'QA ok' in en and 'LUFS' in en and 'não assisti nem ouvi' in en and '0:01,5 fecho' in en and 'logo.png' in en and 'Diga o tempo' in en, en.splitlines()[0])

# 9. falhas achadas no teste real (agente Claude, 25/11/2026)
c, out = run('scripts/ambiente.py', 'mcp', '--mcp', 'mcp__4c57__generate_video')
check('ambiente.py mcp aceita --mcp (antes ignorava e dizia "nada cobra")', 'Higgsfield' in out, out.splitlines()[0] if out else '')
c, out = run('scripts/casos.py', 'sugerir', 'Faz tudo aí: vídeo de lançamento do meu app Lumen')
check('casos.py no modo autônomo não pergunta "Como prefere seguir?"', 'Modo autônomo' in out and 'Como prefere' not in out, out.splitlines()[0])
ab2 = conversa.abertura('', 'faz tudo aí', [], [], '1080', [])
check('combinado sempre responde instalar e navegador, mesmo sem nada faltando', '**No seu computador**' in ab2 and '**Navegador**' in ab2, '')
os.makedirs(f'{W}/outra/assets'); Image.new('RGBA', (1200, 1200), (0, 0, 0, 0)).save(f'{W}/outra/assets/logo.png')
json.dump({'assets': [{'id': 'logo', 'file': 'assets/logo.png', 'license': 'marca de terceiros — só portfólio, não comercial'}]}, open(f'{W}/outra/asset-manifest.json', 'w', encoding='utf8'), ensure_ascii=False)
r5 = material.checar(f'{W}/outra/assets/logo.png')
check('material de outro projeto com licença restrita é barrado e pede o arquivo próprio', r5['nivel'] == 'restrito' and 'próprio' in r5['pedir'], r5['detalhe'][-80:])

# 8. o SKILL.md liga tudo
sk = open('SKILL.md', encoding='utf8').read()
check('SKILL.md: seção de relacionamento, permissões nunca delegadas, entrega honesta', all(k in sk for k in ('Relacionamento com o usuário', 'permissão, nunca gosto', 'conversa.py entrega', 'material.py checar')), '')
json.dump(res, open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(f"\n{sum(r['result'] == 'PASSOU' for r in res)}/{len(res)} passaram"); sys.exit(0 if all(r['result'] == 'PASSOU' for r in res) else 1)
