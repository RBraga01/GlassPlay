#!/usr/bin/env python3
"""Render private Nevermore editorial art in Blender from hash-pinned frames.

Normal Python extracts original plates, runs Blender and encodes delivery WebP.
Blender renders the composition, atmosphere, typography and all visual effects.
OpenCV only decodes/crops/derives an exterior matte. Pillow only encodes/resizes.
This command never changes video, audio, runtime files, or public/.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".private/art-source/nevermore"
MEDIA = ROOT / ".private/media/nevermore"
BLENDER_DEFAULT = os.environ.get("BLENDER", "blender")
VERSION = "2026-10-22-blender-editorial-v1"
FRAMES = {"raven": 57, "host": 15, "bride": 39}
PUBLIC_CHARACTER_CREDIT = "Nevermore's character artwork was developed using 3D assets created with Meshy and animated for this project. Only finished rendered visuals are presented; original source models are not distributed."


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_preparer():
    spec = importlib.util.spec_from_file_location("nevermore_prepare", ROOT / "scripts/prepare-media.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def extract_plates(source, prep):
    import cv2
    import numpy as np
    records = []
    for name, frame_index in FRAMES.items():
        relative, expected = prep.SOURCES[name]
        source_path = source / relative
        if sha(source_path) != expected:
            raise RuntimeError(f"Approved source mismatch: {relative}")
        cap = cv2.VideoCapture(str(source_path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, bgr = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError(f"Cannot decode {name} frame {frame_index}")
        # Fill only the outer silhouette: dark fabric and feathers remain opaque.
        bright = bgr.max(axis=2)
        mask = (bright > 9).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        alpha = np.zeros_like(mask)
        contours = [c for c in contours if cv2.contourArea(c) > 3]
        cv2.drawContours(alpha, contours, -1, 255, cv2.FILLED)
        # Soft exterior edge reduces black video fringe without changing RGB.
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        ys, xs = np.where(alpha > 0)
        x0, x1 = max(0, xs.min()-3), min(bgr.shape[1], xs.max()+4)
        y0, y1 = max(0, ys.min()-3), min(bgr.shape[0], ys.max()+4)
        rgba = np.dstack([bgr, alpha])[y0:y1, x0:x1]
        output = WORK / f"{name}-frame-{frame_index:03d}.png"
        cv2.imwrite(str(output), rgba)
        records.append({"id": name, "source": relative, "source_sha256": expected,
                        "frame_index": frame_index, "timestamp_s": frame_index/24,
                        "source_dimensions": [int(bgr.shape[1]), int(bgr.shape[0])],
                        "crop_xyxy": [int(x0), int(y0), int(x1), int(y1)],
                        "plate": output.relative_to(ROOT).as_posix(), "plate_sha256": sha(output)})
    return records


def render_blender():
    import bpy
    from mathutils import Vector

    argv = sys.argv[sys.argv.index("--")+1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--variant", default="all")
    opts = parser.parse_args(argv)

    def node(nodes, kind, label=None):
        n = nodes.new(kind)
        if label:
            n.label = label
            n.name = label
        return n

    def emission(name, color, strength=1):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        ns, ls = m.node_tree.nodes, m.node_tree.links
        ns.clear()
        e = node(ns, "ShaderNodeEmission")
        e.inputs[0].default_value = (*color, 1)
        e.inputs[1].default_value = strength
        o = node(ns, "ShaderNodeOutputMaterial")
        ls.new(e.outputs[0], o.inputs[0])
        return m

    def plane(name, x, y, z, width, height, material):
        bpy.ops.mesh.primitive_plane_add(size=2, location=(x, y, z))
        ob = bpy.context.object
        ob.name = name
        ob.scale = (width/2, height/2, 1)
        ob.data.materials.append(material)
        return ob

    def atmospheric_material():
        m = bpy.data.materials.new("Midnight / procedural cloud depth")
        m.use_nodes = True
        ns, ls = m.node_tree.nodes, m.node_tree.links
        ns.clear()
        tex = node(ns, "ShaderNodeTexCoord")
        mapping = node(ns, "ShaderNodeVectorMath")
        mapping.operation = "MULTIPLY"
        mapping.inputs[1].default_value = (2.1, 0.85, 1)
        ls.new(tex.outputs["UV"], mapping.inputs[0])
        noise = node(ns, "ShaderNodeTexNoise", "Layered night haze")
        noise.inputs["Scale"].default_value = 3.2
        noise.inputs["Detail"].default_value = 5.5
        noise.inputs["Roughness"].default_value = 0.68
        noise.inputs["Distortion"].default_value = 1.25
        ls.new(mapping.outputs[0], noise.inputs[0])
        ramp = node(ns, "ShaderNodeValToRGB")
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
        for pos, color in [(0.15, (0.0006,0.0012,0.003)), (0.46,(0.002,0.005,0.014)), (0.65,(0.009,0.022,0.056)), (0.83,(0.021,0.043,0.095))]:
            el = ramp.color_ramp.elements[0] if pos == 0.15 else ramp.color_ramp.elements.new(pos)
            el.position = pos
            el.color = (*color, 1)
        ls.new(noise.outputs["Fac"], ramp.inputs[0])
        sep = node(ns, "ShaderNodeSeparateXYZ")
        ls.new(tex.outputs["UV"], sep.inputs[0])
        mask = node(ns, "ShaderNodeMapRange")
        mask.clamp = True
        mask.inputs["From Min"].default_value = .20
        mask.inputs["From Max"].default_value = .68
        mask.inputs["To Min"].default_value = .12
        mask.inputs["To Max"].default_value = 1
        ls.new(sep.outputs["X"], mask.inputs["Value"])
        mult = node(ns, "ShaderNodeMixRGB")
        mult.blend_type = "MULTIPLY"
        mult.inputs[0].default_value = 1
        ls.new(ramp.outputs[0], mult.inputs[1])
        ls.new(mask.outputs[0], mult.inputs[2])
        e = node(ns, "ShaderNodeEmission")
        ls.new(mult.outputs[0], e.inputs[0])
        out = node(ns, "ShaderNodeOutputMaterial")
        ls.new(e.outputs[0], out.inputs[0])
        return m

    def radial_material(name, color, opacity):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.surface_render_method = 'DITHERED'
        ns, ls = m.node_tree.nodes, m.node_tree.links
        ns.clear()
        tex = node(ns, "ShaderNodeTexCoord")
        dist = node(ns, "ShaderNodeVectorMath")
        dist.operation = "DISTANCE"
        dist.inputs[1].default_value = (.5,.5,0)
        ls.new(tex.outputs["UV"], dist.inputs[0])
        ramp = node(ns, "ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = .03
        ramp.color_ramp.elements[0].color = (opacity,)*3+(1,)
        ramp.color_ramp.elements[1].position = .5
        ramp.color_ramp.elements[1].color = (0,0,0,1)
        ramp.color_ramp.interpolation = "EASE"
        ls.new(dist.outputs["Value"], ramp.inputs[0])
        e = node(ns, "ShaderNodeEmission")
        e.inputs[0].default_value = (*color, 1)
        transparent = node(ns, "ShaderNodeBsdfTransparent")
        mix = node(ns, "ShaderNodeMixShader")
        ls.new(ramp.outputs[0], mix.inputs[0])
        ls.new(transparent.outputs[0], mix.inputs[1])
        ls.new(e.outputs[0], mix.inputs[2])
        out = node(ns, "ShaderNodeOutputMaterial")
        ls.new(mix.outputs[0], out.inputs[0])
        return m

    def character(name, x, y, height, z, tint, exposure=1):
        p = WORK / f"{name}-frame-{FRAMES[name]:03d}.png"
        im = bpy.data.images.load(str(p), check_existing=True)
        im.alpha_mode = "STRAIGHT"
        m = bpy.data.materials.new(name + " / approved frame / gentle cool editorial response")
        m.use_nodes = True
        m.surface_render_method = 'DITHERED'
        ns, ls = m.node_tree.nodes, m.node_tree.links
        ns.clear()
        image = node(ns, "ShaderNodeTexImage")
        image.image = im
        image.interpolation = 'Cubic'
        grade = node(ns, "ShaderNodeMixRGB")
        grade.blend_type = 'MULTIPLY'
        grade.inputs[0].default_value = 1
        grade.inputs[2].default_value = (*tint,1)
        ls.new(image.outputs['Color'],grade.inputs[1])
        e = node(ns, "ShaderNodeEmission")
        e.inputs[1].default_value = exposure
        ls.new(grade.outputs[0], e.inputs[0])
        trans = node(ns, "ShaderNodeBsdfTransparent")
        mix = node(ns, "ShaderNodeMixShader")
        ls.new(image.outputs['Alpha'],mix.inputs[0])
        ls.new(trans.outputs[0],mix.inputs[1])
        ls.new(e.outputs[0],mix.inputs[2])
        out = node(ns, "ShaderNodeOutputMaterial")
        ls.new(mix.outputs[0],out.inputs[0])
        return plane(name, x,y,z,height*im.size[0]/im.size[1],height,m)

    def bottom_falloff():
        m=bpy.data.materials.new('Lower matte / gradual midnight blend')
        m.use_nodes=True
        m.surface_render_method='DITHERED'
        ns,ls=m.node_tree.nodes,m.node_tree.links
        ns.clear()
        tex=node(ns,'ShaderNodeTexCoord')
        sep=node(ns,'ShaderNodeSeparateXYZ')
        ls.new(tex.outputs['UV'],sep.inputs[0])
        ramp=node(ns,'ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.01
        ramp.color_ramp.elements[0].color=(.96,.96,.96,1)
        ramp.color_ramp.elements[1].position=.19
        ramp.color_ramp.elements[1].color=(0,0,0,1)
        ramp.color_ramp.interpolation='EASE'
        ls.new(sep.outputs['Y'],ramp.inputs[0])
        e=node(ns,'ShaderNodeEmission')
        e.inputs[0].default_value=(.001,.002,.005,1)
        transparent=node(ns,'ShaderNodeBsdfTransparent')
        mix=node(ns,'ShaderNodeMixShader')
        ls.new(ramp.outputs[0],mix.inputs[0])
        ls.new(transparent.outputs[0],mix.inputs[1])
        ls.new(e.outputs[0],mix.inputs[2])
        out=node(ns,'ShaderNodeOutputMaterial')
        ls.new(mix.outputs[0],out.inputs[0])
        return m

    def text(body, x, y, size, material, font, tracking=1, max_width=None):
        data = bpy.data.curves.new(body, 'FONT')
        data.body = body
        data.font = bpy.data.fonts.load(str(Path('C:/Windows/Fonts')/font), check_existing=True)
        data.size = size
        data.space_character = tracking
        data.resolution_u = 16
        ob = bpy.data.objects.new(body, data)
        bpy.context.collection.objects.link(ob)
        ob.location = (x,y,4)
        ob.data.materials.append(material)
        bpy.context.view_layer.update()
        if max_width and ob.dimensions.x > max_width:
            factor=max_width/ob.dimensions.x
            ob.scale = (factor,factor,factor)
        return ob

    variants = ['hero', 'cover', 'poster', 'glassplay-social'] if opts.variant == 'all' else [opts.variant]
    for variant in variants:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_percentage = 100
        width, height = (2400,840) if variant == 'hero' else (1200,630)
        sc.render.resolution_x, sc.render.resolution_y = width,height
        sc.render.image_settings.file_format = 'PNG'
        sc.render.image_settings.color_mode = 'RGB'
        sc.render.image_settings.color_depth = '8'
        sc.render.film_transparent = False
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = 0
        sc.view_settings.gamma = 1
        sc.world = bpy.data.worlds.new('Near black world')
        sc.world.color=(.0001,.0001,.0001)
        bpy.ops.object.camera_add(location=(width/200,height/200,20))
        camera=bpy.context.object
        camera.name='Orthographic editorial camera'
        camera.data.type='ORTHO'
        camera.data.ortho_scale=width/100
        sc.camera=camera
        W,H=width/100,height/100
        plane('Atmosphere',W/2,H/2,-2,W,H,atmospheric_material())
        # Deep blue and violet separation behind the real approved characters.
        plane('Azure haze',W*.71,H*.55,-1,W*.54,H*1.55,radial_material('Azure diffusion',(.011,.033,.078),.70))
        plane('Violet distant haze',W*.94,H*.50,-.9,W*.30,H*1.35,radial_material('Violet diffusion',(.028,.013,.055),.50))
        if variant == 'hero':
            character('bride',22.04,4.17,6.0,0.0,(.58,.64,.90),.68)
            character('host',18.20,4.22,8.25,.8,(.75,.83,1.0),.94)
            character('raven',14.15,3.47,6.25,1.8,(.71,.86,1.1),1.12)
        else:
            character('bride',10.88,3.05,4.5,0.0,(.58,.64,.90),.68)
            character('host',9.00,3.16,6.20,.8,(.75,.83,1.0),.94)
            character('raven',7.00,2.50,4.35,1.8,(.71,.86,1.1),1.12)
        # Fine drifting motes integrate the plate layers; deterministic placement.
        rng = random.Random(42)
        mote=emission('Dust / cold glints',(.18,.29,.48))
        for i in range(49):
            x=rng.uniform(W*.40,W*.98)
            y=rng.uniform(H*.07,H*.95)
            radius=rng.uniform(.002,.010)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=radius,location=(x,y,2.8))
            ob=bpy.context.object
            ob.name=f'Atmospheric mote {i:02d}'
            ob.data.materials.append(mote)
        # Edge falloff integrates bottom cut-offs into the midnight field.
        plane('Foreground midnight falloff',W*.70,-H*.10,3,W*1.4,H*.9,radial_material('Black foreground veil',(.0004,.0007,.002),.96))
        plane('Quiet title field',W*.12,H*.55,3,W*.77,H*1.8,radial_material('Title field',(.0005,.001,.003),.94))
        plane('Lower edge integration',W/2,H/2,3.1,W,H,bottom_falloff())
        silver=emission('Title / silver',(.75,.80,.87))
        soft=emission('Subtitle / cool grey',(.34,.42,.54))
        blue=emission('Eyebrow / pale blue',(.25,.40,.59))
        if variant == 'hero':
            text('A HALLOWEEN ENCOUNTER',1.04,6.29,.23,blue,'SourceSansPro-Semibold.ttf',1.40)
            text('Nevermore',.94,4.10,1.90,silver,'BASKVILL.TTF',1.02,10.15)
            text('An invitation after dark.',1.04,3.17,.40,soft,'SourceSansPro-Light.ttf')
            text('SILENCE   /   PRESENCE   /   ENCOUNTER',1.06,1.33,.20,blue,'SourceSansPro-Regular.ttf',1.22)
            plane('Title rule',1.42,2.43,4,.74,.012,blue)
        elif variant in ['poster','glassplay-social']:
            if variant == 'glassplay-social':
                text('GlassPlay',.57,5.48,.25,silver,'SourceSansPro-Semibold.ttf',1.1)
            else:
                text('A HALLOWEEN ENCOUNTER',.57,5.48,.12,blue,'SourceSansPro-Semibold.ttf',1.32)
            text('Nevermore',.52,3.44,1.01,silver,'BASKVILL.TTF',1.02,5.25)
            text('An invitation after dark.',.58,2.87,.23,soft,'SourceSansPro-Light.ttf')
            text('FOR AR SMART GLASSES',.58,.61,.115,blue,'SourceSansPro-Regular.ttf',1.25)
            plane('Title rule',.78,2.38,4,.40,.009,blue)
        sc['editorial_version']=VERSION
        sc['approved_input_frames']=json.dumps(FRAMES)
        sc['publication_status']='PRIVATE_REVIEW_ONLY / owner visual review pending'
        sc['note']='Editorial composite of approved runtime plates. No simultaneous gameplay or device imagery.'
        # Images are packed for private source portability. Fonts remain system refs.
        for im in bpy.data.images:
            if im.source == 'FILE':
                im.pack()
        sc.render.filepath=str(WORK/f'{variant}.png')
        bpy.ops.wm.save_as_mainfile(filepath=str(WORK/f'{variant}.blend'))
        bpy.ops.render.render(write_still=True)


def encode_outputs():
    from PIL import Image
    for name in ['cover','poster','glassplay-social']:
        with Image.open(WORK/f'{name}.png') as im:
            im.save(MEDIA/f'{name}.webp',quality=92,method=6)
            im.resize((640,336),Image.Resampling.LANCZOS).save(MEDIA/f'{name}-small.webp',quality=88,method=6)
    hero=ROOT/'docs/assets/nevermore-hero.webp'
    hero.parent.mkdir(parents=True,exist_ok=True)
    with Image.open(WORK/'hero.png') as im:
        im.save(hero,quality=92,method=6)
    shutil.copyfile(hero,ROOT/'experiences/nevermore/cover.webp')


def finalize_manifest(prep, provenance):
    from PIL import Image
    manifest_path=ROOT/'docs/media/manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    credits=MEDIA/'CREDITS.txt'
    credit_text=credits.read_text(encoding='utf-8')
    credit_text=credit_text.replace('Runtime art: approved Nevermore production assets; Meshy-derived models, USER-ATTESTED-MESHY-PAID-ACCOUNT.',PUBLIC_CHARACTER_CREDIT)
    credits.write_text(credit_text,encoding='utf-8')
    for item in manifest['outputs']:
        p=MEDIA/item['file']
        item.update(bytes=p.stat().st_size,sha256=sha(p))
        if p.suffix=='.webp':
            with Image.open(p) as im:
                item.update(width=im.width,height=im.height)
    manifest['assets']=[{'path':item['file'],'sha256':item['sha256'],'bytes':item['bytes']} for item in manifest['outputs']]
    manifest['bundle']=prep.build_bundle()
    manifest['cover']={'file':'cover.webp','type':'blender_editorial_composite_of_runtime_frames',
                       'sources':list(FRAMES),'description':'Azure Night raven in foreground, Midnight Host at portrait scale, distant Bride; Blender-rendered night atmosphere and layered depth. Editorial art, not simultaneous gameplay.'}
    manifest['editorial_art']=provenance
    rules=manifest['editorial_rules']
    rules[:]=[r for r in rules if not r.startswith('Black-margin crop')]
    rules.insert(2,'Gallery stills retain their original crop and colors. Cover, poster, social and README art use Blender with approved frame plates, exterior alpha mattes, gentle cool grading, procedural atmosphere and rendered typography; no pose or model replacement.')
    manifest['promo_edit'][-1]['note']='The existing promo video retains its original end card; the replacement poster is not retroactively present in the video.'
    data=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    manifest_path.write_text(data,encoding='utf-8')
    (MEDIA/'review-manifest.json').write_text(data,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True,help='Nevermore checkout')
    parser.add_argument('--blender',default=BLENDER_DEFAULT)
    parser.add_argument('--finalize-only',action='store_true')
    parser.add_argument('--variant',default='all')
    args=parser.parse_args()
    prep=load_preparer()
    if subprocess.run(['git','check-ignore','--quiet',str(WORK)],cwd=ROOT).returncode:
        raise RuntimeError('Private art source must be Git ignored')
    WORK.mkdir(parents=True,exist_ok=True)
    before={name:sha(MEDIA/name) for name in ['promo.mp4','teaser.mp4']}
    provenance_path=WORK/'provenance.json'
    if not args.finalize_only:
        plates=extract_plates(args.source.resolve(),prep)
        provenance={'version':VERSION,'renderer':'Blender 5.2.2 LTS / EEVEE','script':'scripts/art/nevermore_art.py',
                    'source_revision':prep.SOURCE_REVISION,'plates':plates,'composition_review':'Pending owner visual approval',
                    'private_source_directory':WORK.relative_to(ROOT).as_posix(),
                    'operations':['Source MP4 decode at exact approved frame','Exterior matte and proportional plate scaling','Blender scene planes with mild cool response','Procedural midnight atmosphere, depth overlap, motes and edge falloff','Blender font geometry','WebP delivery encoding and responsive resize'],
                    'font_dependencies':['C:/Windows/Fonts/BASKVILL.TTF','C:/Windows/Fonts/SourceSansPro-Light.ttf','C:/Windows/Fonts/SourceSansPro-Regular.ttf','C:/Windows/Fonts/SourceSansPro-Semibold.ttf'],
                    'publication':'Private repository owner review only. Public media approval remains false.'}
        provenance_path.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
        subprocess.run([args.blender,'-b','--factory-startup','--python',str(Path(__file__).resolve()),'--','--render','--variant',args.variant],check=True)
    provenance=json.loads(provenance_path.read_text(encoding='utf-8'))
    provenance['script_sha256']=sha(Path(__file__))
    encode_outputs()
    provenance['deliverables']=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [ROOT/'docs/assets/nevermore-hero.webp',ROOT/'experiences/nevermore/cover.webp']]
    provenance['render_sources']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted(WORK.glob('*.blend'))]
    provenance['native_plate_resolution_note']='All selected source video frames are 640 x 640. Cropped characters are proportionally enlarged in the 2400 x 840 README art; this is editorial upscaling, not new source detail.'
    provenance_path.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    finalize_manifest(prep,provenance)
    after={name:sha(MEDIA/name) for name in before}
    if before!=after:
        raise RuntimeError('Unexpected video mutation')
    print(json.dumps({'deliverables':provenance['deliverables'],'videos_unchanged':before,'bundle':json.loads((ROOT/'docs/media/manifest.json').read_text())['bundle']},indent=2))


if __name__=='__main__':
    if '--render' in sys.argv:
        render_blender()
    else:
        main()
