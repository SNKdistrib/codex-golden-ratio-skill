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

## What is included

- A Codex-compatible `SKILL.md` and automatic invocation metadata.
- A golden-section calculator using Python's standard library.
- A geometry verifier for alignment, ratios, gaps, positions and whitespace.
- An optional browser DOM measurement helper.
- Tests, mathematical notes and explicit validation limits.

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
