# Studio Lume regression (spec §86): a required photo that is missing, corrupt or not bound must block the final export.
#   python tests/run_studio_lume.py            (from the skill root; needs node, Chrome, ffmpeg)
# Every case copies tests/fixtures/studio-lume to tests/_work/<case>, applies one defect and runs the operator command:
#   node scripts/render_dom.mjs video <case>/sequence.html <out.mp4> --fps 30 --root .
# Evidence (logs, reports, frame, video) goes to tests/evidence/01-studio-lume/.
import sys as _s0
for _st in (_s0.stdout, _s0.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import os, sys, shutil, subprocess, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts')); from lib.tools import find_tool
FIX = 'tests/fixtures/studio-lume'; EV = 'tests/evidence/01-studio-lume'; os.makedirs(EV, exist_ok=True)
FFMPEG, FFPROBE = find_tool('ffmpeg'), find_tool('ffprobe')
def h(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def case(name, mutate):
    w = f'tests/_work/{name}'; shutil.rmtree(w, ignore_errors=True); shutil.copytree(FIX, w); mutate(w); return w
def render(w, out):
    r = subprocess.run(['node', 'scripts/render_dom.mjs', 'video', f'{w}/sequence.html', out, '--fps', '30', '--root', '.', '--replace'], capture_output=True, text=True, encoding='utf8', errors='replace')
    return r.returncode, (r.stdout + r.stderr)
results = []
def decodes(p):   # real decode of the whole MP4 (not just a probe of the header)
    if not os.path.exists(p): return False
    r = subprocess.run([FFMPEG, '-v', 'error', '-i', p, '-f', 'null', '-'], capture_output=True, text=True); return r.returncode == 0 and not r.stderr.strip()
def record(name, expect_ok, code, log, extra='', reason=None, out=None):
    """PASSOU only if: exit code as expected AND (failure) the log names the expected reason and the previous master's sha256 is
    unchanged AND (success) the produced MP4 decodes end to end."""
    why = []
    if (code == 0) != expect_ok: why.append(f'exit {code}')
    if not expect_ok:
        if reason and reason not in log: why.append(f'motivo esperado ausente: "{reason}"')
        if h(master) != mh: why.append('MASTER ALTERADO')
        extra = (extra + ' ' if extra else '') + (f'motivo="{reason}" ' if reason else '') + ('master intacto (sha256 igual)' if h(master) == mh else '')
    if expect_ok and out is not None:
        ok_dec = decodes(out); extra += f' decodifica={"sim" if ok_dec else "NAO"}'
        if not ok_dec: why.append('MP4 não decodifica')
    ok = not why; results.append((name, 'PASSOU' if ok else 'FALHOU', code, extra + ('' if ok else ' <- ' + '; '.join(why))))
    open(f'{EV}/{name}.log', 'w', encoding='utf8').write(log)
    print(f"\n=== {name}: exit {code} -> {'esperado' if ok else 'INESPERADO'} {extra}\n" + '\n'.join(l for l in log.splitlines() if 'FAILED' in l or 'AVISO' in l or 'nota' in l or 'vaga' in l or 'preservado' in l or 'SAVED' in l or 'assets:' in l))

master = f'{EV}/master.mp4'   # a previously valid master must survive any failed export
if not os.path.exists(master):
    w = case('ref', lambda w: None); c, log = render(w, master); assert c == 0, log
mh = h(master)

# 1a. required photo missing
w = case('1a-foto-ausente', lambda w: os.remove(f'{w}/img/duda.jpg'))
c, log = render(w, master); record('1a-foto-ausente', False, c, log, reason='vaga avatar-duda: imagem não carregou')
# 1b. required photo corrupted (truncated JPEG)
def corrupt(w): data = open(f'{w}/img/duda.jpg', 'rb').read(); open(f'{w}/img/duda.jpg', 'wb').write(data[:600])
w = case('1b-foto-corrompida', corrupt)
c, log = render(w, master); record('1b-foto-corrompida', False, c, log, reason='vaga avatar-duda: imagem não carregou ou não decodificou')
# 2. all three files exist and the manifest is complete, but the scene paints a gradient in the third slot
def gradient(w):
    p = f'{w}/s1.html'; s = open(p, encoding='utf8').read()
    s = s.replace('data-asset="avatar-duda" style="background-image:url(img/duda.jpg)"', 'data-asset="avatar-duda" style="background:linear-gradient(140deg,#ffd59a,#f0a030)"')
    open(p, 'w', encoding='utf8').write(s)
w = case('2-vaga-com-gradiente', gradient)
c, log = render(w, master); record('2-vaga-com-gradiente', False, c, log, reason='gradiente')
# 3. an optional hero photo is absent and the storyboard approved the composition without it
def optional(w):
    p = f'{w}/asset-manifest.json'; m = json.load(open(p, encoding='utf8'))
    m['assets'].append({'id': 'foto-fachada', 'type': 'photo', 'scene': 's1', 'slot': 'foto-fachada', 'role': 'foto opcional da fachada', 'required': False,
                        'file': 'img/fachada.jpg', 'status': 'PLANNED', 'approval': {'status': 'approved-without', 'by': 'user', 'scope': 'storyboard aprovado sem a foto da fachada', 'date': '2026-11-24'}})
    json.dump(m, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
w = case('3-opcional-aprovada-sem', optional)
out3 = f'{EV}/3-opcional-aprovada-sem.mp4'; c, log = render(w, out3)
rep = json.load(open(out3.replace('.mp4', '.report.json'), encoding='utf8')) if os.path.exists(out3.replace('.mp4', '.report.json')) else {}
record('3-opcional-aprovada-sem', True, c, log, 'nota: ' + '; '.join(rep.get('notes', [])), out=out3)
# 4. the three correct photos re-integrated: same command must finish, frame shows the three photos, video decodes
w = case('4-fotos-corretas', lambda w: None)
out4 = f'{EV}/4-fotos-corretas.mp4'; c, log = render(w, out4)
probe = subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-show_entries', 'stream=width,height,nb_read_frames,r_frame_rate', '-of', 'csv=p=0', out4], capture_output=True, text=True).stdout.strip() if c == 0 else ''
if c == 0: subprocess.run([FFMPEG, '-v', 'error', '-y', '-ss', '1.5', '-i', out4, '-frames:v', '1', f'{EV}/depois - frame 1.5s (3 fotos).jpg'])
record('4-fotos-corretas', True, c, log, f'probe={probe}', out=out4)
# 5. a new delivery cannot skip the gate by deleting the manifest
w = case('5-sem-manifesto', lambda w: os.remove(f'{w}/asset-manifest.json'))
c, log = render(w, master); record('5-sem-manifesto', False, c, log, reason='sem asset-manifest.json')
# 6. an EMPTY manifest is for films without external assets: it cannot hide the three photo slots
w = case('6-manifesto-vazio-com-vagas', lambda w: open(f'{w}/asset-manifest.json', 'w').write('{"assets": []}'))
c, log = render(w, master); record('6-manifesto-vazio-com-vagas', False, c, log, reason='sem entrada no manifesto')
# 7. a project made before the gate renders only when declared legacy, and the report says so
w = case('7-legado-declarado', lambda w: os.remove(f'{w}/asset-manifest.json'))
out7 = f'{EV}/7-legado-declarado.mp4'
r = subprocess.run(['node', 'scripts/render_dom.mjs', 'video', f'{w}/sequence.html', out7, '--fps', '30', '--root', '.', '--replace', '--legacy', 'filme anterior ao portão (teste)'], capture_output=True, text=True, encoding='utf8', errors='replace')
rep7 = json.load(open(out7.replace('.mp4', '.report.json'), encoding='utf8')) if os.path.exists(out7.replace('.mp4', '.report.json')) else {}
record('7-legado-declarado', True, r.returncode, r.stdout + r.stderr, f"report.legacy={rep7.get('legacy')!r}", out=out7)
if not rep7.get('legacy'): results[-1] = (results[-1][0], 'FALHOU', results[-1][2], results[-1][3] + ' <- relatório sem o campo legacy')
print('\nRESUMO'); [print(f'  {n:28s} {s:7s} exit={c} {x}') for n, s, c, x in results]
json.dump([dict(case=n, result=s, exit=c, detail=x) for n, s, c, x in results], open(f'{EV}/RESUMO.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
sys.exit(0 if all(s == 'PASSOU' for _, s, _, _ in results) else 1)
