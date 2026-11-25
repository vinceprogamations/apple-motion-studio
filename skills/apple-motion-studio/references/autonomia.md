# Autonomia: o que o usuário delegou e quando perguntar

O escopo vem das palavras do usuário, não do hábito do agente. Grave-o antes de começar:

```
python scripts/studio.py state init <projeto> "<palavras exatas do usuário>"
python scripts/studio.py state gate <projeto> <etapa>         # 0 seguir · 3 perguntar SÓ isto · 4 master vira prévia
python scripts/studio.py state decide <projeto> <etapa> "<escolha>" "<motivo em uma frase>"
python scripts/studio.py state approve <projeto> <etapa> "<escolha>" [--by usuario|terceiro:<quem>]
python scripts/studio.py state show <projeto>                 # retomada numa sessão nova: master, aprovações, próxima operação
```

Etapas: `brief`, `storyboard`, `direcao-visual`, `paleta-sonora`, `musica`, `foley`, `locucao`, `mix`, `assets`, `master`.

## Os três estados de uma decisão (nunca misture)

| Estado | Significa | Quem pode mudar |
|---|---|---|
| `delegado-agente` | o agente escolheu porque o usuário delegou; o campo `scope` guarda as palavras dele | o agente, numa revisão; o usuário, a qualquer momento |
| `aprovado-usuario` | o usuário aprovou em pessoa | só o usuário |
| `exige-terceiro` / `aprovado-terceiro` | a aprovação pertence a outra pessoa (cliente, jurídico, dono da marca) | só esse terceiro |

## Tabela de comportamento

| Pedido | O que fazer |
|---|---|
| "Faça o comercial inteiro, decide tudo." | Assuma a direção visual e a sonora. Revise internamente o storyboard e a paleta sonora, escolha assets autorizados, produza, valide e entregue **uma** versão principal. Zero perguntas de gosto. |
| "O storyboard já está aprovado. Cuide de todo o som." | Assuma música, foley, voz quando pertinente, mix e acabamento. A montagem aprovada é a referência: se uma faixa pedir outros cortes, tente antes outra edição musical ou outra faixa. |
| "Faça tudo, mas quero escolher a música." | `music_pick.py --ab <pasta>` prepara a recomendação e uma alternativa no mesmo trecho, com loudness comparável. Faça só essa pergunta e avance em paralelo no foley, na voz e na imagem. |
| "Faça tudo, sem locução." | `voz=False` é requisito. A promessa chega pela imagem, pelo texto e pelos eventos sonoros. |
| A trilha favorita custa créditos e não há verba | Sem verba declarada, a verba é 0: escolha outra faixa apta (o `music_pick.py` faz isso e relata a substituição). Pergunte sobre verba só se o pedido exigir aquela gravação. |
| "…com a assinatura sonora oficial da minha marca" e o arquivo não existe | Faça o resto. Peça somente o arquivo, ou uma forma autorizada de obtê-lo. Até lá o master sai como **PRÉVIA** (`state gate master` → 4). Quando chegar: `state present`. |
| Nada delegado | Modo guiado: pare nos checkpoints acordados (storyboard e master). |

Pedir a preferência musical de quem já delegou o som é uma falha. Uma aprovação específica que o usuário reservou continua
dele mesmo dentro de uma delegação ampla.

## Escolher música de forma reproduzível

1. **Primeiro autorização, depois gosto:** licença desta cópia verificada, uso comercial, destino, verba e disponibilidade.
   - `--dest publico` exclui faixas com Content ID registrado ou desconhecido.
   - `--dest redistribuir` (demo pública, repositório) exige licença de redistribuição.
2. **Depois encaixe:** drop que cai no reveal, contraste respiro → drop, energia no reveal, graves, um final aproveitável e espaço para a voz (prefira faixas instrumentais quando a fala é protagonista). Preferências aprovadas **daquele cliente** só desempatam.
3. **Comando:** `python scripts/music_pick.py <catalogo.json> --reveal <s> --len <s> [--dest …] [--prefer …] [--ab <pasta>] --out escolha.json`.
   - O resultado traz a escolha, a alternativa, as rejeitadas com motivo e a substituição.
   - No modo autônomo, registre o `why` com `state decide … musica`.
   - Faça A/B só quando a dúvida mudar o filme, ou quando o usuário reservou a escolha.
4. **Sem acervo autorizado,** gere uma trilha original: `python scripts/synth_music.py <saida.wav> --len <s> --drop <reveal> [--voice-gap a-b:dB]`.
   - É determinística e de autoria própria, por isso pode ir para uma demo pública.
   - Declare que ela foi medida, não ouvida.

## Voz

- Use locução quando ela acrescentar contexto ou compreensão.
- Em português, confira nomes próprios, siglas, a pronúncia da marca, pausas e ênfases.
- Uma voz obrigatória mantém sua identidade e autorização.
- Para palavras decisivas, a música recua **só** naquele intervalo (automação, não volume global). Meça com `qa_audio.py masking --voice <voz.wav> --bed <cama.wav> --word a-b` (SNR na faixa da fala, ≥ 6 dB).
- O LUFS integrado não prova inteligibilidade.

## Revisar um som em linguagem comum

Transforme a nota numa hipótese audível e mude **uma** variável por vez:

| Nota | Mudança |
|---|---|
| "menos estridente" | `lp` / menos agudos no cue |
| "mais macio" | ataque mais gradual |
| "mais seco" | menos reverberação |
| "parece outro material" | trocar a fonte |

Depois confira:

- **Contato:** o quadro de contato precisa ficar onde estava. Use `align: "start"`, porque realinhar pelo pico depois de filtrar pode mover o contato (medido: −6 ms).
- **Demais stems:** iguais bit a bit (`mix.py --stems`).
- **Arquivo entregue:** meça no MP4 decodificado com `qa_audio.py onset a.mp4 b.mp4 --at <s>`.

Evidência: `tests/run_autonomia_audio.py`.

## Entrega e evidência

`python scripts/qa_audio.py deliver <final.mp4> [--profile web|ebu-r128-s1] --timeline <render>.timeline.json` mede o
arquivo que vai tocar:

- duração, canais, LUFS integrado, true peak e curto prazo máximo;
- cancelamento ao dobrar para mono;
- silêncios não declarados.

Perfis de loudness:

| Perfil | Alvo |
|---|---|
| `web` | −14 LUFS / −1 dBTP |
| EBU R 128 s1 (comerciais em radiodifusão) | −23 LUFS, curto prazo ≤ −18, −1 dBTP |

Um Reels não herda o perfil de radiodifusão.

Registre cada evidência como **medido**, **ouvido**, **simulado** ou **testado em aparelho físico**. Sem escuta disponível:

1. corrija o que é mensurável;
2. entregue a melhor versão tecnicamente validada;
3. declare a limitação;
4. ofereça a escuta humana depois.
