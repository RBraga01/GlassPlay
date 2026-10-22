"""Convert the installed OFL webfonts to static fonts for Blender text objects."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.private/art-source/python-deps'))
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

out = ROOT / '.private/art-source/fonts'
out.mkdir(parents=True, exist_ok=True)
for family, weight, name in [('manrope', 650, 'Manrope-Semibold'),
                              ('manrope', 450, 'Manrope-Regular'),
                              ('newsreader', 500, 'Newsreader-Medium')]:
    source = ROOT / 'node_modules/@fontsource-variable' / family / 'files' / f'{family}-latin-wght-normal.woff2'
    font = TTFont(source)
    font = instantiateVariableFont(font, {'wght': weight}, inplace=True)
    font.flavor = None
    font.save(out / f'{name}.ttf')
print('Converted installed OFL font inputs for Blender.')
