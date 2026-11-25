# Catálogo de estudos de caso (references/casos/): sugere no máximo DUAS referências para um pedido, diz por que combinam e em
# que situação cada uma pode piorar a peça, e respeita a preferência do usuário ("sem cases").
#   python casos.py sugerir "<pedido do usuário>" [--projeto <pasta>] [--max 2] [--json]
#   python casos.py listar                    # o índice inteiro (objetivo → referência → situação)
#   python casos.py ver <id>                  # a ficha completa (fonte, aplicação, quando atrapalha, teste)
#   python casos.py usar <projeto> <id> [<id>] [--por usuario|agente]   # registra a escolha no studio-state.json
#   python casos.py sem <projeto>             # registra "sem cases": nada é sugerido nem citado daí em diante
# As fichas são material de DIREÇÃO (como resolver uma situação), nunca de conteúdo: não copie métricas, textos nem marcas.
import sys, os, re, json, unicodedata, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); CASOS = os.path.join(SKILL, 'references', 'casos')
sys.path.insert(0, HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass

def norm(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
def indice(): return json.load(open(os.path.join(CASOS, 'indice.json'), encoding='utf8'))['casos']
def secao(cid, nome):
    md = open(os.path.join(CASOS, cid + '.md'), encoding='utf8').read()
    m = re.search(r'## ' + nome + r'\s*\n+(.*?)(?=\n## |\Z)', md, re.S); return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
def fonte(cid):
    m = re.search(r'\[([^\]]+)\]\((https?://[^)]+)\)', open(os.path.join(CASOS, cid + '.md'), encoding='utf8').read()); return (m.group(1), m.group(2)) if m else ('', '')

def preferencia(projeto):
    if not projeto: return None
    p = os.path.join(projeto, 'studio-state.json')
    if not os.path.exists(p): return None
    st = json.load(open(p, encoding='utf8')); return st.get('constraints', {}).get('casos')

def sugerir(pedido, mx=2):
    t = ' ' + norm(pedido) + ' '; out = []
    for c in indice():
        hits = [k for k in c['sinais'] if re.search(r'(?<![a-z])' + re.escape(k) + r'(?![a-z])', t)]
        score = sum(c['sinais'][k] for k in hits)
        if score >= 3: out.append({'id': c['id'], 'titulo': c['titulo'], 'objetivo': c['objetivo'], 'score': score, 'sinais': hits,
                                   'situacao': secao(c['id'], 'Quando consultar'), 'aplicacao': secao(c['id'], 'Aplicação proposta'),
                                   'atrapalha': secao(c['id'], 'Quando pode atrapalhar'), 'teste': secao(c['id'], 'Teste na peça'), 'fonte': fonte(c['id'])})
    out.sort(key=lambda r: (-r['score'], r['id'])); return out[:mx]

def mostrar(pedido, sinais):
    """sinais casados → como o usuário escreveu (com acentos), sem repetir um sinal contido em outro maior"""
    keep = [k for k in sinais if not any(k != o and k in o for o in sinais)]
    words = re.findall(r"[\w-]+", pedido); nw = [norm(w) for w in words]; out = []
    for k in keep:
        ks = k.split(); n = len(ks)
        for i in range(len(nw) - n + 1):
            if nw[i:i + n] == ks: out.append(' '.join(words[i:i + n])); break
        else: out.append(k)
    return out

def texto(pedido, sug):
    """O bloco que o agente mostra no primeiro briefing (modo guiado/híbrido)."""
    if not sug:
        return ('Catálogo de estudos de caso: nenhuma das 14 referências corresponde bem a este pedido, então sigo sem elas. '
                'Se quiser ver o catálogo mesmo assim: `python scripts/casos.py listar`.')
    L = [f'**Antes de começar:** a skill tem um catálogo com 14 estudos de caso (produção, apresentações, som, 3D). '
         f'{"Duas combinam" if len(sug) == 2 else "Uma combina"} com o seu pedido:', '']
    for i, s in enumerate(sug, 1):
        L += [f'{i}. **{s["titulo"]}** — {s["objetivo"].lower()}.',
              f'   - *Por que combina:* seu pedido fala em {", ".join(chr(34) + x + chr(34) for x in mostrar(pedido, s["sinais"])[:3])}, que é a situação desta ficha: {s["situacao"][0].lower() + s["situacao"][1:]}',
              f'   - *O que eu faria com ela:* {s["aplicacao"]}',
              f'   - *Quando pode piorar a apresentação:* {s["atrapalha"]}', '']
    L += ['Como prefere seguir?',
          '- **Decida você** — eu aplico o que servir dessas referências e sigo (ou diga "faz tudo aí").',
          '- **Escolho eu** — diga qual (1, 2, as duas ou nenhuma).',
          '- **Ver o catálogo** — mostro as 14 fichas com a situação de cada uma.',
          '- **Sem cases** — sigo só pelo seu briefing e não volto a sugerir referências neste projeto.']
    return '\n'.join(L)

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sugerir'); s.add_argument('pedido'); s.add_argument('--projeto'); s.add_argument('--max', type=int, default=2); s.add_argument('--json', action='store_true')
    sub.add_parser('listar'); v = sub.add_parser('ver'); v.add_argument('id')
    u = sub.add_parser('usar'); u.add_argument('projeto'); u.add_argument('ids', nargs='+'); u.add_argument('--por', default='usuario')
    n = sub.add_parser('sem'); n.add_argument('projeto')
    a = ap.parse_args()
    if a.cmd == 'sugerir':
        pref = preferencia(a.projeto)
        if pref is False:
            r = {'preferencia': 'sem cases', 'sugestoes': []}; print(json.dumps(r, ensure_ascii=False) if a.json else 'Preferência do projeto: sem cases (nada a sugerir).'); return
        sug = sugerir(a.pedido, min(2, a.max))
        print(json.dumps({'sugestoes': sug}, ensure_ascii=False, indent=1) if a.json else texto(a.pedido, sug)); return
    if a.cmd == 'listar':
        print(open(os.path.join(CASOS, 'README.md'), encoding='utf8').read()); return
    if a.cmd == 'ver':
        p = os.path.join(CASOS, a.id + '.md')
        if not os.path.exists(p): sys.exit(f'não existe a ficha {a.id}; ids: ' + ', '.join(c['id'] for c in indice()))
        print(open(p, encoding='utf8').read()); return
    from lib import delegation as D
    st = D.load(a.projeto)
    if a.cmd == 'sem':
        st['constraints']['casos'] = False; st['decisions']['referencias'] = {'status': 'aprovado-usuario', 'choice': 'sem cases', 'scope': 'preferência do usuário: não sugerir nem citar estudos de caso neste projeto'}
    else:
        ids = [i for i in a.ids if i in {c['id'] for c in indice()}][:2]
        if not ids: sys.exit('ids inválidos')
        st['constraints']['casos'] = True
        st['decisions']['referencias'] = {'status': 'aprovado-usuario' if a.por == 'usuario' else 'delegado-agente', 'choice': ', '.join(ids),
                                          'scope': 'escolhidas pelo usuário' if a.por == 'usuario' else f'escolha do agente por delegação: "{st["words"]}"'}
    D.save(a.projeto, st); print(D.summary(st))

if __name__ == '__main__': main()
