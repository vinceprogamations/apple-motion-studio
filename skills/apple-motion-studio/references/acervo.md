# Acervo de referências (modelos 3D, luz de estúdio, materiais, telas de apps)

Os filmes ficam melhores quando a skill não precisa inventar tudo: um vaso de planta, uma poltrona ou uma cadeira de barbeiro
fotorrealista, um HDRI de estúdio para o produto no Blender, couro e madeira com textura de verdade, e o layout real de um perfil
do Instagram ou de uma conversa do WhatsApp para recriar a tela sem errar proporção. O acervo junta isso num só lugar, com
licença livre, e é reutilizado em todos os filmes.

Pasta padrão: `<projeto>/referencias/recursos-3d-e-telas/` (os binários ficam fora do git; `acervo.json` registra o que veio,
de onde, quando e com que consentimento).

## O que tem (lista curada em `scripts/acervo.py`)
| Parte | Conteúdo | Fonte | Licença | Tamanho |
|---|---|---|---|---|
| `polyhaven` | 21 modelos glTF 2k: cadeira de barbeiro, plantas em vaso, vasos de cerâmica, poltronas, sofá, mesas, luminárias, croissant, bolo, jogo de chá, câmera… | Poly Haven | CC0 | ~300 MB |
| `hdris` | 4 HDRIs 4k de estúdio para iluminar produto | Poly Haven | CC0 | ~95 MB |
| `materiais` | 7 PBR 2K: madeira, mármore, concreto, tecido, couro, terrazzo, reboco | ambientCG | CC0 | ~130 MB |
| `telas` | capturas oficiais pt-BR da App Store (Instagram, WhatsApp, Maps, Agenda, Gmail, iFood, Nubank, Spotify, Calendário, Mercado Pago, Uber) | Apple (API pública de busca) | das empresas: **só referência** | ~90 MB |
| aparelhos | iPhone 16 Pro Max, MacBook Pro, iPad Pro, AirPods Pro, Apple Watch (glTF) | Sketchfab (login) | CC-BY 4.0: **creditar** | ~150 MB |
| extras | molduras oficiais da Apple (.dmg → PNG; 7-Zip no Windows) e UI Kit iOS (Figma, pede aceitar a licença) | Apple | **restrita:** molduras só para marketing de apps da App Store; UI Kit só para mockups de software Apple → para filmes de terceiros, só referência | variável |

## Quando perguntar e quando baixar sozinho (decisão do usuário, 28/11/2026)
1. **No início de todo filme**, rode `python scripts/acervo.py status`.
   - exit 0 → o acervo existe: use-o (ver "Como usar").
   - exit 3 → falta algo:
     - **guiado ou híbrido:** inclua na primeira resposta, junto com as outras permissões, a pergunta pronta de
       `python scripts/acervo.py pergunta`. Em essência: *"Para os vídeos ficarem melhores, vale ter um acervo de referências (…).
       Posso acessar o Chrome e baixar tudo?"* Com o sim, rode `acervo.py baixar --sim "<palavras dele>"` e depois os itens de
       `acervo.py chrome` pelo navegador.
     - **autônomo** ("faça tudo", "decide tudo"): **não pergunte, baixe.** O pedido de fazer tudo cobre este acervo grátis e curado,
       inclusive abrir o Chrome para os aparelhos do Sketchfab. Rode `acervo.py baixar --sim "<palavras do pedido>"` e avise numa
       linha ("baixei o acervo de referências: X modelos, Y telas, licenças em acervo.json").
2. A exceção vale **só** para esta lista grátis. Instalar programa (7-Zip, Blender…), pagar, criar conta ou baixar fora da
   lista continua exigindo o sim explícito (`references/relacionamento.md`).
3. Se o usuário recusar, siga sem o acervo e não pergunte de novo no mesmo projeto (registre em `studio-state.json`).

## Como usar
- **Produto ou cenário fotorrealista (Blender):** procure primeiro em `modelos-3d/`; ilumine com um HDRI de `hdris/` (estúdio pequeno
  para produto, `photo_studio_loft_hall` para ambiente quente); superfícies com `materiais/`.
- **Celular em cena:** moldura real a partir de um modelo de `modelos-3d/sketchfab/` com `scripts/blender/device_front.py`
  (ver `references/dom-pipeline.md` § Cantos).
- **Tela de app (perfil, conversa, agenda, delivery):** abra as capturas de `telas-padrao/` e copie o *layout* (ordem, proporções,
  modo escuro, tamanhos relativos). Desenhe uma interface genérica, **sem logo nem nome do app**. A Meta exige aprovação para
  mostrar a interface do Instagram em comercial.
- **Telas do sistema iOS** (tela bloqueada, notificação, teclado, alerta, compartilhar): `telas-padrao/ios-27/`. Se faltar e o
  MCP do Figma estiver conectado, duplique o *iOS and iPadOS UI Kit* da Apple (aceitar a licença é decisão do usuário) e exporte os
  nós da página **Examples** com `download_assets` (`defaultScale: 3`).
- **Créditos:** todo CC-BY usado vai para o `CREDITOS.txt` do filme (autor + link, estão no `license.txt` de cada modelo).
  CC0 não exige, mas registre a fonte.
