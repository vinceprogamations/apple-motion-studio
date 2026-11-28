# Os dois textos que mais mudam o resultado: o combinado do início e a nota de entrega. Gera blocos prontos para mostrar.
#   python conversa.py abertura <projeto> "<pedido>" [--material <arquivo…>] [--mcp <ferramenta…>] [--alvo 1080|4k] [--site <id…>]
#   python conversa.py entrega <master.mp4> [--projeto <pasta>]
# abertura: o que vou fazer, como vamos trabalhar (checkpoints do modo), o material que melhora o filme, o que instalo/gasto/
#   faço no navegador, o que eu não consigo fazer e como dar uma nota. Curto: uma tela.
# entrega: o que foi verificado por máquina, o que ninguém verificou ainda (olhos e ouvidos humanos), onde olhar com
#   tempo exato, o que está fraco no material e como pedir mudanças.
import os, sys, json, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); sys.path.insert(0, HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
import ambiente, material
from lib import delegation as D

def tc(t):
    m, s = divmod(float(t), 60); return f'{int(m)}:{s:04.1f}'.replace('.', ',')

def estado(projeto):
    p = os.path.join(projeto or '', 'studio-state.json')
    return json.load(open(p, encoding='utf8')) if projeto and os.path.exists(p) else None

NOME = {'musica': 'a música', 'storyboard': 'o storyboard', 'paleta-sonora': 'o som', 'locucao': 'a locução', 'direcao-visual': 'a direção visual', 'foley': 'os efeitos', 'mix': 'a mixagem', 'assets': 'as imagens', 'master': 'o master', 'brief': 'o briefing'}
CHECK = {
    'autonomo': 'Você delegou: eu decido, reviso internamente e entrego uma versão pronta. Você só entra se quiser mudar algo.',
    'hibrido': 'Eu decido tudo, menos {reservado}. Paro só para isso e sigo com o resto em paralelo.',
    'guiado': 'Vou parar em dois momentos: (1) storyboard com quadros reais, antes de animar; (2) filme com som, antes do master. Fora isso eu sigo.'}

def abertura(projeto, pedido, arquivos, mcps, alvo, sites):
    st = estado(projeto) or D.classify(pedido or '')
    modo = (st or {}).get('mode', 'guiado'); res = (st or {}).get('reserved') or [k for k, v in (st or {}).get('decisions', {}).items() if v.get('status') == 'aguardando-usuario']
    L = ['**Como vamos trabalhar**', CHECK.get(modo, CHECK['guiado']).format(reservado=', '.join(NOME.get(x, x) for x in res) or 'o que você reservou')]
    rows = [material.checar(f, alvo) for f in arquivos]
    L += ['', '**Material**']
    if rows:
        L.append(material.texto(rows, alvo))
    L.append('O que mais melhora o filme, se você tiver: logo em SVG/PDF · fontes da marca · capturas reais da interface na maior resolução '
             '(ou o Figma) · fotos originais (não as do WhatsApp) · a frase final · 1 vídeo de referência de que você gosta e 1 de que não gosta.')
    rows_amb = ambiente.plano(); falta = [r for r in rows_amb if not r['ok']]
    L += ['', '**No seu computador**', ambiente.texto_plano(falta) if falta else
          'Nada a instalar: ' + ', '.join(r['nome'] for r in rows_amb) + ' já estão aqui. Se um dia faltar algo, mostro o quê, tamanho e origem e espero o seu sim.']
    s, d = ambiente.mcp(mcps)
    pagos = [x for x in s if x['custo'] != 'grátis']
    L += ['', '**Custo**', 'R$ 0: tudo roda aqui com ferramentas grátis e bibliotecas licenciadas.']
    if pagos or d: L.append('Conectadas e que podem cobrar (não uso sem você pedir e sem estimativa):\n' + ambiente.texto_mcp(pagos, d))
    # acervo de referências (modelos 3D, luz de estúdio, materiais, telas de apps): pergunta no guiado/híbrido, baixa no autônomo
    import acervo
    dac = acervo.pasta(argparse.Namespace(dir=None)); fac = [k for k, (sub, alvo, _) in acervo.PARTES.items() if acervo.contar(dac, sub) < alvo]
    if fac:
        L += ['', '**Acervo de referências**', ('Vou baixar o acervo grátis de referências (modelos 3D, luz de estúdio, materiais e telas de apps; ' + acervo.pergunta(fac).split('(')[-1].split(')')[0] + '), como parte do "faça tudo"; as licenças ficam em acervo.json.'
              if modo == 'autonomo' else acervo.pergunta(fac))]
    else:
        L += ['', '**Acervo de referências**', f'Já está aqui ({dac}): uso os modelos 3D, a luz de estúdio e as telas de app como referência.']
    L += ['', '**Navegador**', ambiente.texto_sites(sites) if sites else
          'Não vou usar o seu navegador: o Chrome que desenha os quadros roda invisível, separado das suas contas e abas. '
          'Se precisar baixar algo de um site, antes digo qual site, qual arquivo e a licença, e espero o seu sim.']
    L += ['', '**O que eu não consigo fazer**',
          'Eu não assisto nem ouço o filme como você: confiro quadros parados, meço tempo, volume e cortes. O ritmo e a emoção '
          'quem julga é você — por isso cada entrega diz exatamente onde olhar.',
          '', '**Como dar uma nota**', 'Com o tempo e o que mudar: "aos 0:12,4 o texto entra cedo", "o som do clique está agudo". '
          'Junte as notas numa mensagem só; eu mudo só aquele trecho e mantenho o resto igual.']
    return '\n'.join(L)

def entrega(master, projeto=None):
    base = os.path.splitext(master)[0]; pj = base + '.promote.json'
    prom = json.load(open(pj, encoding='utf8')) if os.path.exists(pj) else {}
    tlp = prom.get('timeline') or base + '.timeline.json'
    root = os.getcwd()
    if tlp and not os.path.exists(tlp) and os.path.exists(os.path.join(os.path.dirname(master), os.path.basename(tlp))): tlp = os.path.join(os.path.dirname(master), os.path.basename(tlp))
    tl = json.load(open(tlp, encoding='utf8')) if tlp and os.path.exists(tlp) else {}
    info = material.probe(master); v = next((x for x in info.get('streams', []) if x.get('codec_type') == 'video'), {})
    a = next((x for x in info.get('streams', []) if x.get('codec_type') == 'audio'), None); dur = float(info.get('format', {}).get('duration', 0) or 0)
    L = [f"**Entrega:** {os.path.basename(master)} — {v.get('width')}×{v.get('height')}, {tc(dur)}, {'com' if a else 'SEM'} som"]
    L += ['', '**Verificado por máquina**', f"- Quadros: {'QA ok (preto, congelado, repetidos, duração)' if prom.get('qa') == 'ok' else 'QA de quadros NÃO rodou/promoção ausente — rode qa_frames.py e studio.py promote'}"]
    if a:
        loud = medir(master)
        if loud: L.append(f'- Áudio: {loud}')
    L += ['', '**Ainda não verificado por ninguém**', '- Eu não assisti nem ouvi o filme em tempo real. Ritmo, emoção e se o som cansa: só você julga.']
    cenas = tl.get('scenes', [])
    if cenas:
        L += ['', '**Onde olhar** (tempo → cena)'] + [f"- {tc(c['start'])} {c['id']}" for c in cenas[:12]] + (['- …'] if len(cenas) > 12 else [])
    man = os.path.join(projeto or os.path.dirname(os.path.dirname(os.path.abspath(master))), 'asset-manifest.json')
    if os.path.exists(man):
        alvo = '4k' if int(v.get('height') or 0) >= 2000 else '1080'
        mroot = os.path.dirname(man); fr = []
        for x in json.load(open(man, encoding='utf8')).get('assets', []):
            f = x.get('file') or x.get('path')
            if f and os.path.exists(os.path.join(mroot, f)):
                r = material.checar(os.path.join(mroot, f), alvo, 'logo' if 'logo' in (x.get('id', '') + f).lower() else 'auto')
                if r['nivel'] != 'ok': fr.append(f"- {os.path.basename(f)}: {r['detalhe']} → mande {r['pedir']}")
        if fr: L += ['', '**O que limita a nitidez**'] + fr
    ex = cenas[min(2, len(cenas) - 1)] if cenas else None
    L += ['', '**Para pedir mudanças**', f'Diga o tempo e o que mudar (ex.: "aos {tc(ex["start"] + 0.5) if ex else "0:05,0"} entra cedo, atrase meio segundo"). '
          'Mudo só aquele trecho, gero uma versão nova e o master atual fica guardado.']
    return '\n'.join(L)

def medir(mp4):
    from lib.tools import find_tool
    ff = find_tool('ffmpeg', required=False)
    if not ff: return ''
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', mp4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf8', errors='replace')
    import re
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr); p = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr)
    return f'{i[-1]} LUFS integrado, pico real {p[-1]} dBTP (alvo web: −14 LUFS, ≤ −1 dBTP)' if i and p else ''

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['abertura', 'entrega']); ap.add_argument('alvo_pos', nargs='+')
    ap.add_argument('--material', nargs='*', default=[]); ap.add_argument('--mcp', nargs='*', default=[]); ap.add_argument('--site', nargs='*', default=[])
    ap.add_argument('--alvo', default='1080'); ap.add_argument('--projeto'); a = ap.parse_args()
    if a.cmd == 'abertura':
        projeto, pedido = (a.alvo_pos + [''])[:2]; print(abertura(projeto, pedido, a.material, a.mcp, a.alvo, a.site))
    else: print(entrega(a.alvo_pos[0], a.projeto))

if __name__ == '__main__': main()
