# Briefing completo numa rodada: lê o pedido do usuário, descobre o que ele JÁ respondeu e devolve só as perguntas que faltam,
# cada uma com opções prontas (a recomendada primeiro). O modelo processa muito melhor um filme quando sabe para quem, onde,
# o que mostrar, que sensação, que material existe e que música — então pergunte tudo de uma vez, nunca a conta-gotas.
#   python briefing.py perguntas "<pedido>" [--projeto <pasta>] [--json]   # perguntas que faltam (blocos de até 4, p/ AskUserQuestion)
#   python briefing.py registrar <projeto> '<json {id: resposta}>'         # grava as respostas em studio-state.json (briefing)
#   python briefing.py resumo <projeto>                                    # o briefing consolidado, para o combinado e o storyboard
# Modo autônomo ("faz tudo aí"): NÃO pergunte gosto — use as recomendadas e registre como delegado. Só permissões são perguntadas.
import sys, os, re, json, unicodedata, argparse, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass

def norm(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')

# (id, cabeçalho ≤12, pergunta, opções [(rótulo, descrição)], multi?, regex que indica que o pedido já respondeu)
Q = [
 ('destino', 'Onde roda', 'Onde o vídeo vai rodar?', [
    ('Reels/TikTok 9:16 (Recommended)', 'Vertical 1080×1920, texto grande, fora das áreas da interface do app'),
    ('YouTube/site 16:9', 'Horizontal 1920×1080, mais espaço para interface e detalhes'),
    ('Apresentação/reunião 16:9', 'Telão ou chamada de vídeo: ritmo mais calmo, leitura longa'),
    ('Vários formatos', 'Master 16:9 + versão 9:16 reenquadrada (não cortada)')], False,
  r'reels?|tiktok|stories|shorts|9:16|vertical|youtube|16:9|horizontal|apresenta|site|landing'),
 ('duracao', 'Duração', 'Quanto tempo de vídeo?', [
    ('30 s (Recommended)', 'Cabe gancho → o que você oferece → prova → marca'),
    ('15–20 s', 'Anúncio rápido: uma ideia, um gancho, um fecho'),
    ('45–60 s', 'Explica mais, exige mais variedade de cenas')], False,
  r'\b\d{1,3} ?(s|seg|segundos)\b|\bmeio minuto\b|\bum minuto\b'),
 ('publico', 'Para quem', 'Quem precisa ser convencido?', [
    ('Quem compra de você (Recommended)', 'Seus clientes: quem consome o produto ou serviço'),
    ('Donos de outros negócios', 'Decisor que contrata o serviço (B2B)'),
    ('Investidor/parceiro', 'Credibilidade, números, visão'),
    ('Público interno', 'Equipe, onboarding, evento')], False,
  r'\bpara (donos?|clientes?|investidor|equipe|empresas?|clinicas?|academias?|lojas?|restaurantes?)\b|\bpublico\b'),
 ('mensagem', 'Mensagem', 'Qual é a UMA frase que a pessoa deve lembrar depois?', [
    ('Proponha 3 opções (Recommended)', 'Eu sugiro três frases no storyboard e você escolhe'),
    ('Eu escrevo', 'Escreva a frase na resposta'),
    ('Use a frase da marca', 'A assinatura que a marca já usa')], False, r'"[^"]{8,}"|“[^”]{8,}”|frase\b'),
 ('material', 'Material', 'Que material você tem? (marque tudo que existe)', [
    ('Logo em vetor (SVG/PDF)', 'Fica nítido em qualquer tamanho'),
    ('Telas do produto/site', 'Prints ou Figma: interface real em vez de redesenhada'),
    ('Fotos/vídeos próprios', 'O local, o produto, a equipe, o cardápio — de verdade'),
    ('Nada, crie tudo', 'Eu desenho o que faltar e uso banco de imagens licenciado')], True, r'\b(svg|figma|prints?|anexo|logo)\b'),
 ('estilo', 'Sensação', 'Que sensação o vídeo deve passar?', [
    ('Premium minimalista (Recommended)', 'Fundo escuro, uma luz, tipografia grande, estilo lançamento Apple'),
    ('Energia alta', 'Cortes rápidos na batida, muitas cenas, cor forte'),
    ('Emocional com pessoas', 'Gente real, gesto, história curta'),
    ('Institucional sóbrio', 'Calmo, claro, confiável')], False, r'apple|minimal|premium|energia|rapid[oa]|emocion|institucional|sobri'),
 ('pessoas', 'Pessoas', 'Pode ter pessoas reais em cena (vídeos de banco licenciados)?', [
    ('Sim, misture com motion (Recommended)', 'Humanos dão escala e emoção; tudo com licença comercial'),
    ('Só motion graphics', 'Sem filmagem, só design animado'),
    ('Só as minhas pessoas', 'Use apenas fotos/vídeos que eu mandar, com autorização')], False, r'pessoas|humanos|gente|atores?|sem pessoas'),
 ('musica', 'Música', 'Que trilha?', [
    ('Eletrônica com drop (Recommended)', 'Subida, respiro e drop no momento principal'),
    ('Atmosférica/garage', 'Mais suave, elegante, ainda com batida'),
    ('Quero ouvir 3 opções', 'Mesma imagem, três trilhas; você escolhe no fim'),
    ('Sem música', 'Só efeitos ou só voz')], False, r'musica|trilha|sem musica|drop'),
 ('voz', 'Voz', 'Vai ter locução?', [
    ('Sem voz, texto na tela (Recommended)', 'Funciona com som desligado no feed'),
    ('Minha voz / locutor meu', 'Você manda o áudio, eu escrevo o roteiro e sincronizo'),
    ('Voz sintética', 'Ferramenta paga (ElevenLabs): mostro o custo antes')], False, r'sem (voz|locucao|narracao)|locucao|narra|voz'),
 ('cta', 'Final', 'O que a pessoa deve fazer no fim?', [
    ('Entrar em contato', 'Botão "Entre em contato" / WhatsApp'),
    ('Visitar o site', 'Endereço do site no fecho'),
    ('Ir até o local', 'Endereço / "abre dia X" no fecho'),
    ('Seguir no Instagram', '@ da marca no fecho')], False, r'\bcta\b|saiba mais|contato|whatsapp|site\b|instagram'),
 ('dados', 'Dados', 'Algum dado precisa aparecer escrito (data, endereço, preço, @, telefone)?', [
    ('Vou mandar agora', 'Escreva os dados na resposta (ex.: "abre 05/12 · Rua X, 120 · @marca")'),
    ('Não precisa', 'Só a marca e a frase')], False, r'\b\d{1,2}/\d{1,2}\b|\brua\b|\bav\.|@\w+|r\$'),
 ('uso', 'Uso', 'Como o vídeo será usado?', [
    ('Post orgânico (Recommended)', 'Feed/Reels da marca'),
    ('Anúncio pago', 'Exige licenças comerciais e música sem Content ID'),
    ('Portfólio/conceito', 'Peça demonstrativa; marca de terceiros só com aviso de não oficial')], False, r'portfolio|conceit|anuncio|ads?\b|pago|organic'),
 ('acabamento', 'Prioridade', 'O que pesa mais?', [
    ('Acabamento máximo (Recommended)', 'Motion blur, Blender onde houver produto/tela física, mais rodadas de crítica'),
    ('Equilíbrio', 'Qualidade alta com render mais leve'),
    ('Rapidez', 'Uma versão boa o quanto antes')], False, r'rapido|urgente|hoje|maxim[ao]|perfeit|extrema qualidade'),
 ('modo', 'Aprovações', 'Como quer acompanhar?', [
    ('Aprovo storyboard e filme (Recommended)', 'Paro em dois pontos para você aprovar'),
    ('Faz tudo e me mostra', 'Eu decido o gosto e entrego uma versão pronta'),
    ('Quero ver cada etapa', 'Paro também na direção visual e na música')], False, r'faz tudo|decide (tudo|por mim)|a direcao e sua|junto|aprovando'),
]
PERMISSAO = ('estimativa', 'Tempo', 'Posso ler as configurações do seu PC (CPU, memória, placa de vídeo) e rodar um teste de render de ~1 minuto para estimar quanto tempo o vídeo leva?', [
    ('Sim, pode ler (Recommended)', 'Leio só o hardware e rodo um render de teste; nada é enviado para fora'),
    ('Não, use valores de referência', 'A estimativa sai genérica e eu aviso isso')], False, None)

def respondidas(pedido, estado=None):
    t = ' ' + norm(pedido) + ' '; r = {qid for qid, *_, rx in Q if rx and re.search(rx, t)}
    if estado:
        r |= set((estado.get('briefing') or {}).keys())
        if estado.get('mode') in ('autonomo', 'hibrido'): r.add('modo')
    return r

def perguntas(pedido, projeto=None):
    st = None
    if projeto and os.path.exists(os.path.join(projeto, 'studio-state.json')): st = json.load(open(os.path.join(projeto, 'studio-state.json'), encoding='utf8'))
    feitas = respondidas(pedido, st)
    autonomo = bool(st and st.get('mode') == 'autonomo') or bool(re.search(r'faz tudo|decide (tudo|por mim)|a direcao e sua', ' ' + norm(pedido) + ' '))
    lista = ([] if autonomo else [q for q in Q if q[0] not in feitas]) + ([PERMISSAO] if 'estimativa' not in feitas else [])   # autônomo: só a permissão
    falta = [dict(id=qid, header=h, question=q, options=[{'label': a, 'description': b} for a, b in ops], multiSelect=m) for qid, h, q, ops, m, rx in lista]
    blocos = [falta[i:i + 4] for i in range(0, len(falta), 4)]
    return {'ja_respondidas': sorted(feitas), 'faltam': len(falta), 'blocos': blocos, 'chamadas': len(blocos), 'nota': 'uma chamada de AskUserQuestion por bloco; adapte o TEXTO das opções ao negócio (cafeteria, clínica, app…) mantendo os ids'}

def texto(r):
    if not r['faltam']: return 'O pedido já responde tudo o que muda o filme. Siga para o combinado.'
    L = [f"Para fazer o melhor vídeo possível, preciso de {r['faltam']} respostas (marque a opção ou escreva a sua; as recomendadas vêm primeiro):"]
    n = 1
    for b in r['blocos']:
        for q in b:
            L.append(f"{n}. {q['question']}" + (' (pode marcar várias)' if q['multiSelect'] else ''))
            L += [f"   {chr(97 + i)}) {o['label'].replace('(Recommended)', '(recomendada)')} — {o['description']}" for i, o in enumerate(q['options'])]; n += 1
    L.append('Responda tudo numa mensagem (ex.: "1a, 2b, 3: donos de academia, 5a+b…"). O que você deixar em branco eu decido pela recomendada e aviso.')
    return '\n'.join(L)

def registrar(projeto, respostas):
    p = os.path.join(projeto, 'studio-state.json'); st = json.load(open(p, encoding='utf8')) if os.path.exists(p) else {}
    b = st.setdefault('briefing', {}); hoje = datetime.date.today().isoformat()
    for k, v in respostas.items(): b[k] = {'resposta': v, 'data': hoje}
    os.makedirs(projeto, exist_ok=True); json.dump(st, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1); return b

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['perguntas', 'registrar', 'resumo']); ap.add_argument('a', nargs='?'); ap.add_argument('b', nargs='?')
    ap.add_argument('--projeto'); ap.add_argument('--json', action='store_true'); a = ap.parse_args()
    if a.cmd == 'perguntas':
        r = perguntas(a.a or '', a.projeto); print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else texto(r)); return
    if a.cmd == 'registrar':
        b = registrar(a.a, json.loads(a.b)); print(f'briefing gravado: {", ".join(sorted(b))}'); return
    st = json.load(open(os.path.join(a.a, 'studio-state.json'), encoding='utf8')); b = st.get('briefing', {})
    for qid, h, q, *_ in Q:
        if qid in b: print(f'- {h}: {b[qid]["resposta"]}')
    faltam = [h for qid, h, *_ in Q if qid not in b]
    if faltam: print('Não respondidas (decido pela recomendada e aviso): ' + ', '.join(faltam))

if __name__ == '__main__': main()
