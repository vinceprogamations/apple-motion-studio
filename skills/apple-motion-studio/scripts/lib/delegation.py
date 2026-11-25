"""Delegation state of a film project: who decides each stage, and what the agent may do without asking.

The user's own words define the scope. Three modes:
  autonomo  "faça tudo / decide tudo / a direção é sua": the agent decides every stage, reviews the storyboard internally,
            produces and delivers one main version. Asking about a delegated taste choice is a failure of autonomy.
  hibrido   part delegated, part reserved ("faça tudo, mas quero escolher a música"; "o storyboard já está aprovado, cuide
            do som"): only the reserved stage goes to the user; everything independent keeps moving.
  guiado    nothing delegated: stop at the agreed checkpoints (storyboard, master).
Status of a decision (one field, three meanings that must never be mixed):
  delegado-agente   chosen by the agent under the user's delegation (words + scope recorded)
  aprovado-usuario  approved by the user in person
  exige-terceiro / aprovado-terceiro   an approval that belongs to someone else (client, legal, brand owner)
  aguardando-usuario   reserved stage, waiting for the one question
State file: <project>/studio-state.json (resumable by a new session: master, approvals, next operation)."""
import json, os, re, datetime, hashlib, unicodedata

STAGES = ['brief', 'storyboard', 'direcao-visual', 'paleta-sonora', 'musica', 'foley', 'locucao', 'mix', 'assets', 'master']
SOUND = ['paleta-sonora', 'musica', 'foley', 'locucao', 'mix']
CHECKPOINTS_GUIADO = ['storyboard', 'master']
ALIASES = {'musica': 'musica', 'trilha': 'musica', 'som': 'paleta-sonora', 'storyboard': 'storyboard', 'roteiro': 'storyboard',
           'locucao': 'locucao', 'voz': 'locucao', 'narracao': 'locucao', 'logo': 'direcao-visual', 'paleta': 'direcao-visual',
           'cor': 'direcao-visual', 'cores': 'direcao-visual', 'visual': 'direcao-visual', 'mix': 'mix', 'mixagem': 'mix', 'final': 'master', 'master': 'master'}

def _norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')

def classify(words):
    """Turn the user's request into a delegation scope. Returns a dict; never asks anything."""
    t = _norm(words); res = {'words': words, 'mode': 'guiado', 'delegated': [], 'reserved': [], 'approved': [], 'constraints': {}, 'requires': []}
    all_ = re.search(r'\b(fa[cz]a?|faz) tudo\b|\bdecid[ea]? (tudo|por mim)\b|\bpode decidir\b|\bvoce decide\b|\ba direcao e sua\b|\bdecide tudo\b', t)
    if all_: res['delegated'] = list(STAGES)
    if re.search(r'cuid[ae] (de )?(todo )?(o )?som|som (fica )?com voce|faca o som|sonoriz', t):
        res['delegated'] = sorted(set(res['delegated']) | set(SOUND), key=STAGES.index)
    for m in re.finditer(r'\bstoryboard (ja )?(esta |foi )?aprovad', t): res['approved'].append('storyboard')
    for m in re.finditer(r'quero (escolher|aprovar|decidir|ver|ouvir) (so |somente |apenas |eu )?(a |o |as |os )?(\w+)', t):
        st = ALIASES.get(m.group(4))
        if st: res['reserved'].append(st)
    if re.search(r'\bsem (locucao|voz|narracao|narrador)\b', t): res['constraints']['voz'] = False
    if re.search(r'\bsem musica\b', t): res['constraints']['musica'] = False
    if re.search(r'assinatura sonora', t): res['requires'].append({'id': 'assinatura-sonora', 'what': 'assinatura sonora oficial da marca', 'owner': 'marca'})
    m = re.search(r'(verba|orcamento) (de )?(r\$ ?)?(\d+)', t); res['constraints']['verba'] = float(m.group(4)) if m else 0.0   # no budget stated = zero extra cost
    res['delegated'] = [s for s in res['delegated'] if s not in res['reserved'] and s not in res['approved']]
    res['reserved'] = sorted(set(res['reserved']), key=STAGES.index); res['approved'] = sorted(set(res['approved']), key=STAGES.index)
    if res['delegated'] and not res['reserved'] and set(res['delegated']) | set(res['approved']) >= set(STAGES): res['mode'] = 'autonomo'
    elif res['delegated']: res['mode'] = 'hibrido'
    return res

def path(proj): return os.path.join(proj, 'studio-state.json')
def load(proj):
    with open(path(proj), encoding='utf8') as f: return json.load(f)
def save(proj, st):
    st['updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    with open(path(proj), 'w', encoding='utf8') as f: json.dump(st, f, ensure_ascii=False, indent=1)

def init(proj, words):
    os.makedirs(proj, exist_ok=True); c = classify(words); now = datetime.date.today().isoformat()
    st = {'version': 1, 'mode': c['mode'], 'words': words, 'constraints': c['constraints'], 'requires': c['requires'], 'decisions': {}, 'master': None, 'next': None, 'history': []}
    for s in c['delegated']: st['decisions'][s] = {'status': 'delegado-agente', 'scope': f'delegado pelas palavras do usuário: "{words}"', 'date': now}
    for s in c['approved']: st['decisions'][s] = {'status': 'aprovado-usuario', 'by': 'usuario', 'scope': f'declarado no pedido: "{words}"', 'date': now}
    for s in c['reserved']: st['decisions'][s] = {'status': 'aguardando-usuario', 'scope': f'reservado pelo usuário: "{words}"', 'date': now}
    if c['mode'] == 'guiado':
        for s in CHECKPOINTS_GUIADO: st['decisions'].setdefault(s, {'status': 'aguardando-usuario', 'scope': 'modo guiado: checkpoint acordado', 'date': now})
    save(proj, st); return st

def gate(st, stage):
    """('seguir', why) when the agent may decide/advance this stage; ('perguntar', question) for the ONE question that is the
    user's (or a third party's) to answer; ('previa', why) for a master that still lacks a mandatory asset."""
    d = st['decisions'].get(stage)
    if stage == 'master':
        missing = [r for r in st.get('requires', []) if not r.get('present')]
        if missing: return 'previa', 'falta asset obrigatório: ' + ', '.join(r['what'] for r in missing) + ' — entregar como PRÉVIA e pedir só esse arquivo'
    if stage == 'locucao' and st['constraints'].get('voz') is False: return 'seguir', 'sem locução (requisito do usuário): a promessa chega por imagem, texto e som'
    if d is None:
        if st['mode'] == 'guiado' and stage in CHECKPOINTS_GUIADO: return 'perguntar', f'aprovar {stage}?'
        return 'seguir', 'etapa técnica / não reservada'
    s = d['status']
    if s in ('delegado-agente', 'aprovado-usuario', 'aprovado-terceiro'): return 'seguir', s
    if s == 'exige-terceiro': return 'perguntar', f'aprovação de {d.get("who", "terceiro")} para {stage}'
    return 'perguntar', f'{stage}: apresente a recomendação e uma alternativa (mesmo trecho, loudness comparável) e peça a escolha'

def decide(st, stage, choice, why):
    verdict, msg = gate(st, stage)
    if verdict == 'perguntar': return False, msg
    d = st['decisions'].setdefault(stage, {'status': 'delegado-agente' if st['mode'] != 'guiado' else 'aprovado-usuario', 'scope': 'etapa técnica'})
    d.update({'choice': choice, 'why': why, 'date': datetime.date.today().isoformat()})
    st['history'].append({'stage': stage, 'choice': choice, 'status': d['status'], 'when': datetime.datetime.now().isoformat(timespec='seconds')}); return True, d['status']

def approve(st, stage, choice, by='usuario'):
    third = by.startswith('terceiro')
    d = st['decisions'].setdefault(stage, {}); d.update({'status': 'aprovado-terceiro' if third else 'aprovado-usuario', 'by': by, 'choice': choice, 'date': datetime.date.today().isoformat()})
    st['history'].append({'stage': stage, 'choice': choice, 'status': d['status'], 'when': datetime.datetime.now().isoformat(timespec='seconds')})

def require_third(st, stage, who): st['decisions'][stage] = {'status': 'exige-terceiro', 'who': who, 'date': datetime.date.today().isoformat()}

def set_master(st, mp4, kind='master'):
    st['master'] = {'path': mp4, 'sha256': hashlib.sha256(open(mp4, 'rb').read()).hexdigest(), 'kind': kind, 'date': datetime.datetime.now().isoformat(timespec='seconds')}

def summary(st):
    out = [f"modo: {st['mode']}  ·  pedido: \"{st['words']}\""]
    if st['constraints']: out.append('restrições: ' + ', '.join(f'{k}={v}' for k, v in st['constraints'].items()))
    for s in STAGES:
        d = st['decisions'].get(s)
        if d: out.append(f"  {s:15s} {d['status']:19s} {d.get('choice', '')}")
    pend = [s for s in STAGES if gate(st, s)[0] == 'perguntar']
    out.append('perguntas pendentes: ' + (', '.join(f'{s} ({gate(st, s)[1]})' for s in pend) if pend else 'nenhuma'))
    mv, mm = gate(st, 'master'); out.append(f"master: {st['master']['path'] + ' (' + st['master']['kind'] + ')' if st['master'] else 'ainda não'}" + (f'  ·  {mm}' if mv == 'previa' else ''))
    out.append('próxima operação: ' + (st.get('next') or '—')); return '\n'.join(out)
