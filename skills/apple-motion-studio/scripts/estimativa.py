# Estima quanto tempo leva para produzir o vídeo NESTE computador — com o consentimento do usuário para ler o PC e rodar um teste.
#   python estimativa.py ler --sim "<palavras do usuário>" [--blender]   # lê CPU/RAM/GPU e mede: render de página (60 quadros 1080p),
#                                                                     # motion blur e (opcional) Blender. Grava .local/maquina.json
#   python estimativa.py estimar --dur 30 [--fps 30] [--formatos 2] [--blur 1|4|6] [--filmagem] [--blender-quadros 168]
#                                  [--cenas 10] [--revisoes 2] [--modo guiado|autonomo] [--json]
# Sem "ler", usa a medição salva; sem medição, usa valores de referência (avisando que são genéricos).
# O texto separa TEMPO DE MÁQUINA (render, Blender, mix, QA — medido) de TEMPO DE TRABALHO DO AGENTE (roteiro, animação,
# revisões — faixa) e de TEMPO SEU (aprovar storyboard e filme). Nada roda sem o sim do usuário.
import sys, os, json, time, platform, subprocess, shutil, tempfile, argparse, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); sys.path.insert(0, HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
from lib.tools import find_tool
MAQ = os.path.join(SKILL, '.local', 'maquina.json')
REF = {'s_por_quadro_1080p': 0.066, 'fator_blur_por_subquadro': 0.8, 's_por_quadro_blender_padrao': 8.3}   # teste medido no PC de origem (Ryzen 7 5700X, RTX 3050)
# Calibração com um filme real (filme de academia com filmagem + Blender, 25–26/11/2026, mesmo PC): página do teste 0,066 s/quadro → filme com vidro e filmagem 0,236 s/quadro
# (×3,6) e sem filmagem ≈ ×2,5; cada subquadro de motion blur custou +0,107 s (≈ 1,6× o quadro do teste); Blender: cena de composição
# (emissão, tela no celular) 1,25 s/quadro ≈ 0,15 × o teste padrão; produto fotorrealista ≈ 1,0 × o teste (8,5 s/quadro medidos).
CAL = {'pagina_filmagem': 3.6, 'pagina_design': 2.5, 'subquadro_x_teste': 1.6, 'blender_composicao': 0.15, 'blender_produto': 1.0}

def run(cmd, t=40):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout.strip()
    except Exception as e: return ''

def hardware():
    h = {'sistema': f'{platform.system()} {platform.release()}', 'threads': os.cpu_count(), 'cpu': platform.processor()}
    if platform.system() == 'Windows':
        h['cpu'] = run(['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_Processor | Select-Object -First 1).Name']) or h['cpu']
        h['ram_gb'] = run(['powershell', '-NoProfile', '-Command', '[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)'])
        h['gpu'] = run(['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_VideoController | ForEach-Object Name) -join " + "'])
    elif platform.system() == 'Darwin':
        h['ram_gb'] = str(round(int(run(['sysctl', '-n', 'hw.memsize']) or 0) / 2 ** 30, 1)); h['gpu'] = run(['sh', '-c', "system_profiler SPDisplaysDataType | grep 'Chipset Model' | head -2"])
    else:
        h['ram_gb'] = str(round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2 ** 30, 1)); h['gpu'] = run(['sh', '-c', 'lspci | grep -i vga'])
    h['disco_livre_gb'] = round(shutil.disk_usage(SKILL).free / 1e9)
    return h

def bench_pagina(blur=1, quadros=60):
    node = shutil.which('node'); out = os.path.join(tempfile.mkdtemp(prefix='ams-bench-'), 'b.mp4')
    cmd = [node, os.path.join(HERE, 'render_dom.mjs'), 'video', os.path.join(HERE, 'lib', 'bench', 'bench.html'), out, '--root', SKILL, '--w', '1920', '--h', '1080',
           '--fps', '30', '--to', str(quadros / 30)] + (['--blur', str(blur)] if blur > 1 else [])
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True, timeout=900); dt = time.time() - t0
    if r.returncode or not os.path.exists(out): raise SystemExit('teste de render falhou: ' + (r.stdout + r.stderr)[-600:])
    shutil.rmtree(os.path.dirname(out), ignore_errors=True)
    return dt / quadros

def bench_blender():
    b = find_tool('blender', required=False)
    if not b: return None
    py = "import bpy,time\nbpy.ops.wm.read_factory_settings(use_empty=False)\nsc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32;sc.render.resolution_x=1920;sc.render.resolution_y=1080\n" \
         "sc.render.filepath=r'%s'\nt=time.time()\nfor f in range(1,4): sc.frame_set(f); bpy.ops.render.render(write_still=True)\nprint('BENCH',(time.time()-t)/3)\n"
    d = tempfile.mkdtemp(prefix='ams-bl-'); s = os.path.join(d, 'b.py'); open(s, 'w').write(py % os.path.join(d, 'f'))
    o = run([b, '-b', '--factory-startup', '-P', s], 600); shutil.rmtree(d, ignore_errors=True)
    for l in o.splitlines():
        if l.startswith('BENCH'): return float(l.split()[1])
    return None

def ler(sim, blender):
    if not sim: raise SystemExit('Peça o consentimento antes: "Posso ler as configurações do seu PC (CPU, memória, placa de vídeo) e rodar um teste de render de ~1 minuto para estimar o tempo?" — e passe a resposta em --sim.')
    h = hardware(); print('PC:', h['cpu'], '·', h['threads'], 'threads ·', h.get('ram_gb'), 'GB ·', h.get('gpu'))
    print('medindo render de página (60 quadros 1080p)…', flush=True); s1 = bench_pagina(1)
    print(f'  {s1:.3f} s/quadro', flush=True); print('medindo motion blur (4 subquadros)…', flush=True); s4 = bench_pagina(4, 30)
    fator = max(0.05, (s4 / s1 - 1) / 3); print(f'  {s4:.3f} s/quadro com blur 4 → +{fator * 100:.0f}% por subquadro')
    bl = bench_blender() if blender else None
    if blender: print(f'  Blender Cycles (cena padrão, 32 amostras, 1080p): {bl:.2f} s/quadro' if bl else '  Blender não encontrado ou falhou')
    d = {'medido_em': datetime.datetime.now().isoformat(timespec='seconds'), 'consentimento': sim, 'hardware': h, 's_por_quadro_1080p': round(s1, 4),
         'fator_blur_por_subquadro': round(fator, 3), 's_por_quadro_blender_padrao': bl}
    os.makedirs(os.path.dirname(MAQ), exist_ok=True); json.dump(d, open(MAQ, 'w', encoding='utf8'), ensure_ascii=False, indent=1); print('gravado em', MAQ)

def fmt(s):
    s = int(round(s)); return f'{s // 3600} h {s % 3600 // 60:02d} min' if s >= 3600 else (f'{s // 60} min' if s >= 60 else f'{s} s')

def estimar(a):
    m = json.load(open(MAQ, encoding='utf8')) if os.path.exists(MAQ) else None
    spf = (m or REF)['s_por_quadro_1080p']; fb = (m or REF)['fator_blur_por_subquadro']
    blp = (m or {}).get('s_por_quadro_blender_padrao') or REF['s_por_quadro_blender_padrao']; bl_q = blp * CAL['blender_' + a.blender_tipo]
    quadros = int(round(a.dur * a.fps))
    spf_film = spf * CAL['pagina_filmagem' if a.filmagem else 'pagina_design'] + (a.blur - 1) * spf * CAL['subquadro_x_teste']
    um_render = quadros * spf_film
    n_render = a.formatos * (1 + a.revisoes) + 1                                         # prévia + finais por formato + uma por revisão
    maq = {'renders do filme': um_render * n_render, 'stills de revisão': 25 * spf * 6 * (1 + a.revisoes),
           'Blender': a.blender_quadros * bl_q * a.formatos * (1.2 if a.revisoes else 1), 'som (mix, master) e QA': 90 * a.formatos * (1 + a.revisoes)}
    cenas = a.cenas or max(6, round(a.dur / 3))
    agente = {'briefing e combinado': (5, 10), 'storyboard com quadros reais': (20, 45), f'animação ({cenas} cenas)': (6 * cenas, 11 * cenas),
              'som (trilha, efeitos, sincronia)': (15, 30), f'revisões ({a.revisoes})': (12 * a.revisoes, 25 * a.revisoes)}
    if a.formatos > 1: agente['reenquadrar formatos extras'] = (25 * (a.formatos - 1), 45 * (a.formatos - 1))
    tot_m = sum(maq.values()); lo = sum(v[0] for v in agente.values()) * 60 + tot_m; hi = sum(v[1] for v in agente.values()) * 60 + tot_m
    r = {'base': 'medido neste PC' if m else 'valores de referência (rode "ler" com o consentimento do usuário para medir este PC)', 'quadros': quadros,
         'render_unico': fmt(um_render), 'maquina': {k: fmt(v) for k, v in maq.items() if v > 0}, 'agente_min': {k: f'{v[0]}–{v[1]} min' for k, v in agente.items()},
         'total': f'{fmt(lo)} a {fmt(hi)}', 'pausas_suas': 'storyboard e filme com som' if a.modo == 'guiado' else 'nenhuma obrigatória'}
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=1)); return
    print(f"Estimativa ({r['base']}) — {a.dur} s, {a.fps} fps, {a.formatos} formato(s){', motion blur ' + str(a.blur) + '×' if a.blur > 1 else ''}{', com filmagem' if a.filmagem else ''}{', Blender ' + str(a.blender_quadros) + ' quadros' if a.blender_quadros else ''}")
    print(f"  Um render completo: {r['render_unico']} ({quadros} quadros)")
    print('  Tempo de máquina:'); [print(f'    {k}: {v}') for k, v in r['maquina'].items()]
    print('  Trabalho do agente:'); [print(f'    {k}: {v}') for k, v in r['agente_min'].items()]
    print(f"  Total estimado: {r['total']} — mais o tempo das suas aprovações ({r['pausas_suas']}).")
    print('  É uma faixa: cada nota de revisão soma um render e a parte de criação varia com a complexidade das cenas.')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['ler', 'estimar']); ap.add_argument('--sim'); ap.add_argument('--blender', action='store_true')
    ap.add_argument('--dur', type=float, default=30); ap.add_argument('--fps', type=int, default=30); ap.add_argument('--formatos', type=int, default=1); ap.add_argument('--blur', type=int, default=1)
    ap.add_argument('--filmagem', action='store_true'); ap.add_argument('--blender-quadros', type=int, default=0); ap.add_argument('--blender-tipo', choices=['composicao', 'produto'], default='composicao'); ap.add_argument('--cenas', type=int, default=0)
    ap.add_argument('--revisoes', type=int, default=2); ap.add_argument('--modo', default='guiado'); ap.add_argument('--json', action='store_true'); a = ap.parse_args()
    ler(a.sim, a.blender) if a.cmd == 'ler' else estimar(a)

if __name__ == '__main__': main()
