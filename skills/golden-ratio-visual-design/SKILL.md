---
name: golden-ratio-visual-design
description: "Create or revise visual layouts using measurable golden-ratio relationships, comfortable margins and balanced controls. Use for UI, images, documents, slides and other visual compositions. Calculate, implement, render and verify. Exclude plain text and nonvisual tasks."
license: MIT
metadata:
  version: "0.1.1"
---

# Golden Ratio Visual Design

Use the golden ratio as a measurable composition constraint, not a decorative
phrase or a guarantee of beauty. Combine this skill with the appropriate tools
for the requested medium. Do not redesign unrelated existing work.

## Scope and priorities

Apply when creating, changing or explicitly auditing a visual composition:
UI, game menus, websites, images, diagrams, slides, documents or formatted tables.
Do not invoke merely to read a screenshot, operate an app or answer in plain text.
Preserve the user's format, content, assets, language, accessibility requirements
and established design system. Explain genuine exceptions; do not silently drop
the constraint or sacrifice usability to satisfy a number.

For a localized repair, change only the requested property. Preserve the original
palette, shapes, framing and alpha transparency. A centering request is not
permission to recolor a logo or add a background. Prefer its editable vector or
code source when available; reject generated variants that alter these invariants.

## Mathematical basis

Read [the mathematical foundation](references/mathematical-foundation.md).

`phi = (1 + sqrt(5)) / 2 = 1.618033988749895`.
For `a > b > 0`, `(a+b)/a = a/b = phi`.
The shares of a usable total are `1/phi` and `1/phi**2`, about 61.8034% and 38.1966%.

Before styling, identify the canvas, safe areas, margins, gutters and important
regions. For one axis, calculate:

```text
usable = total - leading_margin - trailing_margin - gutter
major = usable / phi
minor = usable - major
```

Use a meaningful relationship: main/supporting regions, image/copy balance,
a freely sized golden rectangle, or a specified focal position. Do not impose
two panels on every composition. Keep required A4, 16:9, square or other formats;
apply the relationship inside them. Never distort a logo, glyph or data series.

The included [calculator](scripts/golden_layout.py) supports equal margins and a gutter:

```text
python scripts/golden_layout.py --width 1016 --height 629 --padding 34 --gap 21 --axis x
```

Calculate asymmetric margins separately. Keep all lengths in the same unit.

## Margins, controls and hierarchy

- Choose a meaningful base spacing `b`; derive tokens from `b * phi**n` and round
  consistently. For `b=8`, a useful ladder is `8, 13, 21, 34, 55`.
- Give content comfortable clearance from the screen or page edge. Respect safe
  areas and responsive constraints. These tokens are not fixed dimensions for
  every device or project.
- Keep related controls equal or visually close in height unless their purpose
  requires otherwise. Do not enlarge a primary button solely to create a 55/34
  height ratio. Use color, contrast and type to establish priority.
- Derive primary type levels from a readable base: `16 * phi**n`, approximately
  `16, 26, 42`. An explicitly named half-step uses `sqrt(phi)`, not phi itself.
  Account for font metrics and small-size rounding rather than claiming exact ratios.
- Every important free dimension must come from a relationship, token, content
  requirement or explained constraint. Do not recursively force every pixel into phi.

A usable control can be `16 + 2*13 = 42` units high while its enclosing panel is
a golden rectangle. This is an intentional functional choice, not a failed attempt
to make every button a golden rectangle.

## Position complete groups, not isolated buttons

Specify title/subtitle alignment before rendering: shared left edges or shared
text centers. Left alignment alone is not evidence of the golden ratio.

When a group of height `H` sits inside a usable vertical interval `T`, first
calculate the remaining empty space `V = T-H`. For a larger lower empty region:

```text
empty_above = V / phi**2
empty_below = V / phi
```

Reverse those shares when the upper empty region should dominate. Include every
label, control and internal gap in `H`. Do not put a button center at 61.8% of the
screen while ignoring the rest of the group. Explicit bottom/left anchoring may
take priority; apply a verified relationship inside its actual containing panel.

## Implement and inspect

- UI: implement named tokens and real layout constraints. Percentage columns
  totaling 100% plus a gap overflow; distribute the remaining space with weights
  `phi:1` or subtract the gap explicitly. Test the intended size and a narrow
  viewport for responsive work. Preserve label fit, navigation and usable controls.
- Documents/slides: calculate after margins and gutters in the medium's units;
  preserve pagination and content fit.
- Images: provide concrete regions and positions to the image tool, then inspect
  the result. A prompt is not pixel evidence. Prefer deterministic HTML/CSS, SVG
  or native UI rendering when exact interface geometry is required.
- Data/diagrams: compose the frame and hierarchy without changing values, scales
  or the meaning of connections.

## Required validation workflow

### Glyphs inside badges and controls

The golden ratio does not center a character. Check the visible glyph's center
against its container on **both axes**. `text-anchor`, baseline settings, flex/grid
and a text line box do not prove that visible ink is centered. Obtain ink bounds
from the actual rendered pixels or vector outline. A DOM text Range alone is not
ink geometry. Name any intentional optical offset rather than calling it centered.

For an isolated repair, use the checker's `glyph-centering` profile and a
`glyph_center` rule. Define its scope and tolerance before measuring. A missing
glyph or non-ink box is UNVERIFIED; an offset outside tolerance is FAIL. Neither
can be reported as successful delivery. Inspect the final render at its intended
display sizes. Reject or mark any export whose glyph cannot be verified.

A composition PASS without a declared glyph rule does not validate badge contents.
This remains a local check, not a guarantee of global conformity or optical beauty.

Read [verification instructions](references/verification.md). Define a geometry
contract **before** generation. Then obtain observed measurements from the final
render, not from the contract or prompt.

[measure_dom.mjs](scripts/measure_dom.mjs) extracts rendered DOM boxes. For a bitmap
alone, manually measure and declare the uncertainty. There is no automatic OCR.
[verify_layout.py](scripts/verify_layout.py) binds the measurement file to a PNG/JPEG
by SHA-256 and checks the declared rules, viewport, bounds and tolerances.

```text
python scripts/verify_layout.py --spec contract.json --measurements observed.json --image render.png --out report.json
```

Target no more than 1% relative error for named golden ratios; never exceed 2%
without an explicit, separately documented exception. Pixel tolerances in this
checker cannot exceed two reference-canvas units. Correct failed implementations
and remeasure; never widen tolerances after failure just to obtain a pass.

The checker requires alignment, ratio, spacing and whitespace categories. It does
not prove complete semantic coverage of a composition:

- `PASS_DECLARED_RULES_ONLY`: the supplied observed measurements pass all declared rules.
- `FAIL_DECLARED_RULES_ONLY`: at least one declared check fails.
- `UNVERIFIED_DECLARED_RULES_ONLY`: required evidence or measurements are missing.
- `global_composition_conformity: NOT_ESTABLISHED` remains explicit.

Report the named relationships, actual measurements, error and inspection method.
Distinguish **calculated**, **implemented** and **render inspected**. Do not claim
global conformity, aesthetic superiority or accessibility compliance from this
checker's local result. A ratio between two control heights does not mean that
either control is a golden rectangle. A spiral overlay is diagnostic, not proof.

Do not install hooks, external skill packs or background monitors without a separate
request. [Source notes](references/sources.md) explain the external ideas considered.
