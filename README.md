# Golden Ratio Visual Design for Codex

[Français](README.fr.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)

A community skill for building visual layouts with **measurable golden-ratio
relationships**, comfortable margins and balanced controls—not just a prompt
that says “make it golden.”

The workflow is: define the geometry, implement it, render it, measure the result,
and inspect the image. The included verifier checks declared measurements against
a contract and binds them to a screenshot with SHA-256.

**Work in progress. Contributions are welcome.** A passing local check is not
proof that an entire composition is golden, beautiful or accessible.

## Accepted reference example

**Clean transparent PNG**

![SNK Distrib reference with shared left/bottom edges](skills/golden-ratio-visual-design/assets/examples/snk-lockup/logo-transparent.png)

**Control overlay** — chosen alignment axes, ink boxes and golden subdivisions

![Measured geometry overlay](skills/golden-ratio-visual-design/assets/examples/snk-lockup/logo-audit.png)

Mark/tagline left edge: **67 px**. Mark/name bottom: **124 px**.
The upper row is **466 px**, within the **467 px** tagline.
The named mark/name height ratio is **84/52 = 1.61538**, a **0.164%** difference
from phi. The overlay is diagnostic; it does not claim every glyph is a golden rectangle.
Both images are transparent; the dark lettering is intended for a light surface.
See the [measured example, contract and limits](skills/golden-ratio-visual-design/references/logo-lockup-example.md).

## What is included

- A Codex-compatible `SKILL.md` and automatic invocation metadata.
- A golden-section calculator using Python's standard library.
- A geometry verifier for alignment, ratios, gaps, positions and whitespace.
- An optional browser DOM measurement helper.
- Tests, mathematical notes and explicit validation limits.

### New in 0.1.2: complete lockups and an export gate

The `logo-lockup` profile covers a mark, wordmark and tagline together: shared
explicit center/bottom and center/left alignments, optional tagline width limit,
spacing, safe margins and optional whole-canvas centering. An extra
observed component cannot be silently ignored. `export_verified.py` creates the
delivery file only after verification passes; failures and missing evidence block
that export. This is an explicit pipeline step, not a global image-generation hook.
See the [lockup and export instructions](skills/golden-ratio-visual-design/references/verification.md#three-part-brand-lockups).

### Added in 0.1.1: visible glyph centering

The verifier can now check a character's **visible ink center on both axes** inside
a badge. Missing ink measurements are UNVERIFIED; an offset outside the declared
tolerance fails. An isolated `glyph-centering` profile keeps this repair distinct
from a full composition audit. The CLI's nonzero exit code must block delivery.
The skill also explicitly preserves the original palette and transparency during
localized repairs. See the [centering contract](skills/golden-ratio-visual-design/references/verification.md#isolated-glyph-centering-repairs).

Golden-ratio layout does not mean making every button a golden rectangle.
Usability, readable text and explicit user requirements remain essential.

## Install

Download `golden-ratio-visual-design.zip` from the [latest release](https://github.com/SNKdistrib/codex-golden-ratio-skill/releases/latest).
Extract its `golden-ratio-visual-design` folder into:

```text
~/.agents/skills/
```

On Windows, that is normally `%USERPROFILE%\.agents\skills\`.
Back up an existing folder with the same name before replacing it. No installer,
background service, account connection or API key is required.

Alternatively, clone this repository and copy
`skills/golden-ratio-visual-design` into your user skill directory.

Invoke explicitly in Codex:

```text
$golden-ratio-visual-design
Design this menu with comfortable margins, then verify the rendered geometry.
```

Implicit selection uses the skill description. For an always-on preference, add
an explicit visual-work instruction to your own `AGENTS.md`; this package does
not edit global preferences automatically. If discovery has not refreshed,
restart Codex. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

## Run the tools

Python 3.11+ is supported. From the repository root:

```sh
python skills/golden-ratio-visual-design/scripts/golden_layout.py --width 1016 --height 629 --padding 34 --gap 21 --axis x
python -m unittest discover -s skills/golden-ratio-visual-design/tests -v
```

For an actual rendered layout:

```sh
python skills/golden-ratio-visual-design/scripts/verify_layout.py --spec contract.json --measurements observed.json --image render.png --out report.json
```

Read the [measurement format and rule types](skills/golden-ratio-visual-design/references/verification.md)
before creating those files. The DOM helper runs in a browser page and needs no
Node package installation; it is not a standalone Node screenshot tool.

## What validation means

- Exit `0`: all **declared** rules pass.
- Exit `1`: at least one declared rule fails.
- Exit `2`: missing evidence, unverified measurements or invalid input.

The report explicitly includes `global_composition_conformity: NOT_ESTABLISHED`.
The tool does not recognize objects or text automatically, authenticate manual
annotations, judge beauty, or perform a complete accessibility audit. A screenshot
must still be inspected. These limits are intentional—not hidden behind a score.

## Help develop it

Anyone can fork the public repository, modify their copy and submit a pull request.
Maintainers review changes before merging; public contribution does not grant
everyone direct write access. Issues are open for bugs and proposals.

Useful contributions include reproducible layout examples, improved coverage
reporting, more edge-case tests, browser measurements and clearer documentation.
Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## Attribution

The verifier is implemented in this project. External design references are
credited in [source notes](skills/golden-ratio-visual-design/references/sources.md).
No game artwork, personal screenshots, local account data or unrelated skills
are included. This is an independent community project, not an official OpenAI product.
