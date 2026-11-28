# Renderiza a FRENTE do iPhone (modelo FBX enviado pelo usuário) em ortográfica, fundo transparente:
#   cena/img/iphone-frente.png  — aparelho com a tela vazada (holdout): o DOM desenha a interface por baixo
#   cena/img/iphone-mascara.png — só a forma da tela (branco), para recortar a interface com mask-image
# Uso: blender -b --factory-startup -P device_front.py -- <modelo.fbx> <pasta de saída> [largura px] [nome do material da tela]
import bpy, mathutils, math, os
import sys
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FBX = os.path.abspath(A[0]) if A else os.path.abspath("material/iphone/source/iPhone 16 Pro Max_upload.fbx")
OUT = os.path.abspath(A[1]) if len(A) > 1 else os.path.abspath("cena/img"); W = int(A[2]) if len(A) > 2 else 1240
SCREEN = A[3] if len(A) > 3 else "screen"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
sc = bpy.context.scene
# ilha dinâmica, vidro e faixas de antena: preto brilhante (o vidro do FBX estoura em branco com fundo transparente)
for m in bpy.data.materials:
    if any(k in m.name for k in ('metalframe', 'screen', 'metaL')) or not m.use_nodes: continue
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not b: continue
    b.inputs['Base Color'].default_value = (0.012, 0.012, 0.013, 1); b.inputs['Metallic'].default_value = 0
    b.inputs['Roughness'].default_value = 0.28; b.inputs['Alpha'].default_value = 1
    for k in ('Transmission Weight', 'Transmission'):
        if k in b.inputs: b.inputs[k].default_value = 0
    for l in list(m.node_tree.links):
        if l.to_node == b and l.to_socket.name == 'Base Color': m.node_tree.links.remove(l)
mins = mathutils.Vector((9, 9, 9)); maxs = mathutils.Vector((-9, -9, -9))
for o in sc.objects:
    if o.type == 'MESH':
        for c in o.bound_box:
            v = o.matrix_world @ mathutils.Vector(c); mins = mathutils.Vector(map(min, mins, v)); maxs = mathutils.Vector(map(max, maxs, v))
cy, cz = (mins.y + maxs.y) / 2, (mins.z + maxs.z) / 2
hy, hz = maxs.y - mins.y, maxs.z - mins.z
pad = 1.012
H = round(W * hz / hy)
sc.render.resolution_x, sc.render.resolution_y = W, H
# câmera de frente (lado -x), ortográfica, "para cima" = +z
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = hz * pad
cam.location = (mins.x - 2, cy, cz); cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
# luz: chave grande em cima à esquerda + recorte suave do lado direito (titânio pega brilho na borda)
def area(name, loc, rot, size, energy, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = energy; l.color = color
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
area('key', (mins.x - 1.5, cy + 1.2, cz + 1.6), (math.radians(40), math.radians(-35), math.radians(-60)), 2.5, 220)
area('rim', (mins.x - 0.6, cy - 1.4, cz - 0.4), (math.radians(90), 0, math.radians(-140)), 1.5, 90, (1, .93, .86))
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.02, 0.02, 1); world.node_tree.nodes['Background'].inputs[1].default_value = 0.6
sc.render.engine = 'CYCLES'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e: print('GPU?', e)
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
scr = next(m for m in bpy.data.materials if SCREEN in m.name.lower())
# 1) aparelho com a tela vazada
hold = bpy.data.materials.new('holdout'); hold.use_nodes = True; nt = hold.node_tree; nt.nodes.clear()
o = nt.nodes.new('ShaderNodeOutputMaterial'); h = nt.nodes.new('ShaderNodeHoldout'); nt.links.new(h.outputs[0], o.inputs[0])
for ob in sc.objects:
    if ob.type == 'MESH':
        for i, m in enumerate(ob.data.materials):
            if m == scr: ob.data.materials[i] = hold
sc.render.filepath = os.path.join(OUT, 'iphone-frente.png'); bpy.ops.render.render(write_still=True)
# 2) máscara da tela: tudo holdout menos a tela, que vira emissão branca
white = bpy.data.materials.new('white'); white.use_nodes = True; nt = white.node_tree; nt.nodes.clear()
o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); e.inputs[1].default_value = 1; nt.links.new(e.outputs[0], o.inputs[0])
for ob in sc.objects:
    if ob.type == 'MESH':
        for i, m in enumerate(ob.data.materials): ob.data.materials[i] = white if m == hold else hold
sc.cycles.samples = 8; sc.cycles.use_denoising = False
sc.render.filepath = os.path.join(OUT, 'iphone-mascara.png'); bpy.ops.render.render(write_still=True)
print('OK', W, H)
