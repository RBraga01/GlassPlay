---
name: GlassPlay
description: A little magic, right before your eyes.
colors:
  glassplay-accent: "#c2e6d1"
  glassplay-bg: "#101715"
  glassplay-surface: "#19221e"
  text: "#f0eee5"
  glassplay-muted: "#b6c4ba"
  glassplay-line: "#39473e"
  nevermore-accent: "#e5d5ed"
  nevermore-bg: "#141217"
  nevermore-surface: "#201b25"
  nevermore-muted: "#c6bacb"
  nevermore-line: "#423947"
typography:
  display:
    fontFamily: "'Newsreader Variable', Georgia, serif"
    fontSize: "clamp(3.75rem, 6.6vw, 6rem)"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-.035em"
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

## Overview

**Creative North Star: "A cinematic editorial film programme"**

An independent entertainment collection with expressive typography, generous dark space and deliberate transitions between encounters. GlassPlay remains season-neutral; each experience can carry its own atmosphere. The confirmed mint identity and Nevermore's spectral lavender define the current implementation.

The system uses authored artwork, simple controls and restrained motion. Annapurna Interactive's selection hierarchy and Playdead's restraint informed the review benchmark; neither is a copied visual style. Page-specific composition remains in [the surface brief](docs/PRODUCT-SURFACE.md).

**Key Characteristics:**

- Expressive serif display type with readable sans-serif support.
- Mint collection identity and a distinct lavender Nevermore theme.
- Arched featured artwork, fine dividers and open editorial sections.
- Visible native controls and intentional media states.

## Colors

Mint and lavender accents sit against related dark backgrounds, with warm off-white text and tinted supporting copy.

### Primary

**GlassPlay mint** is the collection's action, focus and emphasis color. It also colors the glasses mark. The default CSS variables map to the `glassplay-*` frontmatter tokens.

### Secondary

**Nevermore lavender** replaces the action and focus accent on Nevermore. Its theme also overrides background, surface, supporting text and divider variables with the `nevermore-*` tokens.

### Neutral

The shared **off-white text** is used for headings and primary copy. **Green-black** and **lavender-black** define the respective page backgrounds; their surface colors identify secondary regions. Supporting text and fine dividers stay tinted toward the active theme.

**The Experience Palette Rule.** Keep the collection mint identity distinct from each experience's palette; Nevermore's lavender does not recolor the collection.

## Typography

**Display Font:** Newsreader Variable, with Georgia and serif fallbacks.
**Body Font:** Manrope Variable, with a sans-serif fallback.

Self-hosted Latin variable fonts provide roman and italic Newsreader plus Manrope, with OFL notices. High-contrast display lettering carries atmosphere; Manrope carries navigation, descriptions and controls.

### Hierarchy

The frontmatter records the shared display, headline, title, body and action roles. Display and headline sizes are fluid; headings balance their lines. Individual hero compositions adjust the display role, while experience names and encounter headings also use Newsreader. Italic emphasis is lighter than surrounding display text. Supporting body sizes vary with context; paragraphs are bounded at 64ch, with narrower promotional copy and expanded details up to 75ch.

**The Display and Reading Rule.** Use Newsreader for expressive headings and Manrope for instructions, navigation and sustained reading.

## Layout

The centered content container caps at 1328px. Its side gutters are 56px by default, 32px at widths up to 1100px, 20px up to 760px and 16px up to 380px. Shared sections use the fluid section spacing token and thin dividing rules.

Paired desktop compositions become an ordered single column at 760px. Seasonal concepts change from three columns into horizontal artwork-and-copy rows; the four interaction steps become two columns. Navigation remains visible without a menu dependency. At 380px and below, Nevermore's title metadata wraps and aligns left.

Images declare intrinsic dimensions or aspect ratios. The featured poster changes its crop and arch proportions for mobile; the experience hero places artwork above its statement. Layout does not depend on client JavaScript.

## Elevation & Depth

Depth comes from artwork, dark tonal layers, fine borders and local image scrims. The interface uses no box-shadow system. The Nevermore hero scrim supports text contrast, and title artwork supplies the fallback atmosphere.

**The Readable Artwork Rule.** Compose and shade imagery to support readable copy; retain visible artwork rather than hiding it behind decoration.

## Shapes

Sections and action surfaces have square corners and fine borders. The arched featured poster is the signature silhouette, with a circular arrow affordance. These forms echo the glasses mark without turning every container into a rounded card. Focus outlines use a slight corner radius.

## Components

### Actions and navigation

Primary links use the active theme's accent fill, a matching one-pixel border and a minimum height of 52px. Hover makes the standard action transparent with accent text. The Nevermore hero uses its own dark-on-lavender action and reverses those colors on hover. Text links remain underlined with an SVG arrow.

Navigation uses Manrope and stays visible on mobile. The shared focus treatment is a two-pixel accent outline with a six-pixel offset. The skip link appears on focus and targets the focusable main region. Selection and scrollbars use the site palette.

### Featured poster and concept entries

The whole featured poster is a link. Its title precedes ordinary sentence-case category metadata; publication status sits within the image. The image scales to 1.035 on hover over one second using an exponential ease-out curve. Reduced-motion preferences remove this effect, transitions and smooth scrolling; content is visible before interaction.

Concept entries use artwork, a display title, a factual status label and short copy. Their mobile rows preserve reading order rather than compressing a desktop grid.

### Media states

The default build uses original title artwork and concept graphics. Local review uses approved runtime-derived artwork and labelled Windows/Simulator footage, staged outside `public/`. Public inclusion requires explicit policy approval and exact file hashes. Production artwork never represents verified physical Prism footage.

Video uses native controls, an explicit poster, reserved 16:9 space and no autoplay. The main film provides captions and a transcript; the teaser is silent. A release-held preview has artwork and explanatory copy, with no false play action. Failed playback reveals a readable status and recovery instruction. Private review is marked noindex; the deployable fallback retains production canonicals and metadata.

### Disclosure rows

Practical details use native details/summary, fine dividers and an authored SVG chevron that rotates when open. Controls retain the shared visible focus treatment. The breadcrumb uses the same drawn arrow vocabulary; icons use rounded strokes.

## Do's and Don'ts

### Do:

- **Do** preserve the distinction between collection and experience palettes.
- **Do** keep the mobile reading order, visible navigation and keyboard focus.
- **Do** show authentic media only within its approved publication boundary, with Simulator labels and text alternatives.
- **Do** use title artwork and explicit availability copy when publication is held.
- **Do** respect reduced motion and require intentional media playback.

### Don't:

- **Don't** turn collection pages permanently Halloween-themed.
- **Don't** substitute emoji, glyph icons or stock imagery for the authored visual system.
- **Don't** place decorative eyebrows above headings or invent play and download actions.
- **Don't** imply verified physical-device behavior through artwork or Simulator footage.
