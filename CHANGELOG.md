# Changelog

## v1.2.0 — 2026-11-25
**Relacionamento com o usuário:** a skill diz antes o que vai instalar, baixar, gastar e fazer no navegador, e na entrega separa o que foi medido do que ninguém viu.
- **`scripts/ambiente.py`**:
  - `plano`: o que falta, com tamanho, origem e comando;
  - `instalar faltando --sim "<palavras do usuário>"`: winget ou brew, com o consentimento registrado em `.local/`; sem o sim, nada é instalado;
  - `mcp`: classifica as ferramentas conectadas em pagas, freemium ou grátis; conector desconhecido = pago;
  - `aviso`: o bloco único de avisos.
- **`references/ferramentas.json`**: registro de programas, serviços (custo, quando usar, aviso) e sites (licença e regra de download).
- **`scripts/material.py checar`**:
  - mede se logo, foto, tela, vídeo e áudio aguentam a resolução do filme e diz o que pedir;
  - lê a licença no `asset-manifest.json` e barra material de outra marca ou de uso restrito.
- **`scripts/conversa.py`**:
  - `abertura`: o combinado com modo, material, instalação, custo, navegador, limites e formato de nota;
  - `entrega`: QA medido × não verificado, onde olhar (tempo → cena), o que limita a nitidez e como pedir mudança.
- **`references/relacionamento.md`**: os cinco momentos de comunicação. Instalar, baixar, gastar e usar o navegador são permissões e nunca contam como delegadas.
- **Delegação**: "pode instalar" vira `constraints.instalar`; "faz tudo aí" não autoriza instalar.
- **`casos.py` no modo autônomo** aplica e registra a referência sem perguntar.
- **`pitfalls.md`**: fonte em fallback, duas animações na mesma propriedade, texto inventado, "pronto" sem ver.
- **Testes**: `tests/run_relacionamento.py` (16 checagens).

## v1.1.0 — 2026-11-25
- **Estudos de caso:**
  - catálogo com 14 fichas e índice em `references/casos/`;
  - `scripts/casos.py` (`sugerir`, `listar`, `ver`, `usar`, `sem`): no máximo duas sugestões, cada uma com por que combina e quando pode piorar.
- **Primeira resposta** (topo do `SKILL.md`): entendimento + bloco de casos + quatro saídas (decida você, escolho eu, ver o catálogo, sem cases). A peça não é produzida antes da escolha.
- **"sem cases"** vira restrição do projeto (`studio-state.json`), respeitada também nas revisões.
- **Apresentação comercial em vídeo:**
  - `scripts/apresentacao.py init` e `templates/dom/apresentacao.js` (slides como dados);
  - o mesmo objeto atravessa os perfis, a estrela ✦ viaja entre os slides;
  - QA com leitura e fundo preto da marca declarados.
- **Descrição para o Codex:** os gatilhos foram para o início, porque o catálogo do Codex mostra só o começo da descrição.
- **Correções:** UTF-8 na saída de `finish.py`, `mix.py` e `apresentacao.py` quando ela vai por pipe no Windows.

## v1.0.0 — 2026-11-25 (primeira versão pública)
- **Autonomia com escopo**:
  - `studio.py state`: modos guiado, híbrido e autônomo; estados `delegado-agente`, `aprovado-usuario` e `exige-terceiro`; prévia quando falta asset obrigatório;
  - retomada por estado salvo;
  - `AGENTS.md` e `SKILL.md` com a mesma regra de parada.
- **Som**:
  - `music_pick.py`: licença e destino antes do gosto, substituição relatada, A/B no mesmo trecho;
  - `synth_music.py`: trilha original com drop no evento e recuo para voz;
  - `mix.py --stems`;
  - `qa_audio.py`: loudness (web / EBU R 128 s1), true peak e mono medidos no MP4 decodificado, mascaramento de palavra-chave, onset;
  - `finish.py` corrige o true peak que o AAC adiciona.
- **Legendas e QA de composição**:
  - `captions.py`: importa, revisa uma frase regravada e checa fronteiras quadro a quadro;
  - `render_dom.mjs layout`: colisões por instante, cobertura registrada, salto × sequência, zero amostras = falha.
- **Portão de assets**:
  - render final sem manifesto falha;
  - `{"assets": []}` para filmes sem fotos, mas vagas não declaradas bloqueiam;
  - `--legacy` explícito para projetos antigos.
- **3D**:
  - three.js r170 vendorizado;
  - `render.mjs dump` para exportar GLB;
  - fluxo Blender headless validado;
  - guia de previs e de luz (uma fonte por vez, prévia em cinza).
- **Comercial com pessoas**:
  - `references/pessoas.md`: rotas verificadas pela operação, licença comercial ≠ redistribuição;
  - `templates/dom/footage.js` (filmagem quadro a quadro);
  - `render_dom.mjs` com HTTP Range e `renderAt` assíncrono;
  - drop refinado em 10 ms no `music_pick.py`;
  - ambiências DSP no `synth_sfx.py`.
- **Distribuição**:
  - `setup.py` idempotente com core fixado;
  - `demo.py` reproduzível (demo "Quando");
  - `studio.py public` com guarda de privacidade;
  - instalação via `npx skills add`.
