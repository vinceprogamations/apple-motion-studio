# Asset manifest tool (asset-manifest.json lives next to the film's sequence/page).
#   python assets.py status   <manifest>                      table: id, scene, slot, required, status, file, hash ok?, approval
#   python assets.py approve  <manifest> <id|all> --scope "storyboard v2 aprovado pelo usuário" [--by user]
#                                                             records sha256 + pixel size + approval (only for files that exist)
#   python assets.py omit     <manifest> <id> --scope "..."   optional slot approved WITHOUT its asset (storyboard decision)
#   python assets.py affected <manifest> <id>                 scenes that must be re-validated when this asset changes
# Statuses: PLANNED NEEDS_USER_ASSET NEEDS_GENERATION NEEDS_CAPTURE NEEDS_DOWNLOAD DOWNLOADED VALIDATING REJECTED APPROVED INTEGRATED
# The renderer (render_dom.mjs) enforces the manifest: a required asset that is missing, changed, unapproved, unlicensed,
# not bound to its data-asset element, invisible in its declared time window or too small blocks the final render.
import sys, os, json, hashlib, argparse, datetime
from PIL import Image

def load(p): return json.load(open(p, encoding='utf8'))
def save(p, m): open(p, 'w', encoding='utf8').write(json.dumps(m, ensure_ascii=False, indent=1) + '\n')
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('manifest'); ap.add_argument('id', nargs='?')
    ap.add_argument('--scope', default=''); ap.add_argument('--by', default='user'); a = ap.parse_args()
    m = load(a.manifest); mdir = os.path.dirname(os.path.abspath(a.manifest)); today = datetime.date.today().isoformat()
    sel = [x for x in m['assets'] if a.id in (None, 'all') or x['id'] == a.id]
    if a.id not in (None, 'all') and not sel: sys.exit(f'id não encontrado: {a.id}')
    if a.cmd == 'status':
        for x in m['assets']:
            f = os.path.join(mdir, x.get('file') or ''); ex = bool(x.get('file')) and os.path.exists(f)
            hk = ('ok' if sha(f) == x.get('sha256') else 'MUDOU') if ex and x.get('sha256') else ('-' if ex else 'AUSENTE')
            print(f"{x['id']:16s} {x.get('scene','?'):4s} req={str(x.get('required', True))[0]} {x.get('status','?'):16s} hash={hk:7s} aprov={x.get('approval',{}).get('status','-'):16s} {x.get('file','')}")
    elif a.cmd == 'approve':
        if not a.scope: sys.exit('--scope é obrigatório: diga O QUE foi aprovado e por quem (ex.: "storyboard v2, usuário, 24/11")')
        for x in sel:
            f = os.path.join(mdir, x.get('file') or '')
            if not x.get('file') or not os.path.exists(f): print(f"pulado (arquivo ausente): {x['id']}"); continue
            with Image.open(f) as im: im.verify()
            with Image.open(f) as im: x['pixels'] = list(im.size)
            x['sha256'] = sha(f); x['status'] = 'APPROVED' if x.get('status') not in ('INTEGRATED',) else x['status']
            x['approval'] = {'status': 'approved', 'by': a.by, 'scope': a.scope, 'date': today}; print(f"aprovado: {x['id']} {x['pixels']} {x['sha256'][:12]}")
        save(a.manifest, m)
    elif a.cmd == 'omit':
        for x in sel:
            if x.get('required', True): sys.exit(f"{x['id']} é obrigatório; só vagas opcionais podem ser omitidas")
            x['approval'] = {'status': 'approved-without', 'by': a.by, 'scope': a.scope or 'storyboard', 'date': today}; print('omissão aprovada:', x['id'])
        save(a.manifest, m)
    elif a.cmd == 'affected':
        print(sorted({x['scene'] for x in sel} | {s for x in sel for s in x.get('also_in', [])}))
    else: sys.exit('comando desconhecido')

if __name__ == '__main__': main()
