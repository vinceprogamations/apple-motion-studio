# Storyboard (etapa 2) — e o checkpoint do modo

Objetivo: antes de qualquer linha de animação, um storyboard **numerado com quadros reais renderizados**. O que acontece
depois depende da delegação (`references/autonomia.md`, `studio.py state gate <projeto> storyboard`):
- **guiado**: mostre e pare. Nada é animado, renderizado ou sonorizado até "aprovado" / "sim" / "pode fazer". Notas não são aprovação.
- **autônomo**: faça a revisão interna abaixo (§ 3), registre `state decide … storyboard "<direção>" "<em que quadro nasce a compreensão>"` e siga.
- **híbrido**: pergunte só se o storyboard foi reservado; senão siga como no autônomo.

Templates: `templates/storyboard-board.html` (grade 3 colunas) e `templates/storyboard.html`.

## Resolva a ideia antes do estilo
1. **Promessa em uma frase** e a pergunta que decide o filme: *em qual quadro ou ação o espectador percebe que a promessa se
   cumpriu?* Antes de engine ou efeito: qual situação muda, quem provoca a mudança, qual detalhe o público precisa ler.
2. **Duas tiras curtas com premissas visuais distintas** quando o roteiro admite soluções diferentes (não para uma revisão de
   seis quadros: aí trabalhe só no trecho). Ex.: "encontre um horário em comum" → (a) duas agendas que se sobrepõem e revelam
   a vaga; (b) duas pessoas trocando mensagens até as duas receberem a confirmação; (c) tipográfica: "QUANDO?" toma o quadro
   e as datas descartadas dão lugar à escolhida. No modo autônomo, escolha você e registre o porquê.
3. **Miniaturas com o texto real**: onde o olhar entra, o que lê primeiro, que relação de escala ajuda, o que pode sair.
   Teste silhueta, fotografia, colagem, poucas formas ou perspectiva conforme a marca. Estilo, beat sheet, quadros de entrada e
   saída e mapa de atenção podem dividir a mesma prancha.
4. **Peças móveis e oclusão**: ordem de oclusão, máscaras, o que a câmera vai revelar. Se o produto sai da frente, o fundo que
   aparece precisa existir. Textura e recorte conferidos no tamanho final (na cerâmica a luz revela o relevo; numa interface a
   mesma textura pode encobrir o nome que precisa ser lido).
5. **Leia em sequência no tamanho de um celular** e assista ao animatic **sem som**: o que se entende só pela imagem? Depois
   confira o que a faixa acrescenta. Peça narrada pode depender da fala de propósito — preserve o papel de cada canal.
6. **Preferências com escopo**: uma escolha aprovada vale para aquele filme/marca, não vira regra global. Repertório por tipo
   de problema: `references/repertorio.md`.


## 0. Guia de estilo (fase 1 do brief) e material da marca
- Leia `launch-film-brief.md`. Escreva o guia de estilo (paleta hex, luz, materiais, câmera, tipografia, composição, o que faz parecer caro) antes de desenhar.
- **Marca real**: procure documentos e artes dela no projeto **e na pasta Downloads do usuário** (`%USERPROFILE%\Downloads` / `~/Downloads`). As regras da marca vencem o resto (paleta, fontes, transições, endcard, regras do logo).
- **Fotos realistas** (pessoas nos perfis, ambientes, produtos de loja): quando o usuário autorizar, gere pelo meio autorizado (ex.: ChatGPT no navegador dele, modo assistido) (prompts em português, foto realista, "sem texto, sem logos"; grade 3×2 de rostos numa imagem só e recorte depois). Baixe com um `<a download>` apontando para o blob da imagem gerada, depois que a geração terminar. Registre em CREDITOS que são geradas.

## 1. Conceito
- Uma jornada em **5–8 planos** (≈2,5–3,5 s cada): gancho → problema → ação → recompensa → prova → logo/CTA.
- **Um objeto recorrente** que a história transforma (ex.: anel → íris → celular → widget → logo; ponto de luz → sol → dial → cartão de vidro → aparelho 3D → anel do logo).
- Headlines curtas em português, sentence case, terminando em ponto. CTA honesto.
- Cada plano diz **como vira o próximo** (morph de forma, máscara pelo furo, mergulho na tela, vidro que materializa,
  dot-dissolve da marca, giro de borda). Nunca dissolve cruzado.
- Marque também a **batida de som-âncora** de cada plano (toque, pouso, riser, drop). O drop da música cai no reveal principal (≈ 55–65 % do filme).
- Tipos de produto diferentes têm que PARECER diferentes: num leque "cada negócio", mostre um sistema (dashboard claro), uma landing page (foto grande + CTA) e uma loja (grade de produtos com preço). Perfis sempre com foto de pessoa.
- Densidade: planeje 1 foco + 2 secundários por plano e não repita o mesmo layout/elemento em dois planos, salvo quando a repetição é o motivo (ex.: sobrecarga proposital).

## 2. Quadros (renders reais, não rascunhos)
**Resolução final** (brief): 4K 16:9 = janela 1920×1080 com `--force-device-scale-factor=2`; Reels = 1080×1920 ×2. Pipeline DOM: `templates/dom/scene.html` + `render_dom.mjs stills`. Reels: área segura — títulos a partir de y ≈ 250, CTA/endcard acima de y ≈ 1600 (legenda e botões do Instagram cobrem o resto).
Para cada plano, uma página HTML estática (1920×1080, ou 1080×1920 para 9:16) mostrando o instante com mais coisa na tela:
- `common.css` compartilhado: fundo escuro **com cor** (luz-chave quente/fria radial, nunca cinza chapado), grão sutil,
  Inter (`templates/dom/fonts/Inter-Variable.ttf`), headline 76 px peso 600, tracking −0,035em, gradiente branco→cinza na parte de baixo das letras.
- Celulares: laje arredondada com moldura de titânio em gradiente, vidro preto, dynamic island, UI realista dentro.
- Vidro: fundo real borrado e saturado por trás (`backdrop-filter: blur(20px) saturate(1.6)`), borda clara de 1 px, especular no topo.
- Ação **no centro**; espaço para a headline em cima (ou embaixo no 9:16).
- Renderize cada página headless:
  - Windows: `"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=1920,1080 --virtual-time-budget=4000 --screenshot=<abs>/N.png file:///<abs>/N.html`
  - Mac: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"` com as mesmas flags.
- Converta para JPEG (PIL) e monte a folha: `python scripts/contact_sheet.py frames/ review.jpg`.

## 3. Revise seus quadros antes de mostrar
Veja cada quadro inteiro **e recortes 1:1** (bordas do celular, texto pequeno, materiais).
- círculo de toque exatamente sobre o botão
- texto centralizado nos anéis e sem colidir com cartões
- nada cortado na borda sem intenção
- sem névoa cinza (vinheta/glare forte demais)
- tamanhos de headline consistentes entre planos
- nenhum plano parecido demais com outro
Corrija, renderize, olhe de novo.

## 4. O board
Preencha o board: número, faixa de tempo, título, descrição, **linha amarela = o que se move**, **linha verde = como vira
o próximo plano**. Cabeçalho com marca, duração, formato e regras de estilo. Screenshot em 1920×1480 (16:9) e confira se
o texto de baixo não foi cortado.

## 5. Checkpoint
- **guiado**: envie `storyboard.jpg` + tabela curta (#, tempo, plano, transição) + suposições (idioma, CTA, nome fictício a
  verificar). Peça aprovação ou notas e **pare**. Só depois de "aprovado" vá para a etapa 3.
- **autônomo**: guarde o board no projeto, registre a decisão (`state decide`) com a direção escolhida e o quadro em que nasce
  a compreensão, e siga. O board acompanha a entrega como nota de direção.
