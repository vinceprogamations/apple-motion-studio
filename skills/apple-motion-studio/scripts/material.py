# Confere se o material que o usuário mandou aguenta o filme ANTES de animar, e diz em linguagem comum o que pedir.
# (Lição de um filme real: logo de ~300 px ficou mole no fecho; teria bastado pedir o vetor no briefing.)
#   python material.py checar <arquivo…> [--alvo 1080|1440|4k] [--papel auto|logo|foto|tela|video|fonte|audio] [--json]
# Regra de tamanho: o maior tamanho em que o item aparece na tela × 1,25 (folga para o push de câmera).
#   logo: símbolo ~35% da altura, wordmark ~45% da largura no fecho · foto/tela: tela cheia · vídeo: resolução e fps do master.
import os, sys, json, argparse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
ALVO = {'1080': (1920, 1080), '1440': (2560, 1440), '4k': (3840, 2160)}
VETOR = {'.svg', '.pdf', '.ai', '.eps'}; IMG = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff'}
VID = {'.mp4', '.mov', '.webm', '.mkv', '.m4v'}; AUD = {'.wav', '.mp3', '.aif', '.aiff', '.flac', '.m4a', '.ogg'}; FON = {'.ttf', '.otf', '.woff', '.woff2'}
FOLGA = 1.25

def papel_auto(path):
    n = os.path.basename(path).lower(); e = os.path.splitext(n)[1]
    if e in VID: return 'video'
    if e in AUD: return 'audio'
    if e in FON: return 'fonte'
    if any(k in n for k in ('logo', 'marca', 'simbolo', 'símbolo', 'wordmark', 'icone', 'icon')): return 'logo'
    if any(k in n for k in ('tela', 'screen', 'print', 'captura', 'ui', 'app')): return 'tela'
    return 'foto'

def probe(path):
    from lib.tools import find_tool
    fp = find_tool('ffprobe', required=False)
    if not fp: return {}
    r = subprocess.run([fp, '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,sample_rate,channels', '-show_entries', 'format=duration', '-of', 'json', path], capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: return {}

RESTRITO = ('terceiros', 'nao comercial', 'não comercial', 'portfolio', 'portfólio', 'uso pessoal', 'restricted', 'sem uso comercial', 'nc')
def licenca(path):
    """Procura o arquivo num asset-manifest.json da pasta dele ou de até duas acima; devolve (licença, restrita?)."""
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(3):
        m = os.path.join(d, 'asset-manifest.json')
        if os.path.exists(m):
            try: assets = json.load(open(m, encoding='utf8')).get('assets', [])
            except Exception: assets = []
            for x in assets:
                f = x.get('file') or x.get('path') or ''
                if f and os.path.normcase(os.path.abspath(os.path.join(d, f))) == os.path.normcase(os.path.abspath(path)):
                    lic = x.get('license', '') or ''; low = ' ' + lic.lower().replace(',', ' ').replace(';', ' ') + ' '
                    return lic, any((' ' + k + ' ') in low if k == 'nc' else k in low for k in RESTRITO)
        d = os.path.dirname(d)
    return '', False

def checar(path, alvo='1080', papel='auto'):
    r = _checar(path, alvo, papel)
    lic, restrita = licenca(path) if os.path.exists(path) else ('', False)
    if restrita:
        r['nivel'] = 'restrito'; r['detalhe'] += f' · LICENÇA RESTRITA: {lic}'
        r['pedir'] = 'o arquivo próprio da marca deste filme (este está liberado só para outro uso)'
    return r

def _checar(path, alvo='1080', papel='auto'):
    W, H = ALVO[alvo]; e = os.path.splitext(path)[1].lower(); p = papel_auto(path) if papel == 'auto' else papel
    r = {'arquivo': path, 'papel': p, 'nivel': 'ok', 'detalhe': '', 'pedir': ''}
    if not os.path.exists(path): return {**r, 'nivel': 'falta', 'detalhe': 'arquivo não encontrado'}
    if e in VETOR: return {**r, 'detalhe': 'vetor: nítido em qualquer resolução'}
    if p == 'fonte': return {**r, 'detalhe': 'fonte instalável; confira a licença de uso em vídeo'}
    if p == 'audio':
        a = next((s for s in probe(path).get('streams', []) if s.get('codec_type') == 'audio'), {})
        sr = int(a.get('sample_rate', 0) or 0)
        if e == '.mp3' or sr and sr < 44100: return {**r, 'nivel': 'fraco', 'detalhe': f'{e[1:]} {sr or "?"} Hz', 'pedir': 'o WAV original (48 kHz) se existir'}
        return {**r, 'detalhe': f'{sr} Hz, {a.get("channels", "?")} canal(is)'}
    if p == 'video':
        v = next((s for s in probe(path).get('streams', []) if s.get('codec_type') == 'video'), {})
        w, h = int(v.get('width', 0) or 0), int(v.get('height', 0) or 0); fr = v.get('r_frame_rate', '0/1'); n, d = (fr.split('/') + ['1'])[:2]
        fps = float(n) / float(d or 1) if float(d or 1) else 0
        r['detalhe'] = f'{w}×{h} @ {fps:.2f} fps'
        if max(w, h) < max(W, H) * 0.99: return {**r, 'nivel': 'insuficiente', 'pedir': f'versão em {W}×{H} ou maior (o filme sai em {alvo})'}
        return r
    if e not in IMG: return {**r, 'nivel': 'fraco', 'detalhe': f'formato {e or "?"} não conferido'}
    from PIL import Image
    im = Image.open(path); w, h = im.size; alpha = im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info
    if p == 'logo' and w < 2 * h: need, eixo, lado = int(H * 0.35 * FOLGA), 'altura', h      # símbolo: ~35% da altura no fecho
    else: need, eixo, lado = int((W * 0.45 if p == 'logo' else W) * FOLGA), 'largura', w     # wordmark ~45% da largura; foto/tela = tela cheia
    r['detalhe'] = f'{w}×{h} px' + (' · fundo transparente' if alpha else '') + f' · precisa ~{need} px de {eixo} em {alvo}'
    falta = lado < need
    if p == 'logo':
        pedidos = []
        if falta: pedidos.append('o logo em SVG/PDF (vetor) do kit de marca')
        if not alpha: pedidos.append('versão com fundo transparente')
        if pedidos: return {**r, 'nivel': 'insuficiente' if lado < need * 0.6 else 'fraco', 'pedir': ' ou '.join(pedidos)}
        return r
    if falta: return {**r, 'nivel': 'insuficiente' if lado < need * 0.6 else 'fraco', 'pedir': ('captura da tela em resolução maior (ou o arquivo do Figma)' if p == 'tela' else 'a foto original, sem compressão de WhatsApp/redes')}
    return r

ICONE = {'ok': 'ok  ', 'fraco': 'FRACO', 'insuficiente': 'BAIXO', 'falta': 'FALTA', 'restrito': 'LICEN'}
def texto(rows, alvo):
    L = [f'Material para um filme em {alvo}:']
    for x in rows: L.append(f"  {ICONE[x['nivel']]} {os.path.basename(x['arquivo'])} ({x['papel']}) — {x['detalhe']}" + (f"\n        → peça: {x['pedir']}" if x['pedir'] else ''))
    ruins = [x for x in rows if x['nivel'] in ('fraco', 'insuficiente', 'falta')]; lic = [x for x in rows if x['nivel'] == 'restrito']
    if lic: L.append(f"\n{len(lic)} item(ns) têm licença que NÃO cobre este filme: não use sem o arquivo próprio ou uma autorização registrada.")
    L.append('\nTudo pronto para a resolução do filme.' if not ruins and not lic else '' if not ruins else
             f"\n{len(ruins)} item(ns) vão aparecer moles ou serrilhados. Dá para seguir com eles (eu aviso na entrega), mas o resultado melhora muito com o que está em \"peça\".")
    return '\n'.join(L)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['checar']); ap.add_argument('arquivos', nargs='+')
    ap.add_argument('--alvo', default='1080', choices=list(ALVO)); ap.add_argument('--papel', default='auto'); ap.add_argument('--json', action='store_true'); a = ap.parse_args()
    rows = [checar(f, a.alvo, a.papel) for f in a.arquivos]
    print(json.dumps(rows, ensure_ascii=False, indent=1) if a.json else texto(rows, a.alvo))
    sys.exit(0 if all(x['nivel'] == 'ok' for x in rows) else 2)

if __name__ == '__main__': main()
