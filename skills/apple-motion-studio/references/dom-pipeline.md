# Pipeline DOM (HTML/CSS por cena)

Quando o filme é feito de **interfaces realistas, vidro, fotos e texto** (anúncio de software, Reels 9:16), escreva
cada cena como uma página HTML/CSS em vez de canvas. `backdrop-filter` dá Liquid Glass de verdade, fotos e fontes
ficam nítidas, e o quadro estático do storyboard já É a cena (só ganha `anim(lt)`). Para 3D de verdade continue com
canvas + `gl3d.js` (`templates/film.html`) ou Blender.

Estrutura de um filme DOM: `storyboard/N.html` = quadros; `aN.html` + `anim/sN.js` = cenas animadas; `sequence.html` = sequência; `BEATS.md`; `sound/`.

## Peças (em `templates/dom/` e `scripts/`)
| Arquivo | Faz |
|---|---|
| `device.js` | aparelho real em cena: moldura renderizada do modelo 3D + interface recortada pela máscara da tela (`buildDevice`) |
| `organico.js` | kit orgânico: folhas em profundidade (deriva, explosão, vórtice) e respingos líquidos chapados (`makeLeaves`, `makeSplash`, `splashAt`) |
| `common.css` | palco (fundo grafite com luz suave, textura de pontos 4 %, grão), `.hl` título Display, `.sub`, `.glass` (Liquid Glass neutro), `.touch`, `.shadow`, `.prog` (barra de progresso em pontos) |
| `phone.css` | celular: moldura de titânio, vidro preto, dynamic island, reflexo |
| `light.css` | UI clara e realista de sistema (topo, hero com foto, cards "para resolver agora" com borda colorida, KPIs, menu inferior) — modelada na tela de referência que o usuário mandou |
| `icons.js` | ícones de linha originais (`icon('agenda', 40, cor)`) |
| `anim.js` | o kit de movimento (abaixo) |
| `logo.js` + `scripts/split_logo.py` | logo oficial em peças |
| `scene.html` | cena-modelo com celular, toast, toque e títulos já animados |
| `sequence.html` | junta as cenas (iframes) e faz o corte "dissolve em pontos" |
| `scripts/render_dom.mjs` | `stills` / `video` / `events` com screenshot por CDP, 60 fps, BT.709, nome temporário |
| `scripts/sheet916.py` | folha de stills em 9:16 (o `contact_sheet.py` estica para 16:9) |

## Cantos: squircle sempre (regra do usuário, 28/11/2026)
Tudo que é arredondado (ícone de app, card, janela de navegador, celular, botão, aviso, pílula, chip) é **squircle**: superelipse
|x/a|⁴ + |y/b|⁴ = 1, curvatura contínua como os ícones da Apple. O arco circular do `border-radius` puro deixa uma quina visível onde
encontra o lado reto e foi reprovado.
- **DOM:** `common.css` já aplica `* { corner-shape: squircle; }` (= `superellipse(2)`, n = 4; Chrome 139+, o render usa 158).
  Ao portar CSS antigo, suba o `border-radius` ~1,25× (o squircle arredonda menos com a mesma medida).
- **Círculos de verdade** (avatar, toque, ripple, partícula, ponto, bolinha do semáforo da janela): classe `.circle` ou `corner-shape: round`.
  Sem isso um `border-radius: 50%` vira um "quadrado gordo".
- **Canvas/SVG:** desenhe a superelipse ponto a ponto (x = a·sgn(cos t)|cos t|^(2/n), y = b·sgn(sin t)|sin t|^(2/n), n = 4) ou, para
  retângulo com cantos, um quarto de superelipse em cada canto.
- **Blender:** perfil de superelipse no bevel/curva (não "arc"); confira o canto a 100 % no still.
- **QA:** recorte 1:1 de um canto em todo filme; não pode haver mudança brusca de curvatura.
- **Exceção: celular.** O corpo de um iPhone não é um squircle de CSS (nota do usuário, 28/11/2026). Use a moldura real:
  `scripts/blender/device_front.py -- <modelo.fbx> <cena/img> 1240` renderiza a frente em ortográfica com a tela vazada
  (`iphone-frente.png`) e a forma exata da tela (`iphone-mascara.png`). Na cena, borda preta = máscara cheia, interface = máscara
  reduzida ~1,8 % (cantos concêntricos), moldura PNG por cima; a UI é desenhada em pontos (440 de largura) e escalada.
  Template: `templates/dom/device.js` → `await buildDevice(host, largura)` (mede a tela na máscara; serve para qualquer modelo).
- **Telas de app real** (perfil de rede social, agenda, loja): copie o *layout* de um print real que o usuário mandar (ordem,
  proporções, modo escuro), nunca o logo ou o nome do app.

## Kit de movimento (`anim.js`)
- `spr(t, f, z)` spring por **frequência (Hz) e amortecimento**; tokens `SP`: heavy [1.0, .72], soft [1.5, .82], ui [2.3, .45] (overshoot visível), snap [2.6, .6]. `sp(t,'ui')`.
- `setT(el, extra, opacity)` aplica movimento **antes** do transform autoral (perspectiva do celular continua valendo).
- `pop(el, lt, t0, {s0, dy, dx, rot, blur, out})`: escala 0,3–0,6 → 1 com overshoot, opacidade em 0,2 s, blur 10 → 0, pequeno ajuste de rotação/offset; `out` faz a saída com blur.
- `words(el, lt, tIn, tOut)` / `titles(lt, dur)`: palavra a palavra, sobe 0,5 em, blur 16 → 0, outExpo 0,9 s, stagger 60 ms; sai com blur. `split()` preserva elementos filhos.
- `touchOn(key, alvo, lt, tA, tP)`: círculo de toque que acha o centro do alvo na tela (funciona com 3D), afunda, solta onda; combine com `squish(lt, tP)` no botão e com uma mudança de estado (classe `on`, cor, check).
- `count(el, lt, t0, t1, a, b, fmt)`, `typeText(el, texto, lt, t0, cps)`, `burst(host, key, x, y, lt, t0)` (partículas), `wiggle(lt, tH)` (vibração háptica), `drift(lt, seed, amp)` (deriva de senos), `ambience(lt)` (marquee).
- `window.ready` espera fontes, `<img>` **e** imagens de fundo CSS — sem isso o quadro 0 sai sem foto.

## Logo por peças (marca real, sem redesenho)
`python scripts/split_logo.py logo-branco.png <filme>/logo` separa o PNG oficial em peças (faces, quadradinhos,
estrela). `buildLogo(host, largura)` recria o logo com `<img>` de cada peça; anime só posição/escala/opacidade/blur:
montar peça a peça (faces deslizam, quadradinhos em cascata, estrela por último com brilho `drop-shadow`), soltar
quadradinhos que voam (viram o próximo elemento), e no final eles voltam e a estrela estoura no drop. Nunca girar,
distorcer ou recolorir um logo oficial (regra comum dos guias de marca).

## Sequência e cortes
- Cenas de 4–6,5 s. `CUTS` com os inícios; cada cena recebe `lt = t − início`; anime a saída dos títulos ~0,5 s antes do corte.
- Corte padrão da marca: **dissolve em pontos** (grade de 30 px que fecha no último ponto de ação da cena, `ORIGIN`). Combine com continuidade real quando der (quadradinhos que saem do logo → módulos; celular que sobe → próximo celular).
- `EVENTS` lista todas as batidas em segundos do filme (cortes, toques, pousos, drop) para o som.

## Render
```bash
node scripts/render_dom.mjs stills <filme>/sequence.html review/r1 0.4 0.8 ... --root .   # --root = pasta que contém fontes/imagens referenciadas
python scripts/sheet916.py review/r1 review/r1.jpg 7
node scripts/render_dom.mjs video  <filme>/sequence.html "out/<Filme> - 1080p (sem som).mp4" --fps 60 --root .
node scripts/render_dom.mjs events <filme>/sequence.html sound/events.json --root .
```
Medido: 1080×1920, 60 fps, 40 s → 2400 quadros em ~2,5 min. Viewport padrão 1080×1920; 16:9 use `--w 1920 --h 1080`.

## Armadilhas (todas aconteceram)
- Texto com gradiente (`background-clip: text`) **some** quando as palavras viram spans com transform: o gradiente vai em cada `.w` (já no anim.js para `.hl` e `.tagline`). Não use a classe `.tag` para a frase final se `.tag` também for pílula de vidro.
- `setT` precisa pôr o movimento antes do transform autoral, senão o translate acontece dentro do espaço rotacionado do celular.
- Elementos de toque estáticos do storyboard ficam escondidos; os toques animados são criados por `touchOn`.
- `contact_sheet.py` estica quadros verticais: para 9:16 use `sheet916.py`.
- Comandos com `.remove()` dentro de heredoc no Bash foram barrados pela checagem de segurança: escreva JS com a ferramenta Write.

## Assets (manifesto e portão) — obrigatório desde 24/11/2026
Causa do caso Studio Lume (cena com avatares em gradiente no lugar das fotos): cena escrita antes das fotos, sem
inventário e sem checagem de cobertura. Agora:
1. **Planeje antes de animar**: para cada cena, liste as vagas (foto de perfil, hero, produto, logo) em `asset-manifest.json`
   ao lado da `sequence.html`: `id`, `scene` (s1…), `slot`, `required`, `file`, `visible` [início, fim em segundos do filme],
   `origin`, `license`, `status` (PLANNED → NEEDS_GENERATION/NEEDS_USER_ASSET/… → APPROVED → INTEGRATED).
   Exemplo completo: `tests/fixtures/studio-lume/asset-manifest.json`.
2. **Marque o elemento** da vaga com `data-asset="<slot>"` e use o arquivo do manifesto (`background-image:url(...)` ou `<img>`). Vaga opcional: `data-optional`.
3. **Aprove com escopo**: `python scripts/assets.py approve <manifest> all --scope "storyboard v2 aprovado pelo usuário em 24/11"` grava sha256, pixels e aprovação.
   Opcional que o storyboard aprovou sem asset: `python scripts/assets.py omit <manifest> <id> --scope "..."`.
4. **O render confere** (modo strict em `video`/`check`, aviso em `stills`): arquivo existe e decodifica, hash = aprovado, licença e aprovação
   presentes, a vaga mostra ESSE arquivo (não gradiente/outro), está visível (opacidade > 0,5, na tela) dentro de `visible`,
   e a imagem tem pixels suficientes para o tamanho na tela × `--scale`. Qualquer falha obrigatória bloqueia o MP4 com
   `cena · vaga · arquivo: motivo → solução`; o relatório fica em `<saída>.report.json`.
5. **Trocou um asset?** `python scripts/assets.py affected <manifest> <id>` lista as cenas a re-renderizar; reaprove só depois de ver.
Nem toda interface precisa de foto: agenda sem perfil, cena de marca ou visualização técnica podem ser não fotográficas —
declare isso no storyboard (vaga opcional omitida com aprovação) para distinguir ausência criativa de ausência acidental.

## Prontidão e erros (o que mudou no kit)
`anim.js` agora rejeita `ready` se fonte/`<img>`/imagem de fundo (inclusive de folha CSS) não decodificar; `data:` URIs são
ignorados. `sequence.html` exige `anim(lt)` + `ready` em cada cena e expõe `window.TIMELINE` (cenas + `INTENTIONAL`).
`render_dom.mjs` lê exceções, `console.error`, HTTP ≥ 400 e falhas de rede pelo CDP, limita a espera (`--ready-timeout`),
diz a etapa e o instante da falha, grava `.tmp` e só renomeia no sucesso, não sobrescreve sem `--replace` e escreve
`<saída>.timeline.json` para o QA. Projetos antigos mantêm suas cópias do kit e renderizam igual (regressão: diferença média
< 0,7 nível/pixel, só do JPEG q95); sem manifesto eles rodam com `--legacy "motivo"` — um filme novo sem fotos usa `{"assets": []}`.
