# GlassPlay

**Interactive experiences for AR smart glasses.**

GlassPlay is a collection of small, immersive experiences designed to bring seasonal events and playful surprises into the real world through smart glasses. Start with **Nevermore** (Halloween); leave room for Christmas, St. Patrick's Day, Easter and other occasions.

> **Project status:** Foundation only. GlassPlay is not yet a downloadable app store or a working multi-device runtime. No experience is publicly installable from this repository yet.

## Explore experiences

| Experience | Theme | Status | Hardware |
| --- | --- | --- | --- |
| [Nevermore](experiences/nevermore/README.md) | Halloween — haunting encounters, animated raven, local voice trigger | **Pilot/MVP candidate; export pending** | Raven Prism: simulator-tested, physical device **unverified** |
| [Christmas](experiences/christmas/README.md) | Christmas / winter | **Idea only** | Not developed |
| [St. Patrick's](experiences/st-patricks/README.md) | St. Patrick's Day | **Idea only** | Not developed |
| [Easter](experiences/easter/README.md) | Easter / spring | **Idea only** | Not developed |

The machine-readable index is [catalog/experiences.json](catalog/experiences.json). **Planned** entries are not downloads.

## What GlassPlay is

- A discoverable home for **AR glasses experiences** and **smart glasses experiences**.
- A place to publish each experience's instructions, compatibility, demo and verified releases.
- A lightweight structure where every experience can evolve independently.

## What it is not (yet)

GlassPlay does **not** claim VR support, cross-device compatibility, background overlays or a common engine. Compatibility is documented per experience and only when verified. A dedicated platform adapter or shared module will be added only when actual implementations require it.

## Repository layout

```text
experiences/             One self-contained directory per experience
  nevermore/             Halloween — current MVP candidate (no export yet)
  christmas/             Future concept
  st-patricks/           Future concept
  easter/                Future concept
catalog/                 Searchable experience metadata
platforms/               Device-specific compatibility notes/adapters (as needed)
shared/                  Reusable components (only once proven reusable)
templates/experience/    Starter files for new experiences
docs/                    Architecture, publishing and release gates
```

## Nevermore and release policy

Nevermore is being developed separately in a **private research repository**. Its production runtime and media **have not been copied here**. Any eventual release must be a **curated snapshot**, never a mirror of research history. Physical Prism validation, deployment authorization and asset redistribution rights remain release gates.

Read [how to add an experience](docs/ADD_EXPERIENCE.md), [architecture](docs/ARCHITECTURE.md) and the [release checklist](docs/RELEASE_CHECKLIST.md).

## Naming and discoverability

**GlassPlay** is the collection. **Nevermore** is an experience. New experiences receive their own names and descriptions; the collection name stays stable.

Search terms: AR glasses, smart glasses, augmented reality, XR experiences, interactive experiences, Raven Prism, Halloween, seasonal experiences.

## Licensing

**No general license grant is implied by this skeleton.** Code, artwork, video, audio, third-party frameworks and models may be governed by different licenses. Establish documented rights and add the appropriate license/attribution files before distributing any runtime or media.
