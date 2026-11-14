---
name: Bank_Data
description: European bank figures, each traced to the filing it came from, drawn as Plate I of a statistical atlas.
colors:
  plate-green: "#0f5a3c"
  plate-green-deep: "#0b4a31"
  tint-1: "#cdeadd"
  tint-2: "#9fd2b7"
  tint-3: "#5ea883"
  tint-4: "#2a7a55"
  dispute-amber: "#8a5a00"
  dispute-rule: "#d9a441"
  dispute-wash: "#fff8ec"
  dispute-ring: "#b07410"
  plate-ink: "#141413"
  ink-secondary: "#45453f"
  paper: "#ffffff"
  unbanked-land: "#e9ece8"
  hairline: "#d4d8d2"
  sea-lettering: "#6d8378"
  code-ground: "#f3f6f3"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(30px, 1.2rem + 1.6vw, 46px)"
    fontWeight: 760
    lineHeight: 1.04
    letterSpacing: "-0.012em"
    fontVariation: "\"wdth\" 112"
  display-short:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(30px, 1rem + 1.5vw, 40px)"
    fontWeight: 760
    lineHeight: 1.02
    letterSpacing: "-0.012em"
    fontVariation: "\"wdth\" 112"
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(24px, 1rem + 1.2vw, 34px)"
    fontWeight: 720
    lineHeight: 1.12
    letterSpacing: "-0.01em"
    fontVariation: "\"wdth\" 110"
  figure:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(30px, 1rem + 2vw, 44px)"
    fontWeight: 720
    lineHeight: 1
    fontFeature: "\"lnum\", \"tnum\""
    fontVariation: "\"wdth\" 90"
  note-numeral:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "44px"
    fontWeight: 300
    lineHeight: 1
    fontVariation: "\"wdth\" 62"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(20px, 1rem + 0.8vw, 26px)"
    fontWeight: 650
    lineHeight: 1.3
    fontVariation: "\"wdth\" 110"
  step-title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 700
    lineHeight: 1.55
    fontVariation: "\"wdth\" 100"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"lnum\", \"tnum\""
    fontVariation: "\"wdth\" 100"
  body-phone:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"lnum\", \"tnum\""
    fontVariation: "\"wdth\" 100"
  table:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"lnum\", \"tnum\""
    fontVariation: "\"wdth\" 100"
  key:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.22
    fontFeature: "\"lnum\", \"tnum\""
  caption:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.3
    fontFeature: "\"lnum\", \"tnum\""
    fontVariation: "\"wdth\" 100"
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "0.14em"
    fontVariation: "\"wdth\" 125"
  sea-lettering:
    fontFamily: "Archivo, sans-serif"
    fontSize: "6.2px"
    fontWeight: 600
    letterSpacing: "0.32em"
    fontVariation: "\"wdth\" 125"
  mono:
    fontFamily: "ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  none: "0px"
  hint: "2px"
spacing:
  gutter: "clamp(16px, 2vw, 24px)"
  plate-inset: "8px"
  tight: "14px"
  panel: "22px"
  column: "28px"
  note-head: "36px"
  step: "44px"
  section: "clamp(64px, 9vw, 120px)"
components:
  button-primary:
    backgroundColor: "{colors.plate-green}"
    textColor: "{colors.paper}"
    typography: "{typography.body}"
    rounded: "{rounded.hint}"
    padding: "14px 20px 14px 22px"
  button-primary-hover:
    backgroundColor: "{colors.plate-green-deep}"
    textColor: "{colors.paper}"
  key-entry:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.plate-ink}"
    typography: "{typography.key}"
    rounded: "{rounded.hint}"
    padding: "1.5px 4px"
  key-entry-active:
    backgroundColor: "{colors.tint-1}"
    textColor: "{colors.plate-ink}"
  disagreement-pair:
    backgroundColor: "{colors.dispute-wash}"
    textColor: "{colors.dispute-amber}"
    typography: "{typography.figure}"
    rounded: "{rounded.none}"
    padding: "14px 16px 12px"
  cartouche:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.plate-ink}"
    rounded: "{rounded.none}"
    padding: "28px 28px 26px"
  inset-panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.plate-ink}"
    rounded: "{rounded.none}"
    padding: "10px 14px 8px"
  legend-panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.plate-ink}"
    rounded: "{rounded.none}"
    padding: "14px 28px 16px"
  template-tag:
    textColor: "{colors.plate-green-deep}"
    typography: "{typography.mono}"
---

# Design System: Bank_Data

## Overview

**Creative North Star: "Atlas Plate I"**

The site is a plate from a statistical atlas of European banking, printed on white paper in near-black ink. The map is the hero and the argument: land is shaded by how many pilot banks a country holds, each bank is a numbered marker, a key in the margin names them, a legend explains the shading, and an inset magnifies the one region where the story turns. Everything else is "notes to the plate", numbered and called from the hook with superscript references, the way an atlas annotates a plate.

Density is that of a reference plate: small, precise lettering inside a ruled frame, then generous, readable notes below. The voice is cartographic and documentary, not promotional. One colour family (plate green) carries structure and the single action; one amber is reserved for a single meaning, two sources that disagree, and it matches the amber the dashboard uses for the same meaning. Depth is printed, not lifted: rules, hairlines and tints do the work.

The world refuses the centred-headline-over-screenshot-and-three-cards project page. This system describes the promo surface `docs/index.html`; the existing dashboard (`docs/dashboard.html`) has its own older look and is not part of this system.

**Key Characteristics:**
- A double-rule neatline with a graduated green-and-white tick band frames the plate.
- Land in a four-step green tint scale keyed to bank count; untinted land for "no pilot bank".
- Numbered circular markers on the map, mirrored by a numbered key that highlights in step with them.
- Archivo as one family across widths: expanded tracked caps for map lettering and labels, normal width for reading, condensed for big numerals; lining tabular figures throughout.
- Amber means disagreement and nothing else.
- One authored motion: the plate inks in, west to east, and respects reduced motion.

## Colors

A white plate in near-black ink, graded greens for land and structure, and one amber kept for source disagreement.

### Primary
- **Plate Green** (`plate-green`): the neatline's tick band, the primary action's fill, note numerals, step counters, focus outline, caret and the active marker fill. The colour of the plate's structure and of its one action.
- **Deep Plate Green** (`plate-green-deep`): link text, superscript note calls, template tags, function names in code, and the primary action's hover fill.

### Secondary
- **Land Tints 1 to 4** (`tint-1`, `tint-2`, `tint-3`, `tint-4`): land shading by number of pilot banks (1, 2, 3 to 4, 6). `tint-1` doubles as the key's hover/active wash and the text selection colour; `tint-3` colours the scrollbar thumb.

### Tertiary
- **Dispute Amber** (`dispute-amber`): text of disagreeing figures (the inset's paired values, the big figures in note 2, the status line's "two filings disagree").
- **Dispute Rule** (`dispute-rule`): the border and the dashed divider of a disagreement pair.
- **Dispute Wash** (`dispute-wash`): the ground of a disagreement pair and the fill of a marker's disagreement ring.
- **Dispute Ring** (`dispute-ring`): the ring around a disagreeing bank's marker, the dashed leader line to the inset, and the ring on a disagreeing country's phone badge. Deeper than the rule so it holds on green land.

### Neutral
- **Plate Ink** (`plate-ink`): all primary text, every rule (neatline, panel borders, note tops), marker strokes and numbers.
- **Secondary Ink** (`ink-secondary`): ledes, captions, status line, country codes, plate foot and footer.
- **Paper** (`paper`): page ground, panel ground, marker fill at rest, open water on the map.
- **Unbanked Land** (`unbanked-land`): countries with no pilot bank (including Germany, explained in note 5).
- **Hairline** (`hairline`): light dividers inside tables, the key and figure captions.
- **Sea Lettering** (`sea-lettering`): the decorative, aria-hidden sea names on the map only. It is not a text colour for content.
- **Code Ground** (`code-ground`): the faint green-grey ground of the install/code block in note 4, under a 1px ink top rule. Its only use.

### Named Rules
**The One Meaning Rule.** Amber marks a disagreement between two filings and nothing else: not warnings, not emphasis, not hover. It is never red, because a disagreement is not an error.

**The Ink-and-Tint Rule.** Colour on the plate is either ink, a land tint, plate green or amber. A new hue needs a new meaning on the map first.

## Typography

**Display Font:** Archivo (variable, weights 100 to 900, widths 62% to 125%, self-hosted from `docs/fonts/`, SIL OFL), with system-ui fallback
**Body Font:** Archivo at normal width
**Label/Mono Font:** ui-monospace stack (Cascadia Mono, Consolas) for template tags, code and the inset table's column heads

**Character:** One grotesque used the way a cartographer uses one alphabet at several widths: expanded and tracked for lettering that labels the plate, normal for prose, condensed for figures and numerals. All figures are lining and tabular so columns of numbers align.

### Hierarchy
- **Display** (`display`): the hook in the title cartouche; balanced wrapping.
- **Display, short screens** (`display-short`): the same hook capped at 40px with tighter leading when the plate is 1280px or wider and the viewport is 860px tall or less.
- **Headline** (`headline`): each note's heading, max 26ch, balanced.
- **Figure** (`figure`): the two disagreeing numbers in a disagreement pair, condensed and in amber.
- **Note numeral** (`note-numeral`): the large thin, most-condensed numeral beside each note, in plate green.
- **Title** (`title`): the closing bar's line.
- **Step title** (`step-title`): the bold 19px title of each "How to try it" step, its number in plate green.
- **Body** (`body`): reading text, 66ch max in notes, 40ch in the cartouche, pretty wrapping.
- **Body, phone** (`body-phone`): body text at 760px and below.
- **Table** (`table`): the provenance table in note 1 and the bank names heading each disagreement pair in note 2.
- **Key** (`key`): the key to the plate; the status line runs at 12.5px, legend at 12.5px, captions at 12.5 to 13px.
- **Caption** (`caption`): the inset table's caption, and the key's status line on short wide screens.
- **Label** (`label`): expanded tracked uppercase for panel titles ("Key to the plate", "Legend", "Inset: Austria"), the notes heading, scope sub-heads and the wordmark (11 to 13px). Country codes in the key and table column heads use the same expanded voice at 0.1em tracking.
- **Sea lettering** (`sea-lettering`): widest tracking, set in SVG map units inside the plate.

### Named Rules
**The Width-Is-Voice Rule.** Width, not a second typeface, separates the voices: 125% expanded caps letter the plate, 100% reads, 90% and below states a figure.

**The Tabular Rule.** Every number on the page sets in lining tabular figures.

## Layout

The page is a full-width plate inside a page gutter (`gutter`), preceded by a thin margin strip (wordmark, plate title, three plain links) and followed by a plate foot, the notes, a closing bar and a footer. Notes, closing bar and footer sit in a 1180px column.

**At 1280px and wider** the plate's field has a fixed height (clamp 640px to 880px, tracking the viewport) and the map fills it absolutely. Panels sit on the map, bordered by half-point ink rules: the title cartouche spans the left 33% full-height, the legend shares that column at the bottom, the key spans the right 21.5% full-height with the status line at its foot, and the inset floats in the Atlantic/Norwegian Sea at 290px wide, joined to Austria by a dashed amber leader. Script reframes the map's viewBox so the pilot region (Portugal to Greece) fits exactly between the cartouche and the key. On short wide screens (height up to 860px) the panels tighten.

**Below 1280px** the panels stack in a column: cartouche, map (cropped to the pilot region, max 820px), inset (no shadow, no leader), legend, then the key set in two columns.

**At 760px and below** body drops to 16px, the 28 numbered markers give way to one tappable count badge per country (amber-ringed where filings disagree) and a status line under the map that lists the tapped country's banks and lights them in the key, sea lettering is hidden, the margin strip stacks, note numerals move above their text, steps go single-column, and the carry table drops its provenance column.

**Rhythm:** 8px plate inset; 14px tight gaps; 22px panel and paragraph spacing; 28px column gaps and panel padding; 36px above each note's content; 44px between steps; `section` padding above the notes. Notes are a two-column grid (72px numeral column, 28px gap) separated by full-width ink rules.

## Elevation & Depth

The plate is printed, so depth is conveyed by rules, hairlines and tints, not shadows. Panels on the map are separated from it by paper ground and half-point ink borders. Two quiet shadows exist, both soft and green- or ink-tinted:

### Shadow Vocabulary
- **Action lift** (`box-shadow: 0 1px 2px rgb(15 90 60 / .25), 0 6px 16px -8px rgb(15 90 60 / .55)`; hover `0 2px 4px rgb(15 90 60 / .3), 0 10px 22px -10px rgb(15 90 60 / .6)`): the primary action only.
- **Inset lift** (`box-shadow: 0 1px 2px rgb(20 20 19 / .08), 0 10px 24px -14px rgb(20 20 19 / .35)`): the inset panel floating on the map at wide widths; removed when stacked.

### Named Rules
**The Printed Plate Rule.** Structure is drawn with rules (1.5px outer neatline, 0.5px inner rules, 1px note rules, 0.5px hairlines), never with cards or shadows. Only the action and the floating inset lift.

## Shapes

Square-cut throughout: panels, neatline, figures, tables and disagreement pairs have no radius. The only rounding is a 2px hint (`hint`) on the primary action, key entries and focus outlines. Circles belong to the map: markers are a 6.4-unit dot, with a 9.6-unit amber ring when the bank's filings disagree. Lines carry meaning by style: solid ink for structure, hairline for subdivision, dashed amber for the disagreement leader and the divider inside a disagreement pair.

**The Neatline.** A 1.5px outer ink rule, 8px padding carrying a 5px graduated band of alternating 28px plate-green and paper ticks on all four sides, a 0.5px inner rule 5px in, and a 0.5px rule around the map field. It frames the plate only, once per page.

## Components

### Buttons
Character: the plate's one green action, solid and direct.
- **Shape:** near-square (2px).
- **Primary:** plate-green fill, paper text, weight 650 at 17px, padding 14px 20px 14px 22px, a trailing 18px stroked arrow; action lift shadow. Label: "Open the interactive plate". Used twice: in the cartouche and in the closing bar.
- **Hover / Focus:** fill deepens to deep plate green with a slightly larger lift; pressed moves down 1px; transitions 0.2s. Focus is the global 2px plate-green outline at 3px offset.
- **Context line:** in the cartouche, one sentence in secondary ink at 14px (13px on short screens), max 38ch, directly under the action, saying what the dashboard shows. The action never stands without it.
- **Secondary:** plain links in deep plate green with 1px underline at 3px offset, thickening to 2px on hover; grouped as a wrapped row at 14px under the action.

### Map markers
- Paper dot with an ink stroke and a bold 7.2px number. Disagreeing banks add an amber ring on a wash fill.
- **Active** (hover or linked key focus): dot fills plate green, number turns paper.
- At phone width: replaced by one count badge per country (8.6-unit dot, bold count, 17-unit tap area, amber ring where filings disagree). A tap fills the badge plate green and lists that country's banks under the map.

### Key to the plate
- A margin panel listing the 28 banks grouped by country: expanded-caps country code in a 30px column, entries with a right-aligned bold number.
- Entries are focusable labels (`tabindex="0"`), not links. Hover or focus on an entry, or hover on its marker, highlights both (tint-1 wash on the entry, green marker) and writes the bank's name, country and total assets into a polite live status line under a 1px ink rule; disagreeing banks add an amber line.

### Legend
- Expanded-caps title; rows of 22x12px swatches with a faint 0.5px border for each land tint and unbanked land, plus the drawn disagreement marker.

### Inset and leader
- A floating panel with expanded-caps title, a magnified map of the disagreement region in a hairline frame, and a compact pairs table: mono column heads, bold amber values, the gap in secondary ink. A dashed amber leader runs from the region on the main map to the inset.

### Disagreement pair
- Two figures side by side on dispute wash inside a 1px dispute-rule border, split by a dashed dispute-rule line; each figure in the condensed amber figure style with its mono source tag beneath, and the gap stated in a line below. Both numbers always appear; neither is ranked above the other.

### Notes to the plate
- Numbered articles: a thin condensed green numeral, a headline, a secondary-ink lede, then body, tables, figures or code. Called from the hook by bold deep-green superscript numbers.
- **Carry table:** expanded-caps column heads over a 1px ink rule, hairline rows, right-aligned bold figures, mono template tags in deep green.
- **Steps:** counted in plate green, text column beside a screenshot figure framed by a 0.5px ink rule with a hairline caption.
- **Code:** mono 14px on a pale green-grey ground between a 1px ink top rule and a hairline bottom.

### Navigation
- The margin strip above the plate: expanded-caps wordmark, plate title in secondary ink, and three plain ink links at weight 500 that underline on hover. Stacks at phone width.

### Motion
- One authored moment: land inks in from desaturated to full colour (1.1s, `cubic-bezier(.16, 1, .3, 1)`), staggered west to east by each country's position; markers then pop from 55% scale and fade up from 35% opacity, 28ms apart after 300ms. It starts from an already-visible state and runs only under `prefers-reduced-motion: no-preference`. Hover states transition at 0.2s.

## Do's and Don'ts

### Do:
- **Do** frame a plate with the neatline: outer 1.5px ink rule, graduated plate-green tick band, inner 0.5px rule.
- **Do** keep amber (dispute-amber text, dispute-wash ground, dispute-rule border, dispute-ring on the map) for source disagreement only, and show both figures with their templates.
- **Do** letter the plate in expanded tracked Archivo caps and set reading text at normal width; set every number in lining tabular figures.
- **Do** link marker and key both ways and announce the selection in a polite live status line.
- **Do** make key entries focusable labels, not links.
- **Do** keep the action label "Open the interactive plate" in solid plate green.
- **Do** stack panels below 1280px, and at 760px and below swap markers for per-country count badges with a tap-to-list status line, and hide sea lettering.
- **Do** keep motion to the single ink-in reveal, from a visible state, behind `prefers-reduced-motion: no-preference`.
- **Do** keep every interactive element on the 2px plate-green focus outline.

### Don't:
- **Don't** use red, or any colour other than this amber, to mark a disagreement; it is not an error.
- **Don't** reconcile, average or rank two disagreeing figures into one.
- **Don't** build the centred-headline-over-screenshot-and-three-cards project page.
- **Don't** borrow the dashboard's (`docs/dashboard.html`) older look into this system, or restyle the dashboard from it.
- **Don't** round panels, tables or pairs; the 2px hint is for the action, key entries and focus only.
- **Don't** use shadows for structure; rules and hairlines draw the plate, and only the action and floating inset lift.
- **Don't** add a second typeface for display; change Archivo's width instead.
- **Don't** add further animated moments, scroll-triggered effects or looping motion.
