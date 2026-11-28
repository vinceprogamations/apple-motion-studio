# Logo e ícones do README do Apple Motion Studio: squircle com gradiente vivo + símbolo em vidro líquido (Cycles).
# Desenho próprio (nada de SF Symbols ou logo da Apple). Uso:
#   blender -b --python-exit-code 1 -P icones.py -- <saida_dir> <amostras> [nome ...]
import bpy, bmesh, math, os, sys
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]; OUT = os.path.abspath(a[0]); SAMPLES = int(a[1]); ONLY = set(a[2:])

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.engine = 'CYCLES'
    pr = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            pr.compute_device_type = kind; pr.get_devices(); ds = [d for d in pr.devices if d.type == kind]
            if ds:
                for d in pr.devices: d.use = d.type == kind
                sc.cycles.device = 'GPU'; break
        except Exception: pass
    sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 16; sc.cycles.transmission_bounces = 16; sc.cycles.glossy_bounces = 8
    sc.cycles.caustics_refractive = True; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
    try: sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -1.1
    except Exception: pass
    sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True; nt = sc.world.node_tree; bg = nt.nodes['Background']
    gr = nt.nodes.new('ShaderNodeTexGradient'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); cr = nt.nodes.new('ShaderNodeValToRGB')
    mp.inputs['Rotation'].default_value[1] = math.radians(90); cr.color_ramp.elements[0].color = (0.02, 0.02, 0.03, 1); cr.color_ramp.elements[1].color = (0.9, 0.92, 1.0, 1)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.35
    return sc

def link(o): bpy.context.scene.collection.objects.link(o); return o
def P(m): return m.node_tree.nodes['Principled BSDF']
def glass(name='vidro', tint=(0.97, 0.98, 1.0)):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = P(m)
    p.inputs['Base Color'].default_value = (*tint, 1); p.inputs['Transmission Weight'].default_value = 0.92; p.inputs['Roughness'].default_value = 0.08; p.inputs['IOR'].default_value = 1.45
    for k, v in (('Thin Film Thickness', 380.0), ('Thin Film IOR', 1.4), ('Coat Weight', 0.3)):
        try: p.inputs[k].default_value = v
        except Exception: pass
    try: p.inputs['Dispersion'].default_value = 0.4   # Blender 4.2+: arco-íris nas bordas
    except Exception: pass
    return m
def pearl():
    m = bpy.data.materials.new('perola'); m.use_nodes = True; p = P(m); p.inputs['Base Color'].default_value = (1, 1, 1, 1); p.inputs['Roughness'].default_value = 0.15
    p.inputs['Coat Weight'].default_value = 1.0; p.inputs['Emission Color'].default_value = (1, 1, 1, 1); p.inputs['Emission Strength'].default_value = 0.5
    return m
def gradient(name, cols):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = P(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); gr = nt.nodes.new('ShaderNodeTexGradient'); cr = nt.nodes.new('ShaderNodeValToRGB')
    mp.inputs['Rotation'].default_value[2] = math.radians(-45); mp.inputs['Location'].default_value = (0.0, 0.5, 0)
    e = cr.color_ramp.elements; e[0].color = (*cols[0], 1); e[1].color = (*cols[-1], 1)
    for i, c in enumerate(cols[1:-1]): x = e.new((i + 1) / (len(cols) - 1)); x.color = (*c, 1)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], p.inputs['Base Color']); nt.links.new(cr.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = 0.7; p.inputs['Roughness'].default_value = 0.55; p.inputs['Coat Weight'].default_value = 0.6; p.inputs['Coat Roughness'].default_value = 0.12
    return m

def squircle(mat, s=2.0, n=5.0, depth=0.16):   # superelipse (forma de ícone de app)
    bm = bmesh.new(); pts = []
    for i in range(256):
        t = 2 * math.pi * i / 256; c, sn = math.cos(t), math.sin(t)
        pts.append((s / 2 * math.copysign(abs(c) ** (2 / n), c), s / 2 * math.copysign(abs(sn) ** (2 / n), sn)))
    f = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts]); bmesh.ops.triangulate(bm, faces=[f])
    me = bpy.data.meshes.new('sq'); bm.to_mesh(me); bm.free(); o = link(bpy.data.objects.new('sq', me)); o.data.materials.append(mat)
    so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = depth; so.offset = -1; bv = o.modifiers.new('b', 'BEVEL'); bv.width = 0.05; bv.segments = 8; bv.limit_method = 'ANGLE'
    for pl in o.data.polygons: pl.use_smooth = True
    return o
def tube(name, pts, r, mat, z=0.22):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 10; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts): sp.points[i].co = (x, y, z, 1)
    o = link(bpy.data.objects.new(name, cu)); o.data.materials.append(mat); return o
def sphere(name, loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=64, ring_count=32); o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
    for pl in o.data.polygons: pl.use_smooth = True
    return o
def rbox(name, loc, size, mat, bev=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size; bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat); b = o.modifiers.new('b', 'BEVEL'); b.width = bev; b.segments = 8
    for pl in o.data.polygons: pl.use_smooth = True
    return o
def lights():
    def area(loc, size, power, col, target=(0, 0, 0)):
        d = bpy.data.lights.new('l', 'AREA'); d.size = size; d.energy = power; d.color = col; o = link(bpy.data.objects.new('l', d)); o.location = loc
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    area((-2.5, 2.5, 5), 4, 380, (1, 1, 1)); area((3, -2, 2.5), 2, 160, (1.0, 0.55, 0.85)); area((-3, -2.5, 2), 2, 160, (0.45, 0.85, 1.0)); area((0, 3.5, 1.2), 3, 120, (1, 0.9, 0.7))
def camera():
    c = link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))); bpy.context.scene.camera = c; c.data.lens = 85
    eye = Vector((0, -0.7, 5.6)); c.location = eye; c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = (Vector((0, 0, 0.05)) - eye).to_track_quat('-Z', 'Y')
def onda(x0, x1, amp, k, w, n=160):
    return [(x0 + (x1 - x0) * i / (n - 1), amp * math.exp(-k * i / (n - 1)) * math.sin(w * i / (n - 1))) for i in range(n)]

# ---------- símbolos ----------
def s_logo(G):   # mola amortecida que assenta num ponto
    tube('mola', onda(-0.6, 0.34, 0.36, 2.6, 2.75 * math.pi, 220), 0.095, G); sphere('ponto', (0.53, 0, 0.24), 0.13, pearl())
def s_storyboard(G):
    for i, x in enumerate((-0.33, 0.33)): rbox(f'q{i}', (x, 0.08, 0.22), (0.5, 0.78, 0.09), G, 0.07)
    for i in range(6): rbox(f'f{i}', (-0.5 + i * 0.2, -0.52, 0.22), (0.1, 0.06, 0.06), G, 0.025)
def s_animacao(G): tube('onda', onda(-0.62, 0.62, 0.36, 2.0, 4 * math.pi, 240), 0.085, G)
def s_som(G):
    for i, h in enumerate((0.35, 0.7, 1.0, 0.55, 0.85, 0.4, 0.25)): rbox(f'b{i}', (-0.54 + i * 0.18, 0, 0.22), (0.11, h, 0.11), G, 0.05)
def s_portoes(G):   # escudo com check
    pts = []
    for i in range(41): x = -0.4 + 0.8 * i / 40; pts.append((x, 0.36 + 0.07 * math.cos(math.pi * x / 0.8)))   # topo levemente arqueado
    for i in range(1, 31): t = i / 30; pts.append((0.4 - 0.4 * t ** 1.6, 0.36 - 0.88 * (1 - (1 - t) ** 1.2) - 0.0))   # lado direito até a ponta
    for i in range(1, 30): t = i / 30; pts.append((-0.4 * (1 - t) ** 0.62 * 0 - 0.4 * (t ** 0.625), -0.52 + 0.88 * (t ** 1.2)) if False else (-(0.4 - 0.4 * (1 - t) ** 1.6), 0.36 - 0.88 * (1 - t ** 1.2)))
    pts.append(pts[0])
    tube('escudo', pts, 0.06, G); tube('check', [(-0.19, -0.04), (-0.04, -0.19), (0.22, 0.14)], 0.065, G, z=0.24)
def s_autonomia(G):   # interruptor ligado
    tube('pilula', [(math.cos(t) * 0.26 + (0.26 if math.cos(t) > 0 else -0.26) * 0 + (0.26 if math.cos(t) >= 0 else -0.26), math.sin(t) * 0.26) for t in [2 * math.pi * i / 120 for i in range(121)]], 0.055, G)
    sphere('botao', (0.26, 0, 0.24), 0.19, pearl())
def s_revisao(G):   # relógio com +6 quadros
    tube('aro', [(math.cos(t) * 0.5, math.sin(t) * 0.5) for t in [2 * math.pi * i / 120 for i in range(121)]], 0.06, G)
    tube('ponteiro', [(0, 0), (0, 0.32)], 0.05, G, z=0.24); tube('ponteiro2', [(0, 0), (0.22, -0.1)], 0.05, G, z=0.24); sphere('eixo', (0, 0, 0.25), 0.07, pearl())
def s_3d(G):
    o = rbox('cubo', (0, 0, 0), (0.62, 0.62, 0.62), G, 0.05); o.rotation_mode = 'ZXY'; o.rotation_euler = (math.radians(54.74), 0, math.radians(45)); o.location = (0, 0.04, 0.5)
def s_casos(G):
    for i in range(3): rbox(f'c{i}', (-0.12 + i * 0.12, 0.12 - i * 0.12, 0.18 + i * 0.09), (0.7, 0.5, 0.05), G, 0.06)

ICONES = {   # nome: (símbolo, gradiente do squircle)
    'logo':       (s_logo,       [(0.36, 0.25, 1.0), (0.85, 0.2, 0.85), (1.0, 0.36, 0.42), (1.0, 0.65, 0.2)]),
    'storyboard': (s_storyboard, [(1.0, 0.55, 0.15), (1.0, 0.25, 0.45)]),
    'animacao':   (s_animacao,   [(0.2, 0.6, 1.0), (0.35, 0.2, 0.95)]),
    'som':        (s_som,        [(1.0, 0.25, 0.5), (0.65, 0.2, 0.95)]),
    'portoes':    (s_portoes,    [(0.15, 0.85, 0.55), (0.05, 0.55, 0.75)]),
    'autonomia':  (s_autonomia,  [(0.55, 0.35, 1.0), (0.2, 0.45, 1.0)]),
    'revisao':    (s_revisao,    [(1.0, 0.8, 0.15), (1.0, 0.45, 0.1)]),
    'blender':    (s_3d,         [(0.1, 0.75, 0.95), (0.15, 0.4, 0.95)]),
    'casos':      (s_casos,      [(0.95, 0.3, 0.3), (0.95, 0.2, 0.6)]),
}
os.makedirs(OUT, exist_ok=True)
for nome, (sim, cols) in ICONES.items():
    if ONLY and nome not in ONLY: continue
    sc = reset(); sc.render.resolution_x = sc.render.resolution_y = 1024 if nome == 'logo' else 512
    squircle(gradient('g_' + nome, cols)); sim(glass()); lights(); camera()
    sc.render.filepath = os.path.join(OUT, nome + '.png'); bpy.ops.render.render(write_still=True); print('ICONE', nome, flush=True)
