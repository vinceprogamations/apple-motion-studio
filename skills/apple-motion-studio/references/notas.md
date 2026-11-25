# Notas e revisões depois de ver e ouvir o filme

Uma nota vira **uma mudança localizada**, não um filme novo. Ela gera uma versão nova e nunca sobrescreve o master aprovado:
`studio.py promote` guarda o master anterior.

## 1. Traduza a nota para uma variável

| Nota | Onde mexer | Prova |
|---|---|---|
| "atrase a confirmação em seis quadros" | uma batida no bloco `B` (`+6/FPS` s). O cue ligado a ela anda junto porque o som segue `window.EVENTS`. Se a música tinha o drop naquele evento, alongue o respiro antes do drop: tudo que vem antes fica idêntico amostra por amostra. | quadros alterados só na janela afetada; eventos alterados = só aquele; onset no **MP4 decodificado** desloca `6/FPS` s e os vizinhos ficam (`qa_audio.py onset`) |
| "troque a foto deste perfil" | o arquivo no `asset-manifest.json` + `assets.py approve` | `assets.py affected` lista as cenas que dependem da foto; o portão confere a ligação e a resolução |
| "deixe a confirmação menos estridente" | uma variável do cue (`lp`) | contato no mesmo quadro (`align: "start"`), demais stems idênticos (`mix.py --stems`), brilho medido menor |
| "mais música no final" | `env` do bed ou edição musical no fim | loudness do trecho medido; o resto inalterado |
| "a headline fica em cima da legenda" | trajetória/tempo da headline | `render_dom.mjs layout`: a colisão some nas mesmas amostras |

## 2. Re-renderize pelo mesmo comando e compare

- Antes e depois lado a lado no mesmo trecho (ex.: `scripts/demo.py` gera `antes x depois.mp4`).
- O relatório deve dizer o que mudou, o que **não** mudou e como isso foi medido.

## 3. Quando volta para o storyboard

Uma nota que muda planos, a ordem ou as transições volta ao storyboard. Ajuste de tempo, cor ou som não volta. No modo guiado, essa volta passa por nova aprovação.
