# Cria uma apresentação comercial animada (16:9) num projeto: page.html (carrega o motor templates/dom/apresentacao.js com o
# caminho relativo certo até a skill), slides.js de exemplo e asset-manifest.json vazio. Depois: edite slides.js e renderize.
#   python apresentacao.py init <pasta-da-apresentação>
#   node render_dom.mjs stills <pasta>/page.html <pasta>/review 1 5 9 --root <projeto> --w 1920 --h 1080
#   node render_dom.mjs video  <pasta>/page.html "<pasta>/out/<nome>.mp4" --root <projeto> --w 1920 --h 1080 --fps 30
import os, sys, json
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8')
    except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
PAGE = '''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{titulo}</title></head><body>
<script src="{kit}/templates/motion-core.js"></script>
<script>window.SLIDES_KIT = "{kit}";</script>
<script src="slides.js"></script>
<script src="{kit}/templates/dom/apresentacao.js"></script>
<script src="{kit}/templates/dom/anim.js"></script>
</body></html>
'''
EXEMPLO = '''// Dados da apresentação. Uma ideia por slide; duração em segundos. Revisar = editar aqui e renderizar de novo.
window.SLIDES = {
  kit: window.SLIDES_KIT, fps: 30, tema: { fundo: '#000000', texto: '#ffffff' },
  slides: [
    { tipo: 'capa', dur: 4.5, kicker: 'Proposta', titulo: 'Sua empresa × seu cliente', sub: 'Uma frase que diz o que muda para ele.' },
    { tipo: 'frase', dur: 5, linhas: ['A dor que ele reconhece.', 'Em palavras dele.'] },
    { tipo: 'fluxo', dur: 9, titulo: 'Um pedido, do começo ao fim.', objeto: { id: '#1042', titulo: 'Pedido', linha: 'Descrição curta' },
      perfis: [{ nome: 'Atendimento', tela: 'registra', estado: 'Novo' }, { nome: 'Equipe', tela: 'executa', estado: 'Em andamento' }, { nome: 'Gestão', tela: 'acompanha', estado: 'Concluído' }] },
    { tipo: 'colunas', dur: 7, titulo: 'Quem faz o quê.', colunas: [{ titulo: 'Nós', itens: ['…'] }, { titulo: 'Vocês', itens: ['…'] }], conclusao: 'A consequência para a operação.' },
    { tipo: 'fim', dur: 4.5, logo: 'assets/logo.png', asset: 'logo', frase: 'A assinatura da marca.' }
  ]
};
'''
def main():
    if len(sys.argv) < 3 or sys.argv[1] != 'init': sys.exit(open(__file__, encoding='utf8').read().split('\nimport')[0])
    d = os.path.abspath(sys.argv[2]); os.makedirs(os.path.join(d, 'assets'), exist_ok=True)
    kit = os.path.relpath(SKILL, d).replace(os.sep, '/')
    open(os.path.join(d, 'page.html'), 'w', encoding='utf8').write(PAGE.format(titulo=os.path.basename(d), kit=kit))
    if not os.path.exists(os.path.join(d, 'slides.js')): open(os.path.join(d, 'slides.js'), 'w', encoding='utf8').write(EXEMPLO)
    if not os.path.exists(os.path.join(d, 'asset-manifest.json')): json.dump({'assets': []}, open(os.path.join(d, 'asset-manifest.json'), 'w'))
    print(f'apresentação criada em {d} (kit = {kit}). Edite slides.js; logo e fotos em assets/ + asset-manifest.json.')
if __name__ == '__main__': main()
