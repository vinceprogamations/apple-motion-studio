# Acervo de referências do estúdio: modelos 3D grátis (CC0/CC-BY), HDRIs de estúdio, materiais PBR e telas reais de apps
# (só como referência de layout). Os filmes ficam melhores com ele: produto e cenário fotorrealistas sem modelar do zero,
# luz de estúdio pronta e telas de app fiéis. Guia completo: references/acervo.md.
#
#   python acervo.py status   [--dir <pasta>]      # o que já existe; exit 0 completo · 3 falta algo (pergunte ao usuário)
#   python acervo.py pergunta [--dir <pasta>]      # a pergunta pronta para o usuário (com tamanho e licenças)
#   python acervo.py baixar   [--dir <pasta>] --sim "<palavras do usuário ou do pedido 'faça tudo'>" [--partes polyhaven,hdris,materiais,telas]
#   python acervo.py chrome                        # itens que só saem pelo navegador (Sketchfab com login, molduras e UI Kit da Apple)
# Pasta padrão: <projeto>/referencias/recursos-3d-e-telas (o projeto é a pasta atual ou a raiz git dela).
import argparse, datetime, hashlib, json, os, subprocess, sys, time, urllib.request, zipfile

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass

UA = {'User-Agent': 'Mozilla/5.0 (apple-motion-studio; downloads individuais)'}
POLYHAVEN = ['BarberShopChair_01', 'potted_plant_01', 'potted_plant_02', 'potted_plant_04', 'ceramic_vase_01', 'ceramic_vase_03',
             'modern_arm_chair_01', 'mid_century_lounge_chair', 'Sofa_01', 'modern_coffee_table_01', 'side_table_01',
             'modern_ceiling_lamp_01', 'hanging_industrial_lamp', 'croissant', 'carrot_cake', 'tea_set_01', 'wooden_bowl_01',
             'decorative_book_set_01', 'alarm_clock_01', 'Camera_01', 'fancy_picture_frame_01']
HDRIS = ['brown_photostudio_02', 'studio_small_09', 'studio_small_08', 'photo_studio_loft_hall']
MATERIAIS = ['Wood049', 'Marble012', 'Concrete034', 'Fabric048', 'Leather037', 'Terrazzo009', 'Plaster001']
APPS = {'instagram': 389801252, 'whatsapp': 310633997, 'google-maps': 585027354, 'google-agenda': 909319292, 'gmail': 422689480,
        'ifood': 483017239, 'nubank': 814456780, 'spotify': 324684580, 'apple-calendario': 1108185179, 'mercado-pago': 925436649,
        'uber': 368677368}
CHROME = [  # Sketchfab exige login: baixar pelo navegador do usuário, um por vez, formato glTF; todos CC-BY 4.0 (creditar)
    ('iPhone 16 Pro Max White', 'Sketcher (@jnanbr07)', 'https://sketchfab.com/3d-models/iphone-16-pro-max-white-a6e53194519448e4885cecfa162dbfcb'),
    ('Apple MacBook Pro 2020', 'CGDELUXE', 'https://sketchfab.com/3d-models/apple-macbook-pro-2020-dfad155b993b45b593054f8970bd6d70'),
    ('iPad Pro 13in silver M4', 'polyman Studio (@Polyman_3D)', 'https://sketchfab.com/3d-models/ipad-pro-13in-silver-m4-8a113340443e49d3b905ab9f0b45efd6'),
    ('AirPods Pro', 'Jed Falcone (@jedlas012)', 'https://sketchfab.com/3d-models/airpods-pro-3f84ddc3d87a4ec0a5e5f379abfecd9c'),
    ('APPLE Watch', 'dope render (@akabhi006)', 'https://sketchfab.com/3d-models/apple-watch-7c9d6b8c97fb4a93a474b8f50cbb2fca')]
EXTRAS = [  # oficiais da Apple: licença própria para mockups; .dmg precisa do 7-Zip no Windows; UI Kit precisa de conta no Figma
    ('Molduras iPhone 16 (PNG/PSD)', 'https://devimages-cdn.apple.com/design/resources/download/Bezel-iPhone-16.dmg'),
    ('Molduras MacBook Pro M5', 'https://devimages-cdn.apple.com/design/resources/download/Bezel-MacBook-Pro-M5.dmg'),
    ('UI Kit iOS/iPadOS (Figma)', 'https://developer.apple.com/design/resources/')]
PARTES = {'polyhaven': ('modelos-3d/polyhaven', len(POLYHAVEN), '~300 MB'), 'hdris': ('hdris', len(HDRIS), '~95 MB'),
          'materiais': ('materiais/ambientcg', len(MATERIAIS), '~130 MB'), 'telas': ('telas-padrao/app-store', len(APPS), '~90 MB')}

def raiz():
    try: return subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return os.getcwd()

def pasta(a): return os.path.abspath(a.dir or os.path.join(raiz(), 'referencias', 'recursos-3d-e-telas'))

def contar(d, sub):
    p = os.path.join(d, sub)
    if not os.path.isdir(p): return 0
    return len([x for x in os.listdir(p) if not x.startswith('.') and not x.endswith('.json')])

def status(d):
    falta = []
    print(f'acervo em {d}')
    for k, (sub, alvo, tam) in PARTES.items():
        n = contar(d, sub); ok = n >= alvo
        print(f'  {"ok   " if ok else "FALTA"} {k:10s} {n}/{alvo}  ({tam}, {sub})')
        if not ok: falta.append(k)
    n = contar(d, 'modelos-3d/sketchfab'); print(f'  {"ok   " if n >= len(CHROME) else "falta"} aparelhos  {n}/{len(CHROME)}  (Sketchfab pelo Chrome, CC-BY)')
    return falta

def pergunta(falta):
    mb = sum(int(PARTES[k][2].strip('~ MB')) for k in falta)
    tam = f'cerca de {mb} MB' if mb < 1000 else f'cerca de {mb / 1000:.1f} GB'
    return ('Para os vídeos ficarem melhores, vale ter um acervo de referências: modelos 3D fotorrealistas grátis (plantas, móveis, '
            'aparelhos), iluminação de estúdio, materiais e telas reais de apps como Instagram e WhatsApp (só para eu copiar o layout). '
            f'São downloads grátis e com licença livre ({tam}, mais os aparelhos pelo Sketchfab). '
            'Posso acessar o Chrome e baixar tudo?')

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r: return r.read()

def salvar(url, path, md5=None):
    if os.path.exists(path) and (md5 is None or hashlib.md5(open(path, 'rb').read()).hexdigest() == md5): return
    os.makedirs(os.path.dirname(path), exist_ok=True); b = get(url)
    if md5 and hashlib.md5(b).hexdigest() != md5: raise RuntimeError('md5 não confere: ' + url)
    open(path, 'wb').write(b); time.sleep(0.4)

def baixar(d, partes, reg):
    if 'polyhaven' in partes:
        for mid in POLYHAVEN:
            fs = json.loads(get(f'https://api.polyhaven.com/files/{mid}'))
            f = fs['gltf']['2k']['gltf'] if 'gltf' in fs else fs['blend']['2k']['blend']
            p = os.path.join(d, 'modelos-3d', 'polyhaven', mid); salvar(f['url'], os.path.join(p, os.path.basename(f['url'])), f.get('md5'))
            for rel, inc in f.get('include', {}).items(): salvar(inc['url'], os.path.join(p, rel), inc.get('md5'))
            reg.append({'id': mid, 'fonte': f'https://polyhaven.com/a/{mid}', 'licenca': 'CC0'}); print('ok', mid, flush=True)
    if 'hdris' in partes:
        for hid in HDRIS:
            f = json.loads(get(f'https://api.polyhaven.com/files/{hid}'))['hdri']['4k']['hdr']
            salvar(f['url'], os.path.join(d, 'hdris', os.path.basename(f['url'])), f.get('md5'))
            reg.append({'id': hid, 'fonte': f'https://polyhaven.com/a/{hid}', 'licenca': 'CC0'}); print('ok', hid, flush=True)
    if 'materiais' in partes:
        for m in MATERIAIS:
            dest = os.path.join(d, 'materiais', 'ambientcg', m)
            if not os.path.isdir(dest):
                z = dest + '.zip'; salvar(f'https://ambientcg.com/get?file={m}_2K-JPG.zip', z)
                zipfile.ZipFile(z).extractall(dest); os.remove(z)
            reg.append({'id': m, 'fonte': f'https://ambientcg.com/view?id={m}', 'licenca': 'CC0'}); print('ok', m, flush=True)
    if 'telas' in partes:
        import re
        for nome, aid in APPS.items():
            r = json.loads(get(f'https://itunes.apple.com/lookup?id={aid}&country=br&entity=software')).get('results') or []
            if not r: print('sem capturas', nome); continue
            for i, u in enumerate(r[0].get('screenshotUrls', []), 1):
                base = re.sub(r'/\d+x\d+bb\.\w+$', '', u); tam = '1320x2868' if re.search(r'6\.9|69', base) else '1242x2688'
                salvar(f'{base}/{tam}bb.png', os.path.join(d, 'telas-padrao', 'app-store', nome, f'{nome}-{i:02d}.png'))
            reg.append({'id': nome, 'fonte': r[0].get('trackViewUrl', '').split('?')[0], 'licenca': 'das empresas: só referência de layout'}); print('ok', nome, flush=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['status', 'pergunta', 'baixar', 'chrome'])
    ap.add_argument('--dir'); ap.add_argument('--sim'); ap.add_argument('--partes', default='polyhaven,hdris,materiais,telas'); a = ap.parse_args()
    d = pasta(a)
    if a.cmd == 'status': sys.exit(3 if status(d) else 0)
    if a.cmd == 'pergunta':
        falta = status(d) if os.path.isdir(d) else list(PARTES)
        print('\n' + pergunta(falta)); return
    if a.cmd == 'chrome':
        print('Pelo navegador do usuário (Claude in Chrome), um por vez, aba nova, formato glTF; conferir a licença na página:')
        for t, au, u in CHROME: print(f'  - {t} — {au} — CC-BY 4.0 — {u}  → {os.path.join(d, "modelos-3d", "sketchfab")}')
        print('Oficiais da Apple (opcional): .dmg pede o 7-Zip no Windows; o UI Kit pede conta no Figma:')
        for t, u in EXTRAS: print(f'  - {t}: {u}')
        return
    if not a.sim:
        print('Sem --sim: nada foi baixado. Pergunte antes (python acervo.py pergunta) ou, no modo autônomo, passe as palavras do pedido.'); sys.exit(3)
    os.makedirs(d, exist_ok=True); reg = []
    baixar(d, [p.strip() for p in a.partes.split(',') if p.strip()], reg)
    log = os.path.join(d, 'acervo.json'); hist = json.load(open(log, encoding='utf8')) if os.path.exists(log) else {'downloads': []}
    hist['downloads'].append({'quando': datetime.datetime.now().isoformat(timespec='seconds'), 'consentimento': a.sim, 'itens': reg})
    json.dump(hist, open(log, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    gi = os.path.join(d, '.gitignore')
    if not os.path.exists(gi): open(gi, 'w', encoding='utf8').write('modelos-3d/\nhdris/\nmateriais/\ntelas-padrao/\n*.zip\n')
    print(f'FIM: {len(reg)} itens em {d}. Faltam os aparelhos do Sketchfab: python acervo.py chrome')

if __name__ == '__main__': main()
