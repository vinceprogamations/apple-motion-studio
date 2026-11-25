# Liquid Glass

O usuário pediu "mais liquid glass onde possível". Vidro de verdade não é um retângulo cinza translúcido: ele mostra o
**fundo atrás dele borrado, saturado e levemente ampliado** (lente), tem uma borda que refrata a luz e um especular no
topo. Tudo abaixo já está implementado em `templates/film.html` (vindo do Vela).

## As três camadas
1. **Fundo refratado (`glassUnder` no 3D, `chip2D`/`glassBackdrop` no 2D).** O fundo é pintado num canvas pequeno
   compartilhado (`BGS`, 384×216 — barato e já desfocado). Dentro do contorno do painel, desenhe `BGS` com
   `filter: blur(10·SCALE px) saturate(1.5) brightness(1.2)` e escala ×1,08–1,14 em volta do centro do painel (é a
   ampliação de lente). No 3D, o contorno é projetado pela câmera (`outline()` → `toWorld()` → `proj()`), então o vidro
   acompanha a perspectiva.
2. **Corpo (`glass(w, h, r)`)**: sombra suave (blur 40, offset Y 20), preenchimento rgba(18,14,12,0,36), gradiente
   diagonal branco 15 % → 4 % → 8 %, **borda de 2,2 px com gradiente** (branco 75 % no canto de cima, quase nada no meio,
   um toque do acento a 25 %, branco 40 % embaixo) e um especular interno de 1,2 px que some em 40 % da altura.
3. **Brilho que passa (`sheen` no gl3d)**: uma faixa especular linear atravessando o cartão quando ele chega ou quando a
   luz gira. Sincronize com um som de vidro bem baixo.

## Materializar em vez de fade
Para entrar, module a lente, não a opacidade: comece com blur grande no corpo e no fundo refratado, escala 0,6 → 1 com
`snappy`, alpha subindo mais rápido que o blur cai (`a = clamp01(k·1.4)`). Para sair, o inverso, mais curto. É a mesma
transição que a Apple descreve para o Liquid Glass (WWDC25), e ela conta como "transformação", não como dissolve.

## Onde usar
- Cartões de dados (dial, bateria, economia, agenda), chips em volta do foco (ícone + rótulo + valor), toast de
  notificação, botões grandes de CTA, controles (toggle), widget que vira logo.
- Em 9:16, chips de vidro empilhados embaixo do foco funcionam bem .

## Limites
- No máximo **uma superfície de vidro dominante por plano**; chips pequenos em volta contam como secundários.
- Precisa de **fundo com cor e luz** atrás; sobre preto chapado o vidro some. Por isso `paintBG` tem luz-chave e preenchimento que se movem.
- Texto sobre vidro claro: escureça ~35 % atrás do texto ou use branco sólido com peso 600+.
- `backdrop-filter` de CSS não refrata e só funciona no DOM; nas páginas de canvas use as funções acima.
- `ctx.filter` com blur é caro em 4K: desenhe a partir de `BGS` (pequeno), não do canvas cheio.
