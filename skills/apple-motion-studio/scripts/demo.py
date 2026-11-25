# Reproducible public demo: "Quando" (fictional app), 12 s vertical with sound, made only with the skill's own files
# (DOM page + generated music and sound kit; no library, no account, no download). Runs the normal production commands:
# delegation state → storyboard board → render (asset gate with an empty manifest) → events → sound (mix with stems, finish)
# → frame QA, layout QA, audio QA → promote. Then the localized revision "atrase a confirmação em seis quadros".
#   python scripts/demo.py [--out <pasta>] [--skip-revision]
# Output (default ./apple-motion-studio-demo/ in the current folder): "Quando - MASTER.mp4", "Quando v2 (confirmação +6 quadros) - MASTER.mp4",
#   "Quando - antes x depois.mp4", RELATORIO.json, storyboard/tiras.jpg.
import os, sys, json, shutil, subprocess, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); DEMO = os.path.join(SKILL, 'demo', 'quando')
sys.path.insert(0, HERE); from lib.tools import find_tool
from lib.venv import ensure; ensure()
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
PY, NODE = sys.executable, (shutil.which('node') or 'node')
def run(*a, check=True):
    t0 = time.time(); r = subprocess.run([str(x) for x in a], capture_output=True, text=True, encoding='utf8', errors='replace', cwd=SKILL)
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] if (r.stdout + r.stderr).strip() else ['']
    print(f'  [{time.time() - t0:5.1f}s] {os.path.basename(str(a[1])) if a[0] in (PY, NODE) else a[0]} {a[2] if len(a) > 2 else ""} → {tail[0][:150]}')
    if check and r.returncode: print(r.stdout[-3000:], r.stderr[-3000:]); sys.exit(f'falhou: {" ".join(map(str, a))}')
    return r

def edit_breath(src, dst, at, delta, sr=48000):
    """Editor's music edit for a timing note: lengthen (or shorten) the silence before the drop by `delta` seconds, so the drop
    follows the moved event and EVERYTHING before the breath stays sample-identical (neighbouring scenes keep their timing)."""
    import numpy as np, wave
    ff = find_tool('ffmpeg'); raw = subprocess.run([ff, '-v', 'error', '-i', src, '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2); i = int(at * sr); n = int(round(delta * sr)); L = len(x)
    y = np.concatenate([x[:i], np.zeros((n, 2), np.float32), x[i:]])[:L] if n >= 0 else np.concatenate([x[:i], x[i - n:], np.zeros((-n, 2), np.float32)])[:L]
    subprocess.run([ff, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', dst], input=y.astype(np.float32).tobytes(), check=True)

def produce(out, tag, page, cues, rep):
    """One full production pass for a page version: render → events → sound → QA → promote."""
    rel = os.path.relpath(page, SKILL); render = os.path.join(out, f'Quando{tag} - render.mp4'); final = os.path.join(out, f'Quando{tag} - FINAL.mp4'); master = os.path.join(out, f'Quando{tag} - MASTER.mp4')
    for p in (render, final): [os.remove(x) for x in (p,) if os.path.exists(x)]
    run(NODE, 'scripts/render_dom.mjs', 'video', rel, render, '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30', '--manifest', os.path.join(DEMO, 'asset-manifest.json'))
    ev = os.path.join(out, f'events{tag}.json'); run(NODE, 'scripts/render_dom.mjs', 'events', rel, ev, '--root', '.', '--w', '1080', '--h', '1920')
    drop = next(e['t'] for e in json.load(open(ev, encoding='utf8')) if e['name'] == 'confirmado')   # the music edit follows the same beat source
    base = os.path.join(out, 'musica-base.wav')   # outside the --lib folder: mix.py matches names by substring
    if not os.path.exists(base): run(PY, 'scripts/synth_music.py', base, '--len', '12', '--drop', '7.0', '--breath', '0.4', '--bpm', '120', '--seed', '4')
    edit_breath(base, os.path.join(out, 'sfx', 'quando-musica.wav'), 7.0 - 0.4, drop - 7.0)
    stem = os.path.join(out, f'Quando{tag} - stem.wav')
    run(PY, 'scripts/mix.py', cues, stem, '--lib', os.path.join(out, 'sfx'), '--events', ev, '--len', '12', '--stems', os.path.join(out, f'stems{tag}'))
    run(PY, 'scripts/finish.py', '--video', render, '--sfx', stem, '--out', final, '--sfx-db', '0', '--fade-in', '0', '--fade-out', '0.4', '--len', '12')
    shutil.copy(render.replace('.mp4', '.timeline.json'), final.replace('.mp4', '.timeline.json'))
    qa = run(PY, 'scripts/qa_audio.py', 'deliver', final, '--timeline', final.replace('.mp4', '.timeline.json'), '--json', os.path.join(out, f'qa-audio{tag}.json'), check=False)
    lay = run(NODE, 'scripts/render_dom.mjs', 'layout', rel, os.path.join(out, f'layout{tag}'), '--root', '.', '--w', '1080', '--h', '1920', '--fps', '30', check=False)
    if os.path.exists(master): os.remove(master)
    pr = run(PY, 'scripts/studio.py', 'promote', final, master, check=False)
    rep[tag or 'v1'] = {'master': master, 'promovido': pr.returncode == 0, 'qa_audio': json.load(open(os.path.join(out, f'qa-audio{tag}.json'), encoding='utf8')),
                        'layout': json.load(open(os.path.join(out, f'layout{tag}', 'layout.json'), encoding='utf8')), 'events': json.load(open(ev, encoding='utf8'))}
    return master

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(os.getcwd(), 'apple-motion-studio-demo')); ap.add_argument('--skip-revision', action='store_true'); a = ap.parse_args()
    out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True); t0 = time.time(); rep = {'demo': 'Quando', 'custo_adicional': 0}
    print('1 · delegação'); run(PY, 'scripts/studio.py', 'state', 'init', out, 'Faça o comercial inteiro, decide tudo.')
    run(PY, 'scripts/studio.py', 'state', 'decide', out, 'storyboard', 'A · sobreposição das agendas', 'o horário é visto, não lido: a compreensão nasce no quadro em que só o 15:00 acende (3,9 s)')
    print('2 · storyboard (duas tiras, escolha registrada)'); run(NODE, 'scripts/render_dom.mjs', 'stills', 'demo/quando/storyboard/tiras.html', os.path.join(out, 'storyboard'), '0', '--root', '.', '--w', '1920', '--h', '1080')
    print('3 · som: kit e trilha gerados (autoria própria)'); sfx = os.path.join(out, 'sfx'); os.makedirs(sfx, exist_ok=True)
    run(PY, 'scripts/synth_sfx.py', sfx)   # the music is generated per version in produce(), with its drop on the "confirmado" event
    run(PY, 'scripts/studio.py', 'state', 'decide', out, 'musica', 'trilha gerada (synth_music, drop no evento confirmado)', 'custo zero e redistribuível na demo pública; o drop cai no "Confirmado"')
    print('4 · produção v1'); m1 = produce(out, '', os.path.join(DEMO, 'page.html'), os.path.join(DEMO, 'cues.json'), rep)
    run(PY, 'scripts/studio.py', 'state', 'master', out, m1); run(PY, 'scripts/studio.py', 'state', 'next', out, 'revisão: atrasar a confirmação em 6 quadros')
    if not a.skip_revision:
        print('5 · revisão localizada: "atrase a confirmação em seis quadros"')
        src = open(os.path.join(DEMO, 'page.html'), encoding='utf8').read(); old = 'confirmado: 7.0,'
        assert old in src; p2 = os.path.join(DEMO, 'page-v2.html'); open(p2, 'w', encoding='utf8').write(src.replace(old, 'confirmado: 7.2,', 1))
        m2 = produce(out, ' v2 (confirmação +6 quadros)', p2, os.path.join(DEMO, 'cues.json'), rep); os.remove(p2)
        e1 = {e['name']: e['t'] for e in rep['v1']['events']}; e2 = {e['name']: e['t'] for e in rep[' v2 (confirmação +6 quadros)']['events']}
        moved = {k: [e1[k], e2[k]] for k in e1 if abs(e1[k] - e2.get(k, -9)) > 1e-9}
        on = run(PY, 'scripts/qa_audio.py', 'onset', m1, m2, '--at', '7.1', '--win', '0.2', check=False); onj = json.loads(on.stdout[on.stdout.index('{'):])
        others = run(PY, 'scripts/qa_audio.py', 'onset', m1, m2, '--at', '5.4', '--win', '0.15', check=False); oth = json.loads(others.stdout[others.stdout.index('{'):])
        rep['revisao'] = {'pedido': 'atrase a confirmação em seis quadros', 'eventos_movidos': moved, 'onset_confirmacao_mp4': onj, 'onset_toque_vizinho_mp4': oth,
                          'ok': list(moved) == ['confirmado'] and abs(onj['delta_ms'] - 200) <= 2 and abs(oth['delta_ms']) <= 1}
        ff = find_tool('ffmpeg'); cmp_ = os.path.join(out, 'Quando - antes x depois.mp4')
        subprocess.run([ff, '-v', 'error', '-y', '-ss', '5.8', '-t', '2.4', '-i', m1, '-ss', '5.8', '-t', '2.4', '-i', m2, '-filter_complex',
                        "[0:v]scale=540:960[a];[1:v]scale=540:960[b];[a][b]hstack[v];[0:a][1:a]amerge=inputs=2,pan=stereo|c0=c0|c1=c2[au]", '-map', '[v]', '-map', '[au]',
                        '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', cmp_], check=True)
        rep['comparativo'] = cmp_ + ' (esquerda/canal L = v1, direita/canal R = v2)'
        run(PY, 'scripts/studio.py', 'state', 'master', out, m2); run(PY, 'scripts/studio.py', 'state', 'next', out, 'entregue; aguardando notas')
    rep['segundos'] = round(time.time() - t0, 1); rep['evidencia_som'] = 'medido (este script não ouve)'
    json.dump(rep, open(os.path.join(out, 'RELATORIO.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    v = rep['v1']; print(f"\nMASTER: {v['master']}  ·  promovido={v['promovido']}  ·  áudio {v['qa_audio']['integrated_lufs']} LUFS / {v['qa_audio']['true_peak_dbtp']} dBTP ({v['qa_audio']['result']})"
                        f"  ·  layout {v['layout']['samples']} amostras, {len(v['layout']['collisions'])} colisões")
    if 'revisao' in rep: print(f"REVISÃO: eventos movidos {rep['revisao']['eventos_movidos']}; confirmação Δ {rep['revisao']['onset_confirmacao_mp4']['delta_ms']} ms no MP4; toque vizinho Δ {rep['revisao']['onset_toque_vizinho_mp4']['delta_ms']} ms → {'OK' if rep['revisao']['ok'] else 'FALHOU'}")
    print(f"tempo total {rep['segundos']} s · relatório {os.path.join(out, 'RELATORIO.json')}")
    sys.exit(0 if v['promovido'] and (('revisao' not in rep) or rep['revisao']['ok']) else 1)

if __name__ == '__main__': main()
