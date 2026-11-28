// An official logo split into its own pieces by scripts/split_logo.py (logo/pN.png + logo/parts.json):
// faces, tiles and the accent piece (kind 'star'). Never redrawn, rotated or recoloured: pieces only move, scale and fade.
// Pattern: assemble piece by piece + tiles lift off at the start; tiles fly back and the accent flares on the drop at the end.
const LOGO = { W: 0, H: 0, parts: null };
async function loadLogo(dir = 'logo') { const j = await (await fetch(dir + '/parts.json')).json(); Object.assign(LOGO, { W: j.W, H: j.H, parts: j.parts, dir }); }
function buildLogo(host, width) {
  const k = width / LOGO.W; host.style.cssText += `;position:absolute;width:${width}px;height:${LOGO.H * k}px`;
  const els = LOGO.parts.map(p => { const i = document.createElement('img'); i.src = LOGO.dir + '/' + p.f;
    i.style.cssText = `position:absolute;left:${p.x * k}px;top:${p.y * k}px;width:${p.w * k}px;height:${p.h * k}px;transform-origin:50% 50%`;
    host.appendChild(i); return { el: i, ...p, cx: (p.x + p.w / 2) * k, cy: (p.y + p.h / 2) * k }; });
  const kindOf = e => e.kind || (e.f === 'p50.png' ? 'star' : null);
  const faces = els.filter(e => kindOf(e) === 'face' || (!e.kind && els.indexOf(e) < 2)), star = els.find(e => kindOf(e) === 'star'), tiles = els.filter(e => !faces.includes(e) && e !== star);
  tiles.sort((a, b) => a.x - b.x || a.y - b.y);
  return { host, k, faces, tiles, star, w: width, h: LOGO.H * k, decoded: Promise.all(els.map(e => e.el.decode().catch(() => 0))) };
}
const rnd = i => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };   // seeded per-piece random
function place(e, dx, dy, s, a, blur = 0) { if (!e) return; e.el.style.transform = `translate(${dx}px, ${dy}px) scale(${s})`; e.el.style.opacity = a; e.el.style.filter = blur > 0.3 ? `blur(${blur}px)` : (e.glow || 'none'); }
