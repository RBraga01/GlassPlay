"""Original GlassPlay / Nevermore brand scenes. Blender 5.2, Cycles/OptiX.

Run from the project root:
  blender --background --python scripts/art/render-brand.py -- --scene glasses --mode preview
  blender --background --python scripts/art/render-brand.py -- --scene glasses --mode final
  blender --background --python scripts/art/render-brand.py -- --scene feather --mode final

Geometry, shaders, lights, atmosphere and typography are authored here. There are
no input artwork, hardware models, private Nevermore assets or image textures.
Concept eyewear is not a depiction of a physical Prism product.
"""
import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.private/art-source'
RENDERS = SOURCE / 'renders'
RENDERS.mkdir(parents=True, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--scene', choices=['glasses', 'feather'], default='glasses')
parser.add_argument('--mode', choices=['preview', 'final'], default='preview')
opts = parser.parse_args(args)
random.seed(4317)


def material(name, color, metallic=0, roughness=.3, transmission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Transmission Weight'].default_value = transmission
    p.inputs['IOR'].default_value = 1.46
    return m


def emission(name, color, strength=1):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    shader = n.new('ShaderNodeEmission')
    shader.inputs['Color'].default_value = (*color, 1)
    shader.inputs['Strength'].default_value = strength
    out = n.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(shader.outputs[0], out.inputs['Surface'])
    return m


def mesh(name, vertices, faces, mat, bevel=0):
    d = bpy.data.meshes.new(name)
    d.from_pydata(vertices, [], faces)
    d.update()
    ob = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new('Machined soft edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 4
    for poly in d.polygons:
        poly.use_smooth = True
    return ob


def curve(name, points, mat, radius=.02, radii=None):
    d = bpy.data.curves.new(name, 'CURVE')
    d.dimensions = '3D'
    d.resolution_u = 24
    d.bevel_depth = radius
    d.bevel_resolution = 4
    s = d.splines.new('BEZIER')
    s.bezier_points.add(len(points) - 1)
    for i, (bp, co) in enumerate(zip(s.bezier_points, points)):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
        if radii:
            bp.radius = radii[i]
    ob = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def cube(name, loc, scale, mat, bevel=.08):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new('Soft precision edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 5
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return ob


def aim(ob, point):
    ob.rotation_euler = (Vector(point) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, loc, target, energy, color, size, size_y=None):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy
    d.color = color
    d.shape = 'RECTANGLE'
    d.size = size
    d.size_y = size_y or size
    ob = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    aim(ob, target)
    return ob


def init():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 80 if opts.mode == 'preview' else 192
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 10
    sc.cycles.transmission_bounces = 8
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for dev in prefs.devices:
            dev.use = dev.type == 'OPTIX'
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('GPU unavailable, using CPU:', e)
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = -.55
    sc.render.film_transparent = False
    world = bpy.data.worlds.new('Quiet navy studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.018, .028, .055, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .28
    sc.world = world
    camd = bpy.data.cameras.new('Art direction camera')
    cam = bpy.data.objects.new('Art direction camera', camd)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    camd.type = 'ORTHO'
    camd.lens = 55
    # Curved cyclorama catches the physical area lights, with no bitmap backdrop.
    navy = material('Navy cyclorama', (.0035, .006, .016), .02, .68)
    navy_shader = navy.node_tree.nodes.get('Principled BSDF')
    navy_shader.inputs['Emission Color'].default_value = (.017, .029, .05, 1)
    navy_shader.inputs['Emission Strength'].default_value = .35
    cube('Infinite studio', (0, 3, -2.2), (200, 200, .12), navy)
    return sc, cam


def lens_contour(cx, a, b, n=120):
    result = []
    for i in range(n):
        t = 2 * math.pi * i / n
        # Squared oval with a subtly raised outer brow and soft lower corners.
        ct, st = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(ct) ** .55, ct)
        z = b * math.copysign(abs(st) ** .66, st)
        z += (.04 * x / a) * (1 if cx > 0 else -1)
        gx = cx + x
        result.append((gx, .025 * gx * gx, z))
    return result


def ring(name, cx, mat):
    n = 120
    outer = lens_contour(cx, 1.44, .98, n)
    inner = lens_contour(cx, 1.23, .77, n)
    vertices = []
    for contour, y in [(outer, -.13), (inner, -.13), (outer, .16), (inner, .16)]:
        vertices.extend((x, yy + y, z) for x, yy, z in contour)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [(i, j, n+j, n+i), (2*n+i, 3*n+i, 3*n+j, 2*n+j),
                  (i, 2*n+i, 2*n+j, j), (n+i, n+j, 3*n+j, 3*n+i)]
    return mesh(name, vertices, faces, mat, .045)


def optical_lens(cx, mat):
    contour = lens_contour(cx, 1.253, .789)
    n = len(contour)
    verts = [(cx, -.01 + .025 * cx*cx, 0)]
    verts.extend((x, y + .008, z) for x, y, z in contour)
    verts += [(cx, .065 + .025 * cx*cx, 0)]
    verts.extend((x, y + .075, z) for x, y, z in contour)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [(0, i+1, j+1), (n+1, n+2+j, n+2+i),
                  (i+1, n+2+i, n+2+j, j+1)]
    return mesh('Coated waveguide lens', verts, faces, mat, .009)


def temple(side, frame, metal):
    # Thick optical-computing temple at the hinge, narrowing to an ear rest.
    centers = [(3.02*side,.31,.43), (3.10*side,.72,.43), (3.00*side,1.45,.40),
               (2.81*side,2.32,.31), (2.63*side,3.05,.10), (2.46*side,3.48,-.21)]
    widths = [.27,.26,.22,.16,.14,.115]
    heights = [.47,.48,.41,.29,.23,.19]
    verts=[]
    for (x,y,z), w,h in zip(centers,widths,heights):
        verts += [(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)]
    faces=[(3,2,1,0)]
    for i in range(len(centers)-1):
        for j in range(4):
            faces.append((4*i+j, 4*i+(j+1)%4, 4*(i+1)+(j+1)%4, 4*(i+1)+j))
    faces.append(tuple(range(len(verts)-4,len(verts))))
    mesh('Integrated optical temple', verts, faces, frame, .07)
    cube('Titanium hinge', (side*3.1,.53,.44), (.19,.28,.30), metal, .035)
    curve('Temple top chamfer', [(x+side*.105,y,z+h/2-.035) for (x,y,z),h in zip(centers[:5],heights[:5])], metal, .013)
    # Fine external speaker grille behind the temple; small, plausible detail.
    for i in range(5):
        cube('Recessed speaker slot', (side*3.095, .87+i*.075, .44), (.012,.031,.12), black, .01)


sc, cam = init()
black = material('Optical graphite', (.006, .009, .018), .45, .22)
frame = material('Midnight satin titanium', (.025, .038, .071), .68, .27)
edge = material('Brushed titanium edge', (.14, .20, .31), .85, .25)
lens = material('Blue violet interference coated optics', (.125, .23, .36), .1, .075, .83)
p = lens.node_tree.nodes.get('Principled BSDF')
p.inputs['Coat Weight'].default_value = .42
p.inputs['Coat Roughness'].default_value = .08
p.inputs['Thin Film Thickness'].default_value = 380
p.inputs['Thin Film IOR'].default_value = 1.36
white = emission('Quiet ivory typography', (.86, .91, 1.0), 3.3)
muted = emission('Blue grey typography', (.44, .55, .72), 1.7)
violet_type = emission('Soft lavender typography', (.55, .51, .86), 1.65)
TEXT = []


def type_line(body, x, y, size, mat=white, font='Manrope-Regular', spacing=1):
    d = bpy.data.curves.new('Text: '+body, 'FONT')
    d.body = body
    d.size = size
    d.space_character = spacing
    d.font = bpy.data.fonts.load(str(SOURCE/'fonts'/f'{font}.ttf'))
    d.extrude = 0
    ob = bpy.data.objects.new('Text: '+body, d)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob.parent = cam
    ob.location = (x,y,-7)
    ob.rotation_euler = (0,0,0)
    TEXT.append(ob)
    return ob


def clear_text():
    for ob in TEXT:
        bpy.data.objects.remove(ob, do_unlink=True)
    TEXT.clear()


def render(name, w,h, scale, loc, target, shift=0):
    sc.render.resolution_x=w
    sc.render.resolution_y=h
    sc.render.resolution_percentage=100
    cam.location=loc
    aim(cam,target)
    cam.data.ortho_scale=scale
    cam.data.shift_x=shift
    sc.render.filepath=str(RENDERS/f'{name}.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{opts.scene}-{name}.blend'))
    bpy.ops.render.render(write_still=True)


def glasses():
    for cx in [-1.55,1.55]:
        ring('Sculpted optical frame',cx,frame)
        optical_lens(cx,lens)
        # A genuinely inset lens border, catching a soft cool edge reflection.
        contour=lens_contour(cx,1.265,.80)
        curve('Polished lens seat',[(x,y-.083,z) for x,y,z in contour[::3]+contour[:1]],edge,.013)
    curve('Sculpted bridge', [(-.31,.02,.36),(0,-.05,.50),(.31,.02,.36)], frame,.115)
    # Nose rests sit behind the lenses, completing an identifiable eyewear object.
    for side in [-1,1]:
        temple(side,frame,edge)
        curve('Nose support',[(side*.36,.12,-.08),(side*.32,.33,-.19)], edge,.032)
        ob=cube('Soft nose pad',(side*.32,.39,-.22),(.16,.13,.34),black,.065)
        ob.rotation_euler[1]=side*-.2
        # Flush sensor modules on both frame ends.
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.095 if side<0 else .065, depth=.05,
                                           location=(side*2.92,.025*2.92**2-.155,.50),rotation=(math.pi/2,0,0))
        sensor=bpy.context.object
        sensor.name='Flush optical sensor'
        sensor.data.materials.append(black)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.052 if side<0 else .028,
                                            location=(side*2.92,.025*2.92**2-.188,.50))
        ob=bpy.context.object
        ob.name='Sapphire sensor glass'
        ob.scale=(1,.30,1)
        ob.data.materials.append(lens)
    led=emission('Soft blue status light',(.16,.36,1),1.5)
    curve('Status indicator',[(2.72,.027,-.01),(2.78,.027,-.01)],led,.012)
    area('Pearl key softbox',(-3,-4,7),(0,0,0),1100,(.67,.79,1),5,2.5)
    area('Blue side separation',(4,2,4),(0,0,.2),1500,(.20,.37,1),4,1.3)
    area('Violet rim',(-4,4,2.3),(0,0,0),1000,(.38,.21,1),4,1.1)
    area('Optical reflection strip',(-1,-4,2.6),(0,0,.1),700,(.72,.84,1),5,.38)
    area('Foreground fill',(0,-5,1),(0,0,0),130,(.25,.42,.73),4,3)
    area('Violet ground pool',(5,5,4),(2,3,-2.2),300,(.31,.12,.65),5)
    if opts.mode=='preview':
        render('glasses-preview',1200,825,9.1,(7,-12,5.7),(0,.9,-.15))
        return
    # The clean site plate leaves room on its left for the responsive text overlay.
    render('glassplay-hero',1600,1100,9.1,(7,-12,5.7),(0,.9,-.15),-.08)
    clear_text()
    type_line('AR SMART GLASSES EXPERIENCES',-10.2,2.12,.27,violet_type,spacing=1.18)
    type_line('GlassPlay',-10.25,.30,1.53,white,'Manrope-Semibold')
    type_line('A little magic, right before your eyes.',-10.16,-.75,.43,muted)
    render('glassplay-banner',2400,720,24,(7,-12,5.7),(-3.8,-.7,-.15))
    clear_text()
    type_line('GlassPlay',-7.25,3.15,.52,white,'Manrope-Semibold')
    type_line('A little magic,',-7.3,1.5,.78,white,'Manrope-Semibold')
    type_line('right before',-7.3,.48,.78,white,'Manrope-Semibold')
    type_line('your eyes.',-7.3,-.54,.78,white,'Manrope-Semibold')
    type_line('Interactive experiences for AR smart glasses.',-7.25,-3.2,.26,muted)
    render('glassplay-social',1200,630,16.5,(7,-12,5.7),(-2.4,-.7,-.1))
    clear_text()
    render('glassplay-icon',512,512,7.7,(.2,-14,3),(0,.5,0))


def feather():
    # Original mesh/ribbon feather; all barbs and fine barbules are procedural geometry.
    feather_mats=[]
    for i in range(6):
        m=material('Iridescent raven vane '+str(i),(.012+i*.003,.020+i*.004,.046+i*.008),.40,.38+i*.018)
        p=m.node_tree.nodes.get('Principled BSDF')
        p.inputs['Coat Weight'].default_value=.27
        p.inputs['Thin Film Thickness'].default_value=310+i*17
        p.inputs['Thin Film IOR'].default_value=1.32
        feather_mats.append(m)
    shaftmat=material('Polished graphite rachis',(.065,.09,.16),.65,.26)
    root=bpy.data.objects.new('Original raven feather',None)
    bpy.context.collection.objects.link(root)
    before=set(bpy.data.objects)
    def center(t):
        return Vector((.16*math.sin(t*2.4)+.16*t*t, .12*math.sin(t*2.8), -2.5+6.9*t))
    shaft=[center(t) for t in [0,.08,.23,.43,.63,.83,1]]
    curve('Central feather shaft',shaft,shaftmat,.048,[.8,1.2,1,.83,.62,.35,.025])
    # 372 individually profiled, tapering vane barbs, with natural tiny separations.
    for side in [-1,1]:
        for i in range(186):
            t=.13+.868*i/185
            width=(math.sin(math.pi*(t-.10)/.90)**.64)*1.17*(1 if side<0 else .76)
            if .44<t<.455 or .71<t<.718:
                width*=.91
            width*=1+random.uniform(-.035,.035)
            start=center(t)
            advance=.63*(1-t)**.62*(1+random.uniform(-.025,.025))
            pts=[]
            for k in range(7):
                u=k/6
                p=start+Vector((side*width*u,-.11*math.sin(math.pi*u)+.07*u*u,advance*u+.1*math.sin(u*math.pi)))
                pts.append(p)
            verts=[]
            strip=.026*(1-.3*t)
            for k,p in enumerate(pts):
                tap=1-.75*(k/6)**2
                verts.extend([p+Vector((0,0,-strip*tap)),p+Vector((0,0,strip*tap))])
            faces=[(2*k,2*k+1,2*k+3,2*k+2) for k in range(6)]
            ob=mesh('Satin feather barb',verts,faces,feather_mats[(i+side)%6])
            mod=ob.modifiers.new('Vane thickness','SOLIDIFY');mod.thickness=.003
            # Delicate ridge traces carry a fine directional highlight.
            curve('Fine vane ridge',pts,feather_mats[(i+2)%6],.0055,[.7,1,1,.9,.7,.45,.04])
            if i%5==0:
                for k in range(2,6):
                    p=pts[k]
                    curve('Interlocking barbule',[p,p+Vector((side*.045,-.007,.055)),p+Vector((side*.075,-.005,.09))],feather_mats[i%6],.0025,[1,.6,.05])
    # Wispy down at the calamus, less regular than the flight vane.
    for i in range(28):
        t=random.uniform(.1,.23); side=random.choice([-1,1]);p=center(t)
        span=random.uniform(.18,.55)
        curve('Downy basal filament',[p,p+Vector((side*span*.35,-.04,.16)),p+Vector((side*span,-.1,.2)),p+Vector((side*span*1.1,-.04,.1))],feather_mats[i%6],.005,[1,.8,.5,.01])
    for ob in set(bpy.data.objects)-before:
        ob.parent=root
    root.rotation_euler=(math.radians(9),math.radians(32),math.radians(-7))
    root.location=(.5,.2,-.2)
    # Soft, out-of-focus dust adds depth without any Halloween source models.
    dustmat=material('Cool atmospheric motes',(.25,.31,.53),.3,.5)
    for i in range(22):
        loc=(random.uniform(-5,5),random.uniform(.8,5),random.uniform(-1.4,5))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=random.uniform(.006,.018),location=loc)
        bpy.context.object.name='Atmospheric mote'
        bpy.context.object.data.materials.append(dustmat)
    area('Feather cool key',(-3,-4,6),(0,0,0),1100,(.35,.51,1),4,2)
    area('Feather violet rim',(4,3,5),(0,0,1),2100,(.48,.24,1),4,2)
    area('Feather long pearl reflection',(-1,-3,4),(0,0,1),900,(.7,.8,1),.7,6)
    area('Feather blue side',(4,-1,1),(0,0,0),500,(.17,.29,.8),3,2)
    area('Atmospheric violet pool',(3,4,4),(3,4,-2),1000,(.32,.12,.62),6)
    if opts.mode=='preview':
        render('feather-preview',1200,750,10,(0,-13,5.4),(0,.2,.8))
        return
    render('nevermore-poster',1600,1000,10,(0,-13,5.4),(0,.2,.8))
    type_line('GlassPlay',-7.2,3.05,.48,white,'Manrope-Semibold')
    type_line('Nevermore',-7.3,.92,1.50,white,'Newsreader-Medium')
    type_line('Halloween comes',-7.2,-.3,.43,muted)
    type_line('looking for you.',-7.2,-.92,.43,muted)
    type_line('An experience for AR smart glasses.',-7.2,-3.12,.27,muted)
    render('nevermore-social',1200,630,16.5,(0,-13,5.4),(-2.8,.2,.8))


glasses() if opts.scene=='glasses' else feather()
print('Finished original '+opts.scene+' '+opts.mode+' art in '+str(RENDERS))
