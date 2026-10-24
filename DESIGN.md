---
name: GlassPlay
description: A little magic, right before your eyes.
colors:
  glassplay-accent: "#b4a6ff"
  glassplay-bg: "#0a111d"
  glassplay-surface: "#111a32"
  text: "#f3f4fa"
  glassplay-muted: "#b7c1d8"
  glassplay-line: "#34415b"
  nevermore-accent: "#e5d5ed"
  nevermore-bg: "#141217"
  nevermore-surface: "#201b25"
  nevermore-muted: "#c6bacb"
  nevermore-line: "#423947"
typography:
  display:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "clamp(3.2rem, 5.4vw, 5rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-.055em"
  headline:
    fontFamily: "'Newsreader Variable', Georgia, serif"
    fontSize: "clamp(2.5rem, 4vw, 4.1rem)"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-.035em"
  title:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "1.25rem"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-.025em"
  body:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "1rem"
    lineHeight: 1.7
  action:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: ".9rem"
    fontWeight: 700
spacing:
  section: "clamp(4.5rem, 9vw, 8.5rem)"
components:
  button-primary:
    backgroundColor: "{colors.glassplay-accent}"
    textColor: "{colors.glassplay-bg}"
    typography: "{typography.action}"
    padding: "13px 21px"
  button-primary-hover:
    backgroundColor: "transparent"
    textColor: "{colors.glassplay-accent}"
  button-nevermore:
    backgroundColor: "{colors.nevermore-accent}"
    textColor: "{colors.nevermore-bg}"
    typography: "{typography.action}"
    padding: "13px 21px"
  button-nevermore-hover:
    backgroundColor: "transparent"
    textColor: "{colors.nevermore-accent}"
---

# Design System: GlassPlay

## Visual authority

The owner's PR #1 review on 2026-10-22 supersedes the rejected mint/editorial direction. The original `docs/assets/glassplay-hero.svg` is the palette and category reference: dark navy, atmospheric blue/violet light, recognizable smart glasses. The SVG is retained as historical reference, not as the current README hero.

**Hero & brand evolution (2026-10-22).** The owner approved a brighter direction: *the playful side of smart glasses*: little unexpected moments around a pair of brand-neutral glasses at dusk (raven and feather, ghost, jack-o'-lantern, lantern-bearer, star, target, floating island). The home hero, README banner and social card all derive from that owner-supplied artwork with its baked-in text removed; the name "GlassPlay" (white "Glass", blue-to-violet "Play") and the tagline are live HTML on the site. Seasonal details sit among non-seasonal ones, so the permanent identity stays season-neutral. Sources and processing: `docs/assets/glassplay-hero-provenance.json`. The illustration is not physical Prism footage or a hardware claim. Nevermore keeps its own dark supernatural composition made from approved production frames.

**Season concept banners (2026-10-22).** Christmas, Easter and St. Patrick's Day use owner-supplied banners in the same language as the hero: the same brand-neutral glasses, small encounters and warm practical light, each with its own palette (snowy blue and gold; sunset lavender and pastel; emerald and gold twilight). The season name, "Coming soon · Concept" and the summary are HTML on the left, over a soft scrim, on a 21:9 banner; on mobile the art sits above the text in a dedicated crop. They are labelled as concepts, not available experiences. Sources: `docs/assets/season-banners-provenance.json`.

## Colors

Navy `#0a111d` is the collection background, `#111a32` the supporting surface, `#b4a6ff` the action/focus accent. Blue/violet light belongs primarily to the rendered imagery. Text is `#f3f4fa`; supporting text `#b7c1d8`. Nevermore retains its separate charcoal/plum/lavender palette recorded above. No mint/green collection theme or crescent/arch hero remains.

## Typography

Self-hosted OFL Manrope carries the collection's confident, direct headline and interface. Newsreader carries the Nevermore name and cinematic encounter headings; it does not replace GlassPlay's identity. Body copy, controls and practical information use Manrope. Mobile sizes are adjusted to keep the category and discovery action readable.

## Composition

The first viewport pairs the brand promise and explicit AR smart-glasses category with the externally rendered glasses. The rendered object leads the visual, without an arch container. Nevermore follows as the featured experience with an authentic playable teaser in private review, or a clearly labelled original 3D title-art fallback while publication is held.

Future seasons are concise concept entries, not pretend products or placeholder product pictures. The about section describes the real-world experience without another decorative glasses drawing.

The Nevermore page gives the new cinematic composition its own large stage. The responsive mobile arrangement keeps the characters above the statement. Authentic encounter stills and a controllable film support the experience; practical release information follows.

## Layout and accessibility

Content caps at 1328px with 56/32/20/16px responsive gutters. Paired compositions stack below 760px. Native video controls, no autoplay, captions, transcript, keyboard skip link, visible focus, explicit image dimensions, readable error messages and reduced-motion behavior remain. Private review is noindex; public metadata is validated separately.

## Artwork and publication

Render scripts and provenance are in `scripts/art/` and `docs/art/`. Editable Blender scenes remain local under `.private/art-source/`; scripts reproduce them. README banners may contain approved project imagery in this repository. They are not copied into the deployable public tree. Public source visibility, website publication, promotional derivatives and application release are separate decisions.

The media review must be measured using `--review`, with its actual MP4s and manifest. Scores from the title-art public fallback cannot be presented as performance evidence for the real media experience. Owner visual approval is still required; technical measurements do not approve the artwork.
