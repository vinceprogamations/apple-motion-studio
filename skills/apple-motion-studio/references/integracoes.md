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

## Curadoria de outras skills (Find Skills)
Pesquisa feita com o [Find Skills da Vercel](https://skills.sh/vercel-labs/skills/find-skills). Ideias incorporadas em
redação própria (nenhum código copiado): perspectiva sonora (ClawFu), revisão de timbre em linguagem comum (Danny J. P.
Williams), tempos e quebras de legenda ([Remotion Captions](https://github.com/remotion-dev/skills/blob/a3f4098a2afd0e13f6a6f8c8760e275f75457ea9/skills/remotion-captions/SKILL.md)),
encenação/câmera e separação de luz (Scenario Blender Previs / Lighting), amostragem de QA
([HyperFrames CLI](https://github.com/heygen-com/hyperframes/blob/4af0e9c09b4b939a85a75029a28e20429fca42ac/skills/hyperframes-cli/SKILL.md)).
Se algum dia código ou asset for incorporado, verifique a licença antes.
