/// The annotation "verbs". `note` carries free text, `ink` carries strokes,
/// `bookmark` marks a saved location (no on-page rendering).
enum AnnotationType { highlight, underline, strikethrough, note, ink, bookmark }

/// Outcome of anchor resolution. The product promise lives here:
/// an annotation is always exactly one of these — never silently misplaced.
enum AnchorState {
  /// Structural locator valid and quote agrees. High confidence.
  resolved,

  /// Structural locator was stale; relocated via the quote selector.
  repaired,

  /// Located by fuzzy match only; flagged "approximate" in the UI.
  approx,

  /// Could not be located. Data is kept and surfaced in "Needs review".
  orphaned,
}

/// Supported content formats. The renderer adapter is chosen from this.
enum BookFormat { html, pdf, epub, image }

/// Format-native structural locator kind.
enum LocatorType { domRange, cfi, pdfQuads, rect, percent }

/// Sync delta operation.
enum ChangeOp { upsert, delete }
