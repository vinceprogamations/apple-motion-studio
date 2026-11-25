# Caption track tied to an audio version: approved text, explicit start/end, editorial line breaks kept, frame-exact.
#   python captions.py import <legenda.srt|.vtt|.json> <captions.json> --audio <versão do áudio> [--fps 30]
#   python captions.py revise <captions.json> --id <c3> [--text "<novo texto>"] --dur <s> [--audio <nova versão>] [--fps 30]
#        a re-recorded line: that line gets its new duration; the lines BEFORE are untouched; the lines AFTER move by the
#        difference (only those that really changed position); report says which ones moved
#   python captions.py check <captions.json> [--fps 30]       overlap, 1-frame holes at boundaries, too-short lines
#   python captions.py export <captions.json> <out.srt|out.vtt>
# captions.json: {"fps": 30, "audio": "voz-v2", "lines": [{"id": "c1", "text": "Primeira linha\nquebra editorial", "start": 0.5, "end": 2.1,
#                 "confidence": null, "words": null}]}  (confidence stays null when unknown; words only if the piece highlights words)
# Times are stored quantised to frames (start = first frame shown, end = first frame NOT shown), so two contiguous lines share
# a boundary frame number: no overlap, no blank frame.
import sys, os, re, json, argparse
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
def q(t, fps): return round(round(t * fps) / fps, 6)
def ts(t, sep=','): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f'{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s % 1) * 1000)):03d}'
def parse_time(s): h, m, rest = s.replace(',', '.').split(':'); return int(h) * 3600 + int(m) * 60 + float(rest)

def load_any(p):
    if p.endswith('.json'): return json.load(open(p, encoding='utf8'))['lines']
    txt = open(p, encoding='utf-8-sig').read().replace('\r', ''); out = []
    for blk in re.split(r'\n\s*\n', txt):
        m = re.search(r'(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)', blk)
        if not m: continue
        lines = blk[m.end():].strip('\n'); out.append({'id': f'c{len(out) + 1}', 'text': lines, 'start': parse_time(m.group(1)), 'end': parse_time(m.group(2)), 'confidence': None, 'words': None})
    return out

def check(doc):
    fps = doc['fps']; L = sorted(doc['lines'], key=lambda c: c['start']); probs = []
    for c in L:
        if round((c['end'] - c['start']) * fps) < max(1, int(0.8 * fps)): probs.append(f"{c['id']}: curta demais ({c['end'] - c['start']:.2f} s) para ler")
    for a, b in zip(L, L[1:]):
        fa, fb = round(a['end'] * fps), round(b['start'] * fps)
        if fb < fa: probs.append(f"{a['id']}/{b['id']}: sobreposição de {fa - fb} quadro(s) em {b['start']:.3f} s")
        elif fb - fa == 1: probs.append(f"{a['id']}/{b['id']}: buraco de 1 quadro em {a['end']:.3f} s (some e volta)")
    return probs

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    i = sub.add_parser('import'); i.add_argument('src'); i.add_argument('out'); i.add_argument('--audio', required=True); i.add_argument('--fps', type=float, default=30)
    r = sub.add_parser('revise'); r.add_argument('file'); r.add_argument('--id', required=True); r.add_argument('--text'); r.add_argument('--dur', type=float, required=True); r.add_argument('--audio')
    c = sub.add_parser('check'); c.add_argument('file')
    e = sub.add_parser('export'); e.add_argument('file'); e.add_argument('out')
    a = ap.parse_args()
    if a.cmd == 'import':
        lines = load_any(a.src)
        for l in lines: l['start'], l['end'] = q(l['start'], a.fps), q(l['end'], a.fps)
        doc = {'fps': a.fps, 'audio': a.audio, 'lines': lines}; json.dump(doc, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
        p = check(doc); print(f'{len(lines)} linhas importadas (áudio {a.audio})'); [print('PROBLEMA:', x) for x in p]; sys.exit(1 if p else 0)
    doc = json.load(open(a.file, encoding='utf8')); fps = doc['fps']
    if a.cmd == 'revise':
        L = sorted(doc['lines'], key=lambda c: c['start']); k = next(n for n, c in enumerate(L) if c['id'] == a.id); tgt = L[k]
        old_end = tgt['end']; new_end = q(tgt['start'] + a.dur, fps); delta = round(new_end - old_end, 6); moved = []
        tgt['end'] = new_end
        if a.text is not None: tgt['text'] = a.text
        tgt['confidence'] = None; tgt['words'] = None
        for c in L[k + 1:]:
            if abs(delta) > 1e-9: c['start'], c['end'] = q(c['start'] + delta, fps), q(c['end'] + delta, fps); moved.append(c['id'])
        doc['audio'] = a.audio or doc['audio']; doc['lines'] = L; json.dump(doc, open(a.file, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
        p = check(doc); print(json.dumps({'revised': a.id, 'delta_s': delta, 'moved': moved, 'kept': [c['id'] for c in L[:k]], 'audio': doc['audio'], 'problems': p}, ensure_ascii=False))
        sys.exit(1 if p else 0)
    if a.cmd == 'check': p = check(doc); [print('PROBLEMA:', x) for x in p]; print('OK' if not p else f'{len(p)} problema(s)'); sys.exit(1 if p else 0)
    if a.cmd == 'export':
        vtt = a.out.endswith('.vtt'); out = ['WEBVTT', ''] if vtt else []
        for n, c in enumerate(sorted(doc['lines'], key=lambda c: c['start']), 1):
            if not vtt: out.append(str(n))
            out += [f"{ts(c['start'], '.' if vtt else ',')} --> {ts(c['end'], '.' if vtt else ',')}", c['text'], '']
        open(a.out, 'w', encoding='utf8').write('\n'.join(out)); print('->', a.out)

if __name__ == '__main__': main()
