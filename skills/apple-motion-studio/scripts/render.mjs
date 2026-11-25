// Render an animation page to stills or a video. Self-contained: it serves the page's folder itself, drives headless
// Chrome frame by frame (window.renderAt(t) on canvas #c) and pipes the frames to ffmpeg.
//
//   node render.mjs stills <page.html> <outDir> <t1> <t2> ...  [--gpu] [--root <dir>]
//   node render.mjs video  <page.html> <out.mp4> [--fps 24] [--scale 2] [--gpu] [--root <dir>] [--audio <file.wav>] [--alpha]
//   node render.mjs events <page.html> <out.json> [--gpu]   (writes the page's window.EVENTS: [{name, t}], for sound sync)
//   node render.mjs dump   <page.html> <out.bin>  [--gpu]   (writes the bytes of `await window.dump()` (base64), e.g. a GLB export for Blender)
//
//   --gpu    real GPU (needed for WebGL / 3D pages; without it headless Chrome has no WebGL2)
//   --scale  2 = 4K (3840x2160) from a 1920x1080 page that reads ?scale=
//   --root   folder to serve (default: the page's own folder; use the project root if the page loads ../ files)
//   --alpha  ProRes 4444 .mov with transparency (the page must leave its background clear)
// Needs: Node 18+, ffmpeg on PATH, Google Chrome or Chromium (set CHROME=/path if it isn't found).
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, renameSync, unlinkSync } from 'node:fs';
import { resolve, dirname, relative, extname, join, sep } from 'node:path';
import { tmpdir } from 'node:os';
import { setTimeout as wait } from 'node:timers/promises';
import { findTool } from './lib/tools.mjs';

const argv = process.argv.slice(2), flag = n => { const i = argv.indexOf(n); if (i < 0) return null; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const bool = n => { const i = argv.indexOf(n); if (i < 0) return false; argv.splice(i, 1); return true; };
const GPU = bool('--gpu'), ALPHA = bool('--alpha'), FPS = +(flag('--fps') || 24), SCALE = +(flag('--scale') || 2), ROOT0 = flag('--root'), AUDIO = flag('--audio');
const [mode, pageArg, out, ...rest] = argv;
if (!mode || !pageArg || !out) { console.log(readFileSync(new URL(import.meta.url)).toString().split('\n').slice(0, 15).join('\n')); process.exit(1); }
const page = resolve(pageArg), ROOT = resolve(ROOT0 || dirname(page)), rel = relative(ROOT, page).split(sep).join('/');

const CHROME = findTool('chrome'), FFMPEG = findTool('ffmpeg');
if (!CHROME) { console.error('Chrome not found: set CHROME=/path/to/chrome'); process.exit(1); }

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2', '.json': 'application/json', '.mp4': 'video/mp4', '.wav': 'audio/wav', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json' };
const server = createServer((req, res) => {   // a tiny static server, so fonts / images / modules load like on a real site
  const p = join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !existsSync(p) || statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[extname(p).toLowerCase()] || 'application/octet-stream' }); res.end(readFileSync(p));
});
await new Promise(r => server.listen(0, '127.0.0.1', r)); const HTTP = `http://127.0.0.1:${server.address().port}`;

const port = 9300 + (process.pid % 600), prof = join(tmpdir(), `smad-chrome-${port}`);
const chrome = spawn(CHROME, ['--headless=new', ...(GPU ? ['--enable-gpu', ...(process.platform === 'darwin' ? ['--use-angle=metal'] : [])] : ['--disable-gpu']), '--hide-scrollbars',
  `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, '--window-size=1920,1080', 'about:blank'], { stdio: 'ignore' });
let tg; for (let i = 0; i < 160 && !tg; i++) { try { tg = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await wait(250); } }
if (!tg) { console.error('Chrome did not start'); process.exit(1); }
const ws = new WebSocket(tg.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r); let mid = 0; const pend = new Map();
// page errors (exceptions, console.error, failed requests) fail the render instead of producing a silently wrong video
const pageErrors = [], reqUrl = new Map(), READY_S = +(process.env.READY_TIMEOUT || 60), ALLOW_ERR = process.argv.includes('--allow-errors');
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); return; } const p = m.params || {};
  if (m.method === 'Runtime.exceptionThrown') pageErrors.push('exceção: ' + (p.exceptionDetails?.exception?.description || p.exceptionDetails?.text || '').split('\n')[0]);
  else if (m.method === 'Runtime.consoleAPICalled' && p.type === 'error') pageErrors.push('console.error: ' + (p.args || []).map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300));
  else if (m.method === 'Network.requestWillBeSent') reqUrl.set(p.requestId, p.request.url);
  else if (m.method === 'Network.responseReceived' && p.response.status >= 400 && !/\/favicon\.ico$/.test(p.response.url)) pageErrors.push(`HTTP ${p.response.status}: ${p.response.url.replace(HTTP, '')}`);
  else if (m.method === 'Network.loadingFailed' && !p.canceled) pageErrors.push(`rede falhou (${p.errorText}): ${(reqUrl.get(p.requestId) || '').replace(HTTP, '')}`); };
const send = (method, params = {}) => new Promise(r => { const i = ++mid; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async x => { const m = await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true }); if (m.result?.exceptionDetails) throw new Error(m.result.exceptionDetails.exception?.description?.split('\n')[0] || m.result.exceptionDetails.text); return m.result.result.value; };
const pageErrorsCheck = where => { if (pageErrors.length && !ALLOW_ERR) throw new Error(`erros na página (${where}):\n  - ` + [...new Set(pageErrors)].join('\n  - ')); };
const done = code => { try { ws.close(); } catch {} chrome.kill(); server.close(); process.exit(code); };

try {
  const sc = mode === 'stills' ? 1 : SCALE;
  await send('Runtime.enable'); await send('Network.enable');
  await send('Page.navigate', { url: `${HTTP}/${rel}?t=0&scale=${sc}` });
  let has = false; for (let i = 0; i < 80 && !has; i++) { await wait(400); has = await ev('typeof window.renderAt === "function" && typeof window.ready !== "undefined"').catch(() => false); }
  if (!has) throw new Error('a página não expôs window.renderAt e window.ready (contrato)' + (pageErrors.length ? ': ' + pageErrors.join(' | ') : ''));
  const rd = await Promise.race([ev('Promise.resolve(window.ready).then(() => "ok", e => "REJECT:" + (e && e.message || e))'), wait(READY_S * 1000).then(() => 'TIMEOUT')]);
  if (rd === 'TIMEOUT') throw new Error(`window.ready não resolveu em ${READY_S} s` + (pageErrors.length ? ': ' + pageErrors.join(' | ') : ''));
  if (rd.startsWith('REJECT:')) throw new Error('composição não ficou pronta: ' + rd.slice(7));
  pageErrorsCheck('carregamento');
  if (mode === 'events') { const evs = await ev('JSON.stringify(window.EVENTS || [])'); writeFileSync(out, evs); console.log(`${JSON.parse(evs).length} events -> ${out}`); done(0); }
  if (mode === 'dump') {
    const b = await ev('(async () => { if (typeof window.dump !== "function") throw new Error("a página não expõe window.dump()"); return await window.dump(); })()');
    writeFileSync(out, Buffer.from(b, 'base64')); pageErrorsCheck('dump'); console.log(`${Buffer.byteLength(b, 'base64')} bytes -> ${out}`); done(0);
  }
  if (mode === 'stills') {
    mkdirSync(out, { recursive: true });
    for (const t of rest.map(Number)) { const b = await ev(`(async()=>{ await renderAt(${t}); return document.getElementById('c').toDataURL('image/jpeg', 0.88).split(',')[1]; })()`); writeFileSync(join(out, `${t.toFixed(2)}.jpg`), Buffer.from(b, 'base64')); }
    pageErrorsCheck('stills'); console.log(`stills -> ${out}`); done(0);
  }
  const total = await ev('window.TOTAL'), n = Math.round(total * FPS), t0 = Date.now(), tmp = resolve(out).replace(/(\.[a-z0-9]+)$/i, '.tmp$1');
  const venc = ALPHA ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0'] : ['-vf', 'colorspace=space=bt709:trc=bt709:primaries=bt709:range=tv:ispace=bt470bg:itrc=bt709:iprimaries=bt709:irange=pc:format=yuv420p',   // JPEG frames are BT.601 full range; swscale can't change the matrix yuv→yuv, this filter can (checked: ±1 level)
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
       '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart'];   // BT.709, tagged (apple-motion-studio)
  const aud = AUDIO ? ['-i', AUDIO, '-map', '0:v', '-map', '1:a', ...(ALPHA ? ['-c:a', 'pcm_s16le'] : ['-c:a', 'aac', '-b:a', '320k'])] : [];
  mkdirSync(dirname(resolve(out)), { recursive: true });
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', ALPHA ? 'png' : 'mjpeg', '-i', '-', ...aud, ...venc, '-t', String(n / FPS), tmp], { stdio: ['pipe', 'ignore', 'pipe'] });
  let err = ''; ff.stderr.on('data', d => err += d); const fin = new Promise((ok, no) => ff.on('close', c => c === 0 ? ok() : no(new Error(err || 'ffmpeg failed'))));
  const type = ALPHA ? "'image/png'" : "'image/jpeg', 0.95";
  try { for (let f = 0; f < n; f++) {
    const len = await ev(`(async () => { await renderAt(${f / FPS}); window.__f = document.getElementById('c').toDataURL(${type}).split(',')[1]; return window.__f.length; })()`).catch(e => { throw new Error(`quadro ${f} (t=${(f / FPS).toFixed(3)} s): ${e.message}`); });
    pageErrorsCheck(`quadro ${f}`);
    let b64 = ''; for (let o = 0; o < len; o += 4e6) b64 += await ev(`window.__f.slice(${o}, ${o + 4e6})`);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 2) === 0) process.stdout.write(`\r${f}/${n} frames`);
  }
  ff.stdin.end(); await fin; } catch (e) { try { ff.stdin.destroy(); ff.kill(); } catch {} await wait(300); try { if (existsSync(tmp)) unlinkSync(tmp); } catch {} if (existsSync(resolve(out))) console.error(`master anterior preservado: ${out}`); throw e; }
  renameSync(tmp, resolve(out));
  const tl = await ev('JSON.stringify(window.TIMELINE || null)').catch(() => 'null');   // canvas pages may declare scenes + intentional black/hold for qa_frames.py
  if (tl !== 'null') writeFileSync(resolve(out).replace(/\.[a-z0-9]+$/i, '.timeline.json'), JSON.stringify({ fps: FPS, ...JSON.parse(tl) }, null, 1));
  console.log(`\nSAVED ${out} (${n} frames at ${FPS} fps, ${((Date.now() - t0) / 60000).toFixed(1)} min)`); done(0);
} catch (e) { console.error('FAILED:', e.message); done(1); }
