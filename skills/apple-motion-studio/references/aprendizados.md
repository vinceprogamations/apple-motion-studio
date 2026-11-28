# Aprendizados de produção (com caso, evidência, quando usar e teste)

Leia no início de cada filme. Uma **decisão do usuário** vale como padrão para os filmes seguintes. Números de um plano
específico ficam ligados ao caso e não viram regra. [hip] = hipótese ainda não testada.
Fontes:

## 1. Ordem das decisões (evita retrabalho)
| Aprendizado | Caso / evidência | Quando | Como testar |
|---|---|---|---|
| **Textos e música antes do storyboard**; SFX por último, sobre a imagem pronta | filme de Natal: slogan repetido; o usuário pediu a ordem nova (27/11/2026) | Sempre (decisão do usuário) | Existe `copy.md` com o roteiro + trilha registrada com o drop antes do 1º still |
| Imagens novas por vaga, nunca repetir as de outro filme | Pedido v1 reprovado ("usam imagens que você já usou") | Sempre | `asset-manifest.json` com origem e data de cada imagem |
| Música: nunca repetir (oferecida também conta) | `audio-library/USADAS.json` | Sempre | `trilhas.py livre` antes de oferecer |

## 2. Câmera, transições e continuidade
| Aprendizado | Caso / evidência | Quando | Como testar |
|---|---|---|---|
| O último quadro de uma cena é o primeiro da seguinte (sem dissolve) | Pedido: azul do flash → cartão da conversa; janela montada → frente do leque | Toda passagem | Comparar quadro N e N+1 do corte: mesma forma e posição |
| Holds com push contínuo (nunca quadro parado) | Pedido v1: `qa_frames` acusou freeze em 23–25 s | Toda frase em tela | `qa_frames` sem `freeze` fora de `INTENTIONAL` |
| Esconder grupo por `opacity`, não por `visibility` | Pedido s1: filhos com `visibility: visible` reapareceram sob o flash | DOM | Still no instante do flash |
| Primeiro quadro nunca vazio | Pedido v1: branco em 0–0,17 s | Abertura | `qa_frames` sem `white` no início |
| Clarão/círculo de fecho em pérola, não branco puro | filme de Natal (QA) + Apple Christmas revalidado: RGB ≈ (231, 230, 231) | Wipes claros | Luma 225–235 no quadro coberto |

## 3. Leitura do texto
| Aprendizado | Caso / evidência | Quando | Como testar |
|---|---|---|---|
| Tema claro: sobrescrever o gradiente branco que o `anim.js` injeta em `.hl .w` | Pedido v1: títulos invisíveis | Fundo claro | Still com o título |
| Texto importante fora das áreas da interface do Reels | Pedido: comentário movido para a esquerda | 9:16 | `qa_celular.py` sem texto nas áreas |
| Método completo de copy | `references/copy.md` | Sempre | Checklist do `copy.md` |

## 4. Qualidade de assets e coerência física
| Aprendizado | Caso / evidência | Quando | Como testar |
|---|---|---|---|
| Interfaces realistas: janela com barra macOS e URL fictícia, loja com header/carrinho, agenda tipo calendário semanal | Pedido v1 reprovado ("não parece um site") | UI em cena | Storyboard aprovado |
| Cada foto é sua própria vaga `data-asset` (o portão mede o tamanho real) | Pedido: avisos de resolução falsos com a vaga na janela inteira | Fotos dentro de UI | `render_dom` sem aviso de resolução |
| **Aparelhos fisicamente coerentes**: peças fixas presas, pivô na dobradiça, folga ao fechar | filme de Natal: teclado solto e tela girando no centro (2 notas) | Todo 3D | Caso de regressão em `references/blender.md` |
| **Squircle em tudo que é arredondado** (ícone, card, janela, celular, botão); círculos verdadeiros ficam round | Pedido do usuário com referências de superelipse n = 4 (28/11/2026) | Sempre (decisão do usuário) | Recorte 1:1 de um canto: curvatura contínua; `corner-shape: squircle` no CSS |
| **Celular = moldura real do modelo 3D**, não squircle de CSS; tela recortada pela máscara renderizada | Raiz v3: "o iphone não é squircle em tudo" (28/11/2026) | Todo celular em cena | `scripts/blender/device_front.py` + `buildIphone()`; still com a ilha preta e borda fina |
| **Formulário/agenda na mesma linguagem da landing** (cores, foto, tipografia) e sem área vazia | Raiz v3: agenda branca "foge da continuidade" e com muito espaço livre | Toda seção de UI | Still da seção: mesmo fundo/acentos do topo; janela preenchida |
| **Respingo líquido em cor chapada**, sem luz/brilho/sombra | Raiz v3: volume iluminado "dá estranheza" | Respingos SVG (goo) | Still no pico do respingo |
| Detalhes reais (teclado com layout, teclas baixas e foscas) | filme de Natal: "olha esse teclado" | Close de aparelho | Recorte a 100 % |

## 5. Música e sincronismo
| Aprendizado | Caso / evidência | Quando | Como testar |
|---|---|---|---|
| Electronic/dance de lançamento com build → silêncio → drop; nada de piano ambiente | Memória do usuário; Pedido: escolheu "Club" (dance 4/4) | Padrão | O usuário aprova |
| Natal: trilha comercial polida (guizos + metais + batida), nunca EDM brega de sininhos | filme de Natal: "Bells of Yule" reprovada; "Christmas Celebration" aceita | Peças de época | — |
| Alinhar o drop da trilha à virada (`finish.py --music-drop X --film-drop Y`) | Pedido 11,2 s; Natal 10,75 s ("Seu sistema,") | Sempre | RMS por 0,05 s em volta do drop |
| SFX inéditos: checar por **substring** nos cues de todos os filmes (os nomes antigos são abreviados) | Pedido: 10 efeitos já usados passaram na checagem por nome exato | Sempre | Script de substring antes do mix |
| Ataque atrasado: `align: peak` em pops e cliques | Avisos do `mix.py` | Sempre | `mix.py` com 0 avisos (ou intencionais) |
| Pixabay: Content ID e "AI generated" na página, um download por vez; sem raspagem em massa | Bloqueio do classificador na varredura em lote | Downloads | Linha em `LICENCAS.txt` com o link |

## 6. Blender (resumo; detalhes em `references/blender.md`)
- 10 s/quadro a 1080×1920, 48 amostras + denoise na RTX 3050 (filme de Natal, 516 quadros ≈ 85 min).
- Cada plano roda separado, com o motion blur próprio: os cortes não borram.
- Camada 2D (títulos, pílula, clarões, círculo do logo) em HTML sobre os PNG do Blender, numa página `renderAt` que carrega o quadro.
- Gravar a posição de tela dos objetos (`world_to_camera_view`) para a camada 2D nascer deles (círculo do logo).
