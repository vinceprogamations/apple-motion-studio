# Comercial com pessoas ("faz tudo aí")

A história depende de uma **ação humana legível**: alguém quer algo, age em quadro, e uma consequência observável liga isso ao
benefício. Retrato parado com zoom é só apoio. Pelo menos uma tomada em movimento precisa carregar a mensagem (gesto, olhar,
interação).

## 1. Descubra o que a sessão consegue operar (pela operação, não pelo nome)

Ver um catálogo resolve a pesquisa. A montagem exige **obter o arquivo**. Teste cada rota pela operação que o plano precisa e
registre o resultado.

| Rota | Prova de que funciona | Observação (verificada em 25/11/2026) |
|---|---|---|
| Pexels (vídeo) | página aberta + link oficial "Free download" baixa o MP4 | Pexels License: uso comercial livre; **não** redistribuir o arquivo isolado |
| Mixkit (vídeo) | ler a licença **na página do clipe** | o download gratuito virou "Personal Use only (Restricted License)": **não serve para comercial** |
| Higgsfield / outro gerador | `balance` + `estimate_video_cost` | só com verba ou créditos autorizados; com orçamento 0 não gera |
| Navegador do usuário (Claude in Chrome) | `tabs_context` responde | se não responder, use o navegador embutido para pesquisa e o link oficial para baixar |
| Acervo local de som | arquivo + linha em `LICENCAS.txt` | trilhas de terceiros: uso no filme sim, redistribuição não |
| Blender / Open Design | `studio.py doctor --deep` | produto físico / UI aproveitável |

Não baixe em massa por script de sites que proíbem isso (Pixabay, Mixkit). Baixe um arquivo de cada vez, pelo link oficial ou
pelo botão do site.

## 2. Seleção curta do material

- **Folha de contato:** `ffmpeg -i clip.mp4 -vf "fps=1,scale=160:-1,tile=8x2" -frames:v 1 folha.jpg`. Confira:
  - atuação e continuidade (figurino e luz entre tomadas);
  - mãos e objetos;
  - se o quadro final 9:16 ou 16:9 corta o gesto.
- **Quadro do contato:** ache-o em tiras de 7,5 fps. Ele vira uma batida (`B.abraco`); a tomada é posicionada para cair nela
  (`B.corte = B.abraco − (contato_no_clipe − entrada)`).
- **Manifesto:** registre cada tomada no `asset-manifest.json` (`type: "video"`) com:
  - `origin`, `obtained` e `license`;
  - `commercial_ok` e `redistribute_ok` (separados);
  - `sha256`;
  - aprovação com escopo (`"escolha do agente por delegação"`).
- **Proxies:** os originais ficam guardados; a montagem usa proxies **all-intra**:
  `ffmpeg -i original.mp4 -vf "scale=1080:1920:flags=lanczos,fps=30" -an -c:v libx264 -crf 16 -g 1 -pix_fmt yuv420p proxy.mp4`.

## 3. Montagem na página DOM

- `templates/dom/footage.js`:
  - `Footage.clip(video)`;
  - `window.ready = Footage.ready([...])` rejeita arquivo que não carrega;
  - `renderAt` é **async** e faz `await Footage.seek(v, t)`.
- `render_dom.mjs` espera o `renderAt` assíncrono e serve vídeo com HTTP Range. Sem Range, o `<video>` não carrega.
- **Câmera:** o push sobre a tomada usa uma **taxa constante** (`1.04 + k * t`). Normalizar pela duração do plano faz uma
  revisão de tempo alterar todos os quadros anteriores (medido).
- **Transição:** transforme, não dissolva. Exemplo: a notificação do app vira o cartão do horário, que vira o salto de tempo, e
  um círculo abre a tomada seguinte.

## 4. Som

- **Clipes de banco costumam vir mudos.** Construa ambiente (`synth_sfx.py` gera `Amb Parque`, `Amb Rua Noite` e
  `Synth Cloth`), foley (passos reais, contato), UI e música.
- **Escolha da música:** `music_pick.py` refina o drop em 10 ms. A varredura de 0,5 s colocou um drop 0,23 s **antes** do
  gesto, e o respiro sumiu. Use `music_from` do resultado como `from` do bed.
- **Decisão audível:** escreva uma frase. Ex.: "os braços se abrem quase em silêncio e o contato chega com o drop".
- **Prova na caixa pequena:** decodifique o master, filtre mono 300 Hz–7 kHz e meça o salto de nível no contato contra os
  300 ms anteriores (> +6 dB).
- **Revisão de tempo do gesto:**
  - mova a batida;
  - a trilha acompanha alongando o respiro antes do drop (tudo antes fica idêntico);
  - prove com `qa_audio.py onset` no gesto (+6/FPS s) e num vizinho (0 ms);
  - confira os quadros: idênticos até o corte antigo.

## 5. Entrega

O master fica no projeto do usuário, com um `LEIA.md` (história, decisões, origem e direito de cada arquivo, rotas testadas,
medições). Material sem direito de redistribuição **nunca** vai para repositório ou release. Na vitrine pública, use uma demo
com material próprio.
