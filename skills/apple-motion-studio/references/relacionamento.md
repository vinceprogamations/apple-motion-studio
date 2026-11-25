# Relacionamento com o usuário: o que dizer, quando, e por quê

O melhor filme sai quando o usuário sabe o que vai acontecer, entrega o material certo cedo e dá notas precisas. Esta página
diz **o que comunicar em cada momento**. Os textos prontos saem de `scripts/conversa.py` e `scripts/ambiente.py`; adapte o tom
à conversa, mas não corte avisos.

Base (pesquisa de 25/11/2026 sobre motion graphics com Claude Code e Codex):
- **Perguntar demais trava; perguntar de menos gera filme genérico.** As perguntas que ajudam são as acionáveis. Num estudo, a abordagem com menos perguntas chegou ao mesmo resultado com 41% menos perguntas. Ver Ambig-SWE (2025) e "Asking What Matters" (2026).
- **A falha que mais irrita é o "fake done":** o agente declara que terminou sem ter verificado. Por isso a entrega separa o que foi medido do que ninguém viu.
- **Notas boas têm tempo e ação** ("aos 0:12,4…"), vêm consolidadas e são poucas rodadas combinadas no início. É a prática de agência e de revisão no Frame.io.
- **Aprovação só para o que é irreversível, visível a terceiros ou custa dinheiro.** O resto o agente decide, para evitar fadiga de aprovação.
- **Mudar fica caro depois do storyboard.** Style frames e storyboard são o checkpoint certo para mudanças grandes.
- **O agente só vê quadros parados.** Timing, ritmo e som são medidos, não sentidos, e isso deve ser dito ao usuário.

## Os cinco momentos

| Momento | O que dizer | Ferramenta |
|---|---|---|
| 1. Primeira resposta | o que entendeu, os cases (se couberem) e no máximo **uma** pergunta de briefing; se o material enviado estiver fraco, **uma linha** pedindo o arquivo melhor | `casos.py sugerir`, `material.py checar` |
| 2. Combinado (antes de produzir) | como vamos trabalhar (checkpoints do modo), material que melhora o filme, o que será instalado, o custo, o uso do navegador, o que eu não consigo fazer, como dar nota | `conversa.py abertura` |
| 3. Antes de cada ação sensível | instalar programa, baixar arquivo, usar o navegador do usuário, chamar ferramenta paga: **o quê, de onde, tamanho/custo, por quê**, e esperar o sim | `ambiente.py plano / instalar / mcp` |
| 4. Checkpoints | storyboard ou prévia com **o que olhar** (2–3 perguntas fechadas: "o fecho com o logo está forte o bastante?") | folha de contato, `stills` |
| 5. Entrega | arquivo, o que a máquina verificou, o que **ninguém** verificou, onde olhar (tempo → cena), o que limita a nitidez, como pedir mudança | `conversa.py entrega` |

No modo autônomo, os momentos 1, 2 e 4 viram uma linha cada na nota de entrega. **O momento 3 nunca é pulado.** Instalar,
baixar pelo navegador e gastar dinheiro são permissões, não escolhas de gosto, e "faz tudo aí" não as cobre. Se o usuário
já disse "pode instalar" (`constraints.instalar` no estado), isso vale para programas **grátis** do plano mostrado. Gasto pago
continua exigindo pedido explícito e estimativa.

## Instalar programas (o usuário quer que a skill instale)
1. `python scripts/ambiente.py plano [--perfil core|3d|extra|tudo]` lista o que já existe e o que falta, com tamanho, origem e comando.
2. Mostre o plano ao usuário e peça **um sim para o lote**, não um sim por programa.
3. `python scripts/ambiente.py instalar faltando --sim "<palavras dele>"`:
   - grava o consentimento em `.local/consentimentos.json`;
   - usa o winget no Windows ou o brew no macOS.
   - O winget aceita os termos de cada pacote, e o plano avisa disso antes.
   - Comandos com `sudo` (Linux) não rodam: o usuário roda.
   - Sem `--sim`, o script não instala nada e sai com código 3.
4. Depois rode `python scripts/setup.py` de novo. Se o PATH não pegar, abra um terminal novo; `lib/tools` acha FFmpeg, Chrome e Blender mesmo fora do PATH.

Instale só o perfil que o filme pede. O core (Node, FFmpeg, Chrome) é para todo filme. O 3D (Blender) é só para produto
fotorrealista. Os extras são só para recorte de ilustração 2D.

## Ferramentas conectadas (MCP) e custo
- No início, passe para `ambiente.py mcp` os nomes das ferramentas que você enxerga nesta sessão (`mcp__<servidor>__<ferramenta>`).
- O script agrupa por servidor e classifica cada um como **pago**, **freemium** ou **grátis** pelo `references/ferramentas.json`.
- Conector desconhecido = tratado como pago até o usuário dizer o contrário.
- Diga ao usuário quais podem cobrar. Nunca use um deles sem:
  - pedido explícito;
  - estimativa da própria ferramenta (ex.: `estimate_video_cost`, `balance`, `account_get_usage`), mostrada **antes**, com valor e saldo;
  - um sim para aquele valor.
- Sem verba declarada, a verba é R$ 0.
- Depois de usar, registre em `CREDITOS.txt` o que foi gerado e quanto custou.

## Navegador do usuário (Claude in Chrome) e navegador embutido
- Para que serve:
  - baixar uma trilha, um vídeo de banco ou um efeito de site com licença clara (`ferramentas.json` → `sites`);
  - gerar imagem no ChatGPT do usuário (modo assistido).
- Antes de abrir, diga o site, o que vai buscar, quantos itens e a licença: `ambiente.py aviso --site pixabay pexels`.
- Durante:
  - trabalhe numa **aba nova**;
  - baixe **um arquivo por vez**;
  - confirme cada download dizendo o nome do arquivo e o site;
  - leia a licença na página do item.
- Nunca:
  - digite senha;
  - resolva CAPTCHA;
  - aceite termos ou compre algo sem o usuário;
  - baixe em massa por script (Pixabay, Pexels e Mixkit proíbem robôs);
  - use APIs de banco fora dos termos. A API do Freesound é só para uso não comercial, e a do Free Music Archive foi desativada.
- Ao bater em login ou CAPTCHA: pare e peça ao usuário para fazer aquela etapa.
- Depois: registre arquivo, origem, licença e data em `CREDITOS.txt`; o `asset-manifest.json` cobre imagens e vídeos.

## Material: peça cedo o que faz diferença
`python scripts/material.py checar <arquivos> --alvo 1080|4k` mede se cada arquivo aguenta o maior tamanho em que aparece,
com 25% de folga para o push de câmera:
- **logo:** vetor ou pixels suficientes, e fundo transparente;
- **foto e tela:** largura do quadro;
- **vídeo:** resolução e fps;
- **áudio:** WAV de 44,1 kHz ou mais.

O script diz o que pedir. Num filme real, não fazer isso custou um logo de ~300 px mole no fecho.

Material fraco não bloqueia o trabalho: siga com ele, avise no combinado e repita o aviso na entrega.
Interface inventada é um risco. Prefira capturas reais da UI com dados de demonstração e nunca invente números ou recursos do produto.

## Pedir e receber notas
- Peça notas **com tempo e ação**, juntas numa mensagem só. Registre cada uma como: **tempo · problema · resultado desejado ·
  o que não pode mudar** (ex.: `0:12,4 · texto entra cedo · entrar no bumbo seguinte · manter o corte`). Uma nota vaga ("tá estranho") vira uma pergunta fechada sua: "é o ritmo dos cortes entre 0:13 e 0:20 ou o som?".
- Nota que muda planos, ordem ou transições volta ao storyboard (`references/notas.md`). Nota de tempo, cor ou som muda só o trecho.
- Nunca diga que ficou bom porque o QA passou. O QA prova que **não há defeito medido**, não que o filme emociona.

## Sugira o próximo passo que mais melhora o filme
Na entrega, ofereça no máximo **um** próximo passo, o de maior ganho:
- material melhor (vetor, captura real);
- uma versão vertical;
- master em 4K;
- legenda.

Não ofereça um menu.
