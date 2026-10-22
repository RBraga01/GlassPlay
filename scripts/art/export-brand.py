"""Export actual Blender PNG renders and record provenance. No drawing operations."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.private/art-source'
RENDERS = SOURCE / 'renders'
OUT = ROOT / 'public/brand'
OUT.mkdir(parents=True, exist_ok=True)

exports = [
    ('glassplay-banner.png', 'docs/assets/glassplay-hero.webp', (2400, 720)),
    ('glassplay-hero.png', 'public/brand/glassplay-hero.webp', (1600, 1100)),
    ('glassplay-hero.png', 'public/brand/glassplay-hero-small.webp', (800, 550)),
    ('glassplay-social.png', 'public/brand/glassplay-social.png', (1200, 630)),
    ('glassplay-icon.png', 'public/brand/glassplay-icon.png', (512, 512)),
    ('glassplay-icon.png', 'public/brand/favicon.png', (64, 64)),
    ('glassplay-icon.png', 'public/brand/apple-touch-icon.png', (180, 180)),
    ('nevermore-poster.png', 'public/brand/nevermore-poster.webp', (1600, 1000)),
    ('nevermore-poster.png', 'public/brand/nevermore-poster-small.webp', (800, 500)),
    ('nevermore-social.png', 'public/brand/nevermore-social.png', (1200, 630)),
]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

records = []
for name, target, size in exports:
    source = RENDERS / name
    image = Image.open(source).convert('RGB')
    if image.size != size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    dest = ROOT / target
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix == '.webp':
        image.save(dest, quality=92, method=6)
    else:
        image.save(dest, optimize=True)
    records.append({'file': target, 'width': size[0], 'height': size[1],
                    'bytes': dest.stat().st_size, 'sha256': digest(dest),
                    'render': str(source.relative_to(ROOT)).replace('\\', '/'),
                    'render_sha256': digest(source)})

font_records=[]
for family in ['manrope', 'newsreader']:
    p=ROOT/'node_modules/@fontsource-variable'/family/'files'/f'{family}-latin-wght-normal.woff2'
    font_records.append({'family':family, 'input':str(p.relative_to(ROOT)).replace('\\','/'),
                         'sha256':digest(p), 'license':'SIL Open Font License 1.1',
                         'license_file':f'public/licenses/{family.title()}-OFL.txt'})

scene_records=[]
for name in ['glasses-glassplay-hero.blend','glasses-glassplay-banner.blend',
             'glasses-glassplay-social.blend','glasses-glassplay-icon.blend',
             'feather-nevermore-poster.blend','feather-nevermore-social.blend']:
    p=SOURCE/name
    scene_records.append({'file':str(p.relative_to(ROOT)).replace('\\','/'), 'sha256':digest(p)})

provenance = {
    'schema_version':1,
    'created':'2026-10-22',
    'method':'Original procedural geometry, materials, lighting and text rendered with Blender Cycles. Pillow is used only to resize, encode and export the actual renders.',
    'renderer':{'application':'Blender','version':'5.2.2 LTS','build':'d13f752e3b9c',
                'engine':'Cycles','device':'NVIDIA GeForce RTX 3060 / OptiX',
                'samples':192,'denoise':True,'view_transform':'AgX / Medium High Contrast'},
    'visual_authority':{'reference':'docs/assets/glassplay-hero.svg',
                         'palette':['#0A111D','#111A32','#221638'],
                         'subject':'Season-neutral conceptual AR eyewear, with restrained blue and violet lighting.'},
    'disclosures':[
        'GlassPlay glasses are original conceptual brand artwork. They do not depict or verify physical Prism hardware.',
        'The Nevermore feather is original atmospheric title artwork, not gameplay, a screenshot, or an asset extracted from Nevermore.',
        'No private models, footage, SDK content, source media, image-generation output, or stock imagery were inputs.',
        'Public-site eligibility of these original images is separate from authorization to launch or distribute the site; the publication hold remains in effect.'
    ],
    'authoring_source':{'file':'scripts/art/render-brand.py',
                        'sha256':digest(ROOT/'scripts/art/render-brand.py'),
                        'instructions':'scripts/art/README.md'},
    'fonts':font_records,
    'editable_scenes':scene_records,
    'exports':records
}
target = ROOT/'docs/art/brand.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
print('Exported',len(records),'rendered assets and docs/art/brand.json.')
for item in records:
    print(item['file'],item['bytes'])
