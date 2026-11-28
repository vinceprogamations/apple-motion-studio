# Level 3: Blender

## Quando usar (decisão por plano)
- **Padrão para os planos principais de produto físico** quando material, reflexo, luz, sombra, profundidade ou close decidem a
  qualidade: no comparativo do mesmo plano (Ressoa R1, `engine-3d.md`), o Blender ficou visivelmente superior na avaliação do
  usuário (sombra de contato, microtextura, reflexos entre peças). Use-o no master quando o teste no ambiente confirmar o ganho
  e o render couber no prazo (≈ 8,5 s/quadro 1080p, 64 amostras, RTX 3050).
- **Three.js** para prévias rápidas, planos que já atingem o padrão e quando a edição em tempo real decide (UI viva na tela,
  revisões de timing em segundos). Mesma geometria nos dois: exporte o GLB do Three (`render.mjs dump`) e importe no Blender.
- Sem Blender: valide a alternativa local e registre a diferença. Compare pelo quadro final e pelo papel do plano, não só pelo tempo.

## Pré-visualização de câmera (previs)
Se o benefício depende de ver profundidade, contato ou a face traseira, monte uma versão econômica com formas simples (ou o GLB
em cinza). Compare enquadramento, lente ou posição **mantendo a mesma ação**: primeiro quadros fixos, depois anime só o trecho de
câmera que prova a revelação ou a ocultação. No modo autônomo, escolha o plano e registre o motivo (câmera: posição, alvo, lente,
quadro em que a promessa aparece). Peça simples de texto/UI segue pelo fluxo que já resolve.

## Luz de produto
No enquadramento escolhido, confira a separação objeto/fundo também numa prévia **sem cor** (diagnóstico). Mude **uma fonte por
vez** e compare o mesmo quadro. Se uma superfície brilhante esconde uma gravação, ajuste posição ou tamanho da fonte e confira a
face vizinha. Materialidade e fidelidade à marca se julgam na prévia em cor. Ensaio validado no projeto de origem
(`luz.py`: luz A × luz B no mesmo quadro, contraste local medido da gravação, prévia em cinza).
Referências de método: [Scenario Blender Previs](https://github.com/scenario-labs/skills/blob/3c4d18cd0be2e5280a5accebfeef9ddc98b9a15b/skills/dcc/blender/scenario-blender-previs-storyboard/SKILL.md),
[Scenario Blender Lighting](https://github.com/scenario-labs/skills/blob/3c4d18cd0be2e5280a5accebfeef9ddc98b9a15b/skills/dcc/blender/scenario-blender-lighting-rendering/SKILL.md) (redação própria).

Use Blender when the product should look filmed. The user installs it from blender.org and never has to open it: Claude
runs it with no window, using `blender -b -P scene.py -- ...`. The conversation looks the same as the other levels, with
a storyboard the user approves first, then a render, and the render just takes longer. Model check shots (below) and
storyboard stills are fine before approval; the animation render is not.

Find Blender first. Common places are `/Applications/Blender.app/Contents/MacOS/Blender`, `/opt/homebrew/bin/blender` and
`C:\Program Files\Blender Foundation\Blender <version>\blender.exe`.

## Start from the example

`scripts/blender/example_scene.py` is a small working scene. Copy `kit.py`, `tracks.py` and the example next to your
assets, then check it runs before building on it:

```
python3 example_scene.py mesh
blender -b -P example_scene.py -- frames 1280 24 0.5 2 3.5
```

Arguments after `--` are the output folder, width, samples, optionally `flat`, then optional times (leave them out for
every frame). Finished frames are skipped, so a crashed render picks up where it stopped.

## Get the model right first

Wrong shapes are the first thing people notice, and Claude won't notice them unless it compares against a reference.

1. **Use a real model if there is one.** `kit.load_model()` reads GLB, glTF and OBJ. Check the licence if it's going
   to be published.
2. **Otherwise build it with distance functions** in `mesh_from_sdf.py`. This gives clean, smooth surfaces: smooth unions
   for bodies, `revolve()` for caps and bells, `rounded_pocket()` for recesses, smooth cuts for slots.
3. **Study reference from every angle.** Ask for a screen recording of a 3D viewer turning the product, plus wireframes
   if the viewer has them. Pull frames with ffmpeg, crop in at full resolution, and write down proportions and
   details. Screen recordings saved through the floating thumbnail can sit in a protected temp folder, so ask the
   user to save them somewhere normal.
4. **Render check shots next to the reference.** Add a grey world and a few still poses, put them side by side with
   the reference, and go round until they match. It takes seconds, so do this before any animation.

Modelling notes:
- Mirror the second of a pair with a negative scale, then check the left and right are the correct way round.
- Details like vents look proud on a curved surface if placed as flat discs. Use an ellipsoid sunk into the surface with
  a matching curve (depth about `a² / surface radius`).
- Heavy smoothing fills small holes and blurs steps, so smooth small parts less.
- Keep creases and seam lines faint. What looks right as a thin line in a reference often looks too harsh when lit.
- Interior detail matters if the object opens: pockets, hinges, rims. Use the wireframes.
- Check how things fit when closed or moving. Parts can poke through a lid, or stems can cut through a case if they
  rotate on the way out. Move them straight out first, then rotate. Hide anything inside a closed object until it opens.

## Light and camera

- **One light source**: `kit.key_light()`, a big soft area light, with a nearly black world. This makes it look cinematic.
- Use a long lens (about 70–90mm) and let the camera get very close for macro beats.
- Build every move from `tracks.py`, with one curve per move. Render a few frames either side of a handover, as a change
  in speed there reads as a jolt even if the position matches.
- Plan the path to show the detail you care about. Turn the object so its most recognisable feature faces the camera.

## Render settings and time

- Render at 1920 wide with 24 samples and motion blur, then upscale to 4K when compositing. On an M2 Pro this took about
  8 seconds a frame, so about 30 minutes for 8 seconds at 25 fps. Close-ups are slower.
- Test at 1280 wide on about 15 frames for the storyboard, which takes a couple of minutes.
- It's heavy on the GPU and the computer may slow down, so warn the user, and don't run anything else big alongside it.
- Render with a transparent background. That makes it easy to put it on black, on footage, or over text.
- If only the end of an animation changes, re-render only those frames and reuse the rest.

## Flat silhouette version

Pure black and white, no shading, no lines. It's a striking look, and it blends well into silhouetted footage.

Pass `flat` to a scene that calls `kit.flat_mode(black_materials=('grille', 'vent'))`. Everything turns pure white except
the named materials. It renders quickly, as there's no real lighting to calculate, so lower samples are fine.

Keep only the parts that are really black on the product. Hide lettering, status lights, seams and hardware: the
fewer the details, the stronger it looks. Black lines between parts are possible, but they look like a drawing rather
than a silhouette, so offer them only if the shape doesn't read.

A variation that works well: start shaded, flash one inverted frame (a negative of the picture, on a fast movement,
with a shutter sound), and carry on as a flat silhouette.
- **Caminho de saída sempre absoluto** (`os.path.abspath`). Um `render.filepath` relativo em modo `-b` foi resolvido na raiz do disco (os PNGs foram para `C:\<pasta>` em vez do projeto).

---

# Guia de execução no Claude Code (27/11/2026)

## Escolha por plano
| O plano depende de… | Use |
|---|---|
| tipografia, UI legível, timing editável em segundos | DOM/canvas (`render_dom.mjs`) |
| 3D simples, parallax e espessura, com revisão rápida | Three.js (`render.mjs --gpu`) |
| **geometria, articulação, material, luz, reflexo, oclusão ou sombra de contato** | **Blender/Cycles** |
| 3D com texto e UI por cima | **híbrido**: PNG do Blender + camada HTML com `renderAt` carregando o quadro (ver o projeto de Natal na pasta `projetos/`) |

## Modelagem e rig
- **Escala real** (metros) e proporções do aparelho de referência. Defina espessura, bevel (raio coerente com o tamanho), normais (smooth + Weighted Normal), UV nas telas e eixos locais.
- **Hierarquia**: as partes fixas são filhas da base. Teclado, trackpad e botões acompanham o corpo.
- **Partes articuladas** ficam sob um **`Empty` no eixo físico**, por exemplo a dobradiça na borda de trás. Desloque a peça de modo que a borda dela coincida com o eixo. Gire o `Empty`, nunca a peça pelo centro, e confira a folga com a peça fechada.
- **Modelos prontos** (o usuário permite): confira licença, escala, eixos e materiais. Evite os que imitam marca real.

## Movimento e câmera
- **Blockout primeiro**, em cinza e com poucas amostras: enquadramento e timing antes de material.
- **Curvas**: `tracks.mono` ou F-curves sem overshoot quando a física não pede. Uma curva por movimento, com velocidade contínua nas emendas. Renderize quadros dos dois lados de cada emenda.
- **Foco (DOF)** acompanha o objeto principal. Parallax e oclusão vêm da câmera.
- **Motion blur** com shutter ~0,45. Renderize um plano por execução, para o blur não atravessar o corte.
- **Geometry Nodes** para repetição procedural (teclas, grades, partículas).
- **Simulação** só quando a interação física justificar, com cache versionado por plano.
- **Tracking** só para integrar o 3D a filmagem.

## Acabamento e saída
- Teste **luz** e **material** separadamente: primeiro uma prévia sem cor (forma), depois em cor. Mude uma fonte de luz por vez.
- Na dúvida entre motores, compare **EEVEE × Cycles** no mesmo enquadramento e em movimento.
- Confira reflexos, sombra de contato e consistência de cor. `Khronos PBR Neutral` preserva a cor de UI e de marca.
- Confira **cintilação** em quadros consecutivos. Se houver, use denoise temporal ou mais amostras.
- Saída em PNG basta para compor em HTML. Use EXR multicamada, com os passes necessários, quando a composição pedir.
- **GLB entre Blender e Three.js**: confira escala, eixos (Y-up × Z-up), materiais e animação importada.

## Regras de CLI (headless)
- Confirme a versão e o dispositivo: `blender -b --version`. O kit escolhe OPTIX ou CUDA e imprime `device`.
- Prefira `bpy.data`, que é direto e não depende de contexto. Ao usar `bpy.ops` em headless, confirme o contexto (objeto ativo, modo).
- Rode `blender -b --python-exit-code 1 -P scene.py -- …`, para que uma exceção vire código de saída diferente de zero.
- Ao renderizar um `.blend`, passe as opções **antes** de `-f`/`-a`, porque os argumentos são processados em ordem. Exemplo: `blender -b f.blend -o //out/#### -F PNG -f 10`.
- Saída sempre em caminho **absoluto** (`os.path.abspath`), com numeração contínua (`0001.png`…) e uma pasta por versão.
- Antes do render completo, meça o custo em 3–4 quadros representativos (close, plano aberto, vidro).
- Para retomar um render, o kit pula os PNG que já existem. Antes de compor, confira a integridade: contagem de arquivos, tamanho maior que zero e se abrem.

## Caso de regressão — notebook do filme de Natal
Aplique a todo aparelho articulado:
1. Teclado e trackpad são filhos da base e não sobem no "explodido".
2. A tampa gira no `Empty` da dobradiça traseira.
   - Fechada, ela fica acima das teclas, com folga.
   - Aberta, o ângulo segue a referência do aparelho. Os ~108° foram decisão daquele plano, não regra.
3. Revise estes momentos: **fechado**, **primeiros quadros da abertura**, **menor folga**, **intermediários** e **pose final**, além da câmera final e de **uma vista lateral**.
4. Nos pontos de risco, use quadros consecutivos e recortes a 100 %.
5. Para checar contato ou interseção, consulte a **geometria avaliada** no quadro certo: `scene.frame_set(f)` seguido de `obj.evaluated_get(depsgraph)`. Não use a malha original.
6. `qa_frames` aprovado **não** encerra a revisão de peça solta, interseção, pivô ou contato errado.

## Fontes
- Render headless, ordem dos argumentos e sequência: https://docs.blender.org/manual/en/latest/advanced/command_line/render.html
- API e *dependency graph*: https://docs.blender.org/api/current/bpy.types.Context.html
- Motores de render: https://docs.blender.org/manual/en/5.3/render/introduction.html
- Instâncias e glTF: https://docs.blender.org/manual/en/5.3/modeling/geometry_nodes/instances.html · https://docs.blender.org/manual/en/5.3/addons/scene_gltf2.html
- Gestão de cor e passes: https://docs.blender.org/manual/en/4.5/render/color_management.html · https://docs.blender.org/manual/en/latest/render/layers/passes.html
- Comunidade, rig de dobradiça: https://blender.stackexchange.com/questions/162967/how-to-rig-a-folding-laptop-with-a-hinge
- Comunidade, luz de produto e bevel: https://blenderartists.org/t/how-do-i-achieve-realistic-lighting-like-the-attached-product-render/1617205
- Cintilação em animação: https://blenderartists.org/t/flickering-noise-on-cycles-animation/1383040 · https://studio.blender.org/blog/denoising-sprite-fright/
