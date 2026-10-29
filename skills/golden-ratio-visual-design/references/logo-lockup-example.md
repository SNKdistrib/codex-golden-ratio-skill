# Reference: explicit left/bottom brand alignment

This example was accepted by the project owner on 2026-10-29. It demonstrates
turning specific placement requirements into a measured contract—not a universal
logo template or a guarantee of aesthetic perfection.

## Required relationships

- The first letter of the tagline shares the mark's left ink edge.
- The wordmark shares the mark's bottom ink edge, not its vertical center.
- The entire upper row fits within the tagline's width.
- Preserve the official artwork, colors, letter shapes and transparent background.

## Render and measurements

The [clean PNG](../assets/examples/snk-lockup/logo-transparent.png) is 600 × 200.
The [audit overlay](../assets/examples/snk-lockup/logo-audit.png) is 1200 × 400,
shown at twice the measurement scale. Both have transparent backgrounds.

| Observed relationship | Result |
| --- | --- |
| Mark/tagline left edge | 67 px / 67 px |
| Mark/wordmark bottom | 124 px / 124 px |
| Upper row width / tagline width | 466 px / 467 px |
| Mark/wordmark ink heights | 84 px / 52 px |
| Height ratio compared with phi | 1.6153846154; relative error 0.1637403% |
| Horizontal gap | 21 px; target `5 * phi^3 = 21.18034` |
| Vertical gap | 13 px; target `5 * phi^2 = 13.09017` |

Alignment tolerance is 1 reference pixel. The width cap allows no overshoot.
The mark/name height ratio is a named golden relationship; the logo canvas and
individual letters are not claimed to be golden rectangles. The original 3:1
format and letter shapes take priority over imposing phi on every bounding box.

The overlay uses green alignment axes and golden subdivisions of object and
letter ink boxes. Its grid is a comparison aid, not independent proof of beauty
or mathematical conformity of every letter. It is kept separate from the clean asset.

## Re-run the geometry checks

From the repository root:

```text
python skills/golden-ratio-visual-design/scripts/verify_layout.py --spec skills/golden-ratio-visual-design/assets/examples/snk-lockup/contract.json --measurements skills/golden-ratio-visual-design/assets/examples/snk-lockup/observed.json --image skills/golden-ratio-visual-design/assets/examples/snk-lockup/logo-transparent.png
```

The [contract](../assets/examples/snk-lockup/contract.json),
[observed boxes](../assets/examples/snk-lockup/observed.json) and
[report](../assets/examples/snk-lockup/report.json) are supplied. The image hash
binds those observations to the accepted PNG. Measurement used actual rendered
layer pixels; it was not OCR. The private artwork-composition check additionally
verified alpha and preserved colors. The shared geometry checker does not perform
that image understanding itself.

For a new image, do not reuse these coordinates or this hash. Fix its own contract
before rendering, measure its own output, inspect it, then use `export_verified.py`.
All reports retain `global_composition_conformity: NOT_ESTABLISHED`.

## Français

Cette référence illustre des contraintes demandées explicitement : B du slogan
aligné à gauche du symbole, nom aligné en bas, rangée supérieure limitée à la
largeur du slogan. Le filigrane sert à comparer les boîtes et les divisions phi ;
il ne transforme pas chaque lettre en rectangle d'or. Réutiliser la méthode,
pas imposer cette disposition à tous les logos. Les mesures doivent toujours venir
du rendu réellement livré.
