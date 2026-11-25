"""Public distribution build: a clean repository tree that contains ONLY the skill, its docs, minimal examples and media whose
rights are confirmed. Project history stays in the private canonical copy:
  - <!-- privado --> … <!-- /privado --> blocks are removed from Markdown files
  - files that only make sense in the origin project are excluded (PRIVATE_FILES)
  - a guard scans every text file for private terms and fails the build if any remain
  python scripts/studio.py public <dest> [--repo-template <dir with README/LICENSE/assets>]"""
import os, re, shutil, sys, json, hashlib
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = os.path.basename(SKILL)
EXCLUDE_DIRS = {'__pycache__', '_work', 'evidence', '.venv', 'node_modules', 'out'}
PRIVATE_FILES = {'references/films.md', 'tests/run_regression.py', 'tests/origin-films.json', 'DISTRIBUTION.json'}
# words that must never reach the public tree (origin-project brand, people, account), stored as sha256 prefixes so this file does
# not publish them itself; plus any absolute user path. Fictional film names are allowed.
GUARD_HASHES = {'ba536f262c1c4ddf', '8d3e0bf685d07778', 'bffc2a5a74cad6a3', 'c5b676c944331fc1'}
GUARD_PATH = re.compile(r'[A-Za-z]:[\/]+Users[\/]|/home/[a-z]|/Users/[A-Za-z]', re.I)
def private_hit(line):
    if GUARD_PATH.search(line): return True
    return any(hashlib.sha256(w.encode()).hexdigest()[:16] in GUARD_HASHES for w in re.findall(r'[a-z]+', line.lower()))
BLOCK = re.compile(r'[ \t]*<!-- privado -->.*?<!-- /privado -->[ \t]*\n?', re.S)
TEXT = ('.md', '.py', '.mjs', '.js', '.html', '.css', '.json', '.txt', '.srt', '.svg', '.yml', '.yaml', '.ps1', '.sh')

def build(dest, template=None):
    dst_skill = os.path.join(dest, 'skills', NAME)
    if os.path.isdir(dest):
        for x in os.listdir(dest):
            if x == '.git': continue
            p = os.path.join(dest, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(dst_skill, exist_ok=True); n = 0
    for d, ds, fs in os.walk(SKILL):
        ds[:] = sorted(x for x in ds if x not in EXCLUDE_DIRS)
        for f in sorted(fs):
            src = os.path.join(d, f); rel = os.path.relpath(src, SKILL).replace(os.sep, '/')
            if rel in PRIVATE_FILES or f.startswith('page-v2'): continue
            out = os.path.join(dst_skill, rel); os.makedirs(os.path.dirname(out), exist_ok=True)
            if rel.endswith('.md'): open(out, 'w', encoding='utf8', newline='\n').write(BLOCK.sub('', open(src, encoding='utf8').read()))
            else: shutil.copy2(src, out)
            n += 1
    if template:
        for d, ds, fs in os.walk(template):
            ds[:] = [x for x in ds if not x.startswith('_')]
            for f in fs:
                if f.endswith('.html') or f.startswith('demo-'): continue    # sources of the banner, not repo content
                src = os.path.join(d, f); rel = os.path.relpath(src, template); out = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(out), exist_ok=True); shutil.copy2(src, out); n += 1
    bad = []
    for d, ds, fs in os.walk(dest):
        ds[:] = [x for x in ds if x != '.git']
        for f in fs:
            p = os.path.join(d, f)
            if not f.lower().endswith(TEXT): continue
            for i, line in enumerate(open(p, encoding='utf8', errors='replace'), 1):
                if private_hit(line): bad.append(f'{os.path.relpath(p, dest)}:{i}: {line.strip()[:120]}')
    if bad:
        print('BLOQUEADO: termos privados na distribuição pública:'); [print('  ' + b) for b in bad[:60]]; return 1
    fm = open(os.path.join(dst_skill, 'SKILL.md'), encoding='utf8').read().split('---')[1]
    desc = re.search(r'^description: (.*)$', fm, re.M).group(1)
    if not re.search(r'^name: ' + NAME + r'$', fm, re.M) or not (0 < len(desc) <= 1024): print(f'BLOQUEADO: frontmatter inválido (name, ou description com {len(desc)} caracteres; máx 1024)'); return 1
    acc = hashlib.sha256()
    for d, ds, fs in sorted(os.walk(dst_skill)):
        for f in sorted(fs): p = os.path.join(d, f); acc.update(os.path.relpath(p, dst_skill).replace(os.sep, '/').encode()); acc.update(open(p, 'rb').read())
    json.dump({'skill': NAME, 'logical_version': acc.hexdigest()[:16], 'files': n}, open(os.path.join(dest, 'skills', NAME, 'DISTRIBUTION.json'), 'w'), indent=1)
    print(f'distribuição pública: {n} arquivos em {dest} · versão lógica {acc.hexdigest()[:16]} · guarda de privacidade OK'); return 0
