# Contributing

Thank you for helping make measurable visual design more reliable.
Contributions to code, tests, documentation and reproducible examples are welcome.

## Workflow

1. Open an issue for a substantial change, or pick an existing issue.
2. Fork the repository and create a focused branch, for example `codex/improve-gap-checks`.
3. Keep unrelated changes out of the pull request.
4. Run the checks below and explain what was tested.
5. Open a pull request against the default branch. Maintainers review before merging.

You do not need direct write access to propose changes through a fork.
Do not request or share passwords, GitHub tokens, API keys or private project files.

## Local checks

Python 3.11+ and a modern Node.js installation are sufficient:

```sh
python -m unittest discover -s skills/golden-ratio-visual-design/tests -v
node --check skills/golden-ratio-visual-design/scripts/measure_dom.mjs
```

The Python tools use only the standard library. Do not add runtime dependencies
without explaining their need and impact.

## Validation principles

- Define constraints before checking an output; do not fit the contract to an image.
- Distinguish planned, implemented and observed geometry.
- Bind evidence to its actual screenshot and preserve reproducibility.
- A local `PASS` must never become an unsupported claim of global conformity.
- Do not widen tolerances merely to silence a failing test.
- Keep usability and accessibility ahead of forcing a ratio onto every control.
- Test invalid inputs and failure paths, not only successful synthetic fixtures.

For a checker change, include a regression test and state its coverage limits.
For a visual example, document canvas, relationships, measurements, rounding
and inspection method. Use original or properly licensed assets. Remove personal
paths and private data. Do not present a same-context comparison as a blind trial.

## Documentation and license

English is the primary technical language. French documentation is welcome;
update both READMEs when changing installation or public behavior.
Describe limitations directly rather than promising mathematical beauty.

By submitting a contribution, you agree that it may be distributed under this
repository's MIT license. Do not contribute material you cannot license.
