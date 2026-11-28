# Som (planejado no storyboard, editado e mixado depois da imagem)

O som é planejado desde o storyboard (ritmo, perspectiva, contato, silêncio, voz) e editado/mixado **depois** da revisão
visual que o modo de delegação prevê — qualquer mudança na animação move as batidas. Quem decide o quê:
`references/autonomia.md` (modos, escolha de música reproduzível, voz, revisão de timbre, QA da entrega).

## Direção sonora
1. **Comece pelo momento que merece ser ouvido**: o instante em que o benefício fica evidente. Para cada trecho decisivo
   anote o primeiro plano sonoro, a camada que recua e o motivo de uma pausa. Se a fala diz o nome do produto, dê espaço ao
   nome; se o toque de um fecho prova o acabamento, esse contato ocupa o primeiro plano sem voz.
2. **Peso e distância**: separe ataque, corpo e cauda quando isso der controle. Botão físico leve: contato plástico curto;
   metal pesado: ataque curto + uma ressonância que pertença à peça. A ambiência situa o espaço e pode atravessar um corte.
   Em demo de software, diga quando um som é acento editorial. Família de feedback: confirmação ≠ atenção ≠ erro, mesmo timbre
   de marca, variação só quando fizer sentido.
3. **Perspectiva**: para sons do mundo da cena, anote a fonte e de onde o espectador a ouve (tomada próxima, distante, ou
   ouvida através de um aparelho — um rádio na bancada soa pequeno e integrado ao cômodo). Prefira uma tomada com a perspectiva
   certa a fabricar distância só baixando o volume; se simular (alto-falante + ambiente), preserve o original e deixe direto e
   tratamento separáveis. No corte para o close do produto, decida o que muda entre detalhe e espaço.
4. **Mapa de áudio sobre eventos e frases**: evento visual (`window.EVENTS`), quadro de referência, parte do som que coincide
   (`align: start | peak | end`), antecipação/atraso intencional e stem (`"stem"` no cue). Um som de abertura pode começar antes
   do corte; o clique de confirmação coincide com o estado confirmado. Emendas de música em fim de frase, nunca no meio de uma
   sílaba cantada.
5. **Mixe para o conflito observado**: grupos editáveis (voz, música, foley/efeitos, ambiência — `mix.py --stems`). Se uma
   batida esconde o clique principal, tire ou desloque a batida antes de subir o clique no filme todo. Voz mascarada: automação
   da música **naquele intervalo** (`synth_music.py --voice-gap a-b:dB` ou `env` do bed) e confira a recuperação entre frases.
6. **Confira a entrega que vai tocar**: `qa_audio.py deliver <final.mp4>` (duração, canais, loudness, true peak no arquivo
   decodificado, mono, silêncios contra a timeline). `finish.py` já mede o true peak do MP4 e corrige o excesso do AAC.

Fontes que fundamentam: Apple *Designing Sound* (WWDC17-803: gravar objetos ligados ao produto, ouvir o som recorrente em
sequência no aparelho); *Explore immersive sound design* (WWDC23-10271: posição, variação, sutileza; em estéreo, preserve a
leitura em mono); Mark Mangini sobre o foley de *Blade Runner 2049* (passos gravados na distância coerente com a ação); Adobe
(remix por estrutura musical; ducking como automação editável); EBU R 128 s1 (comerciais: −23 LUFS, curto prazo ≤ −18,
−1 dBTP — só quando o destino pede); FFmpeg (medição, loudnorm em duas passadas, crossfade, sidechain); a licença de cada asset
(ex.: Sonniss GDC: mixado num filme ≠ redistribuir os efeitos isolados). Revisão de timbre em linguagem comum e perspectiva
sonora: ideias de [ui-sound-design-skill](https://github.com/dannyjpwilliams/ui-sound-design-skill/blob/6cb4be41a19a5556ffd94f04e641e18b623ac483/skills/ui-sound-design/SKILL.md)
e [clawfu sound-design-film](https://github.com/guia-matthieu/clawfu-skills/blob/4108f5c010ccaa8b5707fa05ca1d888ae167e548/skills/audio/sound-design-film/SKILL.md), em redação própria.


## Biblioteca (`audio-library/`)
| Pasta | O que tem | Licença |
|---|---|---|
| `sonniss-gdc2026/` | ~40 WAVs 96/192 kHz: impactos, booms de trailer, bass drop, metal, vidro, papel, interruptores, latches, shimmer, whooshes de vento/metal | Sonniss GDC: royalty-free comercial, sem crédito; **não redistribuir** (pasta no .gitignore) |
| `sfx/ui-interface`, `ui-clicks`, `impacts`, `digital-tones`, `sci-fi`, `glass` | Kenney | CC0 |
| `sfx/ui-premium`, `whoosh-transitions` | Mixkit | Mixkit License |
| `sfx/synth-kit` | gerado por `synth_sfx.py` | próprio |
| `music/product-launch/` | 3 faixas Pixabay (a referência do usuário inclusive) | Pixabay (comercial ok; checar Content ID) |
| `music/fma-electronic/` | Koi-discovery (CC0), laser butterfly, Aldous Ichnite | ver `LICENCAS.txt` (CC BY exige crédito) |
| `music/minimal-tech/` | Mixkit "Digital Clouds" (trilha do Nuvra) etc. | Mixkit License |
| `elevenlabs/` | gerados no plano gratuito | **sem uso comercial** |

Para mais Sonniss: o pacote GDC está online como zip grande; leia só os arquivos escolhidos por HTTP Range (índice do zip
+ range de cada membro), sempre com User-Agent de navegador (senão 403). Não baixe Pixabay/Mixkit em massa por script:
use o botão do site no navegador, poucos itens, com o usuário logado.

## Escolher o som de cada batida
Pergunta-guia: **"o que este objeto está tentando dizer?"** Se o som não responde, deixe em silêncio.

| Intenção | Timbre / material | Exemplos da biblioteca |
|---|---|---|
| peso, escala | escuro, thump, sub 40–80 Hz, cauda longa | booms de trailer, bass drop, metal thud |
| leveza, precisão | brilhante, ataque seco, HPF 150–300 Hz | interruptor, latch, key press, cartas |
| vidro/cerâmica | muito brilhante, "ring" médio | glassy snap, shimmer de sino pequeno |
| energia/luz | textura que cresce, filtrada | energy flow, arc power-up, magic light |
| movimento | whoosh **só quando algo se move** | wind rush, metal slow whoosh, sweep |

Evite: dings e sinos óbvios, digitação, zumbidos contínuos, lasers/8-bit, o mesmo arquivo idêntico repetido (varie `pitch` 0,92–1,15 e ±1–2 dB).

## Sincronia (25 fps, 1 frame = 40 ms)
- **A trilha tem de estar na grade dos cortes.** Meça o andamento com `python scripts/batidas.py <trilha> --grade <período dos cortes>`,
  que usa três bandas e vários trechos e fica com a mais consistente (em garage sincopado, a banda do chimbal). Depois, ou corte
  nos múltiplos do período medido, ou estique a trilha com o `atempo` que o script dá. Erro do filme de academia (26/11/2026): a
  grade de 0,4645 s, estimada por picos de volume, contra a trilha real de 0,4626 s fez a música deslizar ~60 ms até o logo, e
  o usuário notou "desincronia no fim".
- **Golpes com ataque lento** (booms de trailer, whooshes, arpejos): alinhe pelo **pico** (`"align": "peak"`). O `mix.py` avisa
  quando um efeito alinhado pelo início tem o pico mais de 80 ms depois. Leia os AVISOS: são intencionais só quando o som constrói
  para dentro do evento.
| Evento | Regra |
|---|---|
| impacto, pouso, clique, toque | pico no frame do contato ou +1 frame; **nunca adiantado** mais que ~20 ms (som adiantado é o erro que o olho pega) |
| whoosh | pico na velocidade máxima / passagem pelo centro; ataque 4–10 frames antes |
| riser → reveal | termina no frame do reveal ou 2–6 frames antes, deixando silêncio; hit + sub no reveal |
| texto palavra a palavra | tick opcional no início do blur→nítido, −18 a −24 dB abaixo do hit |
| saída | cauda continua 300–1000 ms; nunca truncar |

## Fluxo
1. `window.EVENTS` na página, derivado de `B` (inclua batidas derivadas: cada chip, cada pulso, cada pouso). Depois:
   `node scripts/render.mjs events <filme>.html sound/events.json [--gpu]`.
2. `sound/cues.json` — uma entrada por batida:
   ```json
   {"event": "drop", "file": "DSGNBass_Bass Drop", "db": -21, "align": "start", "dur": 2.6}
   {"event": "card.b", "offset": 0.04, "file": "PAPRHndl_Game Play Cards", "db": -25, "align": "peak", "pitch": 1.08}
   {"at": 3.36, "file": "UIMisc_Kalimba 3 Up", "db": -24}
   {"type": "bed", "file": "magic, energy flow, astonishment", "event": "logo.move", "to_event": "logo.land", "from": 16.0, "db": -27, "fade_in": 0.5, "fade_out": 0.12}
   ```
   - `align: peak` para hits, pops, whooshes curtos; `start` para booms/drops **cujo pico de loudness vem tarde** e para
     beds; `end` para risers que acabam no reveal. `dur` corta caudas longas ou o riser no ponto da parada.
   - `lp`/`hp` para amaciar, `pitch` para variar repetições, `pan` para largura.
3. `python scripts/mix.py cues.json "<Filme> - SFX.wav" --lib ../../audio-library/sonniss-gdc2026 --lib ../../audio-library/sfx --events events.json --len <TOTAL+0.4>`
   — ele imprime o desvio de cada cue (tem que dar 0 ms; mais de 1 frame é bug).
4. Trilha: ache o drop do arquivo (`python scripts/finish.py --probe --music <faixa> --probe-from <s>` imprime RMS a cada
   50 ms; o drop é o salto de ~−35 para ~−5 dB depois do silêncio) e escolha o evento do reveal no filme.
5. `python scripts/finish.py --video "out/<Filme> - 1080p.mp4" --sfx "<Filme> - SFX.wav" --music <faixa> --music-drop <s> --film-drop <s> --out "out/<Filme> - FINAL 1080p.mp4"`
   - Corta a faixa para o drop cair no reveal, fade in 0,4 s / out 1,1 s, SFX +9 dB e música −8 dB (os ganhos que
     funcionaram nos três filmes), `amix normalize=0`, loudnorm em 2 passadas para −14 LUFS / −1 dBTP, e junta com BT.709.
   - Se o filme precisa de mais energia depois do drop do que a faixa dá: `--bpm 110 --repeat 1 3` repete os compassos
     1–3 depois do drop com crossfade de 15 ms (edição sempre em limite de compasso, nunca time-stretch).
   - Confira a linha "RMS around the drop": silêncio (≈ −25 a −35 dB) logo antes e salto (≈ −7 dB) no frame do reveal.
6. Mande o MP4 e peça para ele **ouvir**: você não escuta a mix.

## Hierarquia da mix (sem voz)
Música = cama; hit do reveal +3 a +6 dB acima da música naquele instante; SFX de material −6 a −12 dB abaixo do hit;
ticks −18 a −24 dB. SFX de UI com HPF 100–200 Hz; sub só no drop. Com voz: música duckada 6–10 dB.
Entrega para redes: −14 LUFS integrado, ≤ −1 dBTP, 48 kHz, AAC 320k.

## Música no estilo Apple (curadoria)
Resumo do texto de referência que o usuário mandou (curadoria musical da Apple):
- **A música dita a montagem**: cortes, aberturas de tela e toques caem nas batidas/viradas; sons reais do produto entram na grade rítmica como percussão (foley musical).
- **Descoberta indie em vez de hit saturado**, e **contraste**: quanto mais frio/limpo o visual, mais orgânica, calorosa ou excêntrica a música.
- **Por linha de produto**: iPhone Pro = eletrônica experimental, UK garage, hip-hop alternativo, grave marcante (potência, modernidade); Mac/iPad Pro = soul alternativo, downtempo, jazz-fusion, post-rock (fluidez, foco); AirPods = house melódico, eletrônica imersiva com sub limpo; Watch = pop energético, percussão acelerada, respiração/batimento.
- **2020–2026**: UK garage, afro-house, jazz londrino contemporâneo, hip-hop experimental; edições instrumentais sob medida para 30–90 s com a curva de energia acompanhando as revelações.
- Letra, se houver, funciona como slogan oculto.
Nunca use as faixas reais dos comerciais da Apple (licenciadas; Instagram/YouTube bloqueiam). Procure equivalentes livres.

### Como achar e baixar
1. Busque por gênero no Pixabay (`pixabay.com/music/search/uk garage/`, `future garage`, `melodic house`, `afro house`) ou FMA. Prefira faixas sem o selo "AI" (o card mostra "Shield AI") e **sem "YouTube Content ID"** (aparece no pop-up depois do download).
2. Baixe pelo **Chrome do usuário** (logado; "downloads múltiplos" liberado para o Pixabay): na página da faixa, clique o botão "Free download" e **espere ~6 s antes de navegar**, senão o download é cancelado. O navegador embutido do app não baixa do Pixabay (fica em "Downloading..."). Poucos arquivos, nunca em massa por script.
3. Mova de `Downloads` para `audio-library/music/<estilo>/` (o projeto já tem `apple-style/` com 6 faixas) e registre em `LICENCAS.txt` com a nota de Content ID.
4. `python scripts/music_scan.py audio-library/music/apple-style` ranqueia por punch (transientes/s), grave e drops sem ouvir. Só o punch engana (a escolhida, "Slow Dreams", deu 1,7/s): pads "de igreja" = punch baixo E volume chapado sem drops; boas opções têm grave forte (> 0,8) e quedas seguidas de drops que caem num reveal.
5. **Modo autônomo**: escolha pelo `music_pick.py` (autorização → encaixe) e registre o motivo em uma frase. **Música
   reservada ao usuário**: `music_pick.py --ab` (recomendação + alternativa no mesmo trecho, loudness comparável) e só essa
   pergunta. Sem escuta disponível, declare "medido, não ouvido".

## Música nova
- BPM que cai em frames inteiros a 25 fps: 125 (12 f), 100 (15 f), 150 (10 f). 120 BPM = 12,5 f, evite se tiver animação no tempo.
- Cortes em downbeats; silêncio antes do drop de 1–2 batidas (480–960 ms a 125 BPM; o Nuvra usou ~0,5 s).
- Suno/ElevenLabs Music só se ele pedir e com estimativa de créditos; licença comercial exige plano pago.
- Créditos CC BY vão em `<filme>-ad/CREDITOS.txt`; licenças novas em `audio-library/LICENCAS.txt`.
