// apple-motion-studio — animation kit for DOM scenes. Every scene page exposes window.anim(lt) (lt = local seconds) and is
// a pure function of time: no timers, no CSS transitions, no random without seed.
const clamp01 = v => Math.max(0, Math.min(1, v)), lerp = (a, b, k) => a + (b - a) * k, prog = (t, a, b) => clamp01((t - a) / (b - a));
const outExpo = k => (k = clamp01(k)) >= 1 ? 1 : 1 - Math.pow(2, -10 * k), outCubic = k => 1 - Math.pow(1 - clamp01(k), 3);
const inOutCubic = k => { k = clamp01(k); return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; }, sine = k => 0.5 - 0.5 * Math.cos(Math.PI * clamp01(k));
const inCubic = k => Math.pow(clamp01(k), 3);
// damped spring, step 0 -> 1. f = frequency (Hz), z = damping ratio. Heavy: f 1.0, z .7 | UI pop: f 2.3, z .45 (visible overshoot)
// springs come from the single implementation templates/motion-core.js (load it BEFORE anim.js); spr() keeps its old signature
if (!window.MotionCore) throw new Error('anim.js: inclua templates/motion-core.js antes de anim.js');
const spr = (t, f = 1.6, z = 0.75) => MotionCore.value(t, MotionCore.freq(f, z));   // identical to the old closed form (tests/run_springs.mjs)
const SP = { heavy: [1.0, 0.72], soft: [1.5, 0.82], ui: [2.3, 0.45], snap: [2.6, 0.6], cam: [0.7, 1] };
const sp = (t, k = 'soft') => spr(t, ...SP[k]);
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
// keep each element's authored transform and add motion on top of it
function base(el) { if (el.dataset.b === undefined) el.dataset.b = el.style.transform || ''; return el.dataset.b; }
function setT(el, extra, o) { el.style.transform = ((extra || '') + ' ' + base(el)).trim(); if (o !== undefined) el.style.opacity = o; }
// pop-in: scale from s0 with spring overshoot, opacity in over 0.2 s, blur 10 -> 0, small settling offset/rotation
function pop(el, lt, t0, o = {}) {
  if (!el) return; const k = sp(lt - t0, o.spring || 'ui'), a = clamp01((lt - t0) / 0.2), b = (1 - outCubic((lt - t0) / 0.35)) * (o.blur ?? 10);
  const s = lerp(o.s0 ?? 0.45, 1, k), dy = (1 - k) * (o.dy ?? 40), rot = (1 - k) * (o.rot ?? 4);
  let out = 1, sx = 1, oy = 0; if (o.out != null) { const q = inCubic((lt - o.out) / (o.outDur || 0.35)); out = 1 - q; oy = -q * 40; sx = 1 - 0.1 * q; }
  setT(el, `translate(${o.dx ? (1 - k) * o.dx : 0}px, ${dy + oy}px) rotate(${rot}deg) scale(${s * sx})`, a * out * (o.alpha ?? 1));
  el.style.filter = (b + (o.out != null ? (1 - out) * 12 : 0)) > 0.2 ? `blur(${b + (o.out != null ? (1 - out) * 12 : 0)}px)` : (o.keepFilter || 'none');
  el.style.visibility = lt < t0 ? 'hidden' : 'visible';
}
// words: split once into spans; each rises .5em, fades in, un-blurs 16px -> 0 (ease-out-expo .9 s), stagger 60 ms; exit reverses with blur
function split(el) { if (el.dataset.split) return; el.dataset.split = 1;
  const walk = n => [...n.childNodes].forEach(c => { if (c.nodeType === 3) { const f = document.createDocumentFragment();
      c.textContent.split(/(\s+)/).forEach(w => { if (!w) return; if (/^\s+$/.test(w)) f.appendChild(document.createTextNode(w)); else { const s = document.createElement('span'); s.className = 'w'; s.textContent = w; s.style.display = 'inline-block'; f.appendChild(s); } });
      c.replaceWith(f); } else if (c.nodeType === 1 && c.tagName !== 'BR') walk(c); });
  walk(el); }
function words(el, lt, tIn, tOut, o = {}) { if (!el) return; split(el); const ws = [...el.querySelectorAll('.w')], st = o.stagger ?? 0.06;
  ws.forEach((w, i) => { const ki = outExpo((lt - tIn - i * st) / 0.9), ko = tOut == null ? 0 : inCubic((lt - tOut - i * 0.03) / 0.4), a = ki * (1 - ko);
    w.style.opacity = a; w.style.transform = `translateY(${(1 - ki) * 0.5 - ko * 0.35}em)`; const bl = (1 - ki) * 16 + ko * 14; w.style.filter = bl > 0.2 ? `blur(${bl}px)` : 'none'; }); }
// typewriter
function typeText(el, full, lt, t0, cps = 22) { const n = Math.max(0, Math.min(full.length, Math.floor((lt - t0) * cps))); el.textContent = full.slice(0, n); return n >= full.length; }
// count up
function count(el, lt, t0, t1, a, b, fmt = v => Math.round(v).toLocaleString('pt-BR')) { el.textContent = fmt(lerp(a, b, outCubic(prog(lt, t0, t1)))); }
// touch circle: appears (spring), presses (squish), ripple ring, leaves. Needs a sibling .ripple created on demand.
function touch(el, lt, tA, tP, o = {}) { if (!el) return; base(el);
  const kin = sp(lt - tA, 'snap'), kout = sine(prog(lt, tP + 0.25, tP + 0.55)), press = lt < tP ? 0 : (lt < tP + 0.08 ? sine((lt - tP) / 0.08) : 1 - sp(lt - tP - 0.08, 'snap'));
  const vis = lt >= tA && kout < 1; el.style.visibility = vis ? 'visible' : 'hidden';
  const dx = (1 - outCubic(prog(lt, tA, tP))) * (o.fromX ?? 60), dy = (1 - outCubic(prog(lt, tA, tP))) * (o.fromY ?? 90);
  setT(el, `translate(${dx}px, ${dy}px) scale(${(0.6 + 0.4 * clamp01(kin)) * (1 - 0.22 * press)})`, clamp01(kin * 1.5) * (1 - kout));
  let r = el._rip; if (!r) { r = el._rip = document.createElement('div'); r.className = 'ripple'; el.parentNode.appendChild(r); }
  const rk = prog(lt, tP, tP + 0.7); r.style.left = el.style.left; r.style.top = el.style.top; r.style.zIndex = 12;
  r.style.visibility = rk > 0 && rk < 1 ? 'visible' : 'hidden'; r.style.opacity = 0.7 * (1 - rk); r.style.transform = `scale(${0.4 + 2.6 * outCubic(rk)})`; }
// button squish when pressed at tP
const squish = (lt, tP) => lt < tP ? 1 : 1 - 0.07 * Math.sin(Math.PI * clamp01((lt - tP) / 0.16)) + 0.03 * Math.sin(Math.PI * clamp01((lt - tP - 0.16) / 0.3));
// idle drift: sum of slow sines (deterministic per seed)
const drift = (t, s, amp = 1) => amp * (Math.sin(t * 0.7 + s * 1.7) * 0.6 + Math.sin(t * 1.13 + s * 3.1) * 0.4);
// haptic wiggle at tH
const wiggle = (lt, tH) => { const k = lt - tH; return k < 0 || k > 0.35 ? 0 : Math.sin(k * 90) * 2.2 * (1 - k / 0.35); };
// particle burst (seeded) into a container, at (x,y)
function burst(host, key, x, y, lt, t0, n = 12, color = '#fff') { let ps = host[key]; if (!ps) { ps = host[key] = []; let s = 77; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < n; i++) { const d = document.createElement('div'); d.className = 'pt'; d.style.background = color; host.appendChild(d); ps.push({ d, a: i / n * 6.283 + r() * 0.4, v: 120 + r() * 140, s: 6 + r() * 10 }); } }
  const k = prog(lt, t0, t0 + 0.8); ps.forEach(p => { const e = outCubic(k); p.d.style.visibility = k > 0 && k < 1 ? 'visible' : 'hidden';
    p.d.style.left = (x + Math.cos(p.a) * p.v * e) + 'px'; p.d.style.top = (y + Math.sin(p.a) * p.v * e + 60 * k * k) + 'px'; p.d.style.width = p.d.style.height = p.s * (1 - k * 0.6) + 'px'; p.d.style.opacity = 1 - k; }); }
// shared CSS for runtime helpers
document.head.insertAdjacentHTML('beforeend', `<style>.ripple{position:absolute;width:92px;height:92px;margin:-46px 0 0 -46px;border-radius:50%;corner-shape:round;border:3px solid rgba(255,255,255,.9);pointer-events:none}
.hl,.tagline{background:none!important}.hl .w,.tagline .w{background:linear-gradient(180deg,#fff 0%,#fff 58%,#a7a9b0 100%);-webkit-background-clip:text;background-clip:text;color:transparent;padding-bottom:.08em}
.pt{position:absolute;border-radius:50%;corner-shape:round;margin:-5px 0 0 -5px;box-shadow:0 0 12px rgba(255,255,255,.8);z-index:13}.touch{visibility:hidden}</style>`);
// the dots progress bar and the marquee are global ambience
function ambience(lt) { $$('.marq').forEach((m, i) => setT(m, `translateX(${(i % 2 ? 1 : -1) * lt * 60}px)`)); }
// ---------------------------------------------------------------- readiness (asset-aware)
// A scene is ready only when every font, <img> and CSS background image it uses has really decoded (naturalWidth > 0).
// A failed load REJECTS ready (it used to resolve it). Elements marked data-optional only warn.
// window.__studio exposes what was loaded, the failures, page errors and slots(): the renderer's asset gate reads it.
window.__studio = { assets: [], failures: [], warnings: [], errors: [] };
addEventListener('error', e => { if (e.target === window || !e.target || !e.target.tagName) __studio.errors.push(`${e.message || 'error'} @ ${e.filename || ''}:${e.lineno || ''}`); else __studio.failures.push({ url: e.target.src || e.target.href || '', reason: 'falha ao carregar ' + e.target.tagName.toLowerCase() }); }, true);
addEventListener('unhandledrejection', e => __studio.errors.push('promise rejeitada: ' + (e.reason && e.reason.message || e.reason)));
// url("…") / url('…') / url(…) in the computed background-image; data: URIs are inline (and may contain url(%23id) inside) -> skipped
function cssUrls(el) { const out = []; const bg = getComputedStyle(el).backgroundImage; if (!bg || bg === 'none') return out;
  for (const m of bg.matchAll(/url\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|([^)\s]*))\s*\)/g)) { const u = m[1] ?? m[2] ?? m[3]; if (u && !u.startsWith('data:')) out.push(u); }
  return out; }
function slotOf(el) { const s = el.closest('[data-asset]'); return s ? s.getAttribute('data-asset') : null; }
function loadCheck(url, el) { return new Promise(res => { const i = new Image(); i.onload = () => res({ url, ok: i.naturalWidth > 0, w: i.naturalWidth, h: i.naturalHeight });
  i.onerror = () => res({ url, ok: false, w: 0, h: 0 }); i.src = url; }).then(r => Object.assign(r, { slot: slotOf(el), optional: !!el.closest('[data-optional]') })); }
async function studioReady() {
  await document.fonts.ready;
  const fontFails = [...document.fonts].filter(f => f.status === 'error').map(f => f.family);
  fontFails.forEach(f => __studio.failures.push({ url: 'font:' + f, reason: 'fonte não carregou' }));
  const jobs = [];
  for (const img of document.images) jobs.push(img.decode().then(() => ({ url: img.currentSrc || img.src, ok: img.naturalWidth > 0, w: img.naturalWidth, h: img.naturalHeight }),
    () => ({ url: img.currentSrc || img.src, ok: false, w: 0, h: 0 })).then(r => Object.assign(r, { slot: slotOf(img), optional: !!img.closest('[data-optional]') })));
  const seen = new Set(); for (const el of document.querySelectorAll('body *')) for (const u of cssUrls(el)) { const key = u + '|' + (slotOf(el) || ''); if (!seen.has(key)) { seen.add(key); jobs.push(loadCheck(u, el)); } }
  // vídeos (<video> de filmagem/banco): valem como asset; prontos quando o primeiro quadro decodifica (vaga data-asset de vídeo)
  for (const v of document.querySelectorAll('video')) jobs.push(new Promise(res => {
    const done = () => res({ url: v.currentSrc || v.src, ok: v.videoWidth > 0, w: v.videoWidth, h: v.videoHeight, video: true });
    if (v.readyState >= 2) return done(); v.addEventListener('loadeddata', done, { once: true }); v.addEventListener('error', done, { once: true });
    setTimeout(done, 15000); if (v.preload === 'none') v.preload = 'auto'; v.load && v.readyState === 0 && v.load();
  }).then(r => Object.assign(r, { slot: slotOf(v), optional: !!v.closest('[data-optional]') })));
  __studio.assets = await Promise.all(jobs);
  for (const a of __studio.assets) if (!a.ok) (a.optional ? __studio.warnings : __studio.failures).push({ url: a.url, slot: a.slot, reason: 'imagem não carregou ou não decodificou' + (a.optional ? ' (opcional)' : '') });
  if (__studio.failures.length || __studio.errors.length)
    throw new Error(`${location.pathname.split('/').pop()}: ` + [...__studio.failures.map(f => `${f.slot ? 'vaga ' + f.slot + ': ' : ''}${f.reason} — ${f.url}`), ...__studio.errors].join(' | '));
  return true;
}
// what each asset slot ([data-asset]) currently shows: used by the renderer to prove the photo is bound and visible
__studio.slots = () => [...document.querySelectorAll('[data-asset]')].map(el => {
  const r = el.getBoundingClientRect(), urls = ['IMG', 'VIDEO'].includes(el.tagName) ? [el.currentSrc || el.src] : [...cssUrls(el), ...[...el.querySelectorAll('img, video')].map(i => i.currentSrc || i.src)];
  let op = 1, n = el; while (n && n.nodeType === 1) { const cs = getComputedStyle(n); op *= parseFloat(cs.opacity); if (cs.visibility === 'hidden' || cs.display === 'none') op = 0; n = n.parentElement; }
  const bg = getComputedStyle(el).backgroundImage;
  return { id: el.getAttribute('data-asset'), urls, gradient: /gradient\(/.test(bg) && !urls.length, rect: [r.left, r.top, r.width, r.height], opacity: op, optional: el.hasAttribute('data-optional') };
});
window.ready = studioReady();
// centre of an element on screen (works through 3D transforms), for placing touches
function center(el) { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }
// a touch that follows a target element: creates its own .touch div
function touchOn(key, target, lt, tA, tP, o = {}) { let t = window[key]; if (!t) { t = window[key] = document.createElement('div'); t.className = 'touch'; $('.stage').appendChild(t); }
  if (lt < tA - 0.05 || lt > tP + 0.9) { t.style.visibility = 'hidden'; if (t._rip) t._rip.style.visibility = 'hidden'; return; }
  const [x, y] = center(target); t.style.left = x + (o.ox || 0) + 'px'; t.style.top = y + (o.oy || 0) + 'px'; touch(t, lt, tA, tP, o); }
// headline / sub in and out
function titles(lt, dur, tin = 0.35) { words($('.hl'), lt, tin, dur - 0.5); words($('.sub'), lt, tin + 0.35, dur - 0.45, { stagger: 0.035 }); $$('.fine').forEach(f => f.style.opacity = 0.6 * prog(lt, 1.0, 1.6)); }
// hide authored static touch circles (animated touches are created by touchOn)
$$('.touch').forEach(t => t.style.display = 'none');
