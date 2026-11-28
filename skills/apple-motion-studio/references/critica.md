# Crítica com nota antes de mostrar o filme

O QA técnico (`qa_frames.py`, `qa_audio.py`) prova que não há defeito medido. Não prova que o filme é bom. Antes de mostrar um
filme ao usuário, faça a crítica por nota. Ideia adaptada da motion-reel-kit, com critérios e tetos ajustados ao estilo desta
skill: sem quique no texto e uma câmera contínua.

## Kit de revisão (sempre do MP4 renderizado, nunca da página)
1. **Folha de contato:** `ffmpeg -i <render>.mp4 -vf "fps=2,scale=480:-1,tile=6x8" -frames:v 1 contato.jpg`.
2. **Celular:** `python scripts/qa_celular.py <render>.mp4`. Gera a folha a 360 px de largura e, no 9:16, as áreas cobertas
   pela interface do Reels.
3. **Ação mais rápida:** 12 quadros seguidos no trecho de maior movimento (`render_dom.mjs stills` em passos de 1/fps), para
   pegar pulos, sobreposição de legendas e bordas.
4. **Medições:** `qa_frames.py`, `qa_audio.py deliver` e a saída de `mix.py`. Os avisos de pico atrasado entram como evidência.

## Quem critica
Um **subagente novo**, que não escreveu o filme. Ele recebe o caminho do projeto, o briefing (`briefing.py resumo`) e este
arquivo. Se não houver subagentes, faça você mesmo com a voz de crítico: evidência primeiro, sem defender o código. Ele olha
TODAS as imagens e dá nota de 1 a 10. Uma nota 8 significa que dá para entregar a um cliente exigente.

| Critério | 10 é… | Teto automático |
|---|---|---|
| **Gancho (0–2 s)** | o quadro 0 já diz algo; a promessa chega até 1,5 s | quadro 0 vazio ou quase preto sem intenção declarada → 6 |
| **Leitura no celular** | todo texto que precisa ser lido se lê a 360 px; o fecho/CTA é o mais legível do filme | CTA ilegível → 6; texto nas áreas do Reels → 7 |
| **Qualidade do movimento** | molas com peso, sobreposição e acomodação; motion blur nos movimentos rápidos; nada pula | fade como entrada ou saída → 6; pulo visível na sequência rápida → 7 |
| **Variedade e ritmo** | algo novo a cada 2–4 s; tamanhos de plano e transições variam; acelera rumo à marca | parado > 2 s fora do fecho, ou buraco > 4 s → 7 |
| **Fidelidade à marca** | logo e interface reais, cores e fontes exatas, um acento | interface inventada onde existe a real, fonte errada → 6 |
| **Sincronia do som** | todo golpe cai com a imagem (±45 ms); a trilha na grade dos cortes (`batidas.py`); −14 LUFS | golpe fora > 80 ms, trilha derivando da grade, loudness fora → 6 |
| **Composição em cada formato** | cada formato reenquadrado, não cortado; sem zonas mortas | 9:16 com um terço vazio por > 1 s → 7 |
| **Acabamento** | sem quadro vazio, sem legenda dupla na troca, sem resto de cursor, sem lasca de letra na máscara | qualquer quadro vazio no meio, ou legenda dupla → 7 |

Na saída, ele escreve em `revisao.md` do projeto:
- a tabela com nota e evidência (tempo, quadro, medição);
- os **3 piores problemas**, por dano ao filme;
- uma **correção testável** para cada um;
- o veredito: ENTREGAR (tudo ≥ 8) ou MAIS UMA RODADA.

## Regras do ciclo
- Corrija os 3 piores, confirme cada correção com stills ou com o trecho renderizado e repita.
- Faça **no mínimo 2 rodadas** antes de mostrar a primeira versão ao usuário (modo guiado: antes do checkpoint do filme com som).
- Um problema que já apareceu na rodada anterior e continua visível não pode ganhar nota maior que a anterior.
- Na entrega, cite as notas finais em uma linha: "crítica interna: 8–9 em tudo, 2 rodadas". Isso continua sendo **medido**.
  Não diga que o filme ficou ótimo: quem julga ritmo e emoção é o usuário.
