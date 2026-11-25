# Canonical source + generated distributions (no symlinks: they break on Windows checkouts).
# Canonical: <project>/.claude/skills/apple-motion-studio (Claude Code). Generated: <project>/.agents/skills/apple-motion-studio (Codex),
# identical except SKILL.md paths (.claude/skills -> .agents/skills). DISTRIBUTION.json in the copy records the logical version
# (sha256 of the canonical tree) and every file hash, so `sync --check` detects any divergence (edited copy, stale copy, extra files).
import os, sys, json, hashlib, shutil, re
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL)))
NAME = os.path.basename(SKILL)
TARGETS = {'codex': os.path.join(PROJECT, '.agents', 'skills', NAME)}
EXCLUDE_DIRS = {'__pycache__', '_work', 'evidence', '.venv', 'node_modules', 'out'}
REWRITE = {'SKILL.md': [('.claude/skills/' + NAME, '.agents/skills/' + NAME)]}

def files(root):
    out = []
    for d, ds, fs in os.walk(root):
        ds[:] = sorted(x for x in ds if x not in EXCLUDE_DIRS)
        for f in sorted(fs):
            if f == 'DISTRIBUTION.json': continue
            out.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, '/'))
    return out

def transformed(rel):
    data = open(os.path.join(SKILL, rel), 'rb').read()
    for a, b in REWRITE.get(rel, []): data = data.replace(a.encode(), b.encode())
    return data

def h(b): return hashlib.sha256(b).hexdigest()

def version():
    acc = hashlib.sha256()
    for rel in files(SKILL): acc.update(rel.encode()); acc.update(open(os.path.join(SKILL, rel), 'rb').read())
    return acc.hexdigest()[:16]

def sync(check=False):
    rc = 0; ver = version()
    for name, tgt in TARGETS.items():
        want = {rel: transformed(rel) for rel in files(SKILL)}
        have = set(files(tgt)) if os.path.isdir(tgt) else set()
        missing = [r for r in want if r not in have]; extra = sorted(have - set(want))
        changed = [r for r in want if r in have and h(open(os.path.join(tgt, r), 'rb').read()) != h(want[r])]
        meta_p = os.path.join(tgt, 'DISTRIBUTION.json'); meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
        state = 'em dia' if not (missing or extra or changed) and meta.get('version') == ver else 'DIVERGENTE'
        print(f'{name}: {tgt}\n  versão canônica {ver} · cópia {meta.get("version", "sem registro")} · {state}' +
              f'\n  faltando {len(missing)} · sobrando {len(extra)} · alterados {len(changed)}')
        for t, l in (('faltando', missing), ('sobrando', extra), ('alterado', changed)):
            for r in l[:20]: print(f'    {t}: {r}')
        if check:
            rc |= 0 if state == 'em dia' else 1; continue
        for r in extra: os.remove(os.path.join(tgt, r))          # only inside the generated copy
        for r, data in want.items():
            p = os.path.join(tgt, r); os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p) or h(open(p, 'rb').read()) != h(data): open(p, 'wb').write(data)
        for d, ds, fs in sorted(os.walk(tgt), reverse=True):
            if d != tgt and not os.listdir(d): os.rmdir(d)
        json.dump({'skill': NAME, 'version': ver, 'source': os.path.relpath(SKILL, PROJECT).replace(os.sep, '/'), 'generated_by': 'scripts/studio.py sync',
                   'files': {r: h(data) for r, data in want.items()}}, open(meta_p, 'w'), indent=1)
        print(f'  sincronizado → versão {ver}')
    return rc

def frontmatter(path):
    import yaml
    txt = open(path, encoding='utf8').read(); m = re.match(r'^---\n(.*?)\n---\n', txt, re.S)
    if not m: raise ValueError('sem frontmatter YAML')
    return yaml.safe_load(m.group(1)), txt

def validate():
    errs = 0
    for label, root in (('claude', SKILL), *TARGETS.items()):
        p = os.path.join(root, 'SKILL.md')
        if not os.path.exists(p): print(f'{label}: SKILL.md ausente'); errs += 1; continue
        try: fm, txt = frontmatter(p)
        except Exception as e: print(f'{label}: frontmatter inválido: {e}'); errs += 1; continue
        name, desc = fm.get('name', ''), fm.get('description', '')
        probs = []
        if name != os.path.basename(root): probs.append(f'name "{name}" ≠ pasta "{os.path.basename(root)}"')
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name or '') or len(name) > 64: probs.append('name fora do padrão (minúsculas, hífens, ≤ 64)')
        if not desc or len(desc) > 1024: probs.append(f'description vazia ou > 1024 caracteres ({len(desc)})')
        if set(fm) - {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}: probs.append(f'chaves extras no frontmatter: {set(fm) - {"name", "description"}}')
        refs = sorted(set(re.findall(r'`((?:references|scripts|templates|tests)/[^`\s]+)`', txt)))
        miss = [r for r in refs if not glob_exists(root, r)]
        probs += [f'caminho citado não existe: {r}' for r in miss]
        lines = txt.count('\n')
        print(f'{label}: name={name} · description {len(desc)} car · {lines} linhas · {len(refs)} caminhos citados · ' + ('OK' if not probs else f'{len(probs)} problema(s)'))
        for x in probs: print('   - ' + x)
        errs += len(probs)
    return 1 if errs else 0

def glob_exists(root, rel):
    import glob as g
    rel = rel.rstrip('.,;:)')
    return bool(g.glob(os.path.join(root, rel.replace('<', '*').replace('>', '*')))) or os.path.exists(os.path.join(root, rel))
