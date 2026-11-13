# Evidence report improvements

Reviewed 13 November 2026. The existing four tests passed, including the Streamlit
save-review/export workflow. Everything below is proposed, not implemented.

## Highest-value next updates

1. **Faster review queue.** Thumbnail cards, next/previous shortcuts, unreviewed-only
   and reviewer/decision filters, plus counts of conflicting or stale reviews.
   Keep source frame IDs and timestamps visible when changing filters.
2. **Overlay and evidence browsing.** Show every retained crop, a frame/heatmap
   overlay and explicit evidence-missing state. The current interface displays the
   first evidence image beside a separate heatmap.
3. **Review session state.** Bind unsaved notes to run/frame identity and reset or
   explicitly carry the decision when switching findings. Add a save confirmation
   that displays the exact finding being reviewed.
4. **Robust import validation.** Validate required metadata, score ranges, array
   types, packed offsets and review schemas before opening a run. Show malformed
   records as actionable diagnostics rather than an unhandled exception.
5. **Scale without weakening provenance.** `reviews_for()` scans every review file
   for each finding, and bindings repeatedly hash metadata/manifest/evidence. Build
   a run-level review index and safely cache immutable snapshots. A standard-library
   SQLite index can come later; keep JSON review records as the audit source.

## Useful product additions

- Asset/inspection identifiers, summaries by decision, and explicit unresolved items.
- Selectable full-evidence versus thumbnail-only portable reports, file-size estimates,
  export progress and a retained report/provenance manifest.
- Optional PDF output after layout requirements are defined; keep HTML as the core
  portable artifact and avoid a rendering dependency until PDF is actually needed.
- Import candidate changes from `repeat-inspection-tracker` alongside drone findings.
- A shared versioned run/finding schema across producer and reviewer, with fixtures
  for both NPY and packed heatmaps and legacy migration tests.

## Completion checks

Switching findings must not attach notes or approval to the wrong evidence. Modified
inputs must still invalidate a review. Test empty/malformed/truncated runs, conflicts,
large queues, moved report files, missing assets and HTML escaping. Run status must
remain visible, including incomplete/failed inputs. Authenticate users before any
multi-user deployment; a typed reviewer name is not verified identity.

This plan can be developed with generated runs now; measuring inspector usefulness
and real decision quality remains later work. No extra dependency is required for
the initial queue, validation and overlay improvements.
