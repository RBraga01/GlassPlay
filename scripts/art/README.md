# Blender brand artwork

`render-brand.py` authors both scenes from geometry and shaders. GlassPlay uses
original conceptual AR eyewear; the Nevermore fallback uses an original feather.
Neither scene imports original Nevermore media, hardware models, stock art or
generated images. Text is geometry rendered by Blender using the installed OFL
Manrope and Newsreader fonts. The original navy/violet GlassPlay SVG is the color
and category reference.

## Rebuild

Requires Blender 5.2, Python with Pillow, fontTools and brotli, and the font inputs
installed by `npm ci`. Run from the repository root:

```powershell
python -m pip install --target .private/art-source/python-deps fonttools brotli
python scripts/art/prepare-fonts.py
& $blender --background --python scripts/art/render-brand.py -- --scene glasses --mode final
& $blender --background --python scripts/art/render-brand.py -- --scene feather --mode final
python scripts/art/export-brand.py
```

Set `$blender` to the local Blender executable.
Use `--mode preview` for an initial composition render. Final renders use Cycles,
192 samples, denoising and OptiX when available; CPU rendering is also supported.
The fixed random seed preserves procedural detail. GPU and Blender versions can
produce small pixel differences on a rebuild.

Editable per-composition `.blend` files, converted font inputs and source PNG
renders stay in ignored `.private/art-source/`. Keep this directory together when
moving the scenes so font references remain available. Public outputs and hashes
are recorded in `docs/art/brand.json`.

`export-brand.py` only resizes and encodes rendered pixels. It never draws artwork
or typography. `scripts/brand-images.py` is the earlier flat-art pipeline and must
not be used to regenerate these replacement brand assets.

The product glasses are conceptual art and make no physical Prism claims. The
feather is atmospheric title art, not gameplay. Creating these original files
does not approve a public launch; the repository publication hold still applies.
