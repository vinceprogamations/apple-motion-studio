# Negative + intentional fixtures for qa_frames.py (spec §§ 64, 85). Synthetic clips are generated with ffmpeg lavfi,
# so the defect position is known exactly; then a real DOM render (Studio Lume fixture) is checked with and without its hold declared.
#   python tests/run_frame_qa.py
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); from lib.tools import find_tool
FF = find_tool('ffmpeg'); W = 'tests/_work/frameqa'; EV = 'tests/evidence/04-frame-qa'; os.makedirs(W, exist_ok=True); os.makedirs(EV, exist_ok=True)
def mk(name, vf_chain, extra=None):
    out = f'{W}/{name}.mp4'
    if not os.path.exists(out):
        subprocess.run([FF, '-v', 'error', '-y', *vf_chain, *(extra or []), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '30', out], check=True)
    return out
moving = ['-f', 'lavfi', '-i', 'testsrc2=size=540x960:rate=30:duration=4']
base = mk('ok', moving)
black = mk('preto', [*moving, '-vf', "drawbox=enable='between(t,1.5,2.0)':c=black:t=fill"])
white = mk('branco', [*moving, '-vf', "drawbox=enable='between(t,1.5,2.0)':c=white:t=fill"])
freeze = mk('congelado2', [*moving, '-filter_complex', '[0:v]split[a][b];[a][b]freezeframes=first=45:last=75:replace=45'])      # frames 45..75 repeat frame 45 (1.03 s)
dupes = mk('repetido2', [*moving, '-filter_complex', '[0:v]split[a][b];[a][b]freezeframes=first=60:last=62:replace=59'])        # 3 frames re-captured from frame 59
clip = mk('audio-clipado', [*moving, '-f', 'lavfi', '-i', 'sine=f=440:d=4', '-af', 'volume=30dB', '-shortest'], ['-c:a', 'aac'])
silent = mk('silencio', [*moving, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest'], ['-c:a', 'aac'])
def tl(path, d):
    json.dump(d, open(path, 'w')); return path
cases = [  # (name, video, args, expected_exit)
    ('ok', base, ['--fps', '30', '--duration', '4'], 0),
    ('fps-errado', base, ['--fps', '25'], 1), ('duracao-errada', base, ['--duration', '5'], 1), ('resolucao-errada', base, ['--size', '1080x1920'], 1),
    ('preto', black, [], 1), ('preto-intencional', black, ['--timeline', tl(f'{W}/tl-preto.json', {'intentional': [{'type': 'black', 'from': 1.5, 'to': 2.05, 'why': 'corte para preto'}]})], 0),
    ('branco', white, [], 1), ('branco-intencional', white, ['--timeline', tl(f'{W}/tl-branco.json', {'intentional': [{'type': 'white', 'from': 1.5, 'to': 2.05, 'why': 'bloom para branco'}]})], 0),
    ('congelado', freeze, [], 1), ('pausa-intencional', freeze, ['--timeline', tl(f'{W}/tl-hold.json', {'intentional': [{'type': 'hold', 'from': 1.4, 'to': 2.6, 'why': 'hold de leitura'}]})], 0),
    ('repetido', dupes, [], 1),
    ('timeline-lacuna', base, ['--timeline', tl(f'{W}/tl-lac.json', {'fps': 30, 'total': 4, 'scenes': [{'id': 's1', 'start': 0, 'end': 2}, {'id': 's2', 'start': 2.5, 'end': 4}]})], 1),
    ('timeline-sobreposta', base, ['--timeline', tl(f'{W}/tl-sob.json', {'fps': 30, 'total': 4, 'scenes': [{'id': 's1', 'start': 0, 'end': 2.5}, {'id': 's2', 'start': 2, 'end': 4}]})], 1),
    ('timeline-ok', base, ['--timeline', tl(f'{W}/tl-ok.json', {'fps': 30, 'total': 4, 'scenes': [{'id': 's1', 'start': 0, 'end': 2}, {'id': 's2', 'start': 2, 'end': 4}]})], 0),
    ('audio-clipado', clip, ['--audio'], 1),
    ('silencio', silent, ['--audio'], 1), ('silencio-intencional', silent, ['--audio', '--timeline', tl(f'{W}/tl-sil.json', {'intentional': [{'type': 'silence', 'from': 0, 'to': 4, 'why': 'peça muda'}]})], 0),
]
lume = 'tests/evidence/01-studio-lume/4-fotos-corretas.mp4'
if os.path.exists(lume):
    cases += [('render-dom-sem-hold-declarado', lume, ['--fps', '30', '--duration', '2.5'], 1),
              ('render-dom-hold-declarado', lume, ['--fps', '30', '--duration', '2.5', '--timeline', tl(f'{W}/tl-lume.json', {'fps': 30, 'total': 2.5, 'scenes': [{'id': 's1', 'start': 0, 'end': 2.5}],
                'intentional': [{'type': 'hold', 'from': 1.2, 'to': 2.5, 'why': 'perfis parados para leitura'}]})], 0)]
res = []; log = []
for name, vid, args, want in cases:
    r = subprocess.run([sys.executable, 'scripts/qa_frames.py', vid, *args], capture_output=True, text=True, encoding='utf8')
    ok = (r.returncode == want); res.append((name, 'PASSOU' if ok else 'FALHOU', r.returncode, want))
    log.append(f'### {name} (exit {r.returncode}, esperado {want})\n{r.stdout}{r.stderr}')
open(f'{EV}/frame_qa.log', 'w', encoding='utf8').write('\n'.join(log))
for n, s, c, w in res: print(f'{n:32s} {s}  exit={c} esperado={w}')
json.dump([dict(case=n, result=s, exit=c, expected=w) for n, s, c, w in res], open(f'{EV}/RESUMO.json', 'w'), indent=1)
sys.exit(0 if all(s == 'PASSOU' for _, s, _, _ in res) else 1)
