# O que a skill vai instalar, baixar, gastar ou fazer no navegador — dito ao usuário ANTES, em linguagem comum.
#   python ambiente.py plano [--perfil core,3d,extra|tudo] [--json]       # o que falta, tamanho, origem, comando; não instala nada
#   python ambiente.py instalar <id…|faltando> --sim "<palavras do usuário>" [--perfil …]   # instala só com o sim registrado
#   python ambiente.py mcp <nome-de-ferramenta…>                          # classifica as ferramentas conectadas: grátis / pago / freemium
#   python ambiente.py aviso [--perfil …] [--mcp <nomes…>] [--site <id>…]  # o bloco único de avisos para mostrar ao usuário
# Regras: nada é instalado sem "--sim" com as palavras do usuário (gravadas em .local/consentimentos.json); serviços pagos
# nunca são usados sem pedido explícito e estimativa; o navegador baixa um arquivo por vez, de site com licença clara.
import os, sys, json, shutil, subprocess, platform, datetime, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); sys.path.insert(0, HERE)
from lib.tools import find_tool
from lib.venv import venv_python
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
OS = {'Windows': 'win', 'Darwin': 'mac'}.get(platform.system(), 'linux')
REG = json.load(open(os.path.join(SKILL, 'references', 'ferramentas.json'), encoding='utf8'))
CONSENT = os.path.join(SKILL, '.local', 'consentimentos.json')

def presente(p):
    if p['id'] == 'node':
        n = shutil.which('node')
        if not n: return None
        v = subprocess.run([n, '--version'], capture_output=True, text=True).stdout.strip()
        return f'{n} {v}' if v and int(v.lstrip('v').split('.')[0]) >= 18 else None
    if p['id'] == 'ffmpeg': a, b = find_tool('ffmpeg', False), find_tool('ffprobe', False); return a if a and b else None
    if p['id'] in ('chrome', 'blender'): return find_tool(p['id'], False)
    if p['id'] == 'py-audio':
        py = venv_python() or sys.executable
        r = subprocess.run([py, '-c', 'import cv2, pyloudnorm'], capture_output=True); return py if r.returncode == 0 else None
    return None

def perfis(arg):
    if not arg or arg == 'core': return {'core'}
    return {'core', '3d', 'extra'} if arg == 'tudo' else {'core', *arg.split(',')}

def plano(perfil=None):
    rows = []
    for p in REG['programas']:
        if p['perfil'] not in perfis(perfil): continue
        hit = presente(p); cmd = ('pip install -r ' + p['pip']) if p.get('pip') else p.get(OS, '')
        rows.append({**p, 'ok': bool(hit), 'onde': hit or '', 'comando': cmd})
    return rows

def texto_plano(rows):
    falta = [r for r in rows if not r['ok']]; L = []
    for r in rows:
        L.append(f"  {'ok ' if r['ok'] else 'FALTA'}  {r['nome']} — {r['por_que']}" + (f"  ({r['onde']})" if r['ok'] else f"  · ~{r['mb']} MB · {r['custo']} · {r['fonte']}"))
    if falta:
        L.append(f"\nPara instalar ({sum(r['mb'] for r in falta)} MB no total, tudo grátis), com o seu sim eu rodo:")
        L += [f"  {r['comando']}" for r in falta]
        if OS == 'win' and any(not r.get('pip') for r in falta): L.append('  (o winget aceita os termos de uso de cada pacote; o seu sim cobre esse aceite. Pode pedir confirmação do Windows.)')
    else: L.append('\nNada a instalar.')
    return '\n'.join(L)

def registrar(itens, palavras):
    os.makedirs(os.path.dirname(CONSENT), exist_ok=True)
    log = json.load(open(CONSENT, encoding='utf8')) if os.path.exists(CONSENT) else []
    log.append({'quando': datetime.datetime.now().isoformat(timespec='seconds'), 'o_que': itens, 'palavras_do_usuario': palavras})
    json.dump(log, open(CONSENT, 'w', encoding='utf8'), ensure_ascii=False, indent=1)

def instalar(ids, sim, perfil, dry=False):
    rows = plano(perfil if perfil else ('tudo' if any(i not in ('faltando',) for i in ids) else None))
    alvo = [r for r in rows if not r['ok'] and ('faltando' in ids or r['id'] in ids)]
    if not alvo: print('Nada a instalar: já está tudo aqui.'); return 0
    if not sim:
        print('Ainda não instalei nada. Mostre isto ao usuário e espere o sim:\n' + texto_plano(alvo)); return 3
    registrar([r['id'] for r in alvo], sim); rc = 0
    for r in alvo:
        if r.get('pip'):
            py = venv_python()
            if not py: print('  rode antes: python scripts/setup.py'); rc = 1; continue
            cmd = [py, '-m', 'pip', 'install', '-q', '-r', os.path.join(SKILL, r['pip'])]
        else:
            if not r['comando']: print(f"  {r['nome']}: sem comando para este sistema — {r['fonte']}"); rc = 1; continue
            if OS == 'win' and not shutil.which('winget'): print(f"  winget ausente: instale {r['nome']} por {r['fonte']}"); rc = 1; continue
            if r['comando'].startswith('sudo'): print(f"  {r['nome']}: precisa de senha de administrador — rode você mesmo: {r['comando']}"); rc = 1; continue
            cmd = r['comando'].split()
        print(f"  instalando {r['nome']} (~{r['mb']} MB)…")
        if dry: print('   (ensaio) ' + ' '.join(cmd)); continue
        res = subprocess.run(cmd); print(f"   {'ok' if res.returncode == 0 else 'falhou (código ' + str(res.returncode) + ')'}"); rc = rc or res.returncode
    if not dry: print('\nAbra um terminal novo (ou rode python scripts/setup.py) para o PATH valer.')
    return rc

def mcp(nomes):
    """Agrupa as ferramentas por servidor (mcp__<servidor>__<ferramenta>) e classifica o servidor inteiro pelo registro."""
    grupos = {}
    for n in nomes:
        srv = n.split('__')[1] if n.startswith('mcp__') and n.count('__') >= 2 else n
        grupos.setdefault(srv, []).append(n.lower())
    vistos = {}; desconhecidos = []
    for srv, tools in grupos.items():
        hit = next((s for s in REG['servicos'] if any(p in srv.lower() or any(p in t for t in tools) for p in s['padroes'])), None)
        if hit: vistos.setdefault(hit['id'], hit)
        else: desconhecidos.append(srv)
    return list(vistos.values()), sorted(set(desconhecidos))

def texto_mcp(servs, desc):
    if not servs and not desc: return 'Nenhuma ferramenta conectada que cobre: o filme sai 100% pelo caminho gratuito local.'
    L = []
    for c in ('pago', 'freemium', 'grátis'):
        for s in [s for s in servs if s['custo'] == c]:
            custo = '' if s['cobra'] == '—' else f" — {s['cobra']}"
            L.append(f"  [{c.upper()}] {s['nome']}{custo}. Uso: {s['quando']}. {s['aviso'][0].upper() + s['aviso'][1:]}.")
    if desc: L.append(f"  [?] {len(desc)} conector(es) que não conheço ({', '.join(desc[:6])}{'…' if len(desc) > 6 else ''}): trato como pagos até você dizer o contrário.")
    pagos = [s for s in servs if s['custo'] != 'grátis']
    if pagos: L.append('  Nada pago é usado sem você pedir; antes eu mostro a estimativa da própria ferramenta. Sem verba dita = R$ 0.')
    return '\n'.join(L)

def texto_sites(ids):
    sites = [s for s in REG['sites'] if s['id'] in ids]
    if not sites: return ''
    L = ['Vou usar o navegador (abro uma aba nova; você vê tudo e pode parar a qualquer hora):']
    L += [f"  - {s['nome']}: {s['licenca']}. Como: {s['regra']}." for s in sites]
    L.append('  Cada download eu confirmo com você (nome do arquivo e site). Nunca digito senha, resolvo CAPTCHA ou compro nada: login é com você.')
    return '\n'.join(L)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['plano', 'instalar', 'mcp', 'aviso']); ap.add_argument('itens', nargs='*')
    ap.add_argument('--perfil'); ap.add_argument('--sim'); ap.add_argument('--json', action='store_true'); ap.add_argument('--ensaio', action='store_true')
    ap.add_argument('--mcp', nargs='*', default=[]); ap.add_argument('--site', nargs='*', default=[]); a = ap.parse_args()
    if a.cmd == 'plano':
        rows = plano(a.perfil); print(json.dumps(rows, ensure_ascii=False, indent=1) if a.json else texto_plano(rows))
        sys.exit(0 if all(r['ok'] for r in rows) else 2)
    if a.cmd == 'instalar': sys.exit(instalar(a.itens or ['faltando'], a.sim, a.perfil, a.ensaio))
    if a.cmd == 'mcp':
        s, d = mcp(a.itens + a.mcp); print(json.dumps({'servicos': s, 'desconhecidos': d}, ensure_ascii=False, indent=1) if a.json else texto_mcp(s, d)); return
    rows = plano(a.perfil); s, d = mcp(a.mcp)
    blocos = ['**No seu computador**\n' + texto_plano(rows), '**Ferramentas conectadas e custo**\n' + texto_mcp(s, d)]
    if a.site: blocos.append('**Navegador**\n' + texto_sites(a.site))
    print('\n\n'.join(blocos))

if __name__ == '__main__': main()
