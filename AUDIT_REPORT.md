# Code audit report

## Critical issues fixed

- Replaced the copied education entry `B.Tech CS, IIIT Delhi '24` with the correct education: B.Tech in Computer Science and Engineering at Lovely Professional University, expected graduation in 2027.
- Removed unrelated employment and achievement claims for Dock.us, Turgon AI, AccioJob, 100,000+ learners, books, and podcast streams.
- Corrected the contribution username from `deekshith` to `Deekshith06`.
- Removed the unrelated fallback snapshot that contained fabricated contribution totals.
- Unified contribution generation so the renderer uses the verified JSON produced by the fetch step.
- Fixed current-streak handling for incomplete current days and stale snapshots.
- Rebuilt calendar placement using actual dates, Sunday-based rows, and week offsets.
- Added request retries, timeouts, input validation, deduplication, accessible SVG metadata, and reduced-motion support.
- Updated GitHub Actions and Python dependency versions.
- Prevented unnecessary workflow loops by limiting path triggers.
- Added automated tests and a separate quality-check workflow.

## GitHub Pages root-cause fix

`https://deekshith06.github.io/` cannot be served by the profile repository named `Deekshith06`. GitHub requires a separate repository named exactly `Deekshith06.github.io` for the root user site.

A separate deployment-ready package is included so the profile repository can keep its special name and continue showing the profile README.

## Validation completed

- Python compilation passed.
- Five unit tests passed.
- JavaScript syntax validation passed.
- HTML parsing passed.
- CSS structure checks passed.
- SVG XML validation passed.
- Local asset resolution passed.
- Local HTTP delivery smoke test passed.
- False identity data regression checks passed.

## One-screen portfolio and portrait update

- Replaced the earlier generated SVG portrait with a higher-recognition PNG portrait based on the source photo.
- Removed the obsolete portrait preprocessing/generation scripts, which were no longer used by the workflow and had undeclared heavy dependencies.
- Rebuilt `Deekshith06.github.io` as a fixed-viewport, one-page portfolio with accessible tab panels and no body scrolling.
- Added a dependency-free site validator and JavaScript syntax check to the Pages deployment workflow.
- Verified desktop, tablet, mobile, and compact-mobile viewport dimensions without document overflow.
