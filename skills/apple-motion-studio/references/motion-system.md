# Sistema de motion (o que faz parecer Apple)

Fonte: pesquisa `pesquisa-apple-motion/reports/Engenharia de motion design Apple.md` (seções C e D, 49 tokens com
fórmula) + regras de um designer em várias rodadas de notas + os filmes do projeto de origem. A Apple documenta a física
da UI (WWDC23 "Animate with springs"); a linguagem dos filmes é inferida. Nunca invente "valores da Apple".

## Índice
1. Springs e tokens
2. Qual curva para qual propriedade
3. Tempo, stagger e leitura
4. Composição e densidade
5. Câmera e luz
6. Transições
7. Texto
8. Cor, grão e motion blur
9. Linguagem de movimento do brief "$1M launch film"

## 1. Springs e tokens

Modelo Apple: `duration` = período não amortecido (perceptual), `bounce` = 1 − ζ. Forma fechada (já no `templates/film.html`):
```js
function spring(t, duration = 0.5, bounce = 0) {   // 0 → 1
  if (t <= 0) return 0; const w = 2 * Math.PI / duration, z = 1 - bounce;
  if (z >= 1) return 1 - Math.exp(-w * t) * (1 + w * t);
  const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
}
const SPR = { smooth: [0.5, 0], snappy: [0.5, 0.15], heavy: [0.9, 0.05], hero: [0.7, 0.3] };
const sp = (t, k) => spring(t, ...SPR[k]);   // uso: lerp(a, b, sp(t - B.card, 'snappy'))
```

| Token | duration / bounce (ζ) | Overshoot | Assenta (2 %) | Para |
|---|---|---|---|---|
| smooth | 0,5 s / 0 (1,0) | 0 % | 0,46 s | padrão quando em dúvida |
| snappy | 0,5 s / 0,15 (0,85) | 0,6 % | 0,33 s | cartões, UI, toque |
| quick | 0,3 s / 0 | 0 % | 0,28 s | secundários, 1–2 frames após o pai |
| gentle | 0,8 s / 0 | 0 % | 0,74 s | deslocamentos de área grande (sem overshoot) |
| heavy | 0,9 s / 0,05–0,2 | ≤ 1,5 % | ~0,54 s | produto, anel, objeto com peso |
| heavySettle | 1,1 s / 0,1 | 0,15 % | 0,82 s | pouso solene de logo |
| hero | 0,45–0,7 s / 0,3 (0,7) | 4,6 % | ~0,45 s | **um** pop por filme, no drop |
| effects | 0,25 s / 0 | 0 % | — | opacidade/cor/blur quando quiser física |

Limites: overshoot ≤ 3 % por padrão, ≤ 10 % só no hero; ζ < 0,6 é proibido ("gelatina"); zero bounce em texto, logo,
câmera e saídas. Bounce 0,15 quase não se vê, é normal.

## 2. Qual curva para qual propriedade

| Propriedade | Curva |
|---|---|
| posição, escala, rotação, raio, expansão de cartão | spring ζ 0,7–1 |
| opacidade, blur, cor, sombra | ease-out (`outExpo`, `outCubic`) ou `sine`; **nunca spring com overshoot** |
| câmera (dolly, orbit) | `sine`/`inOutCubic` ou spline monotônica; spring só com ζ ≥ 1 |
| morph de forma | `inOutCubic`, 13–20 frames (0,52–0,80 s), centro de massa parado na tela |
| varredura de brilho, progresso, contador | linear (ou `outExpo` para número que "chega") |
| saída | aceleração curta (~0,35 s), mais curta que a entrada, sem bounce |

Segmentos encadeados precisam casar a velocidade (C¹): ease-out seguido de ease-in dá uma parada na junção. Para um
movimento longo use **uma** curva só (ou `blender/tracks.py`/spline monotônica).

## 3. Tempo, stagger e leitura
- 25 fps: **toda batida é múltiplo de 0,04 s**. Guarde em `B` no topo, nunca espalhado no código.
- "Rápido, depois devagar por mais tempo." Primeiros rascunhos sempre ficam rápidos demais.
- Movimento hero de filme: 0,8–1,6 s. UI: 0,25–0,4 s.
- Stagger: palavra 80 ms (2 f), item 40 ms (1 f); cascata começa a 10–30 % da duração do elemento; para listas longas,
  suavize (delayᵢ = D·ease(i/n)) ou ordene pela distância ao centro. `i*k` fixo vira dominó.
- Antecipação: contra-movimento de ~3 % por 80 ms antes do reveal hero (ou squash de ~8 % uma pose antes de crescer).
- **Hold de texto ≥ max(1,2 s; caracteres/12) + 0,3 s**, contado da última palavra nítida. "Menos dor. Mais movimento." (26 car.) → ≥ 2,2 s.
- Sempre algo se movendo: um drift lento de câmera ou partículas já basta; quadro parado parece morto.

## 4. Composição e densidade
- Ação **no centro** (mira invisível); o centro óptico fica um pouco acima do geométrico. Espaço para a headline em cima.
- Cada estado: 1 foco + até 2 secundários; ≤ 3 coisas se movendo ao mesmo tempo; um movimento dominante por plano.
- Mas **não pode ficar vazio**: o usuário achou o Vela v1 "muito simples". O que deu certo no Vela v2:
  partículas de profundidade com seed, chips de vidro em volta do foco (ícone + rótulo + valor), fluxos de energia
  tracejados correndo para o foco, cartões secundários entrando em cascata, toast de notificação, números contando,
  pulsos/anéis no drop, callouts com linha fina apontando partes do produto 3D.
- **Nada repetido**: um filme foi criticado por repetir o mesmo layout. Cada plano usa outra gramática (close num
  número, cartão em perspectiva, painel 3D, lista que rola, logo).
- 16:9 tem margem lateral; 9:16 empilha: headline em cima, foco no centro, chips embaixo.

## 5. Câmera e luz
- **Uma câmera contínua que nunca volta**: sem zoom in e depois out, sem orbit que para e retorna. Monotônica em cada eixo.
- Lente 50–85 mm equivalente para produto; dolly 5–15 % do quadro/s; orbit ≤ 30–45° por plano; roll ≤ 5–10°; nunca dois movimentos grandes juntos.
- A velocidade da câmera é "carregada" de um plano para o outro (sem parar no corte).
- DOF raso no 3D (gl3d `aperture`) faz o browser parecer filmado.
- **Uma luz-chave** (direção fixa, todas as sombras concordam) + um preenchimento frio fraco do lado oposto. Girar o
  objeto/luz faz o especular correr e "vende" o material; mover a câmera vende o espaço.
- Troca 2D → 3D: troque no mesmo tamanho de tela (o Vela precisou de `sc × 1,05` para não pular) e desenhe a headline nos dois ramos.

## 6. Transições (o coração)
Em ordem de preferência:
1. **Morph / elemento compartilhado** — o objeto do plano cresce, muda de forma e vira o próximo (círculo ↔ quadrado
   arredondado ↔ cartão ↔ tela). Inunde a forma com o fundo do próximo plano antes, depois o próximo entra 93 % → 100 %.
2. **Match cut** por silhueta, posição ou cor.
3. **Máscara com a forma do objeto** — o furo do anel vira janela (íris do Nuvra), o círculo revela (`reveal()`).
   Íris circular genérica parece retrô: use a forma do próprio objeto.
4. **Mergulho/push-through** — a câmera entra na tela do celular.
5. **Materialização do vidro** — o cartão entra modulando a lente (blur/refração) em vez da opacidade. Ver `liquid-glass.md`.
6. **Dot-dissolve da marca** — a forma se desfaz em pontos da identidade e eles formam a próxima (marca com motivo de pontos).
7. **Giro de borda** — objeto fica de perfil (invisível) e a troca acontece escondida.
8. Glint/flash especular sincronizado com som (confira o limite de flash em `qa.md`); rack de foco; corte seco só no drop; whip pan no máximo uma vez.

Nunca cross dissolve entre planos. Opacidade só dentro de uma transformação motivada (lente, foco, luz).

## 7. Texto
- Fonte da marca (ou Inter, OFL, em `templates/dom/fonts/`). Peso 600–700 em títulos, tracking ≈ −0,03 em, sentence case, ponto final.
- **Palavra por palavra** (`words()` no template): blur 14–16 px → 0 (×SCALE), subida ~0,45 em com `outExpo` 0,9 s,
  stagger 80 ms; sai subindo com `sine` 0,45 s. Sem quique, sem pop de escala, sem borda dura de revelação, nunca tracking + escala juntos.
- Gradiente sutil: branco até 60 % da altura, cinza quente (#a9a39c) embaixo. Só em fundo escuro; em campo de cor use tinta sólida.
- Texto sobre vidro claro: escureça o vidro ~35 % atrás do texto.
- Mantenha o texto longe de onde as coisas vão passar.

## 8. Cor, grão e motion blur
- Fundo escuro **com cor**: uma luz-chave quente/da marca + preenchimento frio, que se movem devagar (`paintBG`). Preto e branco chapado foi rejeitado.
- **Um matiz de acento por filme** (Vela: âmbar #FFB547 → #FF7A1A; outra marca: o teal dela). O resto em brancos e cinzas quentes.
- Grão animado sutil (overlay ~6 %, 4 texturas com seed alternando) evita banding de 8 bits no escuro.
- Motion blur por sub-frames: 6 nas janelas `FAST` (movimentos rápidos), 2 no resto, obturador 180° (`0.5/25`). Fantasma = poucos sub-frames.
- Tudo determinístico: nada de `Date.now`, `performance.now`, `Math.random` sem seed, CSS transitions ou setTimeout.

## 9. Linguagem de movimento do brief "$1M launch film"
Os dois modelos de spring são o mesmo: `duration`/`bounce` (Apple) ↔ `f` (Hz) e `z`: f = 1/duration, z = 1 − bounce.
O brief pede: objetos pesados f 0,9–1,2 Hz, z 0,55–0,8; pops de UI f 2,0–2,6 Hz, z 0,38–0,5 (overshoot visível, ~20 %).
É mais elástico que o limite de 3 % da §1: use os pops de UI só em elementos pequenos (chips, checks, toasts, botões);
nunca em texto, logo, câmera ou superfícies grandes. Kit: `templates/dom/anim.js` (`SP.ui` = [2.3, .45]).
Checklist por cena (nada pode "só deslizar"):
- **Pop-in**: escala 0,3–0,6 → 1 com overshoot, opacidade em 0,2 s, blur 10 → 0, pequena rotação/offset que assenta.
- **Texto**: por palavra; sobe 0,4–0,6 em, blur 8–22 px → 0, ease-out-expo ~0,9 s, stagger 30–90 ms; sai ao contrário com blur.
- **Notificações/toasts**: caem com spring bouncy, o ícone estoura um tempo depois, as linhas entram em cascata; o aparelho dá uma vibração háptica (`wiggle`).
- **Pelo menos um toque por cena**: círculo translúcido aparece, afunda, solta onda, e a UI responde (botão afunda + muda de estado, toggle vira, cor muda o produto, coração enche com partículas, cartão sai, widget abre).
- **UI viva**: contadores sobem, barras enchem com brilho correndo, ondas/EQ se mexem, timers andam.
- **Nada morto**: deriva lenta em tudo (soma de senos), push/órbita lenta de câmera, tipo gigante em marquee no fundo, brilhos respirando, grão animado.
- **Motion blur** em 3D por amostras de obturador (1 quando lento, até 6–7 quando rápido). No DOM não há; 60 fps compensa.
- **Cenas de 4,5–6,5 s; cortes desenhados** (match cut): íris pelo furo de um anel, mergulho na tela cujo painel vira o fundo da próxima cena, whip pan com blur direcional no corte, onda de toque que inunda para preto, bloom para branco no final, dissolve em pontos (marca com motivo de pontos).
