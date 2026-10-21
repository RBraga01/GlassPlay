"""Rebuild static brand/share images. Requires Pillow, fonttools and brotli.
Uses the exact OFL font files installed by npm; no private gameplay artwork.
"""
from pathlib import Path
from io import BytesIO
import shutil
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/brand'
OUT.mkdir(parents=True, exist_ok=True)

def font(family, filename, size):
    source = ROOT / f'node_modules/@fontsource-variable/{family}/files/{filename}'
    ttf = TTFont(source)
    ttf.flavor = None
    buffer = BytesIO()
    ttf.save(buffer)
    buffer.seek(0)
    return ImageFont.truetype(buffer, size)

sans = lambda s: font('manrope', 'manrope-latin-wght-normal.woff2', s)
serif = lambda s: font('newsreader', 'newsreader-latin-wght-normal.woff2', s)
italic = lambda s: font('newsreader', 'newsreader-latin-wght-italic.woff2', s)

def logo(draw, x, y, scale=1):
    for ox in [0, 45]:
        draw.rounded_rectangle((x+ox*scale, y, x+(ox+39)*scale, y+31*scale), radius=12*scale, outline='#c2e6d1', width=max(1,int(2*scale)))
    draw.line((x+39*scale,y+9*scale,x+45*scale,y+9*scale),fill='#c2e6d1',width=max(1,int(2*scale)))

im=Image.new('RGB',(1200,630),'#101715'); d=ImageDraw.Draw(im)
logo(d,76,63,.6);d.text((145,55),'GlassPlay',font=sans(34),fill='#f0eee5')
d.line((76,132,1124,132),fill='#39473e',width=1)
d.text((72,177),'A little magic,',font=serif(98),fill='#f0eee5')
d.text((72,282),'right before your eyes.',font=italic(98),fill='#c2e6d1')
d.text((76,507),'Interactive experiences for AR smart glasses.',font=sans(29),fill='#b6c4ba')
im.save(OUT/'glassplay-social.png',optimize=True)

im=Image.new('RGB',(1200,630),'#17111d');d=ImageDraw.Draw(im)
for inset in (0,37,74):
    d.arc((755+inset,65+inset,1190-inset,630-inset),180,360,fill='#49364f',width=2)
d.ellipse((900,110,1040,250),fill='#d7bed7');d.ellipse((935,83,1060,231),fill='#17111d')
d.text((72,67),'GlassPlay',font=sans(30),fill='#c6bacb')
d.text((67,205),'Nevermore',font=serif(134),fill='#f0e6ef')
d.text((76,389),'Halloween comes looking for you.',font=italic(51),fill='#d7bed7')
d.text((76,534),'For AR smart glasses  /  Preview in preparation',font=sans(24),fill='#c6bacb')
im.save(OUT/'nevermore-social.png',optimize=True)

im=Image.new('RGB',(180,180),'#101715');d=ImageDraw.Draw(im);logo(d,27,67,1.5);im.save(OUT/'apple-touch-icon.png',optimize=True)
licenses=ROOT/'public/licenses';licenses.mkdir(exist_ok=True)
for family, name in [('manrope','Manrope'),('newsreader','Newsreader')]:
    shutil.copyfile(ROOT/f'node_modules/@fontsource-variable/{family}/LICENSE',licenses/f'{name}-OFL.txt')
print('Built 1200x630 share images, touch icon and font notices.')
