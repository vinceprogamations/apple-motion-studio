# Teste de celular a partir do MP4 renderizado: o que a pessoa vê no feed, a 360 px de largura, 1 quadro por segundo.
# Em vídeos verticais, sobrepõe as áreas cobertas pela interface do Reels/TikTok (topo 14 %, base 20 %, direita 12 %)
# e mede quanto CONTEÚDO (bordas, texto, botões) cai dentro delas. Olhe a folha: texto que não se lê aqui não se lê no celular.
#   python qa_celular.py <video.mp4> [--saida <pasta>] [--fps 1]
# Saída: <pasta>/celular.jpg (+ celular_areas.jpg no 9:16) e celular.json (segundos com conteúdo forte nas áreas cobertas).
import sys, os, json, subprocess, argparse
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from lib.tools import find_tool
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
FF, FP = find_tool('ffmpeg'), find_tool('ffprobe')
TOPO, BASE, DIREITA = 0.14, 0.20, 0.12

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--saida'); ap.add_argument('--fps', type=float, default=1); a = ap.parse_args()
    out = a.saida or os.path.join(os.path.dirname(os.path.abspath(a.video)), 'qa-celular'); os.makedirs(out, exist_ok=True)
    w, h = map(int, subprocess.run([FP, '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout.strip().split(',')[:2])
    pw = 360; ph = int(round(pw * h / w / 2)) * 2; vert = h > w
    raw = subprocess.run([FF, '-v', 'error', '-i', a.video, '-vf', f'fps={a.fps},scale={pw}:{ph}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, ph, pw, 3)
    cols = 8 if vert else 5; rows = (len(fr) + cols - 1) // cols; lab = 18
    def folha(ims, nome):
        S = Image.new('RGB', (cols * (pw + 6) + 6, rows * (ph + lab + 6) + 6), (18, 18, 18)); d = ImageDraw.Draw(S)
        for i, im in enumerate(ims):
            x = 6 + (i % cols) * (pw + 6); y = 6 + (i // cols) * (ph + lab + 6); S.paste(im, (x, y + lab)); d.text((x + 2, y + 3), f'{i / a.fps:.0f}s', fill=(230, 230, 230))
        S.save(os.path.join(out, nome), quality=88)
    folha([Image.fromarray(f) for f in fr], 'celular.jpg')
    res = {'video': a.video, 'largura_teste': pw, 'quadros': len(fr), 'vertical': vert}
    if vert:
        ims, alertas = [], []
        for i, f in enumerate(fr):
            g = np.asarray(Image.fromarray(f).convert('L'), np.float32); ed = np.abs(np.diff(g, axis=1))   # bordas fortes = texto/botões
            zonas = {'topo': ed[:int(ph * TOPO)], 'base': ed[int(ph * (1 - BASE)):], 'direita': ed[int(ph * TOPO):int(ph * (1 - BASE)), int(pw * (1 - DIREITA)) - 1:]}
            for z, e in zonas.items():
                dens = float((e > 60).mean())
                if dens > 0.012: alertas.append({'s': round(i / a.fps, 1), 'area': z, 'densidade_bordas': round(dens, 3)})
            im = Image.fromarray(f).convert('RGBA'); o = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(o)
            d.rectangle([0, 0, pw, int(ph * TOPO)], fill=(255, 0, 80, 70)); d.rectangle([0, int(ph * (1 - BASE)), pw, ph], fill=(255, 0, 80, 70))
            d.rectangle([int(pw * (1 - DIREITA)), int(ph * TOPO), pw, int(ph * (1 - BASE))], fill=(255, 0, 80, 70)); ims.append(Image.alpha_composite(im, o).convert('RGB'))
        folha(ims, 'celular_areas.jpg'); res['alertas_areas'] = alertas
        print(f"{len(alertas)} segundo(s) com conteúdo forte nas áreas cobertas pela interface" + (': ' + ', '.join(f"{x['s']:g}s {x['area']}" for x in alertas[:12]) if alertas else ''))
    json.dump(res, open(os.path.join(out, 'celular.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('folhas em', out, '— OLHE as imagens: todo texto que precisa ser lido tem de ser legível aqui.')

if __name__ == '__main__': main()
