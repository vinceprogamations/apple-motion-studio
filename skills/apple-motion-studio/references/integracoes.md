# Integrações: ferramenta por plano, estado verificável

O caminho gratuito local (DOM / Canvas / gl3d / Three.js + Chrome headless + FFmpeg + bibliotecas locais) leva do briefing ao
MP4 sem login nem pagamento. Tudo abaixo é **opcional** e entra só no plano que precisa. Use quatro estados, sempre com
evidência: **disponível** (achado no ambiente), **testada** (entrada → saída produzida, com versão), **pendente** (falta um passo
nomeado), **bloqueada** (falta conta, licença, verba ou autorização). A falta de uma integração opcional nunca impede o master.
`python scripts/studio.py doctor` mostra o estado local.

| Ferramenta | Quando entra | Como verificar | Custo |
|---|---|---|---|
| **Blender** | planos principais de produto físico (material, luz, sombra, close) — ver `blender.md` | `doctor --deep` lê a versão; `blender -b -P …` rende | grátis |
| **Three.js** (vendorizado) | geometria real controlável, prévias rápidas, UI viva no objeto | `render.mjs stills … --gpu` | grátis |
| **Open Design** | pré-produção de UI: HTML, tokens, componentes, tipografia de um quadro aprovado | instalador achado ≠ app instalado ≠ app rodando ≠ conexão com o agente funcionando — `doctor` separa os quatro | grátis (app) |
| **Higgsfield** (vídeo generativo) | plano que precisa de filmagem que o código não faz | conta + créditos no momento do uso | créditos — **estime antes**; demo = 0 |
| **Pexels** (vídeo de banco) | atuação real em planos com pessoas — ver `pessoas.md` | página + link oficial "Free download" | grátis (Pexels License; sem redistribuir) |
| **Mixkit** (vídeo) | só se a página do clipe trouxer licença comercial | ler a licença NA página | download grátis = uso pessoal (Restricted) em 25/11/2026 |
| **Artlist** | música/SFX de catálogo | por asset: encaixe + licença do destino | assinatura |
| **ChatGPT Images** (modo assistido) | fotos de vaga (pessoa, ambiente) | por vaga no `asset-manifest.json` | conta do usuário |
| **After Effects** | quando o projeto editável ou um efeito específico justificar | — | assinatura |
| **Creator MCP (LottieFiles)** | só se a entrega for Lottie/dotLottie | — | conforme conta |
| Tone.js, Remotion Studio, Scenario MCP, HyperFrames | só no fluxo que de fato precisar | versão instalada | — |

## Open Design (pré-produção opcional)
- Origem e versão: [releases oficiais](https://github.com/nexu-io/open-design/releases) e
  [integração com agentes](https://github.com/nexu-io/open-design#use-opendesign-from-your-coding-agent). Na hora de usar,
  confira versão, origem e SHA-256 do arquivo escolhido; instalador sem assinatura digital de editor = instalar é decisão do
  usuário. Reaproveite uma instalação existente.
- Ensaio previsto (quando conectado): ler os arquivos por canal autorizado, reaproveitar HTML/tokens/componentes/tipografia,
  animar 3 s de interação no renderer da skill, comparar o 1º quadro com o quadro aprovado no mesmo viewport, fazer uma revisão
  de espaçamento/tipografia na origem e mostrar no filme; registrar o que foi reaproveitado e o que foi reconstruído.
- Sem conexão: diga qual passo falta (ex.: "app não instalado") e conclua a demonstração pelo fluxo local.

## Vídeo generativo e produção híbrida (lições de processo)
Fontes: `Turkey-Job-Process-Guide.pdf` e `Turkey_Job_Production_Pack.pdf` (arquivadas no projeto de origem). Aplicação:
referências ordenadas por função; para cada plano, especifique visual, câmera, ação, som e **estados de entrada e saída**; itere
em rascunho; guarde o take escolhido e o porquê. Trocar figurino ou objeto expõe as descrições antigas nos planos que dependem
dele (revalide esses planos). Se várias tentativas falham, simplifique a encenação ou divida o plano. Separe **pré-produção
local** (feita aqui) de **viabilidade verificada** de **geração executada** (com conta e créditos).

## Imagens e interfaces
Por vaga: planejamento, prompt, ingestão, hash, recorte e revalidação das cenas que dependem dela (`scripts/assets.py
affected`). Em interfaces reais, prefira capturas autorizadas com dados de demonstração, na resolução do maior zoom.
Tutoriais (Thomas Lundström, Rourke, Felipe Borges) entram quando a técnica resolve um problema concreto — registre a
diferença entre **tutorial consultado**, **integração testada** e **resultado produzido**.

## Imagens novas pelo Chrome (ChatGPT Images / Gemini)
1. **Comece pelas vagas.** Liste cada vaga: cena, papel, enquadramento e maior zoom. Resolva o que der com assets aprovados, capturas autorizadas ou UI em código (`telas.html` do Natal, `ui.js` do Pedido). Gere só o que faltar.
2. **Controle o Chrome com o Claude in Chrome** (`claude --chrome` ou `/chrome`, conforme a conexão) e execute o fluxo até **baixar e verificar** o arquivo. Se o Chrome, o login ou a cota bloquear uma vaga, diga qual ação o usuário precisa fazer e avance nas outras.
3. **Escolha o modo.** Se estiver em aberto, pergunte. Com tudo delegado, use o terceiro.
   - **ChatGPT gera tudo:** eu gero e seleciono. O Gemini entra como apoio quando trouxer uma alternativa útil.
   - **O usuário escolhe:** mostro candidatos do ChatGPT e do Gemini para as vagas principais e sigo o trabalho independente enquanto ele decide.
   - **Claude cuida de tudo:** uso o mesmo briefing nos dois para as imagens de destaque, comparo e escolho.
4. **Referências.** Avise que **referências nítidas e específicas melhoram o resultado** e diga o que cada uma orienta: geometria, luz, enquadramento, material ou consistência. Se o usuário não enviar, procure no acervo. Anexe só arquivos autorizados para esse uso.
5. **Geração.**
   - Use grades para explorar e gere individualmente o que vai aparecer em close.
   - Pessoas são fictícias e entram nas vagas de perfil.
   - Dashboards levam dados de demonstração legíveis.
   - **ChatGPT Images:** use referência e edição localizada e salve por **Download** (se for blob: `fetch(src)` → `<a download>`).
   - **Gemini:** use a geração e a edição de imagens da conta e salve por **Download full size**.
   - Se a conversa "grudar" no tema anterior, abra um chat novo.
6. **Verificação e registro.**
   - Compare o arquivo baixado no tamanho real e no recorte do maior zoom do filme.
   - Recorte as grades detectando as calhas brancas.
   - Registre no `asset-manifest.json` a origem, o prompt, as dimensões, o SHA-256 e o vínculo com a cena (`assets.py`).

Fontes: https://code.claude.com/docs/en/chrome · https://help.openai.com/en/articles/11084440-images-in-chatgpt · https://support.google.com/gemini/answer/14286560

**Baixar cada imagem logo que ela sai** (lição do filme Raiz, 28/11/2026): depois de 2–3 downloads automáticos seguidos, o Chrome passa
a bloquear "downloads múltiplos" no chatgpt.com sem avisar, e a imagem não chega à pasta Downloads (o botão "Baixar" do visualizador
também falha). Por isso: gere → baixe → confira o arquivo em Downloads → só então gere a próxima. Se travar, peça ao usuário para
liberar downloads múltiplos para o site (ícone na barra de endereço) — não tente contornar enviando a imagem para um servidor local
(a CSP do site bloqueia e não é um caminho aceito). A conta grátis gera ~4 imagens por janela de tempo: planeje grades (2×2, 3×3).

## Curadoria de outras skills (Find Skills)
Pesquisa feita com o [Find Skills da Vercel](https://skills.sh/vercel-labs/skills/find-skills). Ideias incorporadas em
redação própria (nenhum código copiado): perspectiva sonora (ClawFu), revisão de timbre em linguagem comum (Danny J. P.
Williams), tempos e quebras de legenda ([Remotion Captions](https://github.com/remotion-dev/skills/blob/a3f4098a2afd0e13f6a6f8c8760e275f75457ea9/skills/remotion-captions/SKILL.md)),
encenação/câmera e separação de luz (Scenario Blender Previs / Lighting), amostragem de QA
([HyperFrames CLI](https://github.com/heygen-com/hyperframes/blob/4af0e9c09b4b939a85a75029a28e20429fca42ac/skills/hyperframes-cli/SKILL.md)).
Se algum dia código ou asset for incorporado, verifique a licença antes.
