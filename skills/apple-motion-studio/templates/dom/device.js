// apple-motion-studio — aparelho real em cena (celular, tablet): moldura renderizada de um modelo 3D + interface DOM recortada pela
// forma exata da tela. Nunca desenhe o corpo do celular com border-radius/squircle (nota do usuário, 28/11/2026).
// 1) Gere a moldura e a máscara:  blender -b --factory-startup -P scripts/blender/device_front.py -- <modelo.fbx|glb> <cena/img> 1240
//    → img/iphone-frente.png (aparelho com a tela vazada) e img/iphone-mascara.png (só a tela, branca)
// 2) Na cena:  const P = await buildDevice(document.getElementById('ph'), 560);   // P.ui recebe a interface, desenhada em pontos (440 de largura)
//    <div id="ph"><div class="ip-ui"> …interface… </div></div>   (o .ip-ui pode existir no HTML; senão é criado)
// Camadas: borda preta (máscara cheia) → tela (máscara reduzida em `bezel`, cantos concêntricos) → moldura PNG por cima.
// A geometria da tela é MEDIDA na máscara (qualquer modelo serve). Referência de uso: filme de barbearia (landing page) de 28/11/2026.
(function () {
  const css = `.iph{position:absolute}.iph>*{position:absolute}.ip-bez{inset:0;background:#000}.ip-disp{overflow:hidden;background:#000}
.ip-frame{left:0;top:0;width:100%;height:100%;z-index:3;pointer-events:none}.ip-ui{position:absolute;left:0;top:0;overflow:hidden}`;
  document.head.insertAdjacentHTML('beforeend', `<style>${css}</style>`);
  const cache = {};
  function medir(src) {               // bbox da tela (alfa > 128) na máscara, em px da imagem
    if (cache[src]) return cache[src];
    return cache[src] = new Promise((ok, no) => { const im = new Image(); im.onload = () => {
      const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight; const g = c.getContext('2d'); g.drawImage(im, 0, 0);
      const d = g.getImageData(0, 0, c.width, c.height).data; let x0 = c.width, y0 = c.height, x1 = 0, y1 = 0;
      for (let y = 0; y < c.height; y += 2) for (let x = 0; x < c.width; x += 2) if (d[(y * c.width + x) * 4 + 3] > 128) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
      ok({ W: c.width, H: c.height, sx: x0, sy: y0, sw: x1 - x0 + 1, sh: y1 - y0 + 1 }); };
      im.onerror = () => no(new Error('máscara do aparelho não carregou: ' + src)); im.src = src; });
  }
  async function buildDevice(host, W, o = {}) {
    const frame = o.frame || 'img/iphone-frente.png', maskSrc = o.mask || 'img/iphone-mascara.png', uiW = o.uiWidth || 440;
    const G = await medir(maskSrc), k = W / G.W, H = G.H * k;
    host.style.width = W + 'px'; host.style.height = H + 'px'; host.classList.add('iph');
    const b = (o.bezel ?? 0.017) * G.W * k, dx = G.sx * k + b, dy = G.sy * k + b, dw = G.sw * k - 2 * b, dh = G.sh * k - 2 * b, s = dw / (G.sw * k);
    const mask = (el, w, h, ox, oy) => { for (const p of ['webkitMask', 'mask']) { el.style[p + 'Image'] = `url(${maskSrc})`; el.style[p + 'Size'] = `${w}px ${h}px`; el.style[p + 'Position'] = `${ox}px ${oy}px`; el.style[p + 'Repeat'] = 'no-repeat'; } };
    const bez = document.createElement('div'); bez.className = 'ip-bez'; mask(bez, W, H, 0, 0); host.appendChild(bez);
    const disp = document.createElement('div'); disp.className = 'ip-disp'; disp.style.cssText += `left:${dx}px;top:${dy}px;width:${dw}px;height:${dh}px`;
    mask(disp, W * s, H * s, -G.sx * k * s, -G.sy * k * s); host.appendChild(disp);
    const ui = host.querySelector('.ip-ui') || document.createElement('div'); ui.classList.add('ip-ui');
    const scale = dw / uiW; ui.style.cssText += `width:${uiW}px;height:${dh / scale}px;transform:scale(${scale});transform-origin:0 0`; disp.appendChild(ui);
    const fr = document.createElement('img'); fr.className = 'ip-frame'; fr.src = frame; host.appendChild(fr);
    await fr.decode().catch(() => { throw new Error('moldura do aparelho não carregou: ' + frame); });
    return { host, ui, W, H, scale };
  }
  window.buildDevice = buildDevice;
})();
