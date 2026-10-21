# Architecture — start small

## Scope

GlassPlay is currently a **collection and release/discovery repository**, not a monolithic application. No universal AR/VR/XR engine is implemented.

```text
GlassPlay
├── experiences/<slug>/       Independent experience packages and their docs
├── catalog/                  Minimal metadata for discovery
├── platforms/                Verified device-specific integration notes/code
├── shared/                   Modules proven reusable by >=2 experiences
├── templates/experience/     Scaffolding for the next experience
└── docs/                     Decisions and release gates
```

## Evolution rules

1. **Experience first:** keep runtime, configuration, tests and assets inside the experience that needs them.
2. **Adapters second:** device integration belongs under that experience until a stable, demonstrably reusable interface exists.
3. **Extract third:** only then move a tested component to `shared/` or an adapter to `platforms/`.
4. **Catalogue is metadata:** `catalog/experiences.json` is an index, not an install manifest or proof of compatibility.
5. **No silent compatibility claims:** simulator / hardware / OS / SDK versions must be identified separately.

## Source and release separation

Development repositories may contain prototypes, intermediate assets, research history, and private notes. GlassPlay releases must be minimal, attributable, reproducible exports from approved source snapshots. Nothing in this skeleton automatically imports Nevermore.

## Future options, not current features

A launcher or discovery UI, shared session controls, reusable playback, and additional hardware adapters are possible future work. They are **not** part of the current repository.
