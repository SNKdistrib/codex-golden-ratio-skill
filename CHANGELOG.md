# Changelog

## 0.1.2 — 2026-10-29

- Added the `logo-lockup` profile and automatic relationships for a mark, wordmark and tagline.
- Require explicit center/bottom and center/left alignment choices rather than silently assuming centering.
- Check positive gaps, safe margins, optional canvas centering and a strict upper-row width limit against the tagline.
- Reject ignored extra observed components in this isolated profile.
- Added `export_verified.py`: create a new delivery file only after verification passes.
- Added regression tests that prove failed/unverified exports create no delivery artifact and existing files are preserved.
- Clarified that colors, transparency and complex brand structures still need their own real checks; no global hook is installed.

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
