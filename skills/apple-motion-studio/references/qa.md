# QA antes de mostrar (etapas 4 e 6)

Três instrumentos pegam quase tudo: a **contact sheet de stills** nas transições, o **gráfico de posição/velocidade**
de quem se move (a página é função pura de t, então dá para amostrar `renderAt` ou as funções de curva) e a **energia do
áudio sobre as marcas de `EVENTS`** (`mix.py` e `finish.py` já imprimem).

## Checklist (B = bloqueia a entrega)
| # | O quê | Como | Passa se |
|---|---|---|---|
| 1 | Storyboard aprovado | conversa | "aprovado" explícito (B) |
| 2 | Determinismo | mesmo frame 2×, ordem salteada | idêntico; nada de Date.now/random sem seed (B) |
| 3 | Zero dissolve entre planos | ler o bloco `B` | cada transição nomeia a forma que vira a próxima (B) |
| 4 | Câmera monotônica | derivada por frame | sem troca de sinal (B) |
| 5 | Overshoot | pico/alvo | ≤ 3 %; ≤ 10 % só no hero; 0 em texto, logo, câmera |
| 6 | Juntas | stills em 3–4 pontos de cada transição | sem kink, sem forma invertida, sem pulo de escala 2D→3D, sem headline sumindo |
| 7 | Densidade e repetição | contar por still | 1 foco + 2 secundários vivos; nenhum layout/elemento repetido entre planos |
| 8 | Composição | `scripts/grid.py` ou olho | foco no centro; nada colidindo com a headline; nada cortado na borda |
| 9 | Texto | ler a folha | sentence case, ponto final, sem erro de português; hold ≥ max(1,2 s; car/12)+0,3 s |
| 10 | Vidro | stills | fundo refratado visível; ≤ 1 vidro dominante; texto legível |
| 11 | Luz e cor | stills | uma direção de luz; um acento; fundo com cor, sem cinza chapado |
| 12 | Técnica | still a 100 % | sem aliasing, linha fina piscando, textura pixelada no zoom, fantasma de motion blur |
| 13 | Encode | `ffprobe -show_entries stream=color_space,color_primaries,color_transfer` | bt709 nos três; 25 fps CFR; duração = TOTAL |
| 14 | Sincronia | saída do `mix.py` | todos os cues 0 ms; impactos 0 a +1 frame (B se adiantado) |
| 15 | Drop | "RMS around the drop" do `finish.py` | silêncio antes, salto no frame do reveal |
| 16 | Loudness | saída do `finish.py` | −14 LUFS ±1, TP ≤ −1 dBTP |
| 17 | Flash | revelação de luz no drop | ≤ 3 flashes/s; sem transição de vermelho saturado (B) |
| 18 | Licenças | `audio-library/LICENCAS.txt` | todo asset com licença comercial; CC BY creditado (B) |
| 19 | Originalidade e claims | revisão | nenhuma marca/fonte/som da Apple; claims verdadeiros; nome fictício checado (B) |
| 20 | Playback humano | o usuário assiste e ouve | você não declara pronto só por stills (B) |

## Diagnóstico rápido
| Sintoma | Causa provável | Conserto |
|---|---|---|
| parada seca | `lerp` sem easing | token `sp()` ou `outExpo` |
| gelatina | bounce alto (ζ < 0,6) | `heavy` ou `smooth` |
| dominó mecânico | atraso `i*k` | stagger suavizado ou por distância ao centro |
| câmera nervosa | tweens encadeados | uma curva monotônica |
| elementos colados no fundo | sem sombra/DOF comuns | sombra da luz-chave + DOF no 3D |
| "simples demais" | só o foco na tela | chips de vidro, partículas, fluxo, contador, callout |
| "repetido" | mesmo layout em dois planos | outra gramática de câmera/composição |
| "preto e branco" | fundo neutro, sem acento | `paintBG` com luz quente + fria, um acento |
| som "na frente" | cue posto à mão | ancorar em `EVENTS`; `align: start` em booms de pico tardio |
| drop fora do reveal | faixa cortada a olho | `finish.py --probe` + `--music-drop/--film-drop` |

## Como reportar
Diga em poucas linhas o que checou e o que não dá para checar daqui (playback em tempo real, o som). Mande a contact sheet
ou o MP4 com SendUserFile.

## O que é verificado por código (24/11/2026) × o que ainda é olho
| Falha | Verificação executável | Teste |
|---|---|---|
| foto/imagem obrigatória ausente, corrompida, sem vínculo, invisível, pequena | portão de assets no `render_dom.mjs` | `tests/run_studio_lume.py` |
| fonte/imagem que não carrega, cena sem contrato, erro de JS, 404, espera infinita | `anim.js` + `sequence.html` + CDP no render | `tests/run_render_errors.py` |
| preto, branco, congelado, quadros repetidos, fps/duração/resolução, decodificação | `scripts/qa_frames.py` (blackdetect, negate+blackdetect, freezedetect, diferença por quadro, ffprobe) | `tests/run_frame_qa.py` (19 casos, inclusive intencionais) |
| lacuna/sobreposição de cenas, cena fora de quadro inteiro | `qa_frames.py --timeline` | idem |
| áudio clipado, silêncio não declarado | `qa_frames.py --audio` (astats, silencedetect) | idem |
| master sobrescrito por render ruim | `.tmp` + rename, `--replace`, `studio.py promote` | `tests/evidence/07-versionamento` |
Ainda só por olho/documentação: texto cortado, sobreposição de elementos, logo deformado, contraste, saltos de câmera,
toque fora do botão, flash (WCAG), qualidade perceptiva do som. Os detectores **localizam** intervalos; a intenção vem do storyboard.

## Revisão localizada: conferir também o som decodificado
Uma revisão de tempo ("atrase a notificação 6 quadros") só está entregue quando o deslocamento aparece **no áudio do MP4
final**, não só na timeline: `tests/run_revisao_audio.py` mixa pelo `EVENTS`, muxa, decodifica o áudio do MP4 e mede o onset
(validado: Δ = 0,200 s = 6,0 quadros; erro vs. batida 0,02 ms). Para um filme, a mesma medida no master: onset do evento
principal a ≤ 1 quadro da batida.

## Composição: legendas, texto e transições (por amostragem, com cobertura registrada)
"Zero erros" só significa algo junto de **quantas** amostras e **quais** instantes foram vistos.
- Marque no HTML os papéis que não podem colidir: `data-qa="headline|legenda|prova|cta"`; `data-qa-required="1"` no que
  não pode sumir (a área que comprova a promessa).
- Declare as janelas críticas em `window.TIMELINE`: `transitions: [{from, to}]` (amostra a cada 2 quadros + auge + último
  quadro — começo/auge/fim sozinhos deixaram passar uma colisão real no teste 13), `critical: [{from, to}]` (a cada 0,1 s);
  `window.CAPTIONS` (1º, meio e último quadro de cada linha).
- `node scripts/render_dom.mjs layout <pagina> <pasta> --root <projeto> [--times a,b]` → `layout.json` com o número de
  amostras, os instantes, colisões e sumiços por instante, e o **mesmo quadro por salto direto × por sequência** (estado vazando
  entre quadros aparece aqui). **0 amostras = falha por cobertura insuficiente.**
- Legendas: `scripts/captions.py` importa SRT/VTT ligando a uma versão do áudio, guarda tempos em quadros (fronteira comum = sem
  sobreposição e sem quadro vazio), `revise` uma frase regravada (anteriores preservadas, posteriores deslocadas e listadas) e
  `check`/`export`. Palavra por palavra só quando a peça destaca palavras; confiança de transcrição pode ficar `null`. Revise
  nomes próprios, siglas e o português do cliente. Na vertical, confira no tamanho final se a legenda cobre a prova.
- Continua valendo: erros de JS/iframe, fontes, rede, assets, congelamentos e lacunas de timeline (render e `qa_frames.py`),
  com holds, fundos sólidos, fades e silêncios intencionais declarados. Evidência: `tests/run_legenda_qa.py`.
