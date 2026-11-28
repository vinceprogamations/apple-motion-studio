# Texto de tela (copy) + música — etapa obrigatória ANTES do storyboard

Regra do usuário (27/11/2026): "primeiro pense nos textos e músicas e depois construa a animação com SFX em cima". Ela veio
do filme de Natal: o slogan apareceu duas vezes, no título ("Seu sistema, pra você") e no fecho, porque os textos foram
escritos durante a animação. Este método funciona sozinho. Se os plugins `copy-that-sells` e `Social Media Skills`
(`hook-writer`, `reels-script`) estiverem instalados, use-os **dentro** desta etapa, para gerar alternativas, sem pular o checklist.

## Ordem das decisões
1. **Ideia em uma frase** (o que o espectador entende) e **o inimigo** (a dor concreta que o filme derrota).
2. **Roteiro de texto**: todo texto que aparece na tela, em ordem, com a função e o tempo aproximado de cada um.
3. **Trilha** escolhida (ou as opções reservadas ao usuário) com a **grade**: BPM, drop, respiros (`scripts/batidas.py`, envelope RMS).
   A virada do texto cai no drop.
4. Depois: storyboard → animação → revisão → **SFX em cima da imagem pronta**. Respeite as decisões reservadas (`studio.py state gate`).

## Estrutura (gancho → dor → virada → prova → fecho)
| Função | O que faz | Exemplo aprovado |
|---|---|---|
| Gancho (0–1 s) | Para a rolagem sem som e sem marca: hora, cena ou contraste reconhecível | "23h47." + balão "Tem horário amanhã?" |
| Dor | Consequência concreta, na 2ª pessoa | "Quase meia-noite / e você ainda tá respondendo." |
| Virada (no drop) | A frase mais forte, a mudança | "Com a [marca], / sua agenda responde por você." |
| Prova | Ações que a cena consegue **mostrar** | "Horário marcado. → Lembrete enviado. → Você, dormindo." |
| Diferencial | Quem faz (equipe × automação) | "Montado com você, pela nossa equipe." |
| Fecho | Marca + slogan (uma vez) + CTA (uma vez) | [marca] · *slogan* · site da marca |

## Ganchos: gere de verdade, escolha com critério
Escreva **8–10 ganchos de ângulos diferentes** (não variações da mesma frase):
- hora/cena;
- pergunta;
- contraste ("Dezembro chegou. / Seu WhatsApp, não.");
- número verdadeiro;
- objeção ("Site de modelo pronto? / Todo mundo tem igual.");
- antes × depois;
- frase do cliente;
- consequência.

Pontue cada gancho de 1 a 5 em três critérios e fique com o maior total:
- **impacto no 1º segundo**;
- **legibilidade no celular**;
- **o que a cena consegue mostrar** (a animação precisa provar a frase).

## Regras de cada frase
- **Uma função por frase**; corte tudo o que repete a ideia de outra frase.
- **Concreto > genérico.** Troque adjetivos por ação ou consequência. "Horário marcado. Lembrete enviado." já diz o que mostrar. São proibidos sozinhos: "solução completa", "inovação", "do seu jeito", "tecnologia".
- **Curta**: título com ≤ 5 palavras, uma ideia por tela, legível em 1 s a 360 px de largura (≥ 64 px a 1080). Quebre frases longas em telas.
- **Verbo forte, 2ª pessoa** ("Sua agenda enche sozinha", não "Agenda automatizada").
- **Slogan uma vez** (fecho), **CTA uma vez** (fim, específico).
- **Claims sustentados**: nada de prazo, número ou garantia que a marca não confirme. Números de interface são demonstração.

## Ritmo de leitura (Reels)
- Tempo na tela ≈ **0,3 s + 0,25 s por palavra** (mínimo 0,8 s), entrando palavra a palavra.
- A frase da virada entra **no drop**. A prova vem em batidas seguintes (uma ação por batida).
- Revise **sem áudio**: o filme tem de se entender só pela imagem e pelo texto.
- Revise com a animação: texto, animação e demonstração dizem a mesma coisa no mesmo momento?

## Revisar texto do usuário
Preserve a intenção e as palavras. Proponha só **quebras de tela**, cortes de repetição e trocas de genérico por concreto, sempre explicadas.
Se o usuário pedir "só o texto", responda **só com o que entra no vídeo**, sem comentários.
Exemplo real: "com a [marca] Sua agenda responde por você, com bots automatizados" virou três telas: "Com a [marca]," / "sua agenda responde por você." / "com bots automatizados".

## Checklist (antes do storyboard)
- [ ] O gancho funciona no 1º segundo, sem som e sem a marca?
- [ ] Cada frase tem uma função e nenhuma repete ideia, slogan ou CTA?
- [ ] Cada tela se lê em 1 s no celular?
- [ ] A frase mais forte está no drop da trilha escolhida?
- [ ] A cena consegue mostrar cada prova?
- [ ] Todo claim é verdadeiro e confirmado?

Salve o roteiro em `<filme>/copy.md` (ou `BEATS.md`), com tempo, função e texto de cada tela.
