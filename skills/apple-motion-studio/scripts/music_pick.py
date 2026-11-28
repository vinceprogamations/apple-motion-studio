# Reproducible music choice for a film: filter FIRST by authorisation (commercial use, the delivery's destination, budget,
# availability), THEN rank the viable tracks by fit (a drop that can land on the reveal, energy there, bass, punch, a usable
# ending, client preferences as tie-break). Writes the choice, the alternative and every substitution with its reason.
#   python music_pick.py <catalog.json> --reveal 14.0 --len 21 [--budget 0] [--dest publico|cliente|redistribuir] \
#          [--prefer garage,eletronica] [--ab <dir>] [--out choice.json]
# catalog.json: [{"file": "...", "title": "...", "license": "Pixabay Content License", "verified": true, "commercial": true,
#                 "redistribute": false, "content_id": false|true|null, "cost": 0, "tags": ["eletronica"], "voice": false}]
#   verified = the licence of THIS copy is recorded (where/when downloaded); content_id null = unknown.
# --ab <dir>: renders the recommendation and the alternative on the SAME film window (reveal-aligned), loudness-matched to
#   -16 LUFS, for the one question of the hybrid mode ("quero escolher a música"). Autonomous mode: no A/B, just the choice.
import json, sys, os, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.tools import find_tool
import trilhas
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass

def viable(t, a):
    """(ok, reason) — authorisation before taste."""
    if not t.get('verified'): return False, 'licença desta cópia não verificada'
    if not t.get('commercial'): return False, 'licença não permite uso comercial'
    if (t.get('cost') or 0) > a.budget: return False, f'custa {t["cost"]} e a verba é {a.budget:g}'
    if a.dest == 'redistribuir' and not t.get('redistribute'): return False, 'licença não permite redistribuir o arquivo (demo pública/repositório)'
    if a.dest == 'publico' and t.get('content_id') is not False: return False, 'Content ID ' + ('registrado' if t.get('content_id') else 'desconhecido') + ' (risco de reivindicação em publicação)'
    if not os.path.exists(t['file']): return False, 'arquivo indisponível'
    u = trilhas.usada(t['file'])                                   # pedido do usuário: nenhum vídeo repete a música de outro
    if u: return False, 'já usada em ' + ', '.join(u)
    return True, ''

def fit(t, m, a):
    """Score + the drop to use: the drop must leave >= reveal seconds before it (the film starts before the drop)."""
    drops = [d for d in m['drops'] if d >= a.reveal and d + (a.len - a.reveal) <= m['dur']]
    if not drops: return -1, None, 'sem drop utilizável para revelar em %.1f s' % a.reveal
    d = drops[0]; db = m['db']; i = int(d * 2)
    contrast = db[i] - min(db[max(0, i - 4):i])                     # silence → drop contrast at the reveal
    energy = max(db[i:i + 4]) if i < len(db) else -60
    end = db[min(len(db) - 1, int((d + a.len - a.reveal) * 2))]   # level where the film ends (a natural ending is lower)
    pref = sum(1 for p in a.prefer if p in [x.lower() for x in t.get('tags', [])])
    s = contrast * 1.0 + (energy + 20) * 0.5 + m['bass'] * 6 + min(m['punch'], 4) * 0.8 + pref * 2 - (0 if t.get('voice') is False else 3)
    return float(s), float(d), f'drop em {d:.1f} s (+{contrast:.0f} dB sobre o respiro), energia {energy:.0f} dB, graves {m["bass"]:.2f}' + (f', preferência do cliente ({pref})' if pref else '')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('catalog'); ap.add_argument('--reveal', type=float, required=True); ap.add_argument('--len', type=float, required=True)
    ap.add_argument('--budget', type=float, default=0); ap.add_argument('--dest', default='cliente', choices=['cliente', 'publico', 'redistribuir'])
    ap.add_argument('--prefer', default=''); ap.add_argument('--ab'); ap.add_argument('--out'); a = ap.parse_args(); a.prefer = [p.strip().lower() for p in a.prefer.split(',') if p.strip()]
    cat = json.load(open(a.catalog, encoding='utf8')); base = os.path.dirname(os.path.abspath(a.catalog))
    for t in cat: t['file'] = t['file'] if os.path.isabs(t['file']) else os.path.join(base, t['file'])
    from music_scan import analyze
    rejected, ranked = [], []
    for t in cat:
        ok, why = viable(t, a)
        if not ok: rejected.append({'title': t.get('title', os.path.basename(t['file'])), 'reason': why}); continue
        m = analyze(t['file']); s, d, why = fit(t, m, a) if m else (-1, None, 'faixa curta demais')
        (ranked if s >= 0 else rejected).append({'title': t.get('title', os.path.basename(t['file'])), 'file': t['file'], 'score': round(s, 2), 'drop': d, 'reason': why, 'license': t.get('license')})
    ranked.sort(key=lambda r: -r['score'])
    from music_scan import load, SR as MSR
    import numpy as np
    for r in ranked[:2]:   # the scan works in 0.5 s steps: refine the drop to the 10 ms onset (a 0.25 s error puts the drop BEFORE the gesture)
        x = load(r['file']); h = int(0.01 * MSR); a0 = int(max(0, r['drop'] - 0.75) * MSR); seg = x[a0:a0 + int(1.5 * MSR)]
        e = np.array([20 * np.log10(np.sqrt((seg[i:i + h] ** 2).mean()) + 1e-9) for i in range(0, len(seg) - h, h)])
        jump = e[5:] - np.array([e[i - 5:i].mean() for i in range(5, len(e))]); k = int(np.argmax(jump)) + 5
        r['drop_scan'] = r['drop']; r['drop'] = round((a0 + k * h) / MSR, 3); r['music_from'] = round(r['drop'] - a.reveal, 3)
    # the best track by taste alone may be unusable: report the substitution explicitly
    taste = []
    for t in cat:
        m = analyze(t['file']) if os.path.exists(t['file']) else None
        if m: s, d, _ = fit(t, m, a); taste.append((s, t.get('title', os.path.basename(t['file']))))
    best_taste = max(taste)[1] if taste else None
    res = {'budget': a.budget, 'dest': a.dest, 'reveal': a.reveal, 'choice': ranked[0] if ranked else None, 'alternative': ranked[1] if len(ranked) > 1 else None,
           'rejected': rejected, 'cost': 0 if not ranked else next((t.get('cost', 0) for t in cat if t['file'] == ranked[0]['file']), 0)}
    if ranked and best_taste and best_taste != ranked[0]['title']:
        why = next((r['reason'] for r in rejected if r['title'] == best_taste), 'pontuação menor')
        res['substitution'] = f'a melhor pelo encaixe seria "{best_taste}", mas: {why} → escolhida "{ranked[0]["title"]}"'
    if ranked: res['why'] = f'"{ranked[0]["title"]}": {ranked[0]["reason"]}; licença {ranked[0]["license"]}; custo adicional {res["cost"]}.'
    if a.ab and ranked:
        os.makedirs(a.ab, exist_ok=True); ff = find_tool('ffmpeg')
        for tag, r in (('A-recomendada', ranked[0]), ('B-alternativa', ranked[1] if len(ranked) > 1 else None)):
            if not r: continue
            start = r['music_from']; out = os.path.join(a.ab, f'{tag} - {r["title"][:40]}.wav')
            subprocess.run([ff, '-v', 'error', '-y', '-ss', f'{start:.3f}', '-t', f'{a.len:.3f}', '-i', r['file'], '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', out], check=True)
            r['ab'] = out
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.out: json.dump(res, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    sys.exit(0 if ranked else 1)

if __name__ == '__main__': main()
