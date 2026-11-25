# Brief padrão: "$1M launch film" (o prompt do usuário) e como esta skill cumpre cada item

O usuário usa este brief para pedir filmes. Quando ele colar (ou disser "faz no padrão de sempre"), siga as 3 fases.
Campos `[FILL IN]`: marca (auto = marca fictícia original, nunca marca real), duração/formato, tema (auto = escolha pelas referências).

## Fase 1 — Analisar (sem código)
Escreva um **guia de estilo** curto a partir das referências (imagens anexadas, ou a marca do usuário):
- paletas em hex; luz (estúdio suave, highlights de softbox, rim light);
- materiais (titânio fosco, vidro jateado, cerâmica brilhante, pérola iridescente, cromo líquido);
- câmera (ângulos 3/4 inclinados, objetos flutuando, sombras de contato suaves);
- tipografia (uma grotesca, tracking apertado nos tamanhos grandes);
- composição (aparelhos flutuando, chips e pílulas de vidro, cartões em leque em profundidade, tipo gigante ao fundo);
- o que exatamente faz cada referência parecer cara.
Depois: história em **6 cenas** (ou mais, se o usuário pedir) usando a melhor ideia de cada referência, e **uma marca
original** (forma geométrica 3D simples) que volta em todas as cenas. Tudo inventado: nomes, textos de UI, conteúdo.

**Marca real do usuário:** antes de tudo, procure os documentos dela (no projeto e na pasta Downloads do usuário — `%USERPROFILE%\Downloads` no Windows, `~/Downloads` no macOS/Linux —,
ex.: documento da marca, sistema visual, artes). As regras da marca vencem o brief.

## Fase 2 — Storyboard (PARE para aprovação)
Detalhes em `storyboard.md`. Do brief: quadros na **resolução final** (4K = 3840×2160; Reels 4K = 2160×3840),
um por cena, no instante com mais coisa na tela. Inspecione cada quadro em tamanho real **com recortes de detalhe**
(bordas, texto, materiais) e corrija: corte na borda, highlight estourado, cor lavada, texto sobreposto, objeto grande
ou pequeno demais, texto de template esquecido. Mande os quadros + folha rotulada (uma linha por cena) e espere.
Se não der para chegar na qualidade, diga que assets externos ajudariam (fotos reais, logo vetorial, fontes da marca).

## Fase 3 — Animar (só depois do "aprovado")
Escreva o **beat sheet** com tempos de cada cena antes de codar (ex.: `<filme>/BEATS.md`). Linguagem de movimento
em `motion-system.md` §9 (springs por frequência/amortecimento, pop-in, texto, toasts, toques, UI viva, nada parado,
motion blur, cenas de 4,5–6,5 s, match cuts).

## Abordagem técnica do brief × o que este projeto usa
| Brief pede | Aqui | Status |
|---|---|---|
| Página HTML por cena, `SCENE.frame(t)` puro, servidor HTTP local, headless Chrome a 2× | `anim(lt)` por cena + `sequence.html` + `scripts/render_dom.mjs` (CDP, servidor próprio) | feito |
| HTML/CSS para UI, texto e vidro | `templates/dom/` (common/light/phone.css, anim.js, icons.js) | feito |
| WebGL2 para 3D | `scripts/gl3d.js` (painéis 3D com DOF, fog, sheen) via `templates/film.html` | feito |
| Rasterizador WebGL2 com malhas (slab arredondado, toro, esfera, torno), softboxes analíticos, clear-coat, iridescência, MSAA 4× | **não implementado** — gl3d só tem painéis planos; volume é fingido com fatias empilhadas (Vela) | lacuna: construir quando um filme pedir objeto 3D de verdade; alternativa: Blender (`blender.md`) |
| Telas de celular como páginas HTML com `setT(t)` virando textura | no pipeline DOM a tela é HTML direto dentro do celular de CSS (sem textura) | equivalente |
| Sombras de contato por gradiente radial | `.shadow` em common.css | feito |
| Motion blur por amostras de obturador | canvas: sub-frames nas janelas `FAST` (film.html). DOM: não há (60 fps compensa) | parcial |
| QA a 1/4 da resolução a cada ~0,4 s, recortes em tamanho real | `render_dom.mjs stills` + `scripts/sheet916.py` / `contact_sheet.py` | feito |
| Montagem num passo só, ffmpeg libx264 crf 15, nome temporário e renomear | `render_dom.mjs video` (crf 15, BT.709, `.tmp.mp4` → renomeia) | feito |
| ffprobe e quadros em volta de cada transição | `qa.md` | feito |

Armadilhas do brief que valem para nós: nunca montar objeto 3D com camadas CSS `preserve-3d` + `backdrop-filter`
(rasga e briga em z); separar texto em palavras sem destruir filhos referenciados (`split()` em anim.js preserva
elementos); ao mudar o tamanho do canvas, recalcular a focal (relativa à altura).

## Entregas
1. Fase 2: quadros + folha rotulada, e espera.
2. Fase 3: MP4 final, cópia de prévia e resumo batida a batida. **Avise antes quanto tempo o render leva.**
   Referência medida nesta máquina: DOM 1080×1920 a 60 fps, 40 s = 2400 quadros em ~2,5 min.
   O usuário prefere **1080p** (já pediu "só 1080p" duas vezes): pergunte antes de gastar tempo em 4K.
