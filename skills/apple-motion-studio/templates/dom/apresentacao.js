// apple-motion-studio — apresentação comercial animada (16:9, 1920×1080) a partir de DADOS: window.SLIDES (arquivo slides.js do projeto).
// Uma ideia por slide; texto palavra por palavra; um objeto persistente (o mesmo pedido/cartão) atravessa os perfis do slide "fluxo";
// a estrela ✦ viaja de um slide ao outro (transformação, sem dissolve cruzado); endcard com o logo oficial do cliente.
// Ordem dos scripts na página: motion-core.js → slides.js → apresentacao.js → anim.js (anim.js monta window.ready e o portão de assets).
// Tipos: capa {kicker,titulo,sub} · frase {linhas[],foto?,asset?} · fluxo {titulo,objeto{id,titulo,linha},perfis[{nome,tela,estado}]}
//        colunas {titulo,colunas[{titulo,itens[]}],conclusao} · fim {logo,asset,frase}. Cada slide tem dur (s). Revisão = editar os dados.
(function () {
  const S = window.SLIDES, FPS = S.fps || 30, W = 1920, H = 1080;
  const clamp = v => Math.max(0, Math.min(1, v)), prog = (t, a, b) => clamp((t - a) / (b - a)), sine = k => 0.5 - 0.5 * Math.cos(Math.PI * clamp(k));
  const lerp = (a, b, k) => a + (b - a) * k, SPR = (t, f) => MotionCore.value(t, MotionCore.FAMILIES[f]);
  const T = S.tema || {}; const css = document.createElement('style');
  css.textContent = `
    @font-face { font-family: Disp; src: url("${S.kit}/templates/dom/fonts/Montserrat-latin.woff2"); font-weight: 100 900; }
    @font-face { font-family: Txt; src: url("${S.kit}/templates/dom/fonts/Inter-Variable.ttf"); font-weight: 100 900; }
    html,body{margin:0;width:${W}px;height:${H}px;overflow:hidden;background:${T.fundo || '#000'};color:${T.texto || '#fff'};font-family:Txt,sans-serif}
    .sl{position:absolute;inset:0;display:none} .w{display:inline-block;margin-right:.24em;will-change:transform,filter,opacity}
    .k{position:absolute;left:160px;top:330px;font:600 30px Txt;letter-spacing:.18em;text-transform:uppercase;opacity:.55}
    .t{position:absolute;left:160px;right:160px;font:600 104px/1.04 Disp;letter-spacing:-.035em}
    .s{position:absolute;left:160px;right:300px;font:400 40px/1.35 Txt;opacity:.72}
    .foto{position:absolute;inset:0;background-size:cover;background-position:center;filter:grayscale(1) contrast(1.15) brightness(.55)}
    .ov{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.85),rgba(0,0,0,.35) 70%)}
    *{corner-shape:squircle}.glass{position:absolute;border-radius:40px;background:rgba(140,140,150,.14);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(30px) saturate(1.1);box-shadow:0 40px 100px rgba(0,0,0,.5)}
    .perfil{position:absolute;font:600 34px Txt;opacity:.6;letter-spacing:.02em}
    .tela{position:absolute;font:500 30px Txt;opacity:.55}
    .obj{position:absolute;left:530px;top:420px;width:860px;height:240px;border-radius:30px;background:#fff;color:#000;padding:36px 44px;box-sizing:border-box}
    .obj .id{font:600 28px Txt;opacity:.5} .obj .ti{font:600 46px Disp;white-space:nowrap;letter-spacing:-.02em;margin-top:8px} .obj .li{font:400 30px Txt;opacity:.65;margin-top:8px}
    .est{position:absolute;right:34px;top:32px;font:600 26px Txt;padding:10px 18px;border-radius:24px;background:#000;color:#fff}
    .col{position:absolute;top:420px;width:700px} .col h3{font:600 44px Disp;margin:0 0 26px;letter-spacing:-.02em} .col p{font:400 34px/1.35 Txt;margin:0 0 16px;opacity:.78}
    .conc{position:absolute;left:160px;right:160px;bottom:120px;font:600 48px Disp;letter-spacing:-.02em}
    .logo{position:absolute;left:50%;top:380px;width:560px;transform:translateX(-50%)} .logo img{width:100%;display:block}
    .fr{position:absolute;left:0;right:0;top:700px;text-align:center;font:500 48px Txt;opacity:.85}
    .star{position:absolute;width:44px;height:44px;margin:-22px 0 0 -22px;color:#fff;font-size:44px;line-height:44px;text-align:center;filter:drop-shadow(0 0 18px rgba(255,255,255,.7))}
    .bar{position:absolute;left:160px;right:160px;bottom:64px;height:3px;background:rgba(255,255,255,.12)} .bar i{display:block;height:100%;background:rgba(255,255,255,.7)}`;
  document.head.appendChild(css);
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const wsp = s => esc(s).split(/\s+/).map(w => `<span class="w">${w}</span>`).join('');
  let t0 = 0; const starts = []; const EV = []; const root = document.body;
  S.slides.forEach((s, i) => { s.t0 = t0; s.t1 = t0 + s.dur; starts.push(t0); t0 += s.dur; EV.push({ name: `s${i + 1}.${s.tipo}`, t: +s.t0.toFixed(3) }); });
  const TOTAL = t0;
  S.slides.forEach((s, i) => {
    const el = document.createElement('div'); el.className = 'sl'; el.id = 'sl' + i; let h = '';
    if (s.tipo === 'capa') h = `<div class="k" data-qa="kicker">${esc(s.kicker || '')}</div><div class="t" style="top:390px" data-qa="headline">${wsp(s.titulo)}</div><div class="s" style="top:640px">${wsp(s.sub || '')}</div>`;
    if (s.tipo === 'frase') h = (s.foto ? `<div class="foto" data-asset="${s.asset}" style="background-image:url(${s.foto})"></div><div class="ov"></div>` : '') +
      s.linhas.map((l, k) => `<div class="t" style="top:${300 + k * 140}px;font-size:${s.tamanho || 92}px" data-qa="headline">${wsp(l)}</div>`).join('');
    if (s.tipo === 'fluxo') h = `<div class="t" style="top:150px;font-size:72px" data-qa="headline">${wsp(s.titulo)}</div><div class="glass" style="left:460px;top:330px;width:1000px;height:470px"></div>` +
      `<div class="perfil" id="pf${i}" style="left:520px;top:365px"></div><div class="tela" id="tl${i}" style="left:520px;top:720px"></div>` +
      `<div class="obj" data-qa="prova" data-qa-required="${(s.t0 + 0.8).toFixed(2)}-${(s.t1 - 0.6).toFixed(2)}"><div class="id">${esc(s.objeto.id)}</div><div class="ti">${esc(s.objeto.titulo)}</div><div class="li">${esc(s.objeto.linha)}</div><div class="est" id="es${i}"></div></div>`;
    if (s.tipo === 'colunas') h = `<div class="t" style="top:170px;font-size:80px" data-qa="headline">${wsp(s.titulo)}</div>` +
      s.colunas.map((c, k) => `<div class="col" style="left:${160 + k * 820}px"><h3>${wsp(c.titulo)}</h3>${c.itens.map(x => `<p>${wsp(x)}</p>`).join('')}</div>`).join('') +
      (s.conclusao ? `<div class="conc" data-qa="cta">${wsp(s.conclusao)}</div>` : '');
    if (s.tipo === 'fim') h = `<div class="logo" data-asset="${s.asset}"><img src="${s.logo}" alt=""></div><div class="fr" data-qa="cta">${wsp(s.frase)}</div>`;
    el.innerHTML = h; root.appendChild(el);
    if (s.tipo === 'fluxo') s.perfis.forEach((p, k) => EV.push({ name: `s${i + 1}.perfil${k + 1}`, t: +(s.t0 + 0.9 + k * (s.dur - 1.4) / s.perfis.length).toFixed(3) }));
  });
  const star = document.createElement('div'); star.className = 'star'; star.textContent = '✦'; root.appendChild(star);
  const bar = document.createElement('div'); bar.className = 'bar'; bar.innerHTML = '<i></i>'; root.appendChild(bar);
  const blk = document.createElement('div'); blk.style.cssText = 'position:absolute;inset:0;background:#000'; root.appendChild(blk);
  // onde a estrela pousa em cada slide (acento do título)
  const STAR = S.slides.map(s => s.tipo === 'fim' ? [960, 640] : s.tipo === 'fluxo' ? [1440, 360] : s.tipo === 'colunas' ? [140, 210] : [130, s.tipo === 'capa' ? 450 : 350]);
  function wordsAt(el, lt, tin, tout, st = 0.06) {
    [...el.querySelectorAll('.w')].forEach((w, i) => { const e = clamp(SPR(lt - tin - i * st, 'smooth')), o = 1 - sine(prog(lt, tout, tout + 0.35));
      w.style.opacity = (e * o).toFixed(3); w.style.filter = `blur(${((1 - e) * 10 + (1 - o) * 8).toFixed(2)}px)`; w.style.transform = `translateY(${((1 - e) * 18 - (1 - o) * 12).toFixed(1)}px)`; });
  }
  window.TOTAL = TOTAL;
  window.EVENTS = EV;
  window.TIMELINE = { total: TOTAL, scenes: S.slides.map((s, i) => ({ id: `s${i + 1}`, start: s.t0, end: s.t1 })),
    transitions: S.slides.slice(1).map(s => ({ from: s.t0 - 0.4, to: s.t0 + 0.6 })),
    intentional: [{ type: 'black', from: 0, to: 0.9, why: 'abre do preto' }, ...S.slides.slice(1).map(s => ({ type: 'black', from: s.t0 - 0.7, to: s.t0 + 1.5, why: 'fundo preto da marca entre duas ideias' })),
                  ...S.slides.slice(0, -1).map(s => ({ type: 'hold', from: s.t0 + 1.2, to: s.t1 - 0.4, why: 'tempo de leitura do slide (texto parado de propósito)' })), { type: 'black', from: TOTAL - 0.5, to: TOTAL, why: 'fecha no preto' },
                  { type: 'static_logo', from: S.slides.at(-1).t0 + 0.5, to: TOTAL - 0.5, why: 'endcard para leitura' }] };
  window.renderAt = t => {
    S.slides.forEach((s, i) => {
      const el = document.getElementById('sl' + i), on = t >= s.t0 - 0.01 && t < s.t1 + 0.4 && (i === S.slides.length - 1 || t < s.t1 + 0.4);
      el.style.display = on ? 'block' : 'none'; if (!on) return; const lt = t - s.t0, out = s.dur - 0.45, last = i === S.slides.length - 1;
      // o slide inteiro some na saída (o QA de composição lê a opacidade do contêiner) e respira com um push lento e contínuo
      el.style.opacity = last ? 1 : (1 - sine(prog(lt, out, out + 0.4))).toFixed(3); el.style.transformOrigin = '50% 50%';
      el.style.transform = `scale(${(1 + 0.012 * lt / s.dur).toFixed(5)})`;
      el.querySelectorAll('.k,.t,.s,.col h3,.col p,.conc,.fr').forEach((x, k) => wordsAt(x, lt, 0.25 + k * 0.18, last ? 99 : out));
      if (s.tipo === 'frase' && s.foto) { const f = el.querySelector('.foto'); f.style.transform = `scale(${(1.06 + 0.012 * lt).toFixed(4)})`; f.style.opacity = 1 - sine(prog(lt, out, out + 0.4)); el.querySelector('.ov').style.opacity = f.style.opacity; }
      if (s.tipo === 'fluxo') {   // o MESMO objeto atravessa os perfis: muda o perfil e o estado, nunca o objeto
        const n = s.perfis.length, step = (s.dur - 1.4) / n, k = Math.max(0, Math.min(n - 1, Math.floor((lt - 0.9) / step))), p = s.perfis[k];
        const o = el.querySelector('.obj'), e = SPR(lt - 0.5, 'soft'), sw = SPR(lt - 0.9 - k * step, 'snap');
        o.style.opacity = clamp(e * 1.2) * (1 - sine(prog(lt, out, out + 0.35))); o.style.transform = `translateY(${((1 - e) * 60).toFixed(1)}px) scale(${(k > 0 ? 0.985 + 0.015 * clamp(sw) : 1).toFixed(4)})`;
        document.getElementById('pf' + i).textContent = p.nome; document.getElementById('tl' + i).textContent = p.tela; document.getElementById('es' + i).textContent = p.estado;
        for (const id of ['pf', 'tl']) { const x = document.getElementById(id + i); x.style.opacity = (0.6 * clamp(sw * 1.3) * (1 - sine(prog(lt, out, out + 0.35)))).toFixed(3); x.style.transform = `translateX(${((1 - clamp(sw)) * -24).toFixed(1)}px)`; }
        el.querySelector('.glass').style.opacity = clamp(e) * (1 - sine(prog(lt, out, out + 0.35)));
      }
      if (s.tipo === 'fim') { const lg = el.querySelector('.logo'), e = SPR(lt - 0.2, 'soft'); lg.style.opacity = clamp(e); lg.style.transform = `translateX(-50%) translateY(${((1 - e) * 30).toFixed(1)}px) scale(${(1 + 0.004 * lt).toFixed(4)})`; }
    });
    // a estrela viaja do acento de um slide para o do próximo (spring cam: nunca volta)
    let i = S.slides.findIndex(s => t < s.t1); if (i < 0) i = S.slides.length - 1; const s = S.slides[i];
    const from = STAR[Math.max(0, i - 1)], to = STAR[i], k = i === 0 ? 1 : SPR(t - s.t0 + 0.35, 'cam');
    star.style.left = lerp(from[0], to[0], k) + 'px'; star.style.top = lerp(from[1], to[1], k) + 'px';
    star.style.opacity = (S.slides[i].tipo === 'fim' ? 1 - clamp((t - s.t0) * 3) : clamp(t * 2)).toFixed(3); star.style.transform = `scale(${(1 + 0.08 * Math.sin(t * 2.1)).toFixed(3)})`;
    bar.firstChild.style.width = (100 * t / TOTAL).toFixed(2) + '%'; bar.style.opacity = S.slides[i].tipo === 'fim' ? 0 : 1;
    blk.style.opacity = Math.max(1 - sine(prog(t, 0, 0.3)), sine(prog(t, TOTAL - 0.5, TOTAL)));
  };
})();
