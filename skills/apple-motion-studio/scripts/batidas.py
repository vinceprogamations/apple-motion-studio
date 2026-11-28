# Mede o andamento REAL de uma trilha e diz como casá-la com a grade de cortes do filme.
# Lição (filme de academia, 26/11/2026): estimar BPM por picos de volume ou só pelos bumbos errou 0,4 %–2 % em garage sincopado; os
# cortes e efeitos foram saindo do tempo (~60 ms no logo). Aqui o período é medido por autocorrelação do envelope de ataques em
# TRÊS bandas (bumbo 40–150 Hz, corpo 150–400 Hz, chimbal 2–5 kHz) e em vários trechos; vence a banda mais CONSISTENTE.
#   python batidas.py <trilha> [--de 30 --ate 90] [--grade 0.4645] [--json]
#     --grade <s>   período da grade do filme: devolve o fator atempo que põe a trilha na grade (sem mudar o tom)
# Depois: corte nos múltiplos do período medido OU estique a trilha com atempo para a grade escolhida — nunca misture os dois.
import sys, os, json, subprocess, argparse
import numpy as np
from scipy.signal import butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from lib.tools import find_tool
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
FF = find_tool('ffmpeg'); SR = 11025; HOP = 0.002
BANDAS = {'bumbo': (40, 150), 'corpo': (150, 400), 'chimbal': (2000, 5000)}

def carregar(f, a, b):
    return np.frombuffer(subprocess.run([FF, '-v', 'error', '-ss', str(a), '-t', str(b - a), '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)

def periodo(x, banda, lo=0.40, hi=0.60):   # 100–150 BPM; fora disso use --lo/--hi
    y = sosfilt(butter(4, banda, 'band', fs=SR, output='sos'), x); h = int(SR * HOP)
    e = np.sqrt(np.convolve(y ** 2, np.ones(h) / h, 'same')[::h]); on = np.maximum(0, np.diff(np.log(e + 1e-6))); on = on - on.mean()
    ac = np.correlate(on, on, 'full')[len(on) - 1:]; L0, L1 = int(lo / HOP), int(hi / HOP)
    i = L0 + int(np.argmax(ac[L0:L1])); est = []
    for k in (1, 4, 8):                                        # refina em 4 e 8 batidas (mais precisão), parábola no pico
        c = i * k; w = max(2, int(0.03 / HOP * k ** 0.5))
        if c + w + 1 >= len(ac): continue
        j = c - w + int(np.argmax(ac[c - w:c + w])); y0, y1, y2 = ac[j - 1], ac[j], ac[j + 1]; den = (y0 - 2 * y1 + y2)
        est.append((j + (0.5 * (y0 - y2) / den if den else 0)) * HOP / k)
    return est[-1] if est else i * HOP

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('trilha'); ap.add_argument('--de', type=float, default=20); ap.add_argument('--ate', type=float, default=110)
    ap.add_argument('--grade', type=float); ap.add_argument('--json', action='store_true'); a = ap.parse_args()
    dur = float(subprocess.run([find_tool('ffprobe'), '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.trilha], capture_output=True, text=True).stdout or 0)
    fim = min(a.ate, dur - 1) if dur else a.ate; janelas = [(t, t + 30) for t in np.arange(a.de, max(a.de + 1, fim - 29), 15)][:6]
    res = {}
    for nome, b in BANDAS.items():
        ps = [periodo(carregar(a.trilha, j0, j1), b) for j0, j1 in janelas]
        ps = np.array(ps); med = float(np.median(ps)); ok = ps[np.abs(ps - med) <= 0.006]          # descarta trechos discrepantes (intro, quebra)
        esp = float(ok.max() - ok.min()) * 1000 if len(ok) >= max(2, len(ps) // 2) else 999.0
        res[nome] = {'periodo': round(float(np.median(ok)) if len(ok) else med, 5), 'bpm': round(60 / (float(np.median(ok)) if len(ok) else med), 2), 'espalhamento_ms': round(esp, 1),
                     'trechos_usados': f'{len(ok)}/{len(ps)}', 'janelas': [round(float(p), 4) for p in ps]}
    # a banda mais consistente vence; bandas que "acharam" 2/3 ou 3/2 do período ficam de fora pela própria inconsistência
    melhor = min(res, key=lambda k: res[k]['espalhamento_ms']); P = res[melhor]['periodo']
    r = {'trilha': a.trilha, 'bandas': res, 'escolhida': melhor, 'periodo': P, 'bpm': round(60 / P, 2), 'confiavel': res[melhor]['espalhamento_ms'] <= 6}
    if a.grade: r['atempo_para_grade'] = round(P / a.grade, 5); r['deriva_ms_por_10s_sem_ajuste'] = round((1 - a.grade / P) * 10000, 1)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=1)); return
    for k, v in res.items(): print(f"  {k:8s} {v['periodo']:.4f} s ({v['bpm']:6.2f} BPM)  espalhamento {v['espalhamento_ms']:5.1f} ms  trechos {v['trechos_usados']}")
    print(f"Andamento: {r['bpm']} BPM (período {P:.4f} s, banda {melhor}){'' if r['confiavel'] else '  — ATENÇÃO: bandas inconsistentes, confira de ouvido ou com outro trecho'}")
    if a.grade:
        print(f"Grade do filme {a.grade:.4f} s: sem ajuste, a música desliza {r['deriva_ms_por_10s_sem_ajuste']:+.1f} ms a cada 10 s.")
        print(f"Para casar: ffmpeg -i trilha -af atempo={r['atempo_para_grade']} ...  (o drop também muda: novo tempo = drop / {r['atempo_para_grade']})")

if __name__ == '__main__': main()
