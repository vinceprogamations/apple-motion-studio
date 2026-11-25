# Split a flat logo PNG (shape on transparent background) into its connected pieces, so the OFFICIAL mark can be
# animated piece by piece (assemble, scatter, re-form) without redrawing it. Writes <out>/pN.png + <out>/parts.json.
#   python split_logo.py logo.png out_dir [--min-area 200] [--star-index N]
# parts.json: {W, H, parts: [{f, x, y, w, h, area, kind}]}, sorted by area (largest first). kind: 'face' for pieces
# >= 15% of the largest, 'star' for the small piece that fills its box least (the accent, e.g. a star), 'tile'
# for the rest. Check by eye; --star-index N forces one.
import sys, os, json, argparse, collections
import numpy as np
from PIL import Image
from scipy import ndimage
ap = argparse.ArgumentParser(); ap.add_argument('png'); ap.add_argument('out'); ap.add_argument('--min-area', type=int, default=200); ap.add_argument('--star-index', type=int)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
im = Image.open(a.png).convert('RGBA'); A = np.array(im); mask = A[:, :, 3] > 40
lab, n = ndimage.label(mask); parts = []
for i, sl in enumerate(ndimage.find_objects(lab)):
    area = int((lab[sl] == i + 1).sum())
    if area < a.min_area: continue
    crop = A[sl].copy(); crop[:, :, 3] = np.where(lab[sl] == i + 1, crop[:, :, 3], 0)
    parts.append(dict(x=sl[1].start, y=sl[0].start, w=sl[1].stop - sl[1].start, h=sl[0].stop - sl[0].start, area=area, crop=crop))
parts.sort(key=lambda p: -p['area']); big = parts[0]['area']
# the accent piece (e.g. a 4-point star) fills much less of its bounding box than a square tile does
small = [k for k, p in enumerate(parts) if p['area'] < 0.15 * big]
fill = {k: parts[k]['area'] / (parts[k]['w'] * parts[k]['h']) for k in small}
med = float(np.median(list(fill.values()))) if fill else 1
star = a.star_index if a.star_index is not None else (min(fill, key=fill.get) if fill and min(fill.values()) < 0.75 * med else None)
meta = []
for k, p in enumerate(parts):
    kind = 'face' if p['area'] >= 0.15 * big else ('star' if k == star else 'tile')
    Image.fromarray(p.pop('crop')).save(os.path.join(a.out, f'p{k}.png')); meta.append(dict(f=f'p{k}.png', **{q: int(v) for q, v in p.items()}, kind=kind))
json.dump(dict(W=im.size[0], H=im.size[1], parts=meta), open(os.path.join(a.out, 'parts.json'), 'w'))
print(f'{len(meta)} pieces:', collections.Counter(m['kind'] for m in meta))
