# Registro de trilhas já usadas: nenhum filme repete a música de outro (nem como alternativa oferecida ao usuário).
#   python trilhas.py livre <arquivo> [--registro audio-library/USADAS.json]      # exit 0 livre · 3 já usada (diz onde)
#   python trilhas.py usar <arquivo> "<filme>" [--registro ...]                     # grava ao promover o master (e ao oferecer A/B/C)
#   python trilhas.py listar [--registro ...]
# O registro padrão é audio-library/USADAS.json a partir da pasta atual (ou da variável STUDIO_USADAS). music_pick.py o lê sozinho.
import sys, os, json, argparse
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass

def caminho(p=None):
    return p or os.environ.get('STUDIO_USADAS') or os.path.join(os.getcwd(), 'audio-library', 'USADAS.json')
def carregar(p=None):
    p = caminho(p)
    if not os.path.exists(p): return {'regra': 'nenhum vídeo repete a música de outro', 'faixas': []}
    return json.load(open(p, encoding='utf8'))
def chave(arq): return os.path.splitext(os.path.basename(arq))[0].lower()
def usada(arq, reg=None):
    """[filmes] em que a faixa já apareceu (casa pelo nome do arquivo, com ou sem extensão, ou por prefixo registrado)."""
    k = chave(arq)
    for f in (reg or carregar())['faixas']:
        a = f['arquivo'].lower()
        if k == a or k.startswith(a) or a.startswith(k): return f['filmes']
    return []

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['livre', 'usar', 'listar']); ap.add_argument('arquivo', nargs='?'); ap.add_argument('filme', nargs='?')
    ap.add_argument('--registro'); a = ap.parse_args(); p = caminho(a.registro); reg = carregar(p)
    if a.cmd == 'listar':
        for f in reg['faixas']: print(f"{f['arquivo']}  →  {', '.join(f['filmes'])}")
        return
    if a.cmd == 'livre':
        u = usada(a.arquivo, reg)
        if u: print(f'JÁ USADA em: {", ".join(u)} — escolha outra faixa'); sys.exit(3)
        print('livre: nenhum filme usou esta faixa'); return
    if not a.filme: sys.exit('usar: informe o filme')
    k = chave(a.arquivo)
    for f in reg['faixas']:
        if f['arquivo'].lower() == k:
            if a.filme not in f['filmes']: f['filmes'].append(a.filme)
            break
    else: reg['faixas'].append({'arquivo': k, 'filmes': [a.filme]})
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(reg, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1); print(f'registrada: {k} → {a.filme}')

if __name__ == '__main__': main()
