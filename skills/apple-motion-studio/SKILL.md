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
O filme sai melhor quando você sabe **para quem, onde, o que mostrar, que sensação, que material existe e que música**. Pergunte
tudo **de uma vez**, nunca a conta-gotas. Se o pedido **não** delega ("faz tudo aí", "decide tudo", "a direção é sua"), a
primeira resposta termina nas perguntas e **não produz a peça**, mesmo numa execução não interativa. Ela tem, nesta ordem:
1. **Uma linha com o que você entendeu:** formato (apresentação = **vídeo animado**; para slides editáveis existe outra skill), duração proposta, marca e o material encontrado (procure no projeto e nos Downloads do usuário pelo nome da marca).
2. **O questionário:** `python scripts/briefing.py perguntas "<pedido>" --projeto <projeto> --json`. Ele traz só o que o pedido
   ainda não respondeu: onde roda, duração, público, a frase, material, sensação, pessoas, música, voz, CTA, uso, prioridade e
   aprovações, com a opção recomendada primeiro.
   - Com `AskUserQuestion`: **uma chamada por bloco** do `--json` (até 4 perguntas cada, em sequência). Adapte o texto das opções ao
     negócio (cafeteria, clínica, app…) sem trocar os ids. A última pergunta é a permissão da estimativa de tempo.
   - Sem `AskUserQuestion` (Codex): a lista numerada que `briefing.py perguntas` imprime.
   - Registre as respostas com `briefing.py registrar <projeto> '{"destino": "...", ...}'`. O que ficar em branco é decidido pela recomendada e avisado.
3. **O bloco de estudos de caso** (`python scripts/casos.py sugerir "<pedido>" --projeto <projeto>`), com até duas referências e as quatro saídas: decida você / escolho eu / ver o catálogo / sem cases.
4. **A estimativa de tempo**, que já vem como a última pergunta do questionário; é permissão, não gosto.
   - Com o sim: `python scripts/estimativa.py ler --sim "<palavras dele>" [--blender]`. Mostre `estimativa.py estimar --dur … --formatos … [--blur …] [--filmagem] [--blender-quadros …]` no combinado.
   - Sem o sim: a estimativa sai com valores de referência e diz isso.
5. **O acervo de referências** (`python scripts/acervo.py status`; guia em `references/acervo.md`). Se faltar (exit 3), faça a pergunta
   pronta de `acervo.py pergunta` — *"Para os vídeos ficarem melhores, vale ter um acervo de referências (modelos 3D grátis, luz de
   estúdio, materiais, telas reais de apps). Posso acessar o Chrome e baixar tudo?"* — e, com o sim, `acervo.py baixar --sim "<palavras>"`
   + os itens de `acervo.py chrome` pelo navegador.

Com "faz tudo aí": nada de perguntas de gosto (use as recomendadas e registre como delegado). Só a permissão da estimativa e as de
instalação ou custo são perguntadas. **O acervo grátis não é perguntado: baixe-o** (`acervo.py baixar --sim "<palavras do pedido>"`,
inclusive os aparelhos pelo Chrome) e avise numa linha — decisão do usuário, 28/11/2026. Com "sem cases": produza sem citar o catálogo.
Se o usuário mandou material (logo, prints, fotos), rode `python scripts/material.py checar <arquivos>` antes e, se algo vier
fraco ou com licença que não cobre este filme (ex.: logo de outra marca), peça o arquivo certo **numa linha** (ex.: "mande o logo em SVG: o PNG de 300 px fica mole no fecho").

## Relacionamento com o usuário (avisos que nunca são pulados) — `references/relacionamento.md`
- **Combinado antes de produzir:** `python scripts/conversa.py abertura <projeto> "<pedido>" --material <arquivos> --mcp <ferramentas que você vê>`.
  Diz como vamos trabalhar, que material melhora o filme, o que será instalado, o custo, o uso do navegador e o que você não consegue
  fazer (não assiste nem ouve em tempo real). No modo autônomo, vira uma linha na entrega.
- **Instalar, baixar, gastar, usar o navegador do usuário = permissão, nunca gosto.** "Faz tudo aí" não cobre. Mostre o plano
  (`python scripts/ambiente.py plano` / `aviso --site …`), espere o sim e só então `ambiente.py instalar faltando --sim "<palavras dele>"`.
  Ferramenta paga (ElevenLabs, Higgsfield, Runway…): pedido explícito + estimativa da própria ferramenta + sim para o valor.
- **Entrega honesta:** `python scripts/conversa.py entrega <master.mp4>` — o que a máquina verificou, o que ninguém verificou,
  onde olhar (tempo → cena), o que limita a nitidez e como pedir mudança (tempo + ação). QA ok ≠ filme bom; nunca diga "ficou ótimo".

Comandos abaixo partem da pasta da skill; `python` = o `.venv` da skill se existir (criado por `python scripts/setup.py`, idempotente), senão o do projeto ou o do sistema com as dependências.

## Antes de tudo (ambiente novo ou erro estranho)
`python scripts/setup.py` (1ª vez: cria o `.venv`, instala o core fixado, roda o diagnóstico) · `python scripts/studio.py doctor [--deep]` —
diz o que está pronto, ausente ou é extensão opcional (FFmpeg/Chrome/Blender são achados mesmo fora do PATH). Demo completa: `python scripts/demo.py`.

## O fluxo (nessa ordem)
| # | Etapa | Resultado | Leia |
|---|---|---|---|
| 1 | Brief + guia de estilo | o que o espectador deve perceber, sentir, lembrar; formato; som | `references/launch-film-brief.md` |
| 1b | **Textos + música primeiro** (pedido do usuário): roteiro com todo texto de tela (gancho, virada, CTA; slogan uma vez só) e trilha escolhida com a grade (drop/respiros) | `copy.md` do filme + trilha registrada | `references/copy.md`, `references/sound.md` |
| 2 | Storyboard com assets reais → **checkpoint conforme a delegação** (guiado: pare até "aprovado"; autônomo: revisão interna registrada) | quadros na resolução final + folha + `asset-manifest.json` | `references/storyboard.md`, `references/autonomia.md` |
| 3 | Beat sheet, depois animação | cenas com `anim(lt)` / `renderAt(t)` | `references/motion-system.md` + engine abaixo |
| 4 | Revisão de stills | folha de contato, recortes 1:1 | `references/qa.md` |
| 5 | Render (portões automáticos) | MP4 + `.report.json` + `.timeline.json` | `references/dom-pipeline.md` |
| 6 | QA de quadros, **crítica com nota (≥ 2 rodadas, tudo ≥ 8)** e promoção do master | `qa_celular.py`, `revisao.md`, `studio.py promote` | `references/qa.md`, `references/critica.md` |
| 7 | **SFX em cima da animação pronta** (a trilha já foi decidida na 1b) | cues, mix, master com áudio | `references/sound.md` |
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
| **modelo 3D, HDRI, material ou tela de app** (produto, cenário, celular, perfil, conversa) | `references/acervo.md` | `scripts/acervo.py status/pergunta/baixar/chrome` — use o acervo antes de modelar ou desenhar do zero |
| **celular/tablet em cena** ou **folhas, respingos, natureza** | `references/dom-pipeline.md` § Cantos | `templates/dom/device.js` (`buildDevice`) + `scripts/blender/device_front.py`; `templates/dom/organico.js` |
| **qualquer canto arredondado** (ícone de app, card, janela, celular, botão) | `references/dom-pipeline.md` § Cantos: squircle sempre | `corner-shape: squircle` (já no `common.css`); círculos = `.circle` |
| fotos/imagens/logos em cena | `references/dom-pipeline.md` § Assets | `asset-manifest.json` + `scripts/assets.py` |
| objeto que atravessa o filme, painéis 3D, motion blur | `references/engine-3d.md`, `references/motion-system.md` | `templates/film.html` + `scripts/render.mjs --gpu` |
| produto com geometria real (espessura, traseira, botões) | `references/engine-3d.md` § Three.js | `vendor/three-0.170.0/` + `render.mjs --gpu --root` |
| produto fotorrealista | `references/blender.md` (validado: GLB do Three → Cycles GPU ≈ 8,5 s/quadro 1080p) | `scripts/blender/` + `render.mjs dump` |
| ilustração da marca | `references/engine-2d-puppet.md` | `scripts/puppet.js`, `key.py`, `split.py` |
| "faça tudo", "decide por mim", escolha reservada | `references/autonomia.md` | `studio.py state …` |
| apresentação comercial, pitch, proposta animada (16:9) | `references/casos/README.md`, `references/storyboard.md` | `scripts/apresentacao.py init`, `templates/dom/apresentacao.js`, `scripts/casos.py` |
| comercial com pessoas, filmagem, banco de vídeo, atuação | `references/pessoas.md`, `references/integracoes.md` | `templates/dom/footage.js`, proxies all-intra |
| ideia, direção, duas tiras, referência por tipo de problema | `references/storyboard.md`, `references/repertorio.md` | `templates/storyboard-board.html` |
| som, trilha, voz, licenças | `references/sound.md`, `references/autonomia.md` | `batidas.py` (andamento real → grade de cortes), `mix.py --stems`, `music_pick.py`, `trilhas.py livre/usar` (nenhum filme repete a música de outro), `synth_music.py`, `finish.py`, `qa_audio.py` |
| tempo de produção, "quanto demora", PC do usuário | `references/relacionamento.md` | `estimativa.py ler/estimar` (com consentimento) |
| motion blur, movimento rápido, rolagem, whip | `references/motion-system.md` § 8 | `render_dom.mjs video … --blur 4–8` |
| legendas, texto sobre transições | `references/qa.md` § Composição | `captions.py`, `render_dom.mjs layout` |
| Open Design, Higgsfield, Artlist, imagens assistidas, Adobe | `references/integracoes.md` | `studio.py doctor` |
| instalar programas, ferramentas pagas/MCP, baixar pelo navegador, material do usuário | `references/relacionamento.md`, `references/ferramentas.json` | `ambiente.py`, `material.py`, `conversa.py` |
| **textos de tela, gancho, slogan, CTA** — inclusive "só revisar o texto" ou "só o texto" | `references/copy.md` (etapa obrigatória antes do storyboard; com `copy-that-sells`/`hook-writer`/`reels-script` se instalados) | `<filme>/copy.md` |
| **aparelho articulado ou objeto 3D com peças** (notebook, tampa, porta, celular) | `references/blender.md` § Guia de execução + caso de regressão do notebook | `scripts/blender/kit.py` + `Empty` no eixo físico |
| **filme com todos os assets prontos** | `references/copy.md` → `references/storyboard.md` (pule a geração; só manifesto + portões) | `assets.py approve` |
| **imagem nova a gerar** (foto de vaga, produto, hero de site) | `references/integracoes.md` § Imagens novas pelo Chrome (3 modos) | Claude in Chrome + `asset-manifest.json` |
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
python scripts/qa_celular.py "<render>.mp4"                    # leitura a 360 px + áreas da interface do Reels (9:16)
python scripts/batidas.py <trilha> --grade <período>          # andamento real e atempo para a grade dos cortes
python scripts/assets.py status|approve|omit|affected <asset-manifest.json> ...
python scripts/studio.py sync && python scripts/studio.py validate      # depois de editar a skill (Claude → Codex)
```

## Regras e seu escopo
- **Projeto:** storyboard antes de animar; som por último; nada de IA no som; sem créditos pagos sem pedido + estimativa; sem download em massa de Pixabay/Mixkit; não commitar vídeos; commit/push só a pedido; licenças em `audio-library/LICENCAS.txt` e `<filme>/CREDITOS.txt`.
- **Marca:** o guia da marca vence este.
- **Peça:** escolhas aprovadas de um filme (centralização, câmera contínua, vidro, uma trilha) valem para ele, não viram regra global. Repetição (mesmo corte, mesmo whoosh, mesmo push) só quando for motivo intencional.
- Nunca use nome, fonte SF, sons ou copy da Apple; nunca desenhe logo real de memória; claims só verdadeiros; fotos geradas = pessoas fictícias, nunca apresentadas como clientes reais. Fotos de pessoas reais só com autorização registrada no manifesto.

## Scripts
`briefing.py` (perguntas/registrar/resumo) · `acervo.py` (status/pergunta/baixar/chrome) · `estimativa.py` (ler/estimar) · `ambiente.py` (plano/instalar/mcp/aviso) · `material.py` · `conversa.py` (abertura/entrega) · `qa_celular.py` · `batidas.py` · `render.mjs` (canvas, `dump`) · `render_dom.mjs` (DOM, portões, `stills/video/events/timeline/check/layout`) · `qa_audio.py` · `captions.py` · `music_pick.py` · `trilhas.py` · `synth_music.py` · `qa_frames.py` · `studio.py`
(`doctor/sync/validate/promote/state/public`) · `assets.py` · `mix.py` · `finish.py` · `music_scan.py` · `split_logo.py` · `contact_sheet.py`
/ `sheet916.py` · `gl3d.js` · `puppet.js` · `key.py` / `split.py` / `grid.py` · `synth_sfx.py` · `blender/` · `compose_into_clip.py` ·
`lib/tools.{mjs,py}` (acha FFmpeg/Chrome/Blender). Testes: `tests/run_*.py` (as evidências ficam em tests/evidence na cópia canônica e não são distribuídas).
