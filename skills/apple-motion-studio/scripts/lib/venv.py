"""Run a script inside the skill's own .venv (created by scripts/setup.py) when the current Python lacks the core packages.
Lets the README promise plain `python scripts/demo.py` on a clean machine after setup."""
import os, sys, importlib.util
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def venv_python():
    for rel in (('Scripts', 'python.exe'), ('bin', 'python')):
        p = os.path.join(SKILL, '.venv', *rel)
        if os.path.exists(p): return p
    return None
def ensure(modules=('numpy', 'scipy', 'PIL')):
    if all(importlib.util.find_spec(m) for m in modules): return
    py = venv_python()
    if py and os.path.normcase(os.path.abspath(sys.executable)) != os.path.normcase(os.path.abspath(py)):
        import subprocess; sys.exit(subprocess.call([py] + sys.argv))
    sys.exit('faltam pacotes Python do core (' + ', '.join(m for m in modules if not importlib.util.find_spec(m)) + '): rode  python scripts/setup.py')
