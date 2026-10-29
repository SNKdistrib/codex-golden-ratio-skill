# Changelog

## 0.1.1 — 2026-10-29

- Added `glyph_center` to check visible ink centers on both axes and rectangular containment.
- Added a scoped `glyph-centering` profile for isolated repairs, without weakening the default composition profile.
- Require declared visible-ink bounds; missing ink measurements and stale evidence cannot pass.
- Keep global conformity explicitly NOT_ESTABLISHED, including in targeted reports.
- Added regression and CLI exit-code tests for PASS, FAIL and UNVERIFIED delivery gates.
- Clarified that localized repairs preserve original colors, shapes and transparency.
- Expanded English and French documentation with the new contract and its limits.

## 0.1.0

- Initial public, English-language skill with French project documentation.
- Golden-section calculator and observed-layout verifier.
- Browser DOM measurement helper.
- Explicit distinction between declared-rule validation and global conformity.
- Guidance for comfortable margins and balanced functional controls.
- Standard-library regression tests and contribution workflow.
