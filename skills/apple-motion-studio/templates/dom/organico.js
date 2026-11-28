// apple-motion-studio — kit orgânico: folhas em profundidade (deriva, explosão, vórtice) e respingos líquidos em cor chapada
// (SVG metaballs, sem luz nem sombra: nota do usuário). Tudo é função do tempo, com sementes fixas. Inclua depois de anim.js.
// Folhas: PNG com alfa em img/folha1..9.png (recorte de uma grade gerada, fundo preto removido). Origem: filme de barbearia orgânico (28/11/2026).
// CSS mínimo: .leaf{position:absolute;left:0;top:0;pointer-events:none;transform-origin:50% 50%} svg.splash{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;overflow:visible}
const R = (s) => { const x = Math.sin(s * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// ---------- folhas ----------
// cria n folhas; cada uma tem profundidade z (0 longe .. 1 perto) que define escala, desfoque e opacidade
function makeLeaves(host, n, seed = 1, z0 = 0, z1 = 1) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const im = document.createElement('img'); im.className = 'leaf'; im.src = `img/folha${1 + Math.floor(R(seed * 31 + i) * 9)}.png`;
    const z = lerp(z0, z1, R(seed * 7 + i * 3.3));
    const w = lerp(90, 330, z) * lerp(0.8, 1.2, R(seed + i * 5.1));
    im.style.width = w + 'px'; host.appendChild(im);
    out.push({ el: im, z, w, a: R(seed * 13 + i) * 6.283, v: lerp(0.35, 1, R(seed * 17 + i)), r0: R(seed * 19 + i) * 360,
      spin: (R(seed * 23 + i) - 0.5) * 220, x0: R(seed * 29 + i) * 1180 - 50, y0: R(seed * 37 + i) * 2100 - 90, ph: R(seed * 41 + i) * 6.283 });
  }
  return out;
}
function putLeaf(f, x, y, rot, s = 1, a = 1, extraBlur = 0) {
  const blur = (f.z > 0.8 ? (f.z - 0.8) * 30 : f.z < 0.3 ? (0.3 - f.z) * 12 : 0) + extraBlur;
  f.el.style.transform = `translate(${x - f.w / 2}px, ${y - f.w / 2}px) rotate(${rot}deg) scale(${s})`;
  f.el.style.opacity = a * lerp(0.55, 1, f.z);
  f.el.style.filter = (blur > 0.4 ? `blur(${blur.toFixed(1)}px) ` : '') + `brightness(${lerp(0.55, 1.05, f.z).toFixed(2)})`;
}
// deriva: sobem devagar balançando (vento), em laço
function leafDrift(f, t, speed = 60) {
  const H = 2400, y = ((f.y0 - t * speed * f.v * lerp(0.5, 1.4, f.z)) % H + H) % H - 240;
  return [f.x0 + Math.sin(t * 0.8 + f.ph) * 50 * f.v, y, f.r0 + Math.sin(t * 0.6 + f.ph) * 28 + t * f.spin * 0.15];
}
// explosão a partir de (cx, cy) em t0: voam para fora com arrasto, giram e assentam na deriva
function leafBurst(f, t, t0, cx, cy, reach = 900) {
  const k = Math.max(0, t - t0), d = reach * f.v * lerp(0.6, 1.25, f.z) * (1 - Math.exp(-k * 2.6));
  return [cx + Math.cos(f.a) * d + Math.sin(t * 0.8 + f.ph) * 30 * clamp01(k), cy + Math.sin(f.a) * d * 0.95 - 60 * k,
    f.r0 + f.spin * (1 - Math.exp(-k * 1.8)) * 2 + Math.sin(t * 0.6 + f.ph) * 20];
}
// vórtice: órbita em volta de (cx, cy), raio encolhendo com k (0 = aberto, 1 = no centro)
function leafVortex(f, t, cx, cy, k, r0 = 620) {
  const ang = f.a + t * lerp(0.6, 1.4, f.v) * (1 + 2.5 * k * k), r = r0 * lerp(0.45, 1.15, f.v) * (1 - k);
  return [cx + Math.cos(ang) * r, cy + Math.sin(ang) * r * 0.82, f.r0 + ang * 57.3 * 0.6];
}

// ---------- respingos (metaballs SVG) ----------
let SPL_N = 0;
function makeSplash(host, colors = ['#B8E05A', '#D9713A'], z = 4) {
  const id = 'goo' + (SPL_N++), svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'splash'); svg.setAttribute('viewBox', `0 0 ${innerWidth} ${innerHeight}`); svg.style.zIndex = z;
  // goo (metaballs) em cor chapada: sem luz, brilho nem sombra (nota do usuário, 28/11/2026: o volume iluminado parecia estranho)
  svg.innerHTML = `<defs><filter id="${id}" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
    <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="b"/>
    <feColorMatrix in="b" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 26 -11"/></filter>
    ${colors.map((c, i) => `<linearGradient id="${id}c${i}"><stop offset="0" stop-color="${c}"/><stop offset="1" stop-color="${c}"/></linearGradient>`).join('')}</defs>
    ${colors.map((c, i) => `<g filter="url(#${id})" data-c="${i}"></g>`).join('')}<g class="hi"></g>`;
  host.appendChild(svg);
  const groups = [...svg.querySelectorAll('g[data-c]')], hi = svg.querySelector('g.hi');
  return { svg, groups, hi, id, colors, pool: groups.map(() => []), hpool: [] };
}
function circ(S, gi, j, x, y, r) {
  let c = S.pool[gi][j];
  if (!c) { c = S.pool[gi][j] = document.createElementNS('http://www.w3.org/2000/svg', 'circle'); c.setAttribute('fill', `url(#${S.id}c${gi})`); S.groups[gi].appendChild(c); }
  if (r < 0.5) { c.setAttribute('r', 0); return; }
  c.setAttribute('cx', x.toFixed(1)); c.setAttribute('cy', y.toFixed(1)); c.setAttribute('r', r.toFixed(1));
}
// um respingo: coroa + gotas radiais, por cor. bias = direção preferida (rad) e quanto (0..1)
function splashAt(S, lt, t0, cx, cy, Rr = 420, seed = 1, o = {}) {
  const n = o.n || 22, dur = o.dur || 1.5, k = lt - t0, used = S.pool.map(() => 0);
  S.groups.forEach((g, gi) => {
    let j = 0;
    const on = k >= 0 && k <= dur;
    for (let i = 0; i < n; i++) {
      const s = seed * 100 + gi * 50 + i, bias = o.bias ?? -Math.PI / 2, bw = o.spread ?? 1;
      const a = bias + (R(s) - 0.5) * 6.283 * bw, v = Rr * lerp(0.35, 1.05, R(s + 1)), r0 = lerp(10, 46, R(s + 2)) * (o.size || 1) * (gi ? 0.85 : 1);
      if (!on) { circ(S, gi, j++, 0, 0, 0); circ(S, gi, j++, 0, 0, 0); continue; }
      const kk = k / dur, tr = outExpo(k / (0.55 + R(s + 3) * 0.5)) * v, fall = 140 * kk * kk;
      const shrink = Math.pow(clamp01(1 - (k - 0.2 - R(s + 4) * 0.3) / (dur * 0.75)), 1.3);
      const x = cx + Math.cos(a) * tr, y = cy + Math.sin(a) * tr + fall;
      circ(S, gi, j++, x, y, r0 * shrink * lerp(1.4, 1, clamp01(k * 3)));
      circ(S, gi, j++, cx + Math.cos(a) * tr * 0.55, cy + Math.sin(a) * tr * 0.55 + fall * 0.5, r0 * 1.25 * shrink * clamp01(1 - k * 1.6));
    }
    // coroa central
    const kc = on ? sp(k, 'ui') : 0, rc = on ? Rr * 0.12 * clamp01(kc) * Math.pow(clamp01(1 - k / (dur * 0.6)), 1.5) * (gi ? 0.8 : 1) : 0;
    circ(S, gi, j++, cx + (gi ? 30 : -20), cy + (gi ? 20 : 0), rc);
  });
}

