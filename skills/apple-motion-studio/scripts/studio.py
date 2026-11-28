# apple-motion-studio command entry point (no CLI framework on purpose).
#   python scripts/studio.py doctor [--deep] [--save <file>]   environment diagnosis (deep = launch Chrome to test WebGL2, run Blender)
#   python scripts/studio.py sync [--check]                     regenerate the Codex copy from the canonical skill / detect divergence
#   python scripts/studio.py validate                           frontmatter + paths + references + scripts of both distributions
#   python scripts/studio.py public <dest> [--repo-template <dir>]   clean public repository tree (private blocks stripped, guard)
#   python scripts/studio.py promote <render.mp4> <master.mp4> [qa_frames args]   frame QA (with <render>.timeline.json) then promote; old master kept
#   python scripts/studio.py state init <projeto> "<palavras do usuário>"   classifica a delegação (autônomo/híbrido/guiado)
#   python scripts/studio.py state gate <projeto> <etapa>          exit 0 = seguir · 3 = a única pergunta ao usuário · 4 = master só como prévia
#   python scripts/studio.py state decide <projeto> <etapa> "<escolha>" "<motivo em uma frase>"
#   python scripts/studio.py state approve <projeto> <etapa> "<escolha>" [--by usuario|terceiro:<quem>]
#   python scripts/studio.py state third <projeto> <etapa> <quem>   etapa que exige aprovação de terceiro
#   python scripts/studio.py state master <projeto> <mp4> [previa]  ·  state next <projeto> ["<próxima operação>"]  ·  state show <projeto>
#   python scripts/studio.py state present <projeto> <asset-id> <arquivo>   asset obrigatório recebido (libera o master)
# Status words: disponível e testado · disponível, não testado · ausente · incompatível · opcional · bloqueante · requer autorização
import sys, os, json, platform, shutil, subprocess, importlib, re, hashlib, datetime, glob
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
sys.path.insert(0, HERE); from lib.tools import find_tool
from lib.venv import ensure
if len(sys.argv) > 1 and sys.argv[1] in ('promote', 'validate'): ensure(('yaml',) if sys.argv[1] == 'validate' else ('numpy',))

def run(cmd, timeout=20):
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return (r.stdout + r.stderr).strip()
    except Exception as e: return f'ERRO: {e}'

def first_line(s): return s.splitlines()[0] if s else ''

def doctor(deep=False, save=None):
    rows = []
    def add(item, status, detail='', profile='core'): rows.append({'item': item, 'status': status, 'detail': detail, 'profile': profile})
    add('Sistema', 'disponível e testado', f'{platform.system()} {platform.release()} {platform.version()} ({platform.machine()})')
    add('CPU', 'disponível e testado', f'{platform.processor() or "?"} · {os.cpu_count()} threads')
    try:
        if platform.system() == 'Windows':
            ram = run(['powershell', '-NoProfile', '-Command', '[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)'])
            gpu = run(['powershell', '-NoProfile', '-Command', 'Get-CimInstance Win32_VideoController | ForEach-Object { "$($_.Name) | driver $($_.DriverVersion) | VRAM(WMI) $([math]::Round($_.AdapterRAM/1GB,1)) GB" }'])
        elif platform.system() == 'Darwin':
            ram = str(round(int(run(['sysctl', '-n', 'hw.memsize'])) / 2**30, 1)); gpu = run(['system_profiler', 'SPDisplaysDataType'])[:300]
        else:
            ram = str(round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2**30, 1)); gpu = run(['sh', '-c', 'lspci | grep -i vga'])
        add('RAM', 'disponível e testado', f'{ram} GB'); add('GPU / driver / VRAM', 'disponível e testado', gpu.replace('\n', ' ; ') + ' (VRAM via WMI é limitada a 4 GB em placas grandes)')
    except Exception as e: add('RAM/GPU', 'disponível, não testado', str(e))
    du = shutil.disk_usage(SKILL); add('Disco livre (volume do projeto)', 'disponível e testado' if du.free > 20e9 else 'bloqueante', f'{du.free/1e9:.0f} GB livres de {du.total/1e9:.0f} GB')
    # executables
    for name, prof, block in (('node', 'core', True), ('ffmpeg', 'core', True), ('ffprobe', 'core', True), ('chrome', 'core', True), ('blender', 'motion3d', False)):
        p = shutil.which(name) if name == 'node' else find_tool(name, required=False)
        if not p: add(name, 'bloqueante' if block else 'ausente', 'não encontrado', prof); continue
        if name == 'chrome' and platform.system() == 'Windows':
            ver = run(['powershell', '-NoProfile', '-Command', f"(Get-Item '{p}').VersionInfo.ProductVersion"])
        elif name == 'blender': ver = first_line(run([p, '--version'], 60)) if deep else '(versão não lida sem --deep)'
        else: ver = first_line(run([p, '-version' if name in ('ffmpeg', 'ffprobe') else '--version']))
        on_path = bool(shutil.which(name))
        add(name, 'disponível e testado' if not ver.startswith('ERRO') else 'incompatível', f'{ver} · {p}' + ('' if on_path or name == 'node' else ' · fora do PATH (resolvido por scripts/lib/tools)'), prof)
    add('python', 'disponível e testado', f'{platform.python_version()} · {sys.executable}')
    # python packages
    for mod, pkg, prof, need in (('PIL', 'Pillow', 'core', True), ('numpy', 'numpy', 'core', True), ('scipy', 'scipy', 'core', True), ('yaml', 'PyYAML', 'core', True), ('cv2', 'opencv-python', 'extra', False), ('librosa', 'librosa', 'audio', False), ('pyloudnorm', 'pyloudnorm', 'audio', False), ('scenedetect', 'scenedetect', 'qa', False)):
        try: m = importlib.import_module(mod); add(f'py:{pkg}', 'disponível e testado', getattr(m, '__version__', '?'), prof)
        except Exception: add(f'py:{pkg}', 'bloqueante' if need else 'opcional', 'não instalado' + (' — python scripts/setup.py' if need else ' — opcional: pip install -r requirements-extra.txt'), prof)
    # JS libraries vendored in the skill
    for lib, rel, prof in (('three.js', 'vendor/three-*', 'motion3d'), ('gsap', 'vendor/gsap', 'optional')):
        hit = glob.glob(os.path.join(SKILL, rel, '**', '*.js'), recursive=True)
        add(f'js:{lib}', 'disponível, não testado' if hit else ('ausente' if prof == 'motion3d' else 'opcional'), f'{len(hit)} arquivo(s) em {rel}' if hit else 'não vendorizado', prof)
    # fonts shipped with the DOM kit
    for f in ('Inter-Variable.ttf', 'Montserrat-latin.woff2'):
        p = os.path.join(SKILL, 'templates', 'dom', 'fonts', f); add(f'fonte:{f}', 'disponível, não testado' if os.path.exists(p) else 'ausente', 'OFL')
    # capture / browser integrations (cannot be probed from a script: reported as such)
    add('Captura CDP (render_dom.mjs)', 'disponível e testado' if os.path.exists(os.path.join(SKILL, 'tests', 'evidence', '01-studio-lume', '4-fotos-corretas.mp4')) else 'disponível, não testado', 'screenshot por Page.captureScreenshot', 'core')
    add('Playwright / Puppeteer', 'opcional', 'não usados: o CDP próprio cobre render e captura', 'capture')
    add('Claude in Chrome / ChatGPT', 'requer autorização', 'só pelo agente (MCP) e com login do usuário; não testável por script', 'images')
    add('Serviços pagos (Higgsfield, Artlist, ElevenLabs pago, After Effects, API OpenAI)', 'requer autorização', 'nunca usados sem pedido e orçamento', 'paid')
    # Open Design (optional pre-production): installer found ≠ app installed ≠ runnable ≠ connected to the agent
    dl = os.path.join(os.path.expanduser('~'), 'Downloads')
    od_inst = sorted(glob.glob(os.path.join(dl, 'open-design-*-setup.exe')) + glob.glob(os.path.join(dl, 'open-design-*.dmg')))
    if od_inst:
        hsh = hashlib.sha256(open(od_inst[-1], 'rb').read()).hexdigest()
        add('Open Design: instalador', 'disponível, não testado', f'{os.path.basename(od_inst[-1])} · sha256 {hsh[:16]}… (confira com o SHA-256 da release oficial; instalar é decisão do usuário)', 'preproducao')
    la = os.environ.get('LOCALAPPDATA', '')
    od_app = [q for q in (os.path.join(la, 'Programs', 'open-design', 'Open Design.exe'), os.path.join(la, 'Programs', 'Open Design', 'Open Design.exe'), '/Applications/Open Design.app') if la and os.path.exists(q) or q.startswith('/Applications') and os.path.exists(q)]
    add('Open Design: aplicativo', 'disponível, não testado' if od_app else 'opcional', od_app[0] if od_app else 'não instalado (extensão opcional de pré-produção; o core não depende dele)', 'preproducao')
    add('Open Design: conexão com o agente', 'opcional', 'não testável por script: depende do app aberto e da integração oficial configurada', 'preproducao')
    if deep:
        chrome = find_tool('chrome', required=False)
        if chrome:
            html = os.path.join(SKILL, 'tests', '_work', 'webgl.html'); os.makedirs(os.path.dirname(html), exist_ok=True)
            open(html, 'w').write("<script>const c=document.createElement('canvas');const g=c.getContext('webgl2');document.title=g?('WEBGL2 '+g.getParameter(g.VERSION)):'NO-WEBGL2';</script>")
            out = run([chrome, '--headless=new', '--enable-gpu', '--dump-dom', 'file:///' + html.replace('\\', '/')], 40)
            m = re.search(r'<title>(.*?)</title>', out); add('WebGL2 no Chrome headless (--enable-gpu)', 'disponível e testado' if m and m.group(1).startswith('WEBGL2') else 'incompatível', m.group(1) if m else out[:120], 'motion3d')
    counts = {}
    for r in rows: counts[r['status']] = counts.get(r['status'], 0) + 1
    w = max(len(r['item']) for r in rows)
    for r in rows: print(f"{r['item']:<{w}}  {r['status']:<24}  {r['detail']}")
    print('\nresumo:', ', '.join(f'{k}={v}' for k, v in counts.items()))
    core_bad = [r['item'] for r in rows if r['profile'] == 'core' and r['status'] in ('bloqueante', 'incompatível')]
    print('CORE GRATUITO:', 'PRONTO (pode renderizar a demo)' if not core_bad else 'FALTA ' + ', '.join(core_bad))
    print('EXTENSÕES:', ', '.join(f"{r['item']}={r['status']}" for r in rows if r['profile'] in ('motion3d', 'preproducao', 'extra', 'audio')))
    prof = {'checked': datetime.datetime.now().isoformat(timespec='seconds'), 'items': rows}
    if save: os.makedirs(os.path.dirname(os.path.abspath(save)), exist_ok=True); json.dump(prof, open(save, 'w', encoding='utf8'), ensure_ascii=False, indent=1); print('perfil salvo em', save)
    return 1 if counts.get('bloqueante') else 0

def promote(render, master, extra):
    """Promote a render to master only after frame QA passes (with the timeline written next to the render)."""
    tl = re.sub(r'\.mp4$', '', render, flags=re.I) + '.timeline.json'
    cmd = [sys.executable, os.path.join(HERE, 'qa_frames.py'), render] + (['--timeline', tl] if os.path.exists(tl) else []) + extra
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf8'); print(r.stdout + r.stderr)
    if r.returncode: print('NÃO PROMOVIDO: o QA de quadros encontrou problemas (corrija ou declare a intenção na timeline).'); return 1
    if os.path.exists(master):
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S'); prev = re.sub(r'\.mp4$', '', master, flags=re.I) + f' (anterior {stamp}).mp4'
        os.replace(master, prev); print('master anterior guardado em', prev)
    shutil.copy2(render, master)
    json.dump({'promoted': datetime.datetime.now().isoformat(timespec='seconds'), 'from': render, 'qa': 'ok', 'timeline': tl if os.path.exists(tl) else None,
               'sha256': hashlib.sha256(open(master, 'rb').read()).hexdigest()}, open(re.sub(r'\.mp4$', '', master, flags=re.I) + '.promote.json', 'w'), indent=1)
    print('PROMOVIDO:', master); return 0

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(open(__file__, encoding='utf8').read().split('\nimport')[0]); sys.exit(2)
    if a[0] == 'doctor': sys.exit(doctor('--deep' in a, a[a.index('--save') + 1] if '--save' in a else None))
    if a[0] == 'promote': sys.exit(promote(a[1], a[2], a[3:]))
    if a[0] == 'state':
        from lib import delegation as D
        op, proj = a[1], a[2]
        if op == 'init': st = D.init(proj, a[3]); print(D.summary(st)); sys.exit(0)
        st = D.load(proj)
        if op == 'gate':
            v, m = D.gate(st, a[3]); print(f'{v}: {m}'); sys.exit({'seguir': 0, 'perguntar': 3, 'previa': 4}[v])
        if op == 'decide':
            ok, m = D.decide(st, a[3], a[4], a[5] if len(a) > 5 else '')
            if not ok: print('PERGUNTE AO USUÁRIO (só isto): ' + m); sys.exit(3)
            D.save(proj, st); print(f'{a[3]}: {a[4]} ({m})'); sys.exit(0)
        if op == 'approve': D.approve(st, a[3], a[4], a[a.index('--by') + 1] if '--by' in a else 'usuario'); D.save(proj, st); print(D.summary(st)); sys.exit(0)
        if op == 'third': D.require_third(st, a[3], a[4]); D.save(proj, st); print(D.summary(st)); sys.exit(0)
        if op == 'present':
            for r in st['requires']:
                if r['id'] == a[3]: r['present'] = a[4]
            D.save(proj, st); print(D.summary(st)); sys.exit(0)
        if op == 'master': D.set_master(st, a[3], a[4] if len(a) > 4 else 'master'); D.save(proj, st); print(D.summary(st)); sys.exit(0)
        if op == 'next':
            if len(a) > 3: st['next'] = a[3]; D.save(proj, st)
            print(D.summary(st)); sys.exit(0)
        if op == 'show': print(D.summary(st)); sys.exit(0)
        sys.exit('state: operação desconhecida ' + op)
    if a[0] == 'public':
        from lib import public; sys.exit(public.build(os.path.abspath(a[1]), os.path.abspath(a[a.index('--repo-template') + 1]) if '--repo-template' in a else None))
    if a[0] in ('sync', 'validate'):
        from lib import distrib; sys.exit(distrib.sync(check='--check' in a) if a[0] == 'sync' else distrib.validate())
    sys.exit('comando desconhecido: ' + a[0])
