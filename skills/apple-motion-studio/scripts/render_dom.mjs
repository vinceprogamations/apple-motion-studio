// Render a DOM page (HTML/CSS, backdrop-filter, iframes) frame by frame: window.renderAt(t) then a CDP screenshot.
//   node render_dom.mjs stills <page.html> <outDir> <t1> <t2> ... [options]
//   node render_dom.mjs video  <page.html> <out.mp4> [options]
//   node render_dom.mjs events <page.html> <out.json> [options]
//   node render_dom.mjs check  <page.html> [options]           (gates only, no frames written)
// Options:
//   --root <dir>        folder served (must contain everything the page loads; default: the page's folder)
//   --fps 60            --w 1080 --h 1920 (CSS viewport)   --scale 1  (device scale factor: 2 = 2160x3840 native, not upscaled)
//   --from s --to s     render a time range       --png  lossless PNG intermediate (default JPEG q95)
//   --blur N            motion blur: N subquadros por quadro num obturador de 180° (média no ffmpeg). 4–8 em movimento rápido;
//                       custa N× o tempo. Subquadros nunca atravessam um corte (início de cena em TIMELINE.scenes).
//   --manifest <json>   asset manifest (default: asset-manifest.json next to the page, if present)
//   --gate strict|warn  asset gate mode (default strict for video/check, warn for stills/events)
//   --legacy "<motivo>" render a project made before the asset gate without a manifest (recorded in the report). A new film
//                       with no external assets uses an EMPTY manifest {"assets": []} instead; omitting the manifest fails.
//   --ready-timeout 60  seconds to wait for window.ready before failing
//   --allow-errors      do not fail on page errors / failed requests (exploration only)
//   --replace           allow overwriting an existing output (default: refuse; write a new version, promote with studio.py promote)
//   node render_dom.mjs layout <page.html> <outDir> [--times a,b,c]   composition QA by sampling (no video): at each instant reads
//        every element marked data-qa="<papel>" (headline, legenda, prova, cta…) in the page and its iframes, flags collisions
//        between different roles and required roles that vanish (data-qa-required="1" always, or "a-b" = must be visible in that window); compares the same frame reached by direct seek and by sequential
//        playback. Samples = --times, else the page's critical windows: TIMELINE.transitions [{from,to}] → every 2 frames + peak + last frame,
//        TIMELINE.critical [{from,to}] every 0.1 s, CAPTIONS lines → first/middle/last frame. 0 samples = insufficient coverage.
//   node render_dom.mjs timeline <page.html> <out.json>      (window.TIMELINE: scenes + intentional ranges, with fps, for qa_frames.py)
// Contract: window.renderAt(t), window.TOTAL, window.ready (rejects when a required asset fails), window.EVENTS.
// Video is written to <out>.tmp.mp4 and renamed only after every gate passed; an existing master is never touched on failure.
// A JSON report is written next to the output (<out>.report.json / <outDir>/report.json).
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, renameSync, unlinkSync, createReadStream } from 'node:fs';
import { resolve, dirname, relative, extname, join, sep } from 'node:path';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import { setTimeout as wait } from 'node:timers/promises';
import { findTool } from './lib/tools.mjs';

const argv = process.argv.slice(2), flag = n => { const i = argv.indexOf(n); if (i < 0) return null; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const bool = n => { const i = argv.indexOf(n); if (i < 0) return false; argv.splice(i, 1); return true; };
const FPS = +(flag('--fps') || 60), ROOT0 = flag('--root'), FROM = +(flag('--from') || 0), TO = flag('--to'), W = +(flag('--w') || 1080), H = +(flag('--h') || 1920);
const BLUR = Math.max(1, Math.round(+(flag('--blur') || 1))), SHUTTER = 0.5;
const LEGACY = flag('--legacy'), flagTimes = flag('--times'), REPLACE = bool('--replace'), SCALE = +(flag('--scale') || 1), PNG = bool('--png'), MANIFEST0 = flag('--manifest'), READY_S = +(flag('--ready-timeout') || 60), ALLOW_ERR = bool('--allow-errors');
const [mode, pageArg, out, ...rest] = argv;
const GATE = flag('--gate') || (['video', 'check'].includes(mode) ? 'strict' : 'warn');
if (!mode || !pageArg) { console.log(readFileSync(new URL(import.meta.url)).toString().split('\n').slice(0, 18).join('\n')); process.exit(2); }
const page = resolve(pageArg), ROOT = resolve(ROOT0 || dirname(page)), rel = relative(ROOT, page).split(sep).join('/');
const manifestPath = MANIFEST0 ? resolve(MANIFEST0) : (existsSync(join(dirname(page), 'asset-manifest.json')) ? join(dirname(page), 'asset-manifest.json') : null);
const report = { mode, page: rel, root: ROOT, fps: FPS, viewport: [W, H], scale: SCALE, pixels: [W * SCALE, H * SCALE], gate: GATE, manifest: manifestPath, started: new Date().toISOString(),
  errors: [], warnings: [], notes: [], assets: [], status: 'running' };
const CHROME = findTool('chrome'), FFMPEG = mode === 'video' ? findTool('ffmpeg') : null;

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2', '.json': 'application/json', '.mp4': 'video/mp4', '.webm': 'video/webm', '.glb': 'model/gltf-binary' };
const server = createServer((req, res) => { const p = join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  const type = TYPES[extname(p).toLowerCase()] || 'application/octet-stream', size = statSync(p).size, m = /bytes=(\d*)-(\d*)/.exec(req.headers.range || '');
  if (m) {   // byte ranges: <video> needs them to seek (footage inside DOM films)
    const a = m[1] ? +m[1] : size - +m[2], b = m[1] && m[2] ? Math.min(+m[2], size - 1) : size - 1;
    res.writeHead(206, { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Range': `bytes ${a}-${b}/${size}`, 'Content-Length': b - a + 1 });
    return createReadStream(p, { start: a, end: b }).pipe(res);
  }
  res.writeHead(200, { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Length': size }); createReadStream(p).pipe(res); });
await new Promise(r => server.listen(0, '127.0.0.1', r)); const HTTP = `http://127.0.0.1:${server.address().port}`;
const port = 9300 + (process.pid % 600), prof = join(tmpdir(), `dom-chrome-${port}`);
const chrome = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--enable-gpu', '--force-color-profile=srgb', `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
let tg; for (let i = 0; i < 160 && !tg; i++) { try { tg = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await wait(250); } }
if (!tg) { console.error('FAILED: Chrome não iniciou'); process.exit(1); }
const ws = new WebSocket(tg.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r); let mid = 0; const pend = new Map();
// ---------------------------------------------------------------- page error capture (exceptions, console errors, failed requests)
const pageErrors = []; const reqUrl = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data);
  if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); return; }
  const p = m.params || {};
  if (m.method === 'Runtime.exceptionThrown') pageErrors.push('exceção: ' + (p.exceptionDetails?.exception?.description || p.exceptionDetails?.text || '').split('\n')[0]);
  else if (m.method === 'Runtime.consoleAPICalled' && p.type === 'error') pageErrors.push('console.error: ' + (p.args || []).map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300));
  else if (m.method === 'Log.entryAdded' && p.entry?.level === 'error' && !/Failed to load resource/.test(p.entry.text)) pageErrors.push('log: ' + p.entry.text.slice(0, 300));
  else if (m.method === 'Network.requestWillBeSent') reqUrl.set(p.requestId, p.request.url);
  else if (m.method === 'Network.responseReceived' && p.response.status >= 400 && !/\/favicon\.ico$/.test(p.response.url)) pageErrors.push(`HTTP ${p.response.status}: ${p.response.url.replace(HTTP, '')}`);
  else if (m.method === 'Network.loadingFailed' && !p.canceled) pageErrors.push(`rede falhou (${p.errorText}): ${(reqUrl.get(p.requestId) || '').replace(HTTP, '')}`);
};
const send = (method, params = {}) => new Promise(r => { const i = ++mid; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async x => { const m = await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true });
  if (m.result?.exceptionDetails) throw new Error(m.result.exceptionDetails.exception?.description?.split('\n')[0] || m.result.exceptionDetails.text); return m.result.result.value; };
const reportPath = mode === 'video' ? resolve(out).replace(/\.mp4$/i, '') + '.report.json' : mode === 'stills' ? join(resolve(out), 'report.json') : null;
const done = c => { report.status = c === 0 ? 'ok' : 'failed'; report.finished = new Date().toISOString(); report.errors.push(...pageErrors.filter(x => !report.errors.includes(x)));
  if (reportPath) { mkdirSync(dirname(reportPath), { recursive: true }); writeFileSync(reportPath, JSON.stringify(report, null, 1)); }
  try { ws.close(); } catch {} chrome.kill(); server.close(); process.exit(c); };
const fail = (msg) => { console.error('FAILED: ' + msg); report.errors.push(msg);
  if (mode === 'video' && existsSync(resolve(out))) console.error(`master anterior preservado: ${out}`); done(1); };
const checkPageErrors = (where) => { if (pageErrors.length && !ALLOW_ERR) fail(`erros na página (${where}):\n  - ` + [...new Set(pageErrors)].join('\n  - ')); };
const shot = async () => (await send('Page.captureScreenshot', PNG ? { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 } } : { format: 'jpeg', quality: 95, clip: { x: 0, y: 0, width: W, height: H, scale: 1 } })).result.data;
let stage = 'início';   // where we are, prefixed to any failure message
const sha256 = f => createHash('sha256').update(readFileSync(f)).digest('hex');

// ---------------------------------------------------------------- asset gate: manifest vs files vs what the composition really shows
async function assetGate() {
  if (!manifestPath) {
    if (LEGACY) { report.legacy = LEGACY; report.warnings.push(`projeto legado sem manifesto (declarado: ${LEGACY}); portão de assets não aplicado`); console.warn('AVISO: ' + report.warnings.at(-1)); return; }
    if (GATE === 'strict' && ['video', 'check'].includes(mode)) fail('sem asset-manifest.json: o master não pode pular o portão de assets omitindo o manifesto → crie asset-manifest.json ao lado da página ({"assets": []} se o filme não usa fotos/imagens externas) ou, para projeto anterior ao portão, rode com --legacy "motivo"');
    report.notes.push('sem asset-manifest.json: portão de assets não aplicado (modo ' + GATE + ')'); return; }
  let man; try { man = JSON.parse(readFileSync(manifestPath, 'utf8')); } catch (e) { fail(`asset-manifest.json inválido (${e.message}) → corrija o JSON`); }
  if (!Array.isArray(man.assets)) fail('asset-manifest.json sem a lista "assets" → use {"assets": []} para um filme sem assets externos');
  const mdir = dirname(manifestPath), problems = [];
  if (!man.assets.length) report.notes.push('manifesto vazio: o filme declara não usar assets externos (vagas data-asset ainda são conferidas)');
  // every data-asset slot the composition shows must be declared (an empty manifest cannot hide a photo slot)
  { const declared = new Set(man.assets.map(a => a.slot || a.id)), seen = new Map();
    const probe = await ev(`(() => { const tot = window.TOTAL || 1, sc = window.studioScenes; const ts = sc ? sc.cuts.map((c, i) => (c + (sc.cuts[i + 1] ?? tot)) / 2) : [0, tot / 2, tot * 0.9]; return ts; })()`);
    for (const t of probe) {
      stage = `portão de assets (vagas declaradas, t=${(+t).toFixed(2)} s)`;
      const s = await ev(`(async () => { await renderAt(${t}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); return window.studioScenes ? window.studioScenes.slots(${t}) : { scene: null, slots: window.__studio ? window.__studio.slots() : [] }; })()`);
      for (const x of s.slots || []) if (!declared.has(x.id) && !x.optional) seen.set(x.id, s.scene || 'página');
    }
    for (const [id, sc] of seen) problems.push({ scene: sc, slot: id, file: '?', reason: 'vaga data-asset sem entrada no manifesto', fix: `declare "${id}" em asset-manifest.json (arquivo, licença, aprovação) ou remova o data-asset`, required: true });
  }
  const P = (a, reason, fix) => problems.push({ scene: a.scene, slot: a.slot || a.id, file: a.file, reason, fix, required: a.required !== false });
  for (const a of man.assets || []) {
    const fpath = a.file ? resolve(mdir, a.file) : null, row = { id: a.id, scene: a.scene, slot: a.slot || a.id, file: a.file, required: a.required !== false, checks: {} };
    report.assets.push(row);
    const optionalSkip = a.required === false && a.approval?.status === 'approved-without';
    if (!fpath || !existsSync(fpath)) {
      if (optionalSkip) { report.notes.push(`opcional omitido com aprovação: ${a.id} (${a.approval.scope || 'storyboard'})`); row.checks.file = 'omitido-aprovado'; continue; }
      P(a, 'arquivo não existe', `gere/obtenha o asset e salve em ${a.file} (status atual: ${a.status || '?'})`); row.checks.file = 'ausente'; continue; }
    row.checks.file = 'ok';
    if (a.sha256) { const h = sha256(fpath); row.checks.hash = h === a.sha256 ? 'ok' : 'mudou';
      if (h !== a.sha256) P(a, `arquivo mudou depois da aprovação (sha256 ${h.slice(0, 12)} ≠ ${a.sha256.slice(0, 12)})`, 'revise e reaprove: python scripts/assets.py approve <manifest> ' + a.id); }
    if (a.required !== false && !a.license) P(a, 'sem licença/uso permitido registrado', 'preencha "license" no manifesto');
    if (a.required !== false && a.approval?.status !== 'approved') P(a, `não aprovado (approval.status=${a.approval?.status || 'vazio'})`, 'mostre ao usuário e registre a aprovação com escopo');
  }
  // binding + coverage in time: render the declared instant and read what the slot really shows
  for (const a of man.assets || []) {
    if (!a.visible || !a.scene) continue;
    const row = report.assets.find(r => r.id === a.id); if (row.checks.file !== 'ok') continue;
    const times = [a.visible[0] + Math.min(0.15, (a.visible[1] - a.visible[0]) / 4), (a.visible[0] + a.visible[1]) / 2, a.visible[1] - Math.min(0.15, (a.visible[1] - a.visible[0]) / 4)];
    const expect = '/' + relative(ROOT, resolve(dirname(manifestPath), a.file)).split(sep).join('/');
    let best = null;
    for (const t of times) {
      stage = `portão de assets (cena ${a.scene}, vaga ${a.slot || a.id}, t=${t.toFixed(2)} s)`;
      const s = await ev(`(async () => { await renderAt(${t}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); return window.studioScenes ? window.studioScenes.slots(${t}) : { scene: null, slots: window.__studio ? window.__studio.slots() : null }; })()`);
      if (s.scene && s.scene !== a.scene) { P(a, `no instante ${t.toFixed(2)} s a cena ativa é ${s.scene}, não ${a.scene}`, 'corrija "visible" no manifesto ou o tempo da cena'); best = 'scene'; break; }
      const slot = (s.slots || []).find(x => x.id === (a.slot || a.id));
      if (!slot) { P(a, `a cena não tem elemento com data-asset="${a.slot || a.id}"`, 'marque o elemento da vaga com data-asset e use o arquivo do manifesto'); best = 'missing'; break; }
      const bound = slot.urls.some(u => decodeURIComponent(new URL(u, HTTP).pathname) === expect);
      if (!bound) { P(a, slot.gradient ? 'a vaga mostra um gradiente/cor, não a foto' : `a vaga mostra outro arquivo (${slot.urls.map(u => decodeURIComponent(new URL(u, HTTP).pathname)).join(', ') || 'nada'})`, `use background-image:url(${a.file}), <img src="${a.file}"> ou <video src="${a.file}"> no elemento data-asset="${a.slot || a.id}"`); best = 'unbound'; break; }
      const [x, y, w, h] = slot.rect, onScreen = w > 1 && h > 1 && x + w > 0 && y + h > 0 && x < W && y < H;
      const ok = onScreen && slot.opacity > 0.5; if (ok) best = best || { t, w, h, op: slot.opacity }; if (ok && w * h > (best.w * best.h)) best = { t, w, h, op: slot.opacity };
    }
    if (best && typeof best === 'object') {
      row.checks.bound = 'ok'; row.checks.visible = `t=${best.t.toFixed(2)}s ${Math.round(best.w)}x${Math.round(best.h)} css px, opacidade ${best.op.toFixed(2)}`;
      const loaded = await ev(`(() => { const out = []; const fr = [...document.querySelectorAll('iframe')]; const wins = fr.length ? fr.map(f => f.contentWindow) : [window];
        for (const w of wins) for (const x of (w.__studio ? w.__studio.assets : [])) out.push(x); return out; })()`);
      const info = loaded.find(x => decodeURIComponent(new URL(x.url, HTTP).pathname) === expect);
      if (!info || !info.ok) P(a, info && info.video ? 'o vídeo não decodificou no navegador (codec/arquivo inválido)' : 'a imagem não decodificou no navegador (arquivo corrompido ou formato inválido)', info && info.video ? 'gere um proxy H.264 all-intra (ver footage.js)' : 'substitua o arquivo');
      else { row.checks.pixels = `${info.w}x${info.h}`; const need = Math.max(best.w, best.h) * SCALE;
        // ampliação real, eixo a eixo (cover/contain e fotos verticais em tela cheia); a regra antiga min(lado) × max(tela) reprovava 9:16 com sobra
        const amp = Math.max(best.w * SCALE / info.w, best.h * SCALE / info.h);
        if (amp > 1 / 0.9) P(a, `resolução insuficiente: ${info.w}x${info.h} px ampliada ${amp.toFixed(2)}× para ~${Math.round(best.w * SCALE)}x${Math.round(best.h * SCALE)} px na tela (escala ${SCALE})`, 'gere/obtenha versão maior; ampliar não cria detalhe'); }
    } else if (best === null) P(a, `não aparece visível entre ${a.visible[0]} e ${a.visible[1]} s (fora da tela ou transparente)`, 'confira a animação e o intervalo "visible" no manifesto');
  }
  for (const p of problems) {
    const msg = `cena ${p.scene} · vaga ${p.slot} · arquivo ${p.file}: ${p.reason} → ${p.fix}`;
    if (p.required && GATE === 'strict') report.errors.push(msg); else report.warnings.push(msg);
  }
  const hard = problems.filter(p => p.required && GATE === 'strict');
  for (const wmsg of report.warnings) console.warn('AVISO: ' + wmsg);
  for (const n of report.notes) console.log('nota: ' + n);
  if (hard.length) fail(`portão de assets bloqueou (${hard.length}):\n  - ` + hard.map(p => `cena ${p.scene} · vaga ${p.slot} · ${p.file}: ${p.reason} → ${p.fix}`).join('\n  - '));
  console.log(`assets: ${report.assets.length} no manifesto, ${problems.length} problema(s), modo ${GATE}`);
}

try {
  stage = 'carregamento';
  await send('Runtime.enable'); await send('Log.enable'); await send('Network.enable'); await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: SCALE, mobile: false });
  await send('Page.navigate', { url: `${HTTP}/${rel}?t=0` });
  let has = false; for (let i = 0; i < 100 && !has; i++) { await wait(200); has = await ev('typeof window.renderAt === "function" && !!window.ready').catch(() => false); }
  if (!has) fail('a página não expôs window.renderAt e window.ready (contrato)');
  const r = await Promise.race([ev('Promise.resolve(window.ready).then(() => "ok", e => "REJECT:" + (e && e.message || e))'), wait(READY_S * 1000).then(() => 'TIMEOUT')]);
  if (r === 'TIMEOUT') fail(`window.ready não resolveu em ${READY_S} s` + (pageErrors.length ? ':\n  - ' + [...new Set(pageErrors)].join('\n  - ') : ''));
  if (r.startsWith('REJECT:')) fail('composição não ficou pronta: ' + r.slice(7) + (pageErrors.length ? '\n  - ' + [...new Set(pageErrors)].join('\n  - ') : ''));
  checkPageErrors('carregamento');
  stage = 'eventos/portão';
  if (mode === 'timeline') { const tl = await ev('JSON.stringify(Object.assign({ fps: ' + FPS + ' }, window.TIMELINE || { total: window.TOTAL, scenes: [{ id: "s1", start: 0, end: window.TOTAL }], intentional: [] }))'); writeFileSync(out, tl); console.log('timeline ->', out); done(0); }
  if (mode === 'events') { writeFileSync(out, await ev('JSON.stringify(window.EVENTS || [])')); console.log('events ->', out); done(0); }
  const frame = async t => { await ev(`(async () => { await renderAt(${t}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); return 1; })()`); return Buffer.from(await shot(), 'base64'); };
  if (mode === 'layout') {
    stage = 'QA de composição'; mkdirSync(out, { recursive: true });
    const TIMES = flagTimes ? flagTimes.split(',').filter(Boolean).map(Number) : JSON.parse(await ev(`JSON.stringify((() => { const T = window.TIMELINE || {}, out = [], f = 1 / ${FPS};
      for (const x of T.transitions || []) { for (let t = x.from; t < x.to - 1e-9; t += 2 * f) out.push(t); out.push((x.from + x.to) / 2, x.to - f); }   // start/peak/end alone missed a mid-transition collision (test 13): every 2 frames
      for (const x of T.critical || []) for (let t = x.from; t <= x.to + 1e-9; t += 0.1) out.push(+t.toFixed(3));
      for (const c of (window.CAPTIONS && window.CAPTIONS.lines) || []) out.push(c.start, (c.start + c.end) / 2, c.end - f);
      return [...new Set(out.map(t => +t.toFixed(4)))].sort((a, b) => a - b); })())`));
    const rep = { samples: TIMES.length, instants: TIMES, collisions: [], vanished: [], seek_vs_sequential: [] };
    if (!TIMES.length) { rep.result = 'COBERTURA INSUFICIENTE'; writeFileSync(join(out, 'layout.json'), JSON.stringify(rep, null, 1)); fail('QA de composição: 0 amostras inspecionadas — cobertura insuficiente (declare TIMELINE.transitions / critical / CAPTIONS ou passe --times); "zero erros" sem amostras não vale'); }
    const boxes = async t => JSON.parse(await ev(`(async () => { await renderAt(${t}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
      const out = [], vis = (el, w) => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const cs = w.getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; } return o; };
      const walk = (doc, w, ox, oy) => { for (const el of doc.querySelectorAll('[data-qa]')) { const r = el.getBoundingClientRect(); out.push({ role: el.dataset.qa, text: (el.innerText || '').slice(0, 40), x: r.x + ox, y: r.y + oy, w: r.width, h: r.height, op: vis(el, w), required: (q => q === '1' || (/^[\d.]+-[\d.]+$/.test(q || '') && ${t} >= +q.split('-')[0] && ${t} <= +q.split('-')[1]))(el.dataset.qaRequired) }); }
        for (const f of doc.querySelectorAll('iframe')) { try { const r = f.getBoundingClientRect(); if (+w.getComputedStyle(f).opacity > 0.01) walk(f.contentDocument, f.contentWindow, ox + r.x, oy + r.y); } catch (e) {} } };
      walk(document, window, 0, 0); return JSON.stringify(out); })()`));
    for (const t of TIMES) {
      const B = (await boxes(t)).filter(b => b.w > 1 && b.h > 1);
      const shown = B.filter(b => b.op > 0.15 && b.x < W && b.y < H && b.x + b.w > 0 && b.y + b.h > 0);
      for (let i = 0; i < shown.length; i++) for (let j = i + 1; j < shown.length; j++) { const a = shown[i], b = shown[j]; if (a.role === b.role) continue;
        const ix = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)), iy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y)), area = ix * iy;
        if (area > 0.02 * Math.min(a.w * a.h, b.w * b.h)) rep.collisions.push({ t, a: a.role, b: b.role, overlap_px: Math.round(area), a_text: a.text, b_text: b.text }); }
      for (const b of B.filter(b => b.required && b.op <= 0.15)) rep.vanished.push({ t, role: b.role, text: b.text });
    }
    // same frame by direct seek vs sequential playback (state leaking between frames shows up here)
    for (const t of TIMES.slice(0, Math.min(3, TIMES.length))) {
      await frame(Math.max(0, t + 3)); const seek = await frame(t);
      for (let f = Math.max(0, Math.round((t - 0.5) * FPS)); f < Math.round(t * FPS); f++) await frame(f / FPS); const seq = await frame(t);
      const a = join(out, `seek-${t.toFixed(3)}.${PNG ? 'png' : 'jpg'}`), b = join(out, `seq-${t.toFixed(3)}.${PNG ? 'png' : 'jpg'}`); writeFileSync(a, seek); writeFileSync(b, seq);
      rep.seek_vs_sequential.push({ t, identical_bytes: seek.equals(seq), seek: a, sequential: b });
    }
    rep.result = rep.collisions.length || rep.vanished.length ? 'PROBLEMA' : 'OK'; writeFileSync(join(out, 'layout.json'), JSON.stringify(rep, null, 1));
    console.log(`QA de composição: ${rep.samples} amostras (${TIMES.map(t => t.toFixed(2)).join(', ')})`);
    for (const c of rep.collisions) console.log(`  COLISÃO t=${c.t.toFixed(3)} s: ${c.a} × ${c.b} (${c.overlap_px} px²) "${c.a_text}" / "${c.b_text}"`);
    for (const v of rep.vanished) console.log(`  SUMIU t=${v.t.toFixed(3)} s: ${v.role} "${v.text}"`);
    for (const x of rep.seek_vs_sequential) console.log(`  salto × sequência t=${x.t.toFixed(3)} s: ${x.identical_bytes ? 'idênticos' : 'DIFERENTES (compare os arquivos)'}`);
    done(rep.result === 'OK' ? 0 : 1);
  }
  await assetGate();
  if (mode === 'check') { console.log('check ok'); done(0); }
  if (mode === 'stills') { mkdirSync(out, { recursive: true }); for (const t of rest.map(Number)) writeFileSync(join(out, `${t.toFixed(2)}.${PNG ? 'png' : 'jpg'}`), await frame(t)); checkPageErrors('stills'); console.log('stills ->', out); done(0); }
  if (mode !== 'video') fail('modo desconhecido: ' + mode);
  if (existsSync(resolve(out)) && !REPLACE) fail(`${out} já existe: grave uma nova versão (ex.: "… v2.mp4") ou passe --replace; promova o master com: python scripts/studio.py promote <render> <master>`);
  const total = TO ? +TO : await ev('window.TOTAL'), n0 = Math.round(FROM * FPS), n1 = Math.round(total * FPS), t0 = Date.now(), tmp = resolve(out).replace(/\.mp4$/i, '') + '.tmp.mp4';
  report.frames = n1 - n0; report.duration = (n1 - n0) / FPS;
  mkdirSync(dirname(resolve(out)), { recursive: true });
  const CUTS = BLUR > 1 ? JSON.parse(await ev('JSON.stringify(((window.TIMELINE && window.TIMELINE.scenes) || []).map(s => s.start).filter(x => x > 0))')) : [];
  report.blur = BLUR > 1 ? { subframes: BLUR, shutter: SHUTTER * 360, cuts: CUTS.length } : null;
  const subT = (tc, k) => { let ts = tc + ((k + 0.5) / BLUR - 0.5) * SHUTTER / FPS; for (const c of CUTS) { if (tc < c && ts >= c) ts = c - 1e-4; if (tc >= c && ts < c) ts = c; } return Math.max(0, ts); };
  const blurVf = BLUR > 1 ? `tmix=frames=${BLUR},select='eq(mod(n\\,${BLUR})\\,${BLUR - 1})',setpts=N/${FPS}/TB,` : '';
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * BLUR), '-c:v', PNG ? 'png' : 'mjpeg', '-i', '-',
    '-vf', blurVf + (PNG ? 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv'   // RGB in -> BT.709 limited; setparams so primaries/transfer are tagged too
               : 'colorspace=space=bt709:trc=bt709:primaries=bt709:range=tv:ispace=bt470bg:itrc=bt709:iprimaries=bt709:irange=pc:format=yuv420p'),   // JPEG (BT.601 full) -> BT.709 limited
    '-r', String(FPS),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-movflags', '+faststart', tmp], { stdio: ['pipe', 'ignore', 'pipe'] });
  let err = ''; ff.stderr.on('data', d => err += d); const fin = new Promise((ok, no) => ff.on('close', c => c === 0 ? ok() : no(new Error(err || 'ffmpeg failed'))));
  try {
    for (let f = n0; f < n1; f++) { for (let k = 0; k < BLUR; k++) { const tk = BLUR > 1 ? subT(f / FPS, k) : f / FPS; const b = await frame(tk).catch(e => { throw new Error(`quadro ${f} (t=${tk.toFixed(3)} s): ${e.message}`); }); if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r)); }
      if (pageErrors.length && !ALLOW_ERR) throw new Error(`erro na página no quadro ${f} (t=${(f / FPS).toFixed(3)} s): ${pageErrors[0]}`);
      if (f % (FPS * 2) === 0) process.stdout.write(`\r${f}/${n1} frames ${((Date.now() - t0) / 1000).toFixed(0)}s`); }
    ff.stdin.end(); await fin;
  } catch (e) { try { ff.stdin.destroy(); ff.kill(); } catch {} await wait(300); try { if (existsSync(tmp)) unlinkSync(tmp); } catch {} fail(e.message); }
  renameSync(tmp, resolve(out)); report.output = out;
  if (!TO && !FROM) { const tl = await ev('JSON.stringify(Object.assign({ fps: ' + FPS + ' }, window.TIMELINE || { total: window.TOTAL, scenes: [{ id: "s1", start: 0, end: window.TOTAL }], intentional: [] }))'); writeFileSync(resolve(out).replace(/\.mp4$/i, '') + '.timeline.json', tl); } report.seconds = (Date.now() - t0) / 1000;
  console.log(`\nSAVED ${out} (${n1 - n0} frames, ${W * SCALE}x${H * SCALE}, ${report.seconds.toFixed(0)} s)`); done(0);
} catch (e) { fail(`${stage}: ${e.message}`); }
