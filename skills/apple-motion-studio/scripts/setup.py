# One-time, idempotent setup of the FREE core (run as many times as you like; paths with spaces are fine):
#   python scripts/setup.py [--extras] [--deep]
# 1. finds what already exists (Node, FFmpeg/ffprobe, Chrome/Chromium — also outside PATH; Blender optional)
# 2. creates <skill>/.venv (only if missing) and installs the pinned core packages (requirements.txt); --extras adds requirements-extra.txt
# 3. runs the doctor and prints the next command. It never installs system programs by itself: for a missing one it prints the
#    plan; scripts/ambiente.py instalar --sim "<user's words>" installs them after the user says yes.
import os, sys, subprocess, shutil, platform, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE); from lib.tools import find_tool; from lib.venv import venv_python
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception: pass
OS = platform.system()
HINT = {'Windows': {'node': 'winget install OpenJS.NodeJS.LTS', 'ffmpeg': 'winget install Gyan.FFmpeg', 'chrome': 'winget install Google.Chrome', 'blender': 'winget install BlenderFoundation.Blender'},
        'Darwin': {'node': 'brew install node', 'ffmpeg': 'brew install ffmpeg', 'chrome': 'brew install --cask google-chrome', 'blender': 'brew install --cask blender'},
        'Linux': {'node': 'sudo apt install nodejs  (ou nvm)', 'ffmpeg': 'sudo apt install ffmpeg', 'chrome': 'sudo apt install chromium', 'blender': 'sudo apt install blender'}}.get(OS, {})

def main():
    extras, deep = '--extras' in sys.argv, '--deep' in sys.argv; missing = []
    print(f'Apple Motion Studio · setup · {OS} · Python {platform.python_version()} · {SKILL}')
    if sys.version_info < (3, 10): sys.exit('Python 3.10+ é necessário (testado com 3.11).')
    node = shutil.which('node'); nv = subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip() if node else ''
    if not node or int(nv.lstrip('v').split('.')[0]) < 18: missing.append(('node', 'Node.js 18+'))
    else: print(f'  ok  node {nv}')
    for t in ('ffmpeg', 'ffprobe', 'chrome'):
        p = find_tool(t, required=False)
        if p: print(f'  ok  {t}: {p}')
        else: missing.append(('ffmpeg' if t == 'ffprobe' else t, t))
    b = find_tool('blender', required=False); print(f'  {"ok" if b else "--"}  blender (opcional, produto 3D de acabamento alto): {b or "não encontrado — " + HINT.get("blender", "blender.org")}')
    py = venv_python()
    if not py:
        print('  ..  criando .venv da skill'); subprocess.run([sys.executable, '-m', 'venv', os.path.join(SKILL, '.venv')], check=True); py = venv_python()
    else: print(f'  ok  .venv já existe: {py}')
    reqs = ['-r', os.path.join(SKILL, 'requirements.txt')] + (['-r', os.path.join(SKILL, 'requirements-extra.txt')] if extras else [])
    r = subprocess.run([py, '-m', 'pip', 'install', '--disable-pip-version-check', '-q'] + reqs, capture_output=True, text=True)
    if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit('pip falhou (veja acima). Sem internet? Instale os pacotes de requirements.txt manualmente.')
    print('  ok  pacotes Python do core (versões fixas em requirements.txt)')
    if missing:
        print('\nFALTA instalar (o setup não instala programas do sistema):')
        seen = set()
        for k, what in missing:
            if k in seen: continue
            seen.add(k); print(f'  - {what}:  {HINT.get(k, "instale pelo site oficial")}')
        print('Com o sim do usuário, eu mesmo instalo:  python scripts/ambiente.py instalar faltando --sim "<palavras dele>"')
        print('Depois rode  python scripts/setup.py  de novo.')
    print('\n--- diagnóstico ---'); d = subprocess.run([py, os.path.join(HERE, 'studio.py'), 'doctor'] + (['--deep'] if deep else []))
    json.dump({'setup': datetime.datetime.now().isoformat(timespec='seconds'), 'python': py, 'missing': [m[0] for m in missing]}, open(os.path.join(SKILL, '.venv', 'setup.json'), 'w'))
    if not missing and d.returncode == 0:
        demo = os.path.relpath(os.path.join(HERE, 'demo.py')) if not os.path.relpath(os.path.join(HERE, 'demo.py')).startswith('..') else os.path.join(HERE, 'demo.py')
        print(f'\nPronto. Próximo passo:  python "{demo}"   (≈ 1–2 min; gera a demo "Quando" com som e a revisão de 6 quadros)')
    sys.exit(1 if missing else d.returncode)

if __name__ == '__main__': main()
