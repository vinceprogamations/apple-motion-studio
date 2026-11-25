---
name: apple-motion-studio
description: Vídeo comercial, apresentação comercial animada, Reels e filme de produto com som, feitos como código (HTML/CSS, canvas, Three.js, Blender) e renderizados em MP4 1080p/4K, sem gerador de vídeo por IA. Cobre briefing (com catálogo de 14 estudos de caso) → storyboard → animação → render com portões automáticos → som e mix → QA → master, com modos guiado, híbrido e autônomo ("faz tudo aí"). Use SEMPRE que o usuário pedir vídeo, filme, Reels, anúncio, comercial, apresentação comercial ou pitch em vídeo, motion graphics, logo animado, storyboard ou sonorização; quando delegar a produção ("faça tudo", "decide por mim"); ou quando der uma nota num filme já feito (atrasar um evento em N quadros, trocar uma foto, deixar um som menos estridente, mover uma legenda). Para slides estáticos editáveis (.pptx/Google Slides) prefira uma skill de apresentações; aqui a apresentação vira vídeo animado.
---

# Apple Motion Studio

Comerciais dirigidos por código: cada quadro é função do tempo (`renderAt(t)`), então "atrase a notificação em seis
quadros" ou "troque a foto deste perfil" vira uma mudança localizada e um re-render reprodutível. O caminho padrão é
gratuito (Chrome headless + FFmpeg + bibliotecas locais). A Apple é referência de precisão, composição, materialidade,
tipografia e som; a linguagem de cada filme nasce da marca, do público e da ideia. Fale em português, curto e direto.

## Primeira resposta a um pedido novo (antes de qualquer produção)
Se o pedido **não** delega ("faz tudo aí", "decide tudo", "a direção é sua") e **não** diz "sem cases", a primeira resposta
termina na escolha do usuário. Mesmo numa execução não interativa, **não produza a peça nesta resposta**. A resposta tem, nesta ordem:
1. **Uma linha com o que você entendeu:** formato (aqui, apresentação = **vídeo animado** 16:9; para slides editáveis existe outra skill), duração proposta, marca e material encontrados.
2. **O bloco de estudos de caso** que `python scripts/casos.py sugerir "<pedido>" --projeto <projeto>` imprime, com até duas referências, *por que combina* e *quando pode piorar*.
3. **As quatro saídas:** decida você / escolho eu / ver o catálogo / sem cases.
4. **No máximo uma pergunta de briefing** que mude o filme (ex.: público na plateia ou envio por WhatsApp). O resto você decide depois.

Com "faz tudo aí", pule esta etapa e produza. Com "sem cases", produza sem citar o catálogo.

Comandos abaixo partem da pasta da skill; `python` = o `.venv` da skill (criado por `python scripts/setup.py`, que é idempotente) ou o do projeto.

## Antes de tudo (ambiente novo ou erro estranho)
`python scripts/setup.py` (1ª vez: cria o `.venv`, instala o core fixado, roda o diagnóstico) · `python scripts/studio.py doctor [--deep]` —
diz o que está pronto, ausente ou é extensão opcional (FFmpeg/Chrome/Blender são achados mesmo fora do PATH). Demo completa: `python scripts/demo.py`.

## O fluxo (nessa ordem)
| # | Etapa | Resultado | Leia |
|---|---|---|---|
| 1 | Brief + guia de estilo | o que o espectador deve perceber, sentir, lembrar; formato; som | `references/launch-film-brief.md` |
| 2 | Storyboard com assets reais → **checkpoint conforme a delegação** (guiado: pare até "aprovado"; autônomo: revisão interna registrada) | quadros na resolução final + folha + `asset-manifest.json` | `references/storyboard.md`, `references/autonomia.md` |
| 3 | Beat sheet, depois animação | cenas com `anim(lt)` / `renderAt(t)` | `references/motion-system.md` + engine abaixo |
| 4 | Revisão de stills | folha de contato, recortes 1:1 | `references/qa.md` |
| 5 | Render (portões automáticos) | MP4 + `.report.json` + `.timeline.json` | `references/dom-pipeline.md` |
| 6 | QA de quadros e promoção do master | `studio.py promote` | `references/qa.md` |
| 7 | Som **depois da imagem aprovada** | cues, mix, master com áudio | `references/sound.md` |
| 8 | Notas | nova versão; nunca sobrescrever o aprovado | `references/notas.md` |

**Estudos de caso (catálogo de 14 fichas, `references/casos/`) no primeiro briefing:** rode
`python scripts/casos.py sugerir "<pedido>" --projeto <projeto>` e siga o modo:
- **guiado/híbrido** — mostre o bloco que o script imprime (no máximo **duas** referências, *por que combina* com este pedido e
  *quando pode piorar* a peça) junto com as quatro saídas: **decida você**, **escolho eu**, **ver o catálogo** (`casos.py listar`
  / `ver <id>`), **sem cases**. Registre a resposta (`casos.py usar <projeto> <id>…` ou `casos.py sem <projeto>`).
- **autônomo** ("faz tudo aí") — não pergunte: escolha até duas, registre com `--por agente`, aplique a *aplicação proposta* e
  confira o *teste na peça*; cite as escolhidas em uma linha na nota de entrega.
- **sem cases** (no pedido ou depois) — não sugira, não cite, não use fichas; revisões também não reintroduzem referências.
As fichas orientam a **direção** (como resolver uma situação); nunca copie métricas, textos ou marcas delas.

Notas não são aprovação. Se uma nota muda planos, ordem ou transições, volte ao storyboard; ajuste de tempo/cor não.

**Delegação (antes da etapa 1):** `python scripts/studio.py state init <projeto> "<palavras do usuário>"` grava
`studio-state.json` com o modo (autônomo / híbrido / guiado), o que foi delegado, reservado ou aprovado, restrições ("sem
locução") e assets obrigatórios. Antes de qualquer escolha de gosto: `studio.py state gate <projeto> <etapa>` — exit 0
decida e registre (`state decide`), 3 faça só aquela pergunta, 4 entregue como prévia. Sem verba declarada = custo adicional
zero. Uma nova sessão retoma por `studio.py state show <projeto>`.

## Gatilhos de leitura (obrigatórios)
| O pedido envolve… | Leia | Use |
|---|---|---|
| o brief "$1M launch film" colado ou filme novo | `references/launch-film-brief.md`, `references/storyboard.md` | `templates/dom/scene.html` para styleframes |
| marca real do usuário | docs da marca (projeto e Downloads do usuário) antes de desenhar | `scripts/split_logo.py` para logo plano por peças |
| interfaces, fotos, Reels, texto, vidro | `references/dom-pipeline.md`, `references/liquid-glass.md` | `templates/dom/` + `scripts/render_dom.mjs` |
| fotos/imagens/logos em cena | `references/dom-pipeline.md` § Assets | `asset-manifest.json` + `scripts/assets.py` |
| objeto que atravessa o filme, painéis 3D, motion blur | `references/engine-3d.md`, `references/motion-system.md` | `templates/film.html` + `scripts/render.mjs --gpu` |
| produto com geometria real (espessura, traseira, botões) | `references/engine-3d.md` § Three.js | `vendor/three-0.170.0/` + `render.mjs --gpu --root` |
| produto fotorrealista | `references/blender.md` (validado: GLB do Three → Cycles GPU ≈ 8,5 s/quadro 1080p) | `scripts/blender/` + `render.mjs dump` |
| ilustração da marca | `references/engine-2d-puppet.md` | `scripts/puppet.js`, `key.py`, `split.py` |
| "faça tudo", "decide por mim", escolha reservada | `references/autonomia.md` | `studio.py state …` |
| apresentação comercial, pitch, proposta animada (16:9) | `references/casos/README.md`, `references/storyboard.md` | `scripts/apresentacao.py init`, `templates/dom/apresentacao.js`, `scripts/casos.py` |
| comercial com pessoas, filmagem, banco de vídeo, atuação | `references/pessoas.md`, `references/integracoes.md` | `templates/dom/footage.js`, proxies all-intra |
| ideia, direção, duas tiras, referência por tipo de problema | `references/storyboard.md`, `references/repertorio.md` | `templates/storyboard-board.html` |
| som, trilha, voz, licenças | `references/sound.md`, `references/autonomia.md` | `mix.py --stems`, `music_pick.py`, `synth_music.py`, `finish.py`, `qa_audio.py` |
| legendas, texto sobre transições | `references/qa.md` § Composição | `captions.py`, `render_dom.mjs layout` |
| Open Design, Higgsfield, Artlist, imagens assistidas, Adobe | `references/integracoes.md` | `studio.py doctor` |
| algo quebrado | `references/pitfalls.md`, `references/qa.md` | `scripts/qa_frames.py`, logs `.report.json` |
Registre no estado do projeto (`BEATS.md` / `CREDITOS.txt` / manifesto) o que foi usado.

## Portões que o render aplica sozinho (não contorne)
- **Prontidão real** (`templates/dom/anim.js`): fonte, `<img>` ou imagem de fundo que não decodifica **rejeita** `ready`; `data-optional` só avisa.
- **Contrato de cena** (`templates/dom/sequence.html`): cena sem `anim(lt)`/`ready` derruba o render com o nome do arquivo.
- **Erros da página** (`render_dom.mjs`, `render.mjs`): exceção, `console.error`, HTTP ≥ 400 ou espera esgotada (`--ready-timeout`) param o render com etapa e instante.
- **Portão de assets** (`render_dom.mjs` + `asset-manifest.json` ao lado da página): obrigatório ausente, alterado depois da aprovação, sem licença, não aprovado, não ligado ao elemento `data-asset`, invisível no intervalo `visible` ou pequeno demais para a tela **bloqueia** o MP4; opcional aprovado sem asset passa e fica registrado.
- **Master preservado**: o vídeo é gravado como `.tmp` e só renomeado no sucesso; saída existente não é sobrescrita sem `--replace`.
- **Manifesto obrigatório no master**: sem `asset-manifest.json` o render final falha; filme sem fotos usa `{"assets": []}` (vagas `data-asset` não declaradas ainda bloqueiam); projeto anterior ao portão usa `--legacy "motivo"`.
- **QA de quadros** (`scripts/qa_frames.py`): preto, branco, congelado, quadros repetidos, fps/duração/resolução, lacuna ou sobreposição na timeline, clipping e silêncio. Trechos intencionais vêm de `INTENTIONAL` na `sequence.html` (gravado em `.timeline.json`). `python scripts/studio.py promote <render> <master>` só promove se passar.

## Comandos essenciais
```bash
node scripts/render_dom.mjs stills <filme>/sequence.html <filme>/review/r1 0.5 1.2 ... --root <projeto>
node scripts/render_dom.mjs video  <filme>/sequence.html "<filme>/out/<Filme> v1.mp4" --fps 60 --root <projeto> [--scale 2] [--png]
node scripts/render.mjs video <filme>.html "<filme>/out/<Filme> v1.mp4" --fps 25 --scale 1 --gpu      # canvas
python scripts/qa_frames.py "<render>.mp4" --timeline "<render>.timeline.json"
python scripts/studio.py promote "<render>.mp4" "<filme>/out/<Filme> - MASTER.mp4"
python scripts/qa_audio.py deliver "<master>.mp4" --timeline "<render>.timeline.json"   # loudness/true peak/mono no arquivo decodificado
node scripts/render_dom.mjs layout <filme>/sequence.html <filme>/qa/layout --root <projeto>   # colisões de texto por amostragem
python scripts/assets.py status|approve|omit|affected <asset-manifest.json> ...
python scripts/studio.py sync && python scripts/studio.py validate      # depois de editar a skill (Claude → Codex)
```

## Regras e seu escopo
- **Projeto:** storyboard antes de animar; som por último; nada de IA no som; sem créditos pagos sem pedido + estimativa; sem download em massa de Pixabay/Mixkit; não commitar vídeos; commit/push só a pedido; licenças em `audio-library/LICENCAS.txt` e `<filme>/CREDITOS.txt`.
- **Marca:** o guia da marca vence este.
- **Peça:** escolhas aprovadas de um filme (centralização, câmera contínua, vidro, uma trilha) valem para ele, não viram regra global. Repetição (mesmo corte, mesmo whoosh, mesmo push) só quando for motivo intencional.
- Nunca use nome, fonte SF, sons ou copy da Apple; nunca desenhe logo real de memória; claims só verdadeiros; fotos geradas = pessoas fictícias, nunca apresentadas como clientes reais. Fotos de pessoas reais só com autorização registrada no manifesto.

## Scripts
`render.mjs` (canvas, `dump`) · `render_dom.mjs` (DOM, portões, `stills/video/events/timeline/check/layout`) · `qa_audio.py` · `captions.py` · `music_pick.py` · `synth_music.py` · `qa_frames.py` · `studio.py`
(`doctor/sync/validate/promote/state/public`) · `assets.py` · `mix.py` · `finish.py` · `music_scan.py` · `split_logo.py` · `contact_sheet.py`
/ `sheet916.py` · `gl3d.js` · `puppet.js` · `key.py` / `split.py` / `grid.py` · `synth_sfx.py` · `blender/` · `compose_into_clip.py` ·
`lib/tools.{mjs,py}` (acha FFmpeg/Chrome/Blender). Testes: `tests/run_*.py` (as evidências ficam em tests/evidence na cópia canônica e não são distribuídas).
