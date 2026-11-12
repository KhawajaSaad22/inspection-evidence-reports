# Initial validation — 12 November 2026

Four automated checks passed locally and in a Python 3.11 Linux container:

- Streamlit review selection, save-review and HTML export workflow.
- Review binding invalidation after a changed heatmap and escaped report content.
- Packed heatmap import, truncated grid rejection and path traversal guards.
- Duplicate frame ID rejection and required reviewer identity.

The image builds, the synthetic report exports, and an HTML report also exported
from an existing `drone-inspection-heatmaps` synthetic run. This establishes format
integration, not a real inspection review. Dependencies are bounded compatibility
ranges, not a reproducible lockfile. No PDF export, reviewer authentication or
digital-signature validation is included. GitHub CI is configured; its first run
is checked after publishing. Generated evidence/reviews/reports are not committed.
