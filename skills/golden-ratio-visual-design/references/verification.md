# Verifying an observed layout

Python 3.11+ and its standard library are sufficient. No API key, network or Python
package installation is needed for the calculator, verifier or unit tests.
The optional DOM helper runs in a browser context, not Node alone.

```text
python scripts/verify_layout.py --spec contract.json --measurements observed.json --image render.png --out report.json
python -m unittest discover -s tests -v
```

Exit codes: `0` declared rules pass; `1` at least one fails; `2` evidence is
unverified or input is invalid. Report output cannot replace one of its inputs.

## Contract before creation

The JSON object contains `version: 1`, `canvas: {width, height}`, `spacing_base`,
`tolerance_px` (normally 1, maximum 2 reference units), and `rules`.
Each rule has a unique `id` and a `type`:

- `align`: box IDs `a`, `b`, and `edge`: `x`, `y`, `right`, `bottom`, `center_x`,
  `center_y`, `width` or `height`.
- `glyph_center`: box IDs `glyph` and `container`. Checks visible ink center on
  both X and Y, plus containment within the container's bounding rectangle.
- `lockup`: a complete three-part mark, wordmark and tagline arrangement; see below.
- `ratio`: `a` and `b` are references such as `{"box":"panel","value":"width"}`.
  Length values are `width`, `height` or `font_size`. Expected ratio is
  `phi**exponent`, exponent 1 by default. Relative tolerance defaults to 1%,
  maximum 2%. Exponent zero is not a golden-ratio comparison.
- `gap`: box IDs `from`, `to`, `axis` (`x`/`y`) and `exponent`. The positive
  edge-to-edge gap should equal `spacing_base * phi**exponent`.
- `position`: a `ref` (`box`, `value`) and an `expected` reference-canvas value.
- `void_ratio`: `before` and `after` (box IDs), `group` (a list of box IDs), `axis` and `dominant`
  (`before`/`after`). Compares the two real empty regions around the full group.
- `inner_void_ratio`: uses a real `container` instead of before/after anchors.
  Include `group`, `axis`, `dominant`, and optionally `exponent`. Every member must
  remain inside the container; both empty regions must be positive.

Alignment, ratio, spacing and whitespace categories are required by the default
`composition` profile. These UI-layout
requirements do not create a universal image-understanding tool. Do not invent
invisible boxes to make an illustration pass. Do not alter a contract after failure
to fit whatever the generator produced.

## Three-part brand lockups

Use `profile: "logo-lockup"`, an explicit `scope_note` and exactly one `lockup` rule:

```json
{
  "id": "brand",
  "type": "lockup",
  "mark": "mark",
  "wordmark": "wordmark",
  "tagline": "tagline",
  "horizontal_gap_exponent": 3,
  "vertical_gap_exponent": 2,
  "safe_margin": 21,
  "row_alignment": "bottom",
  "tagline_alignment": "left",
  "upper_width": "at_most_tagline",
  "center_on_canvas": true
}
```

The three observed boxes must be distinct and have `bounds_kind: "visible_ink"`.
The isolated profile does not accept extra observed components that its rule would
ignore. Missing or non-ink observations remain UNVERIFIED.

The required alignment choices are `row_alignment` (`center_y` or `bottom`),
`tagline_alignment` (`center_x` or `left`) and `upper_width` (`free` or
`at_most_tagline`). Missing choices are not silently replaced by centering.
The width-limited mode rejects any upper-row extent outside the tagline's left/right
edges; it does not use the alignment tolerance to permit overshoot.

The rule automatically checks the chosen mark/wordmark vertical alignment and
tagline alignment against the complete upper row, positive edge-to-edge gaps equal to
`spacing_base * phi**exponent`, and the declared safe area. Optional canvas
centering covers the whole three-part union. Optional
`mark_to_wordmark_exponent` and `wordmark_to_tagline_exponent` check height ratios;
do not declare them after the fact merely to fit a generated output.

This does not recognize objects, verify spelling, assess optical balance or check
colors and alpha automatically. Inspect those properties in the medium's workflow.
More complex logos need their real components covered in a composition contract.

## Block delivery on failed or missing checks

```text
python scripts/export_verified.py --spec contract.json --measurements observed.json --image candidate.png --out delivered.png
```

The export gate invokes verification itself. It refuses to replace an input or
existing output. FAIL returns 1, UNVERIFIED or invalid input returns 2; neither
creates the delivery file. Only PASS copies the exact image bytes bound to the
observed measurements by SHA-256. The command is an explicit build/delivery step,
not a system-wide interceptor for all image generators. Read its result and inspect
the delivered PNG/JPEG. The existing verifier remains available for reports alone.

## Isolated glyph-centering repairs

For this narrow task only, specify `profile: "glyph-centering"`, an explicit
nonempty `scope_note`, and one or more `glyph_center` rules. No other rule type is
accepted in this profile. It does not pretend to check unrelated layout categories.

```json
{
  "version": 1,
  "profile": "glyph-centering",
  "scope_note": "Only the currency glyph inside this badge",
  "canvas": {"width": 512, "height": 512},
  "spacing_base": 8,
  "tolerance_px": 0.5,
  "rules": [
    {"id": "currency_center", "type": "glyph_center", "glyph": "currency", "container": "badge"}
  ]
}
```

In the observed measurements, the glyph box must include
`"bounds_kind": "visible_ink"`. Measure actual pixels or the visible vector contour,
not a font's line box, baseline or DOM Range. Without that declaration, the result
is UNVERIFIED. Missing boxes or stale image evidence also prevent PASS. An offset
outside tolerance on either axis, or a glyph outside the container's rectangle,
fails. Exit codes remain 0 / 1 / 2; run the command as a blocking build or delivery
step and check its exit code instead of merely writing a report.

The report records `validation_profile` and `scope_note`. Global conformity remains
NOT_ESTABLISHED. This check cannot authenticate supplied annotations, judge optical
balance, measure clearance at circle corners or recognize a glyph automatically.
For a full composition, keep the default profile and add relevant glyph rules.

## Measurements after rendering

```json
{
  "version": 1,
  "kind": "observed",
  "canvas": {"width": 1016, "height": 629},
  "pixel_ratio": 1,
  "evidence": {
    "method": "dom",
    "image_sha256": "REPLACE_WITH_THE_FINAL_IMAGE_SHA256",
    "uncertainty_px": 0
  },
  "boxes": {
    "panel": {"x": 34, "y": 389, "width": 354, "height": 219}
  }
}
```

This incomplete fragment documents the shape; it is not evidence or a passing
example. Measurements must come from the final render, not the prompt or contract.
Origin `planned` cannot pass. Method is `dom` or `manual`.

`scripts/measure_dom.mjs` exports
`measureLayout(selectors, sourceImageSha256, pixelRatio)`.
Each ID maps to `{selector, textOnly?}`. The helper uses rendered bounding boxes,
or a text Range for title/subtitle alignment. Missing, hidden, empty or ambiguous
selections remain missing. It records computed font size as well.

Capture and measure without changing viewport, scroll or zoom. Use the actual PNG
or JPEG pixel ratio, which may differ from the display's device pixel ratio.
Dimensions must match the measured viewport times that ratio. Canvas aspect
distortion beyond 0.5% fails. Coordinates are normalized to the reference canvas.

For a bitmap, manually annotate observed boxes and declare the uncertainty.
Uncertainty above two observed units is unverified. SHA-256 binds annotations to
an image file but does not authenticate the annotations themselves. No OCR or
automatic object recognition is implemented.

## Scope and limits

`PASS` is reported as `PASS_DECLARED_RULES_ONLY`.
`global_composition_conformity` stays `NOT_ESTABLISHED`.
Four categories do not prove all important visual relationships were checked.
A failure can coexist with unverified measurements; read each check.

The verifier checks declared gaps, containment rules and viewport bounds, not
every possible overlap, spelling, contrast, accessibility or aesthetic property.
Inspect the final image separately. Synthetic unit tests exercise the checker;
they are not real-design validation or proof that an AI always follows the skill.
