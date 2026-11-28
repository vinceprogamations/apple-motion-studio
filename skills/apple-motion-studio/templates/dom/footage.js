// apple-motion-studio — filmagem (live action) dentro de uma página DOM, quadro a quadro e determinística.
// Use proxies ALL-INTRA na resolução/fps do filme (busca exata e rápida), feitos pelo ffmpeg:
//   ffmpeg -i original.mp4 -vf "scale=1080:1920:flags=lanczos,fps=30" -an -c:v libx264 -crf 16 -g 1 -pix_fmt yuv420p proxy.mp4
// Guarde o original + origem/licença no asset-manifest.json (type "video"); o proxy é o material intermediário da revisão.
//   const v = Footage.clip(document.getElementById('a'));             // <video id="a" src="material/proxy-a.mp4" muted playsinline preload="auto">
//   window.ready = Footage.ready([v]);                                 // rejeita se o arquivo não carrega/decodifica (portão de prontidão)
//   window.renderAt = async t => { await Footage.seek(v, clipTime); … } // render_dom.mjs espera a Promise
(function () {
  const clips = [];
  function clip(el) { el.muted = true; el.preload = 'auto'; el.pause(); clips.push(el); return el; }
  function ready(list = clips) {
    return Promise.all(list.map(v => new Promise((ok, no) => {
      const done = () => (v.videoWidth > 0 ? ok(v) : no(new Error(`vídeo sem quadros: ${v.currentSrc || v.src}`)));
      if (v.readyState >= 2) return done();
      v.addEventListener('loadeddata', done, { once: true });
      v.addEventListener('error', () => no(new Error(`vídeo não carregou ou não decodificou: ${v.currentSrc || v.src}`)), { once: true });
      v.load();
    })));
  }
  // busca exata: mira o meio do quadro do proxy (evita cair no quadro anterior por arredondamento) e espera o quadro pintado
  function seek(v, t, fps = 30) {
    const target = Math.max(0, Math.min(v.duration - 0.5 / fps, (Math.floor(t * fps + 1e-6) + 0.5) / fps));
    if (Math.abs(v.currentTime - target) < 1e-4 && v.readyState >= 2) return Promise.resolve();
    return new Promise((ok, no) => {
      const fin = () => { const to = setTimeout(ok, 400); v.requestVideoFrameCallback ? v.requestVideoFrameCallback(() => { clearTimeout(to); ok(); }) : (clearTimeout(to), ok()); };
      v.addEventListener('seeked', fin, { once: true }); v.addEventListener('error', () => no(new Error('falha ao buscar ' + v.src)), { once: true });
      v.currentTime = target;
    });
  }
  window.Footage = { clip, ready, seek };
})();
