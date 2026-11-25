# Executable discovery shared by the Python scripts (mix.py, finish.py, music_scan.py, QA, doctor, tests).
# Order: env var (FFMPEG / FFPROBE / CHROME / BLENDER) -> PATH -> known install locations per OS. No user-specific paths.
import os, sys, shutil, glob

WIN = sys.platform.startswith('win')
ENV = {'ffmpeg': 'FFMPEG', 'ffprobe': 'FFPROBE', 'chrome': 'CHROME', 'blender': 'BLENDER'}

def _winget(binname):
    base = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~/AppData/Local')), 'Microsoft', 'WinGet', 'Packages')
    hits = sorted(glob.glob(os.path.join(base, 'Gyan.FFmpeg*', 'ffmpeg-*', 'bin', binname + '.exe')), reverse=True)
    return hits[0] if hits else None

def _candidates(name):
    if name in ('ffmpeg', 'ffprobe'):
        return [_winget(name) if WIN else None, f'/opt/homebrew/bin/{name}', f'/usr/local/bin/{name}', f'/usr/bin/{name}']
    if name == 'chrome':
        return ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium']
    if name == 'blender':
        return sorted(glob.glob('C:/Program Files/Blender Foundation/*/blender.exe'), reverse=True) + ['/Applications/Blender.app/Contents/MacOS/Blender', '/usr/bin/blender', '/snap/bin/blender']
    return []

def find_tool(name, required=True):
    env = os.environ.get(ENV.get(name, ''), '')
    if env and os.path.exists(env): return env
    hit = shutil.which(name) or next((p for p in _candidates(name) if p and os.path.exists(p)), None)
    if not hit and required:
        raise SystemExit(f'{name} não encontrado. Defina {ENV.get(name, name.upper())}=<caminho> ou rode: python scripts/studio.py doctor')
    return hit
