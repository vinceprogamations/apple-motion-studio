# Pitfalls (each one happened)

| Symptom | Cause | Fix |
|---|---|---|
| Black / empty frames on a 3D page | headless Chrome without a GPU has no WebGL2 | `--gpu` on every still and render |
| Ghost copies of fast-moving things | too few motion-blur sub-frames | 12 sub-frames over a 180° shutter |
| Text hidden behind a card in 3D | depth sort puts it behind | give overlay panels a `bias` (400+ for text) |
| A morphing curve flips inside out | interpolating to a target with opposite curvature | rise/bend to the rim's curvature first, then travel along it |
| Morphing parts overlap | they travel at different speeds | one shared angle; each part starts when the one ahead is a third away |
| A grid's lines appear and vanish | 1–2 px lines resampled by the shot's push-in | ~3.5 px lines, lower opacity, integer offsets |
| End logo off-centre | the logo PNG's centre isn't its visible centre, and the camera drifts | centre by bounding box; no drift on the end shot |
| Phone side buttons look wrong | hard to place them accurately on a rebuilt phone | leave them off |
| Icon pixelates on the final push | it's part of a screenshot texture | overlay it as its own high-res vector panel |
| Phone fade "snaps" off | an ease that ends fast (inCubic) | a symmetric sine fade over ~1s |
| Cut-out loses a yellow folder / light trousers | enclosed-pocket removal or a flood from the bottom edge | `--keep-pockets` / `--no-bottom` |
| Cut-up layers have missing edges | overlapping objects cut apart | redraw the scene as shapes |
| Gradient on a headline is unreadable | gradient text on a colour field | solid ink on fields; gradients only on dark |
| Posterised motion looks uneven at 25 fps | 25/8 isn't whole | render posterised ads at 24 fps |
| Canvas shadow offset wrong at 4K | shadow offsets ignore the transform | multiply offsets by the render scale |
| A mid-line `//` comment swallowed the code after it | comments in long one-line statements | end-of-line comments only; check stills after edits |
| Two renders fight over a port/profile | shared Chrome ports | render.mjs uses its own port + profile per run |
| The Mac freezes during renders | many parallel 4K encodes | 1–2 renders at a time |
| The screen recording can't be opened | it's still in the protected temp folder from the screenshot thumbnail | ask the user to save it somewhere normal |
| Tips or parts poke through a closed lid | they stick out further than the case allows | hide them until the lid opens, or shrink them slightly as it opens |
| Stems cut through the case | rotating before they've cleared it | fly straight out first, then rotate |
| A kink in a smooth move | two paths joined at a handover | one continuous curve for the whole move (`tracks.py`) |
| Details stand proud on a curved surface | flat discs on a curve | curved ellipsoids sunk into the surface |
| A hole fills in | heavy smoothing, or the surface covering a disc | smooth small parts less; check the disc sits above the floor |
| A white object vanishes on white | no edge between them | a thin dark outline as it reaches the white |
| Hard lines around filled gaps in a frame | the fill stops at the anti-aliased edge | dilate the fill mask a few pixels |
| A render stopped halfway or the computer crashed | it's a heavy job | re-run the same command: finished frames are skipped. Test at 1080 before going higher |
| A blank contact sheet from ffmpeg | `-frames:v N` with `tile` counts sheets, not frames | trim with `-t`, then `tile`, then `-frames:v 1` |

## Dos filmes do projeto de origem

| Sintoma | Causa | Conserto |
|---|---|---|
| Recorte do canvas (`destination-out`) não apaga nada | `fillStyle` ainda era um gradiente transparente de antes | `ctx.fillStyle = '#000'` explícito antes de recortar |
| Logo/dial mostra "-1,0" | número negativo antes da batida | passe `null` quando o valor for < 0 e não desenhe |
| Objeto dá um pulo na troca 2D → 3D | o painel 3D não tem o mesmo tamanho projetado | ajuste a escala no frame da troca (Vela: `sc × 1,05`) e confira com stills dos dois lados |
| Headline some na troca 2D → 3D | desenhada só num dos ramos | desenhe o texto nos dois ramos (ou depois deles) |
| Chips sobre a headline (9:16) | layout do 16:9 copiado | mova os chips para baixo do painel |
| Boom/riser entra fora do tempo (0,6–3 s) | o pico do arquivo vem tarde ou o riser tem cauda | `align: start` no boom, `dur` cortando o riser na parada; confira o RMS |
| Drop da música não bate no reveal | faixa cortada a olho | `finish.py --probe` acha o drop; `--music-drop/--film-drop` alinham |
| Cores levemente diferentes entre players | MP4 sem tags e matriz BT.601 | `render.mjs` desta skill converte com o filtro `colorspace` e marca BT.709; `finish.py` mantém as tags |
| `scale=out_color_matrix=bt709` não muda a cor | swscale não troca matriz yuv→yuv (entrada JPEG) | use o filtro `colorspace` (já no render.mjs) |
| `ffmpeg: command not found` no Git Bash | instalado pelo WinGet depois de abrir o terminal | `export PATH="$PATH:$(ls -d /c/Users/*/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin \| head -1)"` |
| 403 ao ler o zip do Sonniss | servidor exige navegador | header `User-Agent` de navegador nas requisições Range |
| `readinto` reclama de memoryview | buffer com formato errado | `memoryview(b).cast('B')` e corte a resposta do Range ao tamanho pedido |
| Curl em massa no Pixabay/Mixkit bloqueado | termos proíbem robôs | botão do site no navegador, poucos itens, usuário logado |
| Vidro parece cinza chapado | sem fundo refratado atrás | `glassUnder`/`chip2D` desenhando `BGS` borrado e ampliado dentro do contorno |
| Render 4K lento demais | `ctx.filter` blur em canvas cheio | desfoque a partir do `BGS` pequeno; sub-frames 6 só nas janelas `FAST` |
| Fonte cai no fallback só no render | fonte de CDN bloqueada ou não carregada antes do quadro | fontes locais em `templates/dom/fonts/`; `ready` rejeita fonte que não decodifica |
| Duas animações brigam pela mesma propriedade | dois tweens/expressões no mesmo `transform` (ex.: push + entrada) | uma expressão só por propriedade; anime só `transform` e `opacity` |
| Tagline, número ou tela inventados | agente preencheu lacuna do brief | todo texto na tela vem do brief/copy aprovado; interface real por captura autorizada |
| "Pronto" sem ter visto | QA passou e o agente concluiu que ficou bom | entrega por `conversa.py entrega`: medido ≠ assistido |

